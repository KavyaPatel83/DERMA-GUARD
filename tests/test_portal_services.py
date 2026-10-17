"""Tests for the portal services added in src/services (auth, scheduling, honest evaluation, morphology)."""
import math
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.services import auth, honest_eval, inference, scheduling


# ---------------------------------------------------------------- auth
def test_password_hash_roundtrip_and_salt():
    h1, h2 = auth.hash_password("Correct-horse-1"), auth.hash_password("Correct-horse-1")
    assert h1 != h2                                   # per-user random salt
    assert auth.verify_password("Correct-horse-1", h1)
    assert not auth.verify_password("wrong-horse-1", h1)
    assert not auth.verify_password("x", "garbage")


@pytest.mark.parametrize("pw,ok", [("short1", False), ("allletters", False), ("12345678", False), ("Valid-pass-1", True)])
def test_password_policy(pw, ok):
    assert (auth.password_problem(pw) is None) == ok


def test_email_regex():
    assert auth.EMAIL_RE.match("a@b.co")
    assert not auth.EMAIL_RE.match("not-an-email")


# ---------------------------------------------------------------- scheduling
def test_valid_slot_rules():
    assert not scheduling.valid_slot("2020-01-06T09:00")          # in the past
    assert not scheduling.valid_slot("garbage")
    future_sat = "2099-01-03T09:00"                                # a Saturday
    assert datetime.strptime(future_sat, "%Y-%m-%dT%H:%M").weekday() == 5
    assert not scheduling.valid_slot(future_sat)
    assert scheduling.valid_slot("2099-01-05T09:30")               # Monday morning
    assert not scheduling.valid_slot("2099-01-05T13:00")           # lunch break
    assert not scheduling.valid_slot("2099-01-05T09:15")           # not on the half hour


# ---------------------------------------------------------------- honest evaluation maths
def test_ece_zero_for_perfectly_calibrated():
    p = np.array([[1.0, 0.0], [0.0, 1.0]])
    assert honest_eval.ece(p, np.array([0, 1])) == pytest.approx(0.0)


def test_temperature_reduces_overconfidence():
    rng = np.random.default_rng(0)
    y = rng.integers(0, 3, 400)
    logits = rng.normal(size=(400, 3)); logits[np.arange(400), y] += 1.0   # weak signal
    p = np.exp(logits * 4); p /= p.sum(1, keepdims=True)                   # overconfident
    T = honest_eval.fit_temperature(p, y)
    assert T > 1.5
    assert honest_eval.ece(honest_eval.temperature_scale(p, T), y) < honest_eval.ece(p, y)


def test_conformal_coverage_on_exchangeable_data():
    rng = np.random.default_rng(1)
    def draw(n):
        y = rng.integers(0, 4, n)
        p = rng.dirichlet(np.ones(4), n); p[np.arange(n), y] += 0.8
        return p / p.sum(1, keepdims=True), y
    pc, yc = draw(500)
    q = honest_eval.conformal_q(pc, yc, alpha=0.1)
    pt, yt = draw(4000)
    covered = (pt >= 1 - q)[np.arange(4000), yt].mean()
    assert covered >= 0.87                                   # ~0.9 up to sampling noise


def test_splits_audit_finds_the_leak():
    """The original script's 'test' indices are a subset of its training indices."""
    y, df, idx_train, idx_test, idx_val, held, held_pd = honest_eval.splits()
    assert set(idx_test.tolist()) <= set(idx_train.tolist())
    assert len(set(held.tolist()) & set(idx_train.tolist())) == 0
    assert len(held_pd) <= len(held)


# ---------------------------------------------------------------- morphology
def _synthetic_lesion(r=70, size=320):
    img = Image.new("RGB", (size, size), (222, 180, 160))
    d = ImageDraw.Draw(img)
    c = size // 2
    d.ellipse([c - r, c - r, c + r, c + r], fill=(95, 55, 40))
    return img


def test_morphology_recovers_circle():
    out = inference.morphology(_synthetic_lesion(70))
    assert out["status"] in ("success", "low_quality")
    assert out["circularity"] > 0.8
    expected = math.pi * 70 ** 2
    assert abs(out["area_px"] - expected) / expected < 0.2
    assert out["asymmetry"] < 0.15


def test_simulated_growth_increases_area():
    base = _synthetic_lesion(50)
    mask = inference.lesion_mask(base)
    grown = inference.simulate_growth(base, mask, 0.8)
    a0 = inference.morphology(base)["area_px"]
    a1 = inference.morphology(grown)["area_px"]
    assert a1 > 1.4 * a0


# ---------------------------------------------------------------- acquisition
def _fake_result(active, conf=0.5, q=0.9):
    return {"active_modalities": active, "diagnosis": {"confidence": conf},
            "evidence": {"quality": {"image": q, "metadata": 1.0}}}


def test_acquisition_uses_measured_gain_and_penalises_cost():
    measured = {"A": {"heldout_accuracy": 0.61, "text_dependent": False},
                "B": {"heldout_accuracy": 0.78, "text_dependent": False},
                "D": {"heldout_accuracy": 0.65, "text_dependent": False}}
    plan = inference.acquisition_plan(_fake_result(["image"]), None, measured)
    add_meta = next(a for a in plan["ranked"] if a["action"] == "add_details")
    assert add_meta["delta_v"] == pytest.approx(0.04, abs=1e-6)       # D - A
    assert add_meta["basis"] == "measured held-out gain"
    scores = [a["score"] for a in plan["ranked"]]
    assert scores == sorted(scores, reverse=True)
    biopsy = next(a for a in plan["ranked"] if a["action"] == "biopsy")
    assert biopsy["cost"] == 10 and biopsy["delay_days"] == 7.0


def test_acquisition_does_not_recommend_negative_value_modality():
    measured = {"A": {"heldout_accuracy": 0.61, "text_dependent": False},
                "B": {"heldout_accuracy": 0.78, "text_dependent": False},
                "D": {"heldout_accuracy": 0.65, "text_dependent": False}}
    plan = inference.acquisition_plan(_fake_result(["metadata"]), None, measured)
    photo = next(a for a in plan["ranked"] if a["action"] == "retake_photo")
    assert photo["delta_v"] < 0 and photo["score"] < 0                 # adding the image hurts vs metadata-only


# ---------------------------------------------------------------- passwordless accounts + agent scores
def test_open_accounts_never_verify_a_password():
    assert not auth.verify_password("anything-1", auth.OPEN_HASH + "abc123")
    assert not auth.verify_password("", auth.OPEN_HASH)


def _score_result(conf=0.8, group="benign", code="NEV", action="ACCEPT"):
    return {"diagnosis": {"code": code, "group": group, "confidence": conf},
            "triage": {"action": action, "models_agree": 6, "models_total": 7},
            "selected_model": "Model G",
            "candidates": [{"code": "G", "modality": "image+meta", "predicted": code, "confidence": conf,
                            "evidence_score": 0.5, "heldout_accuracy": 0.64}]}


def test_agent_scores_are_bounded_and_explained():
    from src.services import care_agents as ag
    steps = [{"agent": a, "action": "x", "ok": True, "ms": 3, "detail": ""}
             for a in ("Intake", "Safety", "Vision-Triage", "Retrieval (RAG)", "Referral", "Report")]
    retrieved = {"chunks": [{"score": 0.9}], "similar": {"k": 2, "cases": [{"diagnosis": "NEV"}, {"diagnosis": "SEK"}]}}
    out = ag.score_agents(steps, _score_result(), [], retrieved, {"urgency": "routine"},
                          {"citations": [1, 2, 3], "mode": "template"}, {"age": 40, "gender": "MALE"}, {}, "")
    assert len(out["agents"]) == 6
    assert all(0.0 <= a["score"] <= 1.0 and a["basis"] for a in out["agents"])
    assert 0.0 <= out["agent_score"] <= 1.0 and 0.0 <= out["combined"] <= 1.0
    retr = next(a for a in out["agents"] if a["agent"].startswith("Retrieval"))
    assert abs(retr["score"] - (0.5 * 0.9 + 0.5 * 0.5)) < 1e-3          # relevance + 1 of 2 look-alikes agree


def test_failed_agent_scores_zero():
    from src.services import care_agents as ag
    steps = [{"agent": "Retrieval (RAG)", "action": "x", "ok": False, "ms": 1, "detail": "boom"}]
    out = ag.score_agents(steps, _score_result(), [], {"chunks": [], "similar": {"k": 0, "cases": []}},
                          None, None, {}, {}, "")
    assert next(a for a in out["agents"] if a["agent"].startswith("Retrieval"))["score"] == 0.0

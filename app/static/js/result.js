/* Renders an /api/analyze result. Shared by the diagnose workspace and the report page. */
(function () {
  const MOD = { image: "Lesion image", metadata: "Patient details", text: "Clinical text" };
  const MOD_COLOR = { image: "var(--brand)", metadata: "var(--accent)", text: "var(--warn)" };
  const ACTION_COPY = {
    ACCEPT: ["Level 1 · Strong consensus", "Evidence is sufficient and the models agree."],
    ARBITRATE: ["Level 2 · Needs arbitration", "Reasonable agreement, but a clinician should confirm."],
    ACQUIRE: ["Level 3 · Acquire more evidence", "The system needs better or additional input before deciding."],
    ESCALATE: ["Level 4 · Escalate to a specialist", "Too risky or too uncertain for automated triage."],
  };
  const RING = { malignant: "var(--bad)", "pre-malignant": "var(--warn)", benign: "var(--ok)" };

  const e = fmt.esc;
  const bar = (name, v, cls = "", extra = "") =>
    `<div class="bar"><span class="name" title="${e(name)}">${e(name)}</span>
     <div class="track"><div class="fill ${cls}" style="width:${Math.max(0, Math.min(1, v)) * 100}%"></div></div>
     <span class="val">${extra || fmt.pct(v, 1)}</span></div>`;

  function triage(r) {
    const t = r.triage, [title, sub] = ACTION_COPY[t.action];
    return `<div class="triage ${t.action}">
      <div style="flex:1">
        <div class="lvl">${t.action} <span style="opacity:.75;font-weight:700">· ${title}</span></div>
        <p>${e(sub)}</p>
        <ul class="clean" style="margin-top:8px">${t.reasons.map((x) => `<li>${e(x)}</li>`).join("")}</ul>
      </div></div>`;
  }

  function diagnosis(r) {
    const d = r.diagnosis;
    return `<div class="dx">
      <div class="ring" style="--p:${d.confidence * 100};--ringc:${RING[d.group]}"><span>${Math.round(d.confidence * 100)}%</span></div>
      <div>
        <div class="row" style="gap:8px"><h3 style="margin:0;font-size:1.4rem">${e(d.name)}</h3><span class="tag ${d.group}">${e(d.group)}</span></div>
        <p class="muted" style="margin:6px 0 0">${e(d.summary)}</p>
      </div></div>
      <p style="margin:14px 0 0;font-size:.9rem"><b>Typical features:</b> <span class="muted">${e(d.features)}</span></p>`;
  }

  function calibNote(r) {
    const c = r.calibration; if (!c || c.heldout_accuracy == null) return "";
    const ci = c.heldout_ci95 ? ` [${Math.round(c.heldout_ci95[0] * 100)}–${Math.round(c.heldout_ci95[1] * 100)}%]` : "";
    return `<div class="callout info" style="margin-top:12px;font-size:.84rem">
      <b>How much to trust this?</b> ${e(r.selected_model)} scored <b>${Math.round(c.heldout_accuracy * 100)}%</b>${ci} accuracy on
      rows it never trained on (temperature-calibrated T = ${c.temperature.toFixed(2)}). Treat the percentage above as
      the model's calibrated belief, not a guarantee.</div>`;
  }

  function ranking(r) {
    return `<div class="bars">${r.ranking.map((c) => bar(`${c.code} · ${c.name}`, c.probability, c.group)).join("")}</div>`;
  }

  function conformal(r) {
    const c = r.conformal;
    return `<div class="row">${c.set.map((x) => `<span class="tag ${CLASS_GROUP[x]}">${x} · ${e(CLASS_NAMES[x])}</span>`).join("")}</div>
      <p style="margin:12px 0 4px"><b>${e(c.uncertainty || "")}</b></p>
      <p class="muted" style="margin:0">${e(c.advice || "")}</p>
      <p class="muted" style="margin:10px 0 0;font-size:.82rem">This ${e(c.coverage)} prediction set uses a threshold calibrated on held-out rows (patient-grouped splits reached about 91% empirical coverage). The more ambiguous the case, the more classes it contains.</p>`;
  }

  function evidence(r) {
    const ev = r.evidence, mods = r.active_modalities;
    const S = ev.sufficiency, left = Math.max(0, Math.min(1, S)) * 100;
    const stack = mods.map((m) => `<div style="flex:${ev.weights[m]};background:${MOD_COLOR[m]}" title="${MOD[m]} ${fmt.pct(ev.weights[m])}"></div>`).join("");
    const legend = mods.map((m) => `<span><i style="background:${MOD_COLOR[m]}"></i>${MOD[m]} ${fmt.pct(ev.weights[m], 0)}</span>`).join("");
    const rows = mods.map((m) => `<tr><td><b>${MOD[m]}</b></td>
        <td>${fmt.num(ev.quality[m], 2)}</td><td>${fmt.num(ev.reliability[m], 2)}</td><td>${fmt.num(ev.utility[m], 2)}</td>
        <td>${fmt.num(ev.scores[m], 3)}</td><td><b>${fmt.pct(ev.weights[m], 1)}</b></td></tr>`).join("");
    return `
      <h4>Dynamic fusion weights</h4>
      <div class="stackbar" style="margin-top:10px">${stack}</div><div class="legend">${legend}</div>
      <h4 style="margin-top:22px">Evidence sufficiency · S = ${fmt.num(S, 2)}</h4>
      <div class="gauge" style="margin-top:12px"><i style="left:${left}%"></i></div>
      <div class="row spread muted" style="font-size:.78rem;margin-top:6px"><span>&lt;0.30 insufficient</span><span>0.30–0.50 acquire</span><span>≥0.50 proceed</span></div>
      <p class="muted" style="margin:10px 0 0;font-size:.9rem">${e(ev.action)} · cross-modal consistency <b>${fmt.num(ev.consistency, 2)}</b></p>
      <div class="scroll-x" style="margin-top:14px"><table class="t"><thead><tr><th>Source</th><th>Quality Q</th><th>Reliability R</th><th>Utility U</th><th>Evidence E</th><th>Weight</th></tr></thead><tbody>${rows}</tbody></table></div>`;
  }

  function models(r) {
    const rows = r.candidates.map((c) => `<tr class="${r.selected_model === "Model " + c.code ? "hl" : ""}">
        <td><b>${c.code}</b></td><td>${e(c.modality)}</td>
        <td><span class="tag ${CLASS_GROUP[c.predicted]}">${c.predicted}</span></td>
        <td>${fmt.pct(c.confidence)}</td><td>${fmt.num(c.evidence_score, 3)}</td></tr>`).join("");
    return `<p class="muted" style="margin-top:0;font-size:.9rem">Every model whose required inputs are present votes. The highlighted row is the primary model for this input combination.</p>
      <div class="scroll-x"><table class="t"><thead><tr><th>Model</th><th>Inputs</th><th>Prediction</th><th>Confidence</th><th>Evidence</th></tr></thead><tbody>${rows}</tbody></table></div>
      <p class="muted" style="margin:12px 0 0;font-size:.9rem">Agreement: <b>${r.triage.models_agree}/${r.triage.models_total}</b> models match the top prediction.</p>`;
  }

  function next(r) {
    return `<ul class="clean">${r.suggestions.map((s) => `<li>${e(s)}</li>`).join("")}</ul>`;
  }

  /* ---------- agent / RAG sections ---------- */
  function flags(b) {
    if (!b.flags || !b.flags.length) return "";
    return b.flags.map((f) => `<div class="flag ${f.level}"><b>${e(f.label)}</b><span>${e(f.message)}</span></div>`).join("");
  }
  function referral(b) {
    const r = b.referral; if (!r) return "";
    return `<div class="refer ${r.urgency}"><div class="row spread"><b>Suggested: ${e(r.department)}</b>
      <span class="tag ${r.urgency === "routine" ? "benign" : r.urgency === "soon" ? "pre-malignant" : "malignant"}">${e(r.urgency)} · ${e(r.window)}</span></div>
      <p class="muted" style="margin:6px 0 0;font-size:.9rem">${e(r.reason)}</p></div>`;
  }
  function summary(b, role) {
    const rp = b.report; if (!rp) return "";
    const text = role === "doctor" ? rp.clinician_summary : rp.patient_summary;
    const cites = (rp.citations || []).map((c) => `<div class="cite">[${c.n}] ${e(c.title)} › ${e(c.section)}</div>`).join("");
    return `<p style="margin:0 0 6px">${e(text)}</p>${role === "doctor" ? `<p class="muted" style="font-size:.88rem">${e(rp.patient_summary)}</p>` : ""}
      <div class="muted" style="font-size:.74rem;text-transform:uppercase;letter-spacing:.06em;margin-top:10px">Summary mode: ${e(rp.mode)}</div>${cites}`;
  }
  function knowledge(b) {
    const rt = b.retrieval || { chunks: [], similar: { cases: [], distribution: {}, k: 0 } };
    const chunks = rt.chunks.map((c, i) => `<div class="chunk"><h5>[${i + 1}] ${e(c.title)} › ${e(c.section)}</h5><p>${e(c.text)}</p>
      <div class="muted" style="font-size:.72rem;margin-top:6px">relevance ${c.score} · keyword ${c.keyword}${c.semantic != null ? " · semantic " + c.semantic : ""}</div></div>`).join("");
    const sim = rt.similar;
    const dist = Object.entries(sim.distribution || {}).sort((x, y) => y[1] - x[1]);
    const simHtml = sim.k ? `<div class="bars">${dist.map(([c, n]) => bar(`${c} · ${CLASS_NAMES[c] || c}`, n / sim.k, CLASS_GROUP[c] || "", n + " of " + sim.k)).join("")}</div>
      <p class="muted" style="font-size:.82rem;margin:10px 0 0">Nearest documented patients by age, size, body site, sex, skin type and symptoms in the PAD-UFES-20 reference set. These are retrospective look-alikes — not a prediction.</p>`
      : '<p class="muted">No patient details were supplied, so no similar cases could be matched.</p>';
    const dxCode = b.result && b.result.diagnosis ? b.result.diagnosis.code : null;
    const own = b.inputs && b.inputs.has_image && b.case_id
      ? `<div class="sim-card query"><span class="badge">This case</span><img loading="lazy" src="/api/case-image/${b.case_id}" alt="This case"><div class="meta"><b>Your image</b><br>${e(dxCode || "")} predicted</div></div>` : "";
    const gallery = (sim.cases || []).length ? `<div class="sim-grid" style="margin-top:12px">${own}${sim.cases.map((c) => `
      <div class="sim-card ${c.diagnosis === dxCode ? "match" : ""}"><span class="badge">${Math.round(c.similarity * 100)}% similar</span>
        <img loading="lazy" src="/api/sample-image/${encodeURIComponent(c.img_id)}?thumb=true" alt="Reference ${e(c.diagnosis)}" onerror="this.style.visibility='hidden'">
        <div class="meta"><span class="tag ${CLASS_GROUP[c.diagnosis] || ""}">${e(c.diagnosis)}</span> ${e(CLASS_NAMES[c.diagnosis] || "")}
          <div class="muted">${c.age} y${c.sex ? " · " + e(c.sex.toLowerCase()) : ""} · ${e((c.region || "").toLowerCase())}${c.diameter ? " · " + c.diameter + " mm" : ""}</div></div></div>`).join("")}</div>
      <p class="muted" style="font-size:.8rem;margin:8px 0 0">Green outline: the documented patient had the same diagnosis as the AI's top class.</p>` : "";
    return `<h4>Knowledge retrieved for this case</h4><div style="margin-top:10px">${chunks || '<p class="muted">Nothing retrieved.</p>'}</div>
      <h4 style="margin-top:18px">Similar documented cases</h4><div style="margin-top:10px">${simHtml}</div>${gallery}`;
  }

  /* ---------- agent score + model score ---------- */
  const mini = (v, cls) => `<div class="row" style="gap:8px;flex-wrap:nowrap"><div class="track" style="flex:1;height:8px"><div class="fill ${cls}" style="width:${Math.round(v * 100)}%"></div></div><b>${Math.round(v * 100)}</b></div>`;
  const ringC = (v) => (v >= 0.7 ? "var(--ok)" : v >= 0.5 ? "var(--warn)" : "var(--bad)");
  const ring = (v) => `<div class="ring" style="--p:${v * 100};--ringc:${ringC(v)};width:84px;height:84px"><span style="font-size:1.05rem">${Math.round(v * 100)}</span></div>`;

  function scoreStrip(b) {
    const s = b.scores; if (!s) return "";
    const chip = (l, v) => `<span class="sc"><i class="dot" style="background:${ringC(v)};width:10px;height:10px;border-radius:50%;display:inline-block"></i>${l} <b>${Math.round(v * 100)}</b></span>`;
    return `<div class="scorestrip">${chip("AI-agent score", s.agent_score)}${chip("Model score", s.model_score)}${chip("Combined", s.combined)}</div>`;
  }

  function scoresPanel(b) {
    const s = b.scores;
    if (!s) return '<p class="muted">Agent scores were not recorded for this older case. Run a new analysis to see them.</p>';
    const agents = s.agents.map((a) => `<tr><td><b>${e(a.agent)}</b></td>
        <td style="min-width:150px">${mini(a.score, a.score >= 0.7 ? "benign" : a.score >= 0.5 ? "pre-malignant" : "malignant")}</td>
        <td>${Math.round(a.weight * 100)}%</td><td>${a.ms} ms</td><td class="muted" style="font-size:.84rem">${e(a.basis)}</td></tr>`).join("");
    const models = s.models.map((m) => `<tr class="${m.selected ? "hl" : ""}"><td><b>Model ${e(m.code)}</b>${m.selected ? ' <span class="tag brand">primary</span>' : ""}</td>
        <td>${e(m.modality)}</td><td><span class="tag ${CLASS_GROUP[m.predicted] || ""}">${e(m.predicted)}</span></td>
        <td style="min-width:140px">${mini(m.confidence, CLASS_GROUP[m.predicted] || "")}</td>
        <td>${fmt.num(m.evidence_score, 3)}</td></tr>`).join("");
    return `<div class="scoregrid">
        <div class="scorecard">${ring(s.agent_score)}<b>AI-agent score</b><span class="sub">how well the 6 agents did their jobs</span></div>
        <div class="scorecard">${ring(s.model_score)}<b>Model score</b><span class="sub">confidence + held-out accuracy of Model ${e(s.selected_model)}</span></div>
        <div class="scorecard">${ring(s.combined)}<b>Combined · ${e(s.level)}</b><span class="sub">assurance index (0–100)</span></div>
      </div>
      <h4 style="margin-top:22px">AI agents</h4>
      <div class="scroll-x"><table class="t"><thead><tr><th>Agent</th><th>Score</th><th>Weight</th><th>Time</th><th>What the score measures</th></tr></thead><tbody>${agents}</tbody></table></div>
      <h4 style="margin-top:22px">Models</h4>
      <div class="scroll-x"><table class="t"><thead><tr><th>Model</th><th>Inputs</th><th>Predicts</th><th>Confidence</th><th>Evidence</th></tr></thead><tbody>${models}</tbody></table></div>
      <div class="callout info" style="margin-top:14px;font-size:.84rem"><b>How to read this.</b>
        Agent score = ${e(s.formula.agent)}. Model score = ${e(s.formula.model)}. Combined = ${e(s.formula.combined)}.
        Agent scores describe process quality (input completeness, guardrails, retrieval support); model scores describe prediction confidence.
        None of them is the probability that the diagnosis is correct.</div>`;
  }
  function agentsTl(b) {
    const steps = b.agents || [];
    return `<p class="muted" style="margin-top:0;font-size:.9rem">Each specialist agent reports to the orchestrator. Total ${steps.reduce((a, s) => a + s.ms, 0)} ms.</p>
      <div class="timeline">${steps.map((s) => `<div class="tl-item ${s.ok ? "" : "fail"}"><div><span class="who">${e(s.agent)}</span><span class="ms">${s.ms} ms</span></div>
        <div class="what">${e(s.action)}</div><div class="out">${e(s.detail)}</div></div>`).join("")}</div>`;
  }
  function extracted(b) {
    const x = b.extracted || (b.inputs && b.inputs.extracted_from_text) || {};
    const keys = Object.keys(x);
    if (!keys.length) return "";
    return `<div class="callout info" style="margin-top:12px">Intake agent read these details from the description: ${keys.map((k) => `<b>${e(k.replace(/_/g, " "))}</b> = ${e(x[k])}`).join(", ")}.</div>`;
  }


  /* ---------- lesion morphology, explanation audit, acquisition ---------- */
  function morphKpi(label, v) { return `<div class="kpi"><b>${v}</b><span>${label}</span></div>`; }

  function lesionPanel(b) {
    const m = b.morphology, a = b.acquisition, au = b.explanation_audit, id = b.case_id;
    let html = "";
    if (m && m.status && m.status !== "failed") {
      const cols = (m.dominant_colours || []).map((c) => `<span class="swatch" title="${Math.round(c.share * 100)}%" style="background:${c.hex}"></span>`).join("");
      html += `<h4>Lesion segmentation &amp; morphology</h4>
        <div class="img-pair" style="margin-top:10px"><figure><img src="/api/case-image/${id}" alt="Photo"><figcaption>Photo</figcaption></figure>
          <figure><img src="/api/case-image/${id}?overlay=true" alt="Segmentation"><figcaption>Segmented lesion (${e(m.model_version)}, quality ${fmt.num(m.segmentation_quality, 2)})</figcaption></figure></div>
        <div class="morph-grid" style="margin-top:12px">
          ${morphKpi("Area (% of image)", (m.area_fraction * 100).toFixed(1) + "%")}${morphKpi("Diameter (px)", m.diameter_px)}
          ${morphKpi("Circularity", m.circularity)}${morphKpi("Asymmetry", m.asymmetry)}
          ${morphKpi("Convexity", m.convexity ?? "—")}${morphKpi("Colour variation", m.colour_variation)}</div>
        <div class="row" style="margin-top:10px"><span class="muted" style="font-size:.84rem">Dominant colours</span><div class="swatches">${cols}</div></div>
        <p class="muted" style="font-size:.82rem;margin:8px 0 0">${e(m.note)} Pixel units only — no physical scale.${m.status === "low_quality" ? " <b>Low segmentation confidence: treat these numbers with caution.</b>" : ""}</p>`;
    } else if (m) {
      html += `<div class="callout">The lesion could not be segmented automatically for this image.</div>`;
    }
    html += `<h4 style="margin-top:22px">Explanation audit</h4><div id="auditBox" style="margin-top:10px">${auditHtml(au, id)}</div>`;
    if (a) {
      html += `<h4 style="margin-top:22px">What would help most? (cost-aware acquisition)</h4>
        <p style="margin:8px 0">${a.recommended ? `<b>Recommended:</b> ${e(a.recommended_label)}` : e(a.recommended_label)}</p>
        <div class="scroll-x"><table class="t"><thead><tr><th>Action</th><th>Expected gain ΔV</th><th>Cost</th><th>Delay</th><th>Score</th><th>Basis</th></tr></thead><tbody>
        ${a.ranked.map((x) => `<tr class="${x.action === a.recommended ? "hl" : ""}"><td>${e(x.label)}</td><td>${(x.delta_v * 100).toFixed(1)} pts</td>
          <td>${x.cost}</td><td>${x.delay_days} d</td><td><b>${x.score.toFixed(3)}</b></td><td class="muted">${e(x.basis)}</td></tr>`).join("")}</tbody></table></div>
        <p class="muted" style="font-size:.82rem;margin:8px 0 0">Score = ΔV − ${a.lambda}·cost − ${a.mu}·delay days. ${e(a.note)}</p>`;
    }
    return html || '<p class="muted">No image was supplied, so there is no lesion analysis.</p>';
  }

  function auditHtml(au, id) {
    if (!au) {
      return `<p class="muted" style="margin:0 0 10px;font-size:.9rem">Checks whether the image model looks at the lesion (rather than the background) and whether its answer survives flips and brightness changes. Takes about 10 s.</p>
        <button class="btn btn-ghost btn-sm" id="auditBtn" data-case="${id}">Run explanation audit</button>`;
    }
    const grid = au.attribution.map((row) => row.map((v) => {
      const t = Math.min(1, v / (au.max_drop || 1)); return `<div style="background:rgba(13,148,136,${(0.08 + 0.9 * t).toFixed(2)});color:${t > .55 ? "#fff" : "var(--text)"}">${(v * 100).toFixed(0)}</div>`;
    }).join("")).join("");
    return `<div class="row" style="gap:8px;margin-bottom:10px"><span class="tag ${au.status === "ok" ? "benign" : "pre-malignant"}">${au.status === "ok" ? "no concerns flagged" : "review required"}</span>
        ${au.flags.map((f) => `<span class="tag malignant">${e(f.replace(/_/g, " "))}</span>`).join("")}</div>
      <div class="img-pair"><figure><img src="/api/case-audit-image/${id}?t=${Date.now()}" alt="Occlusion heat map"><figcaption>Occlusion sensitivity (brighter = prediction drops more when hidden)</figcaption></figure>
        <div><div class="grid-heat" style="grid-template-columns:repeat(${au.grid},1fr)">${grid}</div>
        <div class="morph-grid" style="margin-top:12px">
          ${morphKpi("Mass on lesion", au.lesion_region_overlap == null ? "—" : Math.round(au.lesion_region_overlap * 100) + "%")}
          ${morphKpi("Stable under flips/brightness", Math.round(au.stability * 100) + "%")}
          ${morphKpi("Largest drop", (au.max_drop * 100).toFixed(1) + " pts")}</div></div></div>
      <p class="muted" style="font-size:.82rem;margin:8px 0 0">${e(au.caveat)}</p>`;
  }

  document.addEventListener("click", async (ev) => {
    const btn = ev.target.closest("#auditBtn"); if (!btn) return;
    btn.disabled = true; btn.innerHTML = '<span class="spinner dark" style="width:14px;height:14px;display:inline-block"></span> Auditing…';
    try {
      const out = await api(`/api/cases/${btn.dataset.case}/explanation-audit`, { method: "POST" });
      document.getElementById("auditBox").innerHTML = auditHtml(out, btn.dataset.case);
    } catch (err) { btn.disabled = false; btn.textContent = "Run explanation audit"; toast(err.message, "bad"); }
  });

  window.ResultView = {
    triage, diagnosis, ranking, conformal, evidence, models, next, flags, referral, summary, knowledge, agentsTl, lesionPanel, scoresPanel, scoreStrip,

    /** Tabbed view for the interactive workspace (b = analyze() bundle). */
    tabbed(b, opts = {}) {
      const r = b.result; r.case_id = b.case_id; const role = opts.role || "patient";
      if (!b.case_id) b.case_id = r.case_id;
      return `${flags(b)}${triage(r)}${scoreStrip(b)}
        <div class="card flat" style="margin-top:16px">${diagnosis(r)}</div>
        <div class="card flat" style="margin-top:16px" id="resTabs">
          <div class="tabs">
            <button class="tab on" data-pane="p-sum">Summary</button>
            <button class="tab" data-pane="p-prob">Probabilities</button>
            <button class="tab" data-pane="p-evid">Evidence</button>
            <button class="tab" data-pane="p-models">Models</button>
            <button class="tab" data-pane="p-scores">AI scores</button>
            <button class="tab" data-pane="p-know">Knowledge (RAG)</button>
            <button class="tab" data-pane="p-les">Lesion &amp; follow-up</button>
            <button class="tab" data-pane="p-agents">Agents</button>
          </div>
          <div class="pane on" id="p-sum">${summary(b, role)}${extracted(b)}<div style="margin-top:16px">${referral(b)}</div>
            <h4 style="margin-top:20px">Next steps</h4><div style="margin-top:6px">${next(r)}</div></div>
          <div class="pane" id="p-prob">${ranking(r)}<h4 style="margin-top:22px">Conformal prediction set</h4><div style="margin-top:10px">${conformal(r)}</div></div>
          <div class="pane" id="p-evid">${evidence(r)}</div>
          <div class="pane" id="p-models">${models(r)}</div>
          <div class="pane" id="p-scores">${scoresPanel(b)}</div>
          <div class="pane" id="p-know">${knowledge(b)}</div>
          <div class="pane" id="p-les">${lesionPanel(b)}</div>
          <div class="pane" id="p-agents">${agentsTl(b)}</div>
        </div>
        <div class="row no-print" style="margin-top:16px" id="resActions">
          <a class="btn btn-ghost btn-sm" href="/report?id=${r.case_id}" target="_blank">${icon("print", 16)} Open case &amp; report</a>
          <span class="muted" style="font-size:.82rem">Model ${r.selected_model.replace("Model ", "")} · ${r.inference_seconds}s · case ${r.case_id}</span>
        </div>`;
    },

    /** Linear view for the case/report page. */
    full(b, role = "patient") {
      const r = b.result;
      const sec = (t, body) => `<div class="card" style="margin-top:16px"><h4>${t}</h4><div style="margin-top:12px">${body}</div></div>`;
      return `${flags(b)}${triage(r)}${scoreStrip(b)}
        ${sec("Primary finding", diagnosis(r))}
        ${sec("AI-agent score &amp; model score", scoresPanel(b))}
        ${sec("Summary", summary(b, role) + extracted(b) + `<div style="margin-top:14px">${referral(b)}</div>`)}
        ${sec("Class probabilities", ranking(r))}
        ${sec("Conformal prediction set", conformal(r))}
        ${sec("Evidence profile", evidence(r))}
        ${sec("Candidate models", models(r))}
        ${sec("Retrieved knowledge & similar cases", knowledge(b))}
        ${sec("Lesion morphology, explanation audit & acquisition", lesionPanel(b))}
        ${sec("Recommended next steps", next(r))}
        <div class="no-print">${sec("Agent activity", agentsTl(b))}</div>`;
    },
  };
})();

# 10 — Frontend: the Hospital Web Portal

Code: `app/static/` — plain HTML pages + `css/style.css` (460 lines) + three small JS files
(`common.js`, `diagnose.js`, `result.js`). No build step, no framework.

## 1. Why vanilla HTML/CSS/JS

| Reason | Detail |
|--------|--------|
| Zero tooling | No Node, bundler or `npm install`; the FastAPI server simply serves files |
| Easy to demo and audit | Every behaviour is in a few readable files |
| Fast | No framework payload; pages load instantly on a laptop |
| Sufficient | The UI is forms + result rendering + tables; a SPA framework would add complexity without benefit |
| Same-origin | Calls the API relative to the page, so cookies and CSRF header "just work" |

## 2. Pages

| Page | File | Audience | Purpose |
|------|------|----------|---------|
| Home | `index.html` | all | Landing: "AI-assisted skin triage" |
| Register | `register.html` / `login.html` | visitors | Name + email join |
| Dashboard | `dashboard.html` | role-specific | Patient: cases/pending/upcoming; Doctor: review queue, today's appointments; Admin: user counts, action mix, logins |
| **Diagnose** | `diagnose.html` + `diagnose.js` | patient | Upload photo, enter details, write/generate description, pick model or "automatic", try dataset samples |
| **Case report** | `report.html` + `result.js` | patient / doctor | Full result: diagnosis, probabilities, conformal set, evidence, agents, RAG, referral, report, review |
| Cases | `history.html` | patient / doctor | List and filter cases |
| Lesion tracking | `lesions.html` | patient | Timeline of observations, simulated follow-up, change alerts |
| Appointments | `appointments.html` | patient / doctor | Book and manage slots |
| Doctors | `doctors.html` | all | Directory by department |
| **Evidence & performance** | `performance.html` | all | Measured vs. reported accuracy, calibration, conformal, subgroups, benchmark figures |
| **DERMA-STRESS** | `stress.html` | staff | Launch/inspect robustness benchmarks |
| How it works | `how-it-works.html` | all | Plain-language explanation of the pipeline |
| Safety & limits | `safety.html` | all | Disclaimers and known limitations |
| Documentation | `documentation.html` | all | In-app viewer of project docs |
| Account | `account.html` | all | Profile, password |
| Admin | `admin.html` | admin | Accounts and audit log |

## 3. The diagnose → result flow

1. **Diagnose page** — the user can add any mix of inputs. A live **image-quality check** (`/api/quality`: blur,
   brightness, contrast, resolution) gives instant feedback before analysis. A **"Generate description"** button calls
   `/api/generate-text` to turn metadata into a narrative and show its PTIS.
2. **Analyse** → `POST /api/analyze` (multipart). Errors (503 loading, 400 missing inputs, 429 too many pending) are
   shown inline.
3. **Result page** renders, in order:
   * headline diagnosis + group badge (malignant / pre-malignant / benign) + calibrated confidence;
   * triage banner (ACCEPT / ARBITRATE / ACQUIRE / ESCALATE) with reasons;
   * safety flags (emergency, suspected malignancy, weak evidence);
   * class probability bars and the **conformal set**;
   * **evidence panel** — Q, R, U per modality, C, S, gate, dynamic fusion weights;
   * **candidate-model panel** — each feasible model's prediction, confidence, evidence score, held-out accuracy
     (text-dependent models are marked unvalidated);
   * **agent trace and agent scores** next to **model scores**;
   * **RAG panel** — cited knowledge chunks and look-alike patients with thumbnails;
   * referral (department, urgency, window);
   * morphology overlay and acquisition ranking;
   * patient and clinician summaries; "Request doctor review" and appointment links.

## 4. Role-aware navigation

`common.js` fetches `/api/auth/me` and builds the top bar from the role. Patient sessions show a
**Patient / Doctor / Admin switch** (demo convenience) so one person can submit a case and then review it as a doctor.
All state-changing fetches add `X-Requested-With: dg-web` (CSRF header).

## 5. UX principles

* **Honest labelling** — every number shows what it is (calibrated vs. raw, measured vs. heuristic, validated vs.
  unvalidated).
* **Plain language first, detail on demand** — patient summary on top, evidence tables below.
* **Safety visible** — disclaimers on every result; emergency wording is surfaced before the diagnosis.
* **White, clean theme** — high contrast, minimal colour except risk badges.
* **No sign-in friction** in demo mode (see `09_...` for the trade-off).

## 6. Streamlit apps (secondary UIs)

| App | File | Port | Purpose |
|-----|------|:----:|---------|
| Patient app | `app/patient_app.py` | 8501 | Upload form, status timeline, result view (talks to the legacy `/predict` API) |
| Clinician console | `app/clinician_console.py` | 8502 | Evidence radar, model-confidence heat-map, pipeline trace, system metrics (Plotly) |

The README refers to the clinician file as `clinician_app.py`; the file in the repository is `clinician_console.py`.

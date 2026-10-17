# 09 — Backend: API, Database and Security

Code: `src/main.py` (1,249 lines), `src/services/auth.py`, `db.py`, `scheduling.py`.

## 1. Server

* **FastAPI** application `app` (title "DERMA-GUARD API + portal", version 4.1.0) served by **Uvicorn**.
* Serves both the JSON API and the static website (`app/static`) from the same origin → no CORS configuration, cookies
  are first-party, one command to run.
* Auto-generated OpenAPI docs at `/api/docs`.
* A middleware adds `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: same-origin`,
  `Cache-Control: no-store` for `/api/*` and `no-cache` for pages/static files.

## 2. Endpoint catalogue

### System
| Method & path | Purpose |
|---------------|---------|
| `GET /api/status` | Engine state, device, RAG state, LLM availability |
| `GET /api/v1/health` | Spec-style health |

### Authentication & accounts
| Method & path | Purpose |
|---------------|---------|
| `POST /api/auth/join` | **Passwordless** patient registration (name + email) — the web UI's only sign-up route |
| `POST /api/auth/register` | Password registration (policy: ≥ 8 chars, letter + digit) |
| `POST /api/auth/login` / `logout` | Password sign-in (used by scripts and staff demo accounts) |
| `POST /api/auth/switch` | Demo role switch patient ⇄ doctor ⇄ admin (patient-origin sessions only) |
| `GET /api/auth/me` | Current user + whether switching is available |
| `POST /api/auth/password` | Change password (invalidates other sessions) |

### Cases (the core workflow)
| Method & path | Purpose |
|---------------|---------|
| `POST /api/quality` | Instant image-quality pre-check (no model) |
| `POST /api/generate-text` | Generate a clinical narrative + PTIS from metadata |
| `GET /api/samples`, `/api/sample-image/{id}` | Demo samples from the dataset (4 per class) |
| `POST /api/analyze` | **Run the full agent pipeline** and store the case |
| `GET /api/cases?scope=mine|assigned|all` | List cases (role-aware) |
| `GET /api/cases/{id}` / `DELETE` | Case detail / owner deletion |
| `GET /api/case-image/{id}` | Uploaded image or segmentation overlay |
| `POST /api/cases/{id}/request-review` | Patient assigns a doctor → status `pending_review` |
| `POST /api/cases/{id}/review` | Doctor records the final decision → status `reviewed` |
| `POST /api/cases/{id}/explanation-audit` | Occlusion-based explanation audit |
| `GET/POST /api/lesions`, `…/{id}/timeline`, `…/simulate-followup` | Longitudinal lesion tracking |

### Appointments, chat, dashboards, admin
| Method & path | Purpose |
|---------------|---------|
| `GET /api/doctors`, `GET /api/slots?doctor_id=` | Directory and free slots |
| `GET/POST/PATCH /api/appointments` | Booking and status changes |
| `POST/GET/DELETE /api/chat…` | Assistant conversation |
| `GET /api/dashboard` | Role-specific summary |
| `GET/POST/PATCH /api/admin/users`, `GET /api/admin/audit` | Account management and audit log |

### Evidence & documentation
| Method & path | Purpose |
|---------------|---------|
| `GET /api/evaluation`, `/api/benchmarks`, `/api/dataset`, `/api/artifact/{model}/{name}` | Honest metrics, original benchmark, dataset stats, figures |
| `GET /api/docs-index`, `/api/docs-content/{id}` | In-app documentation viewer |
| `POST/GET /api/v1/benchmarks/stress…` | Run / list **DERMA-STRESS** (async 202) |

### Spec API contract (`/api/v1`) and legacy
| Method & path | Purpose |
|---------------|---------|
| `POST /api/v1/cases` (202) | Asynchronous case submission |
| `GET /api/v1/cases/{id}` / `…/trace` | State and evidence trace |
| `POST /api/v1/cases/{id}/clinician-action` | Clinician action |
| `POST /predict`, `GET /case/{id}`, `/cases`, `/metrics`, `/health` | Legacy v4.0 endpoints (Streamlit apps) |

## 3. Input sanitisation (`_open_image`, `_parse_metadata`)

| Check | Rule |
|-------|------|
| Size | ≤ 10 MB (413 otherwise) |
| Type | Magic bytes must be JPEG (`FF D8 FF`) or PNG; explicit rejection of `MZ`, `%PDF`, `<?php`, `<script`, ELF headers |
| Decode | Must open as an image with Pillow |
| Dimensions | 32–4096 px per side |
| Metadata | JSON object; only the 17 whitelisted fields; `UNK`/empty dropped; values cleaned/typed |
| Text | trimmed to 2,000 chars |
| Rate guard | max **5 pending** cases per user (429) |
| Model choice | `A–G`; rejected with a clear message if the required inputs are missing |

## 4. Database (SQLite, `outputs/portal/hospital.db`)

Opened per call with `PRAGMA foreign_keys=ON` and **WAL** journal mode; JSON blobs stored as text with `jdump/jload`.

```
users(id, email UNIQUE, name, role ∈ {patient,doctor,admin}, password_hash, department, specialty, bio,
      active, failed_attempts, locked_until, created, last_login)
sessions(token_hash PK, user_id → users, created, expires, ip, ua, origin_id)
cases(id PK, owner_id → users, doctor_id → users, created, source, truth, has_image,
      status ∈ {ai_only, pending_review, reviewed}, inputs, result, agents, review,
      lesion_id, observed_at, simulated)
appointments(id, patient_id, doctor_id, slot 'YYYY-MM-DDTHH:MM', reason, case_id, status, doctor_note, created)
      UNIQUE(doctor_id, slot) WHERE status IN ('booked','confirmed')      -- no double booking
audit(id, ts, user_id, email, action, target, ip, detail)
lesions(id, owner_id, label, body_site, created)
stress_runs(id, created, user_id, status, progress, params, results, error)
chat(id, user_id, ts, role, content, meta)
```

* `init()` performs lightweight forward migration (`ALTER TABLE … ADD COLUMN`) for newer columns.
* **Why SQLite:** zero-install, a single file, transactional, adequate for a single-process demo; replacing it with
  PostgreSQL is a documented step (`docs/v5_extension_notes.md`).

## 5. Case lifecycle

```
ai_only ──(patient requests review, picks doctor)──► pending_review ──(doctor submits decision)──► reviewed
```

* A doctor **cannot review their own case**.
* The final decision (`agree` / `override` etc., final diagnosis code, notes) is stored in `cases.review` and shown to
  the patient.
* Doctors see all cases (queue sorted: pending first, then by triage level); admins are explicitly denied clinical
  content (403).

## 6. Authentication and authorisation (`auth.py`)

| Mechanism | Detail |
|-----------|--------|
| Password hashing | `hashlib.scrypt` (N=2¹⁴, r=8, p=1), 16-byte random salt, constant-time `hmac.compare_digest` |
| Passwordless accounts | Stored hash `open$…`; `verify_password` always returns False → such accounts can **never** sign in with a password |
| Sessions | 256-bit random token in an **HttpOnly, SameSite=Lax** cookie `dg_session`; only SHA-256 of the token stored; TTL 7 days |
| Brute-force | 5 failed attempts → account locked for 10 minutes; timing equalisation for unknown emails |
| CSRF | Every state-changing request must carry header `X-Requested-With: dg-web`; cross-site forms cannot set it. SameSite=Lax is the second layer |
| RBAC | `require("patient","doctor")`, `Doc`, `Admin`, `Staff` dependencies + object-level checks (owner / assigned doctor) |
| Audit | Every sensitive action (`login`, `login_failed`, `register`, `case_create`, `review_requested`, `role_switch`, `password_change`…) is written to `audit` |
| Seeded demo accounts | 1 admin, 3 doctors (Oncology, Surgery, General Dermatology), 1 patient; random passwords written once to `outputs/portal/DEMO_CREDENTIALS.txt` |

### Demo-mode trade-off (explicit in the README)
Passwordless registration and role switching exist so one person can demonstrate both the patient and doctor views.
They are **not** suitable for real patient data. Before real use: restore password sign-in, remove `/api/auth/join` and
`/api/auth/switch`, use HTTPS (`Secure` cookies), and move off SQLite/local file storage.

## 7. Scheduling (`scheduling.py`)

* Open days Mon–Fri; slots every 30 min, 09:00–12:30 and 14:00–16:30; 14-day horizon; slots less than 2 h ahead are
  hidden; `valid_slot()` re-validates server-side; uniqueness enforced by a partial unique index.

## 8. Privacy notes

* Uploaded images are stored as ≤ 640 px JPEG thumbnails under `outputs/portal/uploads/`; owners can delete a case.
* Admin role cannot read clinical content.
* The research paper's platform description also mentions a record-deletion capability and append-only audit log.
* No images or free text are sent to any third party; the optional LLM is local (Ollama).

"""
website/auth.py — authentication & authorisation.

* Passwords: scrypt (stdlib) with a per-user random salt, constant-time compare.
* Sessions: 256-bit random token in an HttpOnly, SameSite=Lax cookie; only the
  SHA-256 of the token is stored server-side, so a DB leak cannot hijack sessions.
* Brute force: 5 failed sign-ins lock the account for 10 minutes.
* CSRF: every state-changing request must carry the `X-Requested-With: dg-web`
  header, which cross-site forms cannot set; SameSite=Lax is the second layer.
* RBAC: `require(...)` dependency + object-level checks in the routes.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
import time
from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, Request, Response

from src.services import db

COOKIE = "dg_session"
SESSION_TTL = 7 * 24 * 3600
MAX_FAILS = 5
LOCK_SECONDS = 600
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")


# ------------------------------------------------------------------ passwords
def hash_password(pw: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.scrypt(pw.encode(), salt=salt, n=2 ** 14, r=8, p=1, dklen=32)
    return f"scrypt${salt.hex()}${dk.hex()}"


OPEN_HASH = "open$"     # passwordless patient account created through /api/auth/join


def verify_password(pw: str, stored: str) -> bool:
    if stored.startswith(OPEN_HASH):
        return False                                   # such accounts can never sign in with a password
    try:
        _, salt, dk = stored.split("$")
        calc = hashlib.scrypt(pw.encode(), salt=bytes.fromhex(salt), n=2 ** 14, r=8, p=1, dklen=32)
        return hmac.compare_digest(calc.hex(), dk)
    except Exception:
        return False


def password_problem(pw: str) -> Optional[str]:
    if len(pw) < 8:
        return "Password must be at least 8 characters."
    if not re.search(r"[A-Za-z]", pw) or not re.search(r"\d", pw):
        return "Password must contain at least one letter and one digit."
    if len(pw) > 128:
        return "Password is too long."
    return None


# ------------------------------------------------------------------ sessions
def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def client_ip(request: Request) -> str:
    return request.client.host if request.client else ""


def login(email: str, password: str, request: Request, response: Response) -> Dict[str, Any]:
    email = email.strip().lower()
    user = db.one("SELECT * FROM users WHERE email = ?", (email,))
    ip = client_ip(request)
    generic = HTTPException(401, "Invalid email or password.")
    if user is None:
        verify_password(password, "scrypt$00$00")   # equalise timing
        db.audit(None, "login_failed", email, ip, "unknown account")
        raise generic
    if user["locked_until"] > time.time():
        mins = int((user["locked_until"] - time.time()) / 60) + 1
        raise HTTPException(423, f"Account temporarily locked. Try again in about {mins} min.")
    if not user["active"]:
        db.audit(user, "login_blocked", email, ip, "deactivated")
        raise HTTPException(403, "This account has been deactivated. Contact an administrator.")
    if not verify_password(password, user["password_hash"]):
        fails = user["failed_attempts"] + 1
        lock = time.time() + LOCK_SECONDS if fails >= MAX_FAILS else 0
        db.run("UPDATE users SET failed_attempts=?, locked_until=? WHERE id=?",
               (0 if lock else fails, lock, user["id"]))
        db.audit(user, "login_failed", email, ip, f"attempt {fails}")
        raise generic

    db.run("UPDATE users SET failed_attempts=0, locked_until=0, last_login=? WHERE id=?", (time.time(), user["id"]))
    token = secrets.token_urlsafe(32)
    now = time.time()
    db.run("INSERT INTO sessions(token_hash,user_id,created,expires,ip,ua,origin_id) VALUES (?,?,?,?,?,?,?)",
           (_hash(token), user["id"], now, now + SESSION_TTL, ip, request.headers.get("user-agent", "")[:200], user["id"]))
    response.set_cookie(COOKIE, token, max_age=SESSION_TTL, httponly=True, samesite="lax", path="/")
    db.audit(user, "login", email, ip)
    return public_user(user)


def _new_session(user_id: int, origin_id: int, request: Request, response: Response) -> None:
    token = secrets.token_urlsafe(32)
    now = time.time()
    db.run("INSERT INTO sessions(token_hash,user_id,created,expires,ip,ua,origin_id) VALUES (?,?,?,?,?,?,?)",
           (_hash(token), user_id, now, now + SESSION_TTL, client_ip(request), request.headers.get("user-agent", "")[:200], origin_id))
    response.set_cookie(COOKIE, token, max_age=SESSION_TTL, httponly=True, samesite="lax", path="/")


def join(name: str, email: str, request: Request, response: Response) -> Dict[str, Any]:
    """Patient registration without a password. An existing *passwordless* patient with the same
    email is resumed; accounts that have a password (or are staff) can never be taken over this way."""
    email = email.strip().lower()
    if not EMAIL_RE.match(email):
        raise HTTPException(400, "Enter a valid email address.")
    user = db.one("SELECT * FROM users WHERE email = ?", (email,))
    if user is None:
        uid = db.run("INSERT INTO users(email,name,role,password_hash,created,last_login) VALUES (?,?,?,?,?,?)",
                     (email, name.strip(), "patient", OPEN_HASH + secrets.token_hex(8), time.time(), time.time()))
        user = db.one("SELECT * FROM users WHERE id = ?", (uid,))
        db.audit(user, "register", email, client_ip(request), "passwordless patient")
    elif user["role"] != "patient" or not user["password_hash"].startswith(OPEN_HASH):
        raise HTTPException(409, "That email belongs to a protected account. Use a different email.")
    elif not user["active"]:
        raise HTTPException(403, "This account has been deactivated.")
    else:
        db.run("UPDATE users SET last_login=? WHERE id=?", (time.time(), user["id"]))
        db.audit(user, "resume", email, client_ip(request))
    _new_session(user["id"], user["id"], request, response)
    return public_user(user)


def switch_role(request: Request, response: Response, role: str, doctor_id: Optional[int] = None) -> Dict[str, Any]:
    """Move the current session between the patient's own account and a doctor / admin view."""
    token = request.cookies.get(COOKIE)
    sess = db.one("SELECT * FROM sessions WHERE token_hash=? AND expires>?", (_hash(token or ""), time.time()))
    if not sess:
        raise HTTPException(401, "Please register first.")
    origin_id = sess.get("origin_id")
    origin = db.one("SELECT * FROM users WHERE id=?", (origin_id,)) if origin_id else None
    if not origin or origin["role"] != "patient":
        raise HTTPException(403, "Role switching is only available to self-registered patient sessions.")
    if role == "patient":
        target = origin
    elif role == "doctor":
        if doctor_id:
            target = db.one("SELECT * FROM users WHERE id=? AND role='doctor' AND active=1", (doctor_id,))
        else:
            target = db.one("SELECT * FROM users WHERE role='doctor' AND active=1 ORDER BY id LIMIT 1")
    elif role == "admin":
        target = db.one("SELECT * FROM users WHERE role='admin' AND active=1 ORDER BY id LIMIT 1")
    else:
        raise HTTPException(400, "role must be patient, doctor or admin.")
    if not target:
        raise HTTPException(404, f"No {role} account is available.")
    db.run("UPDATE sessions SET user_id=? WHERE token_hash=?", (target["id"], _hash(token)))
    db.audit(origin, "role_switch", target["email"], client_ip(request), role)
    return public_user(target)


def logout(request: Request, response: Response, user: Optional[Dict[str, Any]]) -> None:
    token = request.cookies.get(COOKIE)
    if token:
        db.run("DELETE FROM sessions WHERE token_hash = ?", (_hash(token),))
    response.delete_cookie(COOKIE, path="/")
    if user:
        db.audit(user, "logout", user["email"], client_ip(request))


def public_user(u: Dict[str, Any]) -> Dict[str, Any]:
    return {k: u.get(k) for k in ("id", "email", "name", "role", "department", "specialty", "bio", "created", "last_login")}


# ------------------------------------------------------------------ dependencies
def optional_user(request: Request) -> Optional[Dict[str, Any]]:
    token = request.cookies.get(COOKIE)
    if not token:
        return None
    row = db.one(
        "SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id "
        "WHERE s.token_hash = ? AND s.expires > ? AND u.active = 1", (_hash(token), time.time()))
    return row


def csrf_guard(request: Request) -> None:
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        if request.headers.get("x-requested-with") != "dg-web":
            raise HTTPException(403, "Missing CSRF header.")


def current_user(request: Request, _: None = Depends(csrf_guard)) -> Dict[str, Any]:
    user = optional_user(request)
    if user is None:
        raise HTTPException(401, "Please sign in.")
    return user


def require(*roles: str):
    def dep(user: Dict[str, Any] = Depends(current_user)) -> Dict[str, Any]:
        if user["role"] not in roles:
            raise HTTPException(403, "You do not have permission to do that.")
        return user
    return dep


def purge_expired() -> None:
    db.run("DELETE FROM sessions WHERE expires < ?", (time.time(),))


# ------------------------------------------------------------------ seeding
DEMO_USERS = [
    ("admin@healthsphere.demo", "Hospital Administrator", "admin", None, None, None),
    ("dr.rao@healthsphere.demo", "Dr. Anita Rao", "doctor", "Dermatologic Oncology", "Melanoma & skin cancer",
     "Leads the skin-cancer clinic; 14 years of dermoscopy and mole-mapping experience."),
    ("dr.mehta@healthsphere.demo", "Dr. Karan Mehta", "doctor", "Dermatologic Surgery", "Mohs & excision surgery",
     "Performs Mohs micrographic surgery and complex excisions of facial skin cancers."),
    ("dr.iyer@healthsphere.demo", "Dr. Sunita Iyer", "doctor", "General Dermatology", "Medical dermatology",
     "General clinic: rashes, pigmentary disorders, actinic keratosis and everyday skin concerns."),
    ("patient@healthsphere.demo", "Demo Patient", "patient", None, None, None),
]


def seed_demo() -> Optional[str]:
    """Create demo accounts on a fresh database. Returns the credentials text."""
    if db.one("SELECT 1 AS x FROM users LIMIT 1"):
        return None
    lines = ["DEMO ACCOUNTS (change or deactivate these before any real use)", ""]
    for email, name, role, dept, spec, bio in DEMO_USERS:
        pw = "Demo-" + secrets.token_urlsafe(6) + "9"
        db.run("INSERT INTO users(email,name,role,password_hash,department,specialty,bio,created) VALUES (?,?,?,?,?,?,?,?)",
               (email, name, role, hash_password(pw), dept, spec, bio, time.time()))
        lines.append(f"{role:8s} {email:32s} {pw}")
    text = "\n".join(lines) + "\n"
    (db.STORAGE / "DEMO_CREDENTIALS.txt").write_text(text, encoding="utf-8")
    return text

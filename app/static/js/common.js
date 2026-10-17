/* DERMA-GUARD — shared helpers: theme, auth-aware nav, API, assistant widget */
(function () {
  const ICONS = {
    shield: '<path d="M12 2 4 5v6c0 5 3.4 9.3 8 11 4.6-1.7 8-6 8-11V5l-8-3Z"/><path d="m9 12 2 2 4-4"/>',
    layers: '<path d="m12 2 10 5-10 5L2 7l10-5Z"/><path d="m2 17 10 5 10-5"/><path d="m2 12 10 5 10-5"/>',
    scan: '<path d="M3 7V5a2 2 0 0 1 2-2h2M17 3h2a2 2 0 0 1 2 2v2M21 17v2a2 2 0 0 1-2 2h-2M7 21H5a2 2 0 0 1-2-2v-2"/><path d="M7 12h10"/>',
    chart: '<path d="M3 3v18h18"/><path d="M7 15v3M12 9v9M17 5v13"/>',
    brain: '<path d="M9 4a3 3 0 0 0-3 3 3 3 0 0 0-2 5 3 3 0 0 0 2 5 3 3 0 0 0 6 1V4a3 3 0 0 0-3 0Z"/><path d="M15 4a3 3 0 0 1 3 3 3 3 0 0 1 2 5 3 3 0 0 1-2 5 3 3 0 0 1-6 1"/>',
    doc: '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8l-5-5Z"/><path d="M14 3v5h5M9 13h6M9 17h6"/>',
    history: '<path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5M12 7v5l3 2"/>',
    alert: '<path d="m10.3 3.9-8.5 14.7A2 2 0 0 0 3.5 21h17a2 2 0 0 0 1.7-2.4L13.7 3.9a2 2 0 0 0-3.4 0Z"/><path d="M12 9v4M12 17h.01"/>',
    flask: '<path d="M9 3h6M10 3v6L4.5 19A2 2 0 0 0 6.3 22h11.4a2 2 0 0 0 1.8-3L14 9V3"/>',
    upload: '<path d="M12 16V4m0 0-4 4m4-4 4 4"/><path d="M4 16v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3"/>',
    camera: '<path d="M4 8a2 2 0 0 1 2-2h2l1.5-2h5L16 6h2a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V8Z"/><circle cx="12" cy="13" r="3.5"/>',
    sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    moon: '<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z"/>',
    menu: '<path d="M4 6h16M4 12h16M4 18h16"/>',
    print: '<path d="M6 9V3h12v6M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><path d="M6 14h12v7H6z"/>',
    trash: '<path d="M3 6h18M8 6V4h8v2M6 6l1 14h10l1-14"/>',
    check: '<path d="m5 12 5 5 9-10"/>',
    zap: '<path d="M13 2 4 14h7l-1 8 9-12h-7l1-8Z"/>',
    users: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.9M16 3.1a4 4 0 0 1 0 7.8"/>',
    target: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
    chat: '<path d="M21 12a8 8 0 0 1-11.6 7.1L3 21l1.9-5.4A8 8 0 1 1 21 12Z"/>',
    send: '<path d="m22 2-7 20-4-9-9-4 20-7Z"/><path d="M22 2 11 13"/>',
    cal: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 11h18"/>',
    lock: '<rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
    stetho: '<path d="M6 3v6a4 4 0 0 0 8 0V3"/><path d="M10 13v2a5 5 0 0 0 10 0v-1"/><circle cx="20" cy="12" r="2"/>',
    book: '<path d="M4 4h12a4 4 0 0 1 4 4v12H8a4 4 0 0 1-4-4V4Z"/><path d="M4 16a4 4 0 0 1 4-4h12"/>',
    bot: '<rect x="4" y="8" width="16" height="12" rx="3"/><path d="M12 4v4M9 14h.01M15 14h.01M9 18h6"/>',
  };
  window.icon = (name, size = 20) =>
    `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONS[name] || ""}</svg>`;

  const store = {
    get(k) { try { return localStorage.getItem(k); } catch { return null; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch { /* private mode */ } },
  };
  document.documentElement.dataset.theme = store.get("dg-theme") === "dark" ? "dark" : "light";   // white by default

  /* ---------- API ---------- */
  window.api = async function (path, opts = {}) {
    opts = { credentials: "same-origin", ...opts };
    opts.headers = { "X-Requested-With": "dg-web", ...(opts.headers || {}) };
    if (opts.json !== undefined) {
      opts.body = JSON.stringify(opts.json);
      opts.headers["Content-Type"] = "application/json";
      opts.method = opts.method || "POST";
    }
    const res = await fetch(path, opts);
    let body = null;
    try { body = await res.json(); } catch { /* non-json */ }
    if (!res.ok) {
      let msg = `Request failed (${res.status})`;
      if (body && body.detail) {
        msg = typeof body.detail === "string" ? body.detail
          : Array.isArray(body.detail) ? body.detail.map((d) => d.msg).join("; ") : JSON.stringify(body.detail);
      }
      const err = new Error(msg); err.status = res.status; throw err;
    }
    return body;
  };

  window.fmt = {
    pct: (v, d = 1) => (v * 100).toFixed(d) + "%",
    num: (v, d = 3) => Number(v).toFixed(d),
    date: (t) => new Date(t * 1000).toLocaleString([], { dateStyle: "medium", timeStyle: "short" }),
    slot: (s) => new Date(s).toLocaleString([], { weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }),
    esc: (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])),
  };

  window.toast = function (msg, kind = "") {
    let wrap = document.querySelector(".toast-wrap");
    if (!wrap) { wrap = document.createElement("div"); wrap.className = "toast-wrap"; document.body.appendChild(wrap); }
    const t = document.createElement("div");
    t.className = "toast " + kind; t.textContent = msg; wrap.appendChild(t);
    setTimeout(() => t.remove(), 4800);
  };

  /* ---------- current user ---------- */
  let userResolve;
  window.whoami = new Promise((r) => { userResolve = r; });
  /** Resolve the signed-in user, redirecting to /register when absent or role not allowed. */
  window.requireAuth = async function (roles) {
    const u = await window.whoami;
    if (!u) { location.href = "/register?next=" + encodeURIComponent(location.pathname + location.search); return new Promise(() => {}); }
    if (roles && !roles.includes(u.role)) { location.href = "/dashboard"; return new Promise(() => {}); }
    return u;
  };

  const NAV = {
    anon: [["/", "Home"], ["/doctors", "Doctors"], ["/performance", "Evidence"], ["/how-it-works", "How it works"], ["/documentation", "Docs"]],
    patient: [["/dashboard", "Dashboard"], ["/diagnose", "New analysis"], ["/history", "My cases"], ["/lesions", "Lesions"], ["/appointments", "Appointments"], ["/doctors", "Doctors"]],
    doctor: [["/dashboard", "Dashboard"], ["/history", "All cases"], ["/appointments", "Schedule"], ["/diagnose", "Analyse"], ["/stress", "DERMA-STRESS"], ["/performance", "Evidence"]],
    admin: [["/dashboard", "Overview"], ["/admin", "Administration"], ["/stress", "DERMA-STRESS"], ["/performance", "Evidence"], ["/documentation", "Docs"]],
  };

  let SWITCHABLE = false;

  function renderChrome(user) {
    const path = location.pathname.replace(/\/$/, "") || "/";
    const links = NAV[user ? user.role : "anon"];
    const wrap = document.createElement("div");
    wrap.innerHTML = `
      <header class="nav"><div class="container">
        <a class="brand" href="/"><span class="brand-mark">${icon("shield", 20)}</span>DERMA-GUARD<small>Dermatology</small></a>
        <nav class="nav-links" id="navLinks">${links.map(([h, t]) =>
          `<a href="${h}" class="${path === h ? "active" : ""}">${t}</a>`).join("")}</nav>
        <div class="nav-right">
          <span class="status-pill" id="enginePill" title="Inference engine"><i class="dot loading"></i><span class="t">Connecting…</span></span>
          <button class="icon-btn" id="themeBtn" aria-label="Toggle theme"></button>
          ${user && SWITCHABLE ? `<div class="roleswitch" id="roleSwitch" role="group" aria-label="Switch view">
                ${[["patient", "Patient"], ["doctor", "Doctor"], ["admin", "Admin"]].map(([r, t]) => `<button data-r="${r}" class="${user.role === r ? "on" : ""}">${t}</button>`).join("")}</div>
              ${user.role === "doctor" ? '<select class="docpick" id="docPick" aria-label="Which doctor"></select>' : ""}` : ""}
          ${user ? `<div class="usermenu"><a class="userchip" href="/account" title="Account"><span class="avatar">${fmt.esc(user.name[0].toUpperCase())}</span><span class="un">${fmt.esc(user.name.split(" ").slice(0, 2).join(" "))}</span><span class="tag brand">${user.role}</span></a>
                  <button class="btn btn-ghost btn-sm" id="logoutBtn">Exit</button></div>`
                 : `<a class="btn btn-primary btn-sm" href="/register">Register as patient</a>`}
          <button class="icon-btn burger" id="burger" aria-label="Menu">${icon("menu")}</button>
        </div>
      </div></header>`;
    document.body.prepend(...wrap.children);

    const footer = document.createElement("footer");
    footer.innerHTML = `<div class="container">
      <div><b>DERMA-GUARD</b> · multimodal skin-lesion triage<br>
      Multimodal, evidence-aware skin-lesion triage. Demonstration hospital — research use only.</div>
      <div class="row"><a href="/doctors">Doctors</a><a href="/performance">Evidence</a><a href="/how-it-works">Method</a><a href="/safety">Safety</a><a href="/documentation">Docs</a><a href="/api/docs">API</a></div>
    </div>`;
    document.body.appendChild(footer);

    const setThemeIcon = () => { document.getElementById("themeBtn").innerHTML = icon(document.documentElement.dataset.theme === "dark" ? "sun" : "moon"); };
    setThemeIcon();
    document.getElementById("themeBtn").onclick = () => {
      const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
      document.documentElement.dataset.theme = next; store.set("dg-theme", next); setThemeIcon();
    };
    document.getElementById("burger").onclick = () => document.getElementById("navLinks").classList.toggle("open");
    const rs = document.getElementById("roleSwitch");
    if (rs) rs.addEventListener("click", async (e) => {
      const b = e.target.closest("button"); if (!b || b.classList.contains("on")) return;
      try { await api("/api/auth/switch", { json: { role: b.dataset.r } }); location.href = "/dashboard"; }
      catch (ex) { toast(ex.message, "bad"); }
    });
    const dp = document.getElementById("docPick");
    if (dp) api("/api/doctors").then((ds) => {
      dp.innerHTML = ds.map((d) => `<option value="${d.id}" ${d.name === user.name ? "selected" : ""}>${fmt.esc(d.name)}</option>`).join("");
      dp.onchange = async () => { try { await api("/api/auth/switch", { json: { role: "doctor", doctor_id: +dp.value } }); location.reload(); } catch (ex) { toast(ex.message, "bad"); } };
    }).catch(() => {});
    const lo = document.getElementById("logoutBtn");
    if (lo) lo.onclick = async () => { try { await api("/api/auth/logout", { method: "POST" }); } catch {} location.href = "/"; };
  }

  /* ---------- engine / rag status ---------- */
  let lastState = null;
  async function pollStatus() {
    const pill = document.getElementById("enginePill");
    if (!pill) return;
    try {
      const s = await api("/api/status");
      const ready = s.state === "ready" && s.rag.state === "ready";
      const st = s.state === "error" ? "error" : ready ? "ready" : "loading";
      pill.innerHTML = `<i class="dot ${st}"></i><span class="t">${{ ready: "AI ready", loading: "Loading AI…", error: "Engine error" }[st]}</span>`;
      pill.title = `Models: ${s.state}${s.device ? " (" + s.device + ")" : ""} · Knowledge base: ${s.rag.mode || s.rag.state} · LLM: ${s.llm.available ? s.llm.model : "not running (retrieval mode)"}`;
      if (s.state !== lastState) { lastState = s.state; document.dispatchEvent(new CustomEvent("enginestate", { detail: s })); }
      if (!ready && st !== "error") setTimeout(pollStatus, 2500);
    } catch {
      pill.innerHTML = `<i class="dot error"></i><span class="t">Server offline</span>`;
      setTimeout(pollStatus, 5000);
    }
  }

  window.initTabs = function (root) {
    const tabs = root.querySelectorAll(".tab"), panes = root.querySelectorAll(".pane");
    tabs.forEach((t) => t.addEventListener("click", () => {
      tabs.forEach((x) => x.classList.toggle("on", x === t));
      panes.forEach((p) => p.classList.toggle("on", p.id === t.dataset.pane));
    }));
  };

  window.CLASS_NAMES = { BCC: "Basal Cell Carcinoma", ACK: "Actinic Keratosis", NEV: "Melanocytic Nevus",
    SEK: "Seborrheic Keratosis", SCC: "Squamous Cell Carcinoma", MEL: "Melanoma" };
  window.CLASS_GROUP = { BCC: "malignant", SCC: "malignant", MEL: "malignant", ACK: "pre-malignant", NEV: "benign", SEK: "benign" };

  /* ---------- assistant widget ---------- */
  function mountAssistant() {
    const el = document.createElement("div");
    el.className = "care-assistant no-print";
    el.innerHTML = `
      <button class="assistant-fab" id="asFab" aria-label="Open assistant">${icon("chat", 24)}</button>
      <section class="assistant-panel" id="asPanel" hidden aria-label="Health assistant">
        <header><div class="row" style="gap:10px"><span class="avatar" style="background:var(--accent)">${icon("bot", 16)}</span>
          <div><b>Care assistant</b><div class="muted" style="font-size:.74rem" id="asMode">Retrieval-grounded · cites sources</div></div></div>
          <button class="icon-btn" id="asClose" aria-label="Close" style="width:30px;height:30px">✕</button></header>
        <div class="as-body" id="asBody"></div>
        <div class="as-chips" id="asChips"></div>
        <form id="asForm"><input type="text" id="asInput" maxlength="600" placeholder="Ask about skin conditions, your result, bookings…" autocomplete="off"><button class="btn btn-primary btn-sm" aria-label="Send">${icon("send", 16)}</button></form>
      </section>`;
    document.body.appendChild(el);
    const $ = (id) => document.getElementById(id), body = $("asBody");
    let loaded = false;

    const bubble = (role, html, meta = {}) => {
      const d = document.createElement("div");
      d.className = "as-msg " + role + (meta.level === "emergency" ? " emergency" : "");
      d.innerHTML = html;
      if (meta.sources && meta.sources.length) {
        const s = document.createElement("div"); s.className = "as-src";
        s.innerHTML = meta.sources.map((x) => `<span title="${fmt.esc(x.source)}">[${x.n}] ${fmt.esc(x.title.length > 34 ? x.title.slice(0, 32) + "…" : x.title)} › ${fmt.esc(x.section)}</span>`).join("");
        d.appendChild(s);
      }
      if (meta.actions && meta.actions.length) {
        const a = document.createElement("div"); a.className = "as-act";
        a.innerHTML = meta.actions.map((x) => `<a class="btn btn-ghost btn-sm" href="${fmt.esc(x.href)}">${fmt.esc(x.label)}</a>`).join("");
        d.appendChild(a);
      }
      if (meta.mode) { const m = document.createElement("div"); m.className = "as-mode"; m.textContent = meta.mode; d.appendChild(m); }
      body.appendChild(d); body.scrollTop = body.scrollHeight;
      return d;
    };
    const text = (s) => fmt.esc(s).replace(/\n/g, "<br>");

    async function open() {
      $("asPanel").hidden = false; $("asFab").hidden = true; $("asInput").focus();
      if (loaded) return; loaded = true;
      try {
        const h = await api("/api/chat/history");
        if (h.length) h.forEach((m) => bubble(m.role, text(m.text), m));
        else bubble("assistant", "Hi, I'm your care assistant. I answer from a curated dermatology knowledge base and always show my sources. I can also explain your latest analysis and help you book a visit.");
      } catch { bubble("assistant", "Hi! Ask me anything about skin health, your results, or appointments."); }
      $("asChips").innerHTML = ["What are the warning signs of melanoma?", "Explain my latest result", "Book an appointment", "How do I protect my skin?"]
        .map((q) => `<button type="button" class="chip">${q}</button>`).join("");
    }
    async function send(q) {
      if (!q.trim()) return;
      bubble("user", fmt.esc(q)); $("asInput").value = "";
      const wait = bubble("assistant", '<span class="spinner dark" style="width:14px;height:14px;display:inline-block"></span>');
      try {
        const r = await api("/api/chat", { json: { message: q } });
        wait.remove(); bubble("assistant", text(r.text), r);
      } catch (e) { wait.remove(); bubble("assistant", fmt.esc(e.message)); }
    }
    $("asFab").onclick = open;
    $("asClose").onclick = () => { $("asPanel").hidden = true; $("asFab").hidden = false; };
    $("asForm").onsubmit = (e) => { e.preventDefault(); send($("asInput").value); };
    $("asChips").onclick = (e) => { const c = e.target.closest(".chip"); if (c) send(c.textContent); };
  }

  document.addEventListener("DOMContentLoaded", async () => {
    let user = null;
    try { const me = await api("/api/auth/me"); user = me.user; SWITCHABLE = !!me.switchable; } catch { /* offline */ }
    userResolve(user);
    renderChrome(user);
    pollStatus();
    if (user && user.role !== "admin") mountAssistant();
    document.querySelectorAll("[data-icon]").forEach((el) => { el.innerHTML = icon(el.dataset.icon, +el.dataset.size || 22); });
    document.dispatchEvent(new CustomEvent("chromeready", { detail: user }));
  });
})();

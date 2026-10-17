/* Diagnostic workspace logic */
(() => {
  const $ = (id) => document.getElementById(id);
  const REGIONS = ["FACE", "NOSE", "EAR", "LIP", "SCALP", "NECK", "CHEST", "BACK", "ABDOMEN", "ARM", "FOREARM", "HAND", "THIGH", "FOOT"];
  const SWITCHES = [
    ["itch", "Itches"], ["grew", "Has grown"], ["changed", "Changed appearance"],
    ["bleed", "Bleeds"], ["hurt", "Painful"], ["elevation", "Raised / elevated"],
    ["smoke", "Smoker"], ["drink", "Drinks alcohol"], ["skin_cancer_history", "Prior skin cancer"],
    ["cancer_history", "Other cancer history"], ["pesticide", "Pesticide exposure"],
  ];
  const NUMERIC = ["age", "diameter_1", "diameter_2"];
  const SELECTS = ["gender", "fitspatrick", "region"];

  let imageFile = null;     // File chosen or loaded from a sample
  let truth = null;         // hidden ground-truth label for sample cases
  let sampleId = null;      // dataset image id when a sample is loaded (excluded from similar-case search)
  let role = "patient";
  whoami.then((u) => { if (!u) location.href = "/register?next=/diagnose"; else role = u.role; });
  let samples = [];
  let busy = false;

  /* ---------- build static form bits ---------- */
  $("region").innerHTML += REGIONS.map((r) => `<option>${r}</option>`).join("");
  $("switches").innerHTML = SWITCHES.map(([k, l]) =>
    `<label class="switch"><input type="checkbox" id="sw_${k}"> ${l}</label>`).join("");

  /* ---------- engine readiness ---------- */
  let engineState = "loading";
  function refreshGo() {
    const go = $("go");
    go.disabled = busy || engineState !== "ready";
    $("goHint").textContent = engineState === "loading" ? "Models are loading — about 30 s on first start…"
      : engineState === "error" ? "Inference engine failed to start — see the status pill." : "";
  }
  document.addEventListener("enginestate", (ev) => { engineState = ev.detail.state; refreshGo(); });
  refreshGo();

  /* ---------- image handling ---------- */
  async function setImage(file, fromSample = false) {
    imageFile = file;
    if (!fromSample) clearSampleSelection();
    const url = URL.createObjectURL(file);
    const pv = $("preview");
    pv.src = url; pv.hidden = false;
    $("drop").classList.add("has-img");
    $("clearImg").hidden = false;
    runQuality(file);
  }
  function clearImage() {
    imageFile = null;
    $("preview").hidden = true; $("preview").removeAttribute("src");
    $("drop").classList.remove("has-img");
    $("clearImg").hidden = true; $("file").value = "";
    $("quality").innerHTML = '<div class="muted" style="font-size:.9rem">An instant quality check appears here once you add a photo.</div>';
  }
  async function runQuality(file) {
    $("quality").innerHTML = '<div class="skeleton" style="height:150px"></div>';
    try {
      const fd = new FormData(); fd.append("image", file);
      const q = await api("/api/quality", { method: "POST", body: fd });
      const col = { good: "ok", fair: "", poor: "bad" }[q.verdict];
      $("quality").innerHTML = `
        <div class="row spread"><h4 style="margin:0">Image quality</h4><span class="tag ${q.verdict === "good" ? "benign" : q.verdict === "fair" ? "pre-malignant" : "malignant"}">${q.verdict} · ${Math.round(q.overall * 100)}%</span></div>
        <div class="bars">${q.checks.map((c) =>
          `<div class="bar" style="grid-template-columns:90px 1fr 40px"><span class="name">${c.label}</span><div class="track"><div class="fill ${c.score < .45 ? "malignant" : c.score < .7 ? "pre-malignant" : "benign"}" style="width:${c.score * 100}%"></div></div><span class="val">${Math.round(c.score * 100)}</span></div>`).join("")}</div>
        <div class="callout ${col}" style="font-size:.84rem">${q.checks.filter((c) => c.score < .7).map((c) => c.hint).join(" ") || "Great — this photo is suitable for analysis."}</div>`;
    } catch (err) {
      $("quality").innerHTML = `<div class="callout bad">${fmt.esc(err.message)}</div>`;
    }
  }

  const drop = $("drop");
  $("file").addEventListener("change", (e) => e.target.files[0] && setImage(e.target.files[0]));
  ["dragover", "dragenter"].forEach((n) => drop.addEventListener(n, (e) => { e.preventDefault(); drop.classList.add("over"); }));
  ["dragleave", "drop"].forEach((n) => drop.addEventListener(n, (e) => { e.preventDefault(); drop.classList.remove("over"); }));
  drop.addEventListener("drop", (e) => { const f = e.dataTransfer.files[0]; if (f && f.type.startsWith("image/")) setImage(f); });
  $("clearImg").addEventListener("click", (e) => { e.preventDefault(); clearImage(); clearSampleSelection(); });

  /* ---------- form <-> metadata ---------- */
  function collectMetadata() {
    const m = {};
    NUMERIC.forEach((k) => { const v = $(k).value; if (v !== "") m[k] = parseFloat(v); });
    SELECTS.forEach((k) => { const v = $(k).value; if (v) m[k] = k === "fitspatrick" ? parseInt(v, 10) : v; });
    const anyTick = SWITCHES.some(([k]) => $("sw_" + k).checked);
    const hasCore = Object.keys(m).length > 0;
    if (hasCore || anyTick) SWITCHES.forEach(([k]) => { m[k] = $("sw_" + k).checked ? "TRUE" : "FALSE"; });
    return m;
  }
  function fillMetadata(m) {
    NUMERIC.concat(SELECTS).forEach((k) => { $(k).value = m[k] !== undefined ? String(m[k]) : ""; });
    SWITCHES.forEach(([k]) => { $("sw_" + k).checked = m[k] === "TRUE"; });
  }

  /* ---------- samples ---------- */
  let sampleFilter = "ALL";
  function renderSamples() {
    const list = samples.filter((s) => sampleFilter === "ALL" || s.truth === sampleFilter);
    $("samples").innerHTML = list.map((s) => `
      <button class="sample" data-id="${s.img_id}" title="${fmt.esc(s.label)}">
        <img loading="lazy" src="/api/sample-image/${s.img_id}" alt="Sample lesion">
        <div class="cap">${fmt.esc(s.label)}</div></button>`).join("") || '<p class="muted">No samples.</p>';
  }
  function clearSampleSelection() {
    truth = null; sampleId = null;
    document.querySelectorAll(".sample.sel").forEach((el) => el.classList.remove("sel"));
  }
  async function loadSample(id) {
    const s = samples.find((x) => x.img_id === id);
    if (!s) return;
    try {
      const blob = await (await fetch(`/api/sample-image/${id}`)).blob();
      await setImage(new File([blob], id, { type: blob.type || "image/png" }), true);
      fillMetadata(s.metadata);
      $("text").value = ""; $("ptis").textContent = "";
      truth = s.truth; sampleId = id;
      document.querySelectorAll(".sample").forEach((el) => el.classList.toggle("sel", el.dataset.id === id));
      toast("Sample loaded — press “Analyse case”.");
    } catch { toast("Could not load that sample.", "bad"); }
  }
  $("samples").addEventListener("click", (e) => { const b = e.target.closest(".sample"); if (b) loadSample(b.dataset.id); });

  api("/api/samples").then((list) => {
    samples = list;
    const classes = ["ALL", ...new Set(list.map((s) => s.truth))];
    $("sampleChips").innerHTML = classes.map((c) => `<button class="chip ${c === "ALL" ? "on" : ""}" data-c="${c}">${c === "ALL" ? "All" : c}</button>`).join("");
    $("sampleChips").addEventListener("click", (e) => {
      const b = e.target.closest(".chip"); if (!b) return;
      sampleFilter = b.dataset.c;
      document.querySelectorAll("#sampleChips .chip").forEach((c) => c.classList.toggle("on", c === b));
      renderSamples();
    });
    renderSamples();
  }).catch(() => { $("samples").innerHTML = '<p class="muted">Samples unavailable.</p>'; });

  /* ---------- text generation ---------- */
  $("genText").addEventListener("click", async () => {
    const meta = collectMetadata();
    const fd = new FormData(); fd.append("metadata", JSON.stringify(meta));
    $("genText").disabled = true;
    try {
      const r = await api("/api/generate-text", { method: "POST", body: fd });
      $("text").value = r.text;
      $("ptis").textContent = `Text informativeness (PTIS): ${r.ptis.toFixed(2)}`;
    } catch (err) { toast(err.message, "bad"); }
    $("genText").disabled = false;
  });

  /* ---------- analyse ---------- */
  const STEPS = ["Encoding image, details and text…", "Profiling evidence quality & reliability…",
    "Running candidate models…", "Fusing evidence & calibrating uncertainty…"];

  $("go").addEventListener("click", async () => {
    const meta = collectMetadata(), text = $("text").value.trim();
    if (!imageFile && !Object.keys(meta).length && !text) {
      toast("Add a photo, some patient details or a description first.", "bad"); return;
    }
    busy = true; refreshGo();
    const label = $("go").textContent; $("go").innerHTML = '<span class="spinner"></span> Analysing…';
    let i = 0;
    const paint = () => { $("result").innerHTML = `<div class="card empty"><div class="spinner dark" style="margin:0 auto 14px;width:30px;height:30px"></div><h3>${STEPS[i % STEPS.length]}</h3><p>Agents are working: intake → models → safety → retrieval → report.</p></div>`; i++; };
    paint(); const timer = setInterval(paint, 1600);

    try {
      const fd = new FormData();
      if (imageFile) fd.append("image", imageFile);
      if (Object.keys(meta).length) fd.append("metadata", JSON.stringify(meta));
      if (text) fd.append("text", text);
      if ($("model").value) fd.append("model", $("model").value);
      if (truth) { fd.append("truth", truth); fd.append("sample_img", sampleId || ""); }
      const r = await api("/api/analyze", { method: "POST", body: fd });
      clearInterval(timer);
      if (r.result && truth) r.result.truth = r.result.truth || null;
      $("result").innerHTML = `<div class="fade-in">${ResultView.tabbed(r, { role })}</div>`;
      initTabs($("resTabs"));
      await mountCaseActions(r);
      if (window.innerWidth < 960) $("result").scrollIntoView({ behavior: "smooth" });
    } catch (err) {
      clearInterval(timer);
      $("result").innerHTML = `<div class="card"><div class="callout bad">${fmt.esc(err.message)}</div></div>`;
    } finally {
      busy = false; $("go").textContent = label; refreshGo();
    }
  });

  async function mountCaseActions(r) {
    if (role !== "patient") return;
    let docs = [];
    try { docs = await api("/api/doctors"); } catch { return; }
    const box = document.createElement("div");
    box.className = "card flat no-print"; box.style.marginTop = "16px";
    box.innerHTML = `<h4>Get a human opinion</h4>
      <div class="row" style="margin-top:10px">
        <select id="revDoc" style="max-width:260px">${docs.map((d) => `<option value="${d.id}">${fmt.esc(d.name)} — ${fmt.esc(d.department || "")}</option>`).join("")}</select>
        <button class="btn btn-primary btn-sm" id="revBtn">Request doctor review</button>
        <a class="btn btn-ghost btn-sm" id="revBook" href="#">Book appointment</a>
      </div>
      <p class="muted" style="font-size:.82rem;margin:8px 0 0">The doctor will see your photo, details and this analysis. Reviews are not instant — use an appointment or emergency care for urgent concerns.</p>`;
    $("result").appendChild(box);
    const upd = () => { $("revBook").href = `/appointments?doctor=${$("revDoc").value}&case=${r.case_id}`; };
    $("revDoc").addEventListener("change", upd); upd();
    $("revBtn").addEventListener("click", async () => {
      $("revBtn").disabled = true;
      try { await api(`/api/cases/${r.case_id}/request-review`, { json: { doctor_id: +$("revDoc").value } });
            $("revBtn").textContent = "Review requested ✓"; toast("Sent to the doctor for review."); }
      catch (err) { toast(err.message, "bad"); $("revBtn").disabled = false; }
    });
  }

  $("reset").addEventListener("click", () => {
    clearImage(); clearSampleSelection(); fillMetadata({}); $("text").value = ""; $("ptis").textContent = ""; $("model").value = "";
    $("result").innerHTML = `<div class="card empty"><div data-icon="scan" data-size="56"></div><h3>Your result appears here</h3><p>Choose a sample or fill in the form, then press <b>Analyse case</b>.</p></div>`;
    document.querySelectorAll("#result [data-icon]").forEach((el) => { el.innerHTML = icon(el.dataset.icon, +el.dataset.size); });
  });
})();

const CrabEyes = (() => {
  const LABELS = {
    high_risk: "High risk", check_first: "Check first",
    looks_legitimate: "Looks legitimate", not_enough_evidence: "Not enough evidence",
  };
  const el = (id) => document.getElementById(id);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]));

  async function streamInvestigation(url, body, onEvent) {
    const resp = await fetch(url, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body)});
    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    for (;;) {
      const {value, done} = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, {stream: true});
      const lines = buffer.split("\n");
      buffer = lines.pop();
      for (const line of lines) if (line.trim()) onEvent(JSON.parse(line));
    }
  }

  function fileToBase64(file) {
    return new Promise((resolve, reject) => {
      const r = new FileReader();
      r.onload = () => resolve(String(r.result).split(",")[1]);
      r.onerror = reject;
      r.readAsDataURL(file);
    });
  }

  function progressHandler(list) {
    return (ev) => {
      if (ev.type === "progress") list.insertAdjacentHTML("beforeend", `<li>${esc(ev.line)}</li>`);
      if (ev.type === "plan") list.insertAdjacentHTML("beforeend", `<li>Plan (round ${ev.round}): ${esc(ev.checks.join(", "))}</li>`);
      if (ev.type === "dossier") location.href = `dossier.html?id=${ev.dossier.id}`;
    };
  }

  async function initHome() {
    el("go").onclick = async () => {
      const file = el("image").files[0];
      const body = {text: el("pitch").value, image_b64: file ? await fileToBase64(file) : null};
      el("progress").innerHTML = "";
      await streamInvestigation("/api/investigate", body, progressHandler(el("progress")));
    };
    const cases = await (await fetch("/api/gallery")).json();
    el("gallery").innerHTML = cases.map((c) =>
      `<li><a href="dossier.html?id=${esc(c.id)}">${esc(c.company || c.id)}</a> - ${esc(LABELS[c.verdict])}</li>`).join("");
  }

  async function initDossier() {
    const id = new URLSearchParams(location.search).get("id");
    const d = await (await fetch(`/api/dossier/${encodeURIComponent(id)}`)).json();
    el("verdict").innerHTML = `<div class="verdict ${esc(d.verdict)}">${esc(LABELS[d.verdict])}</div>` +
      `<ul>${d.reasons.map((r) => `<li>${esc(r)}</li>`).join("")}</ul>`;
    const c = d.claims;
    el("claims").innerHTML = [...c.company_names.map((n) => `Company: ${n}`),
      c.promised_return != null ? `Promised: ${Math.round(c.promised_return * 100)}% per ${c.return_period_months} month(s)` : null,
      ...c.regulator_claims, ...c.other_claims].filter(Boolean).map((x) => `<li>${esc(x)}</li>`).join("");
    el("plan").innerHTML = d.plan.map((p) => `<li>${esc(p)}</li>`).join("");
    el("findings").innerHTML = d.findings.map((f) => `<li class="${f.verified ? "" : "rejected"}">` +
      `<b>${esc(f.check)}</b>: ${esc(f.summary)}` +
      (f.source ? ` <a href="${esc(f.source.url)}" target="_blank" rel="noopener">source</a>` : "") +
      (f.rejected_reason ? ` <span class="muted">(set aside: ${esc(f.rejected_reason)})</span>` : "") + `</li>`).join("");
    el("cvr").innerHTML = "<tr><th>Claim</th><th>Record</th></tr>" + d.claims_vs_records.map((r) =>
      `<tr class="${r.mismatch ? "mismatch" : ""}"><td>${esc(r.claim)}</td><td>${esc(r.record)}` +
      (r.source_url ? ` <a href="${esc(r.source_url)}" target="_blank" rel="noopener">source</a>` : "") + `</td></tr>`).join("");
    el("explanations").innerHTML = d.explanations.map((e) =>
      `<li>${esc(e.label)}: ${Math.round(e.probability * 100)}% - ${esc(e.distinguishing_evidence)}</li>`).join("");
    el("change").innerHTML = d.what_would_change_my_mind.map((x) => `<li>${esc(x)}</li>`).join("");
    el("trace").innerHTML = "<tr><th>Step</th><th>Model / tool</th><th>Tokens in/out</th><th>Cost</th></tr>" +
      d.trace.map((t) => t.model
        ? `<tr><td>${esc(t.role)}</td><td>${esc(t.model)}</td><td>${t.tokens_in}/${t.tokens_out}</td><td>$${t.cost_usd.toFixed(5)}</td></tr>`
        : `<tr><td>tool</td><td>${esc(t.tool)}</td><td></td><td></td></tr>`).join("");
    el("cost").textContent = `Total model cost: $${d.cost_usd.toFixed(4)}`;
    el("disclaimer").textContent = d.disclaimer;
    el("prove").onclick = async () => {
      el("change").innerHTML = "";
      await streamInvestigation(`/api/dossier/${encodeURIComponent(id)}/evidence`, {text: el("evidence").value},
        progressHandler(el("change")));
    };
  }

  async function initLedger() {
    const rows = await (await fetch("/api/ledger")).json();
    el("ledger").innerHTML = "<tr><th>Scheme</th><th>First seen</th><th>Reports (7 days)</th><th>Growth</th><th>Verdict</th></tr>" +
      rows.map((r) => `<tr><td>${esc(r.scheme)}</td><td>${esc(r.first_seen.slice(0, 10))}</td><td>${r.reports_7d}</td>` +
        `<td>${r.growth > 0 ? "+" : ""}${r.growth}</td><td>${esc(LABELS[r.verdict])}</td></tr>`).join("");
  }

  return {initHome, initDossier, initLedger};
})();

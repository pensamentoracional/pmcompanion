const api = "";
let activeProjectId = null;
let cachedItems = [];

function toast(message, type = "info") {
  const el = document.getElementById("toast");
  el.textContent = message;
  el.className = `toast show ${type}`;
  setTimeout(() => {
    el.className = "toast";
  }, 2500);
}

function requireProject() {
  if (!activeProjectId) {
    toast("Selecione um projeto antes de continuar.", "error");
    return false;
  }
  return true;
}

async function loadProjects() {
  const res = await fetch(`${api}/projects`);
  const projects = await res.json();
  const list = document.getElementById("projectList");
  list.innerHTML = "";

  projects.forEach((p) => {
    const li = document.createElement("li");
    const btn = document.createElement("button");
    btn.textContent = "Selecionar";
    btn.onclick = () => selectProject(p.id, p.name);
    li.appendChild(btn);
    li.append(` ${p.name}`);
    list.appendChild(li);
  });
}

function selectProject(id, name) {
  activeProjectId = id;
  document.getElementById("activeProject").innerText = `${name} (#${id})`;
  refreshProjectData();
}

document.getElementById("projectForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = new FormData();
  form.append("name", document.getElementById("projectName").value);
  form.append("description", document.getElementById("projectDesc").value);

  try {
    await fetch(`${api}/projects`, { method: "POST", body: form });
    e.target.reset();
    await loadProjects();
    toast("Projeto criado com sucesso.", "success");
  } catch {
    toast("Erro ao criar projeto.", "error");
  }
});

document.getElementById("uploadBtn").addEventListener("click", async () => {
  if (!requireProject()) return;
  const files = document.getElementById("files").files;
  if (!files.length) return toast("Selecione ao menos um arquivo para upload.", "info");

  const form = new FormData();
  for (const file of files) form.append("files", file);

  try {
    const res = await fetch(`${api}/projects/${activeProjectId}/upload`, { method: "POST", body: form });
    if (!res.ok) throw new Error();
    toast("Upload concluído com sucesso.", "success");
  } catch {
    toast("Erro no upload. Verifique formatos suportados.", "error");
  }
});

document.getElementById("processBtn").addEventListener("click", async () => {
  if (!requireProject()) return;

  try {
    const res = await fetch(`${api}/projects/${activeProjectId}/process`, { method: "POST" });
    if (!res.ok) throw new Error();
    await refreshProjectData();
    toast("Processamento concluído.", "success");
  } catch {
    toast("Erro no processamento do projeto.", "error");
  }
});

document.getElementById("reportBtn").addEventListener("click", async () => {
  if (!requireProject()) return;
  try {
    const res = await fetch(`${api}/projects/${activeProjectId}/report`);
    if (!res.ok) throw new Error();
    const data = await res.json();
    document.getElementById("reportArea").value = data.report;
    toast("Relatório gerado.", "success");
  } catch {
    toast("Erro ao gerar relatório.", "error");
  }
});

document.getElementById("copyReportBtn").addEventListener("click", async () => {
  const reportText = document.getElementById("reportArea").value;
  if (!reportText) return toast("Gere o relatório antes de copiar.", "info");
  await navigator.clipboard.writeText(reportText);
  toast("Relatório copiado para área de transferência.", "success");
});

document.getElementById("itemTypeFilter").addEventListener("change", renderItems);

function renderDashboard(dashboard) {
  const labels = {
    total_documents: "Documentos",
    total_documents_processed: "Processados",
    total_items_found: "Itens",
    total_actions: "Actions",
    total_risks: "Risks",
    total_decisions: "Decisions",
    total_dependencies: "Dependencies",
    total_open_questions: "Open Questions",
    total_alerts: "Alertas",
  };

  const cards = document.getElementById("cards");
  cards.innerHTML = Object.entries(labels)
    .map(([k, label]) => `<div class="card"><div class="label">${label}</div><div class="value">${dashboard[k] ?? 0}</div></div>`)
    .join("");
}

function renderItems() {
  const filter = document.getElementById("itemTypeFilter").value;
  const filtered = filter === "all" ? cachedItems : cachedItems.filter((i) => i.item_type === filter);
  const rows = document.getElementById("itemsTable");
  rows.innerHTML = filtered
    .map((i) => `<tr><td>${i.item_type}</td><td>${i.title}</td><td>${i.owner ?? "-"}</td><td>${i.severity}</td></tr>`)
    .join("");
}

function renderAlerts(alerts) {
  const alertsDiv = document.getElementById("alerts");
  alertsDiv.innerHTML = alerts
    .map((a) => `<div class="alert ${a.severity}"><strong>[${a.severity}] ${a.title}</strong><br>${a.description}</div>`)
    .join("");
}

async function refreshProjectData() {
  if (!activeProjectId) return;

  const [dashboard, alerts, items] = await Promise.all([
    fetch(`${api}/projects/${activeProjectId}/dashboard`).then((r) => r.json()),
    fetch(`${api}/projects/${activeProjectId}/alerts`).then((r) => r.json()),
    fetch(`${api}/projects/${activeProjectId}/items`).then((r) => r.json()),
  ]);

  renderDashboard(dashboard);
  renderAlerts(alerts);
  cachedItems = items;
  renderItems();
}

loadProjects();

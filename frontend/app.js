const api = "";
let activeProjectId = null;

async function loadProjects() {
  const res = await fetch(`${api}/projects`);
  const projects = await res.json();
  const list = document.getElementById("projectList");
  list.innerHTML = "";
  projects.forEach((p) => {
    const li = document.createElement("li");
    li.innerHTML = `<button onclick="selectProject(${p.id}, '${p.name.replace(/'/g, "")}')">Selecionar</button> ${p.name}`;
    list.appendChild(li);
  });
}

window.selectProject = function (id, name) {
  activeProjectId = id;
  document.getElementById("activeProject").innerText = `${name} (#${id})`;
  refreshProjectData();
};

document.getElementById("projectForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = new FormData();
  form.append("name", document.getElementById("projectName").value);
  form.append("description", document.getElementById("projectDesc").value);
  await fetch(`${api}/projects`, { method: "POST", body: form });
  e.target.reset();
  loadProjects();
});

document.getElementById("uploadBtn").addEventListener("click", async () => {
  if (!activeProjectId) return alert("Selecione um projeto");
  const files = document.getElementById("files").files;
  const form = new FormData();
  for (const file of files) form.append("files", file);
  await fetch(`${api}/projects/${activeProjectId}/upload`, { method: "POST", body: form });
  alert("Upload concluído");
});

document.getElementById("processBtn").addEventListener("click", async () => {
  if (!activeProjectId) return alert("Selecione um projeto");
  await fetch(`${api}/projects/${activeProjectId}/process`, { method: "POST" });
  await refreshProjectData();
  alert("Processamento concluído");
});

document.getElementById("reportBtn").addEventListener("click", async () => {
  if (!activeProjectId) return;
  const res = await fetch(`${api}/projects/${activeProjectId}/report`);
  const data = await res.json();
  document.getElementById("reportArea").value = data.report;
});

async function refreshProjectData() {
  if (!activeProjectId) return;

  const [dashboard, alerts, items] = await Promise.all([
    fetch(`${api}/projects/${activeProjectId}/dashboard`).then((r) => r.json()),
    fetch(`${api}/projects/${activeProjectId}/alerts`).then((r) => r.json()),
    fetch(`${api}/projects/${activeProjectId}/items`).then((r) => r.json()),
  ]);

  const cards = document.getElementById("cards");
  cards.innerHTML = Object.entries(dashboard)
    .filter(([k]) => k !== "alerts_by_severity")
    .map(([k, v]) => `<div class="card"><strong>${k}</strong><br>${v}</div>`)
    .join("");

  const alertsDiv = document.getElementById("alerts");
  alertsDiv.innerHTML = alerts.map((a) => `<div class="alert ${a.severity}">[${a.severity}] ${a.title} - ${a.description}</div>`).join("");

  const rows = document.getElementById("itemsTable");
  rows.innerHTML = items.map((i) => `<tr><td>${i.item_type}</td><td>${i.title}</td><td>${i.owner ?? "-"}</td><td>${i.severity}</td></tr>`).join("");
}

loadProjects();

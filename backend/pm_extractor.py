import re
from typing import Any

KEYWORDS = {
    "risk": ["risco", "impacto", "possibilidade", "atenção"],
    "action": ["ação", "proximo passo", "próximo passo", "fazer", "responsável"],
    "decision": ["decidido", "definido", "aprovado"],
    "dependency": ["depende de", "aguardando", "bloqueado"],
    "open_question": ["em aberto", "pendente definir"],
}


def infer_item_type(line: str) -> str | None:
    normalized = line.lower().strip()
    if not normalized:
        return None

    for item_type, words in KEYWORDS.items():
        if any(word in normalized for word in words):
            return item_type

    if normalized.endswith("?"):
        return "open_question"

    return None


def infer_owner(line: str) -> str | None:
    match = re.search(r"responsável\s*:\s*([\w\sÀ-ÿ-]+)", line, flags=re.IGNORECASE)
    return match.group(1).strip() if match else None


def infer_severity(item_type: str, line: str) -> str:
    l = line.lower()
    if "alto" in l or "crítico" in l:
        return "high"
    if item_type in {"risk", "dependency"}:
        return "high"
    if item_type == "open_question":
        return "low"
    return "medium"


def extract_pm_items(text: str, document_id: int, project_id: int) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    for line in lines:
        item_type = infer_item_type(line)
        if not item_type:
            continue

        owner = infer_owner(line)
        severity = infer_severity(item_type, line)
        title = line[:120]
        item = {
            "project_id": project_id,
            "document_id": document_id,
            "item_type": item_type,
            "title": title,
            "description": line,
            "owner": owner,
            "due_date": None,
            "status": "open",
            "severity": severity,
            "source_excerpt": line,
        }
        items.append(item)

    return items

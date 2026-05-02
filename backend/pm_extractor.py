import re
from difflib import SequenceMatcher
from typing import Any

ITEM_KEYWORDS = {
    "risk": [
        "risco",
        "impacto",
        "possibilidade",
        "atenção",
        "pode gerar",
        "pode causar",
        "falha",
        "problema operacional",
    ],
    "action": ["ação", "proximo passo", "próximo passo", "fazer"],
    "decision": ["decidido", "definido", "aprovado"],
    "dependency": ["depende de", "aguardando", "bloqueado"],
    "open_question": ["falta definir", "a definir", "em aberto", "pendente definir"],
}

OWNER_PATTERNS = [
    r"responsável\s*:\s*([\w\sÀ-ÿ'.-]+)",
    r"owner\s*:\s*([\w\sÀ-ÿ'.-]+)",
    r"dono\s*:\s*([\w\sÀ-ÿ'.-]+)",
    r"com\s*:\s*([\w\sÀ-ÿ'.-]+)",
    r"a cargo de\s*:\s*([\w\sÀ-ÿ'.-]+)",
]

DUE_DATE_PATTERNS = [
    r"prazo\s*:\s*(\d{2}/\d{2}/\d{4})",
    r"data limite\s*:\s*(\d{2}/\d{2}/\d{4})",
    r"até\s+(\d{2}/\d{2}/\d{4})",
    r"due date\s*:\s*(\d{4}-\d{2}-\d{2})",
]


def infer_item_type(line: str) -> str | None:
    normalized = line.lower().strip()
    if not normalized:
        return None

    if normalized.endswith("?"):
        return "open_question"

    for item_type, words in ITEM_KEYWORDS.items():
        if any(word in normalized for word in words):
            return item_type

    return None


def infer_owner(line: str) -> str | None:
    for pattern in OWNER_PATTERNS:
        match = re.search(pattern, line, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip(" .")
    return None


def infer_due_date(line: str) -> str | None:
    for pattern in DUE_DATE_PATTERNS:
        match = re.search(pattern, line, flags=re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def infer_severity(line: str) -> str:
    lowered = line.lower()
    if any(word in lowered for word in ["alto", "alta", "crítico", "crítica", "grave"]):
        return "high"
    if any(word in lowered for word in ["médio", "média", "moderado"]):
        return "medium"
    if any(word in lowered for word in ["baixo", "baixa"]):
        return "low"
    return "medium"


def is_owner_or_due_line(line: str) -> bool:
    lowered = line.lower().strip()
    return any(
        marker in lowered
        for marker in ["responsável", "owner", "dono", "com:", "a cargo de", "prazo", "data limite", "due date", "até "]
    )


def is_duplicate_candidate(last_item: dict[str, Any] | None, item_type: str, line: str) -> bool:
    if not last_item or last_item["item_type"] != item_type:
        return False

    last_excerpt = last_item.get("source_excerpt", "")
    if line.lower() == last_excerpt.lower():
        return True

    similarity = SequenceMatcher(None, line.lower(), last_excerpt.lower()).ratio()
    return similarity > 0.9


def extract_pm_items(text: str, document_id: int, project_id: int) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    last_item: dict[str, Any] | None = None

    for line in lines:
        owner = infer_owner(line)
        due_date = infer_due_date(line)

        if last_item and last_item["item_type"] == "action" and (owner or due_date) and is_owner_or_due_line(line):
            if owner and not last_item.get("owner"):
                last_item["owner"] = owner
            if due_date and not last_item.get("due_date"):
                last_item["due_date"] = due_date
            last_item["source_excerpt"] = f"{last_item['source_excerpt']} | {line}"
            continue

        item_type = infer_item_type(line)
        if not item_type:
            continue

        if is_duplicate_candidate(last_item, item_type, line):
            continue

        item = {
            "project_id": project_id,
            "document_id": document_id,
            "item_type": item_type,
            "title": line[:120],
            "description": line,
            "owner": owner,
            "due_date": due_date,
            "status": "open",
            "severity": infer_severity(line),
            "source_excerpt": line,
        }
        items.append(item)
        last_item = item

    return items

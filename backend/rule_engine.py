from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from .models import Alert, Document, PMItem


def _contains_mitigation(text: str | None) -> bool:
    if not text:
        return False
    lowered = text.lower()
    return any(k in lowered for k in ["mitig", "plano", "conting", "reduzir", "tratamento"])


def generate_alerts(project_id: int, db: Session):
    db.query(Alert).filter(Alert.project_id == project_id).delete()

    items = db.query(PMItem).filter(PMItem.project_id == project_id).all()
    documents = db.query(Document).filter(Document.project_id == project_id).all()

    actions = [i for i in items if i.item_type == "action"]
    decisions = [i for i in items if i.item_type == "decision"]
    risks = [i for i in items if i.item_type == "risk"]

    for action in actions:
        if not action.owner:
            db.add(Alert(
                project_id=project_id,
                alert_type="action_missing_owner",
                title="Ação sem responsável",
                description=f"A ação '{action.title}' não possui responsável.",
                severity="high",
                related_item_id=action.id,
                status="open",
            ))
        if not action.due_date:
            db.add(Alert(
                project_id=project_id,
                alert_type="action_missing_due_date",
                title="Ação sem prazo",
                description=f"A ação '{action.title}' não possui data limite.",
                severity="medium",
                related_item_id=action.id,
                status="open",
            ))

    for risk in risks:
        if not _contains_mitigation(risk.description):
            db.add(Alert(
                project_id=project_id,
                alert_type="risk_without_mitigation",
                title="Risco sem mitigação clara",
                description=f"O risco '{risk.title}' não descreve mitigação clara.",
                severity="high",
                related_item_id=risk.id,
                status="open",
            ))

    if decisions and not actions:
        for decision in decisions:
            db.add(Alert(
                project_id=project_id,
                alert_type="decision_without_action",
                title="Decisão sem ação relacionada",
                description=f"A decisão '{decision.title}' não possui ação relacionada.",
                severity="medium",
                related_item_id=decision.id,
                status="open",
            ))

    stale_limit = datetime.utcnow() - timedelta(days=30)
    for doc in documents:
        if doc.status == "error":
            db.add(Alert(
                project_id=project_id,
                alert_type="document_processing_error",
                title="Documento com erro de processamento",
                description=f"Falha ao processar '{doc.filename}'.",
                severity="high",
                related_document_id=doc.id,
                status="open",
            ))
        if doc.updated_at < stale_limit:
            db.add(Alert(
                project_id=project_id,
                alert_type="document_stale",
                title="Documento possivelmente desatualizado",
                description=f"O documento '{doc.filename}' não é atualizado há mais de 30 dias.",
                severity="low",
                related_document_id=doc.id,
                status="open",
            ))

    db.commit()

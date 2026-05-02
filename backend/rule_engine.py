from datetime import datetime, timedelta
import re

from sqlalchemy.orm import Session

from .models import Alert, Document, PMItem


def _contains_mitigation(text: str | None) -> bool:
    if not text:
        return False
    lowered = text.lower()
    return any(k in lowered for k in ["mitig", "plano", "conting", "reduzir", "tratamento"])


def _keywords(text: str) -> set[str]:
    tokens = re.findall(r"[a-zA-ZÀ-ÿ]{4,}", text.lower())
    stopwords = {
        "para", "com", "isso", "essa", "esse", "deve", "mais", "como", "sobre", "entre", "quando", "onde", "qual", "quais",
        "ação", "acoes", "decisão", "decisao", "projeto", "time", "status",
    }
    return {token for token in tokens if token not in stopwords}


def _has_related_action(decision: PMItem, actions: list[PMItem]) -> bool:
    decision_terms = _keywords(decision.description or decision.title)
    if not decision_terms:
        return bool(actions)

    for action in actions:
        action_terms = _keywords(action.description or action.title)
        if not action_terms:
            continue

        overlap = decision_terms.intersection(action_terms)
        ratio = len(overlap) / max(1, len(decision_terms))
        if overlap and ratio >= 0.2:
            return True
    return False


def generate_alerts(project_id: int, db: Session):
    db.query(Alert).filter(Alert.project_id == project_id).delete(synchronize_session=False)
    db.commit()

    items = db.query(PMItem).filter(PMItem.project_id == project_id).all()
    documents = db.query(Document).filter(Document.project_id == project_id).all()

    actions = [i for i in items if i.item_type == "action"]
    decisions = [i for i in items if i.item_type == "decision"]
    risks = [i for i in items if i.item_type == "risk"]
    dependencies = [i for i in items if i.item_type == "dependency"]
    open_questions = [i for i in items if i.item_type == "open_question"]

    for action in actions:
        if not action.owner:
            db.add(Alert(
                project_id=project_id,
                alert_type="action_missing_owner",
                title="Ação sem responsável",
                description=(
                    f"Item: '{action.title}'. Motivo: a ação não possui responsável definido. "
                    "Impacto: risco de atraso por falta de accountability. "
                    "Próximo passo: atribuir owner e comunicar ao time."
                ),
                severity="high",
                related_item_id=action.id,
                status="open",
            ))
        if not action.due_date:
            db.add(Alert(
                project_id=project_id,
                alert_type="action_missing_due_date",
                title="Ação sem prazo",
                description=(
                    f"Item: '{action.title}'. Motivo: a ação não possui data limite. "
                    "Impacto: dificuldade de priorização e acompanhamento. "
                    "Próximo passo: definir um prazo e atualizar o artefato."
                ),
                severity="medium",
                related_item_id=action.id,
                status="open",
            ))

    for risk in risks:
        if not risk.owner:
            db.add(Alert(
                project_id=project_id,
                alert_type="risk_missing_owner",
                title="Risco sem responsável",
                description=(
                    f"Item: '{risk.title}'. Motivo: o risco não possui owner. "
                    "Impacto: mitigação pode não ser executada no tempo certo. "
                    "Próximo passo: indicar responsável pelo monitoramento do risco."
                ),
                severity="medium",
                related_item_id=risk.id,
                status="open",
            ))

        if not _contains_mitigation(risk.description):
            db.add(Alert(
                project_id=project_id,
                alert_type="risk_without_mitigation",
                title="Risco sem mitigação clara",
                description=(
                    f"Item: '{risk.title}'. Motivo: não há mitigação explícita na descrição. "
                    "Impacto: risco pode materializar sem plano de resposta. "
                    "Próximo passo: registrar estratégia de mitigação e contingência."
                ),
                severity="high",
                related_item_id=risk.id,
                status="open",
            ))

    for dep in dependencies:
        if not dep.owner:
            db.add(Alert(
                project_id=project_id,
                alert_type="dependency_missing_owner",
                title="Dependência sem responsável",
                description=(
                    f"Item: '{dep.title}'. Motivo: dependência sem owner definido. "
                    "Impacto: bloqueios podem permanecer sem tratativa. "
                    "Próximo passo: nomear responsável e definir plano de desbloqueio."
                ),
                severity="high",
                related_item_id=dep.id,
                status="open",
            ))

    for question in open_questions:
        if not question.owner:
            db.add(Alert(
                project_id=project_id,
                alert_type="open_question_missing_owner",
                title="Pergunta em aberto sem responsável",
                description=(
                    f"Item: '{question.title}'. Motivo: pergunta em aberto sem owner. "
                    "Impacto: definição pode atrasar decisões e execução. "
                    "Próximo passo: atribuir responsável para resolver a pendência."
                ),
                severity="medium",
                related_item_id=question.id,
                status="open",
            ))

    for decision in decisions:
        if not _has_related_action(decision, actions):
            db.add(Alert(
                project_id=project_id,
                alert_type="decision_without_action",
                title="Decisão sem ação relacionada",
                description=(
                    f"Item: '{decision.title}'. Motivo: não foi encontrada ação relacionada por similaridade de termos. "
                    "Impacto: decisão pode não se converter em execução. "
                    "Próximo passo: criar ação vinculada com owner e prazo."
                ),
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
                description=(
                    f"Documento: '{doc.filename}'. Motivo: falha no processamento. "
                    "Impacto: conteúdo não entra nas análises do projeto. "
                    "Próximo passo: revisar formato/arquivo e reenviar."
                ),
                severity="high",
                related_document_id=doc.id,
                status="open",
            ))
        if doc.updated_at < stale_limit:
            db.add(Alert(
                project_id=project_id,
                alert_type="document_stale",
                title="Documento possivelmente desatualizado",
                description=(
                    f"Documento: '{doc.filename}'. Motivo: sem atualização há mais de 30 dias. "
                    "Impacto: decisões podem usar informações antigas. "
                    "Próximo passo: validar se o documento ainda está vigente."
                ),
                severity="low",
                related_document_id=doc.id,
                status="open",
            ))

    db.commit()

from sqlalchemy.orm import Session

from .models import Alert, Document, PMItem, Project


def generate_executive_report(project_id: int, db: Session) -> str:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return "Projeto não encontrado."

    docs = db.query(Document).filter(Document.project_id == project_id).all()
    items = db.query(PMItem).filter(PMItem.project_id == project_id).all()
    alerts = db.query(Alert).filter(Alert.project_id == project_id).order_by(Alert.created_at.desc()).all()

    risks = [i for i in items if i.item_type == "risk"][:5]
    actions = [i for i in items if i.item_type == "action"][:5]
    decisions = [i for i in items if i.item_type == "decision"][:5]

    def bullet(lines):
        return "\n".join(f"- {line}" for line in lines) if lines else "- Nenhum"

    report = f"""Relatório Executivo - PM Companion MVP

Projeto: {project.name}
Descrição: {project.description or 'Sem descrição'}

Documentos analisados ({len(docs)}):
{bullet([f'{d.filename} ({d.status})' for d in docs])}

Principais riscos:
{bullet([r.title for r in risks])}

Principais ações:
{bullet([f"{a.title} | Responsável: {a.owner or 'N/D'}" for a in actions])}

Principais decisões:
{bullet([d.title for d in decisions])}

Principais alertas:
{bullet([f'[{al.severity}] {al.title}' for al in alerts[:8]])}

Próximas ações recomendadas:
- Definir responsáveis e prazos para ações pendentes.
- Revisar riscos sem mitigação explícita.
- Validar decisões sem desdobramento em plano de ação.
"""
    return report.strip()

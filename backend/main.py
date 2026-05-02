from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func
from sqlalchemy.orm import Session

from .database import Base, UPLOAD_DIR, engine, get_db
from .extract_text import extract_text
from .models import Alert, Document, PMItem, Project
from .pm_extractor import extract_pm_items
from .report_generator import generate_executive_report
from .rule_engine import generate_alerts

Base.metadata.create_all(bind=engine)

app = FastAPI(title="PM Companion MVP")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")


@app.get("/")
def root():
    return FileResponse(Path("frontend/index.html"))


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/projects")
def create_project(name: str = Form(...), description: Optional[str] = Form(None), db: Session = Depends(get_db)):
    project = Project(name=name, description=description)
    db.add(project)
    db.commit()
    db.refresh(project)
    (UPLOAD_DIR / str(project.id)).mkdir(parents=True, exist_ok=True)
    return project


@app.get("/projects")
def list_projects(db: Session = Depends(get_db)):
    return db.query(Project).order_by(Project.created_at.desc()).all()


@app.get("/projects/{project_id}")
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    return project


@app.post("/projects/{project_id}/upload")
def upload_documents(project_id: int, files: list[UploadFile] = File(...), db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

    allowed = {".txt", ".md", ".csv", ".xlsx", ".docx", ".pdf"}
    saved = []
    project_upload = UPLOAD_DIR / str(project_id)
    project_upload.mkdir(parents=True, exist_ok=True)

    for file in files:
        safe_name = Path(file.filename).name
        suffix = Path(safe_name).suffix.lower()
        if suffix not in allowed:
            continue

        destination = project_upload / safe_name
        destination.write_bytes(file.file.read())

        document = Document(
            project_id=project_id,
            filename=safe_name,
            file_path=str(destination),
            file_type=suffix,
            status="uploaded",
        )
        db.add(document)
        saved.append(file.filename)

    if not saved:
        raise HTTPException(status_code=400, detail="Nenhum arquivo suportado foi enviado")

    db.commit()
    return {"uploaded": saved}


@app.post("/projects/{project_id}/process")
def process_project(project_id: int, db: Session = Depends(get_db)):
    documents = db.query(Document).filter(Document.project_id == project_id).all()
    if not documents:
        raise HTTPException(status_code=404, detail="Nenhum documento encontrado")

    db.query(PMItem).filter(PMItem.project_id == project_id).delete()
    db.commit()

    processed = 0
    errors = 0
    for doc in documents:
        try:
            text = extract_text(doc.file_path)
            doc.extracted_text = text
            doc.status = "processed"
            doc.error_message = None
            items = extract_pm_items(text, doc.id, project_id)
            for item_data in items:
                db.add(PMItem(**item_data))
            processed += 1
        except Exception as exc:
            doc.status = "error"
            doc.error_message = str(exc)
            errors += 1

    db.commit()
    generate_alerts(project_id, db)
    return {"processed": processed, "errors": errors}


@app.get("/projects/{project_id}/documents")
def list_documents(project_id: int, db: Session = Depends(get_db)):
    return db.query(Document).filter(Document.project_id == project_id).all()


@app.get("/projects/{project_id}/items")
def list_items(project_id: int, db: Session = Depends(get_db)):
    return db.query(PMItem).filter(PMItem.project_id == project_id).all()


@app.get("/projects/{project_id}/alerts")
def list_alerts(project_id: int, db: Session = Depends(get_db)):
    return db.query(Alert).filter(Alert.project_id == project_id).order_by(Alert.created_at.desc()).all()


@app.get("/projects/{project_id}/dashboard")
def dashboard(project_id: int, db: Session = Depends(get_db)):
    total_docs = db.query(func.count(Document.id)).filter(Document.project_id == project_id).scalar()
    processed_docs = db.query(func.count(Document.id)).filter(Document.project_id == project_id, Document.status == "processed").scalar()
    total_items = db.query(func.count(PMItem.id)).filter(PMItem.project_id == project_id).scalar()

    by_type = dict(db.query(PMItem.item_type, func.count(PMItem.id)).filter(PMItem.project_id == project_id).group_by(PMItem.item_type).all())
    total_alerts = db.query(func.count(Alert.id)).filter(Alert.project_id == project_id).scalar()
    alerts_by_severity = dict(db.query(Alert.severity, func.count(Alert.id)).filter(Alert.project_id == project_id).group_by(Alert.severity).all())

    return {
        "total_documents": total_docs,
        "total_documents_processed": processed_docs,
        "total_items_found": total_items,
        "total_actions": by_type.get("action", 0),
        "total_risks": by_type.get("risk", 0),
        "total_decisions": by_type.get("decision", 0),
        "total_dependencies": by_type.get("dependency", 0),
        "total_open_questions": by_type.get("open_question", 0),
        "total_alerts": total_alerts,
        "alerts_by_severity": alerts_by_severity,
    }


@app.get("/projects/{project_id}/report")
def project_report(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

    report = generate_executive_report(project_id, db)
    return {"report": report}

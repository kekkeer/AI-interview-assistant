import os
import uuid

from fastapi import APIRouter, Depends, Form, Request, UploadFile, File
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Resume
from app.render import render, get_current_user
from app.services.document_parser import parse_file
from app.services.rag_service import chunk_text, build_index, generate_from_resume

router = APIRouter(prefix="/resume", tags=["resume"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

_index_cache = {}
_chunks_cache = {}


@router.get("/")
def resume_page(request: Request, db: Session = Depends(get_db)):
  user = get_current_user(request)
  if not user:
    return RedirectResponse(url="/auth/login", status_code=302)

  resume = db.query(Resume).filter(Resume.user_id == user.id).order_by(Resume.id.desc()).first()
  return render("resume/upload.html", request=request, resume=resume)


@router.post("/upload")
async def upload_resume(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
  user = get_current_user(request)
  if not user:
    return RedirectResponse(url="/auth/login", status_code=302)

  ext = os.path.splitext(file.filename)[1].lower()
  if ext not in (".pdf", ".docx"):
    return render("resume/upload.html", request=request, resume=None, error="仅支持 PDF 和 DOCX 文件")

  save_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}{ext}")
  content = await file.read()
  with open(save_path, "wb") as f:
    f.write(content)

  try:
    text = parse_file(save_path)
  except Exception as e:
    return render("resume/upload.html", request=request, resume=None, error=f"解析失败: {e}")

  resume = Resume(user_id=user.id, filename=file.filename, content=text, status="parsed")
  db.add(resume)
  db.commit()

  chunks = chunk_text(text)
  index, _ = build_index(chunks)
  _index_cache[user.id] = index
  _chunks_cache[user.id] = chunks

  return RedirectResponse(url="/resume/", status_code=302)


@router.get("/interview")
def resume_interview(request: Request, db: Session = Depends(get_db)):
  user = get_current_user(request)
  if not user:
    return RedirectResponse(url="/auth/login", status_code=302)

  resume = db.query(Resume).filter(Resume.user_id == user.id).order_by(Resume.id.desc()).first()
  if not resume or resume.status != "parsed":
    return RedirectResponse(url="/resume/", status_code=302)

  index = _index_cache.get(user.id)
  chunks = _chunks_cache.get(user.id)
  if index is None or chunks is None:
    chunks = chunk_text(resume.content)
    index, _ = build_index(chunks)
    _index_cache[user.id] = index
    _chunks_cache[user.id] = chunks

  try:
    questions = generate_from_resume(chunks, index, resume.content[:200])
  except RuntimeError as e:
    return render("resume/upload.html", request=request, resume=resume, error=str(e))

  return render("resume/interview.html", request=request, questions=questions, filename=resume.filename)

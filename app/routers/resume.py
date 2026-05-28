import os
import uuid
import traceback

from fastapi import APIRouter, Depends, Form, Request, UploadFile, File
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Resume
from app.render import render, get_current_user
from app.services.document_parser import parse_file
from app.services.rag_service import chunk_text, build_index, generate_from_resume
from app.services.scoring_service import score_interview

router = APIRouter(prefix="/resume", tags=["resume"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

_index_cache = {}
_chunks_cache = {}
_questions_cache = {}
_results_cache = {}
MAX_TEXT_LEN = 5000


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

  text = text[:MAX_TEXT_LEN]
  resume = Resume(user_id=user.id, filename=file.filename, content=text, status="parsed")
  db.add(resume)
  db.commit()

  try:
    chunks = chunk_text(text)
    index, _ = build_index(chunks)
    _index_cache[user.id] = index
    _chunks_cache[user.id] = chunks
  except Exception as e:
    traceback.print_exc()
    return render("resume/upload.html", request=request, resume=resume, error=f"向量化失败: {e}")

  return RedirectResponse(url="/resume/", status_code=302)


@router.get("/delete")
def delete_resume(request: Request, db: Session = Depends(get_db)):
  user = get_current_user(request)
  if not user:
    return RedirectResponse(url="/auth/login", status_code=302)

  db.query(Resume).filter(Resume.user_id == user.id).delete()
  db.commit()
  for cache in (_index_cache, _chunks_cache, _questions_cache, _results_cache):
    cache.pop(user.id, None)
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
    try:
      chunks = chunk_text(resume.content)
      index, _ = build_index(chunks)
      _index_cache[user.id] = index
      _chunks_cache[user.id] = chunks
    except Exception as e:
      return render("resume/upload.html", request=request, resume=resume, error=f"向量化失败，请重新上传简历: {e}")

  try:
    questions = generate_from_resume(chunks, index, resume.content[:200])
  except Exception as e:
    return render("resume/upload.html", request=request, resume=resume, error=f"出题失败: {e}")

  _questions_cache[user.id] = questions
  return RedirectResponse(url="/resume/take", status_code=302)


@router.get("/take")
def resume_take(request: Request):
  user = get_current_user(request)
  if not user:
    return RedirectResponse(url="/auth/login", status_code=302)

  questions = _questions_cache.get(user.id)
  if not questions:
    return RedirectResponse(url="/resume/", status_code=302)

  return render("resume/take.html", request=request, questions=questions)


@router.post("/submit")
async def resume_submit(request: Request, db: Session = Depends(get_db)):
  user = get_current_user(request)
  if not user:
    return RedirectResponse(url="/auth/login", status_code=302)

  questions = _questions_cache.get(user.id)
  if not questions:
    return RedirectResponse(url="/resume/", status_code=302)

  resume = db.query(Resume).filter(Resume.user_id == user.id).order_by(Resume.id.desc()).first()
  filename = resume.filename if resume else ""

  form = await request.form()
  scored = []
  for q in questions:
    answer = form.get(f"answer_{q['order']}", "") or ""
    scored.append({"order": q["order"], "content": q["content"], "answer": answer})

  try:
    result = score_interview("简历面试 - " + filename, scored)
    for i, q in enumerate(scored):
      s = result.get("scores", [])[i] if i < len(result.get("scores", [])) else {}
      q["score"] = s.get("score", 0)
      q["comment"] = s.get("comment", "")

    total = sum(q.get("score", 0) for q in scored)
    total_score = round(total / len(scored), 1) if scored else 0
  except Exception as e:
    return render("resume/upload.html", request=request, resume=resume, error=f"评分失败: {e}")

  _results_cache[user.id] = {"results": scored, "total_score": total_score, "filename": filename}
  return RedirectResponse(url="/resume/result", status_code=302)


@router.get("/result")
def resume_result(request: Request):
  user = get_current_user(request)
  if not user:
    return RedirectResponse(url="/auth/login", status_code=302)

  data = _results_cache.get(user.id)
  if not data:
    return RedirectResponse(url="/resume/", status_code=302)

  return render("resume/result.html", request=request, **data)

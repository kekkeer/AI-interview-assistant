from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Interview, Question, Position
from app.render import render, get_current_user
from app.services.ai_service import generate_questions
from app.services.scoring_service import score_interview

router = APIRouter(prefix="/interview", tags=["interview"])
PER_PAGE = 10


@router.get("/history")
def history(request: Request, page: int = 1, position_id: str = "", db: Session = Depends(get_db)):
  user = get_current_user(request)
  if not user:
    return RedirectResponse(url="/auth/login", status_code=302)

  q = db.query(Interview).filter(Interview.user_id == user.id)
  pid = int(position_id) if position_id and position_id.isdigit() else None
  if pid:
    q = q.filter(Interview.position_id == pid)

  total = q.count()
  total_pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)
  page = max(1, min(page, total_pages))

  interviews = q.order_by(Interview.created_at.desc()).offset((page - 1) * PER_PAGE).limit(PER_PAGE).all()
  all_positions = db.query(Position).order_by(Position.id).all()

  return render("history.html", request=request,
    interviews=interviews, all_positions=all_positions,
    page=page, total_pages=total_pages, position_id=pid)


@router.get("/{id}/take")
def take_interview(id: int, request: Request, db: Session = Depends(get_db)):
  user = get_current_user(request)
  if not user:
    return RedirectResponse(url="/auth/login", status_code=302)

  interview = db.query(Interview).filter(Interview.id == id, Interview.user_id == user.id).first()
  if not interview:
    return RedirectResponse(url="/positions/", status_code=302)

  questions = db.query(Question).filter(Question.interview_id == id).order_by(Question.order).all()
  if not questions:
    return RedirectResponse(url="/positions/", status_code=302)

  position_title = interview.position.title if interview.position else ""

  return render(
    "interview/take.html",
    request=request,
    interview=interview,
    question=questions[0],
    total=len(questions),
    position_title=position_title,
    interview_id=interview.id,
  )


@router.post("/{id}/answer")
def save_answer(
  id: int,
  request: Request,
  question_id: int = Form(...),
  answer: str = Form(default=""),
  direction: str = Form(...),
  db: Session = Depends(get_db),
):
  user = get_current_user(request)
  if not user:
    return RedirectResponse(url="/auth/login", status_code=302)

  q = db.query(Question).filter(Question.id == question_id).first()
  if q:
    q.answer = answer
    db.commit()

  all_questions = db.query(Question).filter(Question.interview_id == id).order_by(Question.order).all()
  current_idx = next((i for i, x in enumerate(all_questions) if x.id == question_id), 0)

  if direction == "next":
    next_idx = current_idx + 1
  else:
    next_idx = current_idx - 1

  next_idx = max(0, min(next_idx, len(all_questions) - 1))
  next_q = all_questions[next_idx]

  return render(
    "interview/_question.html",
    request=request,
    question=next_q,
    total=len(all_questions),
    interview_id=id,
  )


@router.post("/{id}/submit")
def submit_interview(
  id: int,
  request: Request,
  question_id: int = Form(...),
  answer: str = Form(default=""),
  db: Session = Depends(get_db),
):
  user = get_current_user(request)
  if not user:
    return RedirectResponse(url="/auth/login", status_code=302)

  q = db.query(Question).filter(Question.id == question_id).first()
  if q:
    q.answer = answer
    db.commit()

  interview = db.query(Interview).filter(Interview.id == id).first()
  if not interview:
    return RedirectResponse(url="/positions/", status_code=302)

  all_questions = db.query(Question).filter(Question.interview_id == id).order_by(Question.order).all()
  title = interview.position.title if interview.position else ""

  try:
    result = score_interview(title, [
      {"order": q.order, "content": q.content, "answer": q.answer or ""}
      for q in all_questions
    ])

    total = 0
    for s in result.get("scores", []):
      question = next((q for q in all_questions if q.order == s["order"]), None)
      if question:
        question.score = s["score"]
        question.comment = s.get("comment", "")
        total += s["score"]

    interview.total_score = round(total / len(all_questions), 1) if all_questions else 0
    interview.status = "completed"
    db.commit()
  except RuntimeError as e:
    interview.status = "completed"
    db.commit()

  return RedirectResponse(url=f"/interview/{id}/result", status_code=302)


@router.get("/{id}/result")
def interview_result(id: int, request: Request, db: Session = Depends(get_db)):
  user = get_current_user(request)
  if not user:
    return RedirectResponse(url="/auth/login", status_code=302)

  interview = db.query(Interview).filter(Interview.id == id, Interview.user_id == user.id).first()
  if not interview:
    return RedirectResponse(url="/positions/", status_code=302)

  questions = db.query(Question).filter(Question.interview_id == id).order_by(Question.order).all()
  position_title = interview.position.title if interview.position else ""

  return render(
    "interview/result.html",
    request=request,
    interview=interview,
    questions=questions,
    position_title=position_title,
    position_id=interview.position_id,
  )

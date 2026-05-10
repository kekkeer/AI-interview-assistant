from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Interview, Question
from app.render import render, get_current_user
from app.services.ai_service import generate_questions

router = APIRouter(prefix="/interview", tags=["interview"])


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
  if interview:
    interview.status = "completed"
    db.commit()

  return RedirectResponse(url=f"/interview/{id}/result", status_code=302)

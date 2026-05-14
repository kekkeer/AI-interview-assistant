from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Position, Interview, Question
from app.render import render, get_current_user
from app.services.ai_service import generate_questions

router = APIRouter(prefix="/positions", tags=["positions"])


@router.get("/")
def position_list(request: Request, db: Session = Depends(get_db)):
  positions = db.query(Position).order_by(Position.is_builtin.desc(), Position.id).all()
  return render("positions/list.html", request=request, positions=positions)


@router.get("/create")
def create_position_form(request: Request):
  if not get_current_user(request):
    return RedirectResponse(url="/auth/login", status_code=302)
  return render("positions/create.html", request=request)


@router.post("/create")
def create_position(
  request: Request,
  title: str = Form(...),
  description: str = Form(...),
  db: Session = Depends(get_db),
):
  user = get_current_user(request)
  if not user:
    return RedirectResponse(url="/auth/login", status_code=302)

  position = Position(title=title, description=description, is_builtin=False)
  db.add(position)
  db.commit()
  db.refresh(position)
  return RedirectResponse(url=f"/positions/{position.id}", status_code=302)


@router.get("/{id}")
def position_detail(id: int, request: Request, db: Session = Depends(get_db)):
  user = get_current_user(request)
  if not user:
    return RedirectResponse(url="/auth/login", status_code=302)

  position = db.query(Position).filter(Position.id == id).first()
  if not position:
    return render("positions/list.html", request=request, positions=[], error="职位不存在")

  interview = Interview(user_id=user.id, position_id=id)
  db.add(interview)
  db.commit()
  db.refresh(interview)

  try:
    questions_data = generate_questions(position.title, position.description)
  except RuntimeError as e:
    return render("positions/list.html", request=request, positions=[], error=str(e))

  for q in questions_data:
    db.add(Question(interview_id=interview.id, content=q["content"], order=q["order"]))
  db.commit()

  return render("positions/detail.html", request=request, interview=interview, position=position)

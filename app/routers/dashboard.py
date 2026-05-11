from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Interview, Position
from app.render import render, get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/")
def dashboard(request: Request, db: Session = Depends(get_db)):
  user = get_current_user(request)
  if not user:
    return RedirectResponse(url="/auth/login", status_code=302)

  total = db.query(func.count(Interview.id)).filter(Interview.user_id == user.id).scalar() or 0
  avg_score = db.query(func.avg(Interview.total_score)).filter(
    Interview.user_id == user.id, Interview.status == "completed"
  ).scalar()
  avg_score = round(avg_score, 1) if avg_score else 0
  max_score = db.query(func.max(Interview.total_score)).filter(
    Interview.user_id == user.id, Interview.status == "completed"
  ).scalar() or 0

  distribution = db.query(
    Position.title, func.count(Interview.id)
  ).join(Position, Interview.position_id == Position.id).filter(
    Interview.user_id == user.id
  ).group_by(Position.title).all()

  recent = db.query(Interview.total_score).filter(
    Interview.user_id == user.id, Interview.status == "completed"
  ).order_by(Interview.created_at).limit(15).all()
  scores = [r[0] for r in recent if r[0] is not None]

  return render("dashboard.html", request=request,
    total=total, avg_score=avg_score, max_score=max_score,
    distribution=distribution, scores=scores)

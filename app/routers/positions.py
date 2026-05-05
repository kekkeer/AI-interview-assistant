from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Position
from app.render import render

router = APIRouter(prefix="/positions", tags=["positions"])


@router.get("/")
def position_list(request: Request, db: Session = Depends(get_db)):
  positions = db.query(Position).order_by(Position.is_builtin.desc(), Position.id).all()
  return render("positions/list.html", request=request, positions=positions)

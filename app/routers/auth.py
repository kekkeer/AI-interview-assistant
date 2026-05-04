from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.render import render
from app.services.auth_service import hash_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/register")
def register_form(request: Request):
  return render("auth/register.html", request=request)


@router.post("/register")
def register(
  request: Request,
  username: str = Form(...),
  email: str = Form(...),
  password: str = Form(...),
  db: Session = Depends(get_db),
):
  existing_user = db.query(User).filter((User.username == username) | (User.email == email)).first()
  if existing_user:
    return render("auth/register.html", request=request, error="用户名或邮箱已被注册")

  user = User(
    username=username,
    email=email,
    hashed_password=hash_password(password),
  )
  db.add(user)
  db.commit()
  db.refresh(user)

  token = create_access_token({"sub": str(user.id)})
  response = RedirectResponse(url="/", status_code=302)
  response.set_cookie(key="access_token", value=f"Bearer {token}", httponly=True)
  return response

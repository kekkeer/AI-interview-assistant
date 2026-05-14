from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.render import render, get_current_user
from app.services.auth_service import hash_password, create_access_token, verify_password

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
  confirm_password: str = Form(...),
  db: Session = Depends(get_db),
):
  if password != confirm_password:
    return render("auth/register.html", request=request, error="两次密码不一致")

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


@router.get("/login")
def login_form(request: Request):
  return render("auth/login.html", request=request)


@router.post("/login")
def login(
  request: Request,
  username: str = Form(...),
  password: str = Form(...),
  db: Session = Depends(get_db),
):
  user = db.query(User).filter(User.username == username).first()
  if not user or not verify_password(password, user.hashed_password):
    return render("auth/login.html", request=request, error="用户名或密码错误")

  token = create_access_token({"sub": str(user.id)})
  response = RedirectResponse(url="/", status_code=302)
  response.set_cookie(key="access_token", value=f"Bearer {token}", httponly=True)
  return response


@router.get("/profile")
def profile(request: Request):
  if not get_current_user(request):
    return RedirectResponse(url="/auth/login", status_code=302)
  return render("profile.html", request=request)


@router.post("/change-password")
def change_password(
  request: Request,
  old_password: str = Form(...),
  new_password: str = Form(...),
  confirm_new_password: str = Form(...),
  db: Session = Depends(get_db),
):
  user = get_current_user(request)
  if not user:
    return RedirectResponse(url="/auth/login", status_code=302)

  if not verify_password(old_password, user.hashed_password):
    return render("profile.html", request=request, error="当前密码不正确")

  if new_password != confirm_new_password:
    return render("profile.html", request=request, error="两次新密码不一致")

  user.hashed_password = hash_password(new_password)
  db.commit()
  return render("profile.html", request=request, success="密码修改成功")


@router.get("/logout")
def logout(request: Request):
  response = RedirectResponse(url="/", status_code=302)
  response.delete_cookie(key="access_token")
  return response

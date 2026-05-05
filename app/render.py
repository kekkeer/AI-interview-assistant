import jinja2
from fastapi import Request
from fastapi.responses import HTMLResponse

from app.database import SessionLocal
from app.models import User
from app.services.auth_service import decode_access_token


_env = jinja2.Environment(
  loader=jinja2.FileSystemLoader("app/templates"),
  autoescape=jinja2.select_autoescape(),
)


def get_current_user(request: Request):
  token_str = request.cookies.get("access_token", "")
  if not token_str.startswith("Bearer "):
    return None
  payload = decode_access_token(token_str[7:])
  if payload is None:
    return None
  user_id = payload.get("sub")
  if user_id is None:
    return None
  db = SessionLocal()
  try:
    user = db.query(User).filter(User.id == int(user_id)).first()
    return user
  finally:
    db.close()


def render(name: str, request: Request, **kwargs):
  user = get_current_user(request)
  template = _env.get_template(name)
  html = template.render(request=request, user=user, **kwargs)
  return HTMLResponse(html)

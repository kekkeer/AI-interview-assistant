import jinja2
from fastapi import Request
from fastapi.responses import HTMLResponse


_env = jinja2.Environment(
  loader=jinja2.FileSystemLoader("app/templates"),
  autoescape=jinja2.select_autoescape(),
)


def render(name: str, request: Request, **kwargs):
  template = _env.get_template(name)
  html = template.render(request=request, **kwargs)
  return HTMLResponse(html)

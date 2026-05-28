import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import engine, Base
from app.render import render
from app.routers import auth, positions, interview, dashboard, resume
from app.services.seed import seed_positions

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


@asynccontextmanager
async def lifespan(app: FastAPI):
  Base.metadata.create_all(bind=engine)
  seed_positions()
  yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

app.include_router(auth.router)
app.include_router(positions.router)
app.include_router(interview.router)
app.include_router(dashboard.router)
app.include_router(resume.router)


@app.exception_handler(404)
async def not_found(request: Request, exc):
  return HTMLResponse(content=render("error.html", request=request, code=404, message="页面不存在").body, status_code=404)

@app.exception_handler(500)
async def server_error(request: Request, exc):
  return HTMLResponse(content=render("error.html", request=request, code=500, message="服务器内部错误").body, status_code=500)

@app.get("/")
def root(request: Request):
  return render("index.html", request=request)

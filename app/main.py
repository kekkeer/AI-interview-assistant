import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import engine, Base
from app.render import render
from app.routers import auth, positions, interview, dashboard
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


@app.get("/")
def root(request: Request):
  return render("index.html", request=request)

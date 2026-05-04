from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import engine, Base
from app.render import render
from app.routers import auth


@asynccontextmanager
async def lifespan(app: FastAPI):
  Base.metadata.create_all(bind=engine)
  yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router)


@app.get("/")
def root(request: Request):
  return render("base.html", request=request)

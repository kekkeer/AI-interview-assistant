from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
  Base.metadata.create_all(bind=engine)
  yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/")
def root():
  return {"message": "AI Interview Assistant is running", "version": "0.1.0"}

@app.get("/ping")
def ping():
    return "pong"

@app.get("/hello/{name}")
def hello(name: str):
    return {"hello": name}

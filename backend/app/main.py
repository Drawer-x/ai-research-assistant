from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError

from app import models
from app.api import agent, auth, graph, papers
from app.core.config import settings
from app.core.response import error_response, success_response
from app.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.upload_path.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return error_response(str(exc.detail), exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = "; ".join(error["msg"] for error in exc.errors())
    return error_response(f"请求参数错误: {errors}", 422)


@app.get("/api/health", tags=["系统"])
def health():
    return success_response(message="backend is running")


app.include_router(auth.router, prefix="/api")
app.include_router(papers.router, prefix="/api")
app.include_router(graph.router, prefix="/api")
app.include_router(agent.router, prefix="/api")

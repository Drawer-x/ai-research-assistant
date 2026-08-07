from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app import models
from app.api import agent, auth, discovery, graph, papers, recommendations
from app.core.config import settings
from app.core.response import error_response, success_response
from app.database import Base, engine
from app.services.crossref_client import CrossrefError, CrossrefNotFound, RateLimitedError, UpstreamTimeoutError


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.upload_path.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.exception_handler(CrossrefNotFound)
async def crossref_not_found(request: Request, exc: CrossrefNotFound): return error_response(str(exc),404)
@app.exception_handler(CrossrefError)
async def crossref_unavailable(request: Request, exc: CrossrefError): return error_response("External paper service unavailable",503)
@app.exception_handler(RateLimitedError)
async def crossref_limited(request: Request, exc: RateLimitedError): return error_response("External paper service requests are too frequent",429)
@app.exception_handler(UpstreamTimeoutError)
async def crossref_timeout(request: Request, exc: UpstreamTimeoutError): return error_response("External paper service is temporarily unavailable",503)
@app.exception_handler(LookupError)
async def lookup_error(request: Request, exc: LookupError): return error_response(str(exc),404)
@app.exception_handler(ValueError)
async def value_error(request: Request, exc: ValueError): return error_response(str(exc),422)

app.include_router(auth.router, prefix="/api")
app.include_router(papers.router, prefix="/api")
app.include_router(graph.router, prefix="/api")
app.include_router(agent.router, prefix="/api")
app.include_router(discovery.router, prefix="/api")
app.include_router(recommendations.router, prefix="/api")

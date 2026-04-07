from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.core.exceptions import ConflictError, NotFoundError, UnauthorizedError
from app.database.session import MongoSession
from app.routers.auth import router as auth_router
from app.routers.categories import router as category_router
from app.routers.products import router as product_router
from app.routers.uploads import router as upload_router

settings = get_settings()
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(_: FastAPI):
    db = MongoSession()
    db.ping()
    db.ensure_indexes()
    db.close()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(category_router, prefix=settings.api_v1_prefix)
app.include_router(product_router, prefix=settings.api_v1_prefix)
app.include_router(upload_router, prefix=settings.api_v1_prefix)
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")


@app.get("/health")
def health_check():
    return {"status": "ok", "environment": settings.app_env}


@app.exception_handler(NotFoundError)
async def handle_not_found(_: Request, exc: NotFoundError):
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})


@app.exception_handler(ConflictError)
async def handle_conflict(_: Request, exc: ConflictError):
    return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)})


@app.exception_handler(UnauthorizedError)
async def handle_unauthorized(_: Request, exc: UnauthorizedError):
    return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"detail": str(exc)})


@app.exception_handler(RequestValidationError)
async def handle_validation(_: Request, exc: RequestValidationError):
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": exc.errors()})

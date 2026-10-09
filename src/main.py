import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from db import check_connection
from ragchat.constants import CHROMA_DIR, COLLECTION_NAME, DATA_DIR
from ragchat.rag_engine import ensure_index
from ragchat.router import router as ragchat_router

logger = logging.getLogger("chatbot-profile")

HOST = "0.0.0.0"
PORT = 8000


def configure_logging() -> None:
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(logging.INFO)
    root.addHandler(handler)

    for name in (
        "chatbot-profile",
        "ragchat",
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "fastapi",
    ):
        logging.getLogger(name).setLevel(logging.INFO)

    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)


def _mask_db_url(url: str) -> str:
    parts = urlsplit(url)
    if parts.password:
        netloc = parts.netloc.replace(f":{parts.password}@", ":***@")
        return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))
    return url


def _log_db_connection() -> None:
    url = settings.database_url
    parts = urlsplit(url)
    logger.info("DB connecting url=%s", _mask_db_url(url))
    logger.info(
        "DB target host=%s port=%s database=%s user=%s",
        parts.hostname,
        parts.port,
        (parts.path or "").lstrip("/"),
        parts.username,
    )
    try:
        info = check_connection()
        logger.info(
            "DB connected ok database=%s user=%s",
            info["database"],
            info["user"],
        )
        logger.info("DB server: %s", info["version"])
    except Exception:
        logger.exception("DB connection FAILED")
        raise


def _log_startup() -> None:
    logger.info("Starting chatbot-profile")
    logger.info("Listen http://%s:%s", HOST, PORT)
    logger.info("Swagger http://localhost:%s/docs", PORT)
    logger.info("ReDoc   http://localhost:%s/redoc", PORT)
    logger.info("Health  http://localhost:%s/health", PORT)
    logger.info("CORS origins: %s", settings.cors_origins)
    logger.info("Gemini keys configured: %s", len(settings.gemini_keys))
    logger.info("Chroma collection=%s path=%s", COLLECTION_NAME, CHROMA_DIR)
    logger.info("Profile data dir: %s", DATA_DIR)
    md_files = sorted(p.name for p in DATA_DIR.glob("*.md")) if DATA_DIR.exists() else []
    logger.info("Markdown files: %s", md_files or "(none — ingest skipped)")
    _log_db_connection()


configure_logging()


@asynccontextmanager
async def lifespan(_: FastAPI):
    _log_startup()
    logger.info("Running rag_engine.ensure_index()")
    ensure_index()
    logger.info("Startup complete")
    yield
    logger.info("Shutting down chatbot-profile")


app = FastAPI(title="chatbot-profile", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(ragchat_router, prefix="/ragchat")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    started = time.perf_counter()
    logger.info("--> %s %s", request.method, request.url.path)
    try:
        response = await call_next(request)
    except Exception:
        elapsed_ms = (time.perf_counter() - started) * 1000
        logger.exception("xx %s %s failed after %.1fms", request.method, request.url.path, elapsed_ms)
        raise
    elapsed_ms = (time.perf_counter() - started) * 1000
    logger.info(
        "<-- %s %s %s %.1fms",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response


@app.get("/health")
def health():
    logger.info("Health check ok")
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    src_dir = Path(__file__).resolve().parent
    logger.info("Launch via python src/main.py (app_dir=%s)", src_dir)
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=True,
        app_dir=str(src_dir),
        log_level="info",
        access_log=True,
        use_colors=True,
    )

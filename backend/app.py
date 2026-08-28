import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from config import get_settings
from database import init_db, seed_db, schema_ready
from routes import spots, bids, webhooks, admin

settings = get_settings()

app = FastAPI(title="Marcá Mi Notebook")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging
logger.remove()
logger.add(sys.stdout, format="<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")

# Routes
app.include_router(spots.router, prefix="/api", tags=["spots"])
app.include_router(bids.router, prefix="/api", tags=["bids"])
app.include_router(webhooks.router, prefix="/api", tags=["webhooks"])
app.include_router(admin.router, prefix="/api", tags=["admin"])

@app.on_event("startup")
async def startup():
    # One round-trip to skip init+seed on every cold start once the schema already exists
    if not schema_ready():
        init_db()
        seed_db()
    logger.info("Database ready")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/meta")
def meta():
    return {
        "auction_ends_at": settings.auction_ends_at,
        "ars_per_usd": settings.ars_per_usd,
    }

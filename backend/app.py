from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings

settings = get_settings()

app = FastAPI(title="Marca Mi Notebook")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}

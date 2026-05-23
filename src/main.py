"""
main.py — FastAPI Application Entry Point
Dynamic Message Mapper untuk Integrasi REST API Multi-Partner
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import models
from database import engine
from api import partners, mappings, transform, logs

# Buat semua tabel
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Dynamic Message Mapper",
    description=(
        "Prototipe penelitian: Message Mapper Dinamis Berbasis Konfigurasi "
        "untuk Integrasi REST API Multi-Partner. "
        "Metode: Design Science Research Methodology (DSRM)."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Daftarkan router
app.include_router(partners.router, prefix="/api/partners", tags=["Partner CRUD"])
app.include_router(mappings.router, prefix="/api/mappings", tags=["Mapping Config"])
app.include_router(transform.router, prefix="/api/transform", tags=["Transform & Preview"])
app.include_router(logs.router, prefix="/api/logs", tags=["Transform Logs"])


@app.get("/", tags=["Health"])
def root():
    return {
        "service": "Dynamic Message Mapper",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}

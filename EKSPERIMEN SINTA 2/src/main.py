"""main.py — FastAPI Application Entry Point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import models
from database import engine
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Dynamic Message Mapper", version="2.0.0", docs_url="/docs", redoc_url="/redoc")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

from api import partners, mappings, transform, logs
app.include_router(partners.router, prefix="/api/partners", tags=["Partner CRUD"])
app.include_router(mappings.router, prefix="/api/mappings", tags=["Mapping Config"])
app.include_router(transform.router, prefix="/api/transform", tags=["Transform & Preview"])
app.include_router(logs.router, prefix="/api/logs", tags=["Transform Logs"])

@app.get("/", tags=["Health"])
def root(): return {"service": "Dynamic Message Mapper", "version": "2.0.0", "status": "running", "docs": "/docs"}

@app.get("/health", tags=["Health"])
def health(): return {"status": "ok"}

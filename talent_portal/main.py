import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ingestion.routes import router

# Cria a aplicação FastAPI.
app = FastAPI(title="Enterprise Vendor Hub — Talent Portal API")

cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS", "http://localhost:5500,http://127.0.0.1:5500"
    ).split(",")
    if origin.strip()
]

# Libera o acesso da landing page (servida em outra porta/origem) durante o desenvolvimento.
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Adiciona à aplicação as rotas definidas em ingestion/routes.py.
app.include_router(router)


# Endpoint simples para verificar se a API está funcionando.
@app.get("/health")
def health():
    return {"status": "ok"}

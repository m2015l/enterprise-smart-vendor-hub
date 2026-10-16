// Endereço da API do talent_portal (talent_portal/main.py, rodada com uvicorn).
// Lê de process.env.API_BASE_URL (injetado em build) ou variável global, com fallback para ambiente local.
window.API_BASE_URL = (typeof process !== "undefined" && process.env && process.env.API_BASE_URL) || window.ENV_API_BASE_URL || "http://localhost:8000";

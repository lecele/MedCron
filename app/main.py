"""
MedCron_Py — Ponto de Entrada da Aplicação FastAPI

Inicializa o app com CORS configurado para segurança,
registra as rotas e configura o ciclo de vida (lifespan).
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import get_settings
from app.core.clients import configure_gemini


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Ciclo de vida do FastAPI:
    - Startup: Configura o Gemini AI
    - Shutdown: Cleanup (se necessário)
    """
    settings = get_settings()
    configure_gemini()
    print(f"MedCron v{settings.app_version} iniciado em modo [{settings.environment}]")
    yield
    print("MedCron finalizado.")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Backend do MedCron — Assistente de Lembretes de Medicamentos. "
            "Powered by LangGraph Multi-Agent Architecture."
        ),
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url="/redoc" if settings.environment != "production" else None,
        lifespan=lifespan,
    )

    # ── CORS ─────────────────────────────────────────────────────────────────
    # Produção: apenas origens configuradas no .env / Vercel
    # Desenvolvimento: inclui localhost
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    # ── Rotas ─────────────────────────────────────────────────────────────────
    app.include_router(router, prefix="/api")

    return app


app = create_app()

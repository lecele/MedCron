"""
MedCron_Py — Clientes de Serviços Externos (Singleton)
Inicializa Supabase, OpenAI e Google Gemini uma única vez.
"""
from functools import lru_cache

from openai import AsyncOpenAI
import google.generativeai as genai
from supabase import AsyncClient, acreate_client

from app.core.config import get_settings


# ── Supabase ──────────────────────────────────────────────────────────────────
@lru_cache()
def _get_settings_cached():
    return get_settings()


async def get_supabase() -> AsyncClient:
    """
    Retorna um cliente Supabase assíncrono.
    Usa a anon key por padrão (respeita RLS).
    Injetar via FastAPI Depends para contextos de usuário autenticado.
    """
    settings = _get_settings_cached()
    return await acreate_client(
        settings.supabase_url,
        settings.supabase_anon_key,
    )


# ── OpenAI ────────────────────────────────────────────────────────────────────
@lru_cache()
def get_openai_client() -> AsyncOpenAI:
    """Singleton do cliente OpenAI assíncrono."""
    settings = _get_settings_cached()
    return AsyncOpenAI(api_key=settings.openai_api_key)


# ── Google Gemini ─────────────────────────────────────────────────────────────
def configure_gemini() -> None:
    """
    Configura a SDK do Gemini com a API Key.
    Deve ser chamado UMA VEZ na inicialização do app (lifespan do FastAPI).
    """
    settings = _get_settings_cached()
    genai.configure(api_key=settings.google_api_key)


def get_gemini_model(model_name: str = "gemini-3-pro-preview") -> genai.GenerativeModel:
    """Retorna uma instância do modelo Gemini especificado."""
    return genai.GenerativeModel(model_name)

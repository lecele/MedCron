"""
MedCron_Py — Configurações Centralizadas da Aplicação
Lê as variáveis do .env de forma segura via pydantic-settings.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Todas as variáveis de ambiente ficam aqui com validação automática.
    Se uma variável obrigatória estiver ausente, a aplicação NÃO sobe.
    """

    # --- Supabase ---
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str | None = None

    # --- OpenAI ---
    openai_api_key: str

    # --- Google AI (Gemini) ---
    google_api_key: str

    # --- Telegram ---
    telegram_bot_token: str | None = None
    telegram_bot_username: str | None = None

    # --- MemPalace (Memória de Longo Prazo na VPS) ---
    mempalace_api_url: str | None = None
    mempalace_path: str | None = None   # Caminho local do ChromaDB na VPS (ex: /root/.mempalace/palace)


    # --- App ---
    environment: str = "development"
    app_name: str = "MedCron"
    app_version: str = "2.0.0"
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def origins_list(self) -> list[str]:
        """Converte a string de origens CORS em lista."""
        return [o.strip() for o in self.allowed_origins.split(",")]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",   # Ignora variáveis extras sem quebrar
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Singleton das configurações — lido uma única vez e cacheado.
    Use: settings = get_settings()
    """
    return Settings()

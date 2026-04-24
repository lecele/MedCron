"""
MedCron_Py — Schemas Pydantic das Rotas FastAPI

Define os modelos de Request e Response para validação automática
e geração da documentação OpenAPI (Swagger UI).
"""
from pydantic import BaseModel, Field


# ── Chat ──────────────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str = Field(..., description="Mensagem do paciente", min_length=1, max_length=4000)
    usuario_id: str = Field(..., description="UUID do paciente no Supabase")
    sessao_id: str | None = Field(None, description="ID da thread para manter contexto de conversa")
    image_base64: str | None = Field(None, description="Foto da receita codificada em base64 (JPEG/PNG)")
    history: list[dict] = Field(default_factory=list, description="Histórico de mensagens para ambientes stateless")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Aqui está minha receita médica",
                "usuario_id": "550e8400-e29b-41d4-a716-446655440000",
                "sessao_id": "sess_abc123",
                "image_base64": None,
            }
        }


class ChatResponse(BaseModel):
    resposta: str = Field(..., description="Resposta do assistente MedCron")
    sessao_id: str = Field(..., description="ID da sessão para continuação da conversa")
    alertas_clinicos: list[str] = Field(default_factory=list, description="Alertas de segurança farmacológica")
    medicamentos_salvos: int = Field(0, description="Número de medicamentos persistidos nesta iteração")


# ── Calendário ────────────────────────────────────────────────────────────────
class CalendarRequest(BaseModel):
    usuario_id: str = Field(..., description="UUID do paciente")


# ── Health Check ─────────────────────────────────────────────────────────────
class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str

# ── TTS ──────────────────────────────────────────────────────────────────────
class TTSRequest(BaseModel):
    text: str = Field(..., description="Texto para ser convertido em áudio")


# ── LGPD ─────────────────────────────────────────────────────────────────────
class ConsentRequest(BaseModel):
    usuario_id: str = Field(..., description="UUID do paciente")
    consentiu: bool = Field(..., description="True se o paciente aceitou os termos")
    versao_politica: str = Field("1.0", description="Versão da política aceita")


class ConsentResponse(BaseModel):
    registrado: bool = Field(..., description="True se o consentimento foi persistido")
    mensagem: str = Field(..., description="Mensagem de confirmação")

"""
MedCron_Py — Estados do Grafo LangGraph

Define os Pydantic Models que transitam entre os Nós dos Agentes.
Toda a informação que os agentes precisam compartilhar vive aqui.
"""
from typing import Annotated, Any
from pydantic import BaseModel, Field
import operator


# ── Mensagem Base ─────────────────────────────────────────────────────────────
class MedCronMessage(BaseModel):
    role: str              # "user" | "assistant" | "system"
    content: str
    image_base64: str | None = None   # Payload da foto da receita (se houver)


# ── Estado Principal do Grafo ─────────────────────────────────────────────────
class AgentState(BaseModel):
    """
    O estado que flui pelo LangGraph. Cada Nó lê e/ou modifica este objeto.
    Campos com Annotated[list, operator.add] são ACUMULADOS (append-only).
    """

    # Identificação do paciente
    usuario_id: str | None = None
    patient_name: str | None = None

    # Histórico de mensagens (acumulado)
    messages: Annotated[list[MedCronMessage], operator.add] = Field(default_factory=list)

    # Dados extraídos pelo Agente de Visão (OCR)
    receita_texto_bruto: str | None = None

    # Medicamentos validados pelo Validador Farmacêutico
    medicamentos_validados: list[dict[str, Any]] = Field(default_factory=list)

    # Alertas clínicos gerados pelo Validador
    alertas_clinicos: list[str] = Field(default_factory=list)

    # Dados extras da Receita (Médico)
    medico_nome: str | None = None
    medico_crm: str | None = None

    # Contexto de memória do paciente (vindo do MemPalace / Supabase)
    perfil_paciente: dict[str, Any] = Field(default_factory=dict)

    # Próximo nó a executar (controlado pelo Supervisor)
    next_node: str = "supervisor"

    # Resposta final a ser enviada ao usuário
    resposta_final: str | None = None

    # Metadados de execução
    tem_imagem: bool = False
    onboarding_completo: bool = False
    sessao_id: str | None = None

    # Dados progressivos coletados pelo agente de onboarding
    dados_onboarding: dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True

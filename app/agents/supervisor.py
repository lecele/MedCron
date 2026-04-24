"""
MedCron_Py — Agente Supervisor (Orquestrador LangGraph)

O "Gerente" da clínica. Analisa o input do paciente e decide
qual agente especialista deve agir: Visão, Triagem ou Chat.
"""
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.agents.state import AgentState, MedCronMessage
from app.core.config import get_settings

SUPERVISOR_SYSTEM_PROMPT = """
Você é o Supervisor Orquestrador do MedCron, um assistente que ajuda pessoas a tomar medicamentos na hora certa.
Analise cuidadosamente a mensagem do paciente e responda em JSON com a seguinte estrutura:

{{
  "next_node": "<agente>",
  "reasoning": "<sua razão breve>"
}}

Regras de roteamento (escolha UM):
- "vision_agent"    → Se a mensagem contém uma foto/imagem de receita médica
- "escrivao_agent"  → Se há medicamentos pendentes de confirmação (`medicamentos_pendentes=true`) e o paciente confirmou que os dados estão corretos
- "onboarding_agent" → Se o cadastro do paciente ainda não está completo (`onboarding_completo=false`) E a mensagem é claramente uma resposta ao cadastro (nome, idade, peso, telefone)
- "chat_agent"      → Para QUALQUER outra situação, incluindo: perguntas gerais, dúvidas, cadastro incompleto + pergunta lateral, tirar dúvidas durante onboarding. O chat_agent saberá retomar o cadastro após responder.
- "calendar_agent"  → Se o paciente pede explicitamente o calendário de medicamentos ou arquivo .ics

REGRA CRÍTICA: Quando `onboarding_completo=false` e o paciente faz uma PERGUNTA (ex: "o que é isso?", "para que serve?", "não entendi"), encaminhe ao "chat_agent" — NÃO ao onboarding_agent. O chat_agent responderá e retomará o cadastro.

Informações do contexto:
- onboarding_completo: {onboarding_completo}
- tem_imagem: {tem_imagem}
- medicamentos_pendentes: {medicamentos_pendentes}
- paciente: {patient_name}
"""


async def supervisor_node(state: AgentState) -> dict:
    """
    Nó Supervisor: decide qual agente deve agir a seguir.
    Também recupera o contexto do MemPalace para enriquecer o routing.
    """
    from app.services.memory_service import get_patient_context

    settings = get_settings()
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=settings.openai_api_key,
        temperature=0,
        response_format={"type": "json_object"},
    )

    ultima_mensagem = ""
    if state.messages:
        ultima_mensagem = state.messages[-1].content

    # Recupera contexto do MemPalace (se disponível) para roteamento mais informado
    contexto_memoria = ""
    if state.usuario_id:
        contexto_memoria = await get_patient_context(
            usuario_id=state.usuario_id,
            pergunta=ultima_mensagem,
        )

    system_content = SUPERVISOR_SYSTEM_PROMPT.format(
        onboarding_completo=state.onboarding_completo,
        tem_imagem=state.tem_imagem,
        medicamentos_pendentes="true" if state.medicamentos_validados else "false",
        patient_name=state.patient_name or "Desconhecido",
    )

    # Injeta contexto de memória se disponível
    if contexto_memoria:
        system_content += f"\n\n## Contexto de Memoria do Paciente (MemPalace)\n{contexto_memoria}"

    response = await llm.ainvoke([
        SystemMessage(content=system_content),
        HumanMessage(content=ultima_mensagem),
    ])

    try:
        decision = json.loads(response.content)
        next_node = decision.get("next_node", "chat_agent")
    except (json.JSONDecodeError, AttributeError):
        next_node = "chat_agent"

    return {"next_node": next_node}

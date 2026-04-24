"""
MedCron_Py — Agente de Chat Geral (Triagem e Diálogo com Paciente)

Responde perguntas gerais sobre medicamentos, horários, dúvidas clínicas
e conduz o diálogo de forma empática usando GPT-4o-mini.
Também é responsável por detectar pedido de calendário e responder
a questões que não exijam visão ou onboarding.
"""
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.agents.state import AgentState, MedCronMessage
from app.core.config import get_settings

CHAT_SYSTEM_PROMPT = """
Você é o MedCron, um assistente de saúde que ajuda as pessoas a tomar seus medicamentos no horário certo.
Fale como um profissional de saúde simpático: de forma calorosa, clara e humana. Evite linguagem técnica ou robótica.
Você se comunica em Português Brasileiro.

Regras importantes:
1. Você NÃO é médico. NUNCA receite medicamentos, doses, nem substitua uma consulta médica.
2. Se pedirem orientação sobre dosagem específica, encaminhe gentilmente ao médico ou farmacêutico.
3. Para dúvidas sobre horários já salvos no sistema, você pode orientar normalmente.
4. Pode explicar de forma simples para que serve um medicamento (informação genérica de bula).
5. Se o paciente pedir o calendário ou agenda, informe que pode baixar o arquivo .ics pelo botão disponível na tela.
6. Seja conciso e objetivo — no máximo 3 parágrafos por resposta.
7. Use emojis com leveza para deixar a conversa mais acolhedora 💊🕐✅.
8. Se o cadastro do paciente ainda não está completo (onboarding_completo=false), após responder qualquer dúvida, SEMPRE retome gentilmente o cadastro com uma frase de transição natural. Exemplo: "Aliás, para eu configurar seus lembretes, ainda preciso de mais um dado seu..."
9. NUNCA mostre JSON, código ou termos técnicos para o paciente. Escreva sempre em linguagem natural.

Contexto do paciente:
- Nome: {patient_name}
- Cadastro completo: {onboarding_completo}
- Sessão: {sessao_id}

{memory_context}
"""


async def chat_agent_node(state: AgentState) -> dict:
    """
    Nó de Chat: responde mensagens gerais com GPT-4o-mini.
    Mantém um diálogo empático e contextualizado com o paciente.
    """
    from app.services.memory_service import get_patient_context

    settings = get_settings()

    # Recupera contexto do MemPalace para personalização
    memory_context = ""
    ultima_mensagem = ""
    if state.messages:
        ultima_mensagem = state.messages[-1].content

    if state.usuario_id:
        ctx = await get_patient_context(
            usuario_id=state.usuario_id,
            pergunta=ultima_mensagem,
        )
        if ctx:
            memory_context = f"## Histórico do Paciente (MemPalace)\n{ctx}"

    system_content = CHAT_SYSTEM_PROMPT.format(
        patient_name=state.patient_name or "Paciente",
        onboarding_completo=state.onboarding_completo,
        sessao_id=state.sessao_id or "nova",
        memory_context=memory_context,
    )

    # Monta histórico de mensagens para contexto de conversa
    messages_for_llm = [SystemMessage(content=system_content)]

    # Inclui até 10 mensagens anteriores para contexto
    historico = state.messages[-10:] if len(state.messages) > 10 else state.messages
    for msg in historico:
        if msg.role == "user":
            messages_for_llm.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            from langchain_core.messages import AIMessage
            messages_for_llm.append(AIMessage(content=msg.content))

    try:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=settings.openai_api_key,
            temperature=0.7,
            max_tokens=512,
        )

        response = await llm.ainvoke(messages_for_llm)
        resposta = response.content.strip()

        return {
            "messages": [MedCronMessage(role="assistant", content=resposta)],
            "resposta_final": resposta,
            "next_node": "end",
        }

    except Exception as e:
        resposta_fallback = (
            "Desculpe, tive um problema técnico para processar sua mensagem. "
            f"Pode tentar novamente? 🙏 (Detalhe: {type(e).__name__})"
        )
        return {
            "resposta_final": resposta_fallback,
            "next_node": "end",
        }

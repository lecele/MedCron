"""
MedCron_Py — Grafo LangGraph (Arquitetura Simplificada)

Fluxo:
  START → medcron_agent → END

O medcron_agent é o agente unificado que controla todo o fluxo conversacional.
O escrivao_agent é chamado programaticamente pelo routes.py quando o frontend
detecta o JSON de agendamento e confirma o salvamento.
"""
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.agents.state import AgentState
from app.agents.medcron_agent import medcron_agent_node
from app.agents.escrivao_agent import escrivao_agent_node


def build_graph() -> StateGraph:
    """
    Constrói e compila o grafo de agentes do MedCron.

    Arquitetura simplificada: um único agente conversacional
    que segue o fluxo do OpenClaw (extração, entrevista, agendamento).
    """
    builder = StateGraph(AgentState)

    # ── Registra os Nós ───────────────────────────────────────────────────────
    builder.add_node("medcron_agent", medcron_agent_node)
    builder.add_node("escrivao_agent", escrivao_agent_node)

    # ── Ponto de Entrada ──────────────────────────────────────────────────────
    builder.set_entry_point("medcron_agent")

    # ── Roteamento do Agente Principal ────────────────────────────────────────
    def _router(state: AgentState) -> str:
        return state.next_node

    builder.add_conditional_edges(
        "medcron_agent",
        _router,
        {
            "escrivao_agent": "escrivao_agent",
            "end": END,
        },
    )

    builder.add_edge("escrivao_agent", END)

    # ── Checkpointer em memória ───────────────────────────────────────────────
    memory = MemorySaver()
    return builder.compile(checkpointer=memory)


# Instância singleton do grafo compilado
medcron_graph = build_graph()

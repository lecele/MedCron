"""
MedCron_Py — Agente Escrivão (Persistência no Supabase)

Responsável por salvar os medicamentos validados nas tabelas
`receitas`, `medicamentos` e `lembretes` do Supabase.
SEM IA — lógica puramente determinística de banco de dados.
"""
from datetime import datetime, timedelta
import uuid

from app.agents.state import AgentState, MedCronMessage
from app.core.clients import get_supabase


def _calcular_horarios(frequencia_por_dia: int, hora_inicio: str = "08:00") -> list[str]:
    """
    Calcula os horários de tomada com base na frequência diária.
    Ex: frequencia_por_dia=3, hora_inicio="08:00" → ["08:00", "16:00", "00:00"]
    """
    hora, minuto = map(int, hora_inicio.split(":"))
    inicio = datetime.today().replace(hour=hora, minute=minuto, second=0)
    intervalo_horas = 24 // frequencia_por_dia
    horarios = []
    for i in range(frequencia_por_dia):
        t = inicio + timedelta(hours=i * intervalo_horas)
        horarios.append(t.strftime("%H:%M"))
    return horarios


async def escrivao_agent_node(state: AgentState) -> dict:
    """
    Nó Escrivão: persiste receita + medicamentos + lembretes no Supabase.
    Executa somente se houver medicamentos validados e usuario_id definido.
    """
    if not state.medicamentos_validados or not state.usuario_id:
        return {
            "resposta_final": "Aguardo a confirmação para salvar seus medicamentos.",
            "next_node": "end",
        }

    supabase = await get_supabase()
    receita_id = str(uuid.uuid4())

    try:
        try:
            update_data = {"id": state.usuario_id}
            if state.medico_nome:
                update_data["medico_nome"] = state.medico_nome
            if state.medico_crm:
                update_data["medico_crm"] = state.medico_crm
            await supabase.table("profiles").upsert(update_data).execute()
        except Exception as e:
            print(f"[Escrivão] Erro no perfil: {e}")
            pass
            
        # 1. Salva a receita
        await supabase.table("receitas").insert({
            "id": receita_id,
            "usuario_id": state.usuario_id,
            "texto_extraido": state.receita_texto_bruto or "Receita processada pelo MedCron",
        }).execute()

        # 2. Salva cada medicamento e seus lembretes
        medicamentos_salvos = []
        lembretes_salvos = []

        for med in state.medicamentos_validados:
            med_id = str(uuid.uuid4())
            freq = med.get("frequencia_por_dia", 1)
            horarios = _calcular_horarios(freq)
            duracao = med.get("duracao_dias", 7)

            # Salva medicamento
            await supabase.table("medicamentos").insert({
                "id": med_id,
                "receita_id": receita_id,
                "usuario_id": state.usuario_id,
                "nome": med["nome"],
                "dosagem": med.get("dosagem", ""),
                "frequencia": med.get("frequencia", ""),
                "duracao_dias": duracao,
            }).execute()
            medicamentos_salvos.append(med["nome"])

            # Salva lembrete para cada horário
            for horario in horarios:
                await supabase.table("lembretes").insert({
                    "usuario_id": state.usuario_id,
                    "nome": med["nome"],
                    "dosagem": med.get("dosagem", ""),
                    "horario": horario,
                    "status": "pendente",
                    "enviado_telegram": False,
                    "data_inicio": datetime.today().strftime("%Y-%m-%d"),
                    "duracao_dias": duracao,
                }).execute()
                lembretes_salvos.append(f"{med['nome']} às {horario}")

        # 3. Limpa o cache de medicamentos esperando salvamento para não re-salvá-los no futuro
        state.medicamentos_validados = []

        # 4. Monta resposta de confirmação
        resumo = "\n".join([f"• {l}" for l in lembretes_salvos])
        resposta = (
            f"✅ Tudo salvo e validado! Configurei {len(lembretes_salvos)} lembrete(s) para você:\n\n"
            f"{resumo}\n\n"
            f"💊 Você receberá notificações nos horários acima. Você pode baixar seu calendário para adicionar ao celular usando os botões na tela!"
        )

        return {
            "medicamentos_validados": [],
            "messages": [MedCronMessage(role="assistant", content=resposta)],
            "resposta_final": resposta,
            "next_node": "end",
        }

    except Exception as e:
        return {
            "resposta_final": (
                f"Ocorreu um erro ao salvar seus medicamentos. "
                f"Tente novamente em instantes. (Erro: {type(e).__name__})"
            ),
            "next_node": "end",
        }

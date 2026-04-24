"""
MedCron_Py — Serviço de Geração de Calendário (.ics)

Migração do bug do Apple Calendar para uma solução robusta:
O servidor Python gera o .ics perfeito — o celular importa nativamente.
"""
from datetime import datetime, timedelta
import uuid

from app.core.clients import get_supabase


def _escape_ics(text: str) -> str:
    """Escapa caracteres especiais para o formato iCalendar."""
    return text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


async def gerar_ics(usuario_id: str) -> str:
    """
    Busca todos os lembretes ativos do paciente no Supabase
    e gera um arquivo .ics com um VEVENT para cada tomada.
    """
    supabase = await get_supabase()

    # Busca lembretes ativos
    result = await supabase.table("lembretes").select("*").eq(
        "usuario_id", usuario_id
    ).eq("status", "pendente").execute()

    lembretes = result.data or []

    linhas = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//MedCron//MedCron Lembretes//PT",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:\U0001f48a MedCron",
        "X-WR-TIMEZONE:America/Sao_Paulo",
        # VTIMEZONE: necessário para Apple Calendar / iOS aceitar eventos com TZID
        "BEGIN:VTIMEZONE",
        "TZID:America/Sao_Paulo",
        "BEGIN:STANDARD",
        "DTSTART:19700101T000000",
        "TZOFFSETFROM:-0300",
        "TZOFFSETTO:-0300",
        "TZNAME:BRT",
        "END:STANDARD",
        "END:VTIMEZONE",
    ]

    hoje = datetime.today()
    # Deduplicar: evita eventos duplicados se o banco tiver entradas repetidas
    vistos: set[tuple] = set()

    for lembrete in lembretes:
        nome = _escape_ics(lembrete.get("nome", "Medicamento"))
        dosagem = _escape_ics(lembrete.get("dosagem", ""))
        horario_str = lembrete.get("horario", "08:00")
        duracao = int(lembrete.get("duracao_dias", 7))
        data_inicio_str = lembrete.get("data_inicio") or hoje.strftime("%Y-%m-%d")

        # Deduplicar: pula se já adicionamos este mesmo medicamento/horário/data
        chave = (nome.lower(), horario_str, data_inicio_str)
        if chave in vistos:
            continue
        vistos.add(chave)

        try:
            hora, minuto = map(int, horario_str.split(":"))
            data_inicio = datetime.strptime(data_inicio_str, "%Y-%m-%d").replace(
                hour=hora, minute=minuto, second=0
            )
        except (ValueError, AttributeError):
            data_inicio = hoje.replace(hour=8, minute=0, second=0)

        data_fim = data_inicio + timedelta(minutes=30)
        data_recorrencia_fim = data_inicio + timedelta(days=duracao)

        dtstart = data_inicio.strftime("%Y%m%dT%H%M%S")
        dtend = data_fim.strftime("%Y%m%dT%H%M%S")
        until = data_recorrencia_fim.strftime("%Y%m%dT%H%M%S") + "Z"
        uid = str(uuid.uuid4())

        linhas += [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTART;TZID=America/Sao_Paulo:{dtstart}",
            f"DTEND;TZID=America/Sao_Paulo:{dtend}",
            f"RRULE:FREQ=DAILY;UNTIL={until}",
            f"SUMMARY:\U0001f48a {nome} {dosagem}",
            f"DESCRIPTION:MedCron \u2014 Hora de tomar {nome}\\n{dosagem}",
            "CATEGORIES:HEALTH",
            # Alerta exatamente no horário da dose (sem avanço)
            "BEGIN:VALARM",
            "TRIGGER:PT0M",
            "ACTION:DISPLAY",
            f"DESCRIPTION:\u23f0 {nome} {dosagem}",
            "END:VALARM",
            "END:VEVENT",
        ]

    linhas.append("END:VCALENDAR")
    return "\r\n".join(linhas)

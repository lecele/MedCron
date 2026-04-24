"""
MedCron_Py — Rotas da API FastAPI

Define todos os endpoints HTTP do backend MedCron.
"""
import uuid
import json
import re
import traceback
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response, StreamingResponse

from app.api.schemas import ChatRequest, ChatResponse, CalendarRequest, HealthResponse, TTSRequest, ConsentRequest, ConsentResponse
from app.agents.graph import medcron_graph
from app.agents.state import AgentState, MedCronMessage
from app.core.config import get_settings
from app.services.calendar_service import gerar_ics
router = APIRouter()


# ── Health Check ──────────────────────────────────────────────────────────────
@router.get("/health", response_model=HealthResponse, tags=["Sistema"])
async def health_check():
    """Verifica se o backend está operacional."""
    settings = get_settings()
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        environment=settings.environment,
    )


# ── Consentimento LGPD ──────────────────────────────────────────────────────────────────────────
@router.post("/consent", response_model=ConsentResponse, tags=["LGPD"])
async def registrar_consentimento(request: ConsentRequest):
    """
    Registra o consentimento LGPD do paciente.

    Chamado pelo frontend quando o usuário aceita os termos de uso de dados
    sensíveis de saúde (Art. 11, Lei 13.709/2018).

    O registro inclui:
    - ID do paciente
    - Se consentiu ou não
    - Versão da política
    - Timestamp automático pelo Supabase
    """
    from datetime import datetime
    from app.core.clients import get_supabase

    try:
        supabase = await get_supabase()
        await supabase.table("consents").upsert({
            "usuario_id": request.usuario_id,
            "consentiu": request.consentiu,
            "versao_politica": request.versao_politica,
        }).execute()

        msg = (
            "Consentimento registrado com sucesso."
            if request.consentiu
            else "Recusa de consentimento registrada."
        )
        return ConsentResponse(registrado=True, mensagem=msg)

    except Exception as e:
        print(f"[Consent] Erro ao registrar consentimento: {e}")
        # Retorna sucesso mesmo em caso de erro no Supabase para não bloquear o usuário
        # O localStorage já garante a persistência local
        return ConsentResponse(
            registrado=False,
            mensagem="Consentimento salvo localmente. Sincronização com servidor falhou.",
        )


# ── Chat Principal ────────────────────────────────────────────────────────────
@router.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat_endpoint(request: ChatRequest):
    """
    Endpoint principal do MedCron.
    Recebe a mensagem do paciente (com ou sem imagem), roda o grafo LangGraph
    e retorna a resposta do agente.

    O thread_id (sessao_id) garante que o LangGraph recupera o estado
    completo da conversa anterior — incluindo histórico de mensagens.
    """
    sessao_id = request.sessao_id or str(uuid.uuid4())

    # Monta histórico vindo do frontend
    historico_mensagens = []
    for msg in request.history:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if content.strip():
            historico_mensagens.append(MedCronMessage(role=role, content=content))

    # Monta mensagem de entrada para o grafo
    mensagem_entrada = MedCronMessage(
        role="user",
        content=request.message,
        image_base64=request.image_base64,
    )
    historico_mensagens.append(mensagem_entrada)

    # Estado inicial — o LangGraph vai fundir com o estado salvo do thread
    # via MemorySaver. Em ambiente serverless (Vercel), o MemorySaver é volátil,
    # por isso dependemos do histórico enviado via request.history.
    estado_inicial = AgentState(
        usuario_id=request.usuario_id,
        messages=historico_mensagens,
        tem_imagem=bool(request.image_base64),
        sessao_id=sessao_id,
    )

    try:
        # O thread_id é a chave que o MemorySaver usa para recuperar histório
        config = {"configurable": {"thread_id": sessao_id}}
        estado_final = await medcron_graph.ainvoke(
            estado_inicial.model_dump(),
            config=config,
        )

        resposta_bruta = estado_final.get("resposta_final") or "Como posso ajudar?"
        alertas = estado_final.get("alertas_clinicos", [])

        # ── Detecta JSON de agendamento na resposta ───────────────────────────
        # Se o agente retornou JSON, significa que o usuário confirmou o agendamento.
        # O backend salva no Supabase e retorna uma resposta limpa ao frontend.
        json_agendamento = _extrair_json_agendamento(resposta_bruta)
        meds_salvos = 0

        if json_agendamento and json_agendamento.get("action") == "schedule_reminders":
            # Salva os dados no Supabase via Escrivão
            resposta_confirmacao, meds_salvos = await _salvar_agendamento(
                json_agendamento, request.usuario_id
            )
            resposta_final = resposta_confirmacao
        else:
            # Resposta conversacional normal
            resposta_final = _limpar_resposta(resposta_bruta)

        return ChatResponse(
            resposta=resposta_final,
            sessao_id=sessao_id,
            alertas_clinicos=alertas,
            medicamentos_salvos=meds_salvos,
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno no processamento. Tente novamente. ({type(e).__name__})",
        )


async def _salvar_agendamento(dados: dict, usuario_id: str | None) -> tuple[str, int]:
    """
    Persiste o agendamento recebido do LLM no Supabase.
    Retorna (mensagem_confirmacao, quantidade_medicamentos_salvos).
    """
    from datetime import datetime, timedelta
    import uuid as uuid_lib
    from app.core.clients import get_supabase

    if not usuario_id:
        return "Agendamento processado, mas sem ID de usuário para salvar.", 0

    reminders = dados.get("reminders", [])
    if not reminders:
        return "Não encontrei medicamentos para agendar na receita.", 0

    try:
        supabase = await get_supabase()
        receita_id = str(uuid_lib.uuid4())
        data_inicio_str = dados.get("data_inicio") or datetime.today().strftime("%Y-%m-%d")
        duracao_dias = int(dados.get("duracao_dias") or 7)

        # Atualiza perfil do paciente com as colunas corretas do schema
        perfil = {
            "id": usuario_id,
            "onboarding_completo": True,
        }
        if dados.get("patient_name"):
            perfil["nome"] = dados["patient_name"]
        if dados.get("patient_age"):
            perfil["idade"] = dados["patient_age"]
        if dados.get("patient_sex"):
            perfil["sexo"] = dados["patient_sex"]
        if dados.get("telefone"):
            perfil["telefone"] = dados["telefone"]
        if dados.get("doctor_name"):
            perfil["medico_nome"] = dados["doctor_name"]
        if dados.get("doctor_crm"):
            perfil["medico_crm"] = dados["doctor_crm"]

        try:
            await supabase.table("profiles").upsert(perfil).execute()
        except Exception as e:
            print(f"[Routes] Erro fatal ao salvar perfil: {e}")
            return "Erro ao sincronizar seu cadastro. Por favor, tente novamente.", 0

        # Salva a receita
        try:
            await supabase.table("receitas").insert({
                "id": receita_id,
                "usuario_id": usuario_id,
                "texto_extraido": f"Receita de {dados.get('patient_name', 'Paciente')} — Dr. {dados.get('doctor_name', 'N/A')}",
            }).execute()
        except Exception as e:
            print(f"[Routes] Erro ao salvar receita: {e}")

        # Salva medicamentos e lembretes
        lembretes_confirmados = []
        for rem in reminders:
            med_id = str(uuid_lib.uuid4())
            nome = rem.get("name", "")
            dosagem = rem.get("dosage", "")
            horario = rem.get("time", "")

            try:
                await supabase.table("medicamentos").insert({
                    "id": med_id,
                    "receita_id": receita_id,
                    "usuario_id": usuario_id,
                    "nome": nome,
                    "dosagem": dosagem,
                    "frequencia": horario,
                    "duracao_dias": duracao_dias,
                }).execute()
            except Exception as e:
                print(f"[Routes] Erro ao salvar medicamento {nome}: {e}")

            if horario:
                try:
                    await supabase.table("lembretes").insert({
                        "usuario_id": usuario_id,
                        "nome": nome,
                        "dosagem": dosagem,
                        "horario": horario,
                        "status": "pendente",
                        "data_inicio": data_inicio_str,
                        "duracao_dias": duracao_dias,
                    }).execute()
                    lembretes_confirmados.append(f"{nome} — {horario}")
                except Exception as e:
                    print(f"[Routes] Erro ao salvar lembrete {nome}: {e}")

        patient = dados.get("patient_name", "")
        resumo = "\n".join(lembretes_confirmados) if lembretes_confirmados else "(sem horário fixo)"
        msg = (
            f"Tudo certo{', ' + patient if patient else ''}. "
            f"Configurei {len(lembretes_confirmados)} lembrete(s) para você:\n\n{resumo}\n\n"
            "Você pode baixar o calendário pelo botão na tela para adicionar ao seu celular."
        )
        return msg, len(reminders)

    except Exception as e:
        print(f"[Routes] Erro crítico ao salvar agendamento: {e}")
        traceback.print_exc()
        return "Ocorreu um problema ao salvar. Tente novamente.", 0


def _extrair_json_agendamento(texto: str) -> dict | None:
    """Extrai JSON de agendamento do texto, se existir."""
    # Bloco markdown ```json ... ```
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", texto)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # JSON solto no texto
    first = texto.find("{")
    last = texto.rfind("}")
    if first != -1 and last > first:
        try:
            return json.loads(texto[first:last + 1])
        except json.JSONDecodeError:
            pass

    return None


def _limpar_resposta(texto: str) -> str:
    """Remove artefatos técnicos da resposta antes de exibir ao usuário."""
    texto = re.sub(r"```[\w]*[\s\S]*?```", "", texto)
    texto = re.sub(r"\{[\s\S]*?\}", "", texto)
    texto = re.sub(r"\*+", "", texto)
    texto = re.sub(r"\n{3,}", "\n", texto)
    return texto.strip()


# ── Geração de Calendário .ics ────────────────────────────────────────────────
@router.get("/calendar/generate", tags=["Calendário"])
async def generate_calendar(usuario_id: str):
    """
    Gera um arquivo .ics com todos os lembretes de medicamentos do paciente.
    iOS Safari abre automaticamente o app Calendário ao receber text/calendar.
    """
    try:
        ics_content = await gerar_ics(usuario_id)
        return Response(
            content=ics_content,
            media_type="text/calendar; charset=utf-8",
            headers={
                # inline = iOS Safari abre direto no app Calendário
                # attachment = Android faz download
                # Usamos inline para forçar abertura nativa no iOS
                "Content-Disposition": "inline; filename=medcron_lembretes.ics",
                "Cache-Control": "no-cache",
                "Access-Control-Allow-Origin": "*",
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao gerar calendário: {type(e).__name__}",
        )





# ── Text-to-Speech (OpenAI) ───────────────────────────────────────────────────
@router.post("/tts", tags=["Voice"])
async def generate_tts(request: TTSRequest):
    """
    Converte texto em áudio usando a API TTS da OpenAI (modelo tts-1, voz onyx).
    Retorna um stream de áudio MPEG (MP3).
    """
    from app.core.clients import get_openai_client
    
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Texto vazio")
        
    try:
        client = get_openai_client()
        response = await client.audio.speech.create(
            model="tts-1",
            voice="onyx",
            input=request.text.strip(),
            response_format="mp3"
        )
        
        # A OpenAI SDK v1.x suporta leitura em chunks assíncrona
        async def generate():
            async for chunk in response:
                yield chunk
                
        return StreamingResponse(
            generate(),
            media_type="audio/mpeg"
        )
        
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro na geração de áudio: {e}"
        )

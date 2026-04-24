"""
MedCron_Py — Agente Unificado (Porta fiel do OpenClaw)

Agente único que orquestra TODO o fluxo conversacional:
1. OCR da receita (via gpt-4o com visão)
2. Entrevista complementar (nome, idade, peso, sexo, telefone)
3. Auditoria farmacológica via GPT-4o-mini (usa peso e idade do paciente)
4. Resumo e pedido de confirmação
5. Geração do JSON de agendamento (silencioso, processado pelo Escrivão)

Este agente substitui onboarding_agent + chat_agent + supervisor como controlador
principal do fluxo. O supervisor ainda existe para roteamento de casos especiais.
"""
import json
import re
import logging
from datetime import datetime, date
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from app.agents.state import AgentState, MedCronMessage
from app.core.config import get_settings

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Prompt principal — espelho fiel do OpenClaw agents.js, adaptado para Python
# ─────────────────────────────────────────────────────────────────────────────
def _build_system_prompt(today_str: str, iso_date: str, alerta_farmaceutico: str = "") -> str:
    alerta_section = ""
    if alerta_farmaceutico:
        alerta_section = f"""
⚠️ ATENÇÃO — ALERTA DE SEGURANÇA ATIVO ⚠️
{alerta_farmaceutico}

"""

    return f"""Você é o MedCron, um assistente de saúde inteligente, humano e direto.

OBJETIVO: Agendamento preciso de medicamentos com foco no cuidado ao paciente.

PERSONALIDADE:
- Seja HUMANO e CALOROSO, mas sem excessos. NUNCA use "Obrigado", "Perfeito", "Ótimo", "Certo" ou "Por favor" como reação às respostas do usuário.
- Para confirmar que entendeu, use variações curtas e naturais: "Entendi.", "Anotado.", "Ok."
- Seja CONCISO e fluido. Escreva sempre em excelente Português do Brasil, com acentuação correta.
- NUNCA use emojis. NUNCA use markdown, asteriscos, hífens de lista ou qualquer formatação. Apenas texto puro.
- NUNCA mostre JSON, código, chaves ou colchetes para o paciente. O JSON é enviado silenciosamente.
{alerta_section}
VALIDAÇÃO FARMACÊUTICA (regra absoluta):
Se você receber um bloco de ALERTA DE SEGURANÇA acima, INTERROMPA O FLUXO COMPLETAMENTE.
Informe o paciente de forma clara, humana e sem tecnicismos sobre o risco identificado na prescrição.
Oriente a contatar o médico prescritor antes de iniciar o tratamento.
NÃO gere JSON. NÃO agende nada. NÃO continue a entrevista. NÃO peça mais dados.
Esta é uma regra de SEGURANÇA e não pode ser ignorada.

PASSO A PASSO (Siga em ordem, a menos que haja alerta de segurança ativo):

1. EXTRACAO E BOAS-VINDAS: Ao receber a imagem (ou texto), varra a receita procurando pelo NOME DO PACIENTE.
   - Sendo seguro, inicie com "Olá [Nome extraído], prazer em te conhecer!" (ou "Olá! Recebi a sua receita." se sem nome).
   - Liste TODOS os medicamentos e horários calculados.
   - Pergunte SOMENTE: "Essas informações estão corretas?"

2. COMPLEMENTO: Após o paciente confirmar a extração, obtenha as informações que faltam (Idade, Peso, Sexo, Telefone). Peça UMA por vez.
   - NUNCA agrupe perguntas na mesma resposta.

3. INICIO DO TRATAMENTO: Tendo as informações, pergunte: "Quer começar o tratamento hoje?"

5. RESUMO COMPLETO: Mostre TODOS os dados coletados em texto puro:
   - Nome, Idade, Peso, Sexo
   - Médico e CRM
   - Cada medicamento com dosagem e todos os horários
   Termine com a pergunta EXATA: "Posso agendar tudo agora?"

6. AGENDAMENTO: Somente após o usuário dar resposta afirmativa (como "Sim", "Pode agendar", "Ok", "Pode", "Pode sim", "Certo", "Agende", "Beleza"), envie o bloco tecnico abaixo. PROIBIDO enviar antes. NAO escreva NADA alem do JSON.

REGRAS:
- TURNO UNICO: NUNCA faca mais de uma pergunta por mensagem.
- SEM MARKDOWN: Apenas texto puro.
- SEM JARGAO: Jamais escreva "JSON" ou "codigo".
- FARMACOLOGIA: Se receber ALERTA DE SEGURANÇA, BLOQUEIE TUDO E EXPLIQUE AO PACIENTE.

JSON SCHEMA (envie silenciosamente apos confirmacao final):
{{
  "action": "schedule_reminders",
  "patient_name": "NOME",
  "patient_sex": "SEXO",
  "patient_age": 0,
  "patient_weight": 0,
  "doctor_name": "NOME DO MEDICO",
  "doctor_crm": "CRM",
  "telefone": "NUMERO",
  "data_inicio": "{iso_date}",
  "duracao_dias": 7,
  "safety_alerts": [],
  "reminders": [
    {{ "name": "Medicamento", "dosage": "Dose", "time": "HH:MM", "leaflet_url": "" }}
  ]
}}
CALCULE TODOS OS LEMBRETES NO ARRAY. Se o medicamento nao tiver horario fixo, deixe time vazio: "".

DATA ATUAL: {today_str}. No JSON, use "{iso_date}" para hoje.
"""


# ─────────────────────────────────────────────────────────────────────────────
# Parser: extrai peso, idade e medicamentos do histórico da conversa
# ─────────────────────────────────────────────────────────────────────────────
def _extrair_dados_paciente_do_historico(messages: list) -> dict:
    """
    Varre o histórico de mensagens buscando peso, idade e medicamentos
    já confirmados para alimentar o validador IA.

    Retorna dict com chaves: peso_kg, idade, sexo, medicamentos
    """
    texto_completo = " ".join(
        msg.content for msg in messages if msg.role in ("user", "assistant")
    ).lower()

    dados = {"peso_kg": None, "idade": None, "sexo": None, "medicamentos": []}

    # ── Peso ─────────────────────────────────────────────────────────────────
    match_peso = re.search(
        r"(?:peso[:\s]+|peso\s+é\s+|pesando\s+|tenho\s+)(\d+(?:[.,]\d+)?)\s*kg",
        texto_completo
    )
    if not match_peso:
        match_peso = re.search(r"\b(\d{2,3})\s*kg\b", texto_completo)
    if match_peso:
        try:
            dados["peso_kg"] = float(match_peso.group(1).replace(",", "."))
        except ValueError:
            pass

    # ── Idade ────────────────────────────────────────────────────────────────
    match_idade = re.search(
        r"(?:idade[:\s]+|tenho\s+|sou\s+|anos?\s*[:=]\s*)(\d{1,3})\s*anos?",
        texto_completo
    )
    if not match_idade:
        match_idade = re.search(r"\b(\d{1,3})\s*anos?\b", texto_completo)
    if match_idade:
        try:
            idade = int(match_idade.group(1))
            if 0 < idade < 120:
                dados["idade"] = idade
        except ValueError:
            pass

    # ── Sexo ─────────────────────────────────────────────────────────────────
    if any(p in texto_completo for p in ["feminino", "mulher", "feminina", " f "]):
        dados["sexo"] = "feminino"
    elif any(p in texto_completo for p in ["masculino", "homem", "masculina", " m "]):
        dados["sexo"] = "masculino"

    return dados


def _ja_validou_nesta_sessao(messages: list) -> bool:
    """
    Verifica se o validador farmacológico já foi executado nesta sessão
    para evitar chamadas duplicadas a cada turno.
    """
    for msg in messages:
        if msg.role == "system" and "[ALERTA FARMACÊUTICO" in msg.content:
            return True
        if msg.role == "assistant" and "risco" in msg.content.lower() and "médico" in msg.content.lower():
            # Heurística: se o agente já alertou sobre risco, provavelmente a validação já ocorreu
            return True
    return False


def _historico_tem_peso_e_idade(messages: list) -> bool:
    """Verifica se peso e idade já foram coletados no histórico."""
    dados = _extrair_dados_paciente_do_historico(messages)
    return dados["peso_kg"] is not None and dados["idade"] is not None


async def medcron_agent_node(state: AgentState) -> dict:
    """
    Nó principal do MedCron — agente conversacional unificado.
    Controla todo o fluxo: extração de receita, entrevista, validação e agendamento.
    """
    settings = get_settings()

    # Data atual para injetar no prompt
    now = datetime.now()
    today_str = now.strftime("%d/%m/%Y")
    iso_date = now.strftime("%Y-%m-%d")

    # Inclui até 20 mensagens de histórico para manter contexto
    historico = state.messages[-20:] if len(state.messages) > 20 else state.messages

    # ── Validação Farmacológica IA ───────────────────────────────────────────
    # Dispara somente quando:
    # 1. Há pelo menos uma imagem (receita foi enviada) OU há medicamentos no estado
    # 2. Peso e idade foram coletados no histórico
    # 3. Ainda não foi validado nesta sessão
    alerta_farmaceutico = ""
    alertas_informativos_para_json = []

    if (
        _historico_tem_peso_e_idade(historico)
        and not _ja_validou_nesta_sessao(historico)
    ):
        try:
            from app.agents.validador_ia import validar_receita_ia, formatar_alerta_para_paciente

            dados_paciente = _extrair_dados_paciente_do_historico(historico)

            # Tenta extrair medicamentos do estado (se OCR já rodou)
            medicamentos_para_validar = state.medicamentos_validados or []

            # Se não há medicamentos estruturados no estado, monta lista mínima
            # a partir das mensagens do agente (heurística de fallback)
            if not medicamentos_para_validar:
                logger.info("[MedCronAgent] Nenhum medicamento estruturado no estado. Validador IA receberá lista vazia.")

            if medicamentos_para_validar:
                resultado = await validar_receita_ia(
                    medicamentos=medicamentos_para_validar,
                    peso_kg=dados_paciente.get("peso_kg"),
                    idade=dados_paciente.get("idade"),
                    sexo=dados_paciente.get("sexo"),
                )

                if not resultado.aprovado and resultado.alertas_criticos:
                    alerta_farmaceutico = formatar_alerta_para_paciente(resultado)
                    logger.warning(
                        f"[MedCronAgent] Validação IA bloqueou o agendamento. "
                        f"Alertas: {resultado.alertas_criticos}"
                    )
                else:
                    alertas_informativos_para_json = resultado.alertas_informativos
                    logger.info("[MedCronAgent] Validação IA aprovada.")

        except Exception as e:
            logger.error(f"[MedCronAgent] Erro na validação IA: {e}")
            # Não bloqueia o fluxo em caso de erro na validação

    # ── Monta o prompt do sistema (com alerta se houver) ─────────────────────
    system_content = _build_system_prompt(today_str, iso_date, alerta_farmaceutico)

    # ── Monta o histórico de mensagens para o LLM ────────────────────────────
    messages_for_llm: list = [SystemMessage(content=system_content)]

    ultima_msg = historico[-1] if historico else None
    tem_imagem = ultima_msg and ultima_msg.image_base64

    for msg in historico:
        if msg.role == "user":
            if msg.image_base64:
                # Mensagem com imagem — usa multimodal
                raw_b64 = msg.image_base64
                mime_type = "image/jpeg"
                if raw_b64.startswith("data:"):
                    header, raw_b64 = raw_b64.split(",", 1)
                    if ":" in header and ";" in header:
                        mime_type = header.split(":")[1].split(";")[0]
                messages_for_llm.append(HumanMessage(content=[
                    {"type": "text", "text": msg.content or "Extraia os dados desta receita."},
                    {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{raw_b64}"}},
                ]))
            else:
                messages_for_llm.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            messages_for_llm.append(AIMessage(content=msg.content))

    try:
        # Usa gpt-4o-mini sempre (suporta visão e é extremamente rápido, evitando Timeout da Vercel Hobby)
        model = "gpt-4o-mini"

        llm = ChatOpenAI(
            model=model,
            api_key=settings.openai_api_key,
            temperature=0.1,
            max_tokens=1024,
        )

        response = await llm.ainvoke(messages_for_llm)
        resposta_bruta = response.content.strip()

        # ── Detecta se a resposta contém JSON de agendamento ─────────────────
        json_data = _extrair_json_agendamento(resposta_bruta)

        if json_data and json_data.get("action") == "schedule_reminders":
            # Injeta alertas informativos no campo safety_alerts do JSON
            if alertas_informativos_para_json:
                json_data["safety_alerts"] = alertas_informativos_para_json
                resposta_bruta = json.dumps(json_data, ensure_ascii=False)

            # Resposta é o JSON puro — não exibir para o usuário
            return {
                "messages": [MedCronMessage(role="assistant", content=resposta_bruta)],
                "resposta_final": resposta_bruta,
                "next_node": "end",
            }

        # Resposta conversacional normal — limpa qualquer resquício de JSON
        resposta_limpa = _limpar_resposta(resposta_bruta)

        return {
            "messages": [MedCronMessage(role="assistant", content=resposta_limpa)],
            "resposta_final": resposta_limpa,
            "next_node": "end",
        }

    except Exception as e:
        fallback = "Não consegui processar sua mensagem. Pode tentar novamente?"
        return {
            "resposta_final": fallback,
            "messages": [MedCronMessage(role="assistant", content=fallback)],
            "next_node": "end",
        }


def _extrair_json_agendamento(texto: str) -> dict | None:
    """
    Extrai o objeto JSON de agendamento do texto, se houver.
    Tenta extrair de blocos markdown ou JSON solto.
    """
    # Remove blocos markdown ```json ... ```
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", texto)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Tenta extrair JSON diretamente (chave de abertura até fechamento)
    first_brace = texto.find("{")
    last_brace = texto.rfind("}")
    if first_brace != -1 and last_brace > first_brace:
        try:
            return json.loads(texto[first_brace:last_brace + 1])
        except json.JSONDecodeError:
            pass

    return None


def _limpar_resposta(texto: str) -> str:
    """Remove artefatos técnicos da resposta antes de exibir ao usuário."""
    # Remove blocos de código
    texto = re.sub(r"```[\w]*[\s\S]*?```", "", texto)
    # Remove objetos JSON soltos
    texto = re.sub(r"\{[\s\S]*?\}", "", texto)
    # Remove asteriscos de markdown
    texto = re.sub(r"\*+", "", texto)
    # Remove hífens de lista no início de linha (mas mantém hifens em palavras)
    texto = re.sub(r"^\s*-\s+", "", texto, flags=re.MULTILINE)
    # Comprime linhas em branco extras
    texto = re.sub(r"\n{3,}", "\n", texto)
    return texto.strip()

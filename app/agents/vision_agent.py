"""
MedCron_Py — Agente de Visão (OCR de Receitas via Gemini 1.5 Pro)

Recebe a imagem da receita médica em base64 e extrai os medicamentos
em formato estruturado (JSON). Usa Gemini pela superioridade em OCR
de caligrafia médica e janela de contexto generosa.
"""
import json
import re
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.agents.state import AgentState, MedCronMessage
from app.agents.validador_farmaceutico import validar_lista_medicamentos
from app.core.config import get_settings

VISION_SYSTEM_PROMPT = """
Você é um especialista em leitura de receitas médicas e documentos clínicos do MedCron.
Analise a imagem da receita médica fornecida e extraia TODOS os medicamentos e informações solicitadas.

Responda SOMENTE com um JSON válido no seguinte formato (sem markdown, sem explicações):
{
  "medicamentos": [
    {
      "nome": "Nome do medicamento",
      "dosagem": "Ex: 500mg",
      "frequencia": "Ex: de 8 em 8 horas",
      "frequencia_por_dia": 3,
      "duracao_dias": 7,
      "instrucao": "Ex: Tomar após as refeições"
    }
  ],
  "medico_nome": "Nome do médico (se visível)",
  "medico_crm": "CRM (se visível)",
  "data_receita": "Data (se visível)",
  "observacoes": "Outras instruções relevantes"
}

Se um campo não for legível, use null.
"""


async def vision_agent_node(state: AgentState) -> dict:
    if not state.tem_imagem or not state.messages:
        return {
            "resposta_final": "Não encontrei nenhuma imagem de receita na sua mensagem. Envie a foto.",
            "next_node": "end",
        }

    ultima_com_imagem = next((m for m in reversed(state.messages) if m.image_base64), None)
    if not ultima_com_imagem:
        return {"resposta_final": "Não consegui localizar a imagem.", "next_node": "end"}

    try:
        settings = get_settings()
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=settings.openai_api_key,
            temperature=0.1,
            max_tokens=600,
            response_format={"type": "json_object"},
        )

        raw_b64 = ultima_com_imagem.image_base64 or ""
        mime_type = "image/jpeg"
        if raw_b64.startswith("data:"):
            header, raw_b64 = raw_b64.split(",", 1)
            if ":" in header and ";" in header:
                mime_type = header.split(":")[1].split(";")[0]

        image_message = HumanMessage(
            content=[
                {"type": "text", "text": "Extraia os dados desta receita."},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{raw_b64}"},
                },
            ]
        )

        response = await llm.ainvoke([SystemMessage(content=VISION_SYSTEM_PROMPT), image_message])
        
        dados_receita = json.loads(response.content)
        medicamentos_brutos = dados_receita.get("medicamentos", [])
        medico_nome = dados_receita.get("medico_nome")
        medico_crm = dados_receita.get("medico_crm")

        # Validação farmacológica determinística
        medicamentos_validados, alertas = validar_lista_medicamentos(medicamentos_brutos)

        has_critical_alert = any(a.startswith("[ALERTA CLINICO]") for a in alertas if a)

        if has_critical_alert:
            resposta = (
                "⚠️ ALERTA DE SEGURANÇA: Por segurança, o agendamento não será realizado. "
                "Foi detectada uma dosagem acima do limite seguro. Por favor, consulte seu médico "
                "para revisar a prescrição.\n\n"
            ) + "\n".join(a for a in alertas if a.startswith("[ALERTA CLINICO]"))
            
            return {
                "alertas_clinicos": alertas,
                "messages": [MedCronMessage(role="assistant", content=resposta)],
                "resposta_final": resposta,
                "next_node": "end",
            }

        if not medicamentos_validados:
            return {
                "resposta_final": "Não consegui identificar nenhum medicamento de forma segura na receita. Pode mandar uma foto mais nítida?",
                "next_node": "end",
            }

        texto_extraido = "Receita lida:\n"
        if medico_nome:
            texto_extraido += f"👨‍⚕️ Médico: {medico_nome}"
            if medico_crm:
                texto_extraido += f" (CRM: {medico_crm})"
            texto_extraido += "\n"
            
        for med in medicamentos_validados:
            texto_extraido += f"• {med['nome']} {med.get('dosagem', '')} — {med.get('frequencia', '')}\n"

        resposta = (
            f"✅ Consegui ler sua receita! Eis o que encontrei:\n\n{texto_extraido}\n"
            "Essas informações estão corretas?"
        )

        # Atualiza o estado
        return {
            "receita_texto_bruto": texto_extraido,
            "medicamentos_validados": medicamentos_validados,
            "medico_nome": medico_nome,
            "medico_crm": medico_crm,
            "alertas_clinicos": alertas,
            "messages": [MedCronMessage(role="assistant", content=resposta)],
            "resposta_final": resposta,
            # NÃO salva ainda! Termina aqui para esperar a resposta "sim" do usuário.
            "next_node": "end",
        }

    except Exception as e:
        return {
            "resposta_final": f"Erro na leitura da receita. (Detalhe: {type(e).__name__})",
            "next_node": "end",
        }

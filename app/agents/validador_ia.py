"""
MedCron_Py — Validador Farmacológico Inteligente (GPT-4o-mini)

Usa o GPT-4o-mini como farmacêutico clínico para validar doses e horários
da receita extraída considerando o perfil do paciente (peso, idade, sexo).

Complementa o validador determinístico (validador_farmaceutico.py):
- Este módulo usa IA para cobrir medicamentos não catalogados e avaliações
  contextuais (dose pediátrica por peso, interações, populações especiais).
- O validador determinístico é usado como fallback se este falhar.
"""
import json
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# ── Prompt do Farmacêutico Clínico ────────────────────────────────────────────
PROMPT_FARMACEUTICO = """Você é um farmacêutico clínico sênior revisando uma prescrição médica.
Analise os medicamentos abaixo considerando o perfil do paciente e as bulas dos fabricantes.

PERFIL DO PACIENTE:
- Idade: {idade} anos
- Peso: {peso_kg} kg
- Sexo: {sexo}

MEDICAMENTOS PRESCRITOS:
{medicamentos_json}

TAREFA:
Verifique cada medicamento em relação a:
1. Dose unitária por tomada — está dentro do limite máximo do fabricante?
2. Dose diária total — está dentro do limite máximo do fabricante?
3. Frequência/horários — são adequados para o medicamento?
4. Populações especiais — ajustes necessários para a idade e peso do paciente?
   - Idosos (>65 anos): verificar clearance renal, sedação, quedas
   - Crianças (<12 anos): verificar dose por kg e contraindicações
   - Baixo peso (<40 kg): verificar dose por kg
5. Interações perigosas — há combinações de risco entre os medicamentos listados?

REGRAS IMPORTANTES:
- Seja CONSERVADOR: em caso de dúvida, gere um alerta.
- Separe alertas CRÍTICOS (risco real de saúde) de alertas INFORMATIVOS (recomendações de uso).
- Alertas críticos justificam BLOQUEAR o agendamento.
- Alertas informativos são apenas orientações ao paciente.
- Se a prescrição estiver dentro dos padrões, confirme como segura.
- Responda SOMENTE com JSON válido, sem texto fora do JSON.

FORMATO DE RESPOSTA (JSON):
{{
  "aprovado": true,
  "alertas_criticos": [],
  "alertas_informativos": [
    "Ex: Tomar o Omeprazol em jejum, 30 minutos antes do café da manhã."
  ]
}}

Se houver risco:
{{
  "aprovado": false,
  "alertas_criticos": [
    "Ex: A dose de Paracetamol (3g por tomada, 4x/dia = 12g/dia) excede em 3x o limite máximo seguro de 4g/dia para adultos. Risco de hepatotoxicidade grave."
  ],
  "alertas_informativos": []
}}
"""


@dataclass
class ResultadoValidacaoIA:
    """Resultado da validação farmacológica via IA."""
    aprovado: bool
    alertas_criticos: list[str] = field(default_factory=list)
    alertas_informativos: list[str] = field(default_factory=list)
    fallback_usado: bool = False  # True se o validador determinístico foi acionado


async def validar_receita_ia(
    medicamentos: list[dict],
    peso_kg: float | None,
    idade: int | None,
    sexo: str | None = None,
) -> ResultadoValidacaoIA:
    """
    Valida a lista de medicamentos contra o perfil do paciente usando GPT-4o-mini.

    Args:
        medicamentos: Lista de dicts com 'nome', 'dosagem', 'frequencia', 'frequencia_por_dia'
        peso_kg:      Peso do paciente em kg (pode ser None se ainda não coletado)
        idade:        Idade do paciente em anos (pode ser None se ainda não coletado)
        sexo:         Sexo do paciente ('masculino' | 'feminino' | None)

    Returns:
        ResultadoValidacaoIA com aprovado=False e alertas_criticos preenchidos se houver risco.
    """
    if not medicamentos:
        return ResultadoValidacaoIA(aprovado=True)

    # Se não temos dados suficientes do paciente, apenas retorna aprovado
    # (a validação completa só faz sentido com peso e idade)
    if peso_kg is None and idade is None:
        logger.info("[ValidadorIA] Peso e idade não disponíveis. Pulando validação IA.")
        return ResultadoValidacaoIA(aprovado=True)

    try:
        from langchain_openai import ChatOpenAI
        from app.core.config import get_settings

        settings = get_settings()

        # Prepara representação legível dos medicamentos para o prompt
        meds_formatados = []
        for med in medicamentos:
            meds_formatados.append({
                "nome": med.get("nome", "Desconhecido"),
                "dosagem_por_tomada": med.get("dosagem", "Não especificada"),
                "frequencia": med.get("frequencia", "Não especificada"),
                "vezes_por_dia": med.get("frequencia_por_dia", 1),
                "duracao_dias": med.get("duracao_dias", 7),
            })

        prompt = PROMPT_FARMACEUTICO.format(
            idade=idade if idade is not None else "não informado",
            peso_kg=peso_kg if peso_kg is not None else "não informado",
            sexo=sexo or "não informado",
            medicamentos_json=json.dumps(meds_formatados, ensure_ascii=False, indent=2),
        )

        llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=settings.openai_api_key,
            temperature=0.0,   # Zero — queremos análise determinística e conservadora
            max_tokens=1024,
            response_format={"type": "json_object"},
        )

        from langchain_core.messages import SystemMessage, HumanMessage
        response = await llm.ainvoke([
            SystemMessage(content="Você é um farmacêutico clínico analisando uma prescrição. Responda APENAS em JSON válido."),
            HumanMessage(content=prompt),
        ])

        dados = json.loads(response.content)

        return ResultadoValidacaoIA(
            aprovado=dados.get("aprovado", True),
            alertas_criticos=dados.get("alertas_criticos", []),
            alertas_informativos=dados.get("alertas_informativos", []),
        )

    except Exception as e:
        logger.warning(f"[ValidadorIA] Falha na validação IA: {e}. Ativando fallback determinístico.")
        return await _fallback_deterministico(medicamentos)


async def _fallback_deterministico(medicamentos: list[dict]) -> ResultadoValidacaoIA:
    """
    Fallback para o validador determinístico se a chamada IA falhar.
    Garante que ao menos os medicamentos catalogados sejam verificados.
    """
    try:
        from app.agents.validador_farmaceutico import validar_lista_medicamentos
        aprovados, alertas = validar_lista_medicamentos(medicamentos)

        # Distingue alertas bloqueantes de informativos pelo prefixo
        criticos = [a for a in alertas if "[ALERTA CLINICO]" in a]
        informativos = [a for a in alertas if "[INFO]" in a or "[AVISO]" in a]

        return ResultadoValidacaoIA(
            aprovado=len(criticos) == 0,
            alertas_criticos=criticos,
            alertas_informativos=informativos,
            fallback_usado=True,
        )
    except Exception as fallback_err:
        logger.error(f"[ValidadorIA] Fallback também falhou: {fallback_err}")
        return ResultadoValidacaoIA(aprovado=True, fallback_usado=True)


def formatar_alerta_para_paciente(resultado: ResultadoValidacaoIA) -> str:
    """
    Formata os alertas críticos em uma mensagem clara e humana para o paciente.
    Usado pelo medcron_agent para injetar no contexto da conversa.
    """
    if not resultado.alertas_criticos:
        return ""

    linhas = ["[ALERTA FARMACÊUTICO - AÇÃO OBRIGATÓRIA]"]
    linhas.append("O sistema de segurança identificou os seguintes problemas na prescrição:")
    for alerta in resultado.alertas_criticos:
        linhas.append(f"- {alerta}")
    linhas.append("")
    linhas.append(
        "INSTRUÇÃO: Informe o paciente de forma clara, humana e sem tecnicismos sobre esse risco. "
        "Oriente-o a contatar o médico prescritor ANTES de iniciar o tratamento. "
        "NÃO gere JSON de agendamento. NÃO continue a entrevista. NÃO agende nada."
    )
    return "\n".join(linhas)

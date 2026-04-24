"""
MedCron_Py — Validador Farmacêutico (Determinístico, Zero IA)

Migração do clinicalValidator.js original para Python.
Bloqueia matematicamente dosagens acima dos limites seguros
ANTES de qualquer resposta ao paciente.
"""
import re
from dataclasses import dataclass


@dataclass
class MedicamentoLimite:
    """Limites de segurança farmacológica."""
    nome_padrao: str          # Nome canônico
    aliases: list[str]        # Variações de escrita aceitas
    dose_maxima_unitaria_mg: float | None   # Por tomada
    dose_maxima_diaria_mg: float            # Limite por 24h


# ── Banco de Dados Farmacológico (Determinístico) ─────────────────────────────
FARMACOS_SEGUROS: list[MedicamentoLimite] = [
    MedicamentoLimite(
        nome_padrao="Paracetamol",
        aliases=["paracetamol", "acetaminofen", "tylenol", "dipirona paracetamol"],
        dose_maxima_unitaria_mg=1000.0,
        dose_maxima_diaria_mg=4000.0,
    ),
    MedicamentoLimite(
        nome_padrao="Ibuprofeno",
        aliases=["ibuprofeno", "ibuprofen", "advil", "nurofen"],
        dose_maxima_unitaria_mg=800.0,
        dose_maxima_diaria_mg=3200.0,
    ),
    MedicamentoLimite(
        nome_padrao="Amoxicilina",
        aliases=["amoxicilina", "amoxicillin", "amoxil"],
        dose_maxima_unitaria_mg=1000.0,
        dose_maxima_diaria_mg=3000.0,
    ),
    MedicamentoLimite(
        nome_padrao="Dipirona",
        aliases=["dipirona", "metamizol", "novalgina", "neosaldina"],
        dose_maxima_unitaria_mg=1000.0,
        dose_maxima_diaria_mg=4000.0,
    ),
    MedicamentoLimite(
        nome_padrao="Azitromicina",
        aliases=["azitromicina", "azithromycin", "zithromax"],
        dose_maxima_unitaria_mg=500.0,
        dose_maxima_diaria_mg=500.0,
    ),
    MedicamentoLimite(
        nome_padrao="Omeprazol",
        aliases=["omeprazol", "omeprazole", "losec", "prilosec"],
        dose_maxima_unitaria_mg=80.0,
        dose_maxima_diaria_mg=160.0,
    ),
]


def _extrair_mg(texto_dosagem: str) -> float | None:
    """
    Extrai o valor numérico de mg de um texto como '500mg', '1g', '0.5g'.
    Retorna None se não conseguir parsear.
    """
    texto = texto_dosagem.lower().strip()

    # Padrão: "500mg" ou "500 mg"
    match_mg = re.search(r"(\d+(?:[.,]\d+)?)\s*mg", texto)
    if match_mg:
        return float(match_mg.group(1).replace(",", "."))

    # Padrão: "1g" ou "0.5 g" → converter para mg
    match_g = re.search(r"(\d+(?:[.,]\d+)?)\s*g\b", texto)
    if match_g:
        return float(match_g.group(1).replace(",", ".")) * 1000

    return None


def _encontrar_farmaco(nome_medicamento: str) -> MedicamentoLimite | None:
    """Busca o farmacológico pelo nome (case-insensitive)."""
    nome_lower = nome_medicamento.lower()
    for farmaco in FARMACOS_SEGUROS:
        for alias in farmaco.aliases:
            if alias in nome_lower or nome_lower in alias:
                return farmaco
    return None


@dataclass
class ResultadoValidacao:
    """Resultado da validação de um medicamento."""
    medicamento: str
    aprovado: bool
    alerta: str | None = None
    dose_mg: float | None = None
    dose_diaria_mg: float | None = None


def validar_medicamento(
    nome: str,
    dosagem_str: str,
    frequencia_por_dia: int = 1,
) -> ResultadoValidacao:
    """
    Valida se um medicamento com a dosagem e frequência fornecidas
    está dentro dos limites seguros.

    Args:
        nome: Nome do medicamento (ex: "Paracetamol")
        dosagem_str: String de dosagem (ex: "500mg", "1g")
        frequencia_por_dia: Quantas vezes ao dia (ex: 3 para "de 8 em 8h")

    Returns:
        ResultadoValidacao com aprovado=False e alerta preenchido se houver risco.
    """
    farmaco = _encontrar_farmaco(nome)

    if farmaco is None:
        # Medicamento desconhecido → passa pela validação (sem dados para bloquear)
        return ResultadoValidacao(
            medicamento=nome,
            aprovado=True,
            alerta=f"[INFO] {nome}: Medicamento nao catalogado. Validacao humana recomendada.",
        )

    dose_mg = _extrair_mg(dosagem_str)

    if dose_mg is None:
        return ResultadoValidacao(
            medicamento=nome,
            aprovado=True,
            alerta=f"[AVISO] {nome}: Nao foi possivel parsear a dosagem '{dosagem_str}'. Verificar manualmente.",
        )

    dose_diaria = dose_mg * frequencia_por_dia

    # Verifica dose unitária
    if farmaco.dose_maxima_unitaria_mg and dose_mg > farmaco.dose_maxima_unitaria_mg:
        return ResultadoValidacao(
            medicamento=nome,
            aprovado=False,
            alerta=(
                f"[ALERTA CLINICO] {nome}: Dose unitaria de {dose_mg:.0f}mg "
                f"excede o maximo seguro de {farmaco.dose_maxima_unitaria_mg:.0f}mg por tomada!"
            ),
            dose_mg=dose_mg,
            dose_diaria_mg=dose_diaria,
        )

    # Verifica dose diária total
    if dose_diaria > farmaco.dose_maxima_diaria_mg:
        return ResultadoValidacao(
            medicamento=nome,
            aprovado=False,
            alerta=(
                f"[ALERTA CLINICO] {nome}: Dose diaria calculada de {dose_diaria:.0f}mg "
                f"({dose_mg:.0f}mg x {frequencia_por_dia}x/dia) excede o maximo seguro de "
                f"{farmaco.dose_maxima_diaria_mg:.0f}mg/dia!"
            ),
            dose_mg=dose_mg,
            dose_diaria_mg=dose_diaria,
        )

    return ResultadoValidacao(
        medicamento=nome,
        aprovado=True,
        dose_mg=dose_mg,
        dose_diaria_mg=dose_diaria,
    )


def validar_lista_medicamentos(
    medicamentos: list[dict],
) -> tuple[list[dict], list[str]]:
    """
    Valida uma lista de medicamentos extraída pelo Agente de Visão.

    Args:
        medicamentos: Lista de dicts com campos 'nome', 'dosagem', 'frequencia_por_dia'

    Returns:
        Tupla: (medicamentos_aprovados, alertas_clinicos)
    """
    aprovados = []
    alertas = []

    for med in medicamentos:
        resultado = validar_medicamento(
            nome=med.get("nome", ""),
            dosagem_str=med.get("dosagem", ""),
            frequencia_por_dia=med.get("frequencia_por_dia", 1),
        )

        if resultado.aprovado:
            aprovados.append({
                **med,
                "_dose_mg_validada": resultado.dose_mg,
                "_dose_diaria_mg": resultado.dose_diaria_mg,
            })
        else:
            alertas.append(resultado.alerta)
            # Remove medicamento não aprovado da lista (agente decidirá o que fazer)

        # Adiciona alertas informativos mesmo para aprovados
        if resultado.aprovado and resultado.alerta:
            alertas.append(resultado.alerta)

    return aprovados, alertas

/**
 * MedCron — Validação Clínica Determinística
 *
 * Esta camada de segurança NUNCA depende do LLM.
 * Ela roda em JavaScript puro antes de qualquer agendamento,
 * com regras fixas baseadas em limites farmacológicos conhecidos.
 */

/**
 * Limites diários máximos por medicamento (nome parcial → mg/dia)
 * Baseado em bulas e diretrizes da ANVISA/WHO.
 */
const DOSE_LIMITS = [
  { pattern: /amoxicilina|antibiotico/i,   maxDosePerDay: 3000,   maxDosePerTake: 1000, minIntervalHours: 6 },
  { pattern: /amoxicilina.*clavulanato/i, maxDosePerDay: 4000, maxDosePerTake: 1000, minIntervalHours: 8 },
  { pattern: /dipirona/i,           maxDosePerDay: 4000,   maxDosePerTake: 1000,  minIntervalHours: 4 },
  { pattern: /paracetamol|acetaminofeno/i, maxDosePerDay: 4000, maxDosePerTake: 1000, minIntervalHours: 4 },
  { pattern: /ibuprofeno/i,         maxDosePerDay: 2400,   maxDosePerTake: 800,   minIntervalHours: 6 },
  { pattern: /azitromicina/i,       maxDosePerDay: 500,    maxDosePerTake: 500,   minIntervalHours: 24 },
  { pattern: /loratadina/i,         maxDosePerDay: 10,     maxDosePerTake: 10,    minIntervalHours: 24 },
  { pattern: /dexametasona/i,       maxDosePerDay: 16,     maxDosePerTake: 8,     minIntervalHours: 8 },
  { pattern: /prednisona/i,         maxDosePerDay: 80,     maxDosePerTake: 60,    minIntervalHours: 12 },
  // Regra genérica para qualquer remédio não mapeado (catch-all preventivo)
  { pattern: /.*/,                  maxDosePerDay: 5000,   maxDosePerTake: 1500,  minIntervalHours: 4 },
]

/**
 * Extrai o valor numérico de mg de uma string de dosagem.
 * Ex: "1 cápsula (500mg)" → 500
 * Ex: "40 gotas" → tenta estimar: 1 gota ≈ variável (padrão 12,5mg para dipirona)
 */
function extractMgFromDosage(dosageStr) {
  if (!dosageStr) return null

  // Tenta extrair valor explícito em mg
  const mgMatch = dosageStr.match(/(\d+(?:[.,]\d+)?)\s*mg/i)
  if (mgMatch) return parseFloat(mgMatch[1].replace(',', '.'))

  // Tenta extrair gotas (1 gota de dipirona 500mg/mL ≈ usa-se 20 gotas = 500mg → 1 gota = 25mg)
  const dropMatch = dosageStr.match(/(\d+)\s*gotas?/i)
  if (dropMatch) return parseInt(dropMatch[1]) * 25 // estimativa conservadora

  // Tenta extrair comprimidos/cápsulas genérico (sem mg → não podemos validar)
  return null
}

/**
 * Conta o número de doses diárias com base nos horários.
 */
function countDailyDoses(reminder) {
  if (!reminder.time || reminder.time === '--:--') return 1
  // Se time contém múltiplos horários separados por vírgula
  const times = reminder.time.split(/[,;]/).filter(t => /\d{1,2}:\d{2}/.test(t))
  return Math.max(times.length, 1)
}

/**
 * Detecta frequência suspeita:
 * intervalo entre doses < mínimo permitido
 */
function detectFrequencyIssue(reminder, rule) {
  if (!reminder.time || reminder.time === '--:--') return null

  const times = reminder.time
    .split(/[,;]/)
    .map(t => t.match(/(\d{1,2}):(\d{2})/))
    .filter(Boolean)
    .map(m => parseInt(m[1]) * 60 + parseInt(m[2]))
    .sort((a, b) => a - b)

  if (times.length < 2) return null

  const minGap = Math.min(
    ...times.slice(1).map((t, i) => t - times[i])
  )
  const minGapHours = minGap / 60

  if (minGapHours < rule.minIntervalHours) {
    return {
      type: 'frequency',
      message: `O intervalo entre doses de "${reminder.name}" está em ${minGapHours.toFixed(1)}h, mas o mínimo seguro é de ${rule.minIntervalHours}h.`
    }
  }
  return null
}

/**
 * Função principal de validação.
 * Retorna objeto com erros (bloqueios) e avisos (orientações).
 *
 * @param {Array} reminders - Lista de reminders do JSON do LLM
 * @param {Object} patient - { age, weight, sex }
 * @returns {{ safe: boolean, errors: string[], warnings: string[] }}
 */
export function validateClinicalSafety(reminders, patient) {
  const errors = []
  const warnings = []

  if (!reminders || reminders.length === 0) return { safe: true, errors: [], warnings: [] }

  const weight = parseFloat(patient?.weight) || null
  const age = parseInt(patient?.age) || null

  for (const reminder of reminders) {
    const name = reminder.name || reminder.nome || ''
    const dosageStr = reminder.dosage || reminder.dosagem || ''

    // Encontra regra correspondente
    const rule = DOSE_LIMITS.find(r => r.pattern.test(name))
    if (!rule) continue 

    const mgPerDose = extractMgFromDosage(dosageStr)
    if (mgPerDose === null) continue

    const dailyDoses = countDailyDoses(reminder)
    const totalMgPerDay = mgPerDose * dailyDoses

    // 1. Verifica dose por tomada (ERRO)
    if (mgPerDose > rule.maxDosePerTake) {
      errors.push(
        `⚠️ DOSE EXCESSIVA: A dosagem de "${name}" está acima do limite de segurança por tomada.`
      )
    }

    // 2. Verifica dose diária total (ERRO)
    if (totalMgPerDay > rule.maxDosePerDay) {
      errors.push(
        `🚨 SUPERDOSE DIÁRIA: A carga diária total de "${name}" excede os limites de segurança do fabricante.`
      )
    }

    // 3. Verifica intervalo de horários (ERRO)
    const freqIssue = detectFrequencyIssue(reminder, rule)
    if (freqIssue) {
      errors.push(`⏱️ INTERVALO INSEGURO: O intervalo entre as doses de "${name}" está fora dos parâmetros de segurança.`)
    }

    // 4. Ajuste por peso (AVISO)
    if (weight && weight < 40) {
      const mgPerKg = mgPerDose / weight
      const maxSafeMgKg = 25 
      if (mgPerKg > maxSafeMgKg) {
        warnings.push(
          `👶 ATENÇÃO PEDIÁTRICA: A dose de "${name}" parece elevada para o peso informado (${weight}kg).`
        )
      }
    }

    // 5. Alerta de idoso com dose alta (AVISO)
    if (age && age >= 65 && totalMgPerDay > rule.maxDosePerDay * 0.75) {
      warnings.push(
        `👴 ATENÇÃO GERIÁTRICA: A dosagem de "${name}" pode ser excessiva para pacientes acima de 65 anos.`
      )
    }
  }

  return {
    safe: errors.length === 0,
    errors,
    warnings
  }
}

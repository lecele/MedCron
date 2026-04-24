/**
 * Serviço de Calendário — MedCron
 *
 * ESTRATÉGIA NOVA (migração para FastAPI):
 * O servidor Python gera o .ics perfeito com VTIMEZONE, VALARM e RRULE.
 * O frontend apenas solicita o arquivo via GET e oferece o download nativo.
 * Isso resolve o bug do Apple Calendar / iOS que ocorria com a geração client-side.
 */

/**
 * Baixa o arquivo .ics gerado pelo backend FastAPI.
 * Em iOS: abre nativamente o app de Calendário para importação.
 * Em Android/PC: dispara o download do arquivo.
 *
 * @param {string} usuarioId - UUID do paciente no Supabase
 * @param {string} [profileName] - Nome do perfil para o nome do arquivo
 */
export const downloadCalendarFromServer = async (usuarioId, profileName = 'medcron') => {
  if (!usuarioId) {
    console.error('[Calendar] usuario_id não fornecido.');
    return;
  }

  const url = `/api/calendar/generate?usuario_id=${encodeURIComponent(usuarioId)}`;

  try {
    const response = await fetch(url);

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    const blob = await response.blob();
    const objectUrl = URL.createObjectURL(blob);

    const isIos = /iPhone|iPad|iPod/i.test(navigator.userAgent);

    if (isIos) {
      // iOS: abre direto — o sistema reconhece text/calendar e sugere adicionar ao Calendário
      window.location.href = objectUrl;
    } else {
      // Android / Desktop: força download do .ics
      const fileName = `${profileName.replace(/\s+/g, '_')}_lembretes.ics`;
      const link = document.createElement('a');
      link.href = objectUrl;
      link.setAttribute('download', fileName);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }

    setTimeout(() => URL.revokeObjectURL(objectUrl), 10000);
  } catch (err) {
    console.error('[Calendar] Erro ao baixar calendário do servidor:', err);
    throw err; // O chamador pode exibir um toast de erro
  }
};

// ── Funções legadas mantidas para compatibilidade retroativa ──────────────────
// (usadas antes da migração para FastAPI — podem ser removidas futuramente)

const formatIcsDate = (dateStr, timeStr) => {
  if (!timeStr || !timeStr.match(/\d{2}:\d{2}/)) return null;
  if (!dateStr || typeof dateStr !== 'string') return null;
  return dateStr.replace(/-/g, '') + 'T' + timeStr.replace(':', '') + '00';
};

/** @deprecated Use downloadCalendarFromServer em vez desta função */
export const generateSingleIcs = (reminders) => {
  if (!reminders || reminders.length === 0) return null;
  const valid = reminders.filter(r => r.time && r.time.match(/^\d{2}:\d{2}$/) && r.data_inicio);
  if (valid.length === 0) return null;

  let icsLines = ['BEGIN:VCALENDAR', 'VERSION:2.0'];
  valid.forEach((rem, idx) => {
    try {
      const dtStart = formatIcsDate(rem.data_inicio, rem.time);
      if (!dtStart) return;
      const duracao = parseInt(rem.duracao_dias) || 7;
      icsLines.push('BEGIN:VEVENT');
      icsLines.push(`UID:m${idx}${dtStart}`);
      icsLines.push(`DTSTART:${dtStart}`);
      icsLines.push(`RRULE:FREQ=DAILY;COUNT=${duracao}`);
      icsLines.push(`SUMMARY:${rem.name || 'Rem'} ${rem.dosage || ''}`.trim());
      icsLines.push('END:VEVENT');
    } catch (err) {
      console.warn('Erro ao processar lembrete', err);
    }
  });
  icsLines.push('END:VCALENDAR');
  return icsLines.join('\r\n');
};

/** @deprecated Use downloadCalendarFromServer em vez desta função */
export const downloadIcsFile = (reminders, profileName) => {
  const text = generateSingleIcs(reminders);
  if (!text) return;
  const blob = new Blob([text], { type: 'text/calendar;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `${(profileName || 'meds').replace(/\s+/g, '_')}.ics`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  setTimeout(() => URL.revokeObjectURL(url), 5000);
};

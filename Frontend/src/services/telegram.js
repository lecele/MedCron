/**
 * Telegram Notification Service
 * Envia mensagens para o grupo Medicações via bot do Telegram.
 *
 * ⚠️  O token do bot NUNCA deve ser exposto no frontend.
 * Todas as chamadas ao Telegram passam pelo backend FastAPI,
 * que lê TELEGRAM_BOT_TOKEN das variáveis de ambiente do servidor.
 *
 * O frontend apenas monta o deep link para o usuário iniciar
 * a conversa com o bot — sem precisar do token.
 */

const TELEGRAM_BOT_USERNAME = import.meta.env.VITE_TELEGRAM_BOT_USERNAME || 'MedCron_bot';
const MEDICACOES_GROUP_ID = '-5299673620';

/**
 * Gera o deep link para o usuário abrir o bot no Telegram.
 * Não requer token — é apenas uma URL pública do Telegram.
 */
export const getTelegramBotLink = () =>
  `https://t.me/${TELEGRAM_BOT_USERNAME}`;

/**
 * notifyRemindersToGroup
 *
 * Chamada roteada pelo backend (FastAPI /api/telegram/notify).
 * O frontend envia os dados para o backend, que usa o token
 * armazenado como variável de ambiente do servidor.
 */
export const notifyRemindersToGroup = async (reminders) => {
  if (!reminders || reminders.length === 0) return;

  try {
    const response = await fetch('/api/telegram/notify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reminders, group_id: MEDICACOES_GROUP_ID }),
    });

    if (!response.ok) {
      console.warn('[Telegram] Backend retornou erro:', response.status);
      return false;
    }
    return true;
  } catch (err) {
    console.error('[Telegram] Erro ao notificar via backend:', err);
    return false;
  }
};

/**
 * sendReminderAlert — delega ao backend
 */
export const sendReminderAlert = async (reminder) => {
  return notifyRemindersToGroup([{
    message_override:
      `⏰ <b>Hora do medicamento!</b>\n\n💊 ${reminder.name}\n📏 Dose: ${reminder.dosage}`,
  }]);
};

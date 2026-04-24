import { createClient } from '@supabase/supabase-js';
import { sendTelegramMessage } from './src/services/telegram.js';

// Mesma configuração do src/services/supabase.js
const SUPABASE_URL = 'https://fpphdvenvxmuslpvemub.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZwcGhkdmVudnhtdXNscHZlbXViIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM3Njc0MTEsImV4cCI6MjA4OTM0MzQxMX0.MX_Z13S8XySJOu0TzubzD9smh8-KXIq28Wq6R-8P1tg';

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// ID do grupo Medicações (mesmo que está lá no telegram.js)
const MEDICACOES_GROUP_ID = '-5299673620';

// Controle de envios em memória para não repetir envio no mesmo minuto/dia
// Formato: "idLembrete-dataLocalISO"
const sentReminders = new Set();

console.log('🤖 Motor de Lembretes do Telegram Iniciado!');
console.log('Verificando horários a cada 30 segundos...\n');

const checkReminders = async () => {
  try {
    // 1. Busca todos perfis para ter o nome do usuário na ponta da língua se possível (opcional)
    const { data: profiles } = await supabase.from('profiles').select('id, nome, telefone');
    const profileMap = profiles ? profiles.reduce((acc, p) => ({...acc, [p.id]: p}), {}) : {};

    // 2. Busca todos lembretes pendentes
    const { data: lembretes, error } = await supabase
      .from('lembretes')
      .select('*')
      .eq('status', 'pendente');

    if (error) {
      console.error('Erro ao buscar lembretes:', error);
      return;
    }

    if (!lembretes || lembretes.length === 0) return;

    // Hora e data atual do servidor (convertendo pra horário local de Brasília UTC-3)
    // Para simplificar e bater com a mesma exibição do usuário, capturamos hh:mm string local
    const now = new Date();
    // Força locale pt-BR que já retorna no fuso do sistema onde estiver rodando (Brasil)
    const currentDateStr = now.toLocaleDateString('en-CA'); // en-CA padroniza YYYY-MM-DD local
    const currentTimeStr = now.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }); // "08:00"

    // 3. Verifica cada lembrete
    for (const rem of lembretes) {
      if (!rem.data_inicio || !rem.duracao_dias || !rem.horario) continue;

      // Verifica se está dentro do período de tratamento
      // Faz park da data do inicio como meio-dia evitamos timezone gaps
      const start = new Date(rem.data_inicio + "T12:00:00");
      start.setHours(0, 0, 0, 0);
      const end = new Date(start);
      end.setDate(start.getDate() + rem.duracao_dias - 1);
      
      const today = new Date(currentDateStr + "T12:00:00");
      today.setHours(0, 0, 0, 0);

      // Se passou do período ou começou ainda, ignora
      if (today < start || today > end) continue;

      // Verifica se é a exata hora "HH:MM". Extrai só os primeros 5 dígitos (ex. "08:00" do BD às vezes vem "08:00:00")
      const remTime = rem.horario.substring(0, 5);

      if (currentTimeStr === remTime) {
        // Encontramos um horário batendo! Verifica se já não enviou hoje:
        const sentKey = `${rem.id}-${currentDateStr}-${remTime}`;

        if (!sentReminders.has(sentKey)) {
          console.log(`⏰ Hora de tomar: ${rem.nome} (${rem.dosagem}) - Paciente: ${rem.usuario_id}`);
          
          let patientName = "Paciente";
          if (profileMap[rem.usuario_id] && profileMap[rem.usuario_id].nome) {
            patientName = profileMap[rem.usuario_id].nome;
          }

          // Monta a mensagem final do robô
          const msg = `⏰ <b>ALERTA DE MEDICAÇÃO</b> ⏰\n\n👤 Paciente: <b>${patientName}</b>\n💊 <b>${rem.nome}</b>\n📏 Dose: ${rem.dosagem}\n\n<i>Não esqueça de marcar como OK no aplicativo!</i>`;

          const success = await sendTelegramMessage(MEDICACOES_GROUP_ID, msg);
          
          if (success) {
            sentReminders.add(sentKey);
            console.log(`✅ Lembrete disparado para ${patientName}! (${rem.nome})`);
          } else {
            console.warn(`❌ Falha ao disparar telegram para id = ${rem.id}`);
          }
        }
      }
    }

  } catch (err) {
    console.error('Falha geral no motor:', err);
  }
};

// Executa a primeira checagem e depois inicia o loop
checkReminders();
setInterval(checkReminders, 30000); // 30 em 30 segundos

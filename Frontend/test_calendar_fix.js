import { generateIcsFile } from './src/services/calendar.js';

const mockReminders = [
  { name: 'Amoxicilina', dosage: '500mg', time: '08:00', data_inicio: '2026-03-25', duracao_dias: 7 },
  { name: 'Amoxicilina', dosage: '500mg', time: '16:00', data_inicio: '2026-03-25', duracao_dias: 7 },
  { name: 'Amoxicilina', dosage: '500mg', time: '00:00', data_inicio: '2026-03-25', duracao_dias: 7 }
];

const icsText = generateIcsFile(mockReminders);
console.log('--- ICS START ---');
console.log(icsText);
console.log('--- ICS END ---');

const vEvents = icsText.match(/BEGIN:VEVENT/g) || [];
console.log(`Encontrados ${vEvents.length} blocos VEVENT (Esperado: 1).`);

const vAlarms = icsText.match(/BEGIN:VALARM/g) || [];
console.log(`Encontrados ${vAlarms.length} blocos VALARM (Esperado: 3).`);

const hasPT0M = icsText.includes('TRIGGER:PT0M');
const hasPT8H = icsText.includes('TRIGGER:PT8H');
const hasPT16H = icsText.includes('TRIGGER:PT16H');

if (vEvents.length === 1 && vAlarms.length === 3 && hasPT0M && hasPT8H && hasPT16H) {
  console.log('✅ TESTE PASSOU: Único evento com 3 alarmes corretos detectado!');
} else {
  console.log('❌ TESTE FALHOU: A lógica de múltiplos alarmes não funcionou como esperado.');
}

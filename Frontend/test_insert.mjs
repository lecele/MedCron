import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = 'https://fpphdvenvxmuslpvemub.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZwcGhkdmVudnhtdXNscHZlbXViIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM3Njc0MTEsImV4cCI6MjA4OTM0MzQxMX0.MX_Z13S8XySJOu0TzubzD9smh8-KXIq28Wq6R-8P1tg';

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

async function testInsert() {
  const row = {
    usuario_id: 'd9b50e2d-dc99-43ef-b387-052637738f61', // arbitrary UUID
    nome: 'Teste',
    dosagem: '1 capsula',
    horario: '10:00',
    status: 'pendente',
    data_inicio: '2026-03-26',
    duracao_dias: 7
  };
  const { data, error } = await supabase.from('lembretes').insert(row).select();
  if (error) {
    console.log("Insert Error Message:", error.message);
    console.log("Full Error:", JSON.stringify(error, null, 2));
  } else {
    console.log("Insert Success! Data:", data);
  }
}
testInsert();

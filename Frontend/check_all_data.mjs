import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = 'https://fpphdvenvxmuslpvemub.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZwcGhkdmVudnhtdXNscHZlbXViIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM3Njc0MTEsImV4cCI6MjA4OTM0MzQxMX0.MX_Z13S8XySJOu0TzubzD9smh8-KXIq28Wq6R-8P1tg';

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

async function check() {
  const { count: profCount } = await supabase.from('profiles').select('*', { count: 'exact', head: true });
  const { count: lembCount } = await supabase.from('lembretes').select('*', { count: 'exact', head: true });
  const { count: recCount } = await supabase.from('receitas').select('*', { count: 'exact', head: true });
  
  console.log(`Profiles: ${profCount}`);
  console.log(`Lembretes: ${lembCount}`);
  console.log(`Receitas: ${recCount}`);
  
  if (lembCount > 0) {
    const { data } = await supabase.from('lembretes').select('*').limit(5);
    console.log("Lembretes data samples:", JSON.stringify(data, null, 2));
  }
}
check();

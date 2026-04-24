import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = 'https://fpphdvenvxmuslpvemub.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZwcGhkdmVudnhtdXNscHZlbXViIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM3Njc0MTEsImV4cCI6MjA4OTM0MzQxMX0.MX_Z13S8XySJOu0TzubzD9smh8-KXIq28Wq6R-8P1tg';

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

async function test() {
  const { data, error } = await supabase.from('lembretes').select('*').limit(1);
  console.log("Error:", error);
  console.log("Data length:", data ? data.length : 0);
}
test();

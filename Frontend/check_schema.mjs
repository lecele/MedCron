import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = 'https://fpphdvenvxmuslpvemub.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZwcGhkdmVudnhtdXNscHZlbXViIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM3Njc0MTEsImV4cCI6MjA4OTM0MzQxMX0.MX_Z13S8XySJOu0TzubzD9smh8-KXIq28Wq6R-8P1tg';

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

async function checkSchema() {
  const { data, error } = await supabase.from('lembretes').select('*').limit(1);
  if (error) {
    console.error("Error fetching lembretes:", error);
    return;
  }
  if (data && data.length > 0) {
    console.log("Columns:", Object.keys(data[0]));
  } else {
    // If empty, try to get column names via an insert attempt (hacky but works for schema discovery if it fails)
    const { error: insError } = await supabase.from('lembretes').insert({ test_non_existent: 1 });
    console.log("Insert error (for schema discovery):", insError.message);
  }
}
checkSchema();

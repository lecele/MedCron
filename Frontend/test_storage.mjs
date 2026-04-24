import { createClient } from '@supabase/supabase-js';
import fs from 'fs';

const SUPABASE_URL = 'https://fpphdvenvxmuslpvemub.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZwcGhkdmVudnhtdXNscHZlbXViIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM3Njc0MTEsImV4cCI6MjA4OTM0MzQxMX0.MX_Z13S8XySJOu0TzubzD9smh8-KXIq28Wq6R-8P1tg';

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

async function testStorage() {
  const icsText = "BEGIN:VCALENDAR\nEND:VCALENDAR";
  const { data, error } = await supabase.storage.from('receitas').upload('calendars/test.ics', icsText, {
    upsert: true,
    contentType: 'text/calendar'
  });
  
  if (error) {
    console.log("Upload Error:", error);
  } else {
    console.log("Upload Success:", data);
    const { data: urlData } = supabase.storage.from('receitas').getPublicUrl('calendars/test.ics');
    console.log("Public URL:", urlData.publicUrl);
  }
}
testStorage();

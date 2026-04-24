import { createClient } from '@supabase/supabase-js'

const SUPABASE_URL = 'https://fpphdvenvxmuslpvemub.supabase.co'
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZwcGhkdmVudnhtdXNscHZlbXViIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM3Njc0MTEsImV4cCI6MjA4OTM0MzQxMX0.MX_Z13S8XySJOu0TzubzD9smh8-KXIq28Wq6R-8P1tg'

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)

async function checkColumns() {
  console.log('Checking profiles columns...')
  const { data, error } = await supabase.from('profiles').select('*').limit(1)
  if (error) {
    console.error(error.message)
  } else if (data && data.length > 0) {
    console.log('Columns found:', Object.keys(data[0]))
  } else {
    // If empty, try to get column names from information_schema if possible, 
    // but usually select * on empty table returns keys if there is a row? No.
    // I'll try to insert a mock row with all possible columns to see what hits.
    console.log('Table is empty or RLS blocked. I will trust the screenshot for now but try a broad update.')
  }
}

checkColumns()

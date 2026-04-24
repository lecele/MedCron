import { createClient } from '@supabase/supabase-js'

const SUPABASE_URL = 'https://fpphdvenvxmuslpvemub.supabase.co'
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZwcGhkdmVudnhtdXNscHZlbXViIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM3Njc0MTEsImV4cCI6MjA4OTM0MzQxMX0.MX_Z13S8XySJOu0TzubzD9smh8-KXIq28Wq6R-8P1tg'

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)

async function testInsert() {
  const userId = '12345678-1234-1234-1234-123456789012' // Mock UUID
  console.log('Testing insert into receitas...')
  
  const { data, error } = await supabase
    .from('receitas')
    .insert({ 
      usuario_id: userId, 
      texto_extraido: 'TESTE DE EXTRAÇÃO - PACIENTE JOÃO', 
      data_receita: new Date().toISOString() 
    })
    .select()

  if (error) {
    console.error('ERRO NO INSERT:', error.message)
    console.error('DICA: Verifique as políticas de RLS no dashboard do Supabase.')
  } else {
    console.log('SUCESSO NO INSERT:', data)
  }
}

testInsert()

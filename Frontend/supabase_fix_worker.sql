-- REPARAR ESTRUTURA E PERMISSÃO PARA O WORKER (ROBÔ) DO TELEGRAM
-- Copie e cole este SQL no Supabase Dashboard > SQL Editor

-- 1. ADICIONA COLUNAS FALTANTES (que estão causando erro ao salvar)
ALTER TABLE public.lembretes ADD COLUMN IF NOT EXISTS data_inicio text;
ALTER TABLE public.lembretes ADD COLUMN IF NOT EXISTS duracao_dias integer;

-- 2. Remove política restritiva anterior (se existir)
DROP POLICY IF EXISTS "Lembretes: leak para worker" ON public.lembretes;

-- 3. Cria nova política permitindo leitura de lembretes para todos (necessário para worker anônimo)
CREATE POLICY "Lembretes: leak para worker" ON public.lembretes 
FOR SELECT USING (true);

-- 4. Verifica se funcionou
-- Rode este SQL e depois reinicie o worker no seu PC.

-- ============================================================
-- MEDICAÇÕES APP — Correção Final de Persistência e RLS
-- ============================================================

-- 1. Remove a trava de Foreign Key do Profile (permite IDs locais se o Auth falhar)
ALTER TABLE public.profiles DROP CONSTRAINT IF EXISTS profiles_id_fkey;

-- 2. Garante que as novas colunas existem em lembretes
ALTER TABLE public.lembretes ADD COLUMN IF NOT EXISTS data_inicio DATE;
ALTER TABLE public.lembretes ADD COLUMN IF NOT EXISTS duracao_dias INTEGER;

-- 3. Libera RLS para perfis (Criação e Consulta aberta para o ID do dispositivo)
DROP POLICY IF EXISTS "Profiles: ver próprio" ON public.profiles;
DROP POLICY IF EXISTS "Profiles: criar próprio" ON public.profiles;
DROP POLICY IF EXISTS "Profiles: atualizar próprio" ON public.profiles;
DROP POLICY IF EXISTS "Profiles: ver" ON public.profiles;
DROP POLICY IF EXISTS "Profiles: criar" ON public.profiles;
DROP POLICY IF EXISTS "Profiles: editar" ON public.profiles;

CREATE POLICY "Profiles: permissivo" ON public.profiles FOR ALL USING (true) WITH CHECK (true);

-- 4. Libera RLS para Receitas
DROP POLICY IF EXISTS "Receitas: gerenciar próprias" ON public.receitas;
CREATE POLICY "Receitas: permissivo" ON public.receitas FOR ALL USING (true) WITH CHECK (true);

-- 5. Libera RLS para Medicamentos
DROP POLICY IF EXISTS "Medicamentos: gerenciar próprios" ON public.medicamentos;
CREATE POLICY "Medicamentos: permissivo" ON public.medicamentos FOR ALL USING (true) WITH CHECK (true);

-- 6. Libera RLS para Lembretes (Essencial para o Worker e para o App)
DROP POLICY IF EXISTS "Lembretes: gerenciar próprios" ON public.lembretes;
DROP POLICY IF EXISTS "Lembretes: leak para worker" ON public.lembretes;
CREATE POLICY "Lembretes: permissivo" ON public.lembretes FOR ALL USING (true) WITH CHECK (true);

-- 7. Garante que as tabelas estão com RLS ativado (mas com as políticas abertas acima)
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.receitas ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.medicamentos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.lembretes ENABLE ROW LEVEL SECURITY;

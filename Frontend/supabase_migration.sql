-- ============================================================
-- MEDICAÇÕES APP — Criação das Tabelas no Supabase
-- Copie e cole este SQL no Supabase Dashboard > SQL Editor
-- ============================================================

-- 1. Perfis dos usuários
create table public.profiles (
  id uuid references auth.users on delete cascade not null primary key,
  nome text,
  idade integer,
  sexo text,
  telefone text,
  telegram_id text,
  medico_nome text,
  medico_crm text,
  onboarding_completo boolean default false,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- 2. Receitas médicas extraídas
create table public.receitas (
  id uuid default gen_random_uuid() primary key,
  usuario_id uuid references public.profiles(id) on delete cascade not null,
  texto_extraido text,
  data_receita timestamptz default now(),
  created_at timestamptz default now()
);

-- 3. Medicamentos de cada receita
create table public.medicamentos (
  id uuid default gen_random_uuid() primary key,
  receita_id uuid references public.receitas(id) on delete cascade,
  usuario_id uuid references public.profiles(id) on delete cascade not null,
  nome text not null,
  dosagem text,
  frequencia text,
  duracao_dias integer,
  created_at timestamptz default now()
);

-- 4. Lembretes de medicamentos
create table public.lembretes (
  id uuid default gen_random_uuid() primary key,
  usuario_id uuid references public.profiles(id) on delete cascade not null,
  nome text not null,
  dosagem text,
  horario text not null,
  status text default 'pendente',
  enviado_telegram boolean default false,
  created_at timestamptz default now()
);

-- ============================================================
-- ROW LEVEL SECURITY — cada usuário vê só seus dados
-- ============================================================

alter table public.profiles enable row level security;
alter table public.receitas enable row level security;
alter table public.medicamentos enable row level security;
alter table public.lembretes enable row level security;

-- Profiles
create policy "Profiles: ver próprio" on public.profiles for select using (auth.uid() = id);
create policy "Profiles: criar próprio" on public.profiles for insert with check (auth.uid() = id);
create policy "Profiles: atualizar próprio" on public.profiles for update using (auth.uid() = id);

-- Receitas
create policy "Receitas: gerenciar próprias" on public.receitas for all using (auth.uid() = usuario_id);

-- Medicamentos
create policy "Medicamentos: gerenciar próprios" on public.medicamentos for all using (auth.uid() = usuario_id);

-- Lembretes
create policy "Lembretes: gerenciar próprios" on public.lembretes for all using (auth.uid() = usuario_id);

-- ============================================================
-- FIM — execute este SQL no Supabase Dashboard > SQL Editor
-- ============================================================

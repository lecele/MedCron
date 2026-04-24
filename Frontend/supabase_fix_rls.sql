drop policy if exists "Profiles: ver próprio" on public.profiles;
drop policy if exists "Profiles: criar próprio" on public.profiles;
drop policy if exists "Profiles: atualizar próprio" on public.profiles;
drop policy if exists "Receitas: gerenciar próprias" on public.receitas;
drop policy if exists "Medicamentos: gerenciar próprios" on public.medicamentos;
drop policy if exists "Lembretes: gerenciar próprios" on public.lembretes;

create policy "Profiles: select" on public.profiles
  for select using (auth.uid() = id);

create policy "Profiles: insert" on public.profiles
  for insert with check (auth.uid() = id);

create policy "Profiles: update" on public.profiles
  for update using (auth.uid() = id);

create policy "Profiles: delete" on public.profiles
  for delete using (auth.uid() = id);

create policy "Receitas: all" on public.receitas
  for all using (auth.uid() = usuario_id)
  with check (auth.uid() = usuario_id);

create policy "Medicamentos: all" on public.medicamentos
  for all using (auth.uid() = usuario_id)
  with check (auth.uid() = usuario_id);

create policy "Lembretes: all" on public.lembretes
  for all using (auth.uid() = usuario_id)
  with check (auth.uid() = usuario_id);

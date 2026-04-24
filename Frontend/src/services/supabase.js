import { createClient } from '@supabase/supabase-js'

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)

// ─── Auth ────────────────────────────────────────────────────────────────────

/** Gera ou recupera um UUID persistente no localStorage (fallback quando auth anonima esta desabilitada) */
const getLocalUserId = () => {
  let id = localStorage.getItem('app_device_id')
  if (!id) {
    id = crypto.randomUUID ? crypto.randomUUID() : `user-${Date.now()}`
    localStorage.setItem('app_device_id', id)
  }
  return id
}

/** Inicia sessão anônima se o usuário não tiver uma. Usa localStorage UUID como fallback. */
export const ensureSession = async () => {
  try {
    const { data: { session } } = await supabase.auth.getSession()
    if (session) return session
    const { data, error } = await supabase.auth.signInAnonymously()
    if (error) throw error
    return data.session
  } catch (err) {
    // Fallback: usa UUID do localStorage como identificador do dispositivo
    console.warn('Supabase anon auth unavailable, using local UUID:', err.message)
    return null
  }
}

/** Retorna o ID do usuário atual (Supabase auth ou UUID local) */
export const getUserId = async () => {
  const { data: { user } } = await supabase.auth.getUser()
  if (user?.id) return user.id
  return getLocalUserId()
}

/** Encerra a sessão atual e apaga o device ID para começar um novo paciente zerado */
export const signOutSession = async () => {
  localStorage.removeItem('app_device_id');
  await supabase.auth.signOut();
}

// ─── Perfil ──────────────────────────────────────────────────────────────────

/** Busca o perfil do usuário atual */
export const getProfile = async () => {
  const userId = await getUserId()
  if (!userId) return null

  const { data, error } = await supabase
    .from('profiles')
    .select('*')
    .eq('id', userId)
    .maybeSingle()

  if (error) console.error('getProfile:', error)
  return data || null
}

/** Cria ou atualiza o perfil do usuário */
export const saveProfile = async (profileData) => {
  const userId = await getUserId()
  if (!userId) return null

  const { data, error } = await supabase
    .from('profiles')
    .upsert({ id: userId, ...profileData, updated_at: new Date().toISOString() })
    .select()
    .single()

  if (error) { console.error('saveProfile:', error); throw error }
  return data
}

// ─── Receitas ─────────────────────────────────────────────────────────────────

/** Salva uma receita extraída com seus medicamentos */
export const saveReceita = async ({ textoExtraido, medicos = [], medicamentos = [] }) => {
  const userId = await getUserId()
  if (!userId) return null

  // Salva a receita
  const { data: receita, error: rErr } = await supabase
    .from('receitas')
    .insert({ usuario_id: userId, texto_extraido: textoExtraido, data_receita: new Date().toISOString() })
    .select()
    .single()

  if (rErr) throw new Error(`Receita falhou: ${rErr.message}`);

  // Salva os medicamentos associados
  if (medicamentos.length > 0) {
    const meds = medicamentos.map(m => ({
      receita_id: receita.id,
      usuario_id: userId,
      nome: m.name || m.nome,
      dosagem: m.dosage || m.dosagem,
      frequencia: m.frequencia || '',
    }))
    const { error: medErr } = await supabase.from('medicamentos').insert(meds)
    if (medErr) throw new Error(`Medicamentos falhou: ${medErr.message}`);
  }

  return receita
}

// ─── Lembretes ────────────────────────────────────────────────────────────────

/** Salva uma lista de lembretes no Supabase e retorna os registros com IDs */
export const saveLembretes = async (reminders) => {
  const userId = await getUserId()
  if (!userId || !reminders?.length) return []

  const rows = reminders.map(r => {
    // Evita falsy silencioso: se vier "", passa a ser '--:--'
    let timeVal = r.time || r.horario || '--:--'
    if (timeVal.trim() === '') timeVal = '--:--'

    return {
      usuario_id: userId,
      nome: r.name || r.nome || 'Medicamento',
      dosagem: r.dosage || r.dosagem || '-',
      horario: timeVal,
      status: r.status || 'pendente',

      data_inicio: r.data_inicio,
      duracao_dias: r.duracao_dias || 7
    }
  })

  const { data, error } = await supabase.from('lembretes').insert(rows).select()
  if (error) {
    throw new Error(`Lembretes falhou: ${error.message}`);
  }
  return data || []
}

/** Exclui todos os lembretes do usuário atual */
export const deleteAllLembretes = async () => {
  const userId = await getUserId()
  if (!userId) return

  const { error } = await supabase
    .from('lembretes')
    .delete()
    .eq('usuario_id', userId)

  if (error) {
    console.error('deleteAllLembretes:', error)
    throw error
  }
}

/** Busca todos os lembretes do usuário */
export const getLembretes = async () => {
  const userId = await getUserId()
  if (!userId) return []

  const { data, error } = await supabase
    .from('lembretes')
    .select('*')
    .eq('usuario_id', userId)
    .order('horario')

  if (error) { console.error('getLembretes:', error); return [] }
  return data || []
}

/** Atualiza o status de um lembrete */
export const updateLembreteStatus = async (id, status) => {
  const { error } = await supabase
    .from('lembretes')
    .update({ status })
    .eq('id', id)
  if (error) console.error('updateLembreteStatus:', error)
}

// ─── Email Auth ───────────────────────────────────────────────────────────────

/**
 * Retorna o estado de autenticação do usuário atual:
 * - 'anonymous': usuário anônimo (sem email)
 * - 'email': usuário com email confirmado
 * - 'none': sem sessão
 */
export const getAuthState = async () => {
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return 'none'
  if (user.is_anonymous) return 'anonymous'
  return 'email'
}

/**
 * Vincula um email à conta anônima atual.
 * Supabase envia um link de confirmação para o email.
 * Após confirmado, a conta anônima vira uma conta permanente com email.
 */
export const linkEmailToAccount = async (email) => {
  const { error } = await supabase.auth.updateUser({ email })
  if (error) throw error
}

/**
 * Envia um OTP (magic link) para o email.
 * Usado quando o usuário quer entrar em um novo dispositivo com email existente.
 */
export const signInWithEmail = async (email) => {
  const { error } = await supabase.auth.signInWithOtp({
    email,
    options: { shouldCreateUser: false }
  })
  if (error) throw error
}

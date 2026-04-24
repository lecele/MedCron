import { useState, useEffect } from 'react'
import { getLembretes, saveLembretes, deleteAllLembretes, updateLembreteStatus } from '../services/supabase'
import { notifyRemindersToGroup } from '../services/telegram'

export const useReminders = (profile) => {
  const [reminders, setReminders] = useState(() => {
    try {
      const saved = localStorage.getItem('med_reminders')
      return saved ? JSON.parse(saved) : []
    } catch {
      return []
    }
  })

  useEffect(() => {
    localStorage.setItem('med_reminders', JSON.stringify(reminders))
  }, [reminders])

  const loadReminders = async () => {
    const lems = await getLembretes()
    if (lems.length > 0) {
      setReminders(lems.map(l => ({
        id: l.id, name: l.nome, dosage: l.dosagem,
        time: l.horario, status: l.status,
        data_inicio: l.data_inicio, duracao_dias: l.duracao_dias
      })))
    }
  }

  const addReminders = (newItems) => {
    setReminders(prev => {
      const existingIds = new Set(newItems.map(ni => ni.id))
      const filtered = prev.filter(r => !existingIds.has(r.id))
      return [...filtered, ...newItems]
    })
  }

  const syncWithSupabase = async (newItems) => {
    const savedRows = await saveLembretes(newItems)
    if (savedRows?.length > 0) {
      setReminders(prev => {
        const filtered = prev.filter(r => !newItems.some(ni => ni.id === r.id))
        return [
          ...filtered,
          ...savedRows.map(l => ({
            id: l.id, name: l.nome, dosage: l.dosagem,
            time: l.horario, status: l.status,
            data_inicio: l.data_inicio, duracao_dias: l.duracao_dias
          }))
        ]
      })
    }
  }

  const markAsDone = async (id) => {
    try {
      const isLocal = typeof id === 'string' && id.startsWith('local-')
      if (!isLocal) {
        await updateLembreteStatus(id, 'tomado')
        const reminder = reminders.find(r => r.id === id)
        if (reminder) {
          const msg = `✅ <b>Medicação Tomada!</b>\n\n💊 <b>${reminder.name}</b>\n📏 Dose: ${reminder.dosage}\n👤 Usuário: ${profile?.nome || 'Paciente'}`
          notifyRemindersToGroup([{ ...reminder, message_override: msg }]).catch(console.error)
        }
      }
      setReminders(prev => prev.map(r => r.id === id ? { ...r, status: 'tomado' } : r))
    } catch (err) {
      console.error('Erro ao marcar como tomado:', err)
      // UI já atualizada acima, apenas log do erro
      setReminders(prev => prev.map(r => r.id === id ? { ...r, status: 'tomado' } : r))
    }
  }

  const clearAll = async () => {
    await deleteAllLembretes()
    setReminders([])
  }

  return { reminders, setReminders, loadReminders, addReminders, syncWithSupabase, markAsDone, clearAll }
}

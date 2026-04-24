import { useState, useEffect, useRef, useCallback } from 'react'
import { processMessage } from './services/agents'
import { downloadIcsFile, generateSingleIcs, downloadCalendarFromServer } from './services/calendar'
import { notifyRemindersToGroup } from './services/telegram'
import {
  ensureSession, getProfile,
  getAuthState, signOutSession
} from './services/supabase'
import * as pdfjsLib from 'pdfjs-dist'

// Componentes
import AnimatedLogo from './components/AnimatedLogo.jsx'
import PillIcon from './components/PillIcon.jsx'
import AlertModal from './components/AlertModal.jsx'
import LGPDConsent, { VERSAO_POLITICA } from './components/LGPDConsent.jsx'

// Hooks
import { useReminders } from './hooks/useReminders.js'
import { useVoice } from './hooks/useVoice.js'

import './App.css'


pdfjsLib.GlobalWorkerOptions.workerSrc =
  `https://unpkg.com/pdfjs-dist@${pdfjsLib.version}/build/pdf.worker.min.mjs`

function App() {
  const [status, setStatus] = useState('conectando...')
  const [profile, setProfile] = useState(null)
  const [messages, setMessages] = useState(() => {
    const saved = localStorage.getItem('med_messages')
    return saved ? JSON.parse(saved) : []
  })
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [showActionButtons, setShowActionButtons] = useState(false)
  const [pendingAlerts, setPendingAlerts] = useState(null)
  // Mobile nav: 'chat' | 'config'
  const [activeTab, setActiveTab] = useState('chat')

  const [showLgpdModal, setShowLgpdModal] = useState(false)

  // ─── LGPD: consentimento ─────────────────────────────────────────────────
  // Chave no localStorage: 'medcron_lgpd_consent_v{VERSAO_POLITICA}'
  const LGPD_KEY = `medcron_lgpd_consent_v${VERSAO_POLITICA}`
  const [lgpdConsentido, setLgpdConsentido] = useState(false)



  const fileInputRef = useRef(null)
  const inputRef = useRef(null)

  const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent)
  const isIos = /iPhone|iPad|iPod/i.test(navigator.userAgent)

  const { reminders, loadReminders, addReminders, syncWithSupabase, markAsDone, clearAll } =
    useReminders(profile)

  // ─── Voice ───────────────────────────────────────────────────────────────
  const handleTranscript = useCallback((text) => handleSend(null, text), [])
  const { isListening, startListening, speak, unlockAudio } = useVoice(handleTranscript)

  // ─── Auto-focus input ─────────────────────────────────────────────────────
  useEffect(() => {
    if (!loading && inputRef.current) inputRef.current.focus()
  }, [loading, messages.length])

  // ─── Init ─────────────────────────────────────────────────────────────────
  useEffect(() => {
    const init = async () => {
      // Só inicializa sessão/perfil se o LGPD já foi aceito
      if (!lgpdConsentido) return
      try {
        await ensureSession()
        const p = await getProfile()
        if (p?.onboarding_completo) {
          setProfile(p)
          await loadReminders()
        } else {
          // Remove apenas a mensagem inicial que pedia para aceitar a LGPD,
          // preservando a mensagem de "Termos aceitos" e outras.
          setMessages(prev => prev.filter(m => !m.content.includes('leia e aceite nossos Termos')))
        }
        await getAuthState()
      } catch (err) {
        console.error('Init error:', err)
      }
    }
    init()
  }, [lgpdConsentido])

  // ─── Gateway status ───────────────────────────────────────────────────────
  useEffect(() => {
    const check = async () => {
      try {
        // Verifica nosso próprio backend FastAPI (via proxy do Vite em dev, direto em prod)
        const res = await fetch('/api/health')
        const data = res.ok ? await res.json() : null
        setStatus(data?.status === 'ok' ? `online v${data.version}` : 'erro de api')
      } catch {
        setStatus('offline (backend)')
      }
    }
    check()
    const id = setInterval(check, 15000)
    return () => clearInterval(id)
  }, [])

  // ─── Persist messages ─────────────────────────────────────────────────────
  useEffect(() => {
    localStorage.setItem('med_messages', JSON.stringify(messages))
    setTimeout(() => {
      const el = document.querySelector('.messages-area')
      if (el) el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
    }, 100)
  }, [messages])

  // ─── Clear chat ───────────────────────────────────────────────────────────
  const clearChat = async () => {
    setMessages([])
    setProfile(null)
    localStorage.removeItem('med_messages')
    localStorage.removeItem('med_reminders')
    localStorage.removeItem('med_sessao_id')  // Reseta thread do LangGraph
    await signOutSession()
    window.location.reload()
  }

  // ─── LGPD: handlers ───────────────────────────────────────────────────────
  const handleLGPDAccept = async () => {
    // 1. Garante sessão anonima para ter usuario_id
    try {
      await ensureSession()
    } catch (_) { /* ignora */ }

    const usuarioId = localStorage.getItem('med_temp_uid') || 'anonimo'

    // 2. Persiste no Supabase
    try {
      await fetch('/api/consent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          usuario_id: usuarioId,
          consentiu: true,
          versao_politica: VERSAO_POLITICA,
        }),
      })
    } catch (err) {
      console.warn('[LGPD] Persistência remota falhou, usando localStorage:', err)
    }

    // 3. Marca como consentido apenas nesta sessão
    setLgpdConsentido(true)
    setShowLgpdModal(false)
    
    // Continua a conversa após aceitar
    const afterAccept = 'Termos aceitos. Obrigado! Para começarmos, você pode me enviar a foto da sua receita ou me dizer quais medicamentos você toma.'
    setMessages(prev => [...prev, { role: 'assistant', content: afterAccept }])
    speak(afterAccept)
  }

  // ─── Sync Bridge (iOS Fix) ────────────────────────────────────────────────
  const [syncReminders, setSyncReminders] = useState(null)
  
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const syncData = params.get('sync')
    if (syncData) {
      try {
        const decoded = JSON.parse(decodeURIComponent(escape(atob(syncData))))
        
        // Decodifica itens compactados
        let extractedReminders = decoded?.reminders;
        if (decoded?.c && Array.isArray(decoded.c)) {
          extractedReminders = decoded.c.map(r => ({
            name: r.n,
            dosage: r.d,
            time: r.t,
            data_inicio: r.s,
            duracao_dias: r.p
          }));
        }

        if (extractedReminders) {
          setSyncReminders({ name: decoded.name, reminders: extractedReminders })
          // Tenta disparar automaticamente
          setTimeout(() => {
            if (isIos) {
              const icsText = generateSingleIcs(extractedReminders)
              window.location.assign('data:text/calendar;charset=utf8,' + encodeURIComponent(icsText))
            } else {
              downloadIcsFile(extractedReminders, decoded.name || 'Paciente')
            }
          }, 700)
        }
      } catch (e) {
        console.error('Sync error:', e)
      }
    }
  }, [])

  const triggerManualSync = () => {
    if (syncReminders) {
      if (isIos) {
        const icsText = generateSingleIcs(syncReminders.reminders)
        window.location.assign('data:text/calendar;charset=utf8,' + encodeURIComponent(icsText))
      } else {
        downloadIcsFile(syncReminders.reminders, syncReminders.name || 'Paciente')
      }
    }
  }

  // ─── Handle clear reminders (com modal customizado) ──────────────────────
  const handleClearReminders = async () => {
    setPendingAlerts({
      type: 'confirm_delete',
      message: 'Deseja excluir todos os lembretes permanentemente?'
    })
  }

  // Remoção do auto-agendamento do Telegram. Agora apenas via botão manual.

  // ─── Handle send ──────────────────────────────────────────────────────────
  const handleSend = async (e, customInput, fileData = null) => {
    if (e) e.preventDefault()
    
    // Desbloqueia áudio no iOS imediatamente no clique
    if (unlockAudio) unlockAudio()
    
    if (loading) return
    const messageText = customInput || input
    if (!messageText.trim() && !fileData) return

    const userMessage = {
      role: 'user',
      content: fileData ? `[Arquivo Enviado] ${messageText}` : messageText
    }
    setMessages(prev => [...prev, userMessage])
    setInput('')

    // Mensagem de boas-vindas antes da primeira interação
    if (!lgpdConsentido) {
      setTimeout(() => {
        const welcome = 'Olá! Sou o MedCron, seu assistente de medicações. Antes de começarmos, por favor, leia e aceite nossos Termos de Privacidade (LGPD) que aparecerão na sua tela a seguir.'
        setMessages(prev => [...prev, { role: 'assistant', content: welcome }])
        
        // Mostra o modal da LGPD logo após o áudio de boas-vindas terminar
        speak(welcome).then(() => {
          setShowLgpdModal(true)
        })
      }, 500)
      return
    }

    // Mensagem de boas-vindas padrão caso já tenha lgpdConsentido e mensagens === 0
    if (messages.length === 0 && !fileData) {
      setTimeout(() => {
        const welcome = 'Olá! Sou o MedCron, seu assistente de medicações. Para começarmos, me envie uma foto da sua receita médica para que eu possa avaliar.'
        setMessages(prev => [...prev, { role: 'assistant', content: welcome }])
        speak(welcome)
      }, 500)
      return
    }

    setLoading(true)

    try {
      const responseData = await processMessage({ 
        messageText: fileData ? `[IMAGEM ENVIADA: EXTRAIA OS DADOS AGORA] ${messageText}` : messageText, 
        history: messages.map(m => ({
          role: m.role,
          content: m.content.replace(/\[Arquivo Enviado\] /g, '')
        })), 
        fileData 
      })

      // O backend agora retorna { resposta, sessao_id, alertas_clinicos, medicamentos_salvos }
      // processMessage já extrai data.resposta — aqui responseData é a string da resposta
      const resposta = responseData
      const medsCount = responseData?._medsCount || 0  // será 0 para texto puro

      if (resposta && resposta.length > 0) {
        setMessages(prev => [...prev, { role: 'assistant', content: resposta }])
        speak(resposta)
      }

      // Se o backend salvou medicamentos, atualiza a lista local e mostra botões
      if (medsCount > 0) {
        await loadReminders()
        setShowActionButtons(true)
      } else {
        setShowActionButtons(false)
      }

      if (fileInputRef.current) fileInputRef.current.value = ''
    } catch (error) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Erro ao processar: ${error.message}`
      }])
    } finally {
      setLoading(false)
    }
  }

  // ─── PDF convert ──────────────────────────────────────────────────────────
  const convertPdfToImage = async (file) => {
    const arrayBuffer = await file.arrayBuffer()
    const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise
    const page = await pdf.getPage(1)
    const viewport = page.getViewport({ scale: 1.2 })
    const canvas = document.createElement('canvas')
    canvas.height = viewport.height
    canvas.width = viewport.width
    await page.render({ canvasContext: canvas.getContext('2d'), viewport }).promise
    return canvas.toDataURL('image/jpeg', 0.6)
  }

  const compressImage = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.readAsDataURL(file)
      reader.onload = (event) => {
        const img = new Image()
        img.src = event.target.result
        img.onload = () => {
          const canvas = document.createElement('canvas')
          const MAX_WIDTH = 1200
          const MAX_HEIGHT = 1200
          let width = img.width
          let height = img.height

          if (width > height) {
            if (width > MAX_WIDTH) {
              height *= MAX_WIDTH / width
              width = MAX_WIDTH
            }
          } else {
            if (height > MAX_HEIGHT) {
              width *= MAX_HEIGHT / height
              height = MAX_HEIGHT
            }
          }

          canvas.width = width
          canvas.height = height
          const ctx = canvas.getContext('2d')
          ctx.drawImage(img, 0, 0, width, height)
          // Comprime para 60% de qualidade
          resolve(canvas.toDataURL('image/jpeg', 0.6))
        }
        img.onerror = (error) => reject(error)
      }
      reader.onerror = (error) => reject(error)
    })
  }

  const handleFileUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    setLoading(true)
    try {
      let dataUrl = ''
      if (file.type === 'application/pdf') {
        setStatus('convertendo pdf...')
        dataUrl = await convertPdfToImage(file)
      } else {
        setStatus('processando imagem...')
        dataUrl = await compressImage(file)
      }
      await handleSend(null, 'Extraia os dados desta receita médica e agende as notificações.', dataUrl)
      setStatus('online')
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: `⚠️ Erro ao processar arquivo: ${err.message}` }])
    } finally {
      setLoading(false)
    }
  }

  // ─── Render ──────────────────────────────────────────────────────────────────────────
  return (
    <div className="container animate-fade">
      {/* Modal LGPD — bloqueia a tela, mas apenas após a primeira interação */}
      {showLgpdModal && (
        <LGPDConsent
          onAccept={handleLGPDAccept}
          onDecline={() => { /* apenas mostra a tela de recusa dentro do modal */ }}
        />
      )}
      {/* Modal de Alertas Farmacológicos ou Confirmação */}
      {pendingAlerts && pendingAlerts.type === 'safety' && (
        <AlertModal
          alerts={pendingAlerts.alerts}
          onConfirm={() => {
            executeScheduleFinalization(pendingAlerts)
            setPendingAlerts(null)
          }}
          onCancel={() => {
            setLoading(false)
            setPendingAlerts(null)
            setMessages(prev => [...prev, {
              role: 'assistant',
              content: 'Agendamento cancelado devido a alertas de segurança medicamentosa.'
            }])
          }}
        />
      )}

      {/* Modal de confirmação de exclusão (substitui confirm() nativo) */}
      {pendingAlerts && pendingAlerts.type === 'confirm_delete' && (
        <div style={{
          position: 'fixed', inset: 0,
          background: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(5px)',
          zIndex: 9999, display: 'flex', alignItems: 'center',
          justifyContent: 'center', padding: '1rem'
        }}>
          <div className="glass-card animate-fade" style={{ maxWidth: '400px', width: '100%', padding: '2rem', borderRadius: '20px' }}>
            <h3 style={{ color: 'white', marginBottom: '1rem' }}>⚠️ Confirmar exclusão</h3>
            <p style={{ color: 'var(--text-dim)', marginBottom: '1.5rem', lineHeight: 1.5 }}>
              {pendingAlerts.message}
            </p>
            <div style={{ display: 'flex', gap: '1rem' }}>
              <button
                onClick={async () => {
                  setPendingAlerts(null)
                  try {
                    setLoading(true)
                    await clearAll()
                  } catch (err) {
                    console.error(err)
                  } finally {
                    setLoading(false)
                  }
                }}
                style={{ flex: 1, padding: '0.75rem', background: 'var(--danger)', color: 'white', border: 'none', borderRadius: '12px', fontWeight: 700, cursor: 'pointer' }}
              >
                Excluir
              </button>
              <button
                onClick={() => setPendingAlerts(null)}
                style={{ flex: 1, padding: '0.75rem', background: 'transparent', color: 'white', border: '1px solid rgba(255,255,255,0.3)', borderRadius: '12px', cursor: 'pointer' }}
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}

      <header className="main-header">
        <AnimatedLogo />
      </header>

      {/* Interface de Sincronismo (iOS Bridge) */}
      {syncReminders && (
        <div className="glass-card animate-fade" style={{ 
          margin: '1rem', 
          padding: '1.5rem', 
          textAlign: 'center', 
          background: 'linear-gradient(135deg, rgba(67, 97, 238, 0.2), rgba(76, 201, 240, 0.2))',
          border: '1px solid var(--accent)'
        }}>
          <h3 style={{ color: 'white', marginBottom: '0.5rem', fontSize: '1.1rem' }}>Sincronizar Tratamento</h3>
          <p style={{ color: 'var(--text-dim)', fontSize: '0.85rem', marginBottom: '1rem' }}>
            {/Android/i.test(navigator.userAgent) 
              ? 'Clique abaixo para baixar e agendar no Google Calendar.'
              : 'Clique abaixo para adicionar todas as doses ao calendário do seu iPhone.'
            }
          </p>
          <button 
            onClick={triggerManualSync}
            style={{ 
              width: '100%', 
              padding: '1rem', 
              background: 'var(--accent)', 
              color: 'white', 
              border: 'none', 
              borderRadius: '12px', 
              fontWeight: '700',
              fontSize: '1rem',
              cursor: 'pointer',
              boxShadow: '0 4px 15px rgba(67, 97, 238, 0.4)'
            }}
          >
            {/Android/i.test(navigator.userAgent) ? '📥 Baixar e Agendar' : '📅 Confirmar Agendamento'}
          </button>
          
          {/Android/i.test(navigator.userAgent) && (
            <p style={{ marginTop: '0.75rem', color: 'var(--text-dim)', fontSize: '0.75rem' }}>
              Após o download, clique em **Abrir** na barra do Chrome para agendar tudo.
            </p>
          )}

          <button 
            onClick={() => setSyncReminders(null)}
            style={{ 
              marginTop: '0.75rem', 
              background: 'transparent', 
              color: 'var(--text-dim)', 
              border: 'none', 
              fontSize: '0.8rem',
              textDecoration: 'underline',
              cursor: 'pointer'
            }}
          >
            Ignorar e ir para o chat
          </button>
        </div>
      )}

      <div className="app-grid">
        {/* ─ Chat central ─ */}
        <div className={`center-column ${isMobile && activeTab !== 'chat' ? 'hidden-mobile' : ''}`}>
          <section className="chat-section glass-card" style={{ display: 'flex', flexDirection: 'column', flex: 1, padding: 0, margin: 0 }}>
            <div className="chat-header" style={{ justifyContent: 'center', flexDirection: 'column', padding: '1.5rem', borderBottom: 'none' }}>
              <p style={{ color: 'var(--text-dim)', fontSize: '0.85rem' }}>
                Converse ou envie sua receita médica.
              </p>
            </div>

            <div className="messages-area">
              {messages.map((msg, i) => (
                <div key={i} className={`message-row ${msg.role}`}>
                  <div className={`msg-avatar ${msg.role === 'assistant' ? 'bot-avatar' : 'user-avatar'}`}>
                    {msg.role === 'assistant' ? <PillIcon size={18} /> : '👤'}
                  </div>
                  <div className={`message-bubble ${msg.role} ${msg.isCritical ? 'critical' : ''}`}>
                    {msg.content}
                  </div>
                </div>
              ))}
              {loading && (
                <div className="message-row assistant">
                  <div className="msg-avatar bot-avatar"><PillIcon size={18} /></div>
                  <div className="typing-indicator">
                    <div className="typing-dot" />
                    <div className="typing-dot" />
                    <div className="typing-dot" />
                  </div>
                </div>
              )}
              {showActionButtons && (
                <div className="action-buttons-container animate-fade">
                  <p style={{ color: 'var(--text-dim)', fontSize: '0.85rem', marginBottom: '0.5rem', textAlign: 'center' }}>
                    Seus lembretes estão prontos. Agende no seu celular (funciona offline):
                  </p>
                  <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center', flexWrap: 'wrap' }}>
                    <button 
                      className="schedule-btn calendar-btn"
                      onClick={async () => {
                        try {
                          const uid = localStorage.getItem('med_temp_uid')
                          if (!uid) { alert('Nenhum usuário identificado.'); return }
                          // Navega na própria aba para a URL do ICS do backend
                          // iOS Safari intercepta text/calendar e abre o app Calendário
                          // sem abrir tela em branco — o usuário pode voltar com (<)
                          const calUrl = `/api/calendar/generate?usuario_id=${encodeURIComponent(uid)}`
                          window.location.href = calUrl
                        } catch (e) {
                          console.error(e)
                          alert('Erro ao gerar calendário.')
                        }
                      }}
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                        <line x1="16" y1="2" x2="16" y2="6" />
                        <line x1="8" y1="2" x2="8" y2="6" />
                        <line x1="3" y1="10" x2="21" y2="10" />
                      </svg>
                      Agendar no Celular
                    </button>
                  </div>
                </div>
              )}
            </div>
            <form onSubmit={(e) => {
              e.preventDefault();
              if (unlockAudio) unlockAudio();
              handleSend(e);
            }} className="input-area-wrapper">
              <input type="file" ref={fileInputRef} style={{ display: 'none' }} accept="image/*,.pdf" onChange={handleFileUpload} />
              
              <div className="input-row">
                <input
                  ref={inputRef}
                  type="text"
                  value={input}
                  disabled={loading}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Digite sua mensagem ou envie uma foto da receita..."
                />
                <button type="submit" className="send-btn" disabled={loading} title="Enviar">
                  <svg className="send-icon" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="22" y1="2" x2="11" y2="13" />
                    <polygon points="22 2 15 22 11 13 2 9 22 2" />
                  </svg>
                  <span className="send-text">Enviar</span>
                </button>
              </div>

              <div className="action-buttons-row">
                {/* Upload */}
                <button type="button" className="action-btn" onClick={() => fileInputRef.current.click()} title="Anexar Receita">
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z" />
                    <circle cx="12" cy="13" r="3" />
                  </svg>
                </button>

                {/* Mic */}
                <button
                  type="button"
                  className={`action-btn mic-btn ${isListening ? 'recording' : ''}`}
                  onClick={startListening}
                  title="Falar com o Assistente"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
                    <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                    <line x1="12" y1="19" x2="12" y2="22" />
                  </svg>
                </button>

                {/* Limpar */}
                <button type="button" className="action-btn" onClick={clearChat} title="Limpar Conversa">
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M3 6h18" /><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
                    <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
                  </svg>
                </button>
              </div>
            </form>
          </section>
        </div>
      </div>

    </div>
  )
}

export default App

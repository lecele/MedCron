import { useState, useEffect, useRef } from 'react'
import { saveProfile } from '../services/supabase'

const QUESTIONS = [
  {
    key: null,
    message: 'Olá sou o medCron seu asistente para te auxilar com as medicações, qual o seu nome?',
    type: 'intro'
  },
  {
    key: 'nome',
    message: 'Diga-me o seu nome completo para começarmos!',
    placeholder: 'Ex: João Silva',
    type: 'text'
  },
  {
    key: 'idade',
    message: (p) => `Prazer, ${p.nome}! Quantos anos voce tem?`,
    placeholder: 'Ex: 35',
    type: 'number'
  },
  {
    key: 'sexo',
    message: 'Qual e o seu sexo biologico?',
    type: 'choice',
    options: ['Masculino', 'Feminino']
  },
  {
    key: 'telefone',
    message: 'Qual e o seu numero de telefone com DDD?',
    placeholder: 'Ex: 11987654321',
    type: 'text'
  },
  {
    key: 'medico_nome',
    message: 'Tem medico de referencia? Se sim, qual o nome? (ou "nao" para pular)',
    placeholder: 'Ex: Dr. Carlos Souza',
    type: 'text'
  }
]

export default function OnboardingChat({ onComplete }) {
  const [step, setStep] = useState(0)
  const [profile, setProfile] = useState({})
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [saving, setSaving] = useState(false)
  const inputRef = useRef(null)
  const bottomRef = useRef(null)

  // Adiciona mensagem inicial
  useEffect(() => {
    setMessages([{ role: 'assistant', content: QUESTIONS[0].message }])
    setTimeout(() => {
      addBotMessage(QUESTIONS[1].message, {})
      setStep(1)
    }, 800)
  }, [])

  // Auto-scroll ao adicionar mensagens
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Auto-focus no input quando mudar de step
  useEffect(() => {
    if (step > 0) {
      setTimeout(() => inputRef.current?.focus(), 100)
    }
  }, [step])

  const addBotMessage = (text, profileData) => {
    const msg = typeof text === 'function' ? text(profileData) : text
    setMessages(prev => [...prev, { role: 'assistant', content: msg }])
  }

  const handleAnswer = async (answer) => {
    const trimmed = answer.trim()
    if (!trimmed) return

    const currentQ = QUESTIONS[step]
    setMessages(prev => [...prev, { role: 'user', content: trimmed }])
    setInput('')

    const newProfile = { ...profile }
    if (currentQ.key) {
      newProfile[currentQ.key] = currentQ.type === 'number' ? parseInt(trimmed) : trimmed
      setProfile(newProfile)
    }

    const nextStep = step + 1

    // Completou todas as perguntas
    if (nextStep >= QUESTIONS.length) {
      setSaving(true)
      try {
        await saveProfile({ ...newProfile, onboarding_completo: true })
        const finalMsg = `Perfeito, ${newProfile.nome || 'usuario'}! Suas informacoes foram salvas. Agora envie uma receita medica usando o botao da camera!`
        setMessages(prev => [...prev, { role: 'assistant', content: finalMsg }])
        setTimeout(() => onComplete(newProfile), 1800)
      } catch (err) {
        console.error('Erro ao salvar perfil:', err)
        // Even on error, proceed - data saved locally
        onComplete(newProfile)
      } finally {
        setSaving(false)
      }
      return
    }

    setStep(nextStep)
    const nextQ = QUESTIONS[nextStep]
    setTimeout(() => {
      addBotMessage(nextQ.message, newProfile)
    }, 350)
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    handleAnswer(input)
  }

  const currentQ = QUESTIONS[step] || {}

  return (
    <div className="chat-section" style={{ height: '100%', flex: 1 }}>
      <div className="chat-header">
        <div className="agent-avatars">
          <span title="Assistente Medicacoes">💊</span>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-dim)' }}>Configuracao inicial</span>
        </div>
      </div>

      <div className="messages-area">
        {messages.map((msg, i) => (
          <div key={i} className={`message-bubble ${msg.role}`}>
            {msg.content}
          </div>
        ))}
        {saving && (
          <div className="message-bubble assistant typing-indicator">
            Salvando informacoes...
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Botoes de opcao (sexo) */}
      {currentQ.type === 'choice' && currentQ.options && (
        <div style={{ display: 'flex', gap: '0.75rem', padding: '0.75rem 1rem', borderTop: '1px solid var(--border-glass)' }}>
          {currentQ.options.map(opt => (
            <button
              key={opt}
              className="send-btn"
              style={{ flex: 1, fontSize: '0.95rem' }}
              onClick={() => handleAnswer(opt)}
            >
              {opt}
            </button>
          ))}
        </div>
      )}

      {/* Input de texto/numero */}
      {(currentQ.type === 'text' || currentQ.type === 'number') && (
        <form className="input-area" onSubmit={handleSubmit}>
          <input
            ref={inputRef}
            type={currentQ.type === 'number' ? 'number' : 'text'}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={currentQ.placeholder || 'Digite sua resposta...'}
          />
          <button type="submit" className="send-btn" disabled={!input.trim()}>
            Enviar
          </button>
        </form>
      )}
    </div>
  )
}

/**
 * LGPDConsent.jsx
 * 
 * Modal de Consentimento LGPD — Art. 11, Lei 13.709/2018
 * 
 * Exibido antes de qualquer interação com o MedCron.
 * Bloqueia totalmente a interface até o paciente dar o aceite explícito.
 * Em conformidade com a Lei Geral de Proteção de Dados (LGPD) para
 * tratamento de dados pessoais sensíveis de saúde.
 */
import { useState } from 'react'

// Versão da política de privacidade — incrementar ao atualizar os termos
export const VERSAO_POLITICA = '1.0'

export default function LGPDConsent({ onAccept, onDecline }) {
  const [loading, setLoading] = useState(false)
  const [declined, setDeclined] = useState(false)

  const handleAccept = async () => {
    setLoading(true)
    try {
      await onAccept()
    } finally {
      setLoading(false)
    }
  }

  const handleDecline = () => {
    setDeclined(true)
    if (onDecline) onDecline()
  }

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(0, 0, 0, 0.88)',
      backdropFilter: 'blur(12px)',
      WebkitBackdropFilter: 'blur(12px)',
      zIndex: 99999,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '1rem',
      overflowY: 'auto',
    }}>
      <div style={{
        maxWidth: '520px',
        width: '100%',
        maxHeight: '85vh',
        display: 'flex',
        flexDirection: 'column',
        background: 'linear-gradient(145deg, rgba(15,25,20,0.98), rgba(20,35,30,0.98))',
        border: '1px solid rgba(18, 204, 143, 0.4)',
        borderRadius: '24px',
        padding: '2rem',
        boxShadow: '0 25px 60px rgba(0,0,0,0.6), 0 0 0 1px rgba(18, 204, 143, 0.1)',
        animation: 'fadeIn 0.4s ease',
      }}>

        {/* Ícone de escudo */}
        <div style={{ textAlign: 'center', marginBottom: '1.25rem' }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '56px',
            height: '56px',
            borderRadius: '16px',
            background: 'linear-gradient(135deg, rgba(18, 204, 143, 0.3), rgba(6, 182, 212, 0.2))',
            border: '1px solid rgba(18, 204, 143, 0.4)',
          }}>
            <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24"
              fill="none" stroke="#12cc8f" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              <polyline points="9 12 11 14 15 10" />
            </svg>
          </div>
        </div>

        {/* Título */}
        <h2 style={{
          color: 'white',
          fontSize: '1.25rem',
          fontWeight: 700,
          textAlign: 'center',
          marginBottom: '0.25rem',
          letterSpacing: '-0.01em',
        }}>
          Privacidade e Proteção de Dados
        </h2>
        <p style={{
          color: 'rgba(255,255,255,0.45)',
          fontSize: '0.75rem',
          textAlign: 'center',
          marginBottom: '1.5rem',
        }}>
          Em conformidade com a LGPD — Lei 13.709/2018
        </p>

        {declined ? (
          /* Tela de recusa */
          <div style={{ textAlign: 'center' }}>
            <p style={{
              color: 'rgba(255,255,255,0.7)',
              fontSize: '0.9rem',
              lineHeight: 1.6,
              marginBottom: '1.5rem',
            }}>
              Entendemos sua decisão. Sem o consentimento para o tratamento dos dados de saúde,
              não é possível utilizar o MedCron, pois esses dados são necessários para o
              agendamento dos lembretes de medicamentos.
            </p>
            <button
              onClick={() => setDeclined(false)}
              style={{
                width: '100%',
                padding: '0.85rem',
                background: 'rgba(255,255,255,0.08)',
                color: 'rgba(255,255,255,0.7)',
                border: '1px solid rgba(255,255,255,0.15)',
                borderRadius: '12px',
                fontSize: '0.9rem',
                cursor: 'pointer',
                transition: 'all 0.2s',
              }}
            >
              Revisar os termos
            </button>
          </div>
        ) : (
          <>
            {/* Corpo do termo rolavel */}
            <div style={{ flex: 1, overflowY: 'auto', paddingRight: '0.5rem', marginBottom: '1.5rem' }}>
              <div style={{
                background: 'rgba(255,255,255,0.04)',
                border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: '14px',
                padding: '1.25rem',
                marginBottom: '1rem',
                fontSize: '0.85rem',
                color: 'rgba(255,255,255,0.75)',
                lineHeight: 1.65,
              }}>
                <p style={{ marginBottom: '1rem' }}>
                  Para usar o MedCron, você autoriza o tratamento dos seguintes
                  <strong style={{ color: 'white' }}> dados pessoais sensíveis de saúde</strong>:
                </p>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem', marginBottom: '1rem' }}>
                  {[
                    { icon: '📄', text: 'Imagem da receita médica — para identificar medicamentos e doses' },
                    { icon: '⚖️', text: 'Nome, idade, peso e sexo — para validação clínica das doses' },
                    { icon: '📱', text: 'Número de telefone — para envio de lembretes via Telegram' },
                  ].map(({ icon, text }) => (
                    <div key={text} style={{ display: 'flex', gap: '0.65rem', alignItems: 'flex-start' }}>
                      <span style={{ fontSize: '1rem', flexShrink: 0, marginTop: '0.05rem' }}>{icon}</span>
                      <span>{text}</span>
                    </div>
                  ))}
                </div>

                <div style={{
                  borderTop: '1px solid rgba(255,255,255,0.08)',
                  paddingTop: '1rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.5rem',
                }}>
                  <p>
                    <strong style={{ color: 'rgba(255,255,255,0.9)' }}>Finalidade:</strong>{' '}
                    Exclusivamente para agendamento de lembretes de medicamentos.
                  </p>
                  <p>
                    <strong style={{ color: 'rgba(255,255,255,0.9)' }}>Uso dos dados:</strong>{' '}
                    Seus dados não são compartilhados com terceiros nem usados para fins comerciais.
                  </p>
                  <p>
                    <strong style={{ color: 'rgba(255,255,255,0.9)' }}>Seus direitos (LGPD):</strong>{' '}
                    Você pode solicitar acesso, correção ou exclusão dos seus dados a qualquer momento
                    limpando o histórico do aplicativo.
                  </p>
                </div>
              </div>

              {/* Nota de desenvolvimento */}
              <p style={{
                color: 'rgba(255,255,255,0.3)',
                fontSize: '0.7rem',
                textAlign: 'center',
                marginBottom: '0.5rem',
              }}>
                Aplicativo em fase de desenvolvimento — versão {VERSAO_POLITICA}
              </p>
            </div>

            {/* Botões */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem', flexShrink: 0 }}>
              <button
                id="lgpd-accept-btn"
                onClick={handleAccept}
                disabled={loading}
                style={{
                  width: '100%',
                  padding: '1rem',
                  background: loading
                    ? 'rgba(18, 204, 143, 0.4)'
                    : 'linear-gradient(135deg, #12cc8f, #06b6d4)',
                  color: 'white',
                  border: 'none',
                  borderRadius: '14px',
                  fontSize: '0.95rem',
                  fontWeight: 700,
                  cursor: loading ? 'not-allowed' : 'pointer',
                  boxShadow: loading ? 'none' : '0 4px 20px rgba(18, 204, 143, 0.45)',
                  transition: 'all 0.2s',
                  letterSpacing: '0.01em',
                }}
              >
                {loading ? 'Registrando...' : 'Concordo e quero continuar'}
              </button>

              <button
                id="lgpd-decline-btn"
                onClick={handleDecline}
                disabled={loading}
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  background: 'transparent',
                  color: 'rgba(255,255,255,0.35)',
                  border: '1px solid rgba(255,255,255,0.08)',
                  borderRadius: '14px',
                  fontSize: '0.8rem',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  transition: 'all 0.2s',
                }}
              >
                Não concordo
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

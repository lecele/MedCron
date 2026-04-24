import { useState, useCallback, useEffect } from 'react'

let availableVoices = []
if (typeof window !== 'undefined' && window.speechSynthesis) {
  window.speechSynthesis.onvoiceschanged = () => {
    availableVoices = window.speechSynthesis.getVoices()
  }
}

const unlockAudio = () => {
  // Desbloqueia o SpeechSynthesis nativo silenciosamente
  if (typeof window !== 'undefined' && window.speechSynthesis) {
    const unlockUtterance = new SpeechSynthesisUtterance('');
    unlockUtterance.volume = 0;
    window.speechSynthesis.speak(unlockUtterance);
  }
}

// Escuta o PRIMEIRO toque real na tela para liberar o áudio
if (typeof document !== 'undefined') {
  const setupUnlock = () => {
    unlockAudio();
    document.removeEventListener('touchstart', setupUnlock);
    document.removeEventListener('touchend', setupUnlock);
    document.removeEventListener('click', setupUnlock);
  };
  document.addEventListener('touchstart', setupUnlock, { once: true, passive: true });
  document.addEventListener('touchend', setupUnlock, { once: true, passive: true });
  document.addEventListener('click', setupUnlock, { once: true, passive: true });
}

const speak = async (text) => {
  const speechText = text
    .replace(/```[\s\S]*?```/g, '')
    .replace(/[*_~`#]/g, '')
    .trim()
  if (!speechText) return

  if (window.speechSynthesis) {
    window.speechSynthesis.cancel()
    
    if (availableVoices.length === 0) {
      availableVoices = window.speechSynthesis.getVoices()
    }
    
    // Tenta encontrar uma voz feminina (Luciana no iOS, Google português Brasil no Android, etc)
    let voice = availableVoices.find(v => v.lang.startsWith('pt') && (v.name.includes('Luciana') || v.name.includes('Vitoria') || v.name.includes('Google português do Brasil')))
    if (!voice) voice = availableVoices.find(v => v.lang === 'pt-BR')
    if (!voice) voice = availableVoices.find(v => v.lang.startsWith('pt'))

    const utterance = new SpeechSynthesisUtterance(speechText)
    utterance.lang = 'pt-BR'
    if (voice) utterance.voice = voice
    // Ajustes para voz feminina/suave
    utterance.rate = 1.05
    utterance.pitch = 1.2 
    window.speechSynthesis.speak(utterance)
  }
}

export const useVoice = (onTranscript) => {
  const [isListening, setIsListening] = useState(false)

  const startListening = useCallback(() => {
    unlockAudio()
    
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      alert('Seu navegador não suporta reconhecimento de voz.')
      return
    }

    const recognition = new SpeechRecognition()
    recognition.lang = 'pt-BR'
    recognition.continuous = false
    recognition.interimResults = false

    recognition.onstart = () => setIsListening(true)
    recognition.onresult = (event) => onTranscript(event.results[0][0].transcript)
    recognition.onerror = () => setIsListening(false)
    recognition.onend = () => setIsListening(false)
    recognition.start()
  }, [onTranscript])

  return { isListening, startListening, speak, unlockAudio }
}


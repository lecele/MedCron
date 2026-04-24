# 💊 Medicações - Assistente Inteligente

Aplicativo de saúde para gestão de medicamentos integrado ao **OpenClaw**.

## 🚀 Como Acessar

1. **Local (Desenvolvimento):**
   - Execute `npm run dev` no terminal desta pasta.
   - Acesse: [http://localhost:5173](http://localhost:5173)

2. **Interface do Gateway (VPS):**
   - Acesse: [http://129.121.33.171:18789](http://129.121.33.171:18789)
   - Token: `openclaw2026`

## 🧠 Agentes de Saúde
- **MedCron (Sistema Integrado)**:
  - **🔍 Verificador**: OCR e extração precisa.
  - **💡 Conselheiro**: Validação e suporte às dúvidas.
  - **⏰ Tutor**: Lembretes inteligentes e sync com Supabase/Telegram.

## ✅ Funcionalidades Implementadas
- [x] Onboarding personalizado (com TTS de boas-vindas).
- [x] **LGPD Dinâmica**: Consentimento solicitado de forma suave *após* a interação inicial, mantendo o usuário engajado. Modal 100% responsivo.
- [x] Extração de receitas via Foto/PDF (GPT-4o).
- [x] Calendário interativo de tratamento.
- [x] **Sincronização em tempo real**: Ao marcar como "tomado", o status é salvo no Supabase e uma notificação de confirmação é enviada ao grupo do Telegram.

---
*Desenvolvido por Antigravity para Leonardo.*


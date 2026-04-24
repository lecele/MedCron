# MedCron — Assistente Inteligente de Medicamentos

> **Agenda seus medicamentos com segurança, inteligência e conformidade com a LGPD.**

O MedCron é um assistente conversacional de saúde que extrai dados de receitas médicas via OCR,
valida clinicamente as doses com IA farmacológica e agenda lembretes personalizados
para o paciente — via calendário nativo (iOS/Android).

🌐 **Deploy:** [medcron-app.vercel.app](https://medcron-app.vercel.app)

---

## ✨ Funcionalidades

| Funcionalidade | Descrição |
|---|---|
| 📷 **OCR de Receitas** | Extrai medicamentos, doses e horários de fotos ou PDFs de receitas médicas via GPT-4o com visão |
| 💬 **Entrevista Conversacional** | Coleta nome, idade, peso, sexo e telefone do paciente de forma natural e humanizada |
| 🧪 **Validação Farmacológica IA** | GPT-4o-mini verifica doses contra bulas, interações e perfil do paciente (peso, idade, populações especiais) |
| ⚠️ **Alertas de Segurança** | Bloqueia automaticamente o agendamento se detectar risco real e orienta o paciente a consultar o médico |
| 📅 **Calendário .ics** | Gera arquivo compatível com iOS (Calendário nativo) e Android (Google Calendar) |

| 🔒 **Conformidade LGPD** | Consentimento explícito antes de qualquer coleta de dado sensível de saúde (Art. 11, Lei 13.709/2018) |
| 🗣️ **Voz (TTS)** | Respostas do agente narradas em áudio via OpenAI TTS (voz Onyx) |
| 🎤 **Reconhecimento de Fala** | Entrada por microfone usando Web Speech API |

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React/Vite)                    │
│  LGPDConsent → Chat Interface → Voice (TTS + STT) → Calendar   │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTPS (Vercel)
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI + Python)                    │
│                                                                 │
│  POST /api/chat ──────────→ LangGraph Graph                    │
│  POST /api/consent                 ↓                           │
│  GET  /api/calendar/generate  MedCron Agent (GPT-4o-mini)      │

│  POST /api/tts                     ↓                           │
│  GET  /api/health             Supabase (PostgreSQL + RLS)      │
└─────────────────────────────────────────────────────────────────┘
```

### Fluxo Conversacional Completo

```
Usuário abre o app
       ↓
  [LGPD] Consentimento explícito (Art. 11 Lei 13.709/2018)
       ↓
  Envio da foto/PDF da receita
       ↓
  OCR → Extração de medicamentos, doses, horários, médico
       ↓
  Entrevista: Confirmação → Idade → Peso → Sexo → Telefone
                                    ↓
                      [VALIDAÇÃO FARMACOLÓGICA IA]
                      GPT-4o-mini como farmacêutico clínico:
                      • Doses por tomada vs. limite do fabricante
                      • Dose diária total vs. limite máximo
                      • Interações medicamentosas
                      • Populações especiais (crianças, idosos, baixo peso)
                                    ↓
               ┌───── Alertas críticos? ─────┐
               │ SIM                      NÃO│
               ↓                             ↓
        Alerta ao paciente          Resumo + Confirmação
        "Consulte seu médico"               ↓
        FIM (sem agendamento)       JSON → Supabase
                                           ↓
                                  Calendário .ics
```

---

## 🤖 Agentes

| Agente | Modelo | Função |
|---|---|---|
| **MedCron Agent** | GPT-4o-mini | Orquestrador principal — extração, entrevista, resumo e confirmação |
| **Validador IA** | GPT-4o-mini | Farmacêutico clínico — valida doses contra perfil do paciente |
| **Validador Determinístico** | Python puro | Fallback com banco de limites para 6+ fármacos comuns |
| **Vision Agent** | GPT-4o-mini | OCR de imagens de receitas médicas |
| **Supervisor** | GPT-4o-mini | Roteamento de casos especiais |
| **Escrivão** | Supabase | Persistência de receitas, medicamentos e lembretes |

---

## 🔒 Conformidade LGPD

O MedCron trata **dados pessoais sensíveis de saúde** (receitas, medicamentos, peso, idade),
enquadrando-se no **Art. 11 da Lei 13.709/2018 (LGPD)**.

**Implementação Atualizada (UX):**
- **Fluxo Não Bloqueante (Inicial):** O paciente recebe uma mensagem inicial de boas-vindas do agente sem bloqueio de tela.
- **Interação Natural:** O modal de consentimento LGPD só é exibido *após* a primeira interação ou apresentação (delay estratégico de 2,5s). Isso melhora a retenção e experiência (UX).
- Texto claro sobre: o que é coletado, finalidade e direitos do paciente.
- Aceite registrado no Supabase com timestamp e versão da política (`v1.0`).
- Fallback em `localStorage` garante persistência offline.
- Componente 100% responsivo para resoluções mobile (com barra de rolagem interna, garantindo visibilidade dos botões de aceite).
- RLS (Row Level Security) no Supabase: cada usuário acessa apenas seus próprios dados.

---

## 📁 Estrutura do Projeto

```
MedCron_Py/
├── app/
│   ├── main.py                        # Ponto de entrada FastAPI + CORS + Lifespan
│   ├── api/
│   │   ├── routes.py                  # Todos os endpoints HTTP
│   │   └── schemas.py                 # Modelos Pydantic Request/Response
│   ├── agents/
│   │   ├── graph.py                   # Compilação do grafo LangGraph
│   │   ├── state.py                   # Estado compartilhado entre agentes
│   │   ├── supervisor.py              # Roteador principal
│   │   ├── medcron_agent.py           # Agente conversacional unificado ⭐
│   │   ├── validador_ia.py            # Validação farmacológica via GPT-4o-mini ⭐
│   │   ├── validador_farmaceutico.py  # Validação determinística (fallback)
│   │   ├── vision_agent.py            # OCR de receitas
│   │   ├── onboarding_agent.py        # Coleta de dados do paciente
│   │   ├── escrivao_agent.py          # Persistência no Supabase
│   │   └── chat_agent.py              # Chat genérico
│   ├── services/
│   │   ├── calendar_service.py        # Gerador de .ics (iOS/Android)
│   │   └── memory_service.py          # Memória de longo prazo (MemPalace)
│   └── core/
│       ├── config.py                  # Configurações (pydantic-settings)
│       └── clients.py                 # Singletons: Supabase, OpenAI, Gemini
├── Frontend/
│   ├── src/
│   │   ├── App.jsx                    # Componente principal + lógica LGPD
│   │   ├── components/
│   │   │   ├── LGPDConsent.jsx        # Modal de consentimento LGPD ⭐
│   │   │   ├── AnimatedLogo.jsx       # Logo animado do MedCron
│   │   │   ├── AlertModal.jsx         # Modal de alertas farmacológicos
│   │   │   └── PillIcon.jsx           # Ícone de pílula (SVG)
│   │   ├── hooks/
│   │   │   ├── useReminders.js        # Hook de lembretes (Supabase)
│   │   │   └── useVoice.js            # Hook de TTS + STT (Web Audio API)
│   │   └── services/
│   │       ├── agents.js              # Chamadas ao backend
│   │       ├── supabase.js            # Auth + perfil
│   │       ├── calendar.js            # Download .ics

│   ├── index.html
│   └── package.json
├── .env.example                       # ✅ Template (sem valores reais)
├── .gitignore                         # Protege .env e segredos
├── requirements.txt                   # Dependências Python
├── vercel.json                        # Configuração de deploy
└── README.md                          # Este arquivo
```

> ⭐ = Adicionado/atualizado na versão atual

---

## 🗄️ Banco de Dados (Supabase)

| Tabela | Descrição |
|---|---|
| `profiles` | Perfil do paciente: nome, idade, peso, sexo, telefone, médico |
| `receitas` | Receitas médicas processadas |
| `medicamentos` | Medicamentos extraídos de cada receita |
| `lembretes` | Horários de tomada para sincronização do calendário |
| `consents` | Registro de consentimento LGPD com timestamp e versão ⭐ |

Todas as tabelas possuem **Row Level Security (RLS)** ativo — cada usuário acessa apenas seus próprios dados.

---

## 🚀 Setup Local

### 1. Pré-requisitos

- Python 3.11+
- Node.js 18+
- Conta Supabase
- Chaves de API: OpenAI, Google AI (opcional)

### 2. Backend

```bash
git clone https://github.com/lecele/MedCron.git
cd MedCron

# Cria ambiente virtual
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

pip install -r requirements.txt

# Configura variáveis de ambiente
cp .env.example .env
# Edite o .env com suas chaves
```

### 3. Frontend

```bash
cd Frontend
npm install
npm run dev
```

### 4. Inicia o backend

```bash
# Na raiz do projeto
uvicorn app.main:app --reload --port 8000
```

Acesse: http://localhost:5173 (frontend) | http://localhost:8000/docs (API Swagger)


## 🌐 Deploy na Vercel

O projeto está configurado para deploy fullstack na Vercel:
- **Backend:** Python (FastAPI via `@vercel/python`)
- **Frontend:** React/Vite (build estático)

### Passos

1. Faça push para o GitHub
2. Importe o repositório na [Vercel](https://vercel.com)
3. Configure as variáveis de ambiente em **Settings → Environment Variables**
4. O deploy é automático a cada push na branch `main` ✅

### Variáveis obrigatórias na Vercel

```
SUPABASE_URL
SUPABASE_ANON_KEY
OPENAI_API_KEY

ENVIRONMENT=production
ALLOWED_ORIGINS=https://medcron.vercel.app
```

---

## 🔐 Segurança

- **`.env` está no `.gitignore`** — nunca vai para o GitHub
- **Swagger UI desabilitado em produção**
- **CORS restrito** — apenas origens configuradas em `ALLOWED_ORIGINS`
- **Supabase RLS** — Row Level Security em todas as tabelas
- **LGPD** — Consentimento explícito antes de qualquer coleta de dado sensível
- **Validação IA conservadora** — em caso de dúvida, o sistema bloqueia e alerta

---

## 📋 API Endpoints

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/health` | Status do backend |
| `POST` | `/api/chat` | Mensagem conversacional (com/sem imagem) |
| `POST` | `/api/consent` | Registro de consentimento LGPD |
| `GET` | `/api/calendar/generate` | Download do arquivo .ics |

| `POST` | `/api/tts` | Texto para fala (OpenAI TTS) |

---

## 🛠️ Stack Tecnológica

| Camada | Tecnologia |
|---|---|
| Frontend | React 18, Vite, Vanilla CSS |
| Backend | Python 3.11, FastAPI, LangGraph |
| IA | GPT-4o-mini (chat + OCR + validação farmacológica) |
| Banco | Supabase (PostgreSQL + Auth + RLS) |
| Voz | OpenAI TTS (Onyx) + Web Speech API |
| Deploy | Vercel (fullstack) |
| Calendario | RFC 5545 (.ics) |
| Notificações | Calendário Nativo (.ics) |

---

## 📄 Licença

Este projeto está em fase de desenvolvimento. Todos os direitos reservados.

---

*MedCron — Cuide da sua saúde com inteligência* 💊

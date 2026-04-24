# 💊 MedCron — Assistente Inteligente de Medicações

O **MedCron** é uma plataforma ecossistêmica projetada para simplificar a gestão de tratamentos médicos. Ele une Inteligência Artificial de ponta, persistência de dados em nuvem e notificações em tempo real para garantir que nenhum paciente perca uma dose.

---

## 🚀 Como o Sistema Funciona (Visão Geral)

O projeto é dividido em três pilares principais que trabalham em harmonia:

1.  **Interface Humana (React)**: Onde o usuário conversa, envia receitas e visualiza seu progresso.
2.  **Cérebro de IA (OpenClaw + OpenAI)**: Onde o processamento de linguagem natural e a visão computacional (OCR) transformam fotos de receitas em agendamentos digitais precisos.
3.  **Motor de Notificações (Node.js + Telegram)**: Um trabalhador de segundo plano que monitora o banco de dados e dispara alertas críticos.

---

## 🛠️ Arquitetura Técnica

### 1. Frontend & Design
Desenvolvido com **Vite + React**, o app utiliza um design moderno baseado em **Glassmorphism**, com foco em acessibilidade e rapidez.
- **Voz**: Integração com API de reconhecimento de voz para comandos rápidos.
- **Calendário**: Visualização dinâmica do período de tratamento.
- **Sincronismo Mobile**: Geração de arquivos `.ics` (iCalendar) otimizados para iOS e Android via QR Code.

### 2. Os Agentes de IA (OpenClaw Gateway)
Toda a lógica de IA é mediada por um **OpenClaw Gateway** instalado em uma VPS dedicada. Isso permite:
- **Proxy Seguro**: Oculta as chaves da OpenAI e centraliza as requisições.
- **Modelos Especializados**:
    - `gpt-4o` (Vision): Usado para "ler" as receitas médicas enviadas em imagem ou PDF.
    - `gpt-4o-mini`: Usado para o chat conversacional rápido e econômico.
- **System Prompt Rígido**: O agente segue regras farmacológicas (ex: regra 8/8h) e extrai metadados estruturados (Médico, CRM, Dosagem).

### 3. Banco de Dados (Supabase)
O MedCron utiliza **Supabase (PostgreSQL)** para persistência resiliente.
- **Tabelas**:
    - `profiles`: Armazena dados do paciente (nome, idade, telefone) e médico.
    - `receitas`: Histórico de prescrições processadas.
    - `medicamentos`: Lista detalhada de substâncias extraídas.
    - `lembretes`: Cada dose individual que precisa ser tomada.
- **Segurança (RLS)**: Cada usuário possui uma sessão anônima persistente (ou vinculada a e-mail), garantindo que apenas ele veja seus próprios dados médicos.

### 4. O Motor de Lembretes (Telegram Worker)
O arquivo `telegram_worker.js` é um serviço autônomo.
- Ele roda continuamente (verificando a cada 30 segundos).
- Consulta a tabela de `lembretes` em busca de doses que devem ser tomadas no minuto atual.
- Dispara mensagens formatadas em HTML para o grupo do Telegram, incluindo o nome do paciente e a dosagem exata.

---

## 📖 Funcionalidades Detalhadas

### 📸 Extração Inteligente de Receitas
Quando você envia uma foto/PDF, o sistema:
1. Converte o arquivo para uma imagem otimizada.
2. Envia para o `gpt-4o` com instruções para extrair dados estruturados.
3. Apresenta os medicamentos encontrados para confirmação.
4. Gera automaticamente um plano de 7 dias (ou o período especificado na receita).

### 💬 Fluxo Conversacional (Socratic Agent)
O assistente não apenas agenda, ele **pergunta**. Ele solicita idade, peso e telefone se não estiverem na receita, garantindo um perfil completo para segurança farmacológica.

### 📅 Sincronização de Calendário (Estratégia RDATE)
Diferente de apps comuns que geram uma "regra de repetição" (que falha em muitos celulares), o MedCron usa a estratégia **RDATE-CANNON**: ele lista cada horário de cada dia explicitamente no arquivo de calendário, garantindo 100% de compatibilidade com iPhones e Androids.

---

## 🛠️ Comandos de Inicialização

Para rodar o projeto localmente, você precisa de dois terminais:

**Terminal 1 (Interface):**
```bash
npm run dev
```

**Terminal 2 (Motor de Notificações):**
```bash
npm run worker
```

> **Nota**: A VPS com o OpenClaw Gateway deve estar online para que a inteligência artificial funcione. O status de conexão é exibido no cabeçalho do aplicativo.

---

## 📂 Estrutura de Pastas Principal

- `/src/services/` — Lógica de integração (Supabase, OpenAI, Telegram, Calendar).
- `/src/hooks/` — Lógica de estado reutilizável (Lembretes, Voz).
- `/src/components/` — UI modular (Calendário, Lista de Lembretes, Modais).
- `telegram_worker.js` — Script de background para alertas.
- `vite.config.js` — Configuração de proxy para a VPS.

---
*Desenvolvido para salvar vidas, uma dose de cada vez.*

# 🚀 Master Plan: MedCron Python (FastAPI + LangGraph)

Este é o documento definitivo arquitetural para a fundação do **MedCron_Py**, idealizado para ser o substituto definitivo e seguro do atual MedCron_OpenClaw.

## 1. Visão Geral e Estratégia
- **Objetivo**: Substituir o roteador OpenClaw e lógicas de proxy em Node.js por um backend nativo em Python (FastAPI) altamente escalável.
- **Ecossistema IA**: Migrar de um "agente único longo" para uma **Rede Multi-Agente (Network of Agents)** baseada no padrão Orquestrador-Trabalhadores usando LangGraph & LangChain.
- **Benefício Clínico**: Redução a zero das alucinações matemáticas (com código Python puro focado em farmacologia) e extração de dados perfeita usando os LLMs mais adequados para cada tarefa.

## 2. A Core Stack (Backend)
- **Framework Web**: `FastAPI` (Rápido, tipado nativamente, excelente documentação automática OpenAPI).
- **Banco de Dados**: `Supabase` (PostgreSQL). Vamos aproveitar as tabelas `profiles`, `receitas` e `lembretes` existentes, aplicando apenas as regras de row-level-security (RLS) corretas.
- **Gerenciamento de Estado**: `LangGraph` compilado. Ele armazenará o histórico e o avanço da triagem do paciente em um Checkpointer atrelado ao PostgreSQL.

## 3. Seleção de Modelos Híbridos (The Best of O.S.)
Vamos aproveitar que você é Desenvolvedor Google AI Studio Pro e também possui chaves OpenAI:
- 🧠 **Agente Orquestrador & Chat Rápido**: OpenAI `GPT-4o-mini` ou `GPT-4o`. Excepcionalmente rápido para classificar a "intenção" do paciente (Tirando dúvida vs Mandando Receita) e interagir no dia-a-dia.
- 👁️ **Agente Visão / Faturamento Médico**: Google `Gemini 1.5 Pro` (Multimodal). Vai receber os arquivos de imagem das prescrições. Escolhido por sua taxa imbatível de OCR em caligrafia complexa e alta janela de contexto.

## 4. Arquitetura do LangGraph (Os Especialistas)

O grafo de conversação rodará pelo seguinte ciclo de decisão inteligente:

1. **Entrada Backend**: FastAPI recebe `message` (e opcionalmente `base64_image`).
2. **Nó de Início (Supervisor)**: Avalia o Payload.
   - Se houver Imagem $\rightarrow$ Direciona para nó "Visão Medica (Gemini)".
   - Se faltar dados no perfil $\rightarrow$ Direciona para "Triagem/Onboarding (GPT-4o-mini)".
3. **Nó Tool Farmacêutica (Sem IA, Puramente Matemático)**:
   - Todo medicamento extraído da receita passará obrigatoriamente por essa função Python.
   - Migração exata do antigo código `clinicalValidator.js`.
   - Limita a "Amoxicilina" a 3000mg/dia, "Paracetamol" a 4000mg/dia. Caso estoure: bloqueia o percurso e alerta o Supervisor sobre o perigo clínico.
4. **Resumo Cognitivo (MemPalace)**:
   - Em background, usamos PgVector ou Summarization para criar histórico passivo do paciente ("O paciente informou alergia a dipirona") que sempre é inserido no System Prompt sem estourar os tokens.

## 5. Resolução de Falhas Críticas do Frontend Web

A interface visual (React) será TOTALMENTE reaproveitada. Nenhuma alteração visual será feita, exceto apontar os endpoints `/api/...` para o novo FastAPI.

**Melhorias Estruturais de UX que serão resolvidas:**
- 🐛 **O Bug do Apple Calendar/Android (.ics)**: 
  - *Problema antigo*: O frontend React tentava montar o `.ics` no cliente e falhava miseravelmente quando um remédio tinha múltiplos horários ("08:00, 16:00, 00:00") devido a validação errada e blobs problemáticos no iOS.
  - *Nova Solução*: O botão "Baixar Calendário" no celular, chamará o backend (Ex: `GET /api/calendar/generate?patient_id=xxx`). O servidor FastAPI gerará um `.ics` perfeitamente protocolado garantindo que iPhones leiam perfeitamente os arquivos remotos.
- 💬 **Acionamento do Telegram Bot:**
  - O App não tentará se comportar feito um software desktop que ativa IAs autônomas no celular. 
  - O fluxo é simples: *Processado pela IA na Nuvem $\rightarrow$ Salvo no Supabase $\rightarrow$ Link `tg://resolve?domain=nome_bot` acionado nativamente*.

---

## 6. Primeiros Passos da Execução
1. Abrir a pasta `MedCron_Py` no VS Code.
2. Inicializar o repo Frontend copiando os assets `src/` e `package.json` puros do projeto velho.
3. Inicializar a subestrutura Python (Criando `app/main.py`, `app/agents/`, `app/core/config.py`).
4. Desenvolver o Nó de Validação Farmacêutica e testá-lo isoladamente.
5. Inserir a Chain de Visão do Gemini e o Orquestrador OpenAI e interligá-los no LangGraph.

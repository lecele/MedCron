"""
MedCron_Py — Agente de Onboarding (Coleta de Dados do Paciente)

Conduz de forma amigável a coleta das informações essenciais do novo paciente:
Nome, idade, peso, telefone, condições crônicas e alergias.
Persiste os dados na tabela `profiles` do Supabase ao final do fluxo.
"""
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.agents.state import AgentState, MedCronMessage
from app.core.clients import get_supabase
from app.core.config import get_settings

ONBOARDING_SYSTEM_PROMPT = """
Você é o MedCron, um assistente de saúde que ajuda as pessoas a tomar seus medicamentos na hora certa.
Sua missão neste momento é conhecer o paciente para personalizar os lembretes de medicamentos.

IMPORTANTE — Você NÃO é médico e NÃO deve fazer diagnósticos ou perguntas clínicas.
Você precisa apenas de informações básicas para criar os lembretes personalizados.

Dados necessários para o cadastro:
- nome_completo (string) — para personalizar os lembretes
- idade (número inteiro) — para adaptar a comunicação
- peso_kg (número decimal) — para referência das doses da receita
- telefone (string, com DDD) — para contato e identificação no app

Analise o histórico da conversa e identifique quais campos já foram coletados.
Responda SOMENTE em JSON com a seguinte estrutura:

{{
  "dados_coletados": {{
    "nome_completo": null,
    "idade": null,
    "peso_kg": null,
    "telefone": null,
    "condicoes_cronicas": [],
    "alergias_medicamentosas": []
  }},
  "cadastro_completo": false,
  "proxima_pergunta": "Sua mensagem amigável para o paciente"
}}

Regras ESSENCIAIS:
- Seja caloroso, natural e humanizado, como um profissional de saúde simpático. Evite linguagem fria ou robótica.
- Use o nome do paciente sempre que souber.
- Colete UM dado por vez de forma totalmente conversacional.
- Se o paciente fizer uma pergunta paralela (por exemplo, "o que é isso?", "para que serve?"), responda de forma simples e IMEDIATAMENTE retome a coleta do próximo dado com uma frase de transição natural.
- NUNCA pergunte sobre doenças crônicas, alergias ou histórico médico. Isso não é necessário para agendar lembretes.
- IMPORTANTE: O número de TELEFONE é essencial para identificação segura do paciente. Se o paciente não informou, você DEVE perguntar de forma gentil.
- Quando todos os 4 campos (nome, idade, peso, telefone) estiverem preenchidos, defina cadastro_completo=true e em proxima_pergunta escreva uma mensagem calorosa de boas-vindas e peça para enviar a receita médica.
- Use emojis com moderação 😊💊.
- Responda sempre em Português Brasileiro.
- O campo proxima_pergunta é o que o paciente vai VER e OUVIR — escreva de forma humana e natural, sem jargões técnicos.

Dados já coletados nesta sessão: {dados_atuais}
"""


async def onboarding_agent_node(state: AgentState) -> dict:
    """
    Nó de Onboarding: coleta dados do novo paciente de forma conversacional
    e persiste no Supabase ao completar o cadastro.
    """
    settings = get_settings()
    ultima_mensagem = ""
    if state.messages:
        ultima_mensagem = state.messages[-1].content

    # Serializa dados já coletados no estado
    dados_atuais = json.dumps(
        state.dados_onboarding or {}, ensure_ascii=False, indent=2
    )

    system_content = ONBOARDING_SYSTEM_PROMPT.format(dados_atuais=dados_atuais)

    # Monta histórico relevante (últimas 12 msgs para contexto de coleta)
    messages_for_llm = [SystemMessage(content=system_content)]
    historico = state.messages[-12:] if len(state.messages) > 12 else state.messages
    for msg in historico:
        if msg.role == "user":
            messages_for_llm.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            from langchain_core.messages import AIMessage
            messages_for_llm.append(AIMessage(content=msg.content))

    try:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=settings.openai_api_key,
            temperature=0.4,
            response_format={"type": "json_object"},
        )

        response = await llm.ainvoke(messages_for_llm)
        dados = json.loads(response.content)

        dados_coletados = dados.get("dados_coletados", {})
        cadastro_completo = dados.get("cadastro_completo", False)
        proxima_pergunta = dados.get("proxima_pergunta", "Como posso ajudar?")

        updates: dict = {
            "dados_onboarding": dados_coletados,
            "messages": [MedCronMessage(role="assistant", content=proxima_pergunta)],
            "resposta_final": proxima_pergunta,
            "next_node": "end",
        }

        # Se cadastro completo → persiste no Supabase e marca onboarding
        if cadastro_completo and state.usuario_id:
            try:
                supabase = await get_supabase()
                await supabase.table("profiles").upsert({
                    "id": state.usuario_id,
                    "nome": dados_coletados.get("nome_completo"),
                    "idade": dados_coletados.get("idade"),
                    "peso": str(dados_coletados.get("peso_kg")),
                    "telefone": dados_coletados.get("telefone"),
                    "onboarding_completo": True,
                }).execute()
                updates["onboarding_completo"] = True
                updates["patient_name"] = dados_coletados.get("nome_completo")
                
                # Se existem medicamentos aguardando salvamento, transfira para o Escrivão
                if state.medicamentos_validados:
                     updates["next_node"] = "escrivao_agent"

                print(f"[Onboarding] Paciente {state.usuario_id} cadastrado com sucesso.")
            except Exception as e:
                print(f"[Onboarding] Erro ao persistir no Supabase: {e}")
                # Continua sem travar o fluxo

        return updates

    except Exception as e:
        resposta_fallback = (
            "Olá! Seja bem-vindo ao MedCron 💊\n\n"
            "Para começar, poderia me dizer seu nome completo?"
        )
        return {
            "resposta_final": resposta_fallback,
            "messages": [MedCronMessage(role="assistant", content=resposta_fallback)],
            "next_node": "end",
        }

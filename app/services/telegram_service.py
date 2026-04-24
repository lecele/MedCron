"""
MedCron_Py — Serviço de Integração com Telegram

Fluxo:
1. Usuário clica "Agendar no Telegram" → frontend redireciona para deep link do bot
2. Usuário abre o bot e clica "Iniciar" → Telegram envia /start {token} para o webhook
3. Webhook decodifica o token (usuario_id em base64) e salva o chat_id no perfil
4. Bot envia os lembretes agendados diretamente na conversa pessoal do usuário
"""
import base64
import json
import urllib.request
from datetime import datetime

from app.core.config import get_settings
from app.core.clients import get_supabase


def _get_bot_token() -> str:
    # .strip() remove o \n que o PowerShell/echo adiciona às env vars na Vercel
    return (get_settings().telegram_bot_token or "").strip()


def _get_bot_username() -> str:
    return get_settings().telegram_bot_username or "lecele_bot"


def _telegram_api(method: str) -> str:
    return f"https://api.telegram.org/bot{_get_bot_token()}/{method}"


def encode_usuario_id(usuario_id: str) -> str:
    """Codifica o usuario_id em base64 URL-safe para uso no deep link do Telegram."""
    return base64.urlsafe_b64encode(usuario_id.encode()).decode().rstrip("=")


def decode_usuario_id(token: str) -> str | None:
    """Decodifica o token do deep link de volta para o usuario_id."""
    try:
        # Repadding necessário para base64 válido
        padding = 4 - len(token) % 4
        if padding != 4:
            token += "=" * padding
        return base64.urlsafe_b64decode(token).decode()
    except Exception:
        return None


async def send_telegram_message(chat_id: str | int, text: str) -> bool:
    """Envia uma mensagem de texto para um chat do Telegram."""
    try:
        payload = json.dumps({
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
        }).encode()
        req = urllib.request.Request(
            _telegram_api("sendMessage"),
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as res:
            data = json.loads(res.read())
            return data.get("ok", False)
    except Exception as e:
        print(f"[Telegram] Erro ao enviar mensagem: {e}")
        return False


async def register_telegram_user(usuario_id: str, chat_id: str | int) -> bool:
    """Salva o chat_id do Telegram no perfil do usuário no Supabase."""
    try:
        supabase = await get_supabase()
        await supabase.table("profiles").upsert({
            "id": usuario_id,
            "telegram_id": str(chat_id),
        }).execute()
        return True
    except Exception as e:
        print(f"[Telegram] Erro ao salvar telegram_id: {e}")
        return False


async def send_reminders_to_user(usuario_id: str, chat_id: str | int) -> bool:
    """
    Busca os lembretes ativos do usuário no Supabase e envia para o Telegram pessoal.
    """
    try:
        supabase = await get_supabase()
        result = await supabase.table("lembretes").select("*").eq(
            "usuario_id", usuario_id
        ).eq("status", "pendente").execute()

        lembretes = result.data or []
        if not lembretes:
            await send_telegram_message(
                chat_id,
                "⚠️ Nenhum lembrete ativo encontrado. Envie sua receita médica no app MedCron primeiro!"
            )
            return False

        # Monta a mensagem de resumo agrupada por medicamento
        linhas = ["📋 <b>Seus lembretes MedCron foram configurados!</b>\n"]
        for lem in lembretes:
            nome = lem.get("nome", "Medicamento")
            dosagem = lem.get("dosagem", "")
            horario = lem.get("horario", "")
            duracao = lem.get("duracao_dias", 7)
            linhas.append(
                f"💊 <b>{nome}</b> {dosagem} — ⏰ {horario} por {duracao} dias"
            )

        linhas.append(
            "\n✅ Você receberá lembretes aqui neste chat nos horários programados."
            "\n\n💡 Dica: Mantenha o app Telegram instalado para receber as notificações."
        )

        texto = "\n".join(linhas)
        return await send_telegram_message(chat_id, texto)

    except Exception as e:
        print(f"[Telegram] Erro ao buscar/enviar lembretes: {e}")
        return False


def generate_deep_link(usuario_id: str) -> str:
    """Gera o link para o usuário iniciar o bot do Telegram com o token do seu perfil."""
    token = encode_usuario_id(usuario_id)
    bot_username = _get_bot_username()
    return f"https://t.me/{bot_username}?start={token}"

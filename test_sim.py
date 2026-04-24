import asyncio
from app.api.routes import chat_endpoint
from app.api.schemas import ChatRequest

async def test_sim():
    try:
        req = ChatRequest(
            message="sim",
            usuario_id="test_uid",
            sessao_id="test_session"
        )
        res = await chat_endpoint(req)
        print("RESPOSTA:", res)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_sim())

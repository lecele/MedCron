import asyncio
import uuid
import uuid as _uuid
from app.core.clients import get_supabase

async def test_insert():
    try:
        supabase = await get_supabase()
        
        # Test UUID
        test_uid = str(_uuid.uuid4())
        receita_id = str(_uuid.uuid4())
        
        # This will probably fail if profile doesn't exist? Wait, maybe profile doesn't exist!
        # If test_uid is totally random, we can see the exact error.
        print("Trocando inserir Receita sem Profile...")
        res = await supabase.table("receitas").insert({
            "id": receita_id,
            "usuario_id": test_uid,
            "texto_extraido": "Teste",
        }).execute()
        print("Sucesso receitas!", res)

    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_insert())

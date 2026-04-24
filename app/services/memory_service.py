"""
MedCron_Py — Serviço de Memória com MemPalace (VPS Nativa)

Integra o MemPalace de forma direta acessando o banco de dados ChromaDB local na VPS.
Isso elimina qualquer latência de rede.
"""

import sys
import os
from pathlib import Path
from typing import Optional
from app.core.config import get_settings

# Caminho do MemPalace local (configurado via .env)
MEMPALACE_PATH = os.environ.get(
    "MEMPALACE_PATH",
    r"/root/.mempalace/palace"
)

_mempalace_disponivel = False
_MemoryStack = None

try:
    # Ajusta path se a library não estiver no pip globals
    from mempalace.layers import MemoryStack as _MemoryStack
    _mempalace_disponivel = True
    print("[MemPalace] Modulo carregado com sucesso nativamente.")
except ImportError as e:
    print(f"[MemPalace] Indisponível nativamente: {e}")
    print("[MemPalace] Operando em modo de degradacao (sem memoria de longo prazo).")

# Ala dedicada ao MedCron dentro do MemPalace
MEDCRON_WING = "medcron"

def _get_stack(palace_path: Optional[str] = None):
    if not _mempalace_disponivel or _MemoryStack is None:
        return None
    try:
        settings = get_settings()
        final_path = palace_path or settings.mempalace_path or MEMPALACE_PATH
        return _MemoryStack(palace_path=final_path)
    except Exception as e:
        print(f"[MemPalace] Erro ao instanciar MemoryStack: {e}")
        return None

async def get_patient_context(usuario_id: str, pergunta: str = "") -> str:
    """Recupera o contexto de memória do paciente do ChromaDB local."""
    stack = _get_stack()
    if stack is None:
        return ""

    try:
        # L1 — Contexto essencial
        contexto_l1 = stack.recall(
            wing=MEDCRON_WING,
            room=usuario_id,
            n_results=5,
        )

        # L3 — Busca semântica profunda
        contexto_l3 = ""
        if pergunta and len(pergunta) > 10:
            contexto_l3 = stack.search(
                query=pergunta,
                wing=MEDCRON_WING,
                room=usuario_id,
                n_results=3,
            )

        partes = []
        if contexto_l1 and "No drawers found" not in contexto_l1:
            partes.append(contexto_l1)
        if contexto_l3 and "No results" not in contexto_l3:
            partes.append(contexto_l3)

        return "\n\n".join(partes) if partes else ""

    except Exception as e:
        print(f"[MemPalace Nativo] Erro ao recuperar contexto do paciente {usuario_id}: {e}")
        return ""

def salvar_fato_paciente(
    usuario_id: str,
    fato: str,
    room: str = "historico",
    importance: float = 3.0,
) -> bool:
    """Salva diretamente no banco de dados do ChromaDB."""
    stack = _get_stack()
    if stack is None:
        return False

    try:
        import chromadb
        import uuid as _uuid
        
        settings = get_settings()
        final_path = settings.mempalace_path or MEMPALACE_PATH
        client = chromadb.PersistentClient(path=final_path)

        try:
            col = client.get_collection("mempalace_drawers")
        except Exception:
            col = client.create_collection("mempalace_drawers")

        col.add(
            documents=[fato],
            metadatas=[{
                "wing": MEDCRON_WING,
                "room": usuario_id,
                "sub_room": room,
                "importance": importance,
                "patient_id": usuario_id,
            }],
            ids=[str(_uuid.uuid4())],
        )
        print(f"[MemPalace Nativo] Fato salvo com sucesso ({importance}): {fato}")
        return True

    except Exception as e:
        print(f"[MemPalace Nativo] Erro ao salvar fato: {e}")
        return False

def is_available() -> bool:
    return _mempalace_disponivel

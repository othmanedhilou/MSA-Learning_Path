# Serveur MCP — expose les outils du SMA via le protocole Model Context Protocol
# Lancement : python learning_tools_server.py
# Inspection : npx @modelcontextprotocol/inspector python learning_tools_server.py
import json
import os
from datetime import datetime

from rag_engine import RAGEngine
from sm2 import SM2

try:
    from mcp.server.fastmcp import FastMCP
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("[WARN] mcp non installé. Lance : pip install mcp")

_rag = RAGEngine()
_sm2 = SM2()

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
PROFILES_PATH = os.path.join(BASE_DIR, 'data', 'profils_etudiants.json')


def search_ressources_rag_impl(query: str, n_results: int = 3) -> list:
    return _rag.chercher_ressources(query)[:n_results]


def compute_sm2_schedule_impl(etudiant: str, notion: str, qualite: int) -> dict:
    return _sm2.calculer(etudiant, notion, qualite)


def update_profile_ltm_impl(etudiant: str, updates: dict) -> dict:
    profils = {}
    if os.path.exists(PROFILES_PATH):
        with open(PROFILES_PATH, 'r', encoding='utf-8') as f:
            try:
                profils = json.load(f)
            except Exception:
                profils = {}
    if etudiant not in profils:
        profils[etudiant] = {"created_at": datetime.now().isoformat()}
    profils[etudiant].update(updates)
    profils[etudiant]["updated_at"] = datetime.now().isoformat()
    os.makedirs(os.path.dirname(PROFILES_PATH), exist_ok=True)
    with open(PROFILES_PATH, 'w', encoding='utf-8') as f:
        json.dump(profils, f, ensure_ascii=False, indent=2)
    return {"status": "saved", "etudiant": etudiant, "fields_updated": list(updates.keys())}


if MCP_AVAILABLE:
    mcp = FastMCP("learning-tools-server")

    @mcp.tool()
    def search_ressources_rag(query: str, n_results: int = 3) -> list:
        """Search learning resources via RAG (vector + keyword similarity).

        Args:
            query: concept to search (e.g., "Communication Inter-agents")
            n_results: maximum number of resources to return
        """
        return search_ressources_rag_impl(query, n_results)

    @mcp.tool()
    def compute_sm2_schedule(etudiant: str, notion: str, qualite: int) -> dict:
        """Compute next review date using SuperMemo-2 algorithm.

        Args:
            etudiant: student identifier
            notion: concept name
            qualite: response quality 0-5 (0=forgot, 5=perfect)
        """
        return compute_sm2_schedule_impl(etudiant, notion, qualite)

    @mcp.tool()
    def update_profile_ltm(etudiant: str, updates: dict) -> dict:
        """Update student long-term memory profile in persistent storage.

        Args:
            etudiant: student identifier
            updates: dict of fields to update
        """
        return update_profile_ltm_impl(etudiant, updates)


if __name__ == "__main__":
    if MCP_AVAILABLE:
        print("[MCP] Démarrage du serveur learning-tools-server (stdio)")
        mcp.run(transport="stdio")
    else:
        print("[FALLBACK] Test local sans MCP\n")
        print("--- search_ressources_rag('Communication Inter-agents') ---")
        for r in search_ressources_rag_impl("Communication Inter-agents", 2):
            print(f"  [{r.get('type')}] {r.get('source', 'n/a')}")
        print("\n--- compute_sm2_schedule('Othmane', 'Agents', 4) ---")
        print(compute_sm2_schedule_impl("Othmane", "Agents Intelligents", 4))
        print("\n--- update_profile_ltm('Othmane', {'last_module': 'MSA'}) ---")
        print(update_profile_ltm_impl("Othmane", {"last_module": "MSA"}))

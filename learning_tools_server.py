"""
Serveur MCP (Model Context Protocol) — expose les outils du SMA.

Référence cours : Chapitre 5 — MCP (FastMCP + @mcp.tool).
Trois outils exposés :
  1. search_ressources_rag    — RAG sur les ressources pédagogiques (Dodo D1)
  2. compute_sm2_schedule     — algorithme de répétition espacée (sm2.py)
  3. update_profile_ltm       — mémoire long-terme dans data/profils_etudiants.json

Lancement standalone (test) :
    python learning_tools_server.py
    npx @modelcontextprotocol/inspector python learning_tools_server.py

Le serveur tourne en mode stdio (sous-processus) — il est démarré par
l'orchestrateur via MultiServerMCPClient.
"""
import json
import os
from datetime import datetime

# Import des modules locaux (la team a déjà tout)
from rag_engine import RAGEngine
from sm2 import SM2

# ──────────────────────────────────────────────────────────────
# Tentative d'import de MCP — fallback gracieux si non installé
# ──────────────────────────────────────────────────────────────
try:
    from mcp.server.fastmcp import FastMCP
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("[WARN] Le package mcp n'est pas installé. "
          "Lance : pip install mcp")
    print("       Le serveur tournera en mode dégradé (fonctions Python directes).")

# ──────────────────────────────────────────────────────────────
# Instances partagées (initialisées une seule fois au démarrage)
# ──────────────────────────────────────────────────────────────
_rag = RAGEngine()
_sm2 = SM2()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILES_PATH = os.path.join(BASE_DIR, 'data', 'profils_etudiants.json')


# ══════════════════════════════════════════════════════════════
# IMPLÉMENTATION DES OUTILS (fonctions Python pures, testables)
# ══════════════════════════════════════════════════════════════

def search_ressources_rag_impl(query: str, n_results: int = 3) -> list:
    """Recherche RAG via le moteur de Dodo."""
    return _rag.chercher_ressources(query)[:n_results]


def compute_sm2_schedule_impl(etudiant: str, notion: str, qualite: int) -> dict:
    """Calcul SM-2 (répétition espacée)."""
    return _sm2.calculer(etudiant, notion, qualite)


def update_profile_ltm_impl(etudiant: str, updates: dict) -> dict:
    """Persistance long-terme du profil étudiant."""
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

    return {"status": "saved", "etudiant": etudiant,
            "fields_updated": list(updates.keys())}


# ══════════════════════════════════════════════════════════════
# EXPOSITION VIA MCP (si disponible)
# ══════════════════════════════════════════════════════════════

if MCP_AVAILABLE:
    mcp = FastMCP("learning-tools-server")

    @mcp.tool()
    def search_ressources_rag(query: str, n_results: int = 3) -> list:
        """Search learning resources via RAG (vector + keyword similarity).
        Use this when an agent needs pedagogical content for a given concept.

        Args:
            query: concept to search (e.g., "Communication Inter-agents")
            n_results: maximum number of resources to return
        Returns:
            List of dicts with {type, description, url, source, contenu}.
        """
        return search_ressources_rag_impl(query, n_results)

    @mcp.tool()
    def compute_sm2_schedule(etudiant: str, notion: str, qualite: int) -> dict:
        """Compute next review date using SuperMemo-2 algorithm.
        Use this when scheduling a future review for a learned concept.

        Args:
            etudiant: student identifier
            notion: concept name
            qualite: response quality 0-5 (0=forgot, 5=perfect)
        Returns:
            Dict with {intervalle_jours, prochaine_revision, facteur_facilite, repetitions}.
        """
        return compute_sm2_schedule_impl(etudiant, notion, qualite)

    @mcp.tool()
    def update_profile_ltm(etudiant: str, updates: dict) -> dict:
        """Update student long-term memory profile (persistent storage).
        Use this when the Tracker needs to save session results.

        Args:
            etudiant: student identifier
            updates: dict of fields to update (e.g., {"last_module": "MSA"})
        Returns:
            Dict with {status, etudiant, fields_updated}.
        """
        return update_profile_ltm_impl(etudiant, updates)


# ══════════════════════════════════════════════════════════════
# ENTRY POINT — lance le serveur en mode stdio
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if MCP_AVAILABLE:
        print("[MCP] Démarrage du serveur learning-tools-server (transport=stdio)")
        mcp.run(transport="stdio")
    else:
        print("[FALLBACK] Test des outils en local (sans MCP) :\n")
        print("--- search_ressources_rag('Communication Inter-agents') ---")
        results = search_ressources_rag_impl("Communication Inter-agents", 2)
        for r in results:
            print(f"  • [{r.get('type')}] {r.get('source', 'n/a')}")
        print("\n--- compute_sm2_schedule('Othmane', 'Agents', 4) ---")
        print(compute_sm2_schedule_impl("Othmane", "Agents Intelligents", 4))
        print("\n--- update_profile_ltm('Othmane', {'last_module': 'MSA'}) ---")
        print(update_profile_ltm_impl("Othmane", {"last_module": "MSA"}))

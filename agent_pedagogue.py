# Agent Pédagogue — sélection de ressources via RAG vectoriel (Chroma + embeddings)
# Utilise multilingual-MiniLM (384 dim) pour une recherche sémantique,
# avec fallback automatique sur recherche par mot-clé si Chroma est indisponible.
from rag_engine import RAGEngine


class AgentPedagogue:

    def __init__(self):
        self.rag = RAGEngine()

    def chercher_ressources(self, notion: str) -> list:
        """Recherche les ressources les plus proches sémantiquement de la notion cible."""
        return self.rag.chercher_ressources(notion)


if __name__ == "__main__":
    agent = AgentPedagogue()
    resultats = agent.chercher_ressources("LangGraph")
    print(f"Ressources trouvées : {len(resultats)}")
    for r in resultats[:3]:
        print(f"  - {r.get('source', '?')} : {r.get('contenu', '')[:80]}...")

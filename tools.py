# Body Layer — outils LangChain (@tool) exposés aux agents
# Le LLM les appelle via bind_tools() selon le pattern ReAct (Reason + Act)
from langchain_core.tools import tool

from agent_pedagogue import AgentPedagogue
from agent_coach import AgentCoach
from agent_tracker import AgentTracker
from diagnostician import AgentDiagnostician

_pedagogue     = AgentPedagogue()
_coach         = AgentCoach()
_tracker       = AgentTracker()
_diagnosticien = AgentDiagnostician()


@tool
def outil_diagnostic(module: str, score_initial: int) -> dict:
    """Evalue le niveau d'un étudiant sur un module et identifie ses lacunes.

    Args:
        module: MSA, Data Mining, Deep Learning, Data Warehouse ou Big Data
        score_initial: estimation du niveau en pourcentage (0-100)
    """
    profil = {"nom": "Etudiant", "score_initial": score_initial, "historique": []}
    rapport = _diagnosticien.run_diagnostic_for_profile(module, profil)
    return rapport or {"erreur": f"Module '{module}' introuvable."}


@tool
def outil_rag_ressources(notion: str, n_resultats: int = 3) -> list:
    """Recherche les ressources pédagogiques les plus pertinentes pour une notion.
    Utilise une recherche vectorielle Chroma (embeddings 384 dim, similarité cosine).

    Args:
        notion: concept à rechercher (ex: "LangGraph", "K-Means Clustering")
        n_resultats: nombre de résultats à retourner
    """
    return _pedagogue.chercher_ressources(notion)[:n_resultats]


@tool
def outil_sm2_revision(etudiant: str, notion: str, qualite: int) -> dict:
    """Calcule la prochaine date de révision via SuperMemo-2.

    Args:
        etudiant: identifiant de l'étudiant
        notion: concept à réviser
        qualite: qualité de réponse de 0 (oublié) à 5 (parfait)
    """
    return _coach.calculer_revision(etudiant, notion, qualite)


@tool
def outil_tracker_sauver(nom: str, notion: str, score: int) -> str:
    """Sauvegarde la progression de l'étudiant en mémoire long-terme.

    Args:
        nom: nom de l'étudiant
        notion: notion travaillée
        score: score de qualité SM-2 (0-5)
    """
    return _tracker.sauver_progres(nom, notion, score)


TOUS_LES_OUTILS = [
    outil_diagnostic,
    outil_rag_ressources,
    outil_sm2_revision,
    outil_tracker_sauver,
]


if __name__ == "__main__":
    print("Tools disponibles :")
    for t in TOUS_LES_OUTILS:
        print(f"  @tool {t.name}")

    print("\n--- Test outil_rag_ressources ---")
    res = outil_rag_ressources.invoke({"notion": "LangGraph", "n_resultats": 2})
    print(f"  {len(res)} ressource(s) trouvée(s)")

    print("\n--- Test outil_sm2_revision ---")
    sm2 = outil_sm2_revision.invoke({"etudiant": "othmane", "notion": "LangGraph", "qualite": 4})
    print(f"  Prochaine révision : {sm2.get('prochaine_revision')}")

"""PARTIE III-B — Code expliqué : learning_tools_server, diagnostician, orchestrator"""

def build(g):
    # ═══════════════════════════════════════════════════════
    # CHAPITRE 13 — learning_tools_server.py
    # ═══════════════════════════════════════════════════════
    g.section_header("13", "Code expliqué : learning_tools_server.py")

    g.p("Ce module implémente le <b>serveur MCP</b> qui expose les outils utilisés "
        "par les agents. Conforme au Chapitre 6 du cours (FastMCP + @mcp.tool).")

    g.h2("13.1 Import avec fallback gracieux")

    g.code_block("""try:
    from mcp.server.fastmcp import FastMCP
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("[WARN] Le package mcp n'est pas installé.")
    print("       Le serveur tournera en mode dégradé.")""")

    g.explain("Si le package <i>mcp</i> n'est pas installé, on peut quand même appeler "
              "les fonctions implémentation en direct. Cela permet de tester le code "
              "sans MCP installé.")

    g.h2("13.2 Instances partagées (chargées une fois)")

    g.code_block("""# Instances partagées (initialisées une seule fois au démarrage)
_rag = RAGEngine()
_sm2 = SM2()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILES_PATH = os.path.join(BASE_DIR, 'data', 'profils_etudiants.json')""")

    g.callout("Pourquoi des instances globales ?",
        "Le serveur MCP tourne dans un sous-processus persistent. Les instances "
        "<b>_rag</b> et <b>_sm2</b> sont créées UNE SEULE FOIS au démarrage du serveur "
        "(coût ~5s pour charger les embeddings). Toutes les requêtes suivantes les "
        "réutilisent (coût ~0.1s). Sans ce pattern, on recoderait l'embedding model à "
        "chaque appel.",
        color=g.ACCENT)

    g.h2("13.3 Les 3 outils MCP — implémentations Python pures")

    g.code_block("""def search_ressources_rag_impl(query: str, n_results: int = 3) -> list:
    \"\"\"Recherche RAG via le moteur de Dodo.\"\"\"
    return _rag.chercher_ressources(query)[:n_results]


def compute_sm2_schedule_impl(etudiant: str, notion: str, qualite: int) -> dict:
    \"\"\"Calcul SM-2 (répétition espacée).\"\"\"
    return _sm2.calculer(etudiant, notion, qualite)


def update_profile_ltm_impl(etudiant: str, updates: dict) -> dict:
    \"\"\"Persistance long-terme du profil étudiant.\"\"\"
    profils = {}
    if os.path.exists(PROFILES_PATH):
        with open(PROFILES_PATH, 'r', encoding='utf-8') as f:
            profils = json.load(f)

    if etudiant not in profils:
        profils[etudiant] = {"created_at": datetime.now().isoformat()}

    profils[etudiant].update(updates)
    profils[etudiant]["updated_at"] = datetime.now().isoformat()

    os.makedirs(os.path.dirname(PROFILES_PATH), exist_ok=True)
    with open(PROFILES_PATH, 'w', encoding='utf-8') as f:
        json.dump(profils, f, ensure_ascii=False, indent=2)

    return {"status": "saved", "etudiant": etudiant,
            "fields_updated": list(updates.keys())}""")

    g.h3("Pattern : séparer impl et exposition MCP")

    g.p("On définit les fonctions <i>_impl</i> en Python pur, puis on les expose via "
        "<b>@mcp.tool()</b> dans un bloc conditionnel. Cela permet :")
    g.bullet([
        "<b>Testabilité</b> : appeler <i>search_ressources_rag_impl()</i> directement "
        "dans les tests pytest, sans démarrer MCP",
        "<b>Réutilisabilité</b> : utiliser ces fonctions dans l'orchestrateur sans "
        "passer par MCP (gain de performance)",
        "<b>Fallback</b> : si MCP_AVAILABLE est False, on a quand même les fonctions",
    ])

    g.h2("13.4 Exposition via @mcp.tool")

    g.code_block("""if MCP_AVAILABLE:
    mcp = FastMCP("learning-tools-server")

    @mcp.tool()
    def search_ressources_rag(query: str, n_results: int = 3) -> list:
        \"\"\"Search learning resources via RAG (vector + keyword similarity).
        Use this when an agent needs pedagogical content for a given concept.

        Args:
            query: concept to search (e.g., "Communication Inter-agents")
            n_results: maximum number of resources to return
        Returns:
            List of dicts with {type, description, url, source, contenu}.
        \"\"\"
        return search_ressources_rag_impl(query, n_results)""")

    g.callout("Importance des docstrings",
        "<b>La docstring est l'API publique vue par le LLM côté client MCP.</b> "
        "Quand un agent doit décider \"dois-je appeler search_ressources_rag ?\", "
        "il lit cette docstring. Elle doit donc être : (1) précise sur QUE fait l'outil, "
        "(2) explicite sur QUAND l'utiliser, (3) claire sur les ARGS et RETURNS.",
        color=g.ACCENT)

    g.h2("13.5 Entry point — démarrage du serveur")

    g.code_block("""if __name__ == "__main__":
    if MCP_AVAILABLE:
        print("[MCP] Démarrage du serveur learning-tools-server (transport=stdio)")
        mcp.run(transport="stdio")
    else:
        print("[FALLBACK] Test des outils en local (sans MCP) :\\n")
        print("--- search_ressources_rag('Communication Inter-agents') ---")
        results = search_ressources_rag_impl("Communication Inter-agents", 2)
        # ... affichage des résultats""")

    g.explain("En mode MCP, le serveur démarre en stdio et attend des requêtes JSON-RPC. "
              "En mode fallback, on teste les fonctions implementation directement "
              "(utile pour debug et CI).")

    g.pagebreak()

    # ═══════════════════════════════════════════════════════
    # CHAPITRE 14 — diagnostician.py modifications
    # ═══════════════════════════════════════════════════════
    g.section_header("14", "Code expliqué : diagnostician.py (modifications O5)")

    g.p("Le fichier <i>diagnostician.py</i> original utilisait <i>input()</i> ce qui "
        "le rendait incompatible avec Streamlit. La tâche O5 a ajouté deux méthodes "
        "state-based : <b>run_diagnostic_for_profile</b> et <b>run_diagnostic_with_answers</b>.")

    g.h2("14.1 La méthode run_diagnostic_for_profile")

    g.code_block("""def run_diagnostic_for_profile(self, module, profile):
    \"\"\"
    Diagnostic basé sur un profil pré-défini (Amina, Yassine, Sarah).
    Pas d'interaction — utilise profile['historique'] et score_initial.

    Args:
        module: nom du module à diagnostiquer
        profile: dict du profil (data/profils_demo.json)

    Returns:
        Rapport au même format que run_diagnostic() (mais sans input()).
    \"\"\"
    notions = self._get_notions(module)
    if not notions:
        return None

    # Construire les ensembles à partir de l'historique du profil
    historique = {h['notion']: h['maitrise'] for h in profile.get('historique', [])}
    score_initial = profile.get('score_initial', 50)

    # Calculer mastery par notion (du module courant)
    notions_maitrisees = []
    lacunes = []
    resultats = {}

    for notion_info in notions:
        label = notion_info['label']
        # Si dans l'historique, prendre la valeur explicite
        if label in historique:
            maitrise = historique[label]
        else:
            # Sinon, déduire du score initial + niveau
            niveau = notion_info.get('niveau', 1)
            if score_initial >= 80:
                maitrise = True
            elif score_initial >= 50:
                maitrise = (niveau <= 2)
            else:
                maitrise = False

        resultats[label] = 1 if maitrise else 0
        if maitrise:
            notions_maitrisees.append(label)
        else:
            lacunes.append(label)
    # ... suite : calcul du score, retour du rapport""")

    g.h3("Algorithme de décision")

    g.p("Pour chaque notion du module, on décide si l'étudiant la maîtrise :")
    g.bullet([
        "<b>Si la notion est dans <i>historique</i></b> : on prend la valeur explicite",
        "<b>Sinon, on déduit du score initial</b> :",
        "&nbsp;&nbsp;&nbsp;&nbsp;score ≥ 80% → maîtrise tout (niveau avancé)",
        "&nbsp;&nbsp;&nbsp;&nbsp;score ≥ 50% → maîtrise niveau 1 et 2 seulement",
        "&nbsp;&nbsp;&nbsp;&nbsp;score &lt; 50% → maîtrise rien (débutant)",
    ])

    g.callout("Pourquoi cette logique de déduction ?",
        "Le profile JSON contient un <b>score_initial</b> indicatif. À partir de ce "
        "score, on doit déduire QUELLES notions sont maîtrisées. La règle "
        "\"plus on est avancé, plus on maîtrise haut dans la hiérarchie\" est "
        "cohérente avec la théorie de la <b>Zone Proximale de Développement</b> "
        "(Vygotski).",
        color=g.ACCENT)

    g.h2("14.2 La méthode run_diagnostic_with_answers")

    g.code_block("""def run_diagnostic_with_answers(self, module, nom_etudiant, answers):
    \"\"\"
    Variante state-based pour Streamlit (questionnaire interactif).

    Args:
        module: nom du module
        nom_etudiant: nom de l'étudiant
        answers: dict {notion_label: index_reponse_choisie}
    \"\"\"
    notions = self._get_notions(module)
    if not notions:
        return None

    resultats = {}
    lacunes = []
    notions_maitrisees = []
    niveau_actuel = "facile"
    niveaux = ["facile", "moyen", "difficile"]

    for notion_info in notions:
        notion = notion_info['label']
        q = self._get_questions(module, notion, niveau_actuel) \\
            or self._get_questions(module, notion, "facile")
        if not q:
            continue

        reponse = answers.get(notion, -1)
        correct = (reponse == q['reponse'])
        resultats[notion] = 1 if correct else 0

        if correct:
            notions_maitrisees.append(notion)
            idx = niveaux.index(niveau_actuel)
            if idx < len(niveaux) - 1:
                niveau_actuel = niveaux[idx + 1]
        else:
            lacunes.append(notion)
            niveau_actuel = "facile"
    # ... suite""")

    g.h3("L'algorithme adaptatif")

    g.p("Cette méthode implémente un <b>test adaptatif</b> simplifié inspiré de l'IRT "
        "(Item Response Theory) :")

    g.code_block("""niveau_actuel = "facile"  # on commence facile

Pour chaque notion :
    1. Récupérer la question au niveau actuel
    2. Lire la réponse de l'étudiant (depuis le dict answers)
    3. Si correcte :
       → ajouter aux maîtrisées
       → MONTER au niveau supérieur (facile → moyen → difficile)
    4. Si incorrecte :
       → ajouter aux lacunes
       → REDESCENDRE au niveau "facile" (revenir aux prérequis)""")

    g.callout("Pourquoi adaptatif ?",
        "Un test linéaire (toutes les questions au même niveau) ne distingue pas un "
        "débutant d'un avancé. L'adaptatif : (1) bonne réponse → on durcit, "
        "(2) mauvaise réponse → on redescend. Utilisé dans Duolingo, TOEFL adaptatif. "
        "<b>Convergence en moins de questions qu'un test fixe.</b>",
        color=g.SUCCESS)

    g.pagebreak()

    # ═══════════════════════════════════════════════════════
    # CHAPITRE 15 — orchestrator.py (le cœur)
    # ═══════════════════════════════════════════════════════
    g.section_header("15", "Code expliqué : orchestrator.py — le cœur du système")

    g.p("Le fichier <i>orchestrator.py</i> est <b>la pièce centrale du projet</b>. "
        "Il définit le State partagé, les 5 nodes, les edges, et le routage conditionnel. "
        "Conforme au Chapitre 5 du cours (LangGraph).")

    g.h2("15.1 Les imports")

    g.code_block("""from typing import Annotated, TypedDict, Literal
from datetime import datetime
from operator import add  # reducer pour les listes
import os
import json

# LangGraph (avec fallback gracieux)
try:
    from langgraph.graph import StateGraph, START, END
    from langgraph.graph.message import add_messages
    from langgraph.checkpoint.memory import InMemorySaver
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    START = "__start__"
    END = "__end__"
    def add_messages(left, right):
        return (left or []) + (right or [])

# Agents existants
from diagnostician import AgentDiagnostician
from planner import AgentPlanificateur
from rag_engine import RAGEngine
from sm2 import SM2
from agents_dodo import AgentTracker
from a2a_protocol import (
    create_a2a_msg, format_timeline_text,
    REQUEST, INFORM, QUERY, CONFIRM, FAILURE
)
from mind_layer import reason_planificateur, LLM_PROVIDER""")

    g.explain("Le double pattern try/except pour LangGraph permet au code de tourner "
              "<b>même si LangGraph n'est pas installé</b>. Dans ce cas, on utilise un "
              "fallback Python pur qui simule le comportement du graphe (cf. "
              "<i>run_session_fallback</i>).")

    g.h2("15.2 Le State (TypedDict)")

    g.code_block("""class LearningState(TypedDict):
    \"\"\"État partagé entre tous les agents du SMA.

    Référence cours : Chapitre 5 LangGraph — TypedDict avec reducer add_messages.
    Chaque champ correspond à une responsabilité d'un agent (séparation des préoccupations).
    \"\"\"
    # Identité de la session
    nom_etudiant: str
    module: str
    profile_data: dict             # profil de démo (Amina / Yassine / Sarah)

    # Messages conversationnels (avec reducer)
    messages: Annotated[list, add_messages]

    # Résultats remplis par chaque agent (un champ = un agent)
    diagnostic: dict               # rempli par Diagnosticien
    parcours: list                 # rempli par Planificateur
    raisonnement: str              # Mind layer — CoT du LLM
    ressources: list               # rempli par Pédagogue (via RAG)
    revision: dict                 # rempli par Coach (via SM-2)
    profile_saved: dict            # rempli par Tracker

    # Journal A2A — communications inter-agents (FIPA-ACL)
    # Reducer `add` pour ACCUMULER les messages (sinon chaque node remplace)
    communications: Annotated[list, add]""")

    g.h3("Analyse champ par champ")

    g.table_grid(
        ["Champ", "Type", "Qui le remplit", "Pourquoi ce nom"],
        [
            ["nom_etudiant", "str", "Initialisation", "Identifie qui passe le diagnostic"],
            ["module", "str", "Initialisation", "Module ciblé (MSA, DM, ...)"],
            ["profile_data", "dict", "Initialisation", "Profil de démo pour test"],
            ["messages", "Annotated[list, add_messages]", "LangGraph",
             "Historique conversationnel (extensible LLM)"],
            ["diagnostic", "dict", "Diagnosticien", "Score, lacunes, notions maîtrisées"],
            ["parcours", "list", "Planificateur", "Liste ordonnée des étapes"],
            ["raisonnement", "str", "Mind layer", "Texte CoT généré par LLM"],
            ["ressources", "list", "Pédagogue", "Top-K résultats RAG"],
            ["revision", "dict", "Coach", "Prochaine date + intervalle SM-2"],
            ["profile_saved", "dict", "Tracker", "Confirmation persistance"],
            ["communications", "Annotated[list, add]", "Tous les nodes", "Journal A2A (reducer add)"],
        ],
        col_widths=[3*g.cm, 4*g.cm, 3*g.cm, 7*g.cm])

    g.callout("Choix crucial : Annotated[list, add]",
        "Sans le reducer <b>add</b>, chaque node REMPLACERAIT le champ "
        "<i>communications</i> par les 2 nouveaux messages qu'il génère. "
        "Avec le reducer, ils s'ACCUMULENT. Résultat : <b>11 messages totaux</b> "
        "pour une session complète, et non 2 (les derniers).",
        color=g.ACCENT)

    g.h2("15.3 Le node Diagnosticien")

    g.code_block("""def diagnosticien_node(state: LearningState) -> dict:
    \"\"\"Node Diagnosticien — lance le test adaptatif et identifie les lacunes.\"\"\"
    cid = state.get("communications") and state["communications"][0]["conversation_id"] \\
          or CONVERSATION_ID

    # Message A2A entrant (Orchestrateur → Diagnosticien)
    req = create_a2a_msg(
        sender="Orchestrateur", receiver="Diagnosticien",
        performative=REQUEST,
        content={"action": "run_diagnostic", "module": state["module"]},
        conversation_id=cid
    )

    # Appel de l'agent
    profile = state.get("profile_data") or {
        "nom": state["nom_etudiant"], "score_initial": 50, "historique": []
    }
    rapport = _diagnosticien.run_diagnostic_for_profile(state["module"], profile)

    # Message A2A sortant (Diagnosticien → Orchestrateur)
    reply = create_a2a_msg(
        sender="Diagnosticien", receiver="Orchestrateur",
        performative=INFORM,
        content={
            "score": rapport["pourcentage"],
            "lacunes": rapport["lacunes"],
            "notion_cible": rapport["notion_cible"]
        },
        conversation_id=cid
    )

    return {
        "diagnostic": rapport,
        "communications": [req, reply]
    }""")

    g.h3("Décortication étape par étape")

    g.bullet([
        "<b>cid (conversation_id)</b> : récupéré depuis le premier message du journal "
        "(envoyé par <i>run_session</i>). Permet de grouper TOUS les messages d'une session.",
        "<b>Création du message REQUEST</b> : avant l'appel à l'agent. Performative "
        "FIPA-ACL = REQUEST car on demande une action.",
        "<b>Profile fallback</b> : si pas de profil fourni, on construit un profil "
        "neutre (score 50%, pas d'historique).",
        "<b>Appel de l'agent</b> : <i>run_diagnostic_for_profile</i> (méthode O5 sans input).",
        "<b>Création du message INFORM</b> : après l'appel. Contenu = résumé du résultat.",
        "<b>Return dict partiel</b> : seuls <i>diagnostic</i> et <i>communications</i> "
        "sont mis à jour. LangGraph fusionne avec le reducer.",
    ])

    g.h2("15.4 Le node Planificateur (avec Mind Layer)")

    g.code_block("""def planificateur_node(state: LearningState) -> dict:
    \"\"\"Node Planificateur — construit le parcours (CoT + SM-2).\"\"\"
    cid = state["communications"][0]["conversation_id"]

    req = create_a2a_msg(
        "Orchestrateur", "Planificateur", REQUEST,
        {"action": "build_parcours",
         "lacunes": state["diagnostic"]["lacunes"]},
        conversation_id=cid
    )

    rapport = _planificateur.construire_parcours(
        module=state["module"],
        lacunes=state["diagnostic"]["lacunes"],
        notions_maitrisees=state["diagnostic"]["notions_maitrisees"],
        nom_etudiant=state["nom_etudiant"]
    )

    # ─── Mind Layer (LLM ou fallback déterministe) ───
    # Chain-of-Thought : faire raisonner le LLM sur le parcours
    raisonnement = reason_planificateur(state["diagnostic"], rapport.get("parcours", []))

    reply = create_a2a_msg(
        "Planificateur", "Orchestrateur", INFORM,
        {"nb_etapes": len(rapport.get("parcours", [])),
         "duree_h": rapport.get("resume", {}).get("duree_totale_h", 0),
         "llm_provider": LLM_PROVIDER},
        conversation_id=cid
    )

    return {
        "parcours": rapport.get("parcours", []),
        "raisonnement": raisonnement,
        "communications": [req, reply]
    }""")

    g.explain("Ce node fait 3 choses : (1) construit le parcours via planner.py, "
              "(2) génère un <b>raisonnement CoT</b> via mind_layer (LLM réel ou "
              "fallback), (3) journalise les messages A2A. Le champ <i>llm_provider</i> "
              "dans le message INFORM permet au jury de voir quelle source de LLM "
              "a été utilisée.")

    g.h2("15.5 La fonction de routage (conditional edge)")

    g.code_block("""def route_after_diagnostic(state: LearningState) -> Literal["planificateur", "coach"]:
    \"\"\"Routage conditionnel après le diagnostic.

    SI score ≥ 80% → l'étudiant est avancé → on saute Planificateur et Pédagogue
                     et on va direct au Coach (révision seule).
    SINON         → parcours complet : Planificateur → Pédagogue → Coach.

    C'est la démonstration la plus visible de la supériorité LangGraph vs LangChain.
    \"\"\"
    pourcentage = state.get("diagnostic", {}).get("pourcentage", 0)
    if pourcentage >= 80:
        return "coach"
    return "planificateur"
""")

    g.callout("Pourquoi 80% et pas 70% ou 90% ?",
        "Le seuil 80% est un <b>compromis pédagogique</b> : (1) suffisamment haut pour "
        "qu'un étudiant qui le franchit soit vraiment avancé, (2) suffisamment bas pour "
        "que la conditional edge se déclenche en démo (Sarah avec score 100% le franchit). "
        "En production, ce seuil serait paramétrable par l'enseignant.",
        color=g.ACCENT)

    g.h2("15.6 Construction du graphe")

    g.code_block("""def build_graph():
    \"\"\"Construit et compile le graphe LangGraph.\"\"\"
    workflow = StateGraph(LearningState)

    # Ajout des nodes
    workflow.add_node("diagnosticien", diagnosticien_node)
    workflow.add_node("planificateur", planificateur_node)
    workflow.add_node("pedagogue", pedagogue_node)
    workflow.add_node("coach", coach_node)
    workflow.add_node("tracker", tracker_node)

    # Edge de départ
    workflow.add_edge(START, "diagnosticien")

    # Conditional edge — cœur de l'orchestration
    workflow.add_conditional_edges(
        "diagnosticien",
        route_after_diagnostic,
        {
            "planificateur": "planificateur",
            "coach": "coach"
        }
    )

    # Edges fixes (chemin "parcours complet")
    workflow.add_edge("planificateur", "pedagogue")
    workflow.add_edge("pedagogue", "coach")

    # Le coach mène toujours au tracker
    workflow.add_edge("coach", "tracker")
    workflow.add_edge("tracker", END)

    # Compilation avec checkpointer pour la mémoire de session
    return workflow.compile(checkpointer=InMemorySaver())""")

    g.h3("Décomposition étape par étape")

    g.bullet([
        "<b>StateGraph(LearningState)</b> : crée le graphe avec le schéma d'état",
        "<b>add_node(\"nom\", fonction)</b> : enregistre chaque agent comme node",
        "<b>add_edge(START, \"diagnosticien\")</b> : entry point fixe",
        "<b>add_conditional_edges</b> : LA décision dynamique selon le state",
        "<b>add_edge(\"planificateur\", \"pedagogue\")</b> : edge fixe (chemin complet)",
        "<b>add_edge(\"coach\", \"tracker\")</b> : convergence des deux branches",
        "<b>workflow.compile(checkpointer=InMemorySaver())</b> : compilation finale "
        "avec mémoire en RAM",
    ])

    g.h2("15.7 La fonction run_session (API publique)")

    g.code_block("""def run_session(nom: str, module: str, profile: dict = None) -> dict:
    \"\"\"Lance une session complète d'apprentissage adaptatif.\"\"\"
    if LANGGRAPH_AVAILABLE:
        graph = build_graph()
        cid = f"{nom}-{module}-{datetime.now().strftime('%H%M%S')}"
        init_msg = create_a2a_msg(
            "User", "Orchestrateur", REQUEST,
            {"action": "start_session"},
            conversation_id=cid
        )
        result = graph.invoke(
            input={
                "nom_etudiant": nom,
                "module": module,
                "profile_data": profile or {},
                "messages": [],
                "diagnostic": {},
                "parcours": [],
                "raisonnement": "",
                "ressources": [],
                "revision": {},
                "profile_saved": {},
                "communications": [init_msg]
            },
            config={"configurable": {"thread_id": cid}}
        )
        return result
    else:
        print("[Orchestrateur] LangGraph absent — mode fallback Python pur.")
        return run_session_fallback(nom, module, profile)""")

    g.explain("<b>thread_id</b> = conversation_id : même identifiant pour grouper les "
              "messages A2A ET pour le checkpointing LangGraph. Si on relance avec le "
              "même thread_id, on reprend la session précédente (mémoire conversationnelle).")

    g.pagebreak()

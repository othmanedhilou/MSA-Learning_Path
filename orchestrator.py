"""
ORCHESTRATEUR LANGGRAPH — cœur du SMA
══════════════════════════════════════════════════════════════════

Réf. cours :
  • Chapitre 3 — Agentic AI (Mind/Body/Memory)
  • Chapitre 4 — SMA & A2A (FIPA-ACL)
  • Chapitre 5 — LangGraph (State / Nodes / Edges / Conditional)
  • Chapitre 5 — MCP (Model Context Protocol)

Architecture :

           ┌─────────┐
           │  START  │
           └────┬────┘
                ▼
       ┌────────────────┐
       │  Diagnosticien │
       └────────┬───────┘
                │
         ╔══════╧══════╗
         ║ Conditional ║   ← LangGraph add_conditional_edges
         ╚══════╤══════╝
       ≥80%    │    <80%
       ▼              ▼
   ┌───────┐    ┌──────────────┐
   │ Coach │    │ Planificateur│
   │direct │    └──────┬───────┘
   └───┬───┘           ▼
       │       ┌──────────────┐
       │       │  Pédagogue   │
       │       │  (RAG / MCP) │
       │       └──────┬───────┘
       │              ▼
       │       ┌──────────────┐
       │       │    Coach     │
       │       └──────┬───────┘
       └──────────┬───┘
                  ▼
            ┌──────────┐
            │ Tracker  │
            └─────┬────┘
                  ▼
              ┌───────┐
              │  END  │
              └───────┘

Le State est partagé entre tous les nodes (pattern Blackboard).
Communication inter-agents tracée via le protocole A2A (FIPA-ACL).
"""
from typing import Annotated, TypedDict, Literal
from datetime import datetime
from operator import add
import os
import json

# ──────────────────────────────────────────────────────────────
# Imports LangGraph — avec fallback gracieux si non installé
# ──────────────────────────────────────────────────────────────
try:
    from langgraph.graph import StateGraph, START, END
    from langgraph.graph.message import add_messages
    from langgraph.checkpoint.memory import InMemorySaver
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    # Fallback minimal : on définit START/END comme constantes
    # add_messages devient un identity reducer
    START = "__start__"
    END = "__end__"
    def add_messages(left, right):
        return (left or []) + (right or [])

# ──────────────────────────────────────────────────────────────
# Imports des agents existants (équipe)
# ──────────────────────────────────────────────────────────────
from diagnostician import AgentDiagnostician
from planner import AgentPlanificateur
from rag_engine import RAGEngine
from sm2 import SM2
from agents_dodo import AgentTracker
from a2a_protocol import (
    create_a2a_msg, format_timeline_text,
    REQUEST, INFORM, QUERY, CONFIRM, FAILURE
)
from mind_layer import reason_planificateur, LLM_PROVIDER


# ══════════════════════════════════════════════════════════════
# STATE — le tableau blanc partagé (Blackboard pattern + TypedDict cours)
# ══════════════════════════════════════════════════════════════

class LearningState(TypedDict):
    """État partagé entre tous les agents du SMA.

    Référence cours : Chapitre 5 LangGraph — TypedDict avec reducer add_messages.
    Chaque champ correspond à une responsabilité d'un agent (séparation des préoccupations).
    """
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
    communications: Annotated[list, add]


# ══════════════════════════════════════════════════════════════
# INSTANCES GLOBALES (chargées une seule fois)
# ══════════════════════════════════════════════════════════════

_diagnosticien = AgentDiagnostician()
_planificateur = AgentPlanificateur()
_rag = RAGEngine()
_sm2 = SM2()
_tracker = AgentTracker()

CONVERSATION_ID = "default-session"


# ══════════════════════════════════════════════════════════════
# NODES — un par agent (Tâche O3)
# ══════════════════════════════════════════════════════════════

def diagnosticien_node(state: LearningState) -> dict:
    """Node Diagnosticien — lance le test adaptatif et identifie les lacunes."""
    cid = state.get("communications") and state["communications"][0]["conversation_id"] or CONVERSATION_ID

    # Message A2A entrant
    req = create_a2a_msg(
        sender="Orchestrateur", receiver="Diagnosticien",
        performative=REQUEST,
        content={"action": "run_diagnostic", "module": state["module"]},
        conversation_id=cid
    )

    # Appel de l'agent
    profile = state.get("profile_data") or {"nom": state["nom_etudiant"], "score_initial": 50, "historique": []}
    rapport = _diagnosticien.run_diagnostic_for_profile(state["module"], profile)

    # Message A2A sortant
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
    }


def planificateur_node(state: LearningState) -> dict:
    """Node Planificateur — construit le parcours d'apprentissage (CoT + SM-2)."""
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
    }


def pedagogue_node(state: LearningState) -> dict:
    """Node Pédagogue — sélectionne les ressources via RAG (Chapitre 2 du cours)."""
    cid = state["communications"][0]["conversation_id"]
    notion_cible = state["diagnostic"]["notion_cible"]

    req = create_a2a_msg(
        "Orchestrateur", "Pedagogue", QUERY,
        {"query": notion_cible}, conversation_id=cid
    )

    ressources = _rag.chercher_ressources(notion_cible)

    reply = create_a2a_msg(
        "Pedagogue", "Orchestrateur", INFORM,
        {"nb_ressources": len(ressources),
         "sources": [r.get("source", "?") for r in ressources[:3]]},
        conversation_id=cid
    )

    return {
        "ressources": ressources,
        "communications": [req, reply]
    }


def coach_node(state: LearningState) -> dict:
    """Node Coach — calcule la prochaine révision (SM-2)."""
    cid = state["communications"][0]["conversation_id"]
    notion_cible = state["diagnostic"]["notion_cible"]
    score = state["diagnostic"]["pourcentage"]
    # Conversion score % → qualité SM-2 (0-5)
    qualite = min(5, max(0, score // 20))

    req = create_a2a_msg(
        "Orchestrateur", "Coach", REQUEST,
        {"action": "schedule_review",
         "notion": notion_cible, "qualite": qualite},
        conversation_id=cid
    )

    res_sm2 = _sm2.calculer(state["nom_etudiant"], notion_cible, qualite)

    reply = create_a2a_msg(
        "Coach", "Orchestrateur", INFORM,
        {"intervalle_jours": res_sm2["intervalle_jours"],
         "prochaine_revision": res_sm2["prochaine_revision"]},
        conversation_id=cid
    )

    return {
        "revision": res_sm2,
        "communications": [req, reply]
    }


def tracker_node(state: LearningState) -> dict:
    """Node Tracker — sauvegarde la session (mémoire long-terme)."""
    cid = state["communications"][0]["conversation_id"]

    req = create_a2a_msg(
        "Orchestrateur", "Tracker", REQUEST,
        {"action": "save_session"}, conversation_id=cid
    )

    # Sauvegarde via l'AgentTracker existant (équipe Dodo)
    notion = state["diagnostic"]["notion_cible"]
    score = state["diagnostic"]["pourcentage"] // 20  # 0-5
    _tracker.sauver_progres(state["nom_etudiant"], notion, score)

    # Sauvegarde long-terme (profil)
    saved = {
        "etudiant": state["nom_etudiant"],
        "module": state["module"],
        "score_final": state["diagnostic"]["pourcentage"],
        "notion_cible": notion,
        "prochaine_revision": state.get("revision", {}).get("prochaine_revision"),
        "timestamp": datetime.now().isoformat()
    }
    profils_path = os.path.join(os.path.dirname(__file__),
                                 'data', 'profils_etudiants.json')
    profils = {}
    if os.path.exists(profils_path):
        try:
            with open(profils_path, 'r', encoding='utf-8') as f:
                profils = json.load(f)
        except Exception:
            profils = {}
    profils[state["nom_etudiant"]] = saved
    os.makedirs(os.path.dirname(profils_path), exist_ok=True)
    with open(profils_path, 'w', encoding='utf-8') as f:
        json.dump(profils, f, ensure_ascii=False, indent=2)

    reply = create_a2a_msg(
        "Tracker", "Orchestrateur", CONFIRM,
        {"status": "saved", "path": "data/profils_etudiants.json"},
        conversation_id=cid
    )

    return {
        "profile_saved": saved,
        "communications": [req, reply]
    }


# ══════════════════════════════════════════════════════════════
# CONDITIONAL EDGE — la valeur ajoutée de LangGraph (Tâche O4)
# ══════════════════════════════════════════════════════════════

def route_after_diagnostic(state: LearningState) -> Literal["planificateur", "coach"]:
    """Routage conditionnel après le diagnostic.

    SI score ≥ 80% → l'étudiant est avancé → on saute Planificateur et Pédagogue
                     et on va direct au Coach (révision seule).
    SINON         → parcours complet : Planificateur → Pédagogue → Coach.

    C'est la démonstration la plus visible de la supériorité LangGraph vs LangChain.
    """
    pourcentage = state.get("diagnostic", {}).get("pourcentage", 0)
    if pourcentage >= 80:
        return "coach"
    return "planificateur"


# ══════════════════════════════════════════════════════════════
# CONSTRUCTION DU GRAPHE (Tâche O4)
# ══════════════════════════════════════════════════════════════

def build_graph():
    """Construit et compile le graphe LangGraph."""
    if not LANGGRAPH_AVAILABLE:
        raise ImportError(
            "LangGraph n'est pas installé. Lance : pip install langgraph"
        )

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
    return workflow.compile(checkpointer=InMemorySaver())


# ══════════════════════════════════════════════════════════════
# FALLBACK — exécution manuelle si LangGraph indisponible
# ══════════════════════════════════════════════════════════════

def run_session_fallback(nom: str, module: str, profile: dict = None) -> dict:
    """Exécution séquentielle pure Python (si LangGraph absent)."""
    state = {
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
        "communications": []
    }

    # Init conversation_id
    init_msg = create_a2a_msg(
        "User", "Orchestrateur", REQUEST,
        {"action": "start_session"},
        conversation_id=f"{nom}-{module}-{datetime.now().strftime('%H%M%S')}"
    )
    state["communications"].append(init_msg)

    # 1. Diagnosticien
    out = diagnosticien_node(state)
    state["diagnostic"] = out["diagnostic"]
    state["communications"].extend(out["communications"])

    # 2. Conditional routing
    next_node = route_after_diagnostic(state)

    if next_node == "planificateur":
        out = planificateur_node(state)
        state["parcours"] = out["parcours"]
        state["raisonnement"] = out.get("raisonnement", "")
        state["communications"].extend(out["communications"])

        out = pedagogue_node(state)
        state["ressources"] = out["ressources"]
        state["communications"].extend(out["communications"])

    # Coach (toujours appelé)
    out = coach_node(state)
    state["revision"] = out["revision"]
    state["communications"].extend(out["communications"])

    # Tracker (toujours appelé)
    out = tracker_node(state)
    state["profile_saved"] = out["profile_saved"]
    state["communications"].extend(out["communications"])

    return state


# ══════════════════════════════════════════════════════════════
# API PUBLIQUE — utilisée par app.py
# ══════════════════════════════════════════════════════════════

def run_session(nom: str, module: str, profile: dict = None) -> dict:
    """Lance une session complète d'apprentissage adaptatif.

    Args:
        nom: nom de l'étudiant
        module: module ciblé (MSA, Data Mining, Deep Learning, ...)
        profile: profil de démo optionnel (data/profils_demo.json)

    Returns:
        State final avec diagnostic, parcours, ressources, revision, communications.
    """
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
        return run_session_fallback(nom, module, profile)


def save_graph_diagram(output_path: str = "data/graph_orchestrator.png") -> bool:
    """Génère le diagramme Mermaid du graphe (pour les slides)."""
    if not LANGGRAPH_AVAILABLE:
        return False
    try:
        graph = build_graph()
        png_bytes = graph.get_graph().draw_mermaid_png()
        full_path = os.path.join(os.path.dirname(__file__), output_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "wb") as f:
            f.write(png_bytes)
        print(f"[OK] Diagramme sauvé : {full_path}")
        return True
    except Exception as e:
        print(f"[ERR] Génération diagramme échouée : {e}")
        return False


# ══════════════════════════════════════════════════════════════
# CLI — test rapide
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    # Force UTF-8 sur stdout (Windows console)
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    print("=" * 60)
    print("  ORCHESTRATEUR LANGGRAPH - Test rapide")
    print(f"  LangGraph disponible : {LANGGRAPH_AVAILABLE}")
    print("=" * 60)

    # Charger un profil de démo
    profils_path = os.path.join(os.path.dirname(__file__),
                                 'data', 'profils_demo.json')
    with open(profils_path, 'r', encoding='utf-8') as f:
        profils = json.load(f)["profils"]

    # Tester les 3 profils
    for profile in profils:
        print(f"\n{'-' * 60}")
        print(f"  Profil : {profile['nom']} (score initial {profile['score_initial']}%)")
        print(f"{'-' * 60}")

        result = run_session(profile["nom"], "MSA", profile)

        print(f"\n  Diagnostic : {result['diagnostic']['pourcentage']}% - "
              f"{result['diagnostic']['niveau_global']}")
        print(f"  Lacunes    : {len(result['diagnostic']['lacunes'])} notion(s)")
        print(f"  Parcours   : {len(result.get('parcours', []))} etape(s)")
        print(f"  Ressources : {len(result.get('ressources', []))} document(s)")
        print(f"  Revision   : {result.get('revision', {}).get('prochaine_revision', 'N/A')}")
        print(f"\n  Communications inter-agents (A2A) :")
        print(format_timeline_text(result["communications"]))

# Orchestrateur LangGraph — cœur du SMA
# Gère le graphe d'états, les 5 agents et la communication A2A inter-agents
from typing import Annotated, TypedDict, Literal
from datetime import datetime
from operator import add
import os
import json

# LangGraph avec fallback si non installé
try:
    from langgraph.graph import StateGraph, START, END
    from langgraph.graph.message import add_messages
    from langgraph.checkpoint.memory import InMemorySaver
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    START = "__start__"
    END   = "__end__"
    def add_messages(left, right):
        return (left or []) + (right or [])

from agent_diagnostician import AgentDiagnostician
from agent_planner       import AgentPlanificateur
from agent_pedagogue import AgentPedagogue
from agent_coach     import AgentCoach
from agent_tracker   import AgentTracker
from a2a_protocol    import create_a2a_msg, format_timeline_text, REQUEST, INFORM, QUERY, CONFIRM, FAILURE
from mind_layer      import reason_planificateur, LLM_PROVIDER


# État partagé entre tous les agents — pattern Blackboard de LangGraph
# Chaque agent lit ce dont il a besoin et écrit ses résultats dans son champ dédié
class LearningState(TypedDict):
    nom_etudiant:         str
    module:               str
    profile_data:         dict
    messages:             Annotated[list, add_messages]
    diagnostic:           dict    # rempli par Diagnosticien
    parcours:             list    # rempli par Planificateur
    raisonnement:         str     # CoT du Planificateur (LLM ou fallback)
    raisonnement_diag:    str     # CoT du Diagnosticien
    raisonnement_coach:   str     # CoT du Coach
    raisonnement_tracker: str     # CoT du Tracker
    ressources:           list    # rempli par Pédagogue (RAG)
    revision:             dict    # rempli par Coach (SM-2)
    profile_saved:        dict    # rempli par Tracker
    communications:       Annotated[list, add]  # reducer add pour accumuler les messages A2A


# Instances lazy — créées au premier appel pour ne pas charger le modèle
# embedding en mémoire à chaque import (évite MemoryError sur machines limitées)
_diagnosticien = None
_planificateur = None
_pedagogue     = None
_coach         = None
_tracker       = None

CONVERSATION_ID = "default-session"


def _agents():
    """Initialise les agents au premier appel (singleton par processus)."""
    global _diagnosticien, _planificateur, _pedagogue, _coach, _tracker
    if _diagnosticien is None:
        _diagnosticien = AgentDiagnostician()
        _planificateur = AgentPlanificateur()
        _pedagogue     = AgentPedagogue()
        _coach         = AgentCoach()
        _tracker       = AgentTracker()


# Nodes LangGraph — un node par agent

def diagnosticien_node(state: LearningState) -> dict:
    """Lance le diagnostic ou déclenche une session de révision SM-2 si des notions sont dues."""
    cid = (state.get("communications") or [{}])[0].get("conversation_id", CONVERSATION_ID)
    req = create_a2a_msg("Orchestrateur", "Diagnosticien", REQUEST,
                         {"action": "run_diagnostic", "module": state["module"]},
                         conversation_id=cid)
    try:
        _agents()
        nom = state["nom_etudiant"]

        # Vérifier si des révisions SM-2 sont dues aujourd'hui pour cet étudiant
        planning_sm2 = _coach.get_planning(nom)

        if planning_sm2:
            # Mode révision : des notions sont dues selon SM-2 — priorité sur le diagnostic normal
            notions_dues = [p["notion"] for p in planning_sm2]
            rapport = {
                "etudiant":          nom,
                "module":            state["module"],
                "score":             0,
                "total":             len(notions_dues),
                "pourcentage":       0,
                "notions_maitrisees": [],
                "lacunes":           notions_dues,
                "notion_cible":      notions_dues[0],
                "niveau_global":     "Révision SM-2",
                "raisonnement":      (
                    f"**Mode révision SM-2** : {len(notions_dues)} notion(s) programmée(s) pour aujourd'hui.\n"
                    f"Notions à réviser : {', '.join(notions_dues)}"
                ),
                "mode": "revision"
            }
        else:
            # Mode diagnostic normal
            profile = state.get("profile_data") or {
                "nom": nom, "score_initial": 50, "historique": []
            }
            rapport = _diagnosticien.run_diagnostic_for_profile(state["module"], profile)
            rapport["mode"] = "diagnostic"

        reply = create_a2a_msg("Diagnosticien", "Orchestrateur", INFORM,
                               {"score": rapport["pourcentage"],
                                "lacunes": rapport["lacunes"],
                                "notion_cible": rapport["notion_cible"],
                                "mode": rapport.get("mode", "diagnostic")},
                               conversation_id=cid)
        return {
            "diagnostic":        rapport,
            "raisonnement_diag": rapport.get("raisonnement", ""),
            "communications":    [req, reply]
        }
    except Exception as e:
        failure = create_a2a_msg("Diagnosticien", "Orchestrateur", FAILURE,
                                 {"erreur": str(e)}, conversation_id=cid)
        fallback = {
            "etudiant": state.get("nom_etudiant", "?"), "module": state.get("module", "?"),
            "score": 0, "total": 0, "pourcentage": 0,
            "notions_maitrisees": [], "lacunes": [], "notion_cible": "N/A",
            "niveau_global": "Erreur", "raisonnement": f"Erreur Diagnosticien : {e}", "mode": "error"
        }
        return {"diagnostic": fallback, "raisonnement_diag": "", "communications": [req, failure]}


def planificateur_node(state: LearningState) -> dict:
    """Construit le parcours d'apprentissage ordonné par prérequis, avec SM-2."""
    cid = state["communications"][0]["conversation_id"]
    req = create_a2a_msg("Orchestrateur", "Planificateur", REQUEST,
                         {"action": "build_parcours", "lacunes": state["diagnostic"]["lacunes"]},
                         conversation_id=cid)
    try:
        _agents()
        rapport = _planificateur.construire_parcours(
            module=state["module"],
            lacunes=state["diagnostic"]["lacunes"],
            notions_maitrisees=state["diagnostic"]["notions_maitrisees"],
            nom_etudiant=state["nom_etudiant"]
        )
        raisonnement = reason_planificateur(state["diagnostic"], rapport.get("parcours", []))
        reply = create_a2a_msg("Planificateur", "Orchestrateur", INFORM,
                               {"nb_etapes": len(rapport.get("parcours", [])),
                                "duree_h": rapport.get("resume", {}).get("duree_totale_h", 0),
                                "llm_provider": LLM_PROVIDER},
                               conversation_id=cid)
        return {"parcours": rapport.get("parcours", []), "raisonnement": raisonnement,
                "communications": [req, reply]}
    except Exception as e:
        failure = create_a2a_msg("Planificateur", "Orchestrateur", FAILURE,
                                 {"erreur": str(e)}, conversation_id=cid)
        return {"parcours": [], "raisonnement": f"Erreur Planificateur : {e}",
                "communications": [req, failure]}


def pedagogue_node(state: LearningState) -> dict:
    """Recherche des ressources RAG pour TOUTES les lacunes détectées."""
    cid    = state["communications"][0]["conversation_id"]
    lacunes = state["diagnostic"]["lacunes"]
    req = create_a2a_msg("Orchestrateur", "Pedagogue", QUERY,
                         {"lacunes": lacunes, "nb_lacunes": len(lacunes)},
                         conversation_id=cid)
    try:
        _agents()
        # Chercher des ressources pour chaque lacune (max 2 par lacune, sans doublons)
        ressources = []
        sources_vues = set()
        for lacune in lacunes:
            for r in _pedagogue.chercher_ressources(lacune)[:2]:
                src = r.get("source", "")
                if src not in sources_vues:
                    r["lacune_cible"] = lacune  # tag pour affichage groupé dans l'UI
                    ressources.append(r)
                    sources_vues.add(src)

        reply = create_a2a_msg("Pedagogue", "Orchestrateur", INFORM,
                               {"nb_ressources": len(ressources),
                                "lacunes_couvertes": lacunes,
                                "sources": [r.get("source", "?") for r in ressources[:3]]},
                               conversation_id=cid)
        return {"ressources": ressources, "communications": [req, reply]}
    except Exception as e:
        failure = create_a2a_msg("Pedagogue", "Orchestrateur", FAILURE,
                                 {"erreur": str(e)}, conversation_id=cid)
        return {"ressources": [], "communications": [req, failure]}


def coach_node(state: LearningState) -> dict:
    """Calcule la prochaine révision SM-2 pour toutes les lacunes."""
    cid          = state["communications"][0]["conversation_id"]
    notion_cible = state["diagnostic"]["notion_cible"]
    score        = state["diagnostic"]["pourcentage"]
    qualite      = min(5, max(0, score // 20))  # conversion score % → qualité SM-2 (0-5)

    req = create_a2a_msg("Orchestrateur", "Coach", REQUEST,
                         {"action": "schedule_review", "notion": notion_cible, "qualite": qualite},
                         conversation_id=cid)
    try:
        _agents()
        # Calculer SM-2 pour la notion prioritaire
        res_sm2 = _coach.calculer_revision(state["nom_etudiant"], notion_cible, qualite)

        # Calculer aussi SM-2 pour les autres lacunes (pour planning complet)
        autres_lacunes = [l for l in state["diagnostic"]["lacunes"] if l != notion_cible]
        for lacune in autres_lacunes:
            _coach.calculer_revision(state["nom_etudiant"], lacune, 0)  # qualité 0 = à apprendre

        reply = create_a2a_msg("Coach", "Orchestrateur", INFORM,
                               {"intervalle_jours": res_sm2["intervalle_jours"],
                                "prochaine_revision": res_sm2["prochaine_revision"],
                                "nb_notions_planifiees": len(state["diagnostic"]["lacunes"])},
                               conversation_id=cid)
        return {"revision": res_sm2, "raisonnement_coach": res_sm2.get("raisonnement", ""),
                "communications": [req, reply]}
    except Exception as e:
        failure = create_a2a_msg("Coach", "Orchestrateur", FAILURE,
                                 {"erreur": str(e)}, conversation_id=cid)
        return {"revision": {}, "raisonnement_coach": "", "communications": [req, failure]}


def tracker_node(state: LearningState) -> dict:
    """Persiste la session en mémoire long-terme — toutes les lacunes, pas seulement la cible."""
    cid    = state["communications"][0]["conversation_id"]
    notion = state["diagnostic"]["notion_cible"]
    score  = state["diagnostic"]["pourcentage"] // 20  # 0-5

    req = create_a2a_msg("Orchestrateur", "Tracker", REQUEST,
                         {"action": "save_session"}, conversation_id=cid)
    try:
        _agents()
        raisonnement_tracker = _tracker.sauver_progres(state["nom_etudiant"], notion, score)

        saved = {
            "etudiant":           state["nom_etudiant"],
            "module":             state["module"],
            "score_final":        state["diagnostic"]["pourcentage"],
            "notion_cible":       notion,
            "toutes_lacunes":     state["diagnostic"]["lacunes"],
            "prochaine_revision": state.get("revision", {}).get("prochaine_revision"),
            "timestamp":          datetime.now().isoformat()
        }

        # Persistance via l'implémentation MCP (même fonction que @mcp.tool update_profile_ltm)
        from learning_tools_server import update_profile_ltm_impl
        update_profile_ltm_impl(state["nom_etudiant"], saved)

        reply = create_a2a_msg("Tracker", "Orchestrateur", CONFIRM,
                               {"status": "saved", "path": "data/profils_etudiants.json"},
                               conversation_id=cid)
        return {"profile_saved": saved, "raisonnement_tracker": raisonnement_tracker or "",
                "communications": [req, reply]}
    except Exception as e:
        failure = create_a2a_msg("Tracker", "Orchestrateur", FAILURE,
                                 {"erreur": str(e)}, conversation_id=cid)
        return {"profile_saved": {}, "raisonnement_tracker": "", "communications": [req, failure]}


# Conditional edge LangGraph :
# score >= 80% → étudiant avancé → on saute Planificateur + Pédagogue, direct au Coach
# score <  80% → parcours complet : Planificateur → Pédagogue → Coach
def route_after_diagnostic(state: LearningState) -> Literal["planificateur", "coach"]:
    if state.get("diagnostic", {}).get("pourcentage", 0) >= 80:
        return "coach"
    return "planificateur"


def build_graph():
    """Construit et compile le graphe LangGraph avec les 5 nodes et la conditional edge."""
    if not LANGGRAPH_AVAILABLE:
        raise ImportError("LangGraph non installé. Lance : pip install langgraph")

    workflow = StateGraph(LearningState)

    # Ajout des 5 nodes (un par agent)
    workflow.add_node("diagnosticien", diagnosticien_node)
    workflow.add_node("planificateur", planificateur_node)
    workflow.add_node("pedagogue",     pedagogue_node)
    workflow.add_node("coach",         coach_node)
    workflow.add_node("tracker",       tracker_node)

    # Edges : START → Diagnosticien → conditional → ...
    workflow.add_edge(START, "diagnosticien")
    workflow.add_conditional_edges("diagnosticien", route_after_diagnostic,
                                   {"planificateur": "planificateur", "coach": "coach"})
    workflow.add_edge("planificateur", "pedagogue")
    workflow.add_edge("pedagogue",     "coach")
    workflow.add_edge("coach",         "tracker")
    workflow.add_edge("tracker",        END)

    # InMemorySaver = mémoire court-terme (checkpointing par thread_id)
    return workflow.compile(checkpointer=InMemorySaver())


def _empty_state(nom, module, profile, init_msg):
    """Initialise un état LangGraph vide pour une nouvelle session."""
    return {
        "nom_etudiant": nom, "module": module, "profile_data": profile or {},
        "messages": [], "diagnostic": {}, "parcours": [],
        "raisonnement": "", "raisonnement_diag": "",
        "raisonnement_coach": "", "raisonnement_tracker": "",
        "ressources": [], "revision": {}, "profile_saved": {},
        "communications": [init_msg] if init_msg else []
    }


def run_session_fallback(nom: str, module: str, profile: dict = None) -> dict:
    """Exécution séquentielle en pur Python — utilisée si LangGraph n'est pas installé."""
    cid      = f"{nom}-{module}-{datetime.now().strftime('%H%M%S')}"
    init_msg = create_a2a_msg("User", "Orchestrateur", REQUEST, {"action": "start_session"}, cid)
    state    = _empty_state(nom, module, profile, init_msg)

    # 1. Diagnostic
    out = diagnosticien_node(state)
    state["diagnostic"]        = out["diagnostic"]
    state["raisonnement_diag"] = out.get("raisonnement_diag", "")
    state["communications"].extend(out["communications"])

    # 2. Routing conditionnel (même logique que LangGraph)
    if route_after_diagnostic(state) == "planificateur":
        out = planificateur_node(state)
        state["parcours"]     = out["parcours"]
        state["raisonnement"] = out.get("raisonnement", "")
        state["communications"].extend(out["communications"])

        out = pedagogue_node(state)
        state["ressources"] = out["ressources"]
        state["communications"].extend(out["communications"])

    # 3. Coach (toujours appelé)
    out = coach_node(state)
    state["revision"]           = out["revision"]
    state["raisonnement_coach"] = out.get("raisonnement_coach", "")
    state["communications"].extend(out["communications"])

    # 4. Tracker (toujours appelé)
    out = tracker_node(state)
    state["profile_saved"]        = out["profile_saved"]
    state["raisonnement_tracker"] = out.get("raisonnement_tracker", "")
    state["communications"].extend(out["communications"])

    return state


def run_session(nom: str, module: str, profile: dict = None) -> dict:
    """Lance une session complète — LangGraph si disponible, fallback sinon."""
    if LANGGRAPH_AVAILABLE:
        graph    = build_graph()
        cid      = f"{nom}-{module}-{datetime.now().strftime('%H%M%S')}"
        init_msg = create_a2a_msg("User", "Orchestrateur", REQUEST, {"action": "start_session"}, cid)
        return graph.invoke(
            input=_empty_state(nom, module, profile, init_msg),
            config={"configurable": {"thread_id": cid}}
        )
    print("[Orchestrateur] LangGraph absent — mode fallback Python pur.")
    return run_session_fallback(nom, module, profile)


def save_graph_diagram(output_path: str = "data/graph_orchestrator.png") -> bool:
    """Génère et sauvegarde le diagramme Mermaid du graphe LangGraph."""
    if not LANGGRAPH_AVAILABLE:
        return False
    try:
        graph     = build_graph()
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


if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    print(f"LangGraph disponible : {LANGGRAPH_AVAILABLE}\n")
    profils_path = os.path.join(os.path.dirname(__file__), 'data', 'profils_demo.json')
    with open(profils_path, 'r', encoding='utf-8') as f:
        profils = json.load(f)["profils"]

    for profile in profils:
        print(f"\n--- {profile['nom']} (score initial {profile['score_initial']}%) ---")
        result = run_session(profile["nom"], "MSA", profile)
        print(f"Diagnostic : {result['diagnostic']['pourcentage']}% - {result['diagnostic']['niveau_global']}")
        print(f"Lacunes    : {len(result['diagnostic']['lacunes'])} notion(s)")
        print(f"Parcours   : {len(result.get('parcours', []))} etape(s)")
        print(f"Ressources : {len(result.get('ressources', []))} document(s)")
        print(f"Revision   : {result.get('revision', {}).get('prochaine_revision', 'N/A')}")
        print(format_timeline_text(result["communications"]))

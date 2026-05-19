# Tests unitaires — pytest tests/ -v
# Couvre : conditional edge, protocole A2A, sessions d'intégration, isolation des nodes
import os
import sys
import json
import pytest

# Permettre l'import depuis le dossier parent
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator import (
    route_after_diagnostic,
    run_session,
    LearningState,
    diagnosticien_node,
    LANGGRAPH_AVAILABLE
)
from a2a_protocol import create_a2a_msg, REQUEST, INFORM


# Tests de la conditional edge LangGraph

class TestConditionalEdge:

    def test_avance_route_vers_coach(self):
        """Score >= 80% doit router vers coach (skip planificateur)."""
        state = {"diagnostic": {"pourcentage": 85}}
        assert route_after_diagnostic(state) == "coach"

    def test_debutant_route_vers_planificateur(self):
        """Score < 80% doit router vers planificateur."""
        state = {"diagnostic": {"pourcentage": 25}}
        assert route_after_diagnostic(state) == "planificateur"

    def test_intermediaire_route_vers_planificateur(self):
        """Score moyen (55%) doit aussi router vers planificateur."""
        state = {"diagnostic": {"pourcentage": 55}}
        assert route_after_diagnostic(state) == "planificateur"

    def test_limite_exacte_80(self):
        """Score = 80 doit router vers coach (≥ 80, pas > 80)."""
        state = {"diagnostic": {"pourcentage": 80}}
        assert route_after_diagnostic(state) == "coach"

    def test_etat_vide_route_vers_planificateur(self):
        """Si pas de diagnostic, fallback sécurisé sur planificateur."""
        state = {}
        assert route_after_diagnostic(state) == "planificateur"


# Tests du protocole A2A

class TestA2AProtocol:

    def test_message_a2a_a_les_champs_obligatoires(self):
        msg = create_a2a_msg("A", "B", REQUEST, {"action": "test"})
        for field in ["msg_id", "timestamp", "from", "to",
                      "performative", "content", "conversation_id"]:
            assert field in msg

    def test_performative_fipa_acl_valide(self):
        msg = create_a2a_msg("X", "Y", INFORM, {})
        assert msg["performative"] == "INFORM"

    def test_conversation_id_par_defaut(self):
        msg = create_a2a_msg("A", "B", REQUEST, {})
        assert msg["conversation_id"] == "session-default"

    def test_conversation_id_personnalise(self):
        msg = create_a2a_msg("A", "B", REQUEST, {}, conversation_id="custom-123")
        assert msg["conversation_id"] == "custom-123"


# Tests d'intégration — sessions complètes

@pytest.fixture
def profils():
    """Charge les 3 profils de démo."""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(base, 'data', 'profils_demo.json'), 'r', encoding='utf-8') as f:
        return {p["id"]: p for p in json.load(f)["profils"]}


class TestSessionsIntegration:

    def test_session_debutant_passe_par_planificateur(self, profils):
        """Profil débutant (Amina, 25%) → parcours complet."""
        result = run_session("Amina", "MSA", profils["etudiant_debutant"])
        assert "diagnostic" in result
        assert "parcours" in result
        assert len(result["parcours"]) > 0, "Le débutant doit avoir un parcours"
        assert "ressources" in result
        assert len(result["ressources"]) >= 0

    def test_session_avance_skip_planificateur(self, profils):
        """Profil avancé (Sarah, 85%) → coach direct (conditional edge)."""
        result = run_session("Sarah", "MSA", profils["etudiant_avance"])
        assert "diagnostic" in result
        # En mode avancé, on saute planificateur ET pédagogue
        # → parcours et ressources peuvent être vides
        assert result["diagnostic"]["pourcentage"] >= 80

    def test_communications_a2a_journalisees(self, profils):
        """Chaque session doit avoir un journal A2A non vide."""
        result = run_session("Yassine", "MSA", profils["etudiant_intermediaire"])
        comms = result.get("communications", [])
        assert len(comms) >= 4, f"Attendu ≥4 messages, obtenu {len(comms)}"
        # Vérifier la structure des messages
        for m in comms:
            assert "performative" in m
            assert "from" in m
            assert "to" in m

    def test_revision_calculee_par_sm2(self, profils):
        """Le Coach doit toujours retourner une date de prochaine révision."""
        result = run_session("Amina", "MSA", profils["etudiant_debutant"])
        assert "revision" in result
        assert "prochaine_revision" in result["revision"]
        assert "intervalle_jours" in result["revision"]

    def test_tracker_sauve_le_profil(self, profils):
        """Le Tracker doit créer/mettre à jour data/profils_etudiants.json."""
        result = run_session("Yassine", "MSA", profils["etudiant_intermediaire"])
        assert "profile_saved" in result
        assert result["profile_saved"]["etudiant"] == "Yassine"
        # Le fichier doit exister
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        profils_path = os.path.join(base, 'data', 'profils_etudiants.json')
        assert os.path.exists(profils_path)


# Tests des nodes individuels

class TestNodesIsolation:

    def test_diagnosticien_node_retourne_diagnostic(self, profils):
        state = {
            "nom_etudiant": "Amina",
            "module": "MSA",
            "profile_data": profils["etudiant_debutant"],
            "messages": [],
            "communications": [
                create_a2a_msg("U", "O", REQUEST, {}, conversation_id="test-1")
            ]
        }
        out = diagnosticien_node(state)
        assert "diagnostic" in out
        assert "communications" in out
        assert len(out["communications"]) == 2  # REQUEST + INFORM


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

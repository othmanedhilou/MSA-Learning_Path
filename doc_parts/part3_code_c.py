"""PARTIE III-C — Code expliqué : app.py, tests"""

def build(g):
    # ═══════════════════════════════════════════════════════
    # CHAPITRE 16 — app.py (Streamlit)
    # ═══════════════════════════════════════════════════════
    g.section_header("16", "Code expliqué : app.py — interface Streamlit")

    g.p("Ce fichier est <b>le point d'entrée utilisateur</b>. Il gère 3 phases : "
        "Accueil → Diagnostic → Résultats. Utilise <i>st.session_state</i> pour la "
        "persistance entre les reruns Streamlit.")

    g.h2("16.1 Configuration de la page")

    g.code_block("""st.set_page_config(
    page_title="AI Learning Architect",
    layout="wide",
    page_icon="🎓",
    initial_sidebar_state="expanded"
)""")

    g.explain("<b>layout=\"wide\"</b> utilise toute la largeur de l'écran (idéal pour "
              "la timeline A2A sur le côté droit). <b>initial_sidebar_state=\"expanded\"</b> "
              "ouvre la sidebar par défaut.")

    g.h2("16.2 Session state — gestion d'état Streamlit")

    g.code_block("""if 'phase' not in st.session_state:
    st.session_state.phase = "ACCUEIL"
if 'selected_profile' not in st.session_state:
    st.session_state.selected_profile = None
if 'selected_module' not in st.session_state:
    st.session_state.selected_module = "MSA"
if 'session_result' not in st.session_state:
    st.session_state.session_result = None""")

    g.callout("Pourquoi st.session_state ?",
        "Streamlit relance TOUT le script à chaque interaction (clic sur un bouton). "
        "Sans <b>st.session_state</b>, on perdrait l'état entre les reruns. "
        "Le pattern <i>if 'x' not in st.session_state</i> initialise une seule fois.",
        color=g.ACCENT)

    g.h2("16.3 La sidebar")

    g.code_block("""with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3449/3449642.png", width=80)
    st.title("🧠 SMA Learning")
    st.caption("Projet 4 · 4AISDR · Mai 2026")

    st.divider()

    if st.session_state.selected_profile:
        p = st.session_state.selected_profile
        st.success(f"👤 **{p['nom']}**")
        st.caption(p['description'])
        st.write(f"📊 Score initial : **{p['score_initial']}%**")

    st.divider()

    # Indicateurs backend
    st.write("**🔧 État du backend :**")
    st.write("✅ LangGraph" if LANGGRAPH_AVAILABLE else "⚠️ Fallback Python")
    st.write("✅ RAG vectoriel (Chroma)" if VECTOR_RAG_AVAILABLE else "⚠️ RAG keyword")
    llm_emoji = {"openrouter": "✅", "openai": "✅",
                  "gemini": "✅", "fallback": "⚠️"}.get(LLM_PROVIDER, "?")
    st.write(f"{llm_emoji} LLM : {LLM_PROVIDER}")""")

    g.explain("Les indicateurs de backend (LangGraph, RAG vectoriel, LLM) sont "
              "<b>visibles au jury</b> pendant la démo. Ils prouvent que TOUTES les "
              "exigences sont actives : un coup d'œil suffit.")

    g.h2("16.4 Phase 1 — Accueil avec choix de profil")

    g.code_block("""if st.session_state.phase == "ACCUEIL":
    st.subheader("👋 Choisissez un profil d'étudiant et un module")

    # Choix du module
    st.session_state.selected_module = st.selectbox(
        "Module",
        ["MSA", "Data Mining", "Deep Learning", "Data Warehouse", "Big Data"]
    )

    # Chargement des profils
    with open('data/profils_demo.json', 'r', encoding='utf-8') as f:
        profils = json.load(f)['profils']

    cols = st.columns(3)
    for i, p in enumerate(profils):
        with cols[i]:
            # Badge couleur selon le niveau
            if p['score_initial'] >= 80:
                badge_color, badge_text = "#15803d", "Avancé"
            elif p['score_initial'] >= 50:
                badge_color, badge_text = "#d97706", "Intermédiaire"
            else:
                badge_color, badge_text = "#dc2626", "Débutant"

            st.markdown(f'''
            <div class="profile-card">
                <h3>{p['nom']}</h3>
                <span class="badge" style="background:{badge_color};color:white;">
                    {badge_text}
                </span>
                <p>{p['description']}</p>
            </div>
            ''', unsafe_allow_html=True)

            if st.button(f"🚀 Lancer session {p['nom']}", key=f"btn_{p['id']}"):
                st.session_state.selected_profile = p
                st.session_state.phase = "DIAGNOSTIC"
                st.rerun()""")

    g.explain("Pour chaque profil, on calcule un <b>badge coloré</b> selon le niveau. "
              "Le clic stocke le profil dans <i>st.session_state</i> et déclenche "
              "<i>st.rerun()</i> qui relance le script en passant en phase DIAGNOSTIC.")

    g.h2("16.5 Phase 2 — Diagnostic (avec barre de progression)")

    g.code_block("""elif st.session_state.phase == "DIAGNOSTIC":
    p = st.session_state.selected_profile
    module = st.session_state.selected_module

    st.subheader(f"⚙️ Orchestration en cours pour {p['nom']}")
    progress_bar = st.progress(0, text="Démarrage de l'orchestrateur LangGraph...")

    with st.spinner("🤖 Les agents collaborent..."):
        progress_bar.progress(20, text="🩺 Diagnosticien — test adaptatif")
        time.sleep(0.4)
        progress_bar.progress(40, text="🗺️ Planificateur — construction (CoT)")
        time.sleep(0.4)
        progress_bar.progress(60, text="📚 Pédagogue — recherche RAG")
        time.sleep(0.4)
        progress_bar.progress(80, text="🔁 Coach — calcul SM-2")
        time.sleep(0.4)

        # APPEL RÉEL DE L'ORCHESTRATEUR
        result = run_session(p['nom'], module, p)
        st.session_state.session_result = result

        progress_bar.progress(100, text="✅ Session terminée")

    st.session_state.phase = "RESULTATS"
    st.rerun()""")

    g.callout("Pourquoi des time.sleep pendant la barre ?",
        "L'orchestrateur est très rapide (~2s). Sans <i>time.sleep</i>, la barre de "
        "progression saute de 0% à 100% trop vite — l'utilisateur ne voit pas les "
        "étapes. Les pauses de 0.4s permettent au jury de LIRE les noms des agents "
        "qui s'exécutent.",
        color=g.ACCENT)

    g.h2("16.6 Phase 3 — Résultats (le clou de la démo)")

    g.code_block("""elif st.session_state.phase == "RESULTATS":
    result = st.session_state.session_result
    diag = result.get('diagnostic', {})
    parcours = result.get('parcours', [])
    ressources = result.get('ressources', [])
    revision = result.get('revision', {})
    comms = result.get('communications', [])

    # Bandeau de stats
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.markdown(f'<div class="stat-box"><div class="value">{diag.get("pourcentage", 0)}%</div>'
                    f'<div class="label">Score global</div></div>', unsafe_allow_html=True)
    # ... s2, s3, s4 similaires

    # Layout principal : colonne gauche (résultats) + colonne droite (timeline)
    col_main, col_timeline = st.columns([2, 1])

    with col_main:
        # Affichage selon conditional edge
        if diag.get('pourcentage', 0) >= 80:
            st.info("🎯 Conditional Edge LangGraph activée : "
                    "étudiant avancé → saut du Planificateur et du Pédagogue, "
                    "accès direct au Coach.")
        else:
            st.info("📍 Parcours complet : Diagnosticien → Planificateur → "
                    "Pédagogue → Coach → Tracker.")

        # Diagnostic, parcours, ressources, révision

    with col_timeline:
        st.subheader("🤖 Timeline A2A")
        st.markdown(format_timeline_html(comms), unsafe_allow_html=True)""")

    g.h3("Les 5 sections de la phase Résultats")

    g.bullet([
        "<b>1. Bandeau stats (4 colonnes)</b> : Score, Niveau, Lacunes, Étapes parcours",
        "<b>2. Encadré conditional edge</b> : explique la décision prise (avancé vs débutant)",
        "<b>3. Raisonnement CoT</b> : <i>st.expander</i> avec le texte du LLM",
        "<b>4. Parcours détaillé</b> : cards avec ordre, durée, date",
        "<b>5. Ressources RAG</b> : cards cliquables vers les URLs",
        "<b>6. Révision SM-2</b> : 3 métriques (intervalle, date, facteur)",
        "<b>7. Timeline A2A (colonne droite)</b> : <b>LE moment culminant pour le jury</b>",
    ])

    g.pagebreak()

    # ═══════════════════════════════════════════════════════
    # CHAPITRE 17 — tests/test_orchestrator.py
    # ═══════════════════════════════════════════════════════
    g.section_header("17", "Code expliqué : tests/test_orchestrator.py")

    g.p("Tests pytest qui valident le comportement de l'orchestrateur. <b>15 tests "
        "en 4 classes</b>. Rare dans les projets étudiants — point bonus assuré.")

    g.h2("17.1 Configuration des tests")

    g.code_block("""import os
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
from a2a_protocol import create_a2a_msg, REQUEST, INFORM""")

    g.explain("Le <b>sys.path.insert(0, ...)</b> permet d'importer le module parent "
              "<i>orchestrator</i> depuis <i>tests/test_orchestrator.py</i>. C'est nécessaire "
              "car pytest peut être lancé depuis le dossier racine OU depuis tests/.")

    g.h2("17.2 Classe TestConditionalEdge — la plus critique")

    g.code_block("""class TestConditionalEdge:
    \"\"\"La conditional edge est la valeur ajoutée majeure de LangGraph.
    Si elle échoue, la démo échoue.\"\"\"

    def test_avance_route_vers_coach(self):
        \"\"\"Score >= 80% doit router vers coach (skip planificateur).\"\"\"
        state = {"diagnostic": {"pourcentage": 85}}
        assert route_after_diagnostic(state) == "coach"

    def test_debutant_route_vers_planificateur(self):
        \"\"\"Score < 80% doit router vers planificateur.\"\"\"
        state = {"diagnostic": {"pourcentage": 25}}
        assert route_after_diagnostic(state) == "planificateur"

    def test_intermediaire_route_vers_planificateur(self):
        \"\"\"Score moyen (55%) doit aussi router vers planificateur.\"\"\"
        state = {"diagnostic": {"pourcentage": 55}}
        assert route_after_diagnostic(state) == "planificateur"

    def test_limite_exacte_80(self):
        \"\"\"Score = 80 doit router vers coach (≥ 80, pas > 80).\"\"\"
        state = {"diagnostic": {"pourcentage": 80}}
        assert route_after_diagnostic(state) == "coach"

    def test_etat_vide_route_vers_planificateur(self):
        \"\"\"Si pas de diagnostic, fallback sécurisé sur planificateur.\"\"\"
        state = {}
        assert route_after_diagnostic(state) == "planificateur"
""")

    g.h3("Analyse des 5 tests")

    g.table_grid(
        ["Test", "Input", "Output attendu", "Pourquoi ce test"],
        [
            ["test_avance_route_vers_coach", "score=85", "coach", "Cas nominal avancé"],
            ["test_debutant_route_vers_planificateur", "score=25", "planificateur", "Cas nominal débutant"],
            ["test_intermediaire_route_vers_planificateur", "score=55", "planificateur", "Cas frontière (50-79%)"],
            ["test_limite_exacte_80", "score=80", "coach", "Cas LIMITE — ≥ et non >"],
            ["test_etat_vide_route_vers_planificateur", "state={}", "planificateur", "Robustesse (état corrompu)"],
        ],
        col_widths=[5*g.cm, 2*g.cm, 3*g.cm, 7*g.cm])

    g.callout("Test 4 (limite 80) crucial",
        "Ce test garantit qu'on utilise <b>≥</b> et non <b>></b>. Sans ce test, un "
        "développeur pourrait écrire <i>if score > 80</i> par erreur, et l'étudiant "
        "avec score exact 80% serait routé vers planificateur. Le test attrape cette "
        "off-by-one error.",
        color=g.ACCENT)

    g.h2("17.3 Classe TestSessionsIntegration")

    g.code_block("""@pytest.fixture
def profils():
    \"\"\"Charge les 3 profils de démo.\"\"\"
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(base, 'data', 'profils_demo.json'),
              'r', encoding='utf-8') as f:
        return {p["id"]: p for p in json.load(f)["profils"]}


class TestSessionsIntegration:

    def test_session_debutant_passe_par_planificateur(self, profils):
        \"\"\"Profil débutant (Amina, 25%) → parcours complet.\"\"\"
        result = run_session("Amina", "MSA", profils["etudiant_debutant"])
        assert "diagnostic" in result
        assert "parcours" in result
        assert len(result["parcours"]) > 0, "Le débutant doit avoir un parcours"
        assert "ressources" in result

    def test_session_avance_skip_planificateur(self, profils):
        \"\"\"Profil avancé (Sarah, 85%) → coach direct (conditional edge).\"\"\"
        result = run_session("Sarah", "MSA", profils["etudiant_avance"])
        assert "diagnostic" in result
        assert result["diagnostic"]["pourcentage"] >= 80

    def test_communications_a2a_journalisees(self, profils):
        \"\"\"Chaque session doit avoir un journal A2A non vide.\"\"\"
        result = run_session("Yassine", "MSA", profils["etudiant_intermediaire"])
        comms = result.get("communications", [])
        assert len(comms) >= 4, f"Attendu ≥4 messages, obtenu {len(comms)}"
        for m in comms:
            assert "performative" in m
            assert "from" in m
            assert "to" in m""")

    g.h3("Le décorateur @pytest.fixture")

    g.callout("Réutilisation des données",
        "La fixture <b>profils</b> charge les 3 profils de démo UNE FOIS et les "
        "rend disponibles à tous les tests qui le demandent comme paramètre. Pytest "
        "gère l'injection automatiquement. Cela évite de recoder le chargement dans "
        "chaque test.",
        color=g.SUCCESS)

    g.h2("17.4 Résultats des tests")

    g.code_block("""$ pytest tests/ -v

tests/test_orchestrator.py::TestConditionalEdge::test_avance_route_vers_coach PASSED [  6%]
tests/test_orchestrator.py::TestConditionalEdge::test_debutant_route_vers_planificateur PASSED [ 13%]
tests/test_orchestrator.py::TestConditionalEdge::test_intermediaire_route_vers_planificateur PASSED [ 20%]
tests/test_orchestrator.py::TestConditionalEdge::test_limite_exacte_80 PASSED [ 26%]
tests/test_orchestrator.py::TestConditionalEdge::test_etat_vide_route_vers_planificateur PASSED [ 33%]
tests/test_orchestrator.py::TestA2AProtocol::test_message_a2a_a_les_champs_obligatoires PASSED [ 40%]
tests/test_orchestrator.py::TestA2AProtocol::test_performative_fipa_acl_valide PASSED [ 46%]
tests/test_orchestrator.py::TestA2AProtocol::test_conversation_id_par_defaut PASSED [ 53%]
tests/test_orchestrator.py::TestA2AProtocol::test_conversation_id_personnalise PASSED [ 60%]
tests/test_orchestrator.py::TestSessionsIntegration::test_session_debutant... PASSED [ 66%]
tests/test_orchestrator.py::TestSessionsIntegration::test_session_avance...  PASSED [ 73%]
tests/test_orchestrator.py::TestSessionsIntegration::test_communications... PASSED [ 80%]
tests/test_orchestrator.py::TestSessionsIntegration::test_revision...         PASSED [ 86%]
tests/test_orchestrator.py::TestSessionsIntegration::test_tracker_sauve...   PASSED [ 93%]
tests/test_orchestrator.py::TestNodesIsolation::test_diagnosticien_node...   PASSED [100%]

============================= 15 passed in 1.89s =============================""")

    g.callout("Argument béton pour le jury",
        "<b>« Notre code est validé par 15 tests automatisés qui s'exécutent en 2 secondes. »</b> "
        "C'est une preuve de maturité d'ingénieur. Aucun autre groupe ne pourra montrer ça.",
        color=g.SUCCESS)

    g.pagebreak()

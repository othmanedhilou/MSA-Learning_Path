# Interface Streamlit — Learning Path Architect
# 4 phases : ACCUEIL → QUIZ (optionnel) → DIAGNOSTIC → RESULTATS
import streamlit as st
import json
import os
import time

# Imports projet
from orchestrator import run_session, LANGGRAPH_AVAILABLE
from a2a_protocol import format_timeline_html
from mind_layer import LLM_PROVIDER
from rag_engine import VECTOR_RAG_AVAILABLE
from diagnostician import AgentDiagnostician

_diagnosticien = AgentDiagnostician()

# ──────────────────────────────────────────────────────────────
# CONFIGURATION PAGE
# ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Learning Architect",
    layout="wide",
    page_icon="🎓",
    initial_sidebar_state="expanded"
)

# ──────────────────────────────────────────────────────────────
# CSS
# ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
.main { background-color: #f8f9fa; }
.stButton>button {
    width: 100%; border-radius: 20px;
    background: linear-gradient(90deg, #4b6cb7 0%, #182848 100%);
    color: white; font-weight: bold; border: none; padding: 0.5rem;
}
.resource-card {
    background-color: white; padding: 18px;
    border-radius: 12px; box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    margin-bottom: 12px; border-left: 5px solid #4b6cb7;
}
.parcours-step {
    background-color: white; padding: 14px;
    border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    margin-bottom: 10px; border-left: 4px solid #15803d;
}
.stat-box {
    text-align: center; padding: 18px;
    background: white; border-radius: 12px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}
.stat-box .value {
    font-size: 2rem; font-weight: bold; color: #182848;
}
.stat-box .label {
    color: #64748b; font-size: 0.85rem;
}
.profile-card {
    background: white; padding: 20px; border-radius: 12px;
    box-shadow: 0 3px 8px rgba(0,0,0,0.08);
    border-top: 4px solid #4b6cb7; height: 220px;
}
.badge {
    display: inline-block; padding: 4px 10px;
    border-radius: 12px; font-size: 0.75rem; font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# SESSION STATE
# ──────────────────────────────────────────────────────────────
if 'phase' not in st.session_state:
    st.session_state.phase = "ACCUEIL"
if 'selected_profile' not in st.session_state:
    st.session_state.selected_profile = None
if 'selected_module' not in st.session_state:
    st.session_state.selected_module = "MSA"
if 'session_result' not in st.session_state:
    st.session_state.session_result = None

# État du quiz interactif
if 'quiz_nom' not in st.session_state:
    st.session_state.quiz_nom = ""
if 'quiz_notions' not in st.session_state:
    st.session_state.quiz_notions = []
if 'quiz_index' not in st.session_state:
    st.session_state.quiz_index = 0
if 'quiz_niveau' not in st.session_state:
    st.session_state.quiz_niveau = "facile"
if 'quiz_answers' not in st.session_state:
    st.session_state.quiz_answers = {}
if 'quiz_feedback' not in st.session_state:
    st.session_state.quiz_feedback = None  # {"correct": bool, "bonne_reponse": str, "reponse_choisie": str}


# ──────────────────────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3449/3449642.png", width=80)
    st.title("🧠 SMA Learning")
    st.caption("Projet 4 · 4AISDR · Mai 2026")

    st.divider()

    if st.session_state.selected_profile:
        p = st.session_state.selected_profile
        st.success(f"👤 **{p['nom']}**")
        if p.get('description'):
            st.caption(p['description'])
        st.write(f"📊 Score : **{p.get('score_initial', '?')}%**")
        st.write(f"📚 Module : **{st.session_state.selected_module}**")
    elif st.session_state.phase == "QUIZ":
        st.info(f"🎯 Quiz en cours — **{st.session_state.quiz_nom}**")
        st.caption(f"Module : {st.session_state.selected_module}")
        total = len(st.session_state.quiz_notions)
        current = st.session_state.quiz_index
        if total > 0:
            st.progress(current / total, text=f"Question {current}/{total}")
    else:
        st.info("⬅️ Choisissez un profil pour commencer")

    st.divider()

    # Indicateurs backend
    st.write("**🔧 État du backend :**")
    st.write("✅ LangGraph" if LANGGRAPH_AVAILABLE else "⚠️ Fallback Python")
    st.write("✅ RAG vectoriel (Chroma)" if VECTOR_RAG_AVAILABLE else "⚠️ RAG keyword")
    llm_emoji = {"openrouter": "✅", "openai": "✅", "gemini": "✅", "fallback": "⚠️"}.get(LLM_PROVIDER, "?")
    st.write(f"{llm_emoji} LLM : {LLM_PROVIDER}")

    st.divider()

    if st.button("🔄 Réinitialiser"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    st.divider()
    st.caption("Équipe : Othmane · Dodo · Mohamed Yassir")


# ──────────────────────────────────────────────────────────────
# HEADER
# ──────────────────────────────────────────────────────────────
st.markdown("# 🎓 Architecte d'Apprentissage Adaptatif")
st.markdown(
    "**Système Multi-Agents** orchestré par LangGraph · "
    "5 agents spécialisés · Communication FIPA-ACL · RAG vectoriel · SM-2"
)
st.divider()


# ══════════════════════════════════════════════════════════════
# PHASE 1 : ACCUEIL
# ══════════════════════════════════════════════════════════════
if st.session_state.phase == "ACCUEIL":
    st.subheader("👋 Choisissez un profil d'étudiant et un module")

    # Choix du module
    col_m1, col_m2 = st.columns([1, 3])
    with col_m1:
        st.write("**Module à diagnostiquer :**")
    with col_m2:
        st.session_state.selected_module = st.selectbox(
            "Module",
            ["MSA", "Data Mining", "Deep Learning", "Data Warehouse", "Big Data"],
            label_visibility="collapsed"
        )

    st.markdown("---")

    # Chargement des profils
    try:
        with open('data/profils_demo.json', 'r', encoding='utf-8') as f:
            profils = json.load(f)['profils']

        cols = st.columns(3)
        for i, p in enumerate(profils):
            with cols[i]:
                # Badge couleur selon le niveau
                if p['score_initial'] >= 80:
                    badge_color = "#15803d"
                    badge_text = "Avancé"
                elif p['score_initial'] >= 50:
                    badge_color = "#d97706"
                    badge_text = "Intermédiaire"
                else:
                    badge_color = "#dc2626"
                    badge_text = "Débutant"

                st.markdown(f"""
                <div class="profile-card">
                    <h3>{p['nom']}</h3>
                    <span class="badge" style="background:{badge_color};color:white;">{badge_text}</span>
                    <p style="color:#475569;margin-top:10px;font-size:0.9rem;">{p['description']}</p>
                    <p><b>Score initial :</b> {p['score_initial']}%</p>
                </div>
                """, unsafe_allow_html=True)

                if st.button(f"🚀 Lancer session {p['nom']}", key=f"btn_{p['id']}"):
                    st.session_state.selected_profile = p
                    st.session_state.phase = "DIAGNOSTIC"
                    st.rerun()

    except Exception as e:
        st.error(f"Erreur de chargement des profils : {e}")

    # Carte "Mon profil" — quiz interactif réel
    st.markdown("---")
    st.subheader("🎯 Ou passez le vrai test vous-même")
    st.caption("Le Diagnosticien vous pose de vraies questions et adapte la difficulté selon vos réponses.")

    col_form, col_info = st.columns([2, 1])
    with col_form:
        nom_input = st.text_input("Votre prénom", placeholder="Ex: Othmane", key="nom_input_field")
        if st.button("🚀 Démarrer mon quiz adaptatif", type="primary"):
            nom = nom_input.strip()
            if not nom:
                st.error("Entrez votre prénom pour commencer.")
            else:
                notions = _diagnosticien._get_notions(st.session_state.selected_module)
                if not notions:
                    st.error(f"Aucune notion disponible pour le module {st.session_state.selected_module}.")
                else:
                    st.session_state.quiz_nom      = nom
                    st.session_state.quiz_notions  = notions
                    st.session_state.quiz_index    = 0
                    st.session_state.quiz_niveau   = "facile"
                    st.session_state.quiz_answers  = {}
                    st.session_state.quiz_feedback = None
                    st.session_state.phase         = "QUIZ"
                    st.rerun()

    with col_info:
        st.markdown("""
        **Comment ça marche :**
        - Bonne réponse → question plus difficile
        - Mauvaise réponse → retour au niveau facile
        - À la fin → parcours 100% personnalisé
        """)

    # Architecture preview
    with st.expander("🔍 Aperçu de l'architecture du système"):
        st.code("""
                    ┌─────────┐
                    │  START  │
                    └────┬────┘
                         ▼
                ┌────────────────┐
                │  Diagnosticien │  ← test adaptatif
                └────────┬───────┘
                         │
                  ╔══════╧══════╗
                  ║ Conditional ║   ← LangGraph !
                  ╚══════╤══════╝
                ≥80%    │    <80%
              ┌────────┘      └────────┐
              ▼                        ▼
        ┌──────────┐         ┌────────────────┐
        │  Coach   │         │ Planificateur  │
        │ (direct) │         └────────┬───────┘
        └────┬─────┘                  ▼
             │              ┌──────────────────┐
             │              │  Pédagogue (RAG) │
             │              └──────────┬───────┘
             │                         ▼
             │                  ┌──────────┐
             │                  │  Coach   │
             │                  └────┬─────┘
             └──────────────────────┘
                                ▼
                          ┌──────────┐
                          │ Tracker  │
                          └─────┬────┘
                                ▼
                            ┌───────┐
                            │  END  │
                            └───────┘
        """, language=None)


# ══════════════════════════════════════════════════════════════
# PHASE 2 : QUIZ INTERACTIF — test adaptatif réel
# ══════════════════════════════════════════════════════════════
elif st.session_state.phase == "QUIZ":
    notions  = st.session_state.quiz_notions
    index    = st.session_state.quiz_index
    nom      = st.session_state.quiz_nom
    module   = st.session_state.selected_module
    niveaux  = ["facile", "moyen", "difficile"]

    # Toutes les notions ont été répondues → lancer le diagnostic réel
    if index >= len(notions):
        rapport = _diagnosticien.run_diagnostic_with_answers(
            module, nom, st.session_state.quiz_answers
        )
        # Construire un profil à partir des résultats pour l'orchestrateur
        historique = [
            {"notion": n, "maitrise": n in rapport["notions_maitrisees"]}
            for n in rapport["notions_maitrisees"] + rapport["lacunes"]
        ]
        profile = {
            "nom":           nom,
            "score_initial": rapport["pourcentage"],
            "historique":    historique,
            "description":   f"Profil personnalisé — quiz {module}"
        }
        st.session_state.selected_profile = profile
        st.session_state.phase = "DIAGNOSTIC"
        st.rerun()

    notion_info  = notions[index]
    notion_label = notion_info["label"]
    niveau       = st.session_state.quiz_niveau
    question     = _diagnosticien._get_questions(module, notion_label, niveau) \
                   or _diagnosticien._get_questions(module, notion_label, "facile")

    # Header du quiz
    st.subheader(f"🎯 Quiz adaptatif — {nom}")
    st.caption(f"Module : **{module}**")

    # Barre de progression
    st.progress((index) / len(notions),
                text=f"Notion {index + 1} / {len(notions)} — {notion_label}")

    st.markdown("---")

    if not question:
        # Pas de question disponible pour cette notion → on passe
        st.warning(f"Pas de question disponible pour « {notion_label} », notion ignorée.")
        st.session_state.quiz_answers[notion_label] = -1
        st.session_state.quiz_index += 1
        st.rerun()

    # Affichage du feedback de la question précédente
    if st.session_state.quiz_feedback:
        fb = st.session_state.quiz_feedback
        if fb["correct"]:
            st.success(f"✅ Correct ! — niveau monte à **{niveau}**")
        else:
            st.error(f"❌ Incorrect — bonne réponse : **{fb['bonne_reponse']}**")
        st.session_state.quiz_feedback = None

    # Affichage de la question
    col_q, col_level = st.columns([4, 1])
    with col_q:
        st.markdown(f"### {question['question']}")
    with col_level:
        niveau_colors = {"facile": "#15803d", "moyen": "#d97706", "difficile": "#dc2626"}
        st.markdown(
            f'<span style="background:{niveau_colors[niveau]};color:white;'
            f'padding:4px 12px;border-radius:12px;font-size:0.8rem;font-weight:bold;">'
            f'{niveau.upper()}</span>',
            unsafe_allow_html=True
        )

    st.markdown("")

    # Boutons de réponse
    for i, option in enumerate(question["options"]):
        if st.button(f"{'ABCD'[i]}. {option}", key=f"opt_{index}_{i}"):
            correct = (i == question["reponse"])

            # Enregistrer la réponse
            st.session_state.quiz_answers[notion_label] = i

            # Adapter la difficulté
            if correct:
                idx_niv = niveaux.index(niveau)
                new_niveau = niveaux[min(idx_niv + 1, len(niveaux) - 1)]
            else:
                new_niveau = "facile"

            # Préparer le feedback
            st.session_state.quiz_feedback = {
                "correct":        correct,
                "bonne_reponse":  question["options"][question["reponse"]],
                "reponse_choisie": option
            }

            st.session_state.quiz_niveau = new_niveau
            st.session_state.quiz_index  = index + 1
            st.rerun()

    st.markdown("---")
    if st.button("⏭️ Passer cette question"):
        st.session_state.quiz_answers[notion_label] = -1
        st.session_state.quiz_index += 1
        st.rerun()


# PHASE 3 : DIAGNOSTIC (orchestration en cours)
elif st.session_state.phase == "DIAGNOSTIC":
    p = st.session_state.selected_profile
    module = st.session_state.selected_module

    st.subheader(f"⚙️ Orchestration en cours pour {p['nom']}")
    st.caption(f"Module : **{module}**")

    progress_bar = st.progress(0, text="Démarrage de l'orchestrateur LangGraph...")

    with st.spinner("🤖 Les agents collaborent..."):
        progress_bar.progress(10, text="🩺 Diagnosticien — évaluation du niveau...")
        time.sleep(0.3)

        # APPEL RÉEL DE L'ORCHESTRATEUR — le graphe LangGraph décide du chemin
        result = run_session(p['nom'], module, p)
        st.session_state.session_result = result

        score = result.get('diagnostic', {}).get('pourcentage', 0)

        if score >= 80:
            # Chemin court : Diagnosticien → Coach → Tracker
            progress_bar.progress(60, text="🎯 Score ≥ 80% — Conditional Edge activée → Coach direct")
            time.sleep(0.3)
            progress_bar.progress(85, text="🔁 Coach — calcul SM-2")
            time.sleep(0.2)
        else:
            # Chemin complet : Diagnosticien → Planificateur → Pédagogue → Coach → Tracker
            progress_bar.progress(35, text="🗺️ Planificateur — construction du parcours (CoT)")
            time.sleep(0.3)
            progress_bar.progress(60, text="📚 Pédagogue — recherche RAG vectorielle")
            time.sleep(0.3)
            progress_bar.progress(80, text="🔁 Coach — calcul SM-2")
            time.sleep(0.2)

        progress_bar.progress(100, text="✅ Session terminée — Tracker a sauvegardé le profil")
        time.sleep(0.3)

    st.session_state.phase = "RESULTATS"
    st.rerun()


# PHASE 4 : RÉSULTATS
elif st.session_state.phase == "RESULTATS":
    result = st.session_state.session_result
    p = st.session_state.selected_profile

    if not result:
        st.error("Aucun résultat disponible. Veuillez relancer une session.")
        st.stop()

    diag = result.get('diagnostic', {})
    parcours = result.get('parcours', [])
    ressources = result.get('ressources', [])
    revision = result.get('revision', {})
    comms = result.get('communications', [])

    # ── Bandeau de stats ──
    st.subheader(f"✅ Session de {p['nom']} terminée")

    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.markdown(f"""<div class="stat-box">
            <div class="value">{diag.get('pourcentage', 0)}%</div>
            <div class="label">Score global</div></div>""", unsafe_allow_html=True)
    with s2:
        st.markdown(f"""<div class="stat-box">
            <div class="value">{diag.get('niveau_global', 'N/A')}</div>
            <div class="label">Niveau</div></div>""", unsafe_allow_html=True)
    with s3:
        st.markdown(f"""<div class="stat-box">
            <div class="value">{len(diag.get('lacunes', []))}</div>
            <div class="label">Lacunes détectées</div></div>""", unsafe_allow_html=True)
    with s4:
        st.markdown(f"""<div class="stat-box">
            <div class="value">{len(parcours)}</div>
            <div class="label">Étapes parcours</div></div>""", unsafe_allow_html=True)

    st.divider()

    # ── Layout principal ──
    col_main, col_timeline = st.columns([2, 1])

    with col_main:
        # ── Décision routage (visible pour le jury) ──
        if diag.get('pourcentage', 0) >= 80:
            st.info("🎯 **Conditional Edge LangGraph activée** : étudiant avancé → "
                    "saut du Planificateur et du Pédagogue, accès direct au Coach.")
        else:
            st.info("📍 **Parcours complet** : Diagnosticien → Planificateur → Pédagogue → Coach → Tracker.")

        # ── Diagnostic détaillé ──
        with st.expander("🩺 Diagnostic détaillé", expanded=True):
            c1, c2 = st.columns(2)
            with c1:
                st.write("**✅ Notions maîtrisées :**")
                if diag.get('notions_maitrisees'):
                    for n in diag['notions_maitrisees']:
                        st.success(f"• {n}")
                else:
                    st.write("_Aucune_")
            with c2:
                st.write("**❌ Lacunes :**")
                if diag.get('lacunes'):
                    for n in diag['lacunes']:
                        st.error(f"• {n}")
                else:
                    st.write("_Aucune_ 🎉")

            st.markdown(f"**🎯 Notion cible :** `{diag.get('notion_cible', 'N/A')}`")

        # ── Raisonnements Chain-of-Thought (Mind Layer — tous les agents) ──
        raisonnement_diag = result.get("raisonnement_diag", "")
        if raisonnement_diag:
            with st.expander("🩺 Raisonnement Agent Diagnosticien (Chain-of-Thought)"):
                st.markdown(raisonnement_diag)
                st.caption(f"Provider LLM : `{LLM_PROVIDER}`")

        raisonnement = result.get("raisonnement", "")
        if raisonnement:
            with st.expander("🗺️ Raisonnement Agent Planificateur (Chain-of-Thought)",
                              expanded=True):
                st.markdown(raisonnement)
                st.caption(f"Provider LLM : `{LLM_PROVIDER}`")

        raisonnement_coach = result.get("raisonnement_coach", "")
        if raisonnement_coach:
            with st.expander("🔁 Raisonnement Agent Coach — SM-2 (Chain-of-Thought)"):
                st.markdown(raisonnement_coach)
                st.caption(f"Provider LLM : `{LLM_PROVIDER}`")

        raisonnement_tracker = result.get("raisonnement_tracker", "")
        if raisonnement_tracker:
            with st.expander("💾 Raisonnement Agent Tracker (Chain-of-Thought)"):
                st.markdown(raisonnement_tracker)
                st.caption(f"Provider LLM : `{LLM_PROVIDER}`")

        # ── Parcours ──
        if parcours:
            st.subheader("🗺️ Parcours d'apprentissage personnalisé")
            for etape in parcours:
                st.markdown(f"""
                <div class="parcours-step">
                    <b>Étape {etape.get('ordre', '?')} : {etape.get('notion', 'N/A')}</b><br/>
                    📅 {etape.get('date_session', 'N/A')} ·
                    ⏱ {etape.get('duree_estimee_min', '?')} min ·
                    🔁 {etape.get('intervalle_revision', 'N/A')}
                </div>
                """, unsafe_allow_html=True)

        # ── Ressources RAG ──
        if ressources:
            st.subheader(f"📚 Ressources RAG pour « {diag.get('notion_cible', 'N/A')} »")
            for r in ressources[:5]:
                contenu = r.get('contenu', r.get('description', ''))
                st.markdown(f"""
                <div class="resource-card">
                    <h4 style="margin:0;">{r.get('type', 'Ressource')}</h4>
                    <p style="color:#475569;margin:8px 0;font-size:0.9rem;">
                        {contenu[:300]}{'...' if len(contenu) > 300 else ''}
                    </p>
                    <small style="color:#64748b;">📂 Source : {r.get('source', 'inconnue')}</small>
                </div>
                """, unsafe_allow_html=True)
                if r.get('url') and r['url'] != '#':
                    st.link_button(f"🚀 Ouvrir {r.get('type', '')}", r['url'])

        # ── Révision SM-2 ──
        if revision:
            st.subheader("🔁 Prochaine révision (algorithme SM-2)")
            r1, r2, r3 = st.columns(3)
            r1.metric("Intervalle", f"{revision.get('intervalle_jours', '?')} jour(s)")
            r2.metric("Prochaine date", revision.get('prochaine_revision', 'N/A'))
            r3.metric("Facteur facilité", revision.get('facteur_facilite', '?'))

    with col_timeline:
        st.subheader("🤖 Timeline A2A")
        st.caption("Protocole FIPA-ACL — chaque échange est tracé")
        st.markdown(format_timeline_html(comms), unsafe_allow_html=True)

        st.divider()

        # Stats com
        st.metric("📨 Messages échangés", len(comms))

        # Décompte par performative
        from collections import Counter
        perf_count = Counter(m['performative'] for m in comms)
        for perf, count in perf_count.most_common():
            st.caption(f"  • {perf} : {count}")

        st.divider()

        if st.button("🔄 Nouvelle session", type="primary"):
            for key in ['phase', 'selected_profile', 'session_result']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()


# ──────────────────────────────────────────────────────────────
# FOOTER
# ──────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "Projet Agentic AI · 4AISDR · 2026 · "
    "Équipe : Othmane · Dodo · Mohamed Yassir · "
    "Encadrants : Pr. H. CHAABI &amp; Pr. N. IDRISSI Zouggari"
)

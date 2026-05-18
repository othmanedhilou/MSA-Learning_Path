import streamlit as st
import json
import time
import os

# --- IMPORT DU MOTEUR RAG (Travail de Dodo D1) ---
from rag_engine import RAGEngine

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="AI Learning Architect", layout="wide", page_icon="🎓")

# --- DESIGN PERSONNALISÉ (CSS) ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button {
        width: 100%;
        border-radius: 20px;
        background: linear-gradient(90deg, #4b6cb7 0%, #182848 100%);
        color: white;
        font-weight: bold;
        border: none;
        padding: 0.5rem;
    }
    .resource-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        border-left: 5px solid #4b6cb7;
    }
    .timeline-msg {
        background-color: #f1f3f4;
        padding: 10px;
        border-radius: 8px;
        border-left: 4px solid #182848;
        margin-bottom: 10px;
        font-family: 'Courier New', Courier, monospace;
        font-size: 0.9rem;
    }
    .stat-box {
        text-align: center;
        padding: 15px;
        background: white;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# --- INITIALISATION ---
@st.cache_resource
def load_rag():
    return RAGEngine()

rag_engine = load_rag()

# --- GESTION DES PHASES (Tâche D2) ---
if 'phase' not in st.session_state:
    st.session_state.phase = "ACCUEIL" # ACCUEIL | DIAGNOSTIC | RESULTATS
if 'selected_profile' not in st.session_state:
    st.session_state.selected_profile = None

# --- BARRE LATÉRALE (SIDEBAR) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3449/3449642.png", width=80)
    st.title("Mon Profil")
    
    if st.session_state.selected_profile:
        st.write(f"👤 **Étudiant :** {st.session_state.selected_profile['nom']}")
        st.caption(f"Cible : {st.session_state.selected_profile['id']}")
    else:
        st.info("Veuillez choisir un profil en page d'accueil.")

    st.divider()
    if st.button("🔄 Réinitialiser la session"):
        st.session_state.phase = "ACCUEIL"
        st.session_state.selected_profile = None
        st.rerun()

# --- CORPS PRINCIPAL ---
st.markdown(f"# 🧠 Architecte d'Apprentissage Adaptatif")

# ==============================================================================
# PHASE ACCUEIL : CHOIX DU PROFIL (Tâche D4)
# ==============================================================================
if st.session_state.phase == "ACCUEIL":
    st.subheader("Bienvenue ! 👋 Choisissez un profil pour simuler l'IA adaptative :")
    
    # Chargement des profils de démo
    try:
        with open('data/profils_demo.json', 'r', encoding='utf-8') as f:
            profils = json.load(f)['profils']
        
        cols = st.columns(3)
        for i, p in enumerate(profils):
            with cols[i]:
                st.markdown(f"**{p['nom']}**")
                st.caption(p['description'])
                if st.button(f"Démarrer session {p['nom']}", key=f"btn_{p['id']}"):
                    st.session_state.selected_profile = p
                    st.session_state.phase = "DIAGNOSTIC"
                    st.rerun()
    except Exception as e:
        st.error("Erreur de chargement des profils. Vérifiez data/profils_demo.json")

# ==============================================================================
# PHASE DIAGNOSTIC : LE TEST (Tâche D2)
# ==============================================================================
elif st.session_state.phase == "DIAGNOSTIC":
    st.header(f"📝 Diagnostic Adaptatif : {st.session_state.selected_profile['nom']}")
    
    # Interface de diagnostic (Simulation du travail d'Othmane)
    st.info("L'Agent Diagnosticien prépare une série de questions basées sur votre profil...")
    
    st.markdown("### Question 1 : Qu'est-ce qu'un agent intelligent ?")
    reponse = st.radio("Sélectionnez votre réponse :", 
                       ["Un simple programme", "Une entité autonome qui perçoit et agit", "Un serveur web"])
    
    if st.button("Valider et passer à l'analyse"):
        with st.spinner("L'Orchestrateur LangGraph génère votre parcours..."):
            time.sleep(2) # Temps de réflexion des agents
            st.session_state.phase = "RESULTATS"
            st.rerun()

# ==============================================================================
# PHASE RESULTATS : PARCOURS & TIMELINE (Tâche D3)
# ==============================================================================
elif st.session_state.phase == "RESULTATS":
    st.header(f"✅ Parcours d'apprentissage de {st.session_state.selected_profile['nom']}")
    
    col_main, col_timeline = st.columns([2, 1])

    with col_main:
        # Simulation du résultat de l'Agent Planificateur
        st.subheader("🗺️ Ma Carte de Progression")
        if os.path.exists("data/graphe_prerequis.png"):
            st.image("data/graphe_prerequis.png", width=700)
        st.divider()
        st.subheader("📚 Mes Ressources personnalisées (RAG)")
        
        # Exemple d'appel au moteur RAG de Dodo
        lacune_detectee = "Communication Inter-agents"
        ressources_rag = rag_engine.chercher_ressources(lacune_detectee)
        
        if ressources_rag:
            for res in ressources_rag:
                st.markdown(f"""
                <div class="resource-card">
                    <h4>{lacune_detectee}</h4>
                    <p>{res['contenu']}</p>
                </div>
                """, unsafe_allow_html=True)
                st.caption(f"Source : {res['source']}")
        else:
            st.write("Chargement des ressources textuelles...")

    with col_timeline:
        st.subheader("🤖 Timeline Agents (A2A)")
        # Simulation du protocole A2A / FIPA-ACL (Tâche D3)
        messages = [
            "Diagnosticien ➡️ Planificateur : REQUEST(lacunes)",
            "Planificateur ➡️ Pédagogue : INFORM(ordre_notions)",
            "Pédagogue ➡️ RAG_Engine : QUERY(Communication)",
            "RAG_Engine ➡️ Pédagogue : INFORM(top_docs)",
            "Tracker ➡️ State : UPDATE(profil_etudiant)"
        ]
        
        for msg in messages:
            st.markdown(f'<div class="timeline-msg">{msg}</div>', unsafe_allow_html=True)
        
        st.divider()
        st.success("🎯 Objectif du jour : Comprendre le protocole FIPA-ACL")

# Footer
st.divider()
st.caption("Projet Agentic AI - Équipe :  Outhman, DODO, Mohamed Yassir - Présentation Mai 2026")
           
#"Équipe : Outhman, DODO, Mohamed Yassir"
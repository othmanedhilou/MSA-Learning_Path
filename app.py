import streamlit as st
from agents_dodo import AgentPedagogue, AgentTracker, AgentCoach
import time
import json
import os

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
    .stat-box {
        text-align: center;
        padding: 15px;
        background: white;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# --- INITIALISATION DES AGENTS ---
try:
    pedagogue = AgentPedagogue()
    tracker = AgentTracker()
    coach = AgentCoach()
except Exception as e:
    st.error(f"Erreur d'initialisation : {e}")
    st.stop()

# --- BARRE LATÉRALE (SIDEBAR) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3449/3449642.png", width=100)
    st.title("Mon Profil")
    nom = st.text_input("Prénom de l'étudiant", "Dodo")
    module_select = st.selectbox("🎯 Choisir un Module", ["MSA", "Data Mining", "Deep Learning", "Data Warehouse", "Big Data"])
    
    st.divider()
    dernier_progres = tracker.charger_dernier_score(nom)
    if dernier_progres:
        st.write("📜 **Dernière activité**")
        st.caption(f"Notion : {dernier_progres['notion']}")
        st.caption(f"Score : {dernier_progres['score']}/5")
    
    st.write("---")
    st.progress(65, text="Progression du module")

# --- CORPS PRINCIPAL ---
st.markdown(f"# 🧠 Architecte d'Apprentissage Adaptatif")
st.markdown(f"### Bienvenue, **{nom}** ! 👋")

# Ligne de statistiques
s1, s2, s3 = st.columns(3)
with s1:
    st.markdown('<div class="stat-box">⭐<br><b>Niveau</b><br>Intermédiaire</div>', unsafe_allow_html=True)
with s2:
    st.markdown(f'<div class="stat-box">📚<br><b>Module</b><br>{module_select}</div>', unsafe_allow_html=True)
with s3:
    st.markdown('<div class="stat-box">🔥<br><b>Série</b><br>5 Jours</div>', unsafe_allow_html=True)

st.write(" ")

# --- ZONE D'INTÉGRATION ---
col_main, col_side = st.columns([2, 1])

with col_main:
    # 1. AFFICHAGE DU GRAPHE
    if os.path.exists("data/graphe_prerequis.png"):
        with st.expander("🗺️ Voir ma carte de progression"):
            st.image("data/graphe_prerequis.png", use_container_width=True)

    # 2. LE DIAGNOSTIC (Adapté à la structure d'Outhman)
    st.subheader("📝 Diagnostic de tes connaissances")
    notion_detectee = "Concepts Généraux"

    if os.path.exists("data/questions.json"):
        with open("data/questions.json", "r", encoding="utf-8") as f:
            questions_data = json.load(f)
        
        # On cherche le bloc correspondant au module (ex: "MSA")
        module_data = [m for m in questions_data if m.get('module') == module_select]
        
        if module_data:
            notion_item = module_data[0]
            notion_detectee = notion_item.get('notion', "Concepts Généraux")
            liste_questions = notion_item.get('questions', [])
            
            if liste_questions:
                q = liste_questions[0] # On prend la 1ère question du bloc
                txt_q = q.get('question')
                options = q.get('options', [])
                reponse_idx = q.get('reponse') # C'est un chiffre (0, 1, 2...)
                
                st.info(f"**Question sur {notion_detectee} :** {txt_q}")
                choix = st.radio("Ta réponse :", options, key="quiz_radio")
                
                if st.button("Vérifier ma réponse"):
                    # On compare le texte choisi avec le texte à l'index de la réponse
                    if choix == options[reponse_idx]:
                        st.success("✅ Bravo ! Tu maîtrises cette notion.")
                    else:
                        st.error(f"❌ Mauvaise réponse. La bonne était : {options[reponse_idx]}")
                        st.warning(f"L'Agent Diagnostique te conseille de réviser : **{notion_detectee}**")
        else:
            st.write("Chargement des questions...")

    st.divider()

    # 3. LES RESSOURCES (Ton travail)
    st.subheader(f"📖 Ressources pour maîtriser : {notion_detectee}")
    ressources = pedagogue.get_ressources(notion_detectee)
    
    if ressources:
        for res in ressources:
            st.markdown(f"""
            <div class="resource-card">
                <h4 style="margin:0;">{res['type']} : {res['notion']}</h4>
                <p style="color:gray;">{res['description']}</p>
            </div>
            """, unsafe_allow_html=True)
            st.link_button(f"🚀 Ouvrir la ressource ({res['type']})", res['url'])
    else:
        st.info("Sélectionne un module pour voir les ressources.")

with col_side:
    # 4. AUTO-ÉVALUATION (Tracker & Coach)
    st.markdown('<div style="background-color:#fff; padding:20px; border-radius:15px; border:1px solid #eee;">', unsafe_allow_html=True)
    st.subheader("📊 Auto-Évaluation")
    score = st.select_slider("Maîtrise (0-5)", options=[0, 1, 2, 3, 4, 5], value=3)
    
    if st.button("✅ Valider ma session"):
        with st.spinner('Synchronisation...'):
            time.sleep(1) 
            tracker.sauver_progres(nom, notion_detectee, score)
            prochaine = coach.calculer_revision(score)
            st.balloons() 
            st.success(f"Enregistré !")
            st.info(f"📅 Révision : **{prochaine}**")
    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.divider()
st.caption("Équipe : Outhman, DODO, Mohamed Yassir")
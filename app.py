import streamlit as st
from agents_dodo import AgentPedagogue, AgentTracker, AgentCoach
import time

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
# On utilise try/except pour éviter que l'app plante si les fichiers sont mal placés
try:
    pedagogue = AgentPedagogue()
    tracker = AgentTracker()
    coach = AgentCoach()
except Exception as e:
    st.error(f"Erreur d'initialisation : Vérifie que ressources.json est bien dans le dossier data. ({e})")
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

# Zone de contenu
col_main, col_side = st.columns([2, 1])

with col_main:
    # Simulation de la lacune identifiée par Outhman
    lacunes = {
        "MSA": "Agents Intelligents",
        "Data Mining": "K-Means Clustering",
        "Deep Learning": "Réseaux Convolutifs (CNN)",
        "Data Warehouse": "Processus ETL",
        "Big Data": "Apache Spark"
    }
    notion_cible = lacunes.get(module_select)

    st.markdown(f"#### 🎯 Ta cible du jour : `{notion_cible}`")
    
    st.subheader("📖 Ressources recommandées")
    ressources = pedagogue.get_ressources(notion_cible)
    
    if ressources:
        for res in ressources:
            st.markdown(f"""
            <div class="resource-card">
                <h4 style="margin:0;">{res['type']} : {res['notion']}</h4>
                <p style="color:gray;">{res['description']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Bouton pour ouvrir la ressource
            st.link_button(f"🚀 Ouvrir la ressource ({res['type']})", res['url'])
    else:
        st.info("Aucune ressource trouvée. Vérifie le fichier ressources.json.")

with col_side:
    st.markdown('<div style="background-color:#fff; padding:20px; border-radius:15px; border:1px solid #eee;">', unsafe_allow_html=True)
    st.subheader("📊 Auto-Évaluation")
    st.write("As-tu bien maîtrisé cette notion ?")
    score = st.select_slider("Note de compréhension", options=[0, 1, 2, 3, 4, 5], value=3)
    
    if st.button("✅ Valider ma session"):
        with st.spinner('Enregistrement en cours...'):
            time.sleep(1) 
            tracker.sauver_progres(nom, notion_cible, score)
            prochaine = coach.calculer_revision(score)
            
            st.balloons() 
            st.success(f"Bravo {nom} !")
            st.info(f"📅 Prochaine révision : **{prochaine}**")
    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.divider()
st.caption("Projet 4AISDR - Module SMA Agentic AI - Équipe Outhman DODO Mohamed Yassir")
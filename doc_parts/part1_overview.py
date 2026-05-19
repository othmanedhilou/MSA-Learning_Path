"""PARTIE I — Vue d'ensemble du projet (chapitres 1-3)"""

def build(g):
    """g est le module generate_doc_complete avec ses helpers."""

    # ═══════════════════════════════════════════════════════
    # CHAPITRE 1 — Résumé exécutif
    # ═══════════════════════════════════════════════════════
    g.section_header("1", "Résumé exécutif", "PARTIE I — VUE D'ENSEMBLE")

    g.p("Ce projet implémente un <b>Système Multi-Agents (SMA)</b> qui automatise "
        "la création de parcours d'apprentissage personnalisés. Conformément au sujet "
        "du Projet 4 du module 4AISDR, le système combine cinq agents spécialisés "
        "orchestrés par LangGraph, communiquant via un protocole inspiré de FIPA-ACL, "
        "et accédant à des outils via le Model Context Protocol (MCP) d'Anthropic.")

    g.h2("1.1 En une phrase")

    g.callout("Le projet en 30 mots",
        "Un Système Multi-Agents qui diagnostique le niveau d'un étudiant, identifie "
        "ses lacunes, construit un parcours personnalisé respectant les pré-requis, "
        "recommande des ressources via RAG vectoriel, et planifie les révisions "
        "avec SuperMemo-2.", color=g.ACCENT)

    g.h2("1.2 Les chiffres du projet")

    g.table_grid(
        ["Métrique", "Valeur"],
        [
            ["Lignes de code Python", "~2 500"],
            ["Fichiers Python", "12 modules"],
            ["Tests unitaires", "15 (tous passent)"],
            ["Agents spécialisés", "5"],
            ["Outils MCP exposés", "3"],
            ["Profils de démo", "3 (débutant, intermédiaire, avancé)"],
            ["Modules pédagogiques", "5 (MSA, DM, DL, DW, BD)"],
            ["Notions enseignées", "20 (4 par module)"],
            ["Ressources RAG indexées", "8 fichiers texte + catalogue JSON"],
            ["Performatives FIPA-ACL", "5 (REQUEST, INFORM, QUERY, CONFIRM, FAILURE)"],
            ["Conditional edges LangGraph", "1 (après diagnostic)"],
            ["Dimension des embeddings", "384"],
        ],
        col_widths=[6*g.cm, 11*g.cm])

    g.h2("1.3 Technologies clés utilisées")

    g.bullet([
        "<b>LangGraph 0.2+</b> — orchestration par graphe d'états (Chapitre 5 du cours)",
        "<b>MCP (Model Context Protocol)</b> — exposition standardisée des outils (Chapitre 6)",
        "<b>Chroma + sentence-transformers</b> — RAG vectoriel multilingue (Chapitre 2)",
        "<b>SuperMemo-2 (SM-2)</b> — algorithme de répétition espacée",
        "<b>FIPA-ACL</b> — protocole de communication inter-agents (Chapitre 7)",
        "<b>Streamlit</b> — interface utilisateur pour la démo",
        "<b>pytest</b> — tests unitaires et d'intégration",
    ])

    g.h2("1.4 Conformité aux exigences du sujet")

    g.table_grid(
        ["Exigence du sujet", "Statut", "Implémentation"],
        [
            ["Architecture multi-agents (≥3 agents)", "✅ DÉPASSÉ",
             "5 agents spécialisés orchestrés"],
            ["Communication inter-agents", "✅ FAIT",
             "Protocole A2A FIPA-ACL traçable"],
            ["RAG sur base vectorielle", "✅ FAIT",
             "Chroma + multilingual-MiniLM 384 dim"],
            ["Tool calling (@tool / @mcp-tool)", "✅ FAIT",
             "3 outils @mcp.tool() exposés"],
            ["Mémoire court terme", "✅ FAIT",
             "InMemorySaver LangGraph (checkpointing)"],
            ["Mémoire long terme", "✅ FAIT",
             "data/profils_etudiants.json persistant"],
            ["Code propre, modulaire, commenté", "✅ FAIT",
             "12 modules, type hints, docstrings"],
            ["README clair", "✅ FAIT",
             "README.md exhaustif (12 sections)"],
        ],
        col_widths=[5*g.cm, 2*g.cm, 10*g.cm])

    g.pagebreak()

    # ═══════════════════════════════════════════════════════
    # CHAPITRE 2 — Contexte et problématique
    # ═══════════════════════════════════════════════════════
    g.section_header("2", "Contexte et problématique")

    g.h2("2.1 Le problème pédagogique")

    g.p("L'enseignement supérieur fait face à une diversité croissante de profils "
        "d'étudiants : parcours antérieurs hétérogènes, rythmes d'apprentissage variables, "
        "styles cognitifs différents (visuel, textuel, kinesthésique). L'approche unique "
        "pour tous, héritée de l'enseignement de masse, montre ses limites.")

    g.p("L'apprentissage adaptatif est la réponse moderne : personnaliser le parcours "
        "en fonction des lacunes réelles et du style d'apprentissage de chacun. "
        "Cependant, sa mise en œuvre manuelle est impossible à grande échelle. "
        "Un enseignant ne peut pas créer un parcours individualisé pour chacun de ses "
        "200 étudiants.")

    g.callout("L'opportunité technologique",
        "L'avènement des LLMs (Large Language Models) et des Systèmes Multi-Agents "
        "(SMA) permet d'automatiser ce processus. Un SMA bien conçu peut diagnostiquer, "
        "planifier, recommander et suivre des centaines d'étudiants en parallèle, "
        "tout en restant adaptable et explicable.")

    g.h2("2.2 Les 5 défis à relever")

    g.bullet([
        "<b>Diagnostic précis</b> — identifier les vraies lacunes sans demander à "
        "l'étudiant de répondre à 100 questions",
        "<b>Construction du parcours</b> — respecter l'ordre des pré-requis et la "
        "courbe de difficulté",
        "<b>Sélection des ressources</b> — trouver le contenu pédagogique pertinent "
        "dans une bibliothèque potentiellement vaste",
        "<b>Mémorisation durable</b> — combattre la courbe de l'oubli d'Ebbinghaus "
        "via la répétition espacée",
        "<b>Suivi longitudinal</b> — adapter le parcours au fil des sessions selon "
        "les progrès réels",
    ])

    g.h2("2.3 Pourquoi un SMA et pas un agent unique ?")

    g.p("Le sujet du Projet 4 impose une architecture multi-agents. Mais cette "
        "exigence est <b>pédagogiquement justifiée</b> par le principe de "
        "<b>séparation des préoccupations</b> :")

    g.table_grid(
        ["Agent unique", "Système Multi-Agents"],
        [
            ["Code monolithique difficile à maintenir",
             "Modules indépendants, faciles à tester"],
            ["Un seul prompt système pour tout faire",
             "Un prompt spécialisé par agent (CoT plus efficace)"],
            ["Difficile à faire évoluer",
             "Ajouter un agent ne casse pas les autres"],
            ["Pas de parallélisme possible",
             "Pédagogue et Coach peuvent tourner en parallèle"],
            ["Pas d'audit fin des décisions",
             "Chaque agent journalise ses messages A2A"],
        ],
        col_widths=[8.5*g.cm, 8.5*g.cm])

    g.h2("2.4 Pourquoi un parcours adaptatif ?")

    g.p("La théorie pédagogique sous-jacente est la <b>Zone Proximale de Développement</b> "
        "(ZPD) de Lev Vygotski (1934). Cette zone correspond à ce que l'étudiant peut "
        "apprendre avec une aide appropriée, mais pas seul. Si on lui présente du "
        "contenu trop facile, il s'ennuie. Trop difficile, il se décourage.")

    g.callout("La règle d'or",
        "<b>Le bon contenu pédagogique se trouve toujours juste au-dessus du niveau "
        "actuel de l'étudiant.</b> Notre système identifie ce niveau par le diagnostic "
        "adaptatif, puis ordonne les notions par le graphe de pré-requis. C'est "
        "l'application directe de la ZPD.",
        color=g.SUCCESS)

    g.pagebreak()

    # ═══════════════════════════════════════════════════════
    # CHAPITRE 3 — Vue d'ensemble de l'architecture
    # ═══════════════════════════════════════════════════════
    g.section_header("3", "Vue d'ensemble de l'architecture")

    g.p("L'architecture s'articule autour de trois couches : "
        "<b>orchestration</b> (LangGraph), <b>communication</b> (A2A FIPA-ACL), "
        "<b>outils</b> (MCP). Chaque agent est un nœud du graphe, et le State "
        "partagé sert de tableau blanc (pattern Blackboard).")

    g.h2("3.1 Diagramme d'architecture globale")

    g.code_block("""
┌──────────────────────────────────────────────────────────────────────────┐
│                       COUCHE UTILISATEUR                                 │
│                                                                          │
│                    ┌──────────────────────────────┐                      │
│                    │  Streamlit Interface         │                      │
│                    │  - Phase 1 : Accueil         │                      │
│                    │  - Phase 2 : Diagnostic      │                      │
│                    │  - Phase 3 : Résultats + A2A │                      │
│                    └────────────┬─────────────────┘                      │
└─────────────────────────────────┼────────────────────────────────────────┘
                                  │ run_session(nom, module, profile)
                                  ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                  COUCHE ORCHESTRATION (LangGraph)                        │
│                                                                          │
│                ┌─────────┐                                               │
│                │  START  │                                               │
│                └────┬────┘                                               │
│                     ▼                                                    │
│            ┌────────────────┐                                            │
│            │ Diagnosticien  │ ─── A2A REQUEST/INFORM                     │
│            └────────┬───────┘                                            │
│                     │                                                    │
│              ╔══════╧══════╗                                             │
│              ║ Conditional ║   ← VALEUR AJOUTÉE LANGGRAPH                │
│              ╚══════╤══════╝                                             │
│            ≥80%    │    <80%                                             │
│          ┌────────┘      └────────┐                                      │
│          ▼                        ▼                                      │
│    ┌──────────┐         ┌────────────────┐                               │
│    │  Coach   │         │ Planificateur  │ ←── Mind Layer (CoT)          │
│    │ (direct) │         └────────┬───────┘                               │
│    └────┬─────┘                  ▼                                       │
│         │              ┌──────────────────┐                              │
│         │              │    Pédagogue     │ ←── RAG vectoriel            │
│         │              └──────────┬───────┘                              │
│         │                         ▼                                      │
│         │                  ┌──────────┐                                  │
│         │                  │  Coach   │ ←── SM-2                         │
│         │                  └────┬─────┘                                  │
│         └──────────────────────┘                                         │
│                              ▼                                           │
│                        ┌──────────┐                                      │
│                        │ Tracker  │ ←── Mémoire LT                       │
│                        └─────┬────┘                                      │
│                              ▼                                           │
│                          ┌───────┐                                       │
│                          │  END  │                                       │
│                          └───────┘                                       │
└──────────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ messages A2A FIPA-ACL
                                  ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                COUCHE OUTILS (MCP + RAG + SM-2)                          │
│                                                                          │
│    ┌─────────────────────────┐    ┌──────────────────────┐               │
│    │  learning_tools_server  │    │   rag_engine.py      │               │
│    │  ─ search_ressources    │    │   ─ Chroma DB        │               │
│    │  ─ compute_sm2_schedule │    │   ─ Embeddings 384d  │               │
│    │  ─ update_profile_ltm   │    │   ─ Cosine sim       │               │
│    └─────────────────────────┘    └──────────────────────┘               │
│                                                                          │
│    ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐      │
│    │  sm2.py      │    │ mind_layer   │    │  a2a_protocol.py     │      │
│    │ SuperMemo-2  │    │  LLM + CoT   │    │   FIPA-ACL helpers   │      │
│    └──────────────┘    └──────────────┘    └──────────────────────┘      │
└──────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                  COUCHE DONNÉES (persistance JSON)                       │
│                                                                          │
│   ┌────────────┐  ┌─────────────┐  ┌────────────┐  ┌─────────────────┐   │
│   │ questions  │  │  prerequis  │  │ profils_   │  │ profils_        │   │
│   │   .json    │  │   .json     │  │ demo.json  │  │ etudiants.json  │   │
│   └────────────┘  └─────────────┘  └────────────┘  └─────────────────┘   │
│                                                                          │
│   ┌────────────┐  ┌─────────────┐  ┌────────────┐  ┌─────────────────┐   │
│   │ ressources │  │ historique  │  │ parcours_  │  │ chroma_db/      │   │
│   │   .json    │  │   .json     │  │etudiants   │  │ (vector store)  │   │
│   └────────────┘  └─────────────┘  └────────────┘  └─────────────────┘   │
└──────────────────────────────────────────────────────────────────────────┘
""")

    g.h2("3.2 Les 4 couches expliquées")

    g.h3("Couche 1 — Interface utilisateur (Streamlit)")
    g.p("Point d'entrée pour la démo. Trois phases :")
    g.bullet([
        "<b>Phase Accueil</b> : sélection d'un profil (Amina/Yassine/Sarah) et d'un module",
        "<b>Phase Diagnostic</b> : barre de progression pendant l'exécution de l'orchestrateur",
        "<b>Phase Résultats</b> : affichage du diagnostic, parcours, ressources RAG, "
        "et timeline A2A en temps réel",
    ])

    g.h3("Couche 2 — Orchestration (LangGraph)")
    g.p("Le cœur du système. Le graphe LangGraph définit :")
    g.bullet([
        "<b>State partagé</b> (TypedDict) : tableau blanc lu et modifié par les nodes",
        "<b>5 nodes</b> : un par agent spécialisé",
        "<b>1 conditional edge</b> : routage dynamique selon le score (≥80% → coach direct)",
        "<b>InMemorySaver</b> : checkpointing pour reprise sur erreur",
    ])

    g.h3("Couche 3 — Outils (MCP, RAG, SM-2, LLM)")
    g.p("Les modules fonctionnels appelés par les agents :")
    g.bullet([
        "<b>learning_tools_server.py</b> : 3 outils @mcp.tool() exposés via stdio",
        "<b>rag_engine.py</b> : moteur RAG vectoriel (Chroma + embeddings)",
        "<b>sm2.py</b> : algorithme SuperMemo-2 de répétition espacée",
        "<b>mind_layer.py</b> : couche LLM avec Chain-of-Thought (fallback déterministe)",
        "<b>a2a_protocol.py</b> : helpers FIPA-ACL pour les messages inter-agents",
    ])

    g.h3("Couche 4 — Données (JSON + Chroma)")
    g.p("La persistance se fait en deux modes :")
    g.bullet([
        "<b>JSON</b> pour les données structurées (questions, prérequis, profils)",
        "<b>Chroma</b> (SQLite sous-jacent) pour les vecteurs d'embedding",
    ])

    g.h2("3.3 Flux d'une session complète")

    g.code_block("""
TEMPS T0 : utilisateur clique "Démarrer session Amina"
    │
    ├─ Streamlit appelle : run_session("Amina", "MSA", profil_amina)
    │
TEMPS T1 : Orchestrateur LangGraph démarre
    │
    ├─ build_graph() crée le StateGraph
    ├─ Le State initial est construit avec profile_data
    ├─ Premier message A2A (User → Orchestrateur, REQUEST)
    │
TEMPS T2 : Node diagnosticien
    │
    ├─ A2A : Orchestrateur → Diagnosticien (REQUEST)
    ├─ Appel : AgentDiagnostician.run_diagnostic_for_profile()
    ├─ Calcul du score basé sur le profil + historique
    ├─ A2A : Diagnosticien → Orchestrateur (INFORM score=0%)
    │
TEMPS T3 : Conditional edge évalue
    │
    ├─ route_after_diagnostic(state) → "planificateur" (score < 80%)
    │
TEMPS T4 : Node planificateur
    │
    ├─ A2A : Orchestrateur → Planificateur (REQUEST)
    ├─ Appel : AgentPlanificateur.construire_parcours()
    ├─ Génère 4 étapes ordonnées par prérequis
    ├─ Mind Layer : reason_planificateur() génère CoT
    ├─ A2A : Planificateur → Orchestrateur (INFORM nb_etapes=4)
    │
TEMPS T5 : Node pedagogue
    │
    ├─ A2A : Orchestrateur → Pedagogue (QUERY)
    ├─ Appel : RAGEngine.search("Agents Intelligents", k=3)
    ├─ Chroma : embedding query → similarité cosine → top-K chunks
    ├─ A2A : Pedagogue → Orchestrateur (INFORM nb_ressources=5)
    │
TEMPS T6 : Node coach
    │
    ├─ A2A : Orchestrateur → Coach (REQUEST)
    ├─ Appel : SM2.calculer() avec qualite=0 (score=0%)
    ├─ Calcul : intervalle=1 jour, prochaine_revision="demain"
    ├─ A2A : Coach → Orchestrateur (INFORM)
    │
TEMPS T7 : Node tracker
    │
    ├─ A2A : Orchestrateur → Tracker (REQUEST)
    ├─ AgentTracker.sauver_progres() → historique_etudiants.json
    ├─ Profil sauvé dans data/profils_etudiants.json
    ├─ A2A : Tracker → Orchestrateur (CONFIRM)
    │
TEMPS T8 : END
    │
    ├─ Streamlit reçoit le State final
    ├─ Affichage : stats, parcours, ressources, timeline A2A
    │
DURÉE TOTALE : ~2-3 secondes
""")

    g.callout("Point clé",
        "<b>Tous les agents tournent dans le même processus Python</b>, donc "
        "les appels sont des fonctions Python normales. Le \"protocole A2A\" est "
        "ici une convention de format des messages — pas un vrai protocole réseau "
        "(qui serait dispensable pour le scope académique).",
        color=g.ACCENT)

    g.pagebreak()

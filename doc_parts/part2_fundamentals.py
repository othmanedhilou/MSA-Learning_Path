"""PARTIE II — Fondamentaux du cours (chapitres 4-9)"""

def build(g):
    # ═══════════════════════════════════════════════════════
    # CHAPITRE 4 — Prompt Engineering
    # ═══════════════════════════════════════════════════════
    g.section_header("4", "Prompt Engineering — CoT et ReAct",
                     "PARTIE II — FONDAMENTAUX DU COURS")

    g.p("Le Prompt Engineering est <b>l'art de concevoir des instructions précises</b> "
        "pour qu'un LLM produise la sortie souhaitée. C'est la fondation de tout système "
        "agentique : sans prompt rigoureux, même le meilleur modèle dérive.")

    g.h2("4.1 Anatomie d'un prompt complet")

    g.code_block("""prompt = [
    # Partie FIXE — System Message
    {
        "role": "system",
        "content": "Tu es l'Agent Planificateur d'un SMA pédagogique. "
                   "Tu raisonnes étape par étape (CoT). "
                   "Format : 4-6 phrases max, étapes numérotées."
    },
    # Partie OPTIONNELLE — Few-shot examples
    {"role": "user", "content": "Exemple 1 : ..."},
    {"role": "assistant", "content": "Étape 1... Étape 2... Réponse"},
    # Partie VARIABLE — User input réel
    {
        "role": "user",
        "content": "Étudiant Amina, score 0%, lacunes : Agents..."
    }
]""")

    g.explain("Le System Message définit le RÔLE permanent. Les exemples few-shot "
              "(optionnels) montrent le FORMAT attendu. La dernière entrée est la "
              "vraie question. L'ordre est important : la vraie question doit "
              "TOUJOURS être en dernier.")

    g.h2("4.2 Les 4 techniques enseignées dans le cours")

    g.table_grid(
        ["Technique", "Principe", "Quand l'utiliser"],
        [
            ["<b>Zero-Shot</b>",
             "Poser la tâche directement, sans exemple",
             "Tâches simples, classification triviale"],
            ["<b>Few-Shot</b>",
             "Fournir 1-5 exemples avant la vraie question",
             "Format de sortie complexe, ton spécifique"],
            ["<b>Chain-of-Thought</b>",
             "Forcer le LLM à raisonner étape par étape",
             "Calculs, raisonnements logiques, décompositions"],
            ["<b>ReAct</b>",
             "Reason + Act : raisonne, appelle un outil, observe, recommence",
             "Quand une information manque (besoin d'un outil externe)"],
        ],
        col_widths=[3*g.cm, 7*g.cm, 7*g.cm])

    g.h2("4.3 Chain-of-Thought (CoT) dans NOTRE projet")

    g.p("Le fichier <i>mind_layer.py</i> implémente le CoT dans le Planificateur. "
        "Voici le System Prompt utilisé :")

    g.code_block("""PLANIFICATEUR_SYSTEM_PROMPT = '''Tu es l'Agent Planificateur d'un Système
Multi-Agents pédagogique.

Ton rôle : analyser le diagnostic d'un étudiant et expliquer le parcours
d'apprentissage optimal en utilisant la technique Chain-of-Thought
(raisonnement étape par étape).

Règles :
1. Sois concis : 4-6 phrases maximum.
2. Raisonne en étapes numérotées (Étape 1, Étape 2, ...).
3. Justifie l'ordre des notions par les pré-requis pédagogiques.
4. Mentionne la durée estimée et le rythme de répétition espacée (SM-2).
5. Ne mentionne JAMAIS les concurrents ou autres systèmes externes.

Format de sortie : raisonnement structuré en étapes, puis recommandation finale.'''""")

    g.h3("Exemple de raisonnement CoT généré")

    g.code_block("""Étape 1 - Analyse : Score 50% avec 2 lacune(s) sur les notions avancées.

Étape 2 - Identification des prérequis : Les notions maîtrisées
(Agents Intelligents, Communication Inter-agents) servent de fondation.

Étape 3 - Construction du parcours : 2 étape(s) ordonnées par
complexité croissante.

Étape 4 - Planification SM-2 : Révisions espacées progressives
(intervalles croissants si succès).""")

    g.callout("Pourquoi CoT améliore la qualité ?",
        "Quand un LLM raisonne étape par étape, il est forcé d'expliciter chaque "
        "sous-décision. Cela évite les sauts logiques et permet à un humain "
        "(ou un autre agent) de vérifier le raisonnement. Études (Wei et al., 2022) : "
        "+20 points de précision sur des benchmarks de raisonnement.")

    g.h2("4.4 ReAct (Reason + Act)")

    g.p("ReAct est le pattern fondamental de l'Agentic AI. Le LLM ne se contente plus "
        "de raisonner sur ses connaissances internes : il <b>agit dans le monde</b> "
        "en appelant des outils, puis intègre les observations dans son raisonnement.")

    g.code_block("""# Cycle ReAct typique
Thought  : "J'ai besoin de connaître la politique de remboursement"
Action   : consulter_politique_db()
Observation : {"prorata": True, "frais_fixes": 10}
Thought  : "Calculer 350 × (8/30) puis retirer 10 DH"
Action   : compute(expr="350 * (8/30) - 10")
Observation : 83.33
Final    : "Le remboursement est de 83.33 DH" """)

    g.h3("ReAct dans notre projet")

    g.p("Notre orchestrateur LangGraph implémente une <b>version structurée de ReAct</b> : "
        "chaque node est une étape Action, le State conserve les Observations, "
        "les conditional edges sont des décisions de Reasoning.")

    g.bullet([
        "<b>Thought</b> : decision logic dans <i>route_after_diagnostic()</i>",
        "<b>Action</b> : appel d'un node (Diagnosticien, Planificateur, etc.)",
        "<b>Observation</b> : mise à jour du State avec le résultat du node",
        "<b>Loop</b> : possible via les conditional edges (revenir en arrière)",
    ])

    g.pagebreak()

    # ═══════════════════════════════════════════════════════
    # CHAPITRE 5 — RAG vectoriel
    # ═══════════════════════════════════════════════════════
    g.section_header("5", "RAG vectoriel en profondeur")

    g.p("RAG (Retrieval-Augmented Generation) enrichit un LLM avec une <b>base de "
        "connaissances externe</b> interrogée dynamiquement — sans réentraîner le "
        "modèle. C'est la solution standard contre les hallucinations et l'information "
        "périmée.")

    g.h2("5.1 Pipeline RAG complet")

    g.code_block("""PHASE 1 — INDEXATION (une fois au démarrage)

  Documents bruts
       │
       ▼
  [1] Chunking récursif
       │  - séparateur \\n\\n (paragraphe)
       │  - puis \\n (ligne)
       │  - puis . (phrase)
       │  - puis espace (mot)
       │
       ▼
  Chunks (textes courts)
       │
       ▼
  [2] Embedding par chunk
       │  modèle : multilingual-MiniLM
       │  dimension : 384
       │
       ▼
  Vecteurs 384-D
       │
       ▼
  [3] Indexation Chroma
       │  - SQLite sous-jacent
       │  - métadonnées préservées
       │
       ▼
  Vector Store persistant


PHASE 2 — RECHERCHE (à chaque query)

  Query utilisateur ("Communication inter-agents")
       │
       ▼
  [1] Embedding de la query
       │  même modèle qu'à l'indexation
       │
       ▼
  Vecteur query 384-D
       │
       ▼
  [2] Similarité cosine vs tous les chunks
       │  cos(A,B) = (A·B) / (||A|| × ||B||)
       │
       ▼
  Liste triée par score
       │
       ▼
  [3] Top-K retournés
       │  K=3 par défaut
       │
       ▼
  3 chunks les plus pertinents""")

    g.h2("5.2 Le chunking en détail")

    g.p("Le <b>chunking</b> est l'opération qui découpe un texte long en segments "
        "courts. C'est l'une des décisions les plus impactantes du pipeline RAG.")

    g.h3("Les 5 méthodes de chunking (cours)")

    g.table_grid(
        ["Méthode", "Principe", "Avantage", "Limite"],
        [
            ["Fixed-Size", "N caractères/tokens fixes",
             "Simple, rapide",
             "Coupe au milieu des phrases"],
            ["Fixed + Overlap", "Avec chevauchement (10-20%)",
             "Préserve le contexte aux frontières",
             "Duplication, stockage +20%"],
            ["<b>Recursive</b>", "Cascade : paragraphe → ligne → phrase → mot",
             "Respecte la structure naturelle",
             "Tailles inégales"],
            ["Semantic", "Coupe quand sim(P_i, P_i+1) &lt; θ",
             "Chunks thématiquement purs",
             "Coûteux (embedding au chunking)"],
            ["Agentic", "Un LLM décompose en propositions",
             "Précision maximale",
             "Très coûteux (1 appel LLM/chunk)"],
        ],
        col_widths=[2.5*g.cm, 4*g.cm, 5*g.cm, 5.5*g.cm])

    g.h3("Notre choix : Recursive Chunking")

    g.code_block("""# rag_engine.py — extrait
splitter = RecursiveCharacterTextSplitter(
    chunk_size=300,        # 300 caractères par chunk
    chunk_overlap=50,      # 50 caractères de chevauchement
    separators=[
        "\\n\\n",          # 1. Paragraphe (essai prioritaire)
        "\\n",             # 2. Ligne (si trop long)
        ".",               # 3. Phrase
        " ",               # 4. Mot
        ""                 # 5. Caractère (dernier recours)
    ]
)
chunks = splitter.split_documents(docs)""")

    g.explain("Pour nos ressources pédagogiques (descriptions de 200-500 caractères), "
              "le chunking récursif est idéal : il préserve l'unité sémantique des "
              "définitions courtes, et l'overlap de 50 caractères évite de couper "
              "une définition cruciale.")

    g.h2("5.3 Les embeddings en détail")

    g.p("Un <b>embedding</b> est une représentation vectorielle d'un texte. "
        "Les textes sémantiquement proches ont des vecteurs proches.")

    g.h3("Notre modèle : multilingual-MiniLM")

    g.table_grid(
        ["Caractéristique", "Valeur", "Justification"],
        [
            ["Nom", "paraphrase-multilingual-MiniLM-L12-v2", ""],
            ["Dimension", "384",
             "Compromis qualité/vitesse (vs 768 BERT, 1536 OpenAI)"],
            ["Langues", "50+ dont français", "Multilingue natif"],
            ["Taille", "~120 MB",
             "Léger, tourne sur CPU sans GPU"],
            ["Coût", "Gratuit, local",
             "Pas d'API key, pas de réseau requis"],
            ["Performance", "Score MTEB 60+",
             "Suffisant pour notre cas d'usage"],
        ],
        col_widths=[4*g.cm, 6*g.cm, 7*g.cm])

    g.h3("Comment fonctionne un embedding (intuition)")

    g.code_block("""Texte : "Communication entre agents"
            │
            ▼
       Tokenisation
            │
            ▼
  ["Communication", "entre", "agents"]
            │
            ▼
   Modèle Transformer
   (Self-Attention)
            │
            ▼
  Vecteur 384-D : [0.23, -0.41, 0.87, ..., 0.12]
                   |     |     |          |
                   axes sémantiques (appris)""")

    g.callout("Propriétés magiques",
        "Les embeddings ont des propriétés algébriques surprenantes :<br/>"
        "<i>vec(\"roi\") - vec(\"homme\") + vec(\"femme\") ≈ vec(\"reine\")</i><br/><br/>"
        "C'est ce qui permet la recherche sémantique : un mot inconnu peut être "
        "trouvé via son contexte sémantique, pas seulement par correspondance exacte.")

    g.h2("5.4 La similarité cosine")

    g.code_block("""               A · B          Σ(a_i × b_i)
cos(A, B) = ─────────── = ─────────────────────────
            ||A|| × ||B||   √(Σa_i²) × √(Σb_i²)

Valeur entre -1 et 1 :
  ▸  1.0 → vecteurs identiques
  ▸  0.0 → vecteurs orthogonaux (sans relation)
  ▸ -1.0 → vecteurs opposés""")

    g.h3("Exemple numérique vu en démo")

    g.code_block("""Query : "K-Means partitionnement"
   ↓ embedding
Vecteur 384-D : [0.12, -0.34, ...]

Comparaison avec tous les chunks indexés :

Chunk "K-Means Clustering"   → cos = 0.634 (très proche !)
Chunk "K-Means Algorithm"    → cos = 0.598
Chunk "Réseaux de neurones"  → cos = 0.142 (loin)
Chunk "Recette guacamole"    → cos = 0.018 (très loin)

Top-3 retourné = [K-Means Clustering, K-Means Algorithm, ...]""")

    g.pagebreak()

    # ═══════════════════════════════════════════════════════
    # CHAPITRE 6 — Agentic AI
    # ═══════════════════════════════════════════════════════
    g.section_header("6", "Agentic AI : Body / Mind / Memory")

    g.p("Un agent IA n'est pas un simple chatbot. C'est un système qui combine "
        "<b>raisonnement, action et mémoire</b> pour accomplir des tâches complexes "
        "de manière autonome.")

    g.h2("6.1 La formule fondamentale du cours")

    g.callout("Définition centrale",
        "<b>AGENT = Mind (LLM qui raisonne) + Body (outils pour agir) + Memory (ce qu'il retient) "
        "+ Loop (boucle décision / action / observation)</b><br/><br/>"
        "Le LLM ne fait JAMAIS d'appel direct à un outil : il génère du JSON. "
        "Le framework intercepte ce JSON, exécute la fonction Python, puis renvoie "
        "le résultat au LLM.",
        color=g.ACCENT)

    g.h2("6.2 Application à NOS 5 agents")

    g.table_grid(
        ["Agent", "Mind", "Body", "Memory"],
        [
            ["Diagnosticien",
             "Logique adaptative IRT-simplifiée",
             "questions.json + prerequis.json",
             "data/rapports_diagnostic.json"],
            ["Planificateur",
             "LLM CoT (via mind_layer)",
             "planner.py (graphe prérequis)",
             "data/parcours_etudiants.json"],
            ["Pédagogue",
             "Recherche vectorielle",
             "rag_engine.py + Chroma",
             "Stateless (recalcule à chaque appel)"],
            ["Coach",
             "Formule mathématique SM-2",
             "sm2.py",
             "data/sm2_profils.json"],
            ["Tracker",
             "Logique I/O",
             "agents_dodo.AgentTracker",
             "data/historique_etudiants.json + profils_etudiants.json"],
        ],
        col_widths=[3*g.cm, 4*g.cm, 5*g.cm, 5*g.cm])

    g.h2("6.3 Le décorateur @tool (Chapitre 5 du cours)")

    g.code_block("""from langchain.tools import tool

@tool
def get_weather(location: str) -> str:
    '''Get current weather for a city.
    Use this when the user asks about weather in a specific place.'''
    return f"Weather in {location}: Sunny, 32°C"

agent = create_agent(model=llm, tools=[get_weather])""")

    g.explain("La <b>docstring est l'API publique vue par le LLM</b>. Une docstring "
              "vague = mauvaises décisions de l'agent. Toujours indiquer : "
              "(1) QUE fait l'outil, (2) QUAND l'utiliser, (3) FORMAT exact des arguments.")

    g.h2("6.4 La mémoire en pratique")

    g.h3("Mémoire court-terme (InMemorySaver)")

    g.code_block("""from langgraph.checkpoint.memory import InMemorySaver

graph = workflow.compile(checkpointer=InMemorySaver())

# Premier appel
result1 = graph.invoke(
    input={"nom_etudiant": "Othmane", "messages": []},
    config={"configurable": {"thread_id": "session-001"}}
)

# Deuxième appel : MÊME thread_id
# → le state du premier appel est restauré automatiquement
result2 = graph.invoke(
    input={"messages": [HumanMessage("Quel était mon score ?")]},
    config={"configurable": {"thread_id": "session-001"}}
)""")

    g.h3("Mémoire long-terme (JSON)")

    g.code_block("""# data/profils_etudiants.json
{
  "Othmane": {
    "created_at": "2026-05-15T10:23:45",
    "module": "MSA",
    "score_final": 75,
    "notion_cible": "Framework LangGraph",
    "prochaine_revision": "2026-05-16",
    "timestamp": "2026-05-15T10:23:45"
  }
}""")

    g.pagebreak()

    # ═══════════════════════════════════════════════════════
    # CHAPITRE 7 — LangGraph
    # ═══════════════════════════════════════════════════════
    g.section_header("7", "LangGraph : State / Nodes / Edges")

    g.p("LangGraph est le framework <b>bas niveau</b> d'orchestration de LangChain. "
        "Il modélise un agent comme un <b>graphe d'états et de transitions</b>.")

    g.h2("7.1 LangChain vs LangGraph (récapitulatif)")

    g.table_grid(
        ["Critère", "LangChain", "LangGraph"],
        [
            ["Modèle mental", "Chaîne linéaire",
             "Graphe avec cycles"],
            ["Branches conditionnelles", "Limitées (if dans le code)",
             "Natives (add_conditional_edges)"],
            ["Boucles", "Difficiles", "Triviales (1 ligne)"],
            ["Human-in-the-loop", "Limitée", "Native"],
            ["Checkpointing", "À implémenter manuellement",
             "Automatique (InMemorySaver, PostgresSaver)"],
            ["Visualisation", "Limitée",
             "Native (draw_mermaid_png)"],
        ],
        col_widths=[3*g.cm, 7*g.cm, 7*g.cm])

    g.h2("7.2 Les 3 concepts fondamentaux")

    g.h3("STATE — l'état partagé")

    g.code_block("""from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages
from operator import add

class LearningState(TypedDict):
    nom_etudiant: str
    module: str
    messages: Annotated[list, add_messages]   # reducer add_messages
    communications: Annotated[list, add]      # reducer add (concat)
    diagnostic: dict
    parcours: list
    ressources: list
    revision: dict""")

    g.callout("Le rôle des Reducers",
        "Sans reducer, un dict retourné par un node REMPLACE le champ existant. "
        "Avec <i>Annotated[list, add]</i>, il s'AJOUTE (concaténation). C'est ce qui "
        "permet à <b>communications</b> d'ACCUMULER les messages A2A à travers les "
        "nodes (au lieu d'écraser à chaque tour).",
        color=g.ACCENT)

    g.h3("NODES — les actions")

    g.code_block("""def diagnosticien_node(state: LearningState) -> dict:
    '''Un node prend le State, fait son travail, retourne les champs modifiés.'''

    # Lire l'état actuel
    module = state["module"]
    profile = state["profile_data"]

    # Faire le travail
    rapport = _diagnosticien.run_diagnostic_for_profile(module, profile)

    # Retourner UNIQUEMENT les champs modifiés
    # LangGraph fusionne automatiquement avec les reducers
    return {
        "diagnostic": rapport,
        "communications": [msg_request, msg_inform]
    }""")

    g.h3("EDGES — les transitions")

    g.bullet([
        "<b>Edge normale</b> : <i>graph.add_edge(\"a\", \"b\")</i> — toujours a → b",
        "<b>Conditional edge</b> : une fonction examine le state et choisit la suite",
        "<b>START / END</b> : nœuds spéciaux d'entrée et de sortie",
    ])

    g.code_block("""def route_after_diagnostic(state) -> Literal['planificateur', 'coach']:
    if state['diagnostic']['pourcentage'] >= 80:
        return 'coach'           # skip planif !
    return 'planificateur'

graph.add_conditional_edges(
    'diagnosticien',
    route_after_diagnostic,
    {
        'planificateur': 'planificateur',
        'coach': 'coach'
    }
)""")

    g.callout("Pourquoi cette conditional edge est CRUCIALE",
        "C'est la <b>valeur ajoutée majeure</b> de LangGraph vs LangChain. "
        "En LangChain pur, il aurait fallu créer deux chaînes parallèles et un "
        "dispatcher manuel. Avec LangGraph, c'est une fonction de 3 lignes.",
        color=g.SUCCESS)

    g.pagebreak()

    # ═══════════════════════════════════════════════════════
    # CHAPITRE 8 — MCP
    # ═══════════════════════════════════════════════════════
    g.section_header("8", "MCP : Model Context Protocol")

    g.p("MCP est un <b>protocole ouvert proposé par Anthropic fin 2024</b>, adopté par "
        "OpenAI, Google, Microsoft et LangChain. Il standardise la communication entre "
        "agents et services externes via JSON-RPC 2.0.")

    g.h2("8.1 L'analogie clé")

    g.callout("La phrase à retenir",
        "<b>« MCP est au LLM ce que l'USB-C est au téléphone — un câble logiciel universel. »</b><br/><br/>"
        "Sans MCP : 4 agents × 4 services = 16 connecteurs à maintenir.<br/>"
        "Avec MCP : 4 + 4 = 8 connexions.<br/>"
        "<b>De O(M×N) à O(M+N).</b>",
        color=g.ACCENT)

    g.h2("8.2 Architecture MCP")

    g.code_block("""┌─────────────────────────┐         ┌──────────────────────┐
│   HOST (notre app)      │         │   SERVEUR MCP        │
│                         │         │                      │
│   ┌─────────────────┐   │         │   ┌──────────────┐   │
│   │ Agent LangGraph │   │         │   │ @mcp.tool()  │   │
│   └────────┬────────┘   │         │   │ search_rag   │   │
│            │            │         │   │ compute_sm2  │   │
│            ▼            │  stdio  │   │ update_ltm   │   │
│   ┌─────────────────┐   │ JSON-RPC│   └──────┬───────┘   │
│   │  Client MCP     │ ◄─┼─────────┼──►       │           │
│   │ langchain-mcp   │   │         │          ▼           │
│   └─────────────────┘   │         │   ┌──────────────┐   │
│                         │         │   │ rag_engine   │   │
└─────────────────────────┘         │   │ sm2 / files  │   │
                                    │   └──────────────┘   │
                                    └──────────────────────┘""")

    g.h2("8.3 Notre serveur MCP")

    g.code_block("""# learning_tools_server.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("learning-tools-server")

@mcp.tool()
def search_ressources_rag(query: str, n_results: int = 3) -> list:
    '''Search learning resources via RAG.
    Use this when an agent needs pedagogical content.'''
    return _rag.chercher_ressources(query)[:n_results]

@mcp.tool()
def compute_sm2_schedule(etudiant: str, notion: str, qualite: int) -> dict:
    '''Compute next review date using SuperMemo-2.'''
    return _sm2.calculer(etudiant, notion, qualite)

@mcp.tool()
def update_profile_ltm(etudiant: str, updates: dict) -> dict:
    '''Update student long-term memory profile.'''
    # Persistance JSON
    return {"status": "saved", "etudiant": etudiant}

if __name__ == "__main__":
    mcp.run(transport="stdio")""")

    g.h2("8.4 Les 3 primitives MCP")

    g.bullet([
        "<b>Tools</b> — actions exécutables (équivalent @tool LangChain). C'est ce qu'on utilise.",
        "<b>Resources</b> — données lisibles (fichiers, BDD). Non utilisés ici.",
        "<b>Prompts</b> — templates partagés. Non utilisés ici.",
    ])

    g.h2("8.5 Sécurité MCP — les 6 règles non négociables")

    g.bullet([
        "1. <b>N'exécutez jamais un serveur MCP non audité</b> sur une machine sensible",
        "2. <b>Isolez le processus</b> (container, utilisateur dédié, sandbox)",
        "3. <b>Aucun secret en dur</b> — variables d'environnement uniquement",
        "4. <b>Authentifiez les serveurs HTTP</b> (OAuth, Bearer token)",
        "5. <b>Journalisez tous les appels sensibles</b> (audit RGPD)",
        "6. <b>Moindre privilège</b> — lecture seule = pas d'écriture",
    ])

    g.pagebreak()

    # ═══════════════════════════════════════════════════════
    # CHAPITRE 9 — SMA + A2A
    # ═══════════════════════════════════════════════════════
    g.section_header("9", "SMA et protocole A2A (FIPA-ACL)")

    g.p("Un Système Multi-Agents (SMA) consiste à <b>orchestrer plusieurs agents "
        "spécialisés</b> qui collaborent pour résoudre un problème complexe. "
        "Le protocole <b>A2A (Agent-to-Agent)</b> standardise leurs échanges.")

    g.h2("9.1 Pourquoi plusieurs agents ?")

    g.table_grid(
        ["Un seul agent", "SMA (plusieurs agents)"],
        [
            ["Surcharge cognitive",
             "Spécialisation (chacun expert dans son domaine)"],
            ["Traitement séquentiel forcé",
             "Parallélisme possible"],
            ["Point unique de défaillance",
             "Résilience (un agent en panne ≠ tout arrêté)"],
            ["Difficile à faire évoluer",
             "Scalabilité (ajout d'agents simple)"],
        ],
        col_widths=[8.5*g.cm, 8.5*g.cm])

    g.h2("9.2 Le protocole FIPA-ACL")

    g.p("FIPA-ACL (Foundation for Intelligent Physical Agents - Agent Communication "
        "Language) est <b>le standard international</b> de communication entre agents, "
        "défini par IEEE Computer Society depuis 1996.")

    g.h3("Structure d'un message FIPA-ACL")

    g.code_block("""{
  "msg_id": "uuid-1234",
  "timestamp": "10:23:45",
  "from": "Orchestrateur",
  "to": "Diagnosticien",
  "performative": "REQUEST",      ← le type d'acte de langage
  "content": {                    ← contenu sémantique
    "action": "run_diagnostic",
    "module": "MSA"
  },
  "conversation_id": "session-001"
}""")

    g.h3("Les performatives FIPA-ACL standards")

    g.table_grid(
        ["Performative", "Usage", "Exemple dans notre projet"],
        [
            ["REQUEST", "Demande une action",
             "Orchestrateur → Diagnosticien : \"lance le diagnostic\""],
            ["INFORM", "Transmet une information",
             "Diagnosticien → Orchestrateur : \"score = 50%\""],
            ["QUERY", "Demande une information",
             "Orchestrateur → Pédagogue : \"trouve ressources pour 'agents'\""],
            ["CONFIRM", "Confirme un fait",
             "Tracker → Orchestrateur : \"profil sauvé\""],
            ["FAILURE", "Signale un échec",
             "Pédagogue → Orchestrateur : \"RAG indisponible\""],
        ],
        col_widths=[3*g.cm, 4*g.cm, 10*g.cm])

    g.h2("9.3 Notre implémentation dans a2a_protocol.py")

    g.code_block("""from datetime import datetime
import uuid

REQUEST = "REQUEST"
INFORM = "INFORM"
QUERY = "QUERY"
CONFIRM = "CONFIRM"
FAILURE = "FAILURE"

def create_a2a_msg(sender: str, receiver: str,
                   performative: str, content: dict,
                   conversation_id: str = None) -> dict:
    return {
        "msg_id": str(uuid.uuid4())[:8],
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "from": sender,
        "to": receiver,
        "performative": performative,
        "content": content,
        "conversation_id": conversation_id or "session-default"
    }""")

    g.h2("9.4 Patterns d'orchestration SMA")

    g.bullet([
        "<b>Hub-and-Spoke</b> — un orchestrateur central appelle les agents (NOTRE CHOIX)",
        "<b>Pipeline linéaire</b> — A → B → C → D (rigide)",
        "<b>Marché / enchères</b> — Contract-Net (les agents soumissionnent)",
        "<b>Blackboard</b> — tableau partagé, chaque agent y lit/écrit",
    ])

    g.callout("Notre pattern hybride",
        "Nous combinons <b>Hub-and-Spoke</b> (orchestrateur central LangGraph) "
        "avec <b>Blackboard</b> (State partagé entre tous les nodes). "
        "Cette combinaison est idéale pour un SMA où l'on veut à la fois "
        "centraliser le contrôle ET partager l'information.",
        color=g.SUCCESS)

    g.pagebreak()

"""PARTIE III-A — Code expliqué ligne par ligne : a2a_protocol, mind_layer, rag_engine"""

def build(g):
    # ═══════════════════════════════════════════════════════
    # CHAPITRE 10 — a2a_protocol.py
    # ═══════════════════════════════════════════════════════
    g.section_header("10", "Code expliqué : a2a_protocol.py",
                     "PARTIE III — CODE LIGNE PAR LIGNE")

    g.p("Ce module définit le protocole de communication inter-agents. "
        "Inspiré de FIPA-ACL, il fournit des helpers pour créer et formater les "
        "messages échangés entre agents.")

    g.h2("10.1 Imports et constantes")

    g.code_block("""from datetime import datetime
import uuid

# Performatives FIPA-ACL utilisées dans notre SMA
REQUEST = "REQUEST"   # Demande à un agent d'exécuter une action
INFORM = "INFORM"     # Transmet un résultat / information
QUERY = "QUERY"       # Demande une information
CONFIRM = "CONFIRM"   # Confirme un fait
FAILURE = "FAILURE"   # Signale un échec""")

    g.explain("On importe <b>datetime</b> pour les timestamps et <b>uuid</b> pour "
              "générer des identifiants uniques. Les performatives sont des constantes "
              "string (et non des Enum) pour rester compatibles avec les sérialisations "
              "JSON triviales.")

    g.h2("10.2 La fonction create_a2a_msg")

    g.code_block("""def create_a2a_msg(sender: str, receiver: str,
                   performative: str, content: dict,
                   conversation_id: str = None) -> dict:
    \"\"\"
    Crée un message A2A standardisé (FIPA-ACL).

    Args:
        sender: nom de l'agent émetteur
        receiver: nom de l'agent destinataire
        performative: type FIPA-ACL (REQUEST, INFORM, ...)
        content: contenu sémantique du message (dict libre)
        conversation_id: identifiant de la conversation (pour grouper)

    Returns:
        Dict standardisé représentant le message.
    \"\"\"
    return {
        "msg_id": str(uuid.uuid4())[:8],
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "from": sender,
        "to": receiver,
        "performative": performative,
        "content": content,
        "conversation_id": conversation_id or "session-default"
    }""")

    g.h3("Analyse ligne par ligne")

    g.p("<b>Ligne 1-2</b> : Signature avec type hints (Python 3.6+). "
        "Tous les paramètres sont typés pour aider l'IDE et le linter.")

    g.p("<b>Paramètre <i>content</i> de type dict</b> : on aurait pu utiliser une "
        "Pydantic BaseModel pour valider, mais un <i>dict</i> est plus flexible pour "
        "un projet académique. Le contenu varie selon le contexte (parfois \"action\", "
        "parfois \"score\", parfois \"lacunes\").")

    g.p("<b>conversation_id = None par défaut</b> : si non fourni, on utilise "
        "\"session-default\". En production, on l'imposerait pour grouper les messages "
        "d'une même session.")

    g.p("<b>msg_id = uuid.uuid4()[:8]</b> : on génère un UUID v4 (aléatoire) et "
        "on en garde 8 caractères. Suffisant pour un projet académique (collision "
        "extrêmement improbable sur une session).")

    g.p("<b>timestamp format HH:MM:SS</b> : on n'affiche pas la date entière car "
        "tous les messages d'une démo sont dans la même journée. Cela rend la timeline "
        "plus lisible.")

    g.h2("10.3 La fonction format_timeline_text")

    g.code_block("""def format_timeline_text(communications: list) -> str:
    \"\"\"Formate la liste de messages A2A en timeline ASCII (pour CLI/debug).\"\"\"
    lines = []
    emoji_map = {
        "REQUEST": "📤", "INFORM": "📥", "QUERY": "❓",
        "CONFIRM": "✅", "FAILURE": "❌"
    }
    for m in communications:
        emoji = emoji_map.get(m['performative'], "•")
        lines.append(
            f"{emoji} [{m['timestamp']}] {m['from']:<15} → {m['to']:<15} : {m['performative']}"
        )
    return "\\n".join(lines)""")

    g.explain("Format f-string avec <b>:&lt;15</b> = padding à gauche sur 15 caractères. "
              "Cela aligne visuellement les colonnes 'from' et 'to' dans la timeline ASCII. "
              "Le emoji_map utilise <i>.get(key, default)</i> pour éviter une KeyError "
              "si une performative inconnue passe.")

    g.h2("10.4 La fonction format_timeline_html (pour Streamlit)")

    g.code_block("""def format_timeline_html(communications: list) -> str:
    \"\"\"Formate la timeline en HTML (pour Streamlit).\"\"\"
    html_parts = []
    color_map = {
        "REQUEST": "#2563eb", "INFORM": "#15803d", "QUERY": "#d97706",
        "CONFIRM": "#7c3aed", "FAILURE": "#dc2626"
    }
    for m in communications:
        color = color_map.get(m['performative'], "#64748b")
        html_parts.append(
            f'<div style="background:#f1f5f9;border-left:4px solid {color};'
            f'padding:8px;margin:4px 0;border-radius:4px;font-family:Courier;'
            f'font-size:0.85rem;">'
            f'<b style="color:{color};">[{m["timestamp"]}]</b> '
            f'<b>{m["from"]}</b> ➡️ <b>{m["to"]}</b> '
            f'<span style="color:{color};">[{m["performative"]}]</span>'
            f'</div>'
        )
    return "".join(html_parts)""")

    g.explain("On génère du HTML inline avec une bordure colorée à gauche selon la "
              "performative (bleu=REQUEST, vert=INFORM, etc.). Streamlit affichera ce "
              "HTML via <i>st.markdown(..., unsafe_allow_html=True)</i>.")

    g.callout("Pourquoi pas Markdown ?",
        "Markdown ne permet pas de personnaliser les couleurs et les borders. "
        "Pour une timeline visuellement riche, le HTML direct est nécessaire. "
        "Streamlit l'accepte avec <i>unsafe_allow_html=True</i>.")

    g.pagebreak()

    # ═══════════════════════════════════════════════════════
    # CHAPITRE 11 — mind_layer.py
    # ═══════════════════════════════════════════════════════
    g.section_header("11", "Code expliqué : mind_layer.py")

    g.p("Ce module fournit la <b>couche LLM</b> du Planificateur — le 'Mind' au sens "
        "Body/Mind/Memory du cours. Il implémente une stratégie hybride : LLM réel "
        "si disponible, fallback déterministe sinon.")

    g.h2("11.1 Détection automatique du provider LLM")

    g.code_block("""LLM_PROVIDER = None
_llm_client = None

def _try_init_llm():
    \"\"\"Détecte la clé API disponible et instancie le client correspondant.\"\"\"
    global LLM_PROVIDER, _llm_client

    # 1. OpenRouter (gratuit, modèles open-source — cf. cours du prof)
    if os.getenv("OPENROUTER_API_KEY"):
        try:
            from langchain_openai import ChatOpenAI
            _llm_client = ChatOpenAI(
                model="openai/gpt-oss-120b:free",
                openai_api_key=os.getenv("OPENROUTER_API_KEY"),
                openai_api_base="https://openrouter.ai/api/v1",
                temperature=0
            )
            LLM_PROVIDER = "openrouter"
            return
        except Exception:
            pass

    # 2. OpenAI standard
    if os.getenv("OPENAI_API_KEY"):
        # ... instancier ChatOpenAI standard
        LLM_PROVIDER = "openai"
        return

    # 3. Google Gemini
    if os.getenv("GOOGLE_API_KEY"):
        # ... instancier ChatGoogleGenerativeAI
        LLM_PROVIDER = "gemini"
        return

    # 4. Pas de LLM disponible — mode déterministe
    LLM_PROVIDER = "fallback"

_try_init_llm()  # exécuté au chargement du module""")

    g.h3("Analyse de la stratégie")

    g.bullet([
        "<b>Cascade de fallback</b> : OpenRouter (priorité, car gratuit dans le cours) "
        "→ OpenAI → Gemini → fallback déterministe",
        "<b>Variables d'environnement uniquement</b> : conforme aux 6 règles MCP du cours "
        "(jamais de secret en dur)",
        "<b>try/except sur l'import</b> : si la lib langchain-openai n'est pas installée, "
        "on passe au provider suivant sans erreur",
        "<b>temperature=0</b> : décisions déterministes (utile pour le débogage)",
        "<b>_try_init_llm() exécuté au module load</b> : pas besoin d'appeler manuellement",
    ])

    g.h2("11.2 Le System Prompt du Planificateur")

    g.code_block("""PLANIFICATEUR_SYSTEM_PROMPT = \"\"\"Tu es l'Agent Planificateur d'un Système
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

Format de sortie : raisonnement structuré en étapes, puis recommandation finale.\"\"\"""")

    g.explain("Ce prompt suit les 5 ingrédients du cours : RÔLE (Agent Planificateur), "
              "PÉRIMÈTRE (analyse + CoT), LANGUE/TON (français + concis), FORMAT "
              "(étapes numérotées), LIMITES (interdiction de mentionner les concurrents).")

    g.h2("11.3 La fonction reason_planificateur")

    g.code_block("""def reason_planificateur(diagnostic: dict, parcours: list) -> str:
    \"\"\"Génère le raisonnement Chain-of-Thought du Planificateur.

    Args:
        diagnostic: rapport du Diagnosticien (score, lacunes, ...)
        parcours: liste des étapes calculées par planner.py

    Returns:
        Texte de raisonnement (CoT).
    \"\"\"
    if LLM_PROVIDER != "fallback" and _llm_client is not None:
        return _reason_with_llm(diagnostic, parcours)
    return _reason_fallback(diagnostic, parcours)""")

    g.explain("Point d'entrée unique : si un LLM est disponible, on l'appelle, sinon "
              "on retombe sur le fallback. <b>Garantit que la fonction retourne TOUJOURS</b> "
              "une string non-vide, quelle que soit la situation.")

    g.h2("11.4 Le fallback déterministe (mode démo offline)")

    g.code_block("""def _reason_fallback(diagnostic: dict, parcours: list) -> str:
    \"\"\"Génère un raisonnement déterministe basé sur des templates.

    Reproduit la STRUCTURE d'un raisonnement Chain-of-Thought.
    \"\"\"
    score = diagnostic.get("pourcentage", 0)
    lacunes = diagnostic.get("lacunes", [])
    maitrisees = diagnostic.get("notions_maitrisees", [])
    nb_etapes = len(parcours)

    if score >= 80:
        lines = [
            f"**Étape 1 — Analyse du niveau** : Le score de {score}% indique un niveau avancé.",
            f"**Étape 2 — Conclusion** : Toutes les notions clés sont déjà maîtrisées "
            f"({len(maitrisees)} notion(s)).",
            f"**Étape 3 — Décision (Conditional Edge LangGraph)** : "
            f"je saute la phase de construction du parcours et délègue directement au Coach "
            f"pour planifier les révisions espacées (SM-2).",
            f"**Recommandation finale** : Maintenir l'acquis par révisions périodiques."
        ]
    elif score >= 50:
        # ... template intermédiaire
        pass
    else:
        # ... template débutant
        pass

    return "\\n".join(lines)""")

    g.callout("Pourquoi un fallback structuré (pas juste 'ok') ?",
        "Le fallback REPRODUIT la STRUCTURE d'un raisonnement CoT (étapes numérotées, "
        "vocabulaire pédagogique). Cela permet de présenter le même format au jury que "
        "le LLM réel — la démo est cohérente même sans Internet.",
        color=g.SUCCESS)

    g.pagebreak()

    # ═══════════════════════════════════════════════════════
    # CHAPITRE 12 — rag_engine.py
    # ═══════════════════════════════════════════════════════
    g.section_header("12", "Code expliqué : rag_engine.py")

    g.p("Ce module implémente le RAG vectoriel conforme au Chapitre 2 du cours : "
        "Chunking récursif + Embeddings + Chroma + Similarité cosine. "
        "Avec fallback gracieux en mode keyword si les dépendances ne sont pas installées.")

    g.h2("12.1 Imports avec fallback")

    g.code_block("""VECTOR_RAG_AVAILABLE = False
try:
    from langchain_chroma import Chroma
    from langchain_huggingface import HuggingFaceEmbeddings
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
    except ImportError:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_core.documents import Document
    VECTOR_RAG_AVAILABLE = True
except ImportError as e:
    print(f"[RAG] Mode dégradé (keyword)")""")

    g.explain("Le double try/except permet de gérer deux versions de LangChain "
              "(<i>langchain.text_splitter</i> pré 0.3, <i>langchain_text_splitters</i> "
              "post 0.3). Si TOUTES les imports échouent, <b>VECTOR_RAG_AVAILABLE</b> "
              "reste False et on utilise le fallback keyword.")

    g.h2("12.2 Initialisation du vector store")

    g.code_block("""def _init_vector_store(self):
    \"\"\"Charge les ressources, chunke, embedde, indexe dans Chroma.\"\"\"
    # 1. Modèle d'embedding (gratuit, local, multilingue)
    self.embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )

    # 2. Si déjà indexé, on recharge
    if os.path.exists(self.persist_dir) and os.listdir(self.persist_dir):
        self.vectorstore = Chroma(
            persist_directory=self.persist_dir,
            embedding_function=self.embeddings,
            collection_name="learning_resources"
        )
        return

    # 3. Sinon, indexation initiale
    docs = self._load_documents()

    # 4. Chunking récursif (Chapitre 2 — méthode recommandée)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=50,
        separators=["\\n\\n", "\\n", ".", " ", ""]
    )
    chunks = splitter.split_documents(docs)

    # 5. Création du vectorstore (1 vecteur par chunk)
    self.vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=self.embeddings,
        persist_directory=self.persist_dir,
        collection_name="learning_resources"
    )""")

    g.h3("Choix expliqués")

    g.bullet([
        "<b>model_kwargs={\"device\": \"cpu\"}</b> : on force CPU pour ne pas dépendre "
        "d'un GPU (machine de démo peut être un laptop standard)",
        "<b>normalize_embeddings=True</b> : produit des vecteurs de norme 1 → la "
        "similarité cosine devient un simple produit scalaire (plus rapide)",
        "<b>collection_name=\"learning_resources\"</b> : permet d'avoir plusieurs "
        "collections dans une même base Chroma (extensible)",
        "<b>Vérification persist_dir</b> : si la base existe, on recharge sans "
        "réindexer (gain de temps au démarrage)",
        "<b>chunk_size=300, overlap=50</b> : optimal pour nos ressources de 200-500 caractères",
    ])

    g.h2("12.3 La fonction _load_documents")

    g.code_block("""def _load_documents(self) -> List["Document"]:
    \"\"\"Charge ressources.json + fichiers texte en Documents LangChain.\"\"\"
    docs = []

    # Source 1 : catalogue JSON (descriptions courtes + URLs)
    if os.path.exists(self.json_path):
        with open(self.json_path, 'r', encoding='utf-8') as f:
            db = json.load(f)
        for r in db:
            content = f"{r.get('notion', '')}: {r.get('description', '')}"
            docs.append(Document(
                page_content=content,
                metadata={
                    "source": "catalog_json",
                    "type": r.get('type', 'Lien'),
                    "notion": r.get('notion', ''),
                    "module": r.get('module', ''),
                    "url": r.get('url', '#')
                }
            ))

    # Source 2 : fichiers texte (chunkage approfondi)
    for filename in os.listdir(self.ressources_path):
        if filename.endswith(".txt"):
            with open(...) as f:
                content = f.read()
            docs.append(Document(
                page_content=content,
                metadata={...}
            ))

    return docs""")

    g.explain("On charge DEUX sources : le catalogue JSON (descriptions courtes + URLs) "
              "et les fichiers texte (contenu approfondi pour le chunking). Chaque Document "
              "garde ses <b>metadata</b> qui permettront le filtrage côté query.")

    g.h2("12.4 La recherche vectorielle")

    g.code_block("""def _search_vector(self, query: str, k: int, module: Optional[str]) -> List[Dict]:
    \"\"\"Implémentation vectorielle (Chroma similarity_search_with_score).\"\"\"
    filter_ = {"module": module} if module else None
    try:
        results = self.vectorstore.similarity_search_with_score(
            query, k=k, filter=filter_
        )
    except Exception:
        # Si filtre non supporté, refaire sans
        results = self.vectorstore.similarity_search_with_score(query, k=k)

    formatted = []
    for doc, score in results:
        formatted.append({
            "type": doc.metadata.get("type", "Ressource"),
            "notion": doc.metadata.get("notion", ""),
            "contenu": doc.page_content,
            "description": doc.page_content[:200] + "...",
            "source": doc.metadata.get("source", "?"),
            "url": doc.metadata.get("url", "#"),
            "module": doc.metadata.get("module", ""),
            "score": round(float(score), 3),
            "mode": "vectoriel"
        })
    return formatted""")

    g.callout("similarity_search_with_score",
        "Cette méthode retourne les top-K documents <b>avec leur score de similarité</b>. "
        "Plus le score est BAS, plus le document est PROCHE (Chroma utilise la distance L2 "
        "par défaut, pas la similarité cosine directe). Score = 0.0 → identique, "
        "score = 2.0 → totalement différent.",
        color=g.ACCENT)

    g.pagebreak()

# 🎓 Learning Path Architect — SMA Agentic AI

> **Projet 4 · Module 4AISDR · Mai 2026**
> Système Multi-Agents pour parcours d'apprentissage adaptatifs
> Encadrants : Pr. Hasnââ CHAABI & Pr. Nadia IDRISSI Zouggari

---

## 📋 Sommaire

1. [Présentation](#-présentation)
2. [Architecture](#-architecture)
3. [Stack technique](#-stack-technique)
4. [Installation](#-installation)
5. [Lancement](#-lancement)
6. [Structure du code](#-structure-du-code)
7. [Choix techniques justifiés](#-choix-techniques-justifiés)
8. [Conformité au cours](#-conformité-au-cours)
9. [Tests](#-tests)
10. [Limitations & perspectives](#-limitations--perspectives)
11. [Équipe](#-équipe)

---

## 🎯 Présentation

Ce projet implémente un **Système Multi-Agents (SMA)** qui :

1. **Diagnostique** le niveau d'un étudiant sur une matière donnée via un test adaptatif
2. **Identifie ses lacunes** précises
3. **Construit un parcours d'apprentissage personnalisé** respectant les pré-requis
4. **Recommande des ressources** via Retrieval-Augmented Generation **vectoriel**
5. **Programme les révisions** via l'algorithme de répétition espacée SuperMemo-2 (SM-2)
6. **Persiste le profil** de l'étudiant pour les sessions futures

L'orchestration est assurée par **LangGraph** (State + Nodes + Edges + Conditional Edge),
la communication inter-agents par le protocole **A2A inspiré FIPA-ACL**, et l'exposition
des outils par **MCP (Model Context Protocol)** d'Anthropic.

---

## 🏗️ Architecture

```
                  ┌─────────┐
                  │  START  │
                  └────┬────┘
                       ▼
              ┌────────────────┐
              │  Diagnosticien │  ← test adaptatif (mode profil)
              └────────┬───────┘
                       │
                ╔══════╧══════╗
                ║ Conditional ║   ← LangGraph add_conditional_edges
                ╚══════╤══════╝
              ≥80%    │    <80%
            ┌────────┘      └────────┐
            ▼                        ▼
      ┌──────────┐         ┌────────────────┐
      │  Coach   │         │ Planificateur  │  ← Mind layer (LLM CoT)
      │ (direct) │         └────────┬───────┘
      └────┬─────┘                  ▼
           │              ┌──────────────────┐
           │              │  Pédagogue (RAG) │  ← Chroma + embeddings
           │              └──────────┬───────┘
           │                         ▼
           │                  ┌──────────┐
           │                  │  Coach   │  ← SM-2
           │                  └────┬─────┘
           └──────────────────────┘
                              ▼
                        ┌──────────┐
                        │ Tracker  │  ← persistance long-terme
                        └─────┬────┘
                              ▼
                          ┌───────┐
                          │  END  │
                          └───────┘
```

### Les 5 agents spécialisés

| Agent | Rôle | Techniques utilisées |
|---|---|---|
| **Diagnosticien** | Lance un test adaptatif, identifie les lacunes par notion | Adaptatif IRT-simplifié |
| **Planificateur** | Construit un parcours ordonné respectant les pré-requis | Chain-of-Thought + ReAct + SM-2 |
| **Pédagogue** | Sélectionne les ressources via RAG vectoriel | Chroma + embeddings + cosine |
| **Coach** | Programme la prochaine révision | Algorithme SuperMemo-2 |
| **Tracker** | Sauvegarde le profil étudiant | JSON long-terme |

### Communication A2A (FIPA-ACL)

Chaque échange entre agents est tracé avec une **performative FIPA-ACL** :
- `REQUEST` — demande d'action
- `INFORM` — transmission d'information
- `QUERY` — demande d'information
- `CONFIRM` — confirmation de fait
- `FAILURE` — signalement d'échec

La timeline est affichée en temps réel dans l'interface Streamlit (côté droit).

---

## 🛠️ Stack technique

| Couche | Technologie | Justification |
|---|---|---|
| **Orchestration** | LangGraph 0.2+ | Graphe d'états avec conditional edges (vs. LangChain linéaire) |
| **LLM (Mind)** | OpenRouter / OpenAI / Gemini (fallback déterministe) | Chain-of-Thought sur le Planificateur |
| **Outils (Body)** | MCP (Model Context Protocol) — FastMCP | Standard ouvert Anthropic, isolation par sous-processus |
| **RAG** | Chroma + sentence-transformers (multilingue, 384 dim) | Base vectorielle persistante, similarité cosine |
| **Mémoire CT** | InMemorySaver (LangGraph) | Checkpointing par thread_id |
| **Mémoire LT** | JSON files (data/profils_etudiants.json) | Persistance simple, scope académique |
| **Répétition** | SuperMemo-2 (SM-2) | Algorithme de référence (Anki) |
| **UI** | Streamlit 1.32+ | Démo visuelle rapide |
| **Tests** | pytest | 15 tests unitaires + intégration |

---

## 📦 Installation

### Pré-requis
- Python 3.10+
- pip
- (Optionnel) Une clé API LLM dans `.env` pour activer le mode Mind complet

### Étapes

```bash
# 1. Cloner le repo
git clone https://github.com/othmanedhilou/MSA-Learning_Path.git
cd MSA-Learning_Path

# 2. (Recommandé) créer un environnement virtuel
python -m venv .venv
.venv\Scripts\activate     # Windows
# source .venv/bin/activate  # Linux/Mac

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. (Optionnel) configurer un LLM dans un fichier .env
# OPENROUTER_API_KEY=sk-or-v1-...

# 5. Initialiser les données RAG (si fichiers textes manquants)
python setup_data.py
```

### Vérification

```bash
# Vérifier que LangGraph est bien installé
python -c "from orchestrator import LANGGRAPH_AVAILABLE; print(LANGGRAPH_AVAILABLE)"
# → True

# Vérifier que le RAG vectoriel fonctionne
python rag_engine.py
# → Mode actif : vectoriel (Chroma)

# Lancer les tests
pytest tests/ -v
# → 15 passed
```

---

## 🚀 Lancement

### Mode 1 — Interface Streamlit (recommandé pour la démo)

```bash
streamlit run app.py
```

Puis ouvrir [http://localhost:8501](http://localhost:8501).

**Parcours :**
1. **Accueil** : choisir un profil parmi *Amina (débutante)*, *Yassine (intermédiaire)*, *Sarah (avancée)*
2. **Diagnostic** : l'orchestrateur tourne (barre de progression visible)
3. **Résultats** : diagnostic, parcours, ressources RAG, **timeline A2A** en direct

### Mode 2 — CLI (test rapide des 3 profils)

```bash
python orchestrator.py
```

Affiche les résultats pour les 3 profils, avec timeline A2A.

### Mode 3 — Serveur MCP standalone

```bash
# Lancer le serveur MCP en mode stdio
python learning_tools_server.py

# Ou avec l'inspector officiel (UI web)
npx @modelcontextprotocol/inspector python learning_tools_server.py
```

### Mode 4 — Tests unitaires

```bash
pytest tests/ -v
```

### Mode 5 — RAG isolé

```bash
python rag_engine.py
```

---

## 📁 Structure du code

```
MSA-Learning_Path/
├── orchestrator.py            ← ★ Cœur : graphe LangGraph (State + Nodes + Edges)
├── a2a_protocol.py            ← Protocole de messages FIPA-ACL
├── mind_layer.py              ← Couche LLM (Chain-of-Thought)
├── learning_tools_server.py   ← Serveur MCP (3 outils @mcp.tool)
├── rag_engine.py              ← RAG vectoriel Chroma + embeddings
│
├── diagnostician.py           ← Agent Diagnosticien (test adaptatif)
├── planner.py                 ← Agent Planificateur (CoT + SM-2)
├── sm2.py                     ← Algorithme SuperMemo-2
├── agent_pedagogue.py         ← Agent Pédagogue (RAG vectoriel Chroma)
├── agent_coach.py             ← Agent Coach (algorithme SuperMemo-2)
├── agent_tracker.py           ← Agent Tracker (persistance JSON long-terme)
├── setup_data.py              ← Génération des fichiers texte ressources
│
├── app.py                     ← Interface Streamlit (3 phases)
│
├── data/
│   ├── questions.json         ← Banque de questions adaptatives
│   ├── prerequis.json         ← Graphe de pré-requis entre notions
│   ├── ressources.json        ← Catalogue de ressources (URLs)
│   ├── profils_demo.json      ← 3 profils de démo (Amina, Yassine, Sarah)
│   ├── profils_etudiants.json ← Mémoire long-terme (généré)
│   ├── ressources_textes/     ← Corpus texte pour RAG (8 fichiers .txt)
│   ├── chroma_db/             ← Index vectoriel Chroma (généré)
│   └── graph_orchestrator.png ← Diagramme LangGraph (généré)
│
├── tests/
│   └── test_orchestrator.py   ← 15 tests pytest
│
├── requirements.txt
└── README.md
```

---

## 🧠 Choix techniques justifiés

### Pourquoi LangGraph plutôt que LangChain ?

Notre logique métier est **non linéaire** : si l'étudiant a un score ≥ 80%, on saute la phase
de planification et on passe directement à la révision. Cette **conditional edge** est
exprimée en une ligne en LangGraph :

```python
workflow.add_conditional_edges("diagnosticien", route_after_diagnostic, {...})
```

En LangChain pur, il aurait fallu créer plusieurs chaînes parallèles et un dispatcher.
Le cours dédie un chapitre entier à LangGraph précisément pour ce type de cas.

### Pourquoi Chroma plutôt que FAISS ?

Pour ~20 ressources, FAISS serait du surdesign. Chroma offre :
- ✅ **Persistance automatique** (SQLite sous-jacent)
- ✅ **Filtrage par métadonnées** (module, type)
- ✅ **Intégration native LangChain** (langchain-chroma)

FAISS resterait pertinent à l'échelle de millions de vecteurs.

### Pourquoi le modèle multilingual-MiniLM ?

- ✅ **384 dimensions** : compromis qualité/vitesse
- ✅ **Multilingue** : fonctionne en français (et 100+ langues)
- ✅ **Gratuit, local** : pas de clé API, pas de réseau requis
- ✅ **Sentence Transformers** : référence du domaine
- ✅ **Léger** : ~120 Mo, tourne sur CPU

### Pourquoi MCP en plus de @tool LangChain ?

Trois raisons :
1. **MCP est un chapitre majeur du cours** — l'utiliser prouve la maîtrise.
2. **Isolation par sous-processus** : le démarrage de l'embedding ne bloque pas l'UI.
3. **Réutilisabilité** : les 3 outils MCP peuvent servir à d'autres projets sans modification.

### Pourquoi SM-2 plutôt qu'un système de règles simples ?

SM-2 (SuperMemo-2) est l'algorithme de référence utilisé par Anki et tous les outils sérieux
de répétition espacée. Le sujet l'exige explicitement (« Implémenter SM-2 ou Leitner »).

### Pourquoi un LLM avec fallback déterministe ?

Le LLM (via OpenRouter/OpenAI/Gemini) produit un **vrai raisonnement Chain-of-Thought** dans le
Planificateur. Mais si la clé API est absente OU si le réseau plante le jour J, un fallback
basé sur des templates structurés (avec étapes numérotées) reproduit la STRUCTURE du CoT.

**Conséquence** : la démo fonctionne en toutes circonstances.

---

## 🎓 Conformité au cours

| Chapitre du cours | Implémentation dans ce projet |
|---|---|
| **Ch.1 — Prompt Engineering (Zero-shot, Few-shot, CoT, ReAct)** | `mind_layer.py` : System prompt + Chain-of-Thought structuré sur le Planificateur |
| **Ch.2 — RAG (Chunking + Embeddings)** | `rag_engine.py` : RecursiveCharacterTextSplitter + multilingual-MiniLM (384 dim) + Chroma |
| **Ch.3 — Agentic AI (Body/Mind/Memory)** | Body = MCP tools, Mind = LLM via mind_layer, Memory = InMemorySaver + JSON LT |
| **Ch.4 — LangChain Middlewares** | Architecture compatible (extension possible via @wrap_model_call) |
| **Ch.5 — LangGraph (State/Nodes/Edges)** | `orchestrator.py` : LearningState TypedDict + 5 nodes + 1 conditional edge |
| **Ch.6 — MCP (FastMCP + @mcp.tool)** | `learning_tools_server.py` : 3 outils MCP exposés via stdio |
| **Ch.7 — SMA & A2A** | `a2a_protocol.py` : messages FIPA-ACL avec 5 performatives |

---

## 🧪 Tests

```bash
pytest tests/ -v
```

Résultat : **15 tests passés en ~1s**.

Couverture :
- ✅ Conditional edge (5 tests : avancé, débutant, intermédiaire, limite 80%, état vide)
- ✅ Protocole A2A (4 tests : structure, performative, conversation_id)
- ✅ Sessions intégration (5 tests : 3 profils, A2A journalisé, SM-2, Tracker)
- ✅ Isolation des nodes (1 test : Diagnosticien indépendant)

---

## 🔭 Limitations & perspectives

### Limitations actuelles

- **Scope académique** : 4 notions × 5 modules = 20 notions. Extensible.
- **Pas d'A/B test pédagogique** : la validation se fait sur 3 profils simulés.
- **RAG : corpus de 8 textes** : représentatif mais petit. Facile à étendre en ajoutant des `.txt`.

### Perspectives d'évolution

- Multi-langue (les embeddings multilingual-MiniLM le permettent déjà côté technique)
- Diagnostic adaptatif IRT complet (théorie de réponse aux items)
- Intégration LMS (Moodle, Canvas) via API MCP supplémentaire
- Génération automatique d'exercices via un 6e agent (LLM-driven)

---

## 👥 Équipe

| Membre | Rôle principal |
|---|---|
| **Othmane Dhilou** | Orchestrateur LangGraph, MCP, A2A, Mind layer, tests |
| **Dodo** | RAG engine, app Streamlit, profils de démo, ressources |
| **Mohamed Yassir** | Documentation, supports de présentation |

**Encadrants :** Pr. Hasnââ CHAABI · Pr. Nadia IDRISSI Zouggari
**Présentation :** semaine du 18 mai 2026

---

## 📜 Licence

Projet académique — Module 4AISDR — 2025/2026.

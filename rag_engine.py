# Moteur RAG vectoriel — Chroma + RecursiveCharacterTextSplitter + embeddings multilingues
# Fallback automatique sur recherche par mot-clé si les dépendances ne sont pas installées.
import os
import json
from typing import List, Dict, Optional

VECTOR_RAG_AVAILABLE = False
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
    print(f"[RAG] Mode dégradé (keyword) - install: pip install langchain-chroma langchain-huggingface sentence-transformers")


class RAGEngine:
    """Moteur RAG hybride : vectoriel (Chroma) avec fallback keyword.

    Au démarrage : charge ressources.json + .txt → chunking récursif →
    embeddings 384 dim → indexation Chroma. À la query : similarité cosine top-K.
    """

    def __init__(self, persist_dir: Optional[str] = None):
        base = os.path.dirname(os.path.abspath(__file__))
        self.ressources_path = os.path.join(base, 'data', 'ressources_textes')
        self.json_path = os.path.join(base, 'data', 'ressources.json')
        self.persist_dir = persist_dir or os.path.join(base, 'data', 'chroma_db')

        self.vector_mode = VECTOR_RAG_AVAILABLE
        self.vectorstore = None
        self.embeddings = None

        if self.vector_mode:
            try:
                self._init_vector_store()
            except Exception as e:
                print(f"[RAG] Erreur init vectoriel : {e}. Bascule en mode keyword.")
                self.vector_mode = False

    def _init_vector_store(self):
        """Charge les ressources, chunke, embedde, indexe dans Chroma."""
        # Modèle d'embedding gratuit, local, multilingue — tourne sur CPU
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )

        # Si déjà indexé, on recharge depuis le disque
        if os.path.exists(self.persist_dir) and os.listdir(self.persist_dir):
            self.vectorstore = Chroma(
                persist_directory=self.persist_dir,
                embedding_function=self.embeddings,
                collection_name="learning_resources"
            )
            return

        # Première fois : chunking récursif → embeddings → indexation Chroma
        docs = self._load_documents()
        if not docs:
            raise RuntimeError("Aucun document à indexer")

        # RecursiveCharacterTextSplitter : découpe paragraphes → lignes → phrases → mots
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=300,
            chunk_overlap=50,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        chunks = splitter.split_documents(docs)

        self.vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=self.persist_dir,
            collection_name="learning_resources"
        )

    def _load_documents(self) -> List["Document"]:
        """Charge ressources.json + fichiers .txt en Documents LangChain."""
        docs = []

        # Source 1 : catalogue JSON (descriptions courtes + URLs)
        if os.path.exists(self.json_path):
            try:
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
            except Exception as e:
                print(f"[RAG] Skipping ressources.json : {e}")

        # Source 2 : fichiers texte (chunkage approfondi)
        if os.path.exists(self.ressources_path):
            for filename in os.listdir(self.ressources_path):
                if filename.endswith(".txt"):
                    filepath = os.path.join(self.ressources_path, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    # Extraire la notion depuis "NOTION: ..." dans le texte
                    notion = filename.replace(".txt", "").replace("_", " ")
                    for line in content.split("\n"):
                        if line.strip().startswith("NOTION:"):
                            notion = line.split("NOTION:")[1].strip().rstrip(".")
                            break

                    docs.append(Document(
                        page_content=content,
                        metadata={
                            "source": filename,
                            "type": "Extrait de cours",
                            "notion": notion,
                            "module": filename.split("_")[0] if "_" in filename else "Général",
                            "url": "#"
                        }
                    ))

        return docs

    def search(self, query: str, k: int = 3, module: Optional[str] = None) -> List[Dict]:
        """Recherche sémantique vectorielle (similarité cosine) — fallback keyword si Chroma absent."""
        if self.vector_mode and self.vectorstore:
            return self._search_vector(query, k, module)
        return self._search_keyword(query, k)

    def _search_vector(self, query: str, k: int, module: Optional[str]) -> List[Dict]:
        """Implémentation vectorielle (Chroma similarity_search_with_score)."""
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
        return formatted

    def _search_keyword(self, query: str, k: int) -> List[Dict]:
        """Fallback keyword matching (mode dégradé)."""
        resultats = []
        q_lower = query.lower()

        # JSON
        if os.path.exists(self.json_path):
            with open(self.json_path, 'r', encoding='utf-8') as f:
                try:
                    db = json.load(f)
                    for r in db:
                        if q_lower in r.get('notion', '').lower():
                            resultats.append({
                                "type": r.get('type', 'Lien'),
                                "notion": r.get('notion', ''),
                                "contenu": r.get('description', ''),
                                "description": r.get('description', ''),
                                "url": r.get('url', '#'),
                                "source": "Catalogue JSON",
                                "module": r.get('module', ''),
                                "score": 1.0,
                                "mode": "keyword"
                            })
                except Exception:
                    pass

        # Textes
        if os.path.exists(self.ressources_path):
            for filename in os.listdir(self.ressources_path):
                if filename.endswith(".txt"):
                    with open(os.path.join(self.ressources_path, filename),
                              'r', encoding='utf-8') as f:
                        content = f.read()
                    if q_lower in content.lower():
                        resultats.append({
                            "type": "Extrait de cours",
                            "notion": filename.replace(".txt", "").replace("_", " "),
                            "contenu": content,
                            "description": content[:200],
                            "url": "#",
                            "source": filename,
                            "module": filename.split("_")[0] if "_" in filename else "?",
                            "score": 1.0,
                            "mode": "keyword"
                        })
        return resultats[:k]

    def chercher_ressources(self, notion_cible: str) -> List[Dict]:
        return self.search(notion_cible, k=5)

if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    print("=" * 60)
    print("  RAG ENGINE - Test")
    print(f"  Mode vectoriel disponible : {VECTOR_RAG_AVAILABLE}")
    print("=" * 60)

    rag = RAGEngine()
    print(f"  Mode actif : {'vectoriel (Chroma)' if rag.vector_mode else 'keyword (fallback)'}")
    print()

    queries = [
        "Communication entre agents",
        "K-Means partitionnement",
        "Self-attention Transformer",
    ]

    for q in queries:
        print(f"\n--- Query: '{q}' ---")
        results = rag.search(q, k=3)
        for i, r in enumerate(results, 1):
            print(f"  {i}. [{r['type']}] {r['notion']} "
                  f"(score={r.get('score', '?')}, source={r['source']})")

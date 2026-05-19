"""
Mind Layer — Couche LLM pour les agents
══════════════════════════════════════════════════════

Référence cours :
  • Chapitre 1 — Prompt Engineering (Zero-shot, Few-shot, CoT, ReAct)
  • Chapitre 3 — Agentic AI : Agent = Mind (LLM) + Body + Memory
  • Chapitre 4 — LangChain create_agent + middleware @wrap_model_call

Ce module expose une fonction `reason()` qui :
  1. Tente d'appeler un LLM réel si une clé API est disponible
     (OpenRouter / Gemini / OpenAI selon les variables d'environnement)
  2. Sinon, retombe sur un fallback déterministe basé sur des templates
     (mode démo offline, garantit que la démo jour J fonctionne sans réseau)

Cette double stratégie est conforme aux 6 règles MCP du cours :
"6. Moindre privilège" — pas de secret en dur, variables d'env uniquement.
"""
import os
from typing import Optional, Literal

# ──────────────────────────────────────────────────────────────
# Détection automatique du provider LLM disponible
# ──────────────────────────────────────────────────────────────
LLM_PROVIDER = None
_llm_client = None

def _try_init_llm():
    """Détecte la clé API disponible et instancie le client correspondant."""
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
        try:
            from langchain_openai import ChatOpenAI
            _llm_client = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0
            )
            LLM_PROVIDER = "openai"
            return
        except Exception:
            pass

    # 3. Google Gemini (gratuit)
    if os.getenv("GOOGLE_API_KEY"):
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            _llm_client = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                temperature=0
            )
            LLM_PROVIDER = "gemini"
            return
        except Exception:
            pass

    # 4. Pas de LLM disponible — mode déterministe
    LLM_PROVIDER = "fallback"

_try_init_llm()


# ══════════════════════════════════════════════════════════════
# PROMPTS — System Messages (Chapitre 1 du cours)
# ══════════════════════════════════════════════════════════════

PLANIFICATEUR_SYSTEM_PROMPT = """Tu es l'Agent Planificateur d'un Système Multi-Agents pédagogique.

Ton rôle : analyser le diagnostic d'un étudiant et expliquer le parcours d'apprentissage
optimal en utilisant la technique Chain-of-Thought (raisonnement étape par étape).

Règles :
1. Sois concis : 4-6 phrases maximum.
2. Raisonne en étapes numérotées (Étape 1, Étape 2, ...).
3. Justifie l'ordre des notions par les pré-requis pédagogiques.
4. Mentionne la durée estimée et le rythme de répétition espacée (SM-2).
5. Ne mentionne JAMAIS les concurrents ou autres systèmes externes.

Format de sortie : raisonnement structuré en étapes, puis recommandation finale."""


PEDAGOGUE_SYSTEM_PROMPT = """Tu es l'Agent Pédagogue. À partir des ressources RAG fournies,
synthétise en 2-3 phrases pourquoi elles sont pertinentes pour cet étudiant.

Sois bienveillant, en français, ton professionnel."""


# ══════════════════════════════════════════════════════════════
# FONCTIONS DE RAISONNEMENT
# ══════════════════════════════════════════════════════════════

def reason_planificateur(diagnostic: dict, parcours: list) -> str:
    """Génère le raisonnement Chain-of-Thought du Planificateur.

    Args:
        diagnostic: rapport du Diagnosticien (score, lacunes, ...)
        parcours: liste des étapes calculées par planner.py

    Returns:
        Texte de raisonnement (CoT) — soit généré par LLM, soit par template.
    """
    if LLM_PROVIDER != "fallback" and _llm_client is not None:
        return _reason_with_llm(diagnostic, parcours)
    return _reason_fallback(diagnostic, parcours)


def _reason_with_llm(diagnostic: dict, parcours: list) -> str:
    """Vrai appel LLM avec Chain-of-Thought."""
    try:
        from langchain_core.messages import SystemMessage, HumanMessage

        lacunes_txt = ", ".join(diagnostic.get("lacunes", [])) or "aucune"
        maitrise_txt = ", ".join(diagnostic.get("notions_maitrisees", [])) or "aucune"
        etapes_txt = " → ".join(e.get("notion", "?") for e in parcours) or "rien"

        user_prompt = f"""Étudiant : {diagnostic.get('etudiant')}
Module : {diagnostic.get('module')}
Score : {diagnostic.get('pourcentage')}%
Notions maîtrisées : {maitrise_txt}
Lacunes : {lacunes_txt}
Parcours proposé (ordre) : {etapes_txt}

Explique-moi en Chain-of-Thought pourquoi cet ordre est pertinent."""

        response = _llm_client.invoke([
            SystemMessage(content=PLANIFICATEUR_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt)
        ])
        return response.content
    except Exception as e:
        # Si échec réseau, on retombe sur le fallback (jamais d'erreur jour J)
        return _reason_fallback(diagnostic, parcours) + f"\n\n[Note: LLM unavailable, used fallback. Error: {str(e)[:80]}]"


def _reason_fallback(diagnostic: dict, parcours: list) -> str:
    """Génère un raisonnement déterministe basé sur des templates (mode offline).

    Reproduit la STRUCTURE d'un raisonnement Chain-of-Thought.
    """
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
        lines = [
            f"**Étape 1 — Analyse** : Score intermédiaire ({score}%) avec {len(lacunes)} lacune(s) "
            f"sur les notions avancées.",
            f"**Étape 2 — Identification des prérequis** : Les notions maîtrisées "
            f"({', '.join(maitrisees[:2])}{'...' if len(maitrisees) > 2 else ''}) "
            f"servent de fondation.",
            f"**Étape 3 — Construction du parcours** : "
            f"{nb_etapes} étape(s) ordonnées par complexité croissante.",
            f"**Étape 4 — Planification SM-2** : Révisions espacées progressives "
            f"(intervalles croissants si succès)."
        ]
    else:
        lines = [
            f"**Étape 1 — Analyse** : Score faible ({score}%) — l'étudiant est débutant.",
            f"**Étape 2 — Stratégie** : Commencer par les fondamentaux, ne pas brûler les étapes.",
            f"**Étape 3 — Parcours** : {nb_etapes} étape(s), du niveau 1 (facile) "
            f"vers les niveaux supérieurs en respectant le graphe de prérequis.",
            f"**Étape 4 — Coach Répétition** : Intervalles SM-2 courts au début "
            f"(1 jour → 6 jours) pour ancrer les bases.",
            f"**Conclusion** : Apprentissage progressif sans saut de niveau."
        ]

    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════
# Test rapide
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    print(f"Provider LLM détecté : {LLM_PROVIDER}")
    print(f"{'LLM réel' if LLM_PROVIDER != 'fallback' else 'Mode fallback déterministe'}")
    print()

    fake_diag = {
        "etudiant": "Yassine",
        "module": "MSA",
        "pourcentage": 50,
        "notions_maitrisees": ["Agents Intelligents", "Communication Inter-agents"],
        "lacunes": ["Framework CrewAI", "Framework LangGraph"]
    }
    fake_parcours = [
        {"ordre": 1, "notion": "Framework CrewAI"},
        {"ordre": 2, "notion": "Framework LangGraph"}
    ]

    print("--- Raisonnement Planificateur (CoT) ---")
    print(reason_planificateur(fake_diag, fake_parcours))

# Mind Layer — couche LLM partagée par tous les agents du SMA
# Tente d'appeler un vrai LLM (OpenRouter / OpenAI / Gemini) selon la clé API disponible.
# Si aucune clé n'est trouvée, bascule sur un fallback déterministe (templates structurés)
# qui reproduit la structure d'un raisonnement Chain-of-Thought — la démo marche toujours.
import os
from dotenv import load_dotenv
load_dotenv()

LLM_PROVIDER = None
_llm_client  = None


def _try_init_llm():
    """Détecte la clé API disponible et instancie le client LangChain correspondant."""
    global LLM_PROVIDER, _llm_client

    # 1. OpenRouter — accès à des modèles open-source via une seule clé
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
            _llm_client = ChatOpenAI(model="gpt-4o-mini", temperature=0)
            LLM_PROVIDER = "openai"
            return
        except Exception:
            pass

    # 3. Google Gemini (gratuit avec clé)
    if os.getenv("GOOGLE_API_KEY"):
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            _llm_client = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)
            LLM_PROVIDER = "gemini"
            return
        except Exception:
            pass

    # Aucune clé trouvée — mode déterministe
    LLM_PROVIDER = "fallback"


_try_init_llm()


# System prompts pour chaque agent — définissent le rôle et le format attendu

# Few-shot : 2 exemples montrent au LLM exactement le format et le niveau de détail attendus
PLANIFICATEUR_SYSTEM_PROMPT = """Tu es l'Agent Planificateur d'un Système Multi-Agents pédagogique.
Analyse le diagnostic d'un étudiant et explique le parcours optimal en Chain-of-Thought.
Sois concis (4-6 phrases max), raisonne en étapes numérotées, justifie l'ordre par les prérequis.
Mentionne la durée estimée et le rythme de révision espacée (SM-2).

--- Exemples (few-shot) ---

Exemple 1 :
Étudiant : Amina | Score : 0% | Lacunes : [Agents Intelligents, Communication Inter-agents, CrewAI, LangGraph]
Étape 1 — Analyse : Score nul → profil débutant complet, toutes les notions sont à apprendre.
Étape 2 — Prérequis : Agents Intelligents (niveau 1) est le prérequis de tout le reste, on commence là.
Étape 3 — Parcours : 4 étapes dans l'ordre de complexité, 3h45 estimées sur 4 jours.
Étape 4 — SM-2 : Intervalles courts (1 jour) pour ancrer les bases avant de passer à la suite.
Recommandation : Progression strictement linéaire, aucun saut de niveau autorisé.

Exemple 2 :
Étudiant : Yassine | Score : 50% | Lacunes : [Framework CrewAI, Framework LangGraph]
Étape 1 — Analyse : Score intermédiaire → les 2 premières notions sont maîtrisées, blocage sur les frameworks.
Étape 2 — Prérequis : CrewAI (niveau 3) doit précéder LangGraph (niveau 4) — dépendance directe.
Étape 3 — Parcours : 2 étapes ciblées, 2h30 estimées.
Étape 4 — SM-2 : Intervalles moyens (3-6 jours) car les bases sont là.
Recommandation : Partir des acquis pour combler uniquement les lacunes identifiées.

--- Fin des exemples ---"""

DIAGNOSTICIEN_SYSTEM_PROMPT = """Tu es l'Agent Diagnosticien d'un Système Multi-Agents pédagogique.
Analyse le résultat du test adaptatif en Chain-of-Thought (3-4 étapes max).
Identifie le pattern des lacunes (fondamentales ou avancées ?), conclus sur le niveau réel,
indique la notion prioritaire à travailler et pourquoi."""

COACH_SYSTEM_PROMPT = """Tu es l'Agent Coach d'un Système Multi-Agents pédagogique.
Explique en Chain-of-Thought (3-4 étapes) pourquoi l'intervalle SuperMemo-2 calculé est optimal.
Relie la qualité de réponse obtenue, le facteur de facilité et la mémorisation long-terme."""

TRACKER_SYSTEM_PROMPT = """Tu es l'Agent Tracker d'un Système Multi-Agents pédagogique.
Explique en 2-3 phrases ce qui vient d'être sauvegardé et son impact sur les sessions futures."""


def get_llm_with_tools():
    """Retourne le LLM avec les outils @tool bindés — le LLM peut alors les appeler (ReAct)."""
    if _llm_client is None:
        return None
    try:
        # Import local pour éviter les imports circulaires au chargement du module
        from tools import TOUS_LES_OUTILS
        return _llm_client.bind_tools(TOUS_LES_OUTILS)
    except Exception:
        return _llm_client


def _call_llm(system_prompt: str, user_prompt: str) -> str:
    """Appel générique au LLM avec les tools bindés."""
    from langchain_core.messages import SystemMessage, HumanMessage
    llm = get_llm_with_tools() or _llm_client
    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ])
    return response.content


def react_planificateur(diagnostic: dict, parcours: list) -> str:
    """Vrai loop ReAct : Reason → Act (appel outil) → Observe → Reason → réponse finale.

    Le LLM peut appeler outil_rag_ressources et outil_sm2_revision pendant son raisonnement.
    Retourne None si LLM indisponible — l'appelant bascule sur CoT fallback.
    """
    if LLM_PROVIDER == "fallback" or _llm_client is None:
        return None

    try:
        from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
        from tools import outil_rag_ressources, outil_sm2_revision, TOUS_LES_OUTILS

        llm_with_tools = _llm_client.bind_tools(TOUS_LES_OUTILS)
        lacunes        = ", ".join(diagnostic.get("lacunes", [])) or "aucune"
        notion_cible   = diagnostic.get("notion_cible", "?")

        system_react = PLANIFICATEUR_SYSTEM_PROMPT + """

Tu as accès aux outils suivants — utilise-les avant de raisonner :
- outil_rag_ressources(notion, n_resultats) : cherche les ressources pédagogiques disponibles
- outil_sm2_revision(etudiant, notion, qualite) : calcule la date de prochaine révision SM-2

Commence par appeler ces outils, puis construis ton raisonnement Chain-of-Thought."""

        messages = [
            SystemMessage(content=system_react),
            HumanMessage(content=(
                f"Étudiant : {diagnostic.get('etudiant')} | Module : {diagnostic.get('module')}\n"
                f"Score : {diagnostic.get('pourcentage')}%\n"
                f"Lacunes : {lacunes} | Notion prioritaire : {notion_cible}\n\n"
                f"Utilise tes outils puis explique le parcours optimal en Chain-of-Thought."
            ))
        ]

        # Boucle ReAct — max 4 itérations (Reason → Act → Observe → Reason...)
        for _ in range(4):
            response = llm_with_tools.invoke(messages)

            if not getattr(response, 'tool_calls', None):
                return response.content  # réponse finale sans appel d'outil

            # Le LLM a appelé un ou plusieurs outils → exécution
            messages.append(response)
            for tc in response.tool_calls:
                name, args, tid = tc["name"], tc["args"], tc["id"]
                if name == "outil_rag_ressources":
                    res = outil_rag_ressources.invoke(args)
                    obs = f"{len(res)} ressource(s) — " + " | ".join(
                        r.get("contenu", "")[:80] for r in res[:2])
                elif name == "outil_sm2_revision":
                    res = outil_sm2_revision.invoke(args)
                    obs = (f"Révision : {res.get('prochaine_revision')} "
                           f"(dans {res.get('intervalle_jours')} j, EF={res.get('facteur_facilite')})")
                else:
                    obs = "Outil exécuté."
                messages.append(ToolMessage(content=obs, tool_call_id=tid))

        return response.content

    except Exception:
        return None  # appelant utilise le fallback CoT


# Flag ReAct — nécessite un modèle avec tool_calling natif (ex: GPT-4, Claude)
# Mettre à True si le modèle supporte les function calls (OpenRouter peut ne pas les supporter)
REACT_ENABLED = False

# Raisonnement du Planificateur — ReAct si activé, sinon CoT, sinon fallback
def reason_planificateur(diagnostic: dict, parcours: list) -> str:
    # 1. Loop ReAct (Reason → Act → Observe → Answer) — activé si REACT_ENABLED=True
    if REACT_ENABLED:
        react_result = react_planificateur(diagnostic, parcours)
        if react_result:
            return react_result

    # 2. CoT simple (Zero-shot + Few-shot examples dans le prompt)
    if LLM_PROVIDER != "fallback" and _llm_client is not None:
        try:
            lacunes  = ", ".join(diagnostic.get("lacunes", [])) or "aucune"
            maitrise = ", ".join(diagnostic.get("notions_maitrisees", [])) or "aucune"
            etapes   = " → ".join(e.get("notion", "?") for e in parcours) or "rien"
            prompt = (
                f"Étudiant : {diagnostic.get('etudiant')} | Module : {diagnostic.get('module')}\n"
                f"Score : {diagnostic.get('pourcentage')}%\n"
                f"Maîtrisées : {maitrise}\nLacunes : {lacunes}\n"
                f"Parcours proposé : {etapes}\n\n"
                f"Explique en Chain-of-Thought pourquoi cet ordre est pertinent."
            )
            return _call_llm(PLANIFICATEUR_SYSTEM_PROMPT, prompt)
        except Exception:
            pass

    # Fallback déterministe — même structure que le LLM mais sans appel réseau
    score      = diagnostic.get("pourcentage", 0)
    lacunes    = diagnostic.get("lacunes", [])
    maitrisees = diagnostic.get("notions_maitrisees", [])
    nb_etapes  = len(parcours)

    if score >= 80:
        return "\n".join([
            f"**Étape 1 — Niveau** : {score}% → niveau avancé, {len(maitrisees)} notion(s) déjà maîtrisée(s).",
            "**Étape 2 — Décision** : Conditional Edge LangGraph activée → Planificateur et Pédagogue sautés, direct au Coach.",
            "**Recommandation** : Maintenir l'acquis par révisions espacées SM-2."
        ])
    elif score >= 50:
        return "\n".join([
            f"**Étape 1 — Analyse** : Score intermédiaire ({score}%), {len(lacunes)} lacune(s) sur les notions avancées.",
            f"**Étape 2 — Prérequis** : Les notions maîtrisées ({', '.join(maitrisees[:2])}) servent de base.",
            f"**Étape 3 — Parcours** : {nb_etapes} étape(s) ordonnées par complexité croissante.",
            "**Étape 4 — SM-2** : Intervalles de révision progressifs, croissants si les réponses sont bonnes."
        ])
    else:
        return "\n".join([
            f"**Étape 1 — Analyse** : Score faible ({score}%) — profil débutant.",
            "**Étape 2 — Stratégie** : Commencer par les fondamentaux, respecter le graphe de prérequis.",
            f"**Étape 3 — Parcours** : {nb_etapes} étape(s) du niveau 1 vers les niveaux supérieurs.",
            "**Étape 4 — Coach** : Intervalles SM-2 courts au début (1 jour → 6 jours) pour ancrer les bases."
        ])


# Raisonnement du Diagnosticien (analyse du rapport de test)
def reason_diagnosticien(rapport: dict) -> str:
    if LLM_PROVIDER != "fallback" and _llm_client is not None:
        try:
            lacunes  = ", ".join(rapport.get("lacunes", [])) or "aucune"
            maitrise = ", ".join(rapport.get("notions_maitrisees", [])) or "aucune"
            prompt = (
                f"Étudiant : {rapport.get('etudiant')} | Module : {rapport.get('module')}\n"
                f"Score : {rapport.get('pourcentage')}% ({rapport.get('score')}/{rapport.get('total')})\n"
                f"Niveau : {rapport.get('niveau_global')}\n"
                f"Maîtrisées : {maitrise}\nLacunes : {lacunes}\n"
                f"Notion prioritaire : {rapport.get('notion_cible')}\n\n"
                f"Analyse ce diagnostic en Chain-of-Thought."
            )
            return _call_llm(DIAGNOSTICIEN_SYSTEM_PROMPT, prompt)
        except Exception:
            pass

    score        = rapport.get("pourcentage", 0)
    lacunes      = rapport.get("lacunes", [])
    maitrisees   = rapport.get("notions_maitrisees", [])
    notion_cible = rapport.get("notion_cible", "?")
    niveau       = rapport.get("niveau_global", "?")
    return "\n".join([
        f"**Étape 1 — Score** : {score}% → niveau **{niveau}**.",
        f"**Étape 2 — Points forts** : {len(maitrisees)} notion(s) maîtrisée(s)"
            + (f" : {', '.join(maitrisees[:3])}." if maitrisees else "."),
        f"**Étape 3 — Lacunes** : {len(lacunes)} notion(s) à combler"
            + (f" : {', '.join(lacunes[:3])}." if lacunes else " — aucune."),
        f"**Étape 4 — Priorité** : Notion cible → **{notion_cible}**.",
    ])


# Raisonnement du Coach (justification de l'intervalle SM-2 calculé)
def reason_coach(etudiant: str, notion: str, qualite: int, resultat_sm2: dict) -> str:
    if LLM_PROVIDER != "fallback" and _llm_client is not None:
        try:
            prompt = (
                f"Étudiant : {etudiant} | Notion : {notion}\n"
                f"Qualité : {qualite}/5 | Intervalle calculé : {resultat_sm2.get('intervalle_jours')} jour(s)\n"
                f"Prochaine révision : {resultat_sm2.get('prochaine_revision')}\n"
                f"Facteur facilité (EF) : {resultat_sm2.get('facteur_facilite')} | "
                f"Répétitions réussies : {resultat_sm2.get('repetitions')}\n\n"
                f"Explique en Chain-of-Thought pourquoi cet intervalle est optimal."
            )
            return _call_llm(COACH_SYSTEM_PROMPT, prompt)
        except Exception:
            pass

    intervalle = resultat_sm2.get("intervalle_jours", 1)
    ef         = resultat_sm2.get("facteur_facilite", 2.5)
    prochaine  = resultat_sm2.get("prochaine_revision", "?")
    return "\n".join([
        f"**Étape 1 — Qualité** : {qualite}/5 → "
            + ("bonne maîtrise, intervalle prolongé." if qualite >= 3 else "difficulté, retour à l'intervalle minimal (1 jour)."),
        f"**Étape 2 — Calcul SM-2** : Intervalle = **{intervalle} jour(s)**.",
        f"**Étape 3 — Facteur facilité** : EF = {ef} "
            + ("(stable — mémorisation efficace)." if ef >= 2.3 else "(en baisse — notion difficile pour cet étudiant)."),
        f"**Étape 4 — Décision** : Prochaine révision planifiée au **{prochaine}**.",
    ])


# Raisonnement du Tracker (confirmation de la sauvegarde et impact futur)
def reason_tracker(nom: str, notion: str, score: int) -> str:
    if LLM_PROVIDER != "fallback" and _llm_client is not None:
        try:
            prompt = (
                f"Étudiant : {nom} | Notion sauvegardée : {notion} | Score : {score}/5\n\n"
                f"Explique ce que cette sauvegarde apporte pour les sessions futures."
            )
            return _call_llm(TRACKER_SYSTEM_PROMPT, prompt)
        except Exception:
            pass

    return "\n".join([
        f"**Étape 1 — Persistance** : Session de **{nom}** sur **{notion}** (score={score}/5) enregistrée dans `data/profils_etudiants.json`.",
        "**Étape 2 — Mémoire long-terme** : Le Diagnosticien utilisera ce profil à la prochaine session pour ne pas repartir de zéro.",
        "**Étape 3 — Impact** : "
            + ("Bon score → notion marquée maîtrisée, le parcours sera allégé."
               if score >= 3 else "Score faible → notion reste prioritaire au prochain diagnostic."),
    ])


if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    print(f"Provider LLM : {LLM_PROVIDER}\n")

    fake_diag = {
        "etudiant": "Yassine", "module": "MSA", "pourcentage": 50,
        "notions_maitrisees": ["Agents Intelligents", "Communication Inter-agents"],
        "lacunes": ["Framework CrewAI", "Framework LangGraph"]
    }
    fake_parcours = [
        {"ordre": 1, "notion": "Framework CrewAI"},
        {"ordre": 2, "notion": "Framework LangGraph"}
    ]
    print("--- Planificateur (Chain-of-Thought) ---")
    print(reason_planificateur(fake_diag, fake_parcours))

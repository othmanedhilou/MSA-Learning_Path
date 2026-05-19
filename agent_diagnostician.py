# Agent Diagnosticien — test adaptatif : bonne réponse → difficulté monte, mauvaise → redescend
import json
import os
import random
from mind_layer import reason_diagnosticien

class AgentDiagnostician:
    def __init__(self):
        base = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(base, 'data/questions.json'), 'r', encoding='utf-8') as f:
            self.questions_db = json.load(f)
        with open(os.path.join(base, 'data/prerequis.json'), 'r', encoding='utf-8') as f:
            self.prerequis_db = json.load(f)

    def _get_questions(self, module, notion, niveau):
        """Récupère une question pour une notion et un niveau donnés."""
        for entry in self.questions_db:
            if entry['module'] == module and entry['notion'] == notion:
                for q in entry['questions']:
                    if q['niveau'] == niveau:
                        return q
        return None

    def _get_notions(self, module):
        """Retourne les notions ordonnées par niveau pour un module."""
        notions = self.prerequis_db['modules'].get(module, {}).get('notions', [])
        return sorted(notions, key=lambda x: x['niveau'])

    def run_diagnostic(self, module, nom_etudiant="Etudiant"):
        """
        Lance le test adaptatif complet pour un module.
        - Bonne réponse  → notion plus difficile
        - Mauvaise réponse → retour aux prérequis
        Retourne un rapport de diagnostic.
        """
        print(f"\n{'='*55}")
        print(f"  DIAGNOSTIC ADAPTATIF — {module}")
        print(f"  Etudiant : {nom_etudiant}")
        print(f"{'='*55}\n")

        notions = self._get_notions(module)
        if not notions:
            print(f"Module '{module}' introuvable.")
            return None

        resultats = {}       # notion -> score (0 ou 1)
        lacunes = []
        maitrisees = []

        niveau_actuel = "facile"
        niveaux = ["facile", "moyen", "difficile"]

        for i, notion_info in enumerate(notions):
            notion = notion_info['label']
            print(f"--- Notion {i+1}/{len(notions)} : {notion} ---")

            q = self._get_questions(module, notion, niveau_actuel)
            if not q:
                # Fallback si niveau non dispo
                q = self._get_questions(module, notion, "facile")
            if not q:
                print(f"  [!] Pas de question pour cette notion, on passe.\n")
                continue

            # Afficher la question
            print(f"\n  [{niveau_actuel.upper()}] {q['question']}")
            for idx, opt in enumerate(q['options']):
                print(f"    {idx}) {opt}")

            # Lire la réponse
            while True:
                try:
                    reponse = int(input("\n  Votre réponse (0-3) : "))
                    if reponse in range(len(q['options'])):
                        break
                    print("  Entrez un chiffre valide.")
                except ValueError:
                    print("  Entrez un chiffre.")

            correct = (reponse == q['reponse'])
            resultats[notion] = 1 if correct else 0

            if correct:
                print(f"  ✅ Correct !\n")
                maitrisees.append(notion)
                # Monter en difficulté
                idx_niv = niveaux.index(niveau_actuel)
                if idx_niv < len(niveaux) - 1:
                    niveau_actuel = niveaux[idx_niv + 1]
            else:
                print(f"  ❌ Incorrect. Bonne réponse : {q['options'][q['reponse']]}\n")
                lacunes.append(notion)
                # Revenir au niveau facile (retour aux prérequis)
                niveau_actuel = "facile"

        # Calcul du score global
        score_global = sum(resultats.values())
        total = len(resultats)
        pourcentage = round((score_global / total) * 100) if total > 0 else 0

        # Notion prioritaire à travailler (première lacune)
        notion_cible = lacunes[0] if lacunes else maitrisees[-1] if maitrisees else notions[0]['label']

        rapport = {
            "etudiant": nom_etudiant,
            "module": module,
            "score": score_global,
            "total": total,
            "pourcentage": pourcentage,
            "notions_maitrisees": maitrisees,
            "lacunes": lacunes,
            "notion_cible": notion_cible,
            "niveau_global": self._evaluer_niveau(pourcentage)
        }

        self._afficher_rapport(rapport)
        self._sauver_rapport(rapport)
        return rapport

    def _evaluer_niveau(self, pourcentage):
        if pourcentage >= 80:
            return "Avancé"
        elif pourcentage >= 50:
            return "Intermédiaire"
        else:
            return "Débutant"

    def _afficher_rapport(self, rapport):
        print(f"\n{'='*55}")
        print(f"  RAPPORT DE DIAGNOSTIC")
        print(f"{'='*55}")
        print(f"  Etudiant  : {rapport['etudiant']}")
        print(f"  Module    : {rapport['module']}")
        print(f"  Score     : {rapport['score']}/{rapport['total']} ({rapport['pourcentage']}%)")
        print(f"  Niveau    : {rapport['niveau_global']}")
        print(f"\n  ✅ Notions maîtrisées : {', '.join(rapport['notions_maitrisees']) or 'Aucune'}")
        print(f"  ❌ Lacunes détectées  : {', '.join(rapport['lacunes']) or 'Aucune'}")
        print(f"\n  🎯 Notion prioritaire à travailler : {rapport['notion_cible']}")
        print(f"{'='*55}\n")

    def _sauver_rapport(self, rapport):
        """Sauvegarde le rapport dans data/rapports_diagnostic.json"""
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/rapports_diagnostic.json')
        rapports = []
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                rapports = json.load(f)
        rapports.append(rapport)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(rapports, f, ensure_ascii=False, indent=4)

    def get_lacune_pour_app(self, module, nom_etudiant="Etudiant"):
        """Retourne directement la notion cible (lacune principale) pour intégration UI."""
        rapport = self.run_diagnostic(module, nom_etudiant)
        if rapport:
            return rapport['notion_cible']
        return None

    def run_diagnostic_for_profile(self, module, profile):
        """Diagnostic non-interactif basé sur profile['historique'] + score_initial — pour Streamlit."""
        notions = self._get_notions(module)
        if not notions:
            return None

        # Construire les ensembles à partir de l'historique du profil
        historique = {h['notion']: h['maitrise'] for h in profile.get('historique', [])}
        score_initial = profile.get('score_initial', 50)

        # Calculer mastery par notion (du module courant)
        notions_maitrisees = []
        lacunes = []
        resultats = {}

        for notion_info in notions:
            label = notion_info['label']
            # Si dans l'historique, prendre la valeur explicite
            if label in historique:
                maitrise = historique[label]
            else:
                # Sinon, déduire du score initial + niveau
                # Avancé (>= 80) : maîtrise tout sauf le niveau 4 max
                # Intermédiaire (50-79) : maîtrise niveau 1-2, échec sur 3-4
                # Débutant (< 50) : échec partout sauf peut-être niveau 1
                niveau = notion_info.get('niveau', 1)
                if score_initial >= 80:
                    # Avance : maitrise tout (l'historique peut surcharger)
                    maitrise = True
                elif score_initial >= 50:
                    maitrise = (niveau <= 2)
                else:
                    maitrise = False

            resultats[label] = 1 if maitrise else 0
            if maitrise:
                notions_maitrisees.append(label)
            else:
                lacunes.append(label)

        total = len(resultats)
        score = sum(resultats.values())
        pourcentage = round((score / total) * 100) if total > 0 else 0

        # Notion cible = première lacune
        notion_cible = (lacunes[0] if lacunes
                        else (notions_maitrisees[-1] if notions_maitrisees
                              else notions[0]['label']))

        rapport = {
            "etudiant": profile.get('nom', 'Etudiant'),
            "module": module,
            "score": score,
            "total": total,
            "pourcentage": pourcentage,
            "notions_maitrisees": notions_maitrisees,
            "lacunes": lacunes,
            "notion_cible": notion_cible,
            "niveau_global": self._evaluer_niveau(pourcentage),
        }
        rapport["raisonnement"] = reason_diagnosticien(rapport)
        self._sauver_rapport(rapport)
        return rapport

    def run_diagnostic_with_answers(self, module, nom_etudiant, answers):
        """Diagnostic adaptatif à partir des réponses collectées dans l'UI Streamlit (quiz)."""
        notions = self._get_notions(module)
        if not notions:
            return None

        resultats = {}
        lacunes = []
        notions_maitrisees = []
        niveau_actuel = "facile"
        niveaux = ["facile", "moyen", "difficile"]

        for notion_info in notions:
            notion = notion_info['label']
            q = self._get_questions(module, notion, niveau_actuel) \
                or self._get_questions(module, notion, "facile")
            if not q:
                continue

            reponse = answers.get(notion, -1)
            correct = (reponse == q['reponse'])
            resultats[notion] = 1 if correct else 0

            if correct:
                notions_maitrisees.append(notion)
                idx = niveaux.index(niveau_actuel)
                if idx < len(niveaux) - 1:
                    niveau_actuel = niveaux[idx + 1]
            else:
                lacunes.append(notion)
                niveau_actuel = "facile"

        total = len(resultats)
        score = sum(resultats.values())
        pourcentage = round((score / total) * 100) if total > 0 else 0
        notion_cible = (lacunes[0] if lacunes
                        else (notions_maitrisees[-1] if notions_maitrisees
                              else notions[0]['label']))

        rapport = {
            "etudiant": nom_etudiant,
            "module": module,
            "score": score,
            "total": total,
            "pourcentage": pourcentage,
            "notions_maitrisees": notions_maitrisees,
            "lacunes": lacunes,
            "notion_cible": notion_cible,
            "niveau_global": self._evaluer_niveau(pourcentage),
        }
        rapport["raisonnement"] = reason_diagnosticien(rapport)
        self._sauver_rapport(rapport)
        return rapport


if __name__ == '__main__':
    agent = AgentDiagnostician()
    modules = ["MSA", "Data Mining", "Deep Learning", "Data Warehouse", "Big Data"]
    print("Modules disponibles :")
    for i, m in enumerate(modules):
        print(f"  {i}) {m}")
    choix = int(input("\nChoisir un module (0-4) : "))
    nom = input("Votre prénom : ")
    agent.run_diagnostic(modules[choix], nom)

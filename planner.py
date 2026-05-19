# Agent Planificateur — construit le parcours d'apprentissage en respectant les prérequis
# Utilise SM-2 pour planifier les dates de session et estimer les durées
import json
import os
from datetime import datetime, timedelta
from sm2 import SM2

class AgentPlanificateur:
    def __init__(self):
        base = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(base, 'data/prerequis.json'), 'r', encoding='utf-8') as f:
            self.prerequis_db = json.load(f)
        self.sm2 = SM2()

    def _get_notions(self, module):
        """Retourne les notions ordonnées par niveau (pré-requis respectés)."""
        notions = self.prerequis_db['modules'].get(module, {}).get('notions', [])
        return sorted(notions, key=lambda x: x['niveau'])

    def _trouver_index_lacune(self, notions, notion_cible):
        """Trouve la position de la notion cible dans la liste."""
        for i, n in enumerate(notions):
            if n['label'] == notion_cible:
                return i
        return 0

    def construire_parcours(self, module, lacunes, notions_maitrisees, nom_etudiant="Etudiant"):
        """Construit le parcours ordonné par prérequis avec planning SM-2 et durées estimées."""
        print(f"\n{'='*55}")
        print(f"  AGENT PLANIFICATEUR — {module}")
        print(f"  Etudiant : {nom_etudiant}")
        print(f"{'='*55}")

        toutes_notions = self._get_notions(module)

        # Étape 1 : identifier les notions non maîtrisées dans l'ordre des prérequis
        print("\n  [1] Analyse des pré-requis...")
        a_apprendre = []
        for notion_info in toutes_notions:
            label = notion_info['label']
            if label in lacunes or label not in notions_maitrisees:
                a_apprendre.append(notion_info)
                statut = "❌ lacune" if label in lacunes else "⬜ non vue"
                print(f"      → {label} ({statut})")
            else:
                print(f"      → {label} ✅ maîtrisée")

        if not a_apprendre:
            print("\n  Bravo ! Toutes les notions sont maîtrisées.")
            return {"parcours": [], "message": "Module complété !"}

        # Etape 2 : planifier avec SM-2
        print("\n  [2] Planification SM-2...")
        parcours = []
        date_courante = datetime.today()

        for i, notion_info in enumerate(a_apprendre):
            notion = notion_info['label']
            niveau = notion_info['niveau']

            # Qualité initiale : 0 si lacune, 3 si non vue
            qualite_initiale = 0 if notion in lacunes else 3
            res_sm2 = self.sm2.calculer(nom_etudiant, notion, qualite_initiale)

            # Durée estimée selon le niveau
            durees = {1: 30, 2: 45, 3: 60, 4: 90}
            duree = durees.get(niveau, 45)

            etape = {
                "ordre": i + 1,
                "notion": notion,
                "niveau_difficulte": niveau,
                "statut": "lacune" if notion in lacunes else "a_apprendre",
                "date_session": date_courante.strftime("%Y-%m-%d"),
                "duree_estimee_min": duree,
                "prochaine_revision": res_sm2['prochaine_revision'],
                "intervalle_revision": self.sm2.resume_texte(res_sm2)
            }
            parcours.append(etape)

            print(f"      Etape {i+1} : {notion}")
            print(f"        📅 Session : {etape['date_session']}")
            print(f"        ⏱  Durée   : {duree} min")
            print(f"        🔁 Révision: {etape['intervalle_revision']}")

            date_courante += timedelta(days=1)

        # Etape 3 : résumé
        total_minutes = sum(e['duree_estimee_min'] for e in parcours)
        total_jours = len(parcours)

        rapport = {
            "etudiant": nom_etudiant,
            "module": module,
            "parcours": parcours,
            "resume": {
                "nb_notions": len(parcours),
                "duree_totale_min": total_minutes,
                "duree_totale_h": round(total_minutes / 60, 1),
                "nb_jours_estime": total_jours,
                "date_debut": parcours[0]['date_session'],
                "date_fin_estimee": parcours[-1]['date_session']
            }
        }

        self._afficher_resume(rapport)
        self._sauver_parcours(rapport)
        return rapport

    def _afficher_resume(self, rapport):
        r = rapport['resume']
        print(f"\n  {'='*45}")
        print(f"  PARCOURS GENERE")
        print(f"  {'='*45}")
        print(f"  Notions à travailler : {r['nb_notions']}")
        print(f"  Durée totale estimée : {r['duree_totale_h']}h ({r['duree_totale_min']} min)")
        print(f"  Durée en jours       : {r['nb_jours_estime']} jours")
        print(f"  Début                : {r['date_debut']}")
        print(f"  Fin estimée          : {r['date_fin_estimee']}")
        print(f"  {'='*45}\n")

    def _sauver_parcours(self, rapport):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/parcours_etudiants.json')
        parcours_list = []
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                parcours_list = json.load(f)
        parcours_list.append(rapport)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(parcours_list, f, ensure_ascii=False, indent=4)

    def get_parcours_pour_app(self, module, lacunes, notions_maitrisees, nom_etudiant="Etudiant"):
        """
        Interface simplifiée pour app.py de DODO.
        Retourne directement la liste des étapes du parcours.
        """
        rapport = self.construire_parcours(module, lacunes, notions_maitrisees, nom_etudiant)
        return rapport.get('parcours', [])


# ─── TEST RAPIDE ───────────────────────────────────────────
if __name__ == '__main__':
    planner = AgentPlanificateur()
    planner.construire_parcours(
        module="MSA",
        lacunes=["Communication Inter-agents", "Framework CrewAI"],
        notions_maitrisees=["Agents Intelligents"],
        nom_etudiant="othmane"
    )

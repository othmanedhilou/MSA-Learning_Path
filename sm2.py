# Algorithme SuperMemo-2 (SM-2) — répétition espacée
# Calcule l'intervalle optimal avant la prochaine révision selon la qualité de réponse (0-5)
# Même algorithme que celui utilisé par Anki
import json
import os
from datetime import datetime, timedelta

class SM2:
    def __init__(self):
        self.path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/sm2_profils.json')
        self.profils = self._charger()

    def _charger(self):
        if os.path.exists(self.path):
            with open(self.path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _sauver(self):
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self.profils, f, ensure_ascii=False, indent=4)

    def _cle(self, etudiant, notion):
        return f"{etudiant}::{notion}"

    def _init_carte(self):
        """Valeurs initiales SM-2 pour une nouvelle notion."""
        return {
            "intervalle": 1,       # jours avant prochaine révision
            "repetitions": 0,      # nombre de répétitions réussies
            "facilite": 2.5,       # facteur de facilité (EF), entre 1.3 et 2.5
            "prochaine_revision": datetime.today().strftime("%Y-%m-%d")
        }

    def calculer(self, etudiant, notion, qualite):
        """
        Met à jour la carte SM-2 d'une notion pour un étudiant.

        qualite : int entre 0 et 5
          5 = réponse parfaite
          4 = bonne réponse avec hésitation
          3 = réponse correcte mais difficile
          2 = mauvaise réponse mais souvenir correct après
          1 = mauvaise réponse, souvenir vague
          0 = aucun souvenir

        Retourne un dict avec l'intervalle et la date de prochaine révision.
        """
        cle = self._cle(etudiant, notion)
        carte = self.profils.get(cle, self._init_carte())

        if qualite >= 3:
            # Réponse correcte → avancer
            if carte['repetitions'] == 0:
                carte['intervalle'] = 1
            elif carte['repetitions'] == 1:
                carte['intervalle'] = 6
            else:
                carte['intervalle'] = round(carte['intervalle'] * carte['facilite'])
            carte['repetitions'] += 1
        else:
            # Réponse incorrecte → recommencer
            carte['repetitions'] = 0
            carte['intervalle'] = 1

        # Mise à jour du facteur de facilité (EF)
        ef = carte['facilite'] + (0.1 - (5 - qualite) * (0.08 + (5 - qualite) * 0.02))
        carte['facilite'] = max(1.3, round(ef, 2))

        # Date de prochaine révision
        prochaine = datetime.today() + timedelta(days=carte['intervalle'])
        carte['prochaine_revision'] = prochaine.strftime("%Y-%m-%d")

        self.profils[cle] = carte
        self._sauver()

        return {
            "notion": notion,
            "intervalle_jours": carte['intervalle'],
            "prochaine_revision": carte['prochaine_revision'],
            "facteur_facilite": carte['facilite'],
            "repetitions": carte['repetitions']
        }

    def get_planning(self, etudiant):
        """Retourne toutes les notions à réviser aujourd'hui pour un étudiant."""
        aujourd_hui = datetime.today().strftime("%Y-%m-%d")
        a_reviser = []
        for cle, carte in self.profils.items():
            if cle.startswith(f"{etudiant}::"):
                notion = cle.split("::")[1]
                if carte['prochaine_revision'] <= aujourd_hui:
                    a_reviser.append({
                        "notion": notion,
                        "prochaine_revision": carte['prochaine_revision'],
                        "repetitions": carte['repetitions']
                    })
        return sorted(a_reviser, key=lambda x: x['prochaine_revision'])

    def resume_texte(self, resultat):
        """Convertit le résultat SM-2 en phrase lisible pour l'interface."""
        j = resultat['intervalle_jours']
        if j == 1:
            return "Demain"
        elif j <= 3:
            return f"Dans {j} jours"
        elif j <= 14:
            return f"Dans {j} jours"
        else:
            semaines = j // 7
            return f"Dans {semaines} semaine(s)"


# ─── TEST RAPIDE ───────────────────────────────────────────
if __name__ == '__main__':
    sm2 = SM2()
    print("=== Test SM-2 ===")
    tests = [
        ("othmane", "Agents Intelligents", 5),
        ("othmane", "Agents Intelligents", 4),
        ("othmane", "K-Means Clustering", 2),
        ("othmane", "Transformers", 5),
    ]
    for etudiant, notion, qualite in tests:
        res = sm2.calculer(etudiant, notion, qualite)
        print(f"  {notion} (qualité={qualite}) → {sm2.resume_texte(res)} ({res['prochaine_revision']})")

    print("\n=== Planning de révision othmane ===")
    planning = sm2.get_planning("othmane")
    for p in planning:
        print(f"  📅 {p['notion']} — révision le {p['prochaine_revision']}")

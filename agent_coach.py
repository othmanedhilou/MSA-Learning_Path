# Agent Coach — planification des révisions avec l'algorithme SuperMemo-2
# SM-2 est l'algorithme de référence utilisé par Anki : ajuste l'intervalle
# selon la qualité de réponse (0=oublié, 5=parfait) et un facteur de facilité.
from sm2 import SM2
from mind_layer import reason_coach


class AgentCoach:

    def __init__(self):
        self.sm2 = SM2()

    def calculer_revision(self, etudiant: str, notion: str, qualite: int) -> dict:
        """Calcule la prochaine date de révision et génère le raisonnement CoT."""
        resultat = self.sm2.calculer(etudiant, notion, qualite)
        resultat["raisonnement"] = reason_coach(etudiant, notion, qualite, resultat)
        return resultat

    def resume_texte(self, resultat: dict) -> str:
        """Convertit le résultat SM-2 en phrase lisible (ex: 'Dans 6 jours')."""
        return self.sm2.resume_texte(resultat)

    def get_planning(self, etudiant: str) -> list:
        """Retourne toutes les notions à réviser aujourd'hui pour un étudiant."""
        return self.sm2.get_planning(etudiant)


if __name__ == "__main__":
    agent = AgentCoach()
    res = agent.calculer_revision("othmane", "LangGraph", 4)
    print(f"Prochaine révision : {res['prochaine_revision']} (dans {res['intervalle_jours']} jour(s))")
    print(f"Facteur facilité   : {res['facteur_facilite']}")
    print(f"Résumé             : {agent.resume_texte(res)}")

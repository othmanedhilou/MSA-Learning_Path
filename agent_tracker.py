# Agent Tracker — mémoire long-terme du SMA
# Persiste chaque session dans un fichier JSON pour que les sessions futures
# puissent reprendre depuis le bon niveau sans re-diagnostiquer l'étudiant.
import json
import os
from mind_layer import reason_tracker


class AgentTracker:

    def __init__(self):
        self.log_file = 'data/historique_etudiants.json'
        if not os.path.exists('data'):
            os.makedirs('data')

    def sauver_progres(self, nom: str, notion: str, score: int):
        """Ajoute une entrée dans l'historique et retourne le raisonnement CoT."""
        historique = []
        if os.path.exists(self.log_file):
            with open(self.log_file, 'r', encoding='utf-8') as f:
                historique = json.load(f)
        historique.append({"etudiant": nom, "notion": notion, "score": score})
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(historique, f, indent=4, ensure_ascii=False)
        return reason_tracker(nom, notion, score)

    def charger_dernier_score(self, nom: str):
        """Retourne la dernière entrée de session pour un étudiant donné."""
        if os.path.exists(self.log_file):
            with open(self.log_file, 'r', encoding='utf-8') as f:
                h = json.load(f)
            resultats = [x for x in h if x['etudiant'] == nom]
            return resultats[-1] if resultats else None
        return None

    def charger_historique(self, nom: str) -> list:
        """Retourne tout l'historique de sessions pour un étudiant."""
        if os.path.exists(self.log_file):
            with open(self.log_file, 'r', encoding='utf-8') as f:
                h = json.load(f)
            return [x for x in h if x['etudiant'] == nom]
        return []


if __name__ == "__main__":
    agent = AgentTracker()
    agent.sauver_progres("othmane", "LangGraph", 4)
    print(f"Dernier score    : {agent.charger_dernier_score('othmane')}")
    print(f"Sessions totales : {len(agent.charger_historique('othmane'))}")

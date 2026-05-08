import json
import os

class AgentPedagogue:
    def __init__(self):
        path = 'data/ressources.json' if os.path.exists('data/ressources.json') else 'ressources.json'
        with open(path, 'r', encoding='utf-8') as f:
            self.db = json.load(f)
    
    def get_ressources(self, notion):
        return [r for r in self.db if r['notion'] == notion]

class AgentTracker:
    def __init__(self):
        self.log_file = 'data/historique_etudiants.json'
        if not os.path.exists('data'): os.makedirs('data')

    def sauver_progres(self, nom, notion, score):
        # On charge l'existant ou on crée une liste vide
        historique = []
        if os.path.exists(self.log_file):
            with open(self.log_file, 'r') as f: historique = json.load(f)
        
        # On ajoute la nouvelle session
        historique.append({"etudiant": nom, "notion": notion, "score": score})
        
        with open(self.log_file, 'w') as f:
            json.dump(historique, f, indent=4)

    def charger_dernier_score(self, nom):
        # Pour afficher le dernier score de l'étudiant
        if os.path.exists(self.log_file):
            with open(self.log_file, 'r') as f:
                h = json.load(f)
                resultats = [x for x in h if x['etudiant'] == nom]
                return resultats[-1] if resultats else None
        return None

class AgentCoach:
    def calculer_revision(self, score):
        if score < 3: return "Demain"
        elif score < 5: return "Dans 3 jours"
        else: return "Dans 7 jours"
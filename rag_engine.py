import os
import json

class RAGEngine:
    def __init__(self):
        base = os.path.dirname(os.path.abspath(__file__))
        self.ressources_path = os.path.join(base, 'data/ressources_textes')
        self.json_path = os.path.join(base, 'data/ressources.json')

    def chercher_ressources(self, notion_cible):
        """
        Tâche D1/D3 de Dodo : Recherche les ressources (Catalogue + Extraits textes).
        """
        resultats = []
        
        # 1. Recherche dans le JSON (Liens officiels)
        if os.path.exists(self.json_path):
            with open(self.json_path, 'r', encoding='utf-8') as f:
                try:
                    db = json.load(f)
                    for r in db:
                        if notion_cible.lower() in r.get('notion', '').lower():
                            resultats.append({
                                "type": r.get('type', 'Lien'),
                                "description": r.get('description', ''),
                                "url": r.get('url', '#'),
                                "source": "Catalogue JSON",
                                "contenu": r.get('description', '') # Pour l'affichage UI
                            })
                except: pass

        # 2. Recherche dans les fichiers textes (Le vrai RAG)
        if os.path.exists(self.ressources_path):
            for filename in os.listdir(self.ressources_path):
                if filename.endswith(".txt"):
                    with open(os.path.join(self.ressources_path, filename), 'r', encoding='utf-8') as f:
                        content = f.read()
                        if notion_cible.lower() in content.lower():
                            resultats.append({
                                "type": "Extrait du cours",
                                "description": "Détails approfondis trouvés par l'agent RAG.",
                                "url": "#",
                                "source": filename,
                                "contenu": content # On donne tout le texte
                            })
        
        return resultats
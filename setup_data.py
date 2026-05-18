import os

# --- CONFIGURATION ---
# Dossier où seront stockés les textes pour le moteur RAG
folder = "data/ressources_textes"

# --- CONTENU DES COURS (Basé sur tes notions) ---
# On crée des résumés textuels que l'IA pourra "lire" et comparer
ressources = {
    "MSA_Agents.txt": """
    NOTION: Agents Intelligents. 
    Un agent intelligent est une entité autonome qui perçoit son environnement à l'aide de capteurs et agit sur celui-ci via des actionneurs. 
    Il possède quatre propriétés clés : l'autonomie, la réactivité, la proactivité et la capacité sociale. 
    Les types d'agents incluent les agents de réflexion simple, les agents basés sur des modèles, les agents basés sur des objectifs et les agents basés sur l'utilité.
    """,

    "MSA_Communication.txt": """
    NOTION: Communication Inter-agents & FIPA-ACL. 
    Pour collaborer, les agents utilisent un langage de communication appelé ACL (Agent Communication Language). 
    Le standard FIPA-ACL définit des 'performatives' (types de messages) comme INFORM (pour donner une info), 
    REQUEST (pour demander une action), ou QUERY (pour poser une question). 
    Cela permet l'interopérabilité entre différents systèmes multi-agents.
    """,

    "MSA_Frameworks.txt": """
    NOTION: Framework CrewAI et LangGraph. 
    CrewAI est conçu pour orchestrer des agents de manière collaborative en définissant des rôles (Processus séquentiel ou hiérarchique). 
    LangGraph est une extension de LangChain permettant de créer des agents cycliques (avec boucles de rétroaction), 
    ce qui est crucial pour les systèmes qui doivent s'auto-corriger ou raisonner en plusieurs étapes.
    """,

    "DataMining_KMeans.txt": """
    NOTION: K-Means Clustering. 
    C'est un algorithme d'apprentissage non supervisé utilisé pour le partitionnement de données. 
    L'objectif est de diviser N observations en K groupes (clusters) dans lesquels chaque observation appartient au groupe 
    avec la moyenne la plus proche (le centroïde). C'est une méthode de minimisation de l'inertie intra-classe.
    """,

    "DeepLearning_Transformers.txt": """
    NOTION: Transformers et Mécanismes d'Attention. 
    L'architecture Transformer repose sur le mécanisme de 'Self-Attention' qui permet au modèle de se concentrer sur 
    différentes parties d'une séquence d'entrée pour comprendre le contexte global. 
    Contrairement aux RNN, les Transformers traitent les données en parallèle, ce qui les rend extrêmement rapides et efficaces 
    pour le traitement du langage naturel (NLP) et les modèles de type GPT.
    """,

    "BigData_Spark_Hadoop.txt": """
    NOTION: Apache Spark et Hadoop HDFS. 
    Hadoop HDFS est un système de fichiers distribué conçu pour stocker de très gros volumes de données sur des clusters de serveurs. 
    Apache Spark est un moteur de traitement de données ultra-rapide qui travaille principalement en mémoire vive (RAM), 
    ce qui le rend jusqu'à 100 fois plus rapide que MapReduce pour certaines tâches de Big Data et de Machine Learning.
    """,
    
    "Pedagogie_SM2.txt": """
    NOTION: Algorithme SM-2 (Spaced Repetition). 
    L'algorithme de SuperMemo-2 est une méthode de répétition espacée. 
    Il calcule l'intervalle idéal pour réviser une information en fonction de sa difficulté perçue et de la performance passée de l'apprenant. 
    Le but est de présenter l'information juste avant que l'apprenant ne l'oublie pour renforcer la mémoire à long terme.
    """
}

def create_data():
    # Création du dossier s'il n'existe pas
    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"📁 Dossier '{folder}' créé.")
    else:
        print(f"📁 Dossier '{folder}' déjà présent.")

    # Création des fichiers
    for filename, content in ressources.items():
        filepath = os.path.join(folder, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"📄 Fichier généré : {filename}")

    print("\n✅ Initialisation des données terminée. Ton moteur RAG peut maintenant indexer ces fichiers.")

if __name__ == "__main__":
    create_data()
    
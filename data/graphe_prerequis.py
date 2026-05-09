import json
import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# Couleurs par module
COULEURS = {
    "MSA":            "#4b6cb7",
    "Data Mining":    "#e74c3c",
    "Deep Learning":  "#2ecc71",
    "Data Warehouse": "#f39c12",
    "Big Data":       "#9b59b6"
}

def build_graph():
    with open('data/prerequis.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    G = nx.DiGraph()
    node_colors = {}
    node_labels = {}

    for module, contenu in data['modules'].items():
        for notion in contenu['notions']:
            nid = notion['id']
            G.add_node(nid)
            node_colors[nid] = COULEURS[module]
            node_labels[nid] = notion['label']
            for pre in notion['prerequis']:
                G.add_edge(pre, nid)

    return G, node_colors, node_labels, data

def visualiser_graphe():
    G, node_colors, node_labels, data = build_graph()

    fig, axes = plt.subplots(1, 5, figsize=(26, 6))
    fig.patch.set_facecolor('#f8f9fa')
    fig.suptitle("🎓 Graphe de Pré-requis — Learning Path Adaptatif",
                 fontsize=16, fontweight='bold', y=1.02, color='#2c3e50')

    modules = list(data['modules'].keys())

    for idx, module in enumerate(modules):
        ax = axes[idx]
        ax.set_facecolor('#ffffff')
        ax.set_title(module, fontsize=12, fontweight='bold',
                     color='white', backgroundcolor=COULEURS[module],
                     pad=10)

        notions = data['modules'][module]['notions']
        sub_nodes = [n['id'] for n in notions]
        SG = G.subgraph(sub_nodes)

        # Layout vertical (du haut vers le bas selon niveau)
        pos = {}
        for n in notions:
            pos[n['id']] = (0.5, -n['niveau'])

        colors = [COULEURS[module] for _ in sub_nodes]

        nx.draw_networkx_nodes(SG, pos, ax=ax, node_color=colors,
                               node_size=2200, alpha=0.92)
        nx.draw_networkx_edges(SG, pos, ax=ax,
                               edge_color='#555555',
                               arrows=True,
                               arrowsize=20,
                               arrowstyle='-|>',
                               width=2,
                               connectionstyle='arc3,rad=0.1')

        labels = {n: node_labels[n] for n in sub_nodes}
        # Wrap long labels
        wrapped = {}
        for k, v in labels.items():
            words = v.split()
            if len(words) > 2:
                mid = len(words) // 2
                wrapped[k] = ' '.join(words[:mid]) + '\n' + ' '.join(words[mid:])
            else:
                wrapped[k] = v

        nx.draw_networkx_labels(SG, pos, labels=wrapped, ax=ax,
                                font_size=8, font_color='white',
                                font_weight='bold')

        ax.set_xlim(-0.2, 1.2)
        ax.set_ylim(-4.8, -0.2)
        ax.axis('off')

        # Légende niveaux
        for i, n in enumerate(notions):
            ax.text(1.15, -n['niveau'], f"N{n['niveau']}",
                    fontsize=8, color=COULEURS[module],
                    va='center', fontweight='bold')

    # Légende globale
    patches = [mpatches.Patch(color=COULEURS[m], label=m) for m in modules]
    fig.legend(handles=patches, loc='lower center', ncol=5,
               fontsize=10, frameon=True, bbox_to_anchor=(0.5, -0.05))

    plt.tight_layout()
    plt.savefig('data/graphe_prerequis.png', dpi=150,
                bbox_inches='tight', facecolor='#f8f9fa')
    print("✅ Graphe sauvegardé : data/graphe_prerequis.png")

if __name__ == '__main__':
    visualiser_graphe()

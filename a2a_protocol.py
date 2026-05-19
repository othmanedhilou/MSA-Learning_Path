# Protocole A2A inspiré FIPA-ACL — standardise les messages échangés entre agents
# FIPA-ACL définit des "performatives" : types de messages qui précisent l'intention
from datetime import datetime
import uuid

# Les 5 performatives utilisées dans notre SMA
REQUEST = "REQUEST"   # demande à un agent d'exécuter une action
INFORM  = "INFORM"    # transmission d'un résultat ou d'une information
QUERY   = "QUERY"     # demande d'information
CONFIRM = "CONFIRM"   # confirmation qu'une action a été réalisée
FAILURE = "FAILURE"   # signalement d'un échec


def create_a2a_msg(sender: str, receiver: str,
                   performative: str, content: dict,
                   conversation_id: str = None) -> dict:
    """Crée un message A2A standardisé avec horodatage et identifiant unique."""
    return {
        "msg_id":          str(uuid.uuid4())[:8],
        "timestamp":       datetime.now().strftime("%H:%M:%S"),
        "from":            sender,
        "to":              receiver,
        "performative":    performative,
        "content":         content,
        "conversation_id": conversation_id or "session-default"
    }


def format_timeline_text(communications: list) -> str:
    """Formate la liste de messages A2A en timeline ASCII pour le terminal."""
    emoji_map = {
        "REQUEST": "📤", "INFORM": "📥", "QUERY": "❓",
        "CONFIRM": "✅", "FAILURE": "❌"
    }
    lines = []
    for m in communications:
        emoji = emoji_map.get(m['performative'], "•")
        lines.append(
            f"{emoji} [{m['timestamp']}] {m['from']:<15} → {m['to']:<15} : {m['performative']}"
        )
    return "\n".join(lines)


def format_timeline_html(communications: list) -> str:
    """Formate la timeline en HTML coloré pour l'interface Streamlit.
    Chaque performative a sa propre couleur pour faciliter la lecture visuelle."""
    color_map = {
        "REQUEST": "#2563eb", "INFORM": "#15803d", "QUERY": "#d97706",
        "CONFIRM": "#7c3aed", "FAILURE": "#dc2626"
    }
    parts = []
    for m in communications:
        color = color_map.get(m['performative'], "#64748b")
        parts.append(
            f'<div style="background:#f1f5f9;border-left:4px solid {color};'
            f'padding:8px;margin:4px 0;border-radius:4px;font-family:Courier;font-size:0.85rem;">'
            f'<b style="color:{color};">[{m["timestamp"]}]</b> '
            f'<b>{m["from"]}</b> ➡️ <b>{m["to"]}</b> '
            f'<span style="color:{color};">[{m["performative"]}]</span>'
            f'</div>'
        )
    return "".join(parts)


if __name__ == "__main__":
    # Exemple d'une conversation complète entre agents
    msgs = [
        create_a2a_msg("Orchestrateur", "Diagnosticien", REQUEST,
                       {"action": "run_diagnostic", "module": "MSA"}),
        create_a2a_msg("Diagnosticien", "Orchestrateur", INFORM,
                       {"score": 55, "lacunes": ["CrewAI", "LangGraph"]}),
        create_a2a_msg("Orchestrateur", "Planificateur", REQUEST,
                       {"action": "build_parcours"}),
        create_a2a_msg("Planificateur", "Orchestrateur", INFORM,
                       {"nb_etapes": 4, "duree_h": 3.5}),
    ]
    print(format_timeline_text(msgs))

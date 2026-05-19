"""
Protocole A2A — inspiré FIPA-ACL (Foundation for Intelligent Physical Agents)
Standardise les messages échangés entre les agents du SMA.

Référence cours : Chapitre 4 (SMA & Protocole A2A) + Chapitre 1 MSA (questions.json).
Le protocole FIPA-ACL définit des "performatives" : INFORM, REQUEST, QUERY, etc.
"""
from datetime import datetime
import uuid

# ─────────────────────────────────────────────────────────────
# Performatives FIPA-ACL utilisées dans notre SMA
# ─────────────────────────────────────────────────────────────
REQUEST = "REQUEST"   # Demande à un agent d'exécuter une action
INFORM = "INFORM"     # Transmet un résultat / information
QUERY = "QUERY"       # Demande une information
CONFIRM = "CONFIRM"   # Confirme un fait
FAILURE = "FAILURE"   # Signale un échec


def create_a2a_msg(sender: str, receiver: str,
                   performative: str, content: dict,
                   conversation_id: str = None) -> dict:
    """
    Crée un message A2A standardisé (FIPA-ACL).

    Args:
        sender: nom de l'agent émetteur
        receiver: nom de l'agent destinataire
        performative: type FIPA-ACL (REQUEST, INFORM, ...)
        content: contenu sémantique du message (dict libre)
        conversation_id: identifiant de la conversation (pour grouper)

    Returns:
        Dict standardisé représentant le message.
    """
    return {
        "msg_id": str(uuid.uuid4())[:8],
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "from": sender,
        "to": receiver,
        "performative": performative,
        "content": content,
        "conversation_id": conversation_id or "session-default"
    }


def format_timeline_text(communications: list) -> str:
    """Formate la liste de messages A2A en timeline ASCII (pour CLI/debug)."""
    lines = []
    emoji_map = {
        "REQUEST": "📤", "INFORM": "📥", "QUERY": "❓",
        "CONFIRM": "✅", "FAILURE": "❌"
    }
    for m in communications:
        emoji = emoji_map.get(m['performative'], "•")
        lines.append(
            f"{emoji} [{m['timestamp']}] {m['from']:<15} → {m['to']:<15} : {m['performative']}"
        )
    return "\n".join(lines)


def format_timeline_html(communications: list) -> str:
    """Formate la timeline en HTML (pour Streamlit)."""
    html_parts = []
    color_map = {
        "REQUEST": "#2563eb", "INFORM": "#15803d", "QUERY": "#d97706",
        "CONFIRM": "#7c3aed", "FAILURE": "#dc2626"
    }
    for m in communications:
        color = color_map.get(m['performative'], "#64748b")
        html_parts.append(
            f'<div style="background:#f1f5f9;border-left:4px solid {color};'
            f'padding:8px;margin:4px 0;border-radius:4px;font-family:Courier;font-size:0.85rem;">'
            f'<b style="color:{color};">[{m["timestamp"]}]</b> '
            f'<b>{m["from"]}</b> ➡️ <b>{m["to"]}</b> '
            f'<span style="color:{color};">[{m["performative"]}]</span>'
            f'</div>'
        )
    return "".join(html_parts)


if __name__ == "__main__":
    # Test rapide
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

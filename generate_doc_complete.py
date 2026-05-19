"""
Génère le PDF exhaustif (80-100+ pages) qui explique TOUT du projet :
- Architecture détaillée avec diagrammes
- Code expliqué ligne par ligne
- Justification de chaque choix
- Conformité au cours chapitre par chapitre
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    KeepTogether
)
import os

# ===== COULEURS =====
PRIMARY = HexColor("#1a3a6e")
SECONDARY = HexColor("#2c5aa0")
ACCENT = HexColor("#d97706")
SUCCESS = HexColor("#15803d")
DANGER = HexColor("#b91c1c")
LIGHT_BG = HexColor("#f1f5f9")
BORDER = HexColor("#cbd5e1")
CODE_BG = HexColor("#0f172a")
CODE_TEXT = HexColor("#e2e8f0")
COMMENT_GREEN = HexColor("#22c55e")
GRAY = HexColor("#64748b")

# ===== STYLES =====
styles = getSampleStyleSheet()

H1 = ParagraphStyle('H1', parent=styles['Heading1'],
    fontName='Helvetica-Bold', fontSize=24, textColor=PRIMARY,
    spaceAfter=12, spaceBefore=18, leading=28)

H2 = ParagraphStyle('H2', parent=styles['Heading2'],
    fontName='Helvetica-Bold', fontSize=17, textColor=SECONDARY,
    spaceAfter=8, spaceBefore=14, leading=21)

H3 = ParagraphStyle('H3', parent=styles['Heading3'],
    fontName='Helvetica-Bold', fontSize=13, textColor=PRIMARY,
    spaceAfter=6, spaceBefore=10, leading=16)

H4 = ParagraphStyle('H4', parent=styles['Heading4'],
    fontName='Helvetica-Bold', fontSize=11, textColor=ACCENT,
    spaceAfter=4, spaceBefore=6, leading=14)

BODY = ParagraphStyle('Body', parent=styles['Normal'],
    fontName='Helvetica', fontSize=10, leading=14,
    alignment=TA_JUSTIFY, spaceAfter=6, textColor=black)

CODE = ParagraphStyle('Code', parent=styles['Normal'],
    fontName='Courier', fontSize=8.5, leading=11,
    backColor=CODE_BG, textColor=CODE_TEXT,
    leftIndent=6, rightIndent=6, spaceAfter=6, spaceBefore=4,
    borderPadding=5)

EXPL = ParagraphStyle('Explanation', parent=BODY,
    fontSize=10, leading=14, leftIndent=10, rightIndent=10,
    spaceAfter=8, backColor=HexColor("#fefce8"),
    borderPadding=6, textColor=black)

story = []

def add(p): story.append(p)
def space(h=6): story.append(Spacer(1, h))
def pagebreak(): story.append(PageBreak())
def h1(t): add(Paragraph(t, H1))
def h2(t): add(Paragraph(t, H2))
def h3(t): add(Paragraph(t, H3))
def h4(t): add(Paragraph(t, H4))
def p(t): add(Paragraph(t, BODY))

def code_block(text):
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    text = text.replace('\n', '<br/>').replace(' ', '&nbsp;')
    add(Paragraph(text, CODE))
    space(4)

def explain(text):
    """Boîte d'explication jaune pâle."""
    add(Paragraph(f"💡 <b>Explication :</b> {text}", EXPL))

def callout(title, text, color=PRIMARY, bg=LIGHT_BG):
    inner = ParagraphStyle('co_in', parent=BODY,
        fontSize=10, leading=14, textColor=black)
    title_s = ParagraphStyle('co_t', parent=BODY,
        fontSize=11, textColor=color, fontName='Helvetica-Bold', spaceAfter=4)
    data = [[Paragraph(title, title_s)],
            [Paragraph(text, inner)]]
    t = Table(data, colWidths=[16*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), bg),
        ('LINEBEFORE', (0,0), (0,-1), 3, color),
        ('PADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    add(t)
    space(8)

def bullet(items, color=PRIMARY):
    for it in items:
        bs = ParagraphStyle('bul', parent=BODY,
            leftIndent=20, bulletIndent=8, spaceAfter=3)
        add(Paragraph(f"<font color='{color.hexval()}'>▸</font> {it}", bs))
    space(4)

def table_grid(headers, rows, col_widths=None):
    data = [headers] + rows
    if col_widths is None:
        col_widths = [17*cm/len(headers)] * len(headers)
    cell_st = ParagraphStyle('cell', fontSize=9, leading=11)
    head_st = ParagraphStyle('head', fontSize=9, leading=11,
        textColor=white, fontName='Helvetica-Bold')
    new_data = []
    for i, row in enumerate(data):
        new_row = []
        for cell in row:
            sty = head_st if i == 0 else cell_st
            new_row.append(Paragraph(str(cell), sty))
        new_data.append(new_row)
    t = Table(new_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.4, BORDER),
        ('PADDING', (0,0), (-1,-1), 5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [white, LIGHT_BG]),
    ]))
    add(t)
    space(8)

def section_header(num, title, part=None):
    if part:
        add(Paragraph(part, ParagraphStyle('part', fontSize=10,
            textColor=ACCENT, fontName='Helvetica-Bold', spaceAfter=4)))
    add(Paragraph(f"{num}. {title}", H1))
    line = Table([['']], colWidths=[17*cm], rowHeights=[2])
    line.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), ACCENT)]))
    add(line)
    space(8)

def big_separator():
    sep = Table([['']], colWidths=[17*cm], rowHeights=[3])
    sep.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), PRIMARY)]))
    add(sep)
    space(10)


# ════════════════════════════════════════════════════════════════
# PAGE DE TITRE
# ════════════════════════════════════════════════════════════════
def page_garde():
    add(Spacer(1, 3.5*cm))
    add(Paragraph("DOCUMENTATION TECHNIQUE EXHAUSTIVE",
        ParagraphStyle('s1', fontSize=14, alignment=TA_CENTER,
            textColor=ACCENT, fontName='Helvetica-Bold')))
    space(10)
    add(Paragraph("PROJET 4 — SMA Agentic AI",
        ParagraphStyle('s2', fontSize=18, alignment=TA_CENTER,
            textColor=SECONDARY, fontName='Helvetica-Bold')))
    space(20)
    add(Paragraph("Learning Path Architect",
        ParagraphStyle('s3', fontSize=36, alignment=TA_CENTER,
            textColor=PRIMARY, fontName='Helvetica-Bold', leading=42)))
    space(8)
    add(Paragraph("Architecte de Parcours d'Apprentissage Adaptatif",
        ParagraphStyle('s4', fontSize=16, alignment=TA_CENTER,
            textColor=GRAY, fontName='Helvetica-Oblique', leading=22)))
    space(30)
    add(Paragraph(
        "Architecture détaillée · Code expliqué ligne par ligne<br/>"
        "Diagrammes complets · Justification de chaque choix<br/>"
        "Conformité au cours chapitre par chapitre",
        ParagraphStyle('s5', fontSize=12, alignment=TA_CENTER,
            textColor=black, leading=18)))
    add(Spacer(1, 3.5*cm))

    info = [
        ['Module', '4AISDR — SMA Agentic AI'],
        ['Projet', 'N°4 — Learning Paths Adaptatifs'],
        ['Encadrants', 'Pr. H. CHAABI & Pr. N. IDRISSI Zouggari'],
        ['Équipe', 'Othmane Dhilou · Dodo · Mohamed Yassir'],
        ['Présentation', 'Semaine du 18 mai 2026'],
        ['Document', 'Référence technique complète'],
    ]
    t = Table(info, colWidths=[5*cm, 11*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), PRIMARY),
        ('TEXTCOLOR', (0,0), (0,-1), white),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER),
        ('BACKGROUND', (1,0), (1,-1), LIGHT_BG),
    ]))
    add(t)
    pagebreak()


# ════════════════════════════════════════════════════════════════
# TABLE DES MATIÈRES
# ════════════════════════════════════════════════════════════════
def toc():
    h1("Table des matières")
    space(4)
    entries = [
        ("PARTIE I — VUE D'ENSEMBLE", True, PRIMARY),
        ("1. Résumé exécutif", False, black),
        ("2. Contexte et problématique", False, black),
        ("3. Vue d'ensemble de l'architecture", False, black),
        ("PARTIE II — FONDAMENTAUX (cours)", True, PRIMARY),
        ("4. Prompt Engineering : CoT et ReAct", False, black),
        ("5. RAG vectoriel en profondeur", False, black),
        ("6. Agentic AI : Body / Mind / Memory", False, black),
        ("7. LangGraph : State / Nodes / Edges", False, black),
        ("8. MCP : Model Context Protocol", False, black),
        ("9. SMA et protocole A2A (FIPA-ACL)", False, black),
        ("PARTIE III — CODE EXPLIQUÉ LIGNE PAR LIGNE", True, PRIMARY),
        ("10. a2a_protocol.py", False, black),
        ("11. mind_layer.py", False, black),
        ("12. rag_engine.py", False, black),
        ("13. learning_tools_server.py", False, black),
        ("14. diagnostician.py (modifications O5)", False, black),
        ("15. orchestrator.py — le cœur du système", False, black),
        ("16. app.py — interface Streamlit", False, black),
        ("17. tests/test_orchestrator.py", False, black),
        ("PARTIE IV — JUSTIFICATIONS", True, PRIMARY),
        ("18. Pourquoi LangGraph et pas LangChain", False, black),
        ("19. Pourquoi Chroma et pas FAISS", False, black),
        ("20. Pourquoi MCP en plus de @tool", False, black),
        ("21. Pourquoi SM-2 et pas règles simples", False, black),
        ("22. Pourquoi LLM hybride avec fallback", False, black),
        ("23. Pourquoi FIPA-ACL", False, black),
        ("PARTIE V — DIAGRAMMES", True, PRIMARY),
        ("24. Diagramme d'architecture globale", False, black),
        ("25. Diagramme de flux de données", False, black),
        ("26. Diagrammes de séquence (3 profils)", False, black),
        ("27. Diagramme d'états (LangGraph)", False, black),
        ("28. Pipeline RAG détaillé", False, black),
        ("29. Communication MCP", False, black),
        ("PARTIE VI — VALIDATION", True, PRIMARY),
        ("30. Tests et résultats", False, black),
        ("31. Conformité au cours (matrice)", False, black),
        ("PARTIE VII — DÉMO ET ANTICIPATION JURY", True, PRIMARY),
        ("32. Script de démonstration", False, black),
        ("33. Questions probables et réponses", False, black),
        ("PARTIE VIII — ANNEXES", True, PRIMARY),
        ("34. Inventaire des fichiers", False, black),
        ("35. Schémas JSON", False, black),
        ("36. Glossaire", False, black),
    ]
    for text, bold, color in entries:
        st = ParagraphStyle('toc_e', parent=BODY,
            textColor=color, leftIndent=0 if bold else 16,
            fontName='Helvetica-Bold' if bold else 'Helvetica',
            fontSize=11 if bold else 10,
            spaceAfter=3 if bold else 2,
            leading=15)
        add(Paragraph(text, st))
    pagebreak()


page_garde()
toc()

# Stockage du nom du fichier de sortie
_OUTPUT_PATH = r"c:\Users\Othma\OneDrive\سطح المكتب\multi_ag\MSA-Learning_Path\Documentation_Complete.pdf"

# Exposer les helpers comme attributs de module pour les parties
import sys as _sys
_this = _sys.modules[__name__]

# Helpers utilisés par les parties externes
_helpers = {
    'cm': cm, 'TA_CENTER': TA_CENTER, 'Paragraph': Paragraph,
    'ParagraphStyle': ParagraphStyle, 'add': add, 'space': space,
    'pagebreak': pagebreak, 'h1': h1, 'h2': h2, 'h3': h3, 'h4': h4, 'p': p,
    'code_block': code_block, 'explain': explain, 'callout': callout,
    'bullet': bullet, 'table_grid': table_grid, 'section_header': section_header,
    'PRIMARY': PRIMARY, 'SECONDARY': SECONDARY, 'ACCENT': ACCENT,
    'SUCCESS': SUCCESS, 'DANGER': DANGER, 'LIGHT_BG': LIGHT_BG,
}
for k, v in _helpers.items():
    setattr(_this, k, v)

# Importer et exécuter les parties
_BASE = os.path.dirname(os.path.abspath(_OUTPUT_PATH))
_sys.path.insert(0, _BASE)

from doc_parts import part1_overview, part2_fundamentals
from doc_parts import part3_code_a, part3_code_b, part3_code_c
from doc_parts import part4_to_8

part1_overview.build(_this)
part2_fundamentals.build(_this)
part3_code_a.build(_this)
part3_code_b.build(_this)
part3_code_c.build(_this)
part4_to_8.build(_this)

# Helper export
def build_pdf():
    def hf(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(HexColor("#64748b"))
        canvas.drawString(2*cm, 1*cm, "Projet 4 - SMA Agentic AI · Documentation complète")
        canvas.drawRightString(19*cm, 1*cm, f"Page {doc.page}")
        if doc.page > 1:
            canvas.setStrokeColor(BORDER)
            canvas.setLineWidth(0.5)
            canvas.line(2*cm, 27.5*cm, 19*cm, 27.5*cm)
            canvas.setFont('Helvetica-Oblique', 8)
            canvas.drawString(2*cm, 27.7*cm, "Learning Path Architect · Documentation technique exhaustive")
        canvas.restoreState()

    doc = SimpleDocTemplate(_OUTPUT_PATH, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2.5*cm, bottomMargin=2*cm,
        title="Documentation Complete Projet 4")
    doc.build(story, onFirstPage=hf, onLaterPages=hf)
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    print(f"OK : {_OUTPUT_PATH}")
    print(f"Size : {os.path.getsize(_OUTPUT_PATH) / 1024:.1f} KB")

#!/usr/bin/env python3
"""Generate OrgBrain README diagram (light + dark) as diagram-design HTML files."""
import pathlib
import sys
from string import Template

OUT = pathlib.Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)

SANS = "'Geist', -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "'Geist Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

SKINS = {
    "light": dict(paper="#ffffff", node="#ffffff", ink="#14202b", muted="#4a5568", soft="#8a8a8a",
                  accent="#c8501a", tint="#f4ded0", link="#2e5aa8",
                  inkrgb="20,32,43", mutedrgb="74,85,104", accentrgb="200,80,26"),
    "dark": dict(paper="#2d3142", node="#393e53", ink="#f5f5f5", muted="#bfc0c0", soft="#8e98ac",
                 accent="#e06a35", tint="rgba(224,106,53,0.12)", link="#6a95d8",
                 inkrgb="245,245,245", mutedrgb="191,192,192", accentrgb="224,106,53"),
}

KIND = {
    "focal":    dict(fill="$tint", stroke="$accent", tag="$accent", dash=""),
    "backend":  dict(fill="$node", stroke="$ink", tag="$ink", dash=""),
    "store":    dict(fill="rgba($inkrgb,0.05)", stroke="$muted", tag="$muted", dash=""),
    "external": dict(fill="rgba($inkrgb,0.03)", stroke="rgba($inkrgb,0.30)", tag="$soft", dash=""),
    "input":    dict(fill="rgba($mutedrgb,0.10)", stroke="$soft", tag="$soft", dash=""),
    "optional": dict(fill="rgba($inkrgb,0.02)", stroke="rgba($inkrgb,0.35)", tag="$soft",
                     dash=' stroke-dasharray="4,3"'),
}


def tag_w(text):
    return max(20, ((len(text) * 5 + 10 + 3) // 4) * 4)


def node(x, y, w, h, kind, tag, name, sub):
    k = KIND[kind]
    cx = x + w // 2
    tw = tag_w(tag)
    out = [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="$paper"/>',
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{k["fill"]}" '
        f'stroke="{k["stroke"]}" stroke-width="1"{k["dash"]}/>',
        f'<rect x="{x + 8}" y="{y + 6}" width="{tw}" height="12" rx="2" fill="none" '
        f'stroke="{k["tag"]}" stroke-opacity="0.45" stroke-width="0.8"/>',
        f'<text x="{x + 8 + tw // 2}" y="{y + 15}" fill="{k["tag"]}" font-size="7" font-family="{MONO}" '
        f'text-anchor="middle" letter-spacing="0.08em">{tag}</text>',
        f'<text x="{cx}" y="{y + 36}" fill="$ink" font-size="12" font-weight="600" font-family="{SANS}" '
        f'text-anchor="middle">{name}</text>',
    ]
    if sub:
        out.append(f'<text x="{cx}" y="{y + 52}" fill="$muted" font-size="9" font-family="{MONO}" '
                   f'text-anchor="middle">{sub}</text>')
    return out


def label(x, y, w, text, color="$soft"):
    return [
        f'<rect x="{x}" y="{y}" width="{w}" height="12" rx="2" fill="$paper"/>',
        f'<text x="{x + w // 2}" y="{y + 9}" fill="{color}" font-size="8" font-family="{MONO}" '
        f'text-anchor="middle" letter-spacing="0.08em">{text}</text>',
    ]


def zone(x, y, w, h, lx, lw, text):
    return [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="rgba($inkrgb,0.02)" '
        f'stroke="rgba($inkrgb,0.12)" stroke-width="0.8"/>',
        f'<rect x="{lx}" y="{y + 4}" width="{lw}" height="12" rx="2" fill="$paper"/>',
        f'<text x="{lx + lw // 2}" y="{y + 13}" fill="rgba($inkrgb,0.45)" font-size="7" font-family="{MONO}" '
        f'text-anchor="middle" letter-spacing="0.14em">{text}</text>',
    ]


def path(d, color, width, marker, dashed=False):
    dash = ' stroke-dasharray="4,3"' if dashed else ""
    return [f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"{dash} '
            f'marker-end="url(#{marker})"/>']


def legend_item(x, y, kind, text):
    if kind in KIND:
        k = KIND[kind]
        swatch = (f'<rect x="{x}" y="{y}" width="16" height="12" rx="2" fill="{k["fill"]}" '
                  f'stroke="{k["stroke"]}" stroke-width="1"{k["dash"]}/>')
    elif kind == "gate":
        swatch = (f'<polygon points="{x + 8},{y - 1} {x + 15},{y + 6} {x + 8},{y + 13} {x + 1},{y + 6}" '
                  f'fill="$tint" stroke="$accent" stroke-width="1"/>')
    else:
        stroke, marker, extra = {
            "accent": ("$accent", "arrow-accent", ' stroke-width="1.4"'),
            "link": ("$link", "arrow-link", ' stroke-width="1.2"'),
            "dashed": ("$muted", "arrow", ' stroke-width="1" stroke-dasharray="4,3"'),
        }[kind]
        swatch = (f'<line x1="{x}" y1="{y + 6}" x2="{x + 24}" y2="{y + 6}" stroke="{stroke}"{extra} '
                  f'marker-end="url(#{marker})"/>')
    return [swatch, f'<text x="{x + 32}" y="{y + 10}" fill="$muted" font-size="9" font-family="{SANS}">{text}</text>']


def legend(y_line, items, step):
    out = [
        f'<line x1="32" y1="{y_line}" x2="960" y2="{y_line}" stroke="rgba($inkrgb,0.12)" stroke-width="0.8"/>',
        f'<text x="32" y="{y_line + 20}" fill="$muted" font-size="8" font-family="{MONO}" '
        f'letter-spacing="0.18em">LEGEND</text>',
    ]
    x = 32
    for k, t in items:
        out += legend_item(x, y_line + 32, k, t)
        x += ((32 + int(len(t) * 5.2) + 20 + 3) // 4) * 4
    return out


DEFS = [
    "<defs>",
    '<marker id="arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">'
    '<polygon points="0 0, 8 3, 0 6" fill="$muted"/></marker>',
    '<marker id="arrow-accent" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">'
    '<polygon points="0 0, 8 3, 0 6" fill="$accent"/></marker>',
    '<marker id="arrow-link" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">'
    '<polygon points="0 0, 8 3, 0 6" fill="$link"/></marker>',
    "</defs>",
]


def architecture():
    W, H, TOP = 992, 432, 40
    s = [f'<rect width="{W}" height="{H}" fill="$paper"/>']
    s += zone(16, 56, 752, 296, 28, 88, "YOUR MACHINE")
    s += zone(784, 56, 192, 296, 844, 72, "EXTERNAL")
    s += path("M 160,128 H 208", "$muted", "1.2", "arrow")
    s += path("M 352,128 H 400", "$muted", "1.2", "arrow")
    s += path("M 560,128 H 608", "$muted", "1.2", "arrow")
    s += path("M 752,128 H 800", "$link", "1.2", "arrow-link")
    s += path("M 480,160 V 256", "$muted", "1.2", "arrow")
    s += path("M 680,160 V 256", "$muted", "1.2", "arrow")
    s += path("M 800,288 H 752", "$link", "1.2", "arrow-link")
    s += path("M 160,288 H 372 Q 380,288 380,280 V 160 Q 380,152 388,152 H 400", "$muted", "1.2", "arrow")
    s += label(168, 108, 32, "ASK")
    s += label(360, 108, 32, "HTTP")
    s += label(562, 108, 44, "SPAWNS")
    s += label(756, 108, 40, "CALLS", "$link")
    s += label(488, 200, 88, "GRAPH · VECTORS")
    s += label(688, 200, 40, "READS")
    s += label(756, 268, 40, "CLONE", "$link")
    s += label(244, 268, 32, "HTTP")
    s += node(32, 96, 128, 64, "input", "YOU", "You", "browser")
    s += node(208, 96, 144, 64, "backend", "UI", "React UI", "Vite · :5173")
    s += node(400, 96, 160, 64, "focal", "CORE", "FastAPI process", "API · worker · SSE")
    s += node(608, 96, 144, 64, "backend", "LLM", "claude -p", "one process per call")
    s += node(800, 96, 160, 64, "external", "MCP", "Claude &amp; MCP", "Anthropic · Jira · Slack")
    s += node(32, 256, 128, 64, "input", "CLI", "orgbrain CLI", "thin client")
    s += node(400, 256, 160, 64, "store", "DB", "Postgres 16", "pgvector · graph")
    s += node(608, 256, 144, 64, "store", "FILES", "Cloned repos", "file:line source")
    s += node(800, 256, 160, 64, "external", "GIT", "Git hosts", "GitHub · remotes")
    s += legend(372, [("focal", "One async process"), ("backend", "Component"), ("store", "Local data"),
                      ("external", "External service"), ("input", "Entry point"), ("link", "Network call")], 120)
    return W, H, TOP, s


FONTS = ("https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1"
         "&family=Geist:wght@400;500;600&family=Geist+Mono:wght@400;500;600&display=swap")

CSS = " ".join([
    "*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }",
    "body { font-family: 'Geist', system-ui, sans-serif; background: $paper; color: $ink;",
    "min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 3rem 2rem; }",
    ".frame { max-width: 1040px; width: 100%; }",
    ".eyebrow { font-family: 'Geist Mono', ui-monospace, monospace; font-size: 0.66rem; font-weight: 500;",
    "letter-spacing: 0.18em; text-transform: uppercase; color: $muted; margin-bottom: 0.5rem; }",
    "h1 { font-family: 'Instrument Serif', serif; font-size: 2rem; font-weight: 400; letter-spacing: -0.02em;",
    "line-height: 1.15; color: $ink; margin-bottom: 1.5rem; }",
    "svg { width: 100%; min-width: 900px; display: block; }",
])


def page(slug, eyebrow, title, desc, W, H, TOP, body):
    lines = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="UTF-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
        f"<title>{title}</title>",
        f'<link href="{FONTS}" rel="stylesheet">',
        f"<style>{CSS}</style>",
        "</head>",
        "<body>",
        '<div class="frame">',
        f'<p class="eyebrow">{eyebrow}</p>',
        f"<h1>{title}</h1>",
        f'<svg viewBox="0 {TOP} {W} {H - TOP}" xmlns="http://www.w3.org/2000/svg" role="img" '
        f'aria-labelledby="{slug}-title {slug}-desc">',
        f'<title id="{slug}-title">{title}</title>',
        f'<desc id="{slug}-desc">{desc}</desc>',
        *DEFS,
        *body,
        "</svg>",
        "</div>",
        "</body>",
        "</html>",
        "",
    ]
    return "\n".join(lines)


DIAGRAMS = {
    "orgbrain-architecture": (architecture, "Architecture · OrgBrain", "How OrgBrain fits together",
                              "Architecture diagram showing the browser UI and the orgbrain CLI calling one FastAPI "
                              "process, which stores the extracted graph and vectors in Postgres with pgvector and "
                              "spawns one claude -p subprocess per model call. The subprocess reads the cloned repos "
                              "and reaches Anthropic and MCP servers. Repositories are cloned from git hosts."),
}

for slug, (fn, eyebrow, title, desc) in DIAGRAMS.items():
    W, H, TOP, body = fn()
    for skin, tokens in SKINS.items():
        sslug = slug if skin == "light" else f"{slug}-dark"
        html = Template(page(sslug, eyebrow, title, desc, W, H, TOP, body)).substitute(tokens)
        (OUT / f"{sslug}.html").write_text(html)
        print("wrote", OUT / f"{sslug}.html")

# -*- coding: utf-8 -*-
"""Rebuild self-contained artifact.html from the dota-leaderboard repo."""
import base64
import io
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "artifact-build.html")

html = io.open(os.path.join(REPO, "index.html"), encoding="utf-8").read()

# 1. fonts -> data URIs
def font_repl(m):
    p = os.path.join(REPO, m.group(1).replace("/", os.sep))
    b64 = base64.b64encode(open(p, "rb").read()).decode()
    return "url(data:font/woff2;base64," + b64 + ")"

html, n_fonts = re.subn(r"url\((fonts/[\w-]+\.woff2)\)", font_repl, html)

# 2. inline data.js
data = io.open(os.path.join(REPO, "data.js"), encoding="utf-8").read().strip()
html = html.replace('<script src="data.js"></script>', "<script>" + data + "</script>", 1)

# 3. flags -> window.FLAGS map + flagCell rewrite
flags_dir = os.path.join(REPO, "flags")
entries = []
for fn in sorted(os.listdir(flags_dir)):
    if fn.endswith(".png"):
        b64 = base64.b64encode(open(os.path.join(flags_dir, fn), "rb").read()).decode()
        entries.append('"%s":"data:image/png;base64,%s"' % (fn[:-4], b64))
flags_js = "<script>window.FLAGS={" + ",".join(entries) + "};</script>"
html = html.replace("</head>", flags_js + "\n</head>", 1)

old_fc = """  var flagCell = function (c) {
    if (!c) return '<span class="noflag"></span>';
    return '<img class="flag" loading="lazy" src="flags/' + c + '.png" alt="" onerror="this.outerHTML=\\'<span class=noflag></span>\\'">';
  };"""
new_fc = """  var flagCell = function (c) {
    if (!c || !window.FLAGS || !window.FLAGS[c]) return '<span class="noflag"></span>';
    return '<img class="flag" src="' + window.FLAGS[c] + '" alt="">';
  };"""
assert old_fc in html, "flagCell source drifted"
html = html.replace(old_fc, new_fc, 1)

# 4. unofficial note appended to legend popup strings
ru_note = " Неофициальный фан-сайт, не связан с Valve."
en_note = " Unofficial fan site, not affiliated with Valve."
html, n_ru = re.subn(r'(legend: "База[^"]+)"', lambda m: m.group(1) + ru_note + '"', html)
html, n_en = re.subn(r'(legend: "Baseline[^"]+)"', lambda m: m.group(1) + en_note + '"', html)

# 5. dark background enforcement for the artifact wrapper
html = html.replace(
    "<style>",
    "<style>\n  html, body { background: #0c0f14 !important; }\n  :root { color-scheme: dark; }",
    1,
)

# 6. strip document wrapper tags (artifact host supplies its own), keep meta/title
for tag in ["<!DOCTYPE html>", '<html lang="ru">', "</html>", "<head>", "</head>", "<body>", "</body>"]:
    html = html.replace(tag, "", 1)

io.open(OUT, "w", encoding="utf-8", newline="\n").write(html)
print("fonts inlined:", n_fonts, "| flags:", len(entries), "| legend ru/en:", n_ru, n_en,
      "| size:", os.path.getsize(OUT))

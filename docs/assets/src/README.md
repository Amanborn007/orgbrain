# Diagram sources

The README diagram is generated, not hand-edited. `generate.py` holds the geometry and writes a light and a dark HTML page. `export_svg.py` turns those pages into the committed `.svg` files one folder up, and the README embeds those.

```sh
python3 docs/assets/src/generate.py docs/assets/src
python3 docs/assets/src/export_svg.py docs/assets/src/*.html
python3 docs/assets/src/export_png.py docs/assets/src/*.html   # optional PNGs, needs Playwright: pip install playwright && playwright install chromium
```

Edit `generate.py`, run the commands, and commit the HTML and SVG together so they stay in step.

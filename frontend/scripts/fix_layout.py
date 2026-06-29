# -*- coding: utf-8 -*-
import re

# Fix Layout - remove lobby link
layout_path = "../src/components/Layout.tsx"
with open(layout_path, "r", encoding="utf-8") as f:
    content = f.read()

# Remove lobby link from top nav
content = re.sub(
    r'\s*<Link to="/create-lobby-competition"[^>]*>[^<]*</Link>\s*',
    "",
    content
)

with open(layout_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Layout fixed")

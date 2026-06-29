# -*- coding: utf-8 -*-
"""Reorder Dashboard - put lobby first, then welcome, then clubs"""

import codecs

content = codecs.open('../src/pages/Dashboard.tsx', 'r', 'utf-8').read()

# Find and extract the lobby section
lobby_start = content.find('      <div className="card-nailong p-6 bg-gradient-to-r from-nailong-orange/5 to-nailong-yellow/5">')
lobby_end_marker = '      <div className="card-nailong p-6">\n        <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">\n          🏟️ 我的俱乐部'
lobby_end = content.find(lobby_end_marker)

if lobby_start == -1 or lobby_end == -1:
    print("Could not find sections")
    exit(1)

lobby_section = content[lobby_start:lobby_end]

# Find welcome section
welcome_start = content.find('      <div className="bg-gradient-to-r from-nailong-orange/10')
welcome_end = lobby_start
welcome_section = content[welcome_start:welcome_end]

# Reorder: remove welcome, put lobby first, then welcome, then rest
rest = content[lobby_end:]

new_content = content[:welcome_start] + lobby_section + welcome_section + rest

codecs.open('../src/pages/Dashboard.tsx', 'w', 'utf-8').write(new_content)
print("Dashboard reordered: Lobby first, then welcome, then clubs")

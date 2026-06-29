# -*- coding: utf-8 -*-
with open("../src/pages/Dashboard.tsx", "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if "不知道怎么做？点击右上角" in line:
        line = '            点击右上角{" "}\n'
    if "「AI 助手」" in line and "问奶龙" in line:
        line = '            <span className="text-nailong-orange font-bold">「AI 助手」</span>，奶龙帮你：\n'
    if "试试说：「帮我创建一个八人转比赛」" in line:
        line = '            创建比赛 · 预测胜负 · 查排名 · 录比分\n'
    if "「我想加入俱乐部」「记录比分 21:15」" in line:
        line = '            例如：「帮我创建一个八人转」「预测张三和李四谁赢」「记录一下比分」\n'
    new_lines.append(line)

with open("../src/pages/Dashboard.tsx", "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("Prompt updated")

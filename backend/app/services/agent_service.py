"""AI Agent 服务：Function Calling + 意图预判辅助

架构（混合方案——真正的 Agent 技术）：
1. _preload_intent() 用正则预判用户意图，生成"线索"注入系统提示词
2. LLM 收到线索 + TOOLS，自主决策调用哪个工具（Function Calling 核心）
3. 代码层只做两件事：给线索 + 执行 LLM 决定的工具调用
"""

import json
import logging
import os
import re
from datetime import datetime
from typing import AsyncGenerator

from anthropic import AsyncAnthropic
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.models.player import ClubMember, Player
from app.models.club import Club
from app.models.competition import Competition
from app.models.user import User
from app.services import club_service, competition_service, leaderboard_service
from app.services.player_stats_service import get_partner_stats, suggest_balanced_teams
from app.services.memory_service import save_message, build_context, generate_summary

logger = logging.getLogger("badminton")

SYSTEM_PROMPT = """你是"奶龙"，用户的专属羽毛球管家和球场伙伴，性格活泼爱调侃。

【核心规则 - 极其重要】
1. 你的所有知识基于下面的「当前用户信息」和对话历史。不要重复查询已知数据。
2. 每次回复必须先说话再调工具！禁止无文字直接调用工具。
3. 信息已在上下文中时绝不要重复查询。
4. 用户说"单挑/对决/切磋/打一场/打一局/PK/开打/对战/比赛/比一场/来一局" = 创建比赛。
5. 创建比赛参数齐备就直接建，不要反复确认。
6. 注意看「意图预判」提示——那是最可能的操作方向。
7. 用户提到"自主报名/开放报名/公开报名/大厅报名"时，应优先用开放报名模式创建比赛。

【多步操作规则 - 新功能】
如果用户的一句话包含多个操作需求，你可以连续调用多个工具来完成：
· "创建比赛并记录21:0的比分" → 先 create_competition，再 record_latest_score 或 record_competition_score
· "创建张三李四的比赛，比分21:15" → 先创建比赛，再 record_latest_score
· 用户只说「记比分/计分 21:15」且没给比赛ID → 直接调用 record_latest_score（自动找最近可计分比赛，必要时自动开赛）
· 创建比赛后会返回比赛详情，包含对阵信息，你可以根据用户指定的比分直接录入
· 每次调用工具后，我会把结果返回给你，你可以决定是否需要继续调用下一个工具
· 多步操作完成后，给用户一个总结性的回复

【说话风格】
· 像球友聊天：亲切、活泼、带点调侃
· 简短有力，2-4 句为宜
· 适当使用 emoji（🏸、👀、💪 等）
· 多步操作完成后可以说"搞定！"、"一气呵成！"之类的话

【格式规则 - 必须严格遵守】
- 禁止使用 markdown 格式（**、*、` 等）
- 列表项用「·」开头"""

# Function Calling 工具集
TOOLS = [
    {
        "name": "create_competition",
        "description": "创建比赛。支持两种模式：1) 俱乐部模式：需要club_id，适合俱乐部内部比赛；2) 大厅模式：club_id设为null，任何人都可以报名，无需加入俱乐部。开放报名模式(open_signup=true)下player_ids可为空，创建者自动占1个名额。",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "比赛名称"},
                "club_id": {"type": ["integer", "null"], "description": "俱乐部ID。设为null表示大厅/公开比赛，任何人可参加"},
                "format": {"type": "string", "description": "singles_rotation/doubles_rotation/eight_player_rotation/four_player_rotation/knockout"},
                "courts": {"type": "integer", "description": "场地数(默认1)"},
                "player_ids": {"type": "array", "items": {"type": "integer"}, "description": "参赛球员ID列表（普通模式必填，开放报名可为空）"},
                "scheduled_at": {"type": "string", "description": "比赛时间(ISO格式，如2026-07-15T14:00:00)，可选"},
                "open_signup": {"type": "boolean", "description": "是否开放自主报名（大厅模式自动为true）"},
                "is_public": {"type": "boolean", "description": "是否公开到比赛大厅（大厅模式自动为true）"},
                "max_players": {"type": "integer", "description": "报名人数上限（建议填写）"},
                "signup_deadline": {"type": "string", "description": "报名截止时间(ISO格式，可选)"},
            },
            "required": ["name", "club_id", "format", "courts"],
        },
    },
    {
        "name": "list_open_competitions",
        "description": "查看当前可报名的比赛大厅列表",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "可选搜索关键词（比赛名/球员名）"}},
            "required": [],
        },
    },
    {
        "name": "join_open_competition",
        "description": "报名加入开放中的比赛",
        "input_schema": {
            "type": "object",
            "properties": {"comp_id": {"type": "integer", "description": "比赛 ID"}},
            "required": ["comp_id"],
        },
    },
    {
        "name": "start_competition",
        "description": "开始比赛（开放报名场景常用，报名人数满足赛制后可开赛）",
        "input_schema": {
            "type": "object",
            "properties": {"comp_id": {"type": "integer", "description": "比赛 ID"}},
            "required": ["comp_id"],
        },
    },
    {
        "name": "list_my_competitions",
        "description": "查看我参加过/正在参加的比赛和战绩",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_competition",
        "description": "查看比赛详情（对阵表、比分），返回match_id用于录入比分",
        "input_schema": {
            "type": "object",
            "properties": {"comp_id": {"type": "integer", "description": "比赛 ID"}},
            "required": ["comp_id"],
        },
    },
    {
        "name": "record_score",
        "description": "录入比赛比分（需 match_id）。若只有比赛ID和比分，优先用 record_competition_score。",
        "input_schema": {
            "type": "object",
            "properties": {
                "match_id": {"type": "integer", "description": "对阵ID（从get_competition返回的matches中获取）"},
                "score_a": {"type": "integer", "description": "A队分数"},
                "score_b": {"type": "integer", "description": "B队分数"},
            },
            "required": ["match_id", "score_a", "score_b"],
        },
    },
    {
        "name": "record_competition_score",
        "description": "为指定比赛录入比分（只需比赛ID和比分，自动找到第一场未计分的对阵）。用户说「记录比分21:15」时，先 list_active_competitions 找到比赛，再调用此工具。",
        "input_schema": {
            "type": "object",
            "properties": {
                "comp_id": {"type": "integer", "description": "比赛 ID"},
                "score_a": {"type": "integer", "description": "A队分数"},
                "score_b": {"type": "integer", "description": "B队分数"},
            },
            "required": ["comp_id", "score_a", "score_b"],
        },
    },
    {
        "name": "list_active_competitions",
        "description": "查看我可计分的比赛（含进行中、待开赛但人数已满的开放报名比赛）",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "record_latest_score",
        "description": "为最近一场可计分的比赛录入比分（只需比分，自动识别比赛、必要时自动开赛）。用户说「记比分21:15」「帮我计分」且未指定比赛ID时优先使用。",
        "input_schema": {
            "type": "object",
            "properties": {
                "score_a": {"type": "integer", "description": "A队分数"},
                "score_b": {"type": "integer", "description": "B队分数"},
            },
            "required": ["score_a", "score_b"],
        },
    },
    {
        "name": "get_leaderboard",
        "description": "查看俱乐部排行榜",
        "input_schema": {
            "type": "object",
            "properties": {"club_id": {"type": "integer", "description": "俱乐部 ID"}},
            "required": ["club_id"],
        },
    },
    {
        "name": "get_partner_stats",
        "description": "查看球员与不同搭档的合作胜率",
        "input_schema": {
            "type": "object",
            "properties": {"player_id": {"type": "integer", "description": "球员 ID"}},
            "required": ["player_id"],
        },
    },
    {
        "name": "suggest_teams",
        "description": "根据球员等级和胜率建议均衡分组",
        "input_schema": {
            "type": "object",
            "properties": {
                "club_id": {"type": "integer", "description": "俱乐部 ID"},
                "player_ids": {"type": "array", "items": {"type": "integer"}, "description": "候选球员ID（可选）"},
            },
            "required": ["club_id"],
        },
    },
    {
        "name": "create_club",
        "description": "创建新俱乐部",
        "input_schema": {
            "type": "object",
            "properties": {"name": {"type": "string", "description": "俱乐部名称"}},
            "required": ["name"],
        },
    },
    {
        "name": "join_club",
        "description": "加入已有俱乐部",
        "input_schema": {
            "type": "object",
            "properties": {"club_id": {"type": "integer", "description": "俱乐部 ID"}},
            "required": ["club_id"],
        },
    },
    {
        "name": "search_clubs",
        "description": "按名称搜索俱乐部。query 为空字符串时返回所有可搜索俱乐部。",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "搜索关键词，可为空"}},
            "required": ["query"],
        },
    },
    {
        "name": "list_available_clubs",
        "description": "列出系统中用户尚未加入、可加入的俱乐部。用户问「有哪些俱乐部」「能加入什么俱乐部」时使用。",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "可选名称关键词过滤"}},
            "required": [],
        },
    },
]

def _build_user_context(db: Session, user: User) -> str:
    """预加载用户的所有俱乐部和球员信息，注入 system prompt"""
    context_parts: list[str] = []

    # 用户身份
    context_parts.append(f"当前用户（就是你！）：{user.name}（用户名={user.username}，用户ID={user.id}）")

    # 用户的俱乐部
    try:
        clubs = club_service.list_user_clubs(db, user)
    except Exception:
        clubs = []

    if clubs:
        lines_ctx = ["你的俱乐部及成员："]
        for c in clubs:
            try:
                players = club_service.get_club_players(db, c.id)
            except Exception:
                players = []
            player_list = ", ".join(f"{p.name}(id={p.id})" for p in players)
            lines_ctx.append(f"  · 俱乐部「{c.name}」(id={c.id})：{player_list}")
        context_parts.append("\n".join(lines_ctx))
    else:
        context_parts.append(
            "你还没有加入任何俱乐部。系统里可能有其他俱乐部，"
            "请用 list_available_clubs 或 search_clubs（query 可为空）查询。"
        )

    return "\n".join(context_parts)


def _find_player_in_clubs(db: Session, user: User, name: str):
    """在用户的俱乐部中按名字查找球员，返回(球员, 所属俱乐部)"""
    try:
        clubs = club_service.list_user_clubs(db, user)
    except Exception:
        return None, None

    name_lower = name.strip().lower()
    for club in clubs:
        try:
            players = club_service.get_club_players(db, club.id)
        except Exception:
            continue
        for p in players:
            if p.name.lower() == name_lower or name_lower in p.name.lower():
                return p, club
    return None, None


def _get_user_player(db: Session, user: User):
    """获取用户对应的球员记录"""
    return db.query(Player).filter(Player.id == user.id).first()


def _preload_intent(message: str, db: Session, user: User) -> str:
    """预判用户意图，生成操作线索注入系统提示词。

    不执行任何操作，只返回给 LLM 的「提示」文本。
    LLM 仍然需要自己调用工具——这才是 Agent 的自主决策。
    """
    msg = message.strip()
    hints: list[str] = []

    # === 0. 复合意图：创建比赛 + 记录比分 ===
    # 检测类似 "创建比赛并记录21:0"、"打完比分21:15" 这样的复合指令
    score_pattern = r"[:\uff1a](\d+)[:\uff1a\-](\d+)|比分\s*(\d+)\s*[:\uff1a\-]\s*(\d+)|打[完成].*?(\d+)\s*[:\uff1a\-]\s*(\d+)"
    score_match = re.search(score_pattern, msg)
    
    # 检查是否有创建比赛的意图 + 比分信息
    has_competition_intent = any(kw in msg for kw in ["单挑", "对决", "切磋", "PK", "打一场", "比赛", "比一场", "来一局", "开打"])
    has_score_in_intent = score_match is not None
    
    if has_competition_intent and has_score_in_intent:
        # 提取比分
        if score_match.group(1):
            score_a, score_b = score_match.group(1), score_match.group(2)
        elif score_match.group(3):
            score_a, score_b = score_match.group(3), score_match.group(4)
        else:
            score_a, score_b = score_match.group(5), score_match.group(6)
        
        hints.append(
            f"用户要求创建比赛并记录比分（{score_a}:{score_b}）。"
            f"这是多步操作：1）先调用 create_competition 创建比赛；"
            f"2）拿到比赛ID和 match_id 后，调用 record_score 录入比分 {score_a}:{score_b}"
        )

    # === 1. 创建比赛意图 ===
    duel_patterns = [
        r"(?:和|跟|与|同|找)\s*(\S{1,10}?)\s*(?:单挑|对决|切磋|PK|打一场|打一局|开打|对战|比赛|比一场|来一局|较量|比试)",
        r"(\S{1,10}?)\s*(?:单挑|对决|切磋|PK)\s*(?:我|一下|吧)?",
        r"(?:我要|我想|我想和|我要和|我要跟)\s*(\S{1,10}?)\s*(?:单挑|对决|切磋|PK|打一场|打一局|开打|对战|比赛|比一场|来一局|较量|比试)",
        r"(?:创建|新建|开始|发起|开一场?)\s*(?:一场\s*)?(?:和|跟|与)\s*(\S{1,10}?)\s*(?:的)?\s*(?:单挑|对决|切磋|PK|比赛|对战)",
        r"(\S{1,10}?)\s*，?\s*(?:来|我们)?\s*(?:单挑|对决|切磋|PK|打一场|打一局|开打|对战|比赛|比一场|来一局)",
    ]

    opponent_name = None
    for pattern in duel_patterns:
        m = re.search(pattern, msg)
        if m:
            candidate = m.group(1).strip()
            if candidate not in ("我", "你", "他", "她", "它", "吗", "吧", "呢", "啊", "哦", "的", "了", "是"):
                opponent_name = candidate
            break

    # 尝试提取比赛时间
    time_hint = ""
    time_patterns = [
        r"(\d{1,2})\s*[点:]\s*(\d{2})?",  # 14点 或 14:30
        r"(明天|后天|下周[一二三四五六日])",  # 相对时间
        r"(\d{1,2})[月/](\d{1,2})[日/]",  # 7月15日 或 7/15
    ]
    for tp in time_patterns:
        tm = re.search(tp, msg)
        if tm:
            time_hint = f"用户提到了时间「{tm.group(0)}」，如果有scheduled_at参数可以带上。"
            break
    
    if opponent_name:
        user_player = _get_user_player(db, user)
        opponent, target_club = _find_player_in_clubs(db, user, opponent_name)
        if user_player and opponent and target_club and opponent.id != user_player.id:
            hint_text = (
                f"用户说「{message}」，很像要创建比赛。线索："
                f"name='{user_player.name} VS {opponent.name}'，"
                f"club_id={target_club.id}，format='singles_rotation'，"
                f"courts=1，player_ids=[{user_player.id}, {opponent.id}]。"
                f"{time_hint}"
                f"你应该调用 create_competition 工具（先打招呼！）。"
            )
            hints.append(hint_text)
        elif opponent and opponent.id == user_player.id:
            hints.append("用户想和自己单挑，这不合理，调侃一下建议换对手。")

    # N人转
    rotation_match = re.search(r"(\d+)\s*人\s*转", msg)
    if rotation_match:
        n = int(rotation_match.group(1))
        try:
            clubs = club_service.list_user_clubs(db, user)
        except Exception:
            clubs = []
        if clubs:
            try:
                club_players = club_service.get_club_players(db, clubs[0].id)
            except Exception:
                club_players = []
            if len(club_players) >= n >= 2:
                selected = club_players[:n]
                player_ids = [p.id for p in selected]
                player_names = [p.name for p in selected]
                if n == 4:
                    fmt = "four_player_rotation"
                elif n == 8:
                    fmt = "eight_player_rotation"
                elif n % 2 == 0:
                    fmt = "doubles_rotation"
                else:
                    fmt = "singles_rotation"
                hints.append(
                    f"用户想做{n}人转。线索："
                    f"name='{n}人转'，club_id={clubs[0].id}，format='{fmt}'，"
                    f"courts=1，player_ids={player_ids}（{'、'.join(player_names)}）。"
                    f"{time_hint}"
                    f"你应该调用 create_competition 工具。"
                )

    # === 1.1 自主报名比赛意图 ===
    if re.search(r"(?:自主报名|开放报名|公开报名|大厅报名|所有人可报名|可报名比赛)", msg):
        try:
            clubs = club_service.list_user_clubs(db, user)
        except Exception:
            clubs = []
        if clubs:
            hints.append(
                f"用户想创建自主报名比赛。线索：club_id={clubs[0].id}，open_signup=true，is_public=true。"
                f"若用户提到人数上限可填 max_players；提到截止时间可填 signup_deadline。"
                f"你应该调用 create_competition 工具。"
            )

    # === 1.2 大厅/公开比赛（无需俱乐部）===
    if re.search(r"(?:大厅比赛|公开比赛|大厅.*创建|无需俱乐部|不用俱乐部|直接创建比赛|创建大厅比赛|大厅.*比赛)", msg):
        hints.append(
            "用户想创建大厅/公开比赛，无需加入俱乐部即可参加。"
            "线索：club_id=null（表示大厅），open_signup=true，is_public=true。"
            "你应该调用 create_competition 工具，并设置 club_id 为 null。"
        )

    # === 2. 排行榜 ===
    if re.search(r"(?:排行榜|排名|积分榜|谁最强|谁最厉害)", msg):
        try:
            clubs = club_service.list_user_clubs(db, user)
        except Exception:
            clubs = []
        if clubs:
            hints.append(
                f"用户想看排行榜。线索：club_id={clubs[0].id}。"
                f"你应该调用 get_leaderboard 工具。"
            )

    # === 3. 搭档统计 ===
    if re.search(r"(?:搭档|合作|配合).*(?:统计|胜率|数据|情况)", msg):
        partner_match = re.search(r"(?:搭档|合作|配合|和谁配合|跟谁配合)\s*(\S{1,10})?", msg)
        target_name = (partner_match.group(1) or "").strip() if partner_match else ""
        if target_name:
            player, _ = _find_player_in_clubs(db, user, target_name)
        else:
            player = _get_user_player(db, user)
        if player:
            hints.append(
                f"用户想看{player.name}的搭档统计。线索：player_id={player.id}。"
                f"你应该调用 get_partner_stats 工具。"
            )

    # === 4. 智能分组 ===
    if re.search(r"(?:分组|分队|蛇形|均衡|公平|分两队|分下队|怎么分)", msg):
        try:
            clubs = club_service.list_user_clubs(db, user)
        except Exception:
            clubs = []
        if clubs:
            hints.append(
                f"用户想做智能分组。线索：club_id={clubs[0].id}。"
                f"你应该调用 suggest_teams 工具。"
            )

    # === 5. 搜索俱乐部 ===
    search_match = re.search(
        r"(?:搜索|找|查|看看?有什么)\s*(?:俱乐部|球会)\s*(\S.{0,20})?", msg
    )
    club_name_match = re.search(r"(?:找|搜|查)\s*(.+?)\s*(?:俱乐部|球会)", msg)
    if search_match:
        query = (search_match.group(1) or "").strip()
        hints.append(
            f"用户想搜索俱乐部{f'「{query}」' if query else ''}。"
            f"你应该调用 search_clubs 工具，query='{query}'。"
        )
    elif club_name_match:
        query = club_name_match.group(1).strip()
        hints.append(
            f"用户想搜索俱乐部「{query}」。"
            f"你应该调用 search_clubs 工具，query='{query}'。"
        )
    elif re.search(r"俱乐部", msg) and re.search(
        r"(?:有哪些|可加入|可以加入|能加入|什么|哪些|搜|找|查|推荐|加入什么|哪个)", msg
    ):
        hints.append(
            "用户想了解可加入的俱乐部。你应该调用 list_available_clubs 工具；"
            "如需按名称搜索则调用 search_clubs。"
        )

    # === 6. 查看比赛 ===
    comp_match = re.search(r"(?:查看|看看|打开|进入)\s*(?:比赛|赛事)\s*(\d+)", msg)
    if comp_match:
        hints.append(
            f"用户想查看比赛 id={comp_match.group(1)}。"
            f"你应该调用 get_competition 工具。"
        )

    # === 7. 查看比赛大厅 ===
    if re.search(r"(?:比赛大厅|报名中|可报名|开放比赛|有哪些比赛能报名)", msg):
        hints.append("用户想看比赛大厅。你应该调用 list_open_competitions 工具。")

    # === 8. 报名某场比赛 ===
    join_match = re.search(r"(?:报名|加入).*(?:比赛|赛事)\s*(\d+)", msg)
    if join_match:
        hints.append(
            f"用户想报名比赛 id={join_match.group(1)}。"
            f"你应该调用 join_open_competition 工具。"
        )

    # === 9. 开始比赛 ===
    start_match = re.search(r"(?:开始|开赛).*(?:比赛|赛事)\s*(\d+)", msg)
    if start_match:
        hints.append(
            f"用户想开始比赛 id={start_match.group(1)}。"
            f"你应该调用 start_competition 工具。"
        )

    # === 10. 我的比赛/战绩 ===
    if re.search(r"(?:我的比赛|我的战绩|我参加的比赛|我打过的比赛)", msg):
        hints.append("用户想查看自己的比赛和战绩。你应该调用 list_my_competitions 工具。")

    # === 11. 录入比分/计分意图（需要上下文）===
    score_nums = re.search(r"(\d+)\s*[:：]\s*(\d+)", msg)
    if re.search(r"(?:录入比分|记录比分|计分|记比分|比分.*\d+[:：]\d+|\d+[:：]\d+.*比分)", msg):
        comp_id_match = (
            re.search(r"(?:比赛|赛事)\s*(\d+)", msg)
            or re.search(r"当前比赛ID[=＝](\d+)", msg, re.I)
            or re.search(r"comp[_\-]?id\s*(?:=|:)?\s*(\d+)", msg, re.I)
        )
        has_comp_id = bool(comp_id_match)
        has_match_id = bool(re.search(r"match[_\-]?id\s*(?:=|:)?\s*(\d+)", msg, re.I))
        score_hint = ""
        if score_nums:
            score_hint = f"比分线索 score_a={score_nums.group(1)}, score_b={score_nums.group(2)}。"

        if not has_comp_id and not has_match_id:
            hints.append(
                f"用户想录入比分。{score_hint}"
                "你应该优先调用 record_latest_score（只需比分，自动找比赛并开赛）；"
                "若失败再调用 list_active_competitions 查看详情。"
            )
        elif has_comp_id and score_nums:
            cid = comp_id_match.group(1)
            hints.append(
                f"用户想为比赛 id={cid} 录入比分。{score_hint}"
                f"你应该调用 record_competition_score，comp_id={cid}，"
                f"score_a={score_nums.group(1)}，score_b={score_nums.group(2)}。"
            )
        else:
            hints.append(
                f"用户想录入比分。{score_hint}"
                "如需 match_id 先调用 get_competition；"
                "有 comp_id 时优先 record_competition_score。"
            )

    # === 12. 查看可加入的俱乐部 ===
    if re.search(
        r"(?:有哪些俱乐部|可加入.*俱乐部|可以加入.*俱乐部|推荐.*俱乐部|什么俱乐部.*加入|哪些俱乐部|能加入.*俱乐部)",
        msg,
    ):
        hints.append("用户想看有哪些俱乐部可以加入。你应该调用 list_available_clubs 工具。")

    if hints:
        return "【意图预判 - 系统线索】\n" + "\n".join(f"  → {h}" for h in hints) + "\n\n（以上是线索，你仍需自行决策是否调用工具。但方向已经很明显了！）"
    return ""


async def execute_tool(name: str, args: dict, db: Session, user: User) -> tuple[str, list[dict]]:
    """执行 LLM 决定的工具调用，返回 (JSON 结果, nav_links)"""
    nav_links: list[dict] = []
    try:
        if name == "create_club":
            club = club_service.create_club(db, user, args["name"])
            nav_links.append({"label": f"进入{club.name}", "path": f"/clubs/{club.id}"})
            return json.dumps({
                "id": club.id, "name": club.name,
                "owner_name": club.owner.name,
                "message": f"俱乐部「{club.name}」创建成功！",
            }, ensure_ascii=False), nav_links

        elif name == "join_club":
            club_service.join_club(db, args["club_id"], user)
            club_obj = db.query(Club).filter(Club.id == args["club_id"]).first()
            nav_links.append({"label": f"进入{club_obj.name if club_obj else '俱乐部'}", "path": f"/clubs/{args['club_id']}"})
            return json.dumps({
                "club_id": args["club_id"],
                "club_name": club_obj.name if club_obj else "",
                "message": f"已加入俱乐部「{club_obj.name if club_obj else ''}」",
            }, ensure_ascii=False), nav_links

        elif name == "search_clubs":
            results = club_service.search_clubs(db, args["query"], user.id)
            for r in results:
                nav_links.append({"label": f"进入{r['name']}", "path": f"/clubs/{r['id']}"})
            return json.dumps(results, ensure_ascii=False), nav_links

        elif name == "create_competition":
            # 解析时间类字段（如果提供）
            scheduled_at = None
            if args.get("scheduled_at"):
                try:
                    scheduled_at = datetime.fromisoformat(args["scheduled_at"].replace("Z", "+00:00"))
                except ValueError:
                    scheduled_at = None
            signup_deadline = None
            if args.get("signup_deadline"):
                try:
                    signup_deadline = datetime.fromisoformat(args["signup_deadline"].replace("Z", "+00:00"))
                except ValueError:
                    signup_deadline = None

            open_signup = bool(args.get("open_signup", False))
            is_public = bool(args.get("is_public", False))
            max_players = args.get("max_players")
            player_ids = args.get("player_ids") or []

            # 已指定球员时走直接开赛（避免开放报名只加入创建者、无法计分）
            if len(player_ids) >= 2:
                open_signup = False
                is_public = False
            
            # 支持大厅比赛（club_id 为 null 或 0）
            club_id = args.get("club_id")
            if club_id == 0 or club_id == "null" or club_id == "":
                club_id = None

            comp = competition_service.create_competition(
                db, args["name"], club_id, args["format"],
                args["courts"], player_ids, scheduled_at,
                open_signup=open_signup, is_public=is_public,
                max_players=max_players, signup_deadline=signup_deadline,
                creator_user_id=user.id,
            )
            nav_links.append({"label": f"进入{comp.name}", "path": f"/competitions/{comp.id}"})
            # 构建包含对阵信息的返回结果，方便后续录入比分
            rounds_data = []
            for rnd in comp.rounds:
                matches_data = []
                for m in rnd.matches:
                    matches_data.append({
                        "match_id": m.id,
                        "court": m.court,
                        "team_a": m.team_a,
                        "team_b": m.team_b,
                        "score_a": m.score_a,
                        "score_b": m.score_b,
                    })
                rounds_data.append({
                    "round_number": rnd.round_number,
                    "matches": matches_data,
                })
            return json.dumps({
                "id": comp.id, 
                "name": comp.name, 
                "status": comp.status, 
                "format": comp.format, 
                "is_public": comp.is_public,
                "max_players": comp.max_players,
                "signup_deadline": comp.signup_deadline.isoformat() if comp.signup_deadline else None,
                "rounds_count": len(comp.rounds),
                "rounds": rounds_data,
                "message": f"比赛「{comp.name}」创建成功！状态={comp.status}。",
            }, ensure_ascii=False), nav_links

        elif name == "list_open_competitions":
            query = (args.get("query") or "").strip()
            competitions = competition_service.list_open_competitions(db, user.id, query)
            payload = []
            for comp in competitions:
                joined = bool(getattr(comp, "my_joined", False))
                creator_name = getattr(comp, "creator_name", None)
                player_count = len(comp.competition_players or [])
                payload.append({
                    "id": comp.id,
                    "name": comp.name,
                    "club_id": comp.club_id,
                    "format": comp.format,
                    "status": comp.status,
                    "is_public": comp.is_public,
                    "max_players": comp.max_players,
                    "signup_deadline": comp.signup_deadline.isoformat() if comp.signup_deadline else None,
                    "creator_name": creator_name,
                    "my_joined": joined,
                    "player_count": player_count,
                })
                nav_links.append({"label": f"查看{comp.name}", "path": f"/competitions/{comp.id}"})
            return json.dumps(payload, ensure_ascii=False), nav_links

        elif name == "join_open_competition":
            comp = competition_service.join_open_competition(db, args["comp_id"], user.id)
            nav_links.append({"label": f"进入{comp.name}", "path": f"/competitions/{comp.id}"})
            return json.dumps({
                "id": comp.id,
                "name": comp.name,
                "status": comp.status,
                "player_count": len(comp.competition_players or []),
                "max_players": comp.max_players,
                "message": f"已报名比赛「{comp.name}」",
            }, ensure_ascii=False), nav_links

        elif name == "start_competition":
            comp = competition_service.start_competition(db, args["comp_id"])
            nav_links.append({"label": f"进入{comp.name}", "path": f"/competitions/{comp.id}"})
            return json.dumps({
                "id": comp.id,
                "name": comp.name,
                "status": comp.status,
                "message": f"比赛「{comp.name}」已开赛",
            }, ensure_ascii=False), nav_links

        elif name == "list_my_competitions":
            items = competition_service.list_my_competitions(db, user.id)
            nav_links.append({"label": "我的比赛", "path": "/my-competitions"})
            for item in items[:5]:
                nav_links.append({"label": f"查看{item['name']}", "path": f"/competitions/{item['id']}"})
            return json.dumps(items, ensure_ascii=False), nav_links

        elif name == "list_active_competitions":
            items = competition_service.list_scorable_competitions(db, user.id)
            ready = [i for i in items if i.get("ready_to_score")]
            nav_links.append({"label": "我的比赛", "path": "/my-competitions"})
            for item in ready[:5]:
                nav_links.append({"label": f"查看{item['name']}", "path": f"/competitions/{item['id']}"})
            return json.dumps({
                "count": len(ready),
                "ready_count": len(ready),
                "competitions": items,
                "ready_competitions": ready,
                "message": (
                    f"有 {len(ready)} 场可计分（最近：{ready[0]['name']} id={ready[0]['id']}）"
                    if ready
                    else (
                        f"暂无可直接计分的比赛。{items[0]['message']}"
                        if items
                        else "暂无可计分的比赛，请先创建或加入比赛"
                    )
                ),
            }, ensure_ascii=False), nav_links

        elif name == "list_available_clubs":
            try:
                query = (args.get("query") or "").strip()
                user_clubs = club_service.list_user_clubs(db, user)
                user_club_ids = {c.id for c in user_clubs}
                all_clubs = club_service.search_clubs(db, query, user.id)
                available_clubs = [c for c in all_clubs if c["id"] not in user_club_ids]
                for c in available_clubs[:6]:
                    nav_links.append({"label": f"加入{c['name']}", "path": f"/clubs/{c['id']}"})
                return json.dumps({
                    "count": len(available_clubs),
                    "clubs": available_clubs[:10],
                    "message": f"找到 {len(available_clubs)} 个可加入的俱乐部" if available_clubs else "暂无可加入的俱乐部，你可以创建一个新的！",
                }, ensure_ascii=False), nav_links
            except Exception as e:
                logger.warning(f"获取可加入俱乐部失败: {e}")
                return json.dumps({
                    "count": 0,
                    "clubs": [],
                    "message": "获取俱乐部列表失败，请稍后重试",
                }, ensure_ascii=False), []

        elif name == "get_competition":
            nav_links.append({"label": "查看比赛详情", "path": f"/competitions/{args['comp_id']}"})
            comp = competition_service.get_competition(db, args["comp_id"])
            pid_to_name = {p.id: p.name for p in comp.players}
            result = {
                "id": comp.id, "name": comp.name, "status": comp.status,
                "format": comp.format, "courts": comp.courts,
                "players": [{"id": p.id, "name": p.name, "level": p.level} for p in comp.players],
                "rounds": [],
            }
            for rnd in comp.rounds:
                rnd_data = {"round_number": rnd.round_number, "matches": []}
                for m in rnd.matches:
                    rnd_data["matches"].append({
                        "match_id": m.id, "court": m.court,
                        "team_a_names": [pid_to_name.get(pid, f"球员{pid}") for pid in m.team_a],
                        "team_b_names": [pid_to_name.get(pid, f"球员{pid}") for pid in m.team_b],
                        "team_a": m.team_a, "team_b": m.team_b,
                        "score_a": m.score_a, "score_b": m.score_b,
                        "scored": m.score_a is not None,
                    })
                result["rounds"].append(rnd_data)
            return json.dumps(result, ensure_ascii=False), nav_links

        elif name == "record_score":
            match = competition_service.record_score(
                db, args["match_id"], args["score_a"], args["score_b"], user.id,
            )
            if match.round:
                nav_links.append({"label": "查看比赛", "path": f"/competitions/{match.round.competition_id}"})
            return json.dumps({
                "match_id": match.id, "score_a": match.score_a, "score_b": match.score_b,
                "message": f"比分已录入: {args['score_a']}:{args['score_b']}",
            }, ensure_ascii=False), nav_links

        elif name == "record_competition_score":
            match, match_id = competition_service.record_competition_score(
                db, args["comp_id"], args["score_a"], args["score_b"], user.id,
            )
            comp_id = match.round.competition_id if match.round else args["comp_id"]
            nav_links.append({"label": "查看比赛", "path": f"/competitions/{comp_id}"})
            return json.dumps({
                "comp_id": comp_id,
                "match_id": match_id,
                "score_a": match.score_a,
                "score_b": match.score_b,
                "message": f"比赛 #{comp_id} 比分已录入: {args['score_a']}:{args['score_b']}",
            }, ensure_ascii=False), nav_links

        elif name == "record_latest_score":
            match, match_id, comp_id = competition_service.record_latest_score(
                db, args["score_a"], args["score_b"], user.id,
            )
            nav_links.append({"label": "查看比赛", "path": f"/competitions/{comp_id}"})
            return json.dumps({
                "comp_id": comp_id,
                "match_id": match_id,
                "score_a": match.score_a,
                "score_b": match.score_b,
                "message": f"已为最近比赛 #{comp_id} 录入比分: {args['score_a']}:{args['score_b']}",
            }, ensure_ascii=False), nav_links

        elif name == "get_leaderboard":
            entries, total = leaderboard_service.get_leaderboard(db, args["club_id"], skip=0, limit=20)
            nav_links.append({"label": "查看排行榜", "path": "/leaderboard"})
            return json.dumps({"entries": entries, "total": total}, ensure_ascii=False), nav_links

        elif name == "get_partner_stats":
            stats = get_partner_stats(db, args["player_id"])
            return json.dumps(stats, ensure_ascii=False), []

        elif name == "suggest_teams":
            result = suggest_balanced_teams(db, args["club_id"], args.get("player_ids"))
            nav_links.append({"label": "进入俱乐部", "path": f"/clubs/{args['club_id']}"})
            return json.dumps(result, ensure_ascii=False), nav_links

        else:
            return json.dumps({"error": f"未知工具: {name}", "error_type": "unknown_tool"}), []

    except ValueError as e:
        # 参数验证错误
        logger.warning(f"工具参数错误 [{name}]: {e}")
        return json.dumps({"error": str(e), "error_type": "invalid_params"}, ensure_ascii=False), []
    except KeyError as e:
        # 缺少必要参数
        logger.warning(f"工具缺少参数 [{name}]: {e}")
        return json.dumps({"error": f"缺少必要参数: {e}", "error_type": "missing_params"}, ensure_ascii=False), []
    except HTTPException as e:
        # FastAPI HTTP错误
        logger.warning(f"工具HTTP错误 [{name}]: {e.detail}")
        return json.dumps({"error": e.detail, "error_type": "http_error", "status_code": e.status_code}, ensure_ascii=False), []
    except Exception as e:
        # 未知错误 - 记录详细信息但返回友好提示
        logger.exception(f"工具执行错误 [{name}]: {e}")
        return json.dumps({
            "error": "操作执行失败，请稍后重试",
            "error_type": "internal_error",
            "detail": str(e) if os.getenv("DEBUG") else None
        }, ensure_ascii=False), []


MAX_TOOL_ROUNDS = 5  # 最多支持5轮工具链式调用


async def run_agent(message: str, history: list[dict], user: User, db: Session) -> AsyncGenerator[str, None]:
    """运行 Agent 对话（Function Calling + 意图预判 + 多轮工具链），流式返回 SSE 事件"""
    api_key = settings.anthropic_auth_token or settings.anthropic_api_key
    if not api_key:
        yield json.dumps({"type": "error", "content": "Agent 未配置 API Key"}, ensure_ascii=False)
        return

    client_kwargs = {"api_key": api_key}
    if settings.anthropic_base_url:
        client_kwargs["base_url"] = settings.anthropic_base_url
    client = AsyncAnthropic(**client_kwargs)

    # 保存用户消息
    save_message(db, user, "user", message)

    # 智能构建上下文：近期完整消息 + 远期总结
    context_msgs, memory_note = build_context(db, user, message)

    # ===== 意图预判：生成线索注入系统提示词（LLM 仍自主决策） =====
    intent_hint = _preload_intent(message, db, user)
    emitted_nav_paths: set[str] = set()

    # 构建消息列表（纯对话）
    messages: list[dict] = []
    for m in context_msgs:
        role = "assistant" if m["role"] == "assistant" else "user"
        messages.append({"role": role, "content": m["content"]})
    if not messages or messages[-1]["content"] != message:
        messages.append({"role": "user", "content": message})

    # 系统提示词 = 基础规则 + 用户上下文 + 记忆摘要 + 意图线索
    # 【新增】多轮链式调用提示
    chain_hint = """
【多步操作规则】
如果用户的需求需要多个步骤完成（如创建比赛并记录比分），你可以连续调用多个工具。
每完成一个工具调用，我会返回结果，你可以根据结果决定是否继续调用下一个工具。
最多支持5轮工具调用。"""
    
    user_ctx = _build_user_context(db, user)
    system_prompt = SYSTEM_PROMPT + chain_hint + "\n\n【当前用户信息 - 每次对话自动更新】\n" + user_ctx
    if memory_note:
        system_prompt += "\n\n" + memory_note
    if intent_hint:
        system_prompt += "\n\n" + intent_hint

    # 发送开始事件
    yield json.dumps({"type": "start"})

    model = settings.anthropic_model or settings.agent_model
    full_response = ""
    tool_round = 0  # 工具调用轮数计数

    # ===== 多轮工具链式调用循环 =====
    while tool_round < MAX_TOOL_ROUNDS:
        # LLM 自主决策
        try:
            response = await client.messages.create(
                model=model,
                max_tokens=2048,  # 增加token以支持多轮思考
                system=system_prompt,
                messages=messages,
                tools=TOOLS,
            )
        except Exception as e:
            logger.exception(f"Claude API 调用失败 (轮次 {tool_round + 1}): {e}")
            
            # 区分不同类型的错误
            error_str = str(e).lower()
            if "rate limit" in error_str or "429" in error_str:
                error_msg = "🏸 哎呀，问的人太多了，奶龙需要喘口气，请稍等30秒再试~"
            elif "authentication" in error_str or "401" in error_str:
                error_msg = "🔧 奶龙的API密钥好像出问题了，请联系管理员检查配置"
            elif "timeout" in error_str or "timed out" in error_str:
                error_msg = "⏰ 网络有点慢，奶龙等得睡着了……请检查网络后重试"
            elif "connection" in error_str:
                error_msg = "🌐 网络连接好像断了，请检查你的网络~"
            else:
                error_msg = f"🏸 奶龙脑子短路了……({str(e)[:50]})"
            
            yield json.dumps({"type": "error", "content": error_msg, "error_code": type(e).__name__})
            return

        # 分离文本和工具调用
        text_blocks: list[str] = []
        tool_use_blocks: list = []
        for block in response.content:
            if block.type == "text":
                text_blocks.append(block.text)
            elif block.type == "tool_use":
                tool_use_blocks.append(block)

        # 先输出 LLM 说的话（文字在前——Agent 的"人格"体现）
        round_text = "".join(text_blocks).strip()
        if round_text:
            yield json.dumps({"type": "text", "content": round_text})
            full_response = full_response + ("\n" if full_response else "") + round_text

        # 如果没有工具调用，说明对话完成
        if not tool_use_blocks:
            break

        # 有工具调用，执行并继续下一轮
        tool_round += 1
        logger.info(f"第 {tool_round} 轮工具调用，共 {len(tool_use_blocks)} 个工具")

        for tb in tool_use_blocks:
            logger.info(f"LLM 决定调用工具: {tb.name}, 参数: {tb.input}")

            # 【新增】流式通知前端正在执行工具
            yield json.dumps({"type": "tool_call", "name": tb.name, "args": tb.input, "round": tool_round})

            # 执行工具
            result_json, nav_links = await execute_tool(tb.name, tb.input, db, user)

            # 发送导航链接（去重）
            for nav in nav_links:
                if nav["path"] not in emitted_nav_paths:
                    emitted_nav_paths.add(nav["path"])
                    yield json.dumps({"type": "nav_link", "label": nav["label"], "path": nav["path"]})

            # 把 assistant 的 tool_use 加入消息历史
            messages.append({
                "role": "assistant",
                "content": [tb.to_dict()],
            })
            # 把工具执行结果作为 user 消息加入
            messages.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": tb.id,
                    "content": result_json,
                }],
            })

    # 循环结束，可能是完成或达到最大轮数
    if tool_round >= MAX_TOOL_ROUNDS:
        logger.warning(f"达到最大工具调用轮数限制 ({MAX_TOOL_ROUNDS})")

    # 没有输出时的兜底
    if not full_response.strip():
        fallback = "嗯...这个问题我需要想想，要不换个方式问我？🏸"
        yield json.dumps({"type": "text", "content": fallback})
        full_response = fallback

    # 保存助手完整回复到记忆
    if full_response.strip():
        save_message(db, user, "assistant", full_response.strip())

    generate_summary(db, user)
    yield json.dumps({"type": "done", "total_tool_rounds": tool_round})

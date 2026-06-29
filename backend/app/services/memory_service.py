"""Agent 记忆服务：分层记忆管理"""

from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.agent_conversation import AgentConversation
from app.models.user import User

MAX_FULL_MESSAGES = 12  # 保留最近 12 条完整消息
MAX_TOTAL_MESSAGES = 200  # 每个用户最多保留 200 条


def save_message(db: Session, user: User, role: str, content: str):
    """保存一条消息到数据库"""
    if not content.strip():
        return
    msg = AgentConversation(user_id=user.id, role=role, content=content)
    db.add(msg)
    db.commit()
    # 清理超出限制的旧消息
    total = db.query(AgentConversation).filter(
        AgentConversation.user_id == user.id,
        AgentConversation.role != "summary",
    ).count()
    if total > MAX_TOTAL_MESSAGES:
        oldest = db.query(AgentConversation).filter(
            AgentConversation.user_id == user.id,
            AgentConversation.role != "summary",
        ).order_by(AgentConversation.id.asc()).limit(total - MAX_TOTAL_MESSAGES).all()
        for m in oldest:
            db.delete(m)
        db.commit()


def get_recent_messages(db: Session, user: User, limit: int = 30) -> list[dict]:
    """获取最近的对话消息"""
    msgs = (
        db.query(AgentConversation)
        .filter(AgentConversation.user_id == user.id)
        .order_by(AgentConversation.id.desc())
        .limit(limit)
        .all()
    )
    msgs.reverse()
    return [{"role": m.role, "content": m.content} for m in msgs if m.role != "summary"]


def get_summaries(db: Session, user: User) -> list[str]:
    """获取所有对话总结"""
    summaries = (
        db.query(AgentConversation)
        .filter(
            AgentConversation.user_id == user.id,
            AgentConversation.role == "summary",
        )
        .order_by(AgentConversation.id.asc())
        .all()
    )
    return [s.content for s in summaries]


def build_context(db: Session, user: User, current_message: str) -> tuple[list[dict], str]:
    """
    构建发送给 Claude 的上下文。
    返回 (messages_list, memory_note)：
    - messages_list: 完整的最近消息
    - memory_note: 可注入 system prompt 的旧对话总结
    """
    all_msgs = get_recent_messages(db, user, limit=MAX_TOTAL_MESSAGES)

    if len(all_msgs) <= MAX_FULL_MESSAGES:
        return all_msgs, ""

    # 分离：最近 N 条完整保留，更早的交给总结
    recent = all_msgs[-MAX_FULL_MESSAGES:]
    older = all_msgs[:-MAX_FULL_MESSAGES]

    # 从 DB 读取已有总结 + 生成新的总结
    summaries = get_summaries(db, user)

    # 为新产生的旧消息生成总结
    older_text = "\n".join(
        f"[{m['role']}]: {m['content'][:200]}" for m in older
    )
    if len(older_text) > 500:
        older_text = older_text[:500] + "..."

    # 合并所有总结
    all_summaries = summaries + [f"更早的对话摘要：{older_text}"] if older_text else summaries

    memory_note = ""
    if all_summaries:
        memory_note = "【对话历史摘要】\n" + "\n".join(
            f"· {s}" for s in all_summaries[-5:]  # 最多保留 5 条总结
        )
        memory_note += "\n\n请结合以上历史摘要理解用户的上下文，但回答时不要重复摘要内容。"

    return recent, memory_note


def generate_summary(db: Session, user: User):
    """为超过阈值的旧消息生成一条总结并存入数据库"""
    all_msgs = get_recent_messages(db, user, limit=MAX_TOTAL_MESSAGES)
    if len(all_msgs) <= MAX_FULL_MESSAGES + 6:
        return  # 不够多，不需要总结

    older = all_msgs[: -MAX_FULL_MESSAGES]
    # 简单的关键词提取总结（不调 AI，避免额外开销）
    topics: set[str] = set()
    for m in older:
        content = m["content"]
        for keyword in ["俱乐部", "比赛", "球员", "创建", "排行榜", "比分", "单打", "双打", "八人转", "四人转", "淘汰赛", "搭档", "分组"]:
            if keyword in content:
                topics.add(keyword)

    if topics:
        summary = f"用户讨论过：{'、'.join(sorted(topics))}等话题"
        existing = (
            db.query(AgentConversation)
            .filter(
                AgentConversation.user_id == user.id,
                AgentConversation.role == "summary",
            )
            .count()
        )
        if existing < 5:  # 最多保留 5 条总结
            msg = AgentConversation(user_id=user.id, role="summary", content=summary)
            db.add(msg)
            db.commit()

        # 删除已被总结的旧消息（保留最近 20 条非总结消息）
        to_delete = (
            db.query(AgentConversation)
            .filter(
                AgentConversation.user_id == user.id,
                AgentConversation.role.in_(["user", "assistant"]),
            )
            .order_by(AgentConversation.id.asc())
            .limit(len(older))
            .all()
        )
        for m in to_delete:
            db.delete(m)
        db.commit()


def clear_memory(db: Session, user: User):
    """清空用户的所有记忆"""
    db.query(AgentConversation).filter(
        AgentConversation.user_id == user.id
    ).delete()
    db.commit()


def get_memory_stats(db: Session, user: User) -> dict:
    """获取记忆统计信息"""
    total = (
        db.query(AgentConversation)
        .filter(AgentConversation.user_id == user.id)
        .count()
    )
    user_msgs = (
        db.query(AgentConversation)
        .filter(
            AgentConversation.user_id == user.id,
            AgentConversation.role == "user",
        )
        .count()
    )
    agent_msgs = (
        db.query(AgentConversation)
        .filter(
            AgentConversation.user_id == user.id,
            AgentConversation.role == "assistant",
        )
        .count()
    )
    summaries = (
        db.query(AgentConversation)
        .filter(
            AgentConversation.user_id == user.id,
            AgentConversation.role == "summary",
        )
        .count()
    )

    # 提取最近讨论的关键词
    recent = get_recent_messages(db, user, limit=20)
    keywords: set[str] = set()
    for m in recent:
        for kw in ["俱乐部", "比赛", "球员", "创建", "排行榜", "比分", "单打", "双打", "分组"]:
            if kw in m["content"]:
                keywords.add(kw)

    return {
        "total_messages": total,
        "user_messages": user_msgs,
        "agent_messages": agent_msgs,
        "summaries": summaries,
        "recent_topics": sorted(keywords) if keywords else [],
        "storage": "服务端数据库 (SQLite)",
    }

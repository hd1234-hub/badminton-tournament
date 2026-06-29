"""Agent 路由：SSE 流式对话端点 + 记忆管理"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from app.database import get_db
from app.deps import get_current_user
from app.limiter import limiter
from app.models.user import User
from app.services.agent_service import run_agent
from app.services.memory_service import get_memory_stats, clear_memory, get_recent_messages

router = APIRouter(prefix="/api/v1/agent", tags=["agent"])


@router.post("/chat")
@limiter.limit("20/minute")  # AI对话限制：每分钟20次（成本保护）
async def chat(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    body = await request.json()
    message = body.get("message", "").strip()
    history = body.get("history", [])
    if not message:
        return EventSourceResponse(iter([]))

    async def event_generator():
        async for event in run_agent(message, history, user, db):
            if await request.is_disconnected():
                break
            yield event

    return EventSourceResponse(event_generator())


@router.get("/memory")
def get_memory(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取用户的记忆状态"""
    stats = get_memory_stats(db, user)
    recent = get_recent_messages(db, user, limit=10)
    return {"stats": stats, "recent": recent}


@router.delete("/memory")
def delete_memory(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """清空用户记忆"""
    clear_memory(db, user)
    return {"message": "记忆已清空"}

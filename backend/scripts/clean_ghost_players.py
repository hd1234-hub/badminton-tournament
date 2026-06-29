#!/usr/bin/env python3
"""清理 player_id <= 0 的幽灵 CompetitionPlayer 记录"""

import sys
sys.path.insert(0, "/app")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.competition import CompetitionPlayer
from app.database import DATABASE_URL

def clean_ghost_players():
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    # 查找 player_id <= 0 的记录
    ghost_records = db.query(CompetitionPlayer).filter(CompetitionPlayer.player_id <= 0).all()
    
    if not ghost_records:
        print("✅ 没有发现幽灵球员记录")
        return
    
    print(f"⚠️  发现 {len(ghost_records)} 条幽灵记录，准备清理...")
    
    for record in ghost_records:
        print(f"  - 删除: competition_id={record.competition_id}, player_id={record.player_id}")
        db.delete(record)
    
    db.commit()
    print(f"✅ 已清理 {len(ghost_records)} 条幽灵记录")

if __name__ == "__main__":
    clean_ghost_players()

#!/usr/bin/env python3
"""
SQLite → PostgreSQL 数据迁移脚本
使用: python scripts/migrate_to_postgres.py
"""

import json
import sqlite3
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def migrate():
    # 1. 连接SQLite
    print("📂 连接SQLite数据库...")
    sqlite_conn = sqlite3.connect("data/badminton.db")
    sqlite_conn.row_factory = sqlite3.Row
    
    # 2. 连接PostgreSQL（从环境变量读取）
    print("🐘 连接PostgreSQL数据库...")
    import os
    from app.config import settings
    
    pg_url = os.getenv("DATABASE_URL", settings.database_url)
    if "postgresql" not in pg_url:
        print("❌ 请先将DATABASE_URL改为PostgreSQL连接字符串")
        print("   当前:", pg_url)
        return
    
    pg_engine = create_engine(pg_url)
    
    # 3. 确保表已创建
    print("📋 检查PostgreSQL表结构...")
    from app.database import Base
    Base.metadata.create_all(bind=pg_engine)
    
    # 4. 获取所有表
    tables = [
        "users", "clubs", "club_members", "players", 
        "competitions", "competition_players", "rounds", "matches",
        "activities", "activity_signups", "notifications",
        "agent_conversations", "predictions"
    ]
    
    Session = sessionmaker(bind=pg_engine)
    pg_session = Session()
    
    for table in tables:
        print(f"\n📥 迁移表: {table}")
        
        # 读取SQLite数据
        cursor = sqlite_conn.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        
        if not rows:
            print(f"   跳过（无数据）")
            continue
        
        print(f"   发现 {len(rows)} 条记录")
        
        # 清空PostgreSQL表（避免冲突）
        pg_session.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
        
        # 插入数据
        for row in rows:
            row_dict = dict(row)
            
            # 处理datetime字段
            for key, value in row_dict.items():
                if value is None:
                    continue
                if isinstance(value, str) and "T" in value:
                    # ISO格式转datetime
                    try:
                        row_dict[key] = datetime.fromisoformat(value.replace("Z", "+00:00"))
                    except:
                        pass
            
            # 构建INSERT语句
            columns = ", ".join(row_dict.keys())
            placeholders = ", ".join([f":{k}" for k in row_dict.keys()])
            sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
            
            try:
                pg_session.execute(text(sql), row_dict)
            except Exception as e:
                print(f"   ⚠️ 插入失败: {e}")
                continue
        
        pg_session.commit()
        print(f"   ✅ 迁移完成")
    
    sqlite_conn.close()
    pg_session.close()
    
    print("\n🎉 数据迁移完成！")
    print("请检查PostgreSQL中的数据是否完整")

if __name__ == "__main__":
    # 添加项目路径
    import sys
    sys.path.insert(0, ".")
    
    migrate()

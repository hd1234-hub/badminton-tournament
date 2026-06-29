# 带有 Agent 的羽毛球比赛编排系统 — 设计文档

日期: 2026-06-26

## 一、项目定位

面向羽毛球俱乐部和球友的 AI 增强比赛编排系统。核心是"赛制引擎 + AI Agent 智能交互"，让用户通过自然语言即可完成比赛创建、分组、统计。

使用者：俱乐部运营方 + 球员自助使用。

## 二、技术栈

| 层 | 选择 | 理由 |
|---|---|---|
| 后端 | Python FastAPI | AI/Agent 生态最成熟，异步性能好 |
| 前端 | React + TypeScript + Tailwind + shadcn/ui | 组件化开发，UI 出活快 |
| Agent | LangGraph + Claude API / 通义千问 | 有状态编排，Tool Calling 稳定 |
| 数据库 | SQLite（后期切 PostgreSQL） | MVP 零配置 |
| 向量库 | ChromaDB（嵌入式） | RAG 检索，与后端同进程 |
| 部署 | Docker Compose + Nginx | 一台服务器搞定 |

## 三、系统架构

```
┌─────────────────────────────────────────────────┐
│                  前端 (React)                      │
│   比赛创建 · 编排看板 · 数据统计 · 聊天对话            │
└─────────────────────┬───────────────────────────┘
                      │ REST + SSE (Agent 流式)
┌─────────────────────▼───────────────────────────┐
│              后端 (FastAPI)                       │
│                                                   │
│  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │
│  │ 比赛管理  │  │ 用户系统  │  │  Agent 编排层  │  │
│  │          │  │          │  │               │  │
│  │· 赛制引擎 │  │· 登录注册 │  │ · 自然语言理解 │  │
│  │· 对阵生成 │  │· 俱乐部  │  │ · 智能分组     │  │
│  │· 计分系统 │  │· 权限    │  │ · 数据分析     │  │
│  └──────────┘  └──────────┘  └───────────────┘  │
│                       │                         │
│              ┌────────▼────────┐                 │
│              │   SQLite +      │                 │
│              │   ChromaDB      │                 │
│              └─────────────────┘                 │
└─────────────────────────────────────────────────┘
```

核心原则：Agent → Service → DB，Agent 不直接操作数据库。Agent 不可用时，用户仍可通过表单手动操作。

## 四、赛制引擎

### 支持的赛制

| 赛制 | 说明 | 优先级 |
|------|------|--------|
| 八人转 | 8人轮转双打，每人搭档7人各一次，共7轮 | P0 |
| 小组循环 + 淘汰 | N组单循环 → 排名 → 交叉淘汰 | P1 |
| 瑞士制 | 多轮同战绩自动匹配 | P2 |
| 直排淘汰 | 单败/双败淘汰 | P2 |

### 八人转核心逻辑

预设 8 人标准对阵表，数学上保证每人与其他 7 人各搭档一次。生成时只需填充 8 名球员，输出 7 轮对阵。支持 2 场地或 4 场地。

### 数据结构

```
Competition（比赛）
  ├── id, name, format, status, courts, scheduled_at
  ├── players[]
  └── rounds[] → matches[]
      ├── court, round_number
      ├── team_a: [player_id, player_id]
      ├── team_b: [player_id, player_id]
      └── score: {a: int, b: int} | null
```

赛制引擎是纯算法模块，不依赖 Agent，可独立测试。

## 五、Agent 层设计

### 能力矩阵

| 类型 | 示例 | 技术 |
|------|------|------|
| 命令类 | "创建一个八人转" | Tool Calling → 调用 Service API |
| 建议类 | "帮我分组让两边实力均衡" | 读取历史数据 → 调用分组算法 |
| 分析类 | "张三最近胜率怎么样" | RAG 检索 + LLM 生成报告 |

### 技术组合

1. **Tool Calling** — LLM 调用后端 Service，执行命令
2. **RAG** — ChromaDB 向量检索历史战绩，注入上下文
3. **Memory** — 短期（LangGraph checkpointer）+ 长期（user_profile 表）
4. **Human-in-the-Loop** — LangGraph interrupt 节点，关键操作等用户确认
5. **结构化输出** — Agent 返回 JSON widgets，前端混合渲染卡片/图表

### 核心约束

- Agent 只调用 Service 层，不直接操作数据库
- Agent 调用失败 → 重试 1 次 → 降级提示用户用表单操作
- 前端通过 SSE 接收 Agent 流式输出

## 六、前端设计

### 页面

| 页面 | 功能 |
|------|------|
| 比赛看板 | 当前对阵表、实时比分、轮次切换 |
| 创建比赛 | 表单创建 + Agent 对话创建（双入口） |
| 俱乐部主页 | 成员、历史比赛、创建入口 |
| 个人主页 | 战绩统计、胜率图表 |
| Agent 对话面板 | 浮动聊天窗口，随时唤出 |

### 创建比赛 — 双入口

快速创建（表单）和 AI 创建（聊天）tab 切换。AI 创建完成后展示对阵预览卡片，用户确认后才落库。

### 技术

React + TypeScript + Tailwind CSS + shadcn/ui + SSE 流式渲染。

### 不做

- 实时比分 WebSocket（MVP 刷新页面即可）
- 移动端独立 App（响应式适配）

## 七、数据模型

```
players: id, name, club_id, level(1-5), handedness, gender, win_rate
clubs: id, name, owner_id
competitions: id, club_id, format, status, courts, scheduled_at
rounds: id, competition_id, round_number
matches: id, round_id, court, team_a[], team_b[], score
agent_sessions: id, user_id, competition_id, messages[], checkpoint
```

## 八、部署方案

MVP：一台 2C4G 云服务器 + Docker Compose + Nginx 反代 + SQLite + ChromaDB 嵌入式。

费用约 100 元/月（服务器 ~60 + LLM API ~20-30）。

## 九、测试策略

- 赛制引擎：pytest 参数化单元测试（重点投入）
- Service 层：集成测试
- Agent 层：Mock LLM 测 Tool Calling 链路
- E2E：Playwright 覆盖核心路径（创建比赛 → 编排 → 计分）

## 十、MVP 分两期

| 期数 | 内容 | 预估 |
|------|------|------|
| 第一期 P0 | 注册登录、俱乐部、八人转编排、手动创建比赛、计分、看板 | 2-3 周 |
| 第二期 P1 | Agent 自然语言创建、智能分组、赛后分析、RAG、HL | 1-2 周 |

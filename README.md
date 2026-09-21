# Multiplayer Game — 多人联机网页对战游戏

> 基于 Django + WebSocket 的实时多人联机对战游戏：支持注册登录、匹配系统、积分记录、多人联机对战与人机对战。

浏览器端负责渲染与游戏逻辑，服务端负责房间管理与状态同步，匹配由独立的 Thrift 服务完成。

---

## 功能

- **用户体系**：注册 / 登录 / 登出，支持 AcWing 账号一键授权登录
- **匹配系统**：独立的匹配服务，按队列撮合玩家进入同一房间
- **实时对战**：WebSocket 双向通信同步玩家位置、技能与状态
- **游戏机制**：玩家移动、火球技能、粒子特效、地图、对局内聊天
- **积分系统**：对局结果计入玩家积分
- **人机对战**：支持与电脑对手对战
- **房间容量**：每房间最多 3 人（`ROOM_CAPACITY`）

---

## 技术栈

**后端**

| 用途 | 技术 |
|---|---|
| Web 框架 | Django 3.2.8 |
| 实时通信 | Django Channels（ASGI / WebSocket） |
| 房间广播 | channels_redis（Redis Channel Layer） |
| 缓存 | django-redis |
| 匹配服务 | Thrift RPC（`match_system/`） |
| 数据库 | SQLite |

**前端**

- 原生 JavaScript（ES6 模块，按模块拆分到 `game/static/js/src/`）
- Canvas 渲染
- WebSocket 客户端

**部署**

- Linux + Nginx + Redis，ASGI 服务托管 Channels

---

## 架构

```
┌──────────────────────────────────────────┐
│  浏览器 (game/static/js/src/)             │
│  ├─ menu/            主菜单与登录          │
│  ├─ playground/      对局场景             │
│  │   ├─ player/      玩家与移动            │
│  │   ├─ skill/       技能（火球）          │
│  │   ├─ game_map/    地图                 │
│  │   ├─ particle/    粒子特效              │
│  │   ├─ chat_field/  对局内聊天            │
│  │   └─ socket/      WebSocket 客户端      │
│  └─ settings/        设置与账号            │
└────────────────┬─────────────────────────┘
                 │ HTTP（登录 / 匹配） + WebSocket（对局）
┌────────────────▼─────────────────────────┐
│  Django (acapp/) + Channels              │
│  ├─ game/views/       登录、注册、设置     │
│  ├─ game/consumers/   WebSocket 消费者     │
│  ├─ game/models/      玩家与积分           │
│  └─ game/routing.py   WebSocket 路由       │
└────────────────┬─────────────────────────┘
                 │ Thrift RPC
        ┌────────▼────────┐        ┌─────────┐
        │  match_system/  │───────▶│  Redis  │
        │  匹配服务        │        └─────────┘
        └─────────────────┘
```

对局链路：玩家点击匹配 → 匹配服务按队列撮合 → 房间满员后通知玩家进入对局 → 浏览器建立 WebSocket → 玩家操作经 WebSocket 上报 → 服务端广播给房间内其他玩家 → 各端渲染同步。

---

## 目录结构

```
.
├── manage.py
├── acapp/                          # Django 项目配置
│   ├── settings.py                 # Channels / Redis / 数据库配置
│   ├── asgi.py                     # ASGI 入口（WebSocket）
│   ├── urls.py
│   └── wsgi.py
├── game/                           # 主应用
│   ├── consumers/multiplayer/      # WebSocket 消费者（对局同步）
│   ├── models/player/              # 玩家模型与积分
│   ├── migrations/
│   ├── routing.py                  # WebSocket 路由
│   ├── urls/                       # 按模块拆分的路由
│   │   ├── index.py
│   │   ├── menu/
│   │   ├── playground/
│   │   └── settings/
│   ├── views/
│   │   ├── index.py
│   │   └── settings/               # 登录、注册、登出、信息获取
│   │       └── acwing/             # AcWing 授权登录
│   ├── templates/multimatch/       # 页面模板
│   └── static/
│       ├── css/game.css
│       ├── image/                  # 背景图与图标
│       └── js/
│           ├── src/                # 源码（按模块拆分）
│           └── dist/               # 打包产物
├── match_system/                   # 独立匹配服务（Thrift）
├── scripts/                        # 启动脚本
└── static/                         # collectstatic 产物（不应提交）
```

---

## 快速开始

### 环境要求

- Python 3.8+
- Redis（用于 Channel Layer 与缓存）
- Node.js（仅在需要重新打包前端 JS 时使用）

### 步骤

```bash
# 1) 启动 Redis
redis-server

# 2) 后端
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt        # 见下方说明
python manage.py migrate
python manage.py runserver             # 开发环境（需 ASGI 支持 WebSocket）

# 3) 匹配服务（独立进程）
cd match_system && ./run.sh            # 或按 scripts/ 中的脚本启动
```

生产环境需以 ASGI 方式托管（Daphne / Uvicorn），并由 Nginx 转发 WebSocket。

---

## 配置

`acapp/settings.py` 中的以下项需要按环境调整，**建议全部外置为环境变量**：

```
SECRET_KEY      Django 密钥（请重新生成，不要沿用仓库中的值）
DEBUG           生产环境必须为 False
ALLOWED_HOSTS   按实际部署域名配置
REDIS           Channel Layer 与缓存地址
ROOM_CAPACITY   每房间人数上限
```

---

## Roadmap

- [ ] 补充对局截图与演示 GIF
- [ ] 补齐单元测试
- [ ] 房间容量与匹配策略可配置化
- [ ] 增加观战模式
- [ ] 静态资源接入 CDN

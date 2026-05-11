# APITokenWatcher

多 API 平台 Token 用量实时监控工具。通过代理层拦截 API 请求，自动记录各平台 Token 消耗与费用，提供可视化仪表盘、阈值告警与桌面通知。

## 功能特性

- **实时监控**：通过代理层自动记录每次 API 请求的 Token 用量和费用
- **多平台支持**：支持 DeepSeek、Mimo 等 OpenAI 兼容接口
- **余额同步**：自动从平台 API 获取真实账户余额
- **可视化仪表盘**：Token 趋势图、费用趋势图、最近用量记录
- **阈值告警**：余额不足、费用超限时自动提醒
- **桌面应用**：基于 pywebview 的桌面窗口，方便挂在屏幕角落

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 16+

### 安装依赖

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 安装前端依赖并构建
cd frontend
npm install
npm run build
cd ..
```

### 启动应用

```bash
python run.py
```

启动后会打开桌面窗口，首次使用需要在「配置」页面添加平台配置。

## 配置说明

### 添加平台

1. 打开应用，点击「配置」标签
2. 点击「新增平台」
3. 填写以下信息：
   - **名称**：平台标识（如 `deepseek`）
   - **API Key**：你的 API 密钥
   - **Base URL**：API 地址（如 `https://api.deepseek.com`）
   - **初始余额**：可选，或使用「同步余额」自动获取
4. 保存后，点击「同步余额」获取真实余额

### 配置 CC Switch

如果你使用 CC Switch 连接 Claude Code：

1. 打开 CC Switch 设置
2. 将「请求地址」改为：
   ```
   http://127.0.0.1:8765/proxy/deepseek
   ```
3. API 格式选择「Anthropic Messages (原生)」
4. 保存并测试

## 项目结构

```
APITokenWatcher/
├── backend/                 # FastAPI 后端
│   ├── main.py             # 应用入口
│   ├── models.py           # 数据模型
│   ├── database.py         # 数据库配置
│   ├── config.py           # 配置管理
│   ├── routers/            # API 路由
│   │   ├── proxy.py        # 代理服务（核心）
│   │   ├── config.py       # 平台配置
│   │   ├── usage.py        # 用量统计
│   │   └── alerts.py       # 告警管理
│   └── services/           # 业务逻辑
│       ├── cost.py         # 费用计算
│       ├── monitor.py      # 定时任务
│       ├── balance.py      # 余额同步
│       └── notifier.py     # 通知服务
├── frontend/               # React 前端
│   ├── src/
│   │   ├── App.tsx         # 主界面
│   │   ├── api.ts          # API 封装
│   │   └── components/     # UI 组件
│   └── package.json
├── run.py                  # 启动脚本
├── requirements.txt        # Python 依赖
└── .gitignore
```

## 技术栈

- **后端**：FastAPI、SQLModel、SQLite、APScheduler
- **前端**：React、TypeScript、Tailwind CSS、Recharts
- **桌面**：pywebview

## 数据存储

- 数据库文件：`data.db`（SQLite，含 API Key，请勿提交到 Git）
- 已在 `.gitignore` 中排除

## 开发模式

```bash
# 后端
cd backend
uvicorn main:app --reload --host 127.0.0.1 --port 8765

# 前端
cd frontend
npm run dev
```

## 许可证

MIT License

# 全栈 CRUD 项目

Python (FastAPI) + PostgreSQL 后端，React + Vite + TypeScript 前端。

## 项目结构

```
├── backend/          # FastAPI 后端
├── frontend/         # React + Vite + TS 前端
└── docker-compose.yml  # PostgreSQL 数据库
```

## 快速开始

### 1. 启动 PostgreSQL

**方式 A：Docker**

```bash
docker compose up -d
```

后端 `.env` 使用：
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/crud_db
```

**方式 B：Homebrew（本机已安装时）**

```bash
brew services start postgresql@18
createdb crud_db
```

后端 `.env` 使用当前系统用户名（无密码）：
```
DATABASE_URL=postgresql://你的用户名@localhost:5432/crud_db
```

### 2. 启动后端

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API 文档：http://localhost:8000/docs

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端地址：http://localhost:5173

## API 接口

| 方法 | 路径          | 说明     |
|------|---------------|----------|
| GET  | /api/list     | 获取列表 |
| GET  | /api/detail   | 获取详情（?id=1） |
| POST | /api/add      | 新增     |
| POST | /api/update   | 更新     |
| POST | /api/delete   | 删除     |

## 环境变量

后端 `backend/.env`：

```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/crud_db
```

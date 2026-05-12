# Aegis 债优盾 — 中小债权人维权智能平台

Aegis 债优盾是一个面向中小债权人的法律智能平台，核心聚焦**股东出资义务加速到期**专项维权。项目整合了 FastAPI 后端、AI 对话、Chroma 法律知识库检索、财务数据库查账、文件 OCR 解析与 DOCX 文书导出能力。

## 项目结构

```text
Code/
  dual_api_server.py        # FastAPI 主后端
  Web/index.html            # 前端页面（SPA）
  Scripts/embedding_bge.py  # 从 Data/ 法律文本构建 Chroma 向量库
  Scripts/init_finance_db.py # 从 Data/财务数据/ Excel 构建 SQLite 财务库
  Scripts/get_headers.py    # 扫描 Excel 表头
Data/
  法律案例/                 # 法律案例 txt 文件
  法条/                    # 法律法规 txt 文件
  司法解释/                # 司法解释 txt 文件
  财务数据/                # 财务报表 xlsx 文件
Model/
  chroma_db/               # Chroma 向量库
  finance_data.db          # SQLite 财务数据库
Log/                       # 聊天日志与平台事件
```

## 快速开始

### 1. 准备环境变量

```bash
cp .env.example Code/.env
```

将 `Code/.env` 里的 `DEEPSEEK_API_KEY` 改成真实密钥。

> **安全提示：** `Code/.env` 已被 `.gitignore` 排除，不会被提交。

### 2. 配置公网后端地址

部署在 GitHub Pages 时，需要配置 cpolar / cloudflared 隧道地址。编辑 `config.js` 将 `publicApiBase` 改为你的隧道地址。也可以通过 URL 参数在运行时覆盖：

```text
https://timemachinedmc.github.io/Aegis/?api=https://your-tunnel.cpolar.top
```

### 3. 构建知识库

**法律知识库**（从 Data/ 下所有 .txt 文件构建）：

```bash
source .venv/bin/activate
python Code/Scripts/embedding_bge.py
```

**财务数据库**（从 Data/财务数据/ 下所有 .xlsx 文件构建）：

```bash
python Code/Scripts/init_finance_db.py
```

### 4. 启动后端

macOS：
```bash
./run_local.sh
```

Windows：
```bat
run_local.bat
```

浏览器访问 `http://127.0.0.1:8080`。

### 5. 健康检查

```text
http://127.0.0.1:8080/api/health
```

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/chat` | AI 对话（支持 SSE 流式） |
| POST | `/api/upload` | 文件上传 + OCR |
| POST | `/api/export-docx` | 法律文书 DOCX 导出 |
| GET | `/api/finance/tables` | 财务数据库表列表 |
| GET | `/api/scenarios` | 维权场景定义 |
| GET | `/api/health` | 健康检查 |
| GET | `/api/admin/events` | 管理看板事件 |

## 维权场景

1. **主线**：公司欠钱不还，想追未实缴股东
2. **主线**：公司不能清偿，判断能否主张股东出资加速到期
3. 债务发生后，公司延长了股东出资期限
4. 怀疑股东出资后又把钱转走（抽逃出资）
5. 公司减资后导致债权无法清偿
6. 股东转让股权后无人履行出资义务
7. 不确定属于哪种情况，需要系统初步判断

## 技术栈

- 后端：FastAPI + DeepSeek V3/V4 + ChromaDB (BGE-M3) + SQLite
- 前端：原生 HTML/CSS/JS + Tailwind CSS + Marked.js
- OCR：RapidOCR (PP-OCRv4) / EasyOCR
- 文档：python-docx

## 开源协议

本项目采用 [MIT License](LICENSE) 许可协议。

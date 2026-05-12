# Aegis 债优盾 · 完整部署与使用指南

## 目录

1. [环境准备](#1-环境准备)
2. [添加法律知识库数据](#2-添加法律知识库数据)
3. [添加财务数据库数据](#3-添加财务数据库数据)
4. [构建/训练知识库](#4-构建训练知识库)
5. [修改文书模板](#5-修改文书模板)
6. [修改维权场景](#6-修改维权场景)
7. [修改 AI 回答逻辑](#7-修改-ai-回答逻辑)
8. [启动系统](#8-启动系统)
9. [部署到公网](#9-部署到公网)
10. [常见问题](#10-常见问题)

---

## 1. 环境准备

### 1.1 安装 Python 依赖

```bash
# macOS
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Windows
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
```

### 1.2 配置 API Key

```bash
cp .env.example Code/.env
```

编辑 `Code/.env`，填入你的 DeepSeek API Key：

```
DEEPSEEK_API_KEY=sk-your-real-api-key
```

> 申请地址：https://platform.deepseek.com/api_keys

### 1.3 首次下载嵌入模型

首次运行需要下载 `BAAI/bge-m3` 模型（约 2GB）。编辑 `Code/.env`，将 `HF_OFFLINE` 设为 `0`：

```
HF_OFFLINE=0
```

构建完知识库后，改回 `1` 以加速启动。

---

## 2. 添加法律知识库数据

法律数据放在 `Data/` 目录下，支持多级子目录。系统会自动扫描所有 `.txt` 文件。

### 2.1 目录结构

```
Data/
├── 法条/
│   ├── 公司法2024修订全文.txt
│   ├── 企业破产法.txt
│   └── 民事诉讼法.txt
├── 司法解释/
│   ├── 公司法解释三.txt
│   ├── 九民纪要全文.txt
│   └── 最高人民法院关于适用公司法的规定.txt
├── 法律案例/
│   ├── 股东出资加速到期典型案例.txt
│   ├── 抽逃出资裁判要旨.txt
│   └── 减资程序违法案例.txt
└── 财务数据/
    ├── 利润表.xlsx
    ├── 资产负债表.xlsx
    └── RESSET科创板利润表.xlsx
```

### 2.2 法律文本格式要求

- 文件格式：`.txt`（UTF-8 或 GBK 编码均可，系统自动检测）
- 建议每个文件不超过 50KB，过大的文件会被自动切块
- 文件名会作为检索来源标注，建议使用中文描述性文件名
- 子目录名会作为分类标签（如 `法条/公司法2024修订全文.txt` → 分类为 `法条`）

### 2.3 添加一条法条示例

创建一个新文件 `Data/法条/公司法第54条.txt`：

```
《中华人民共和国公司法》第五十四条

公司不能清偿到期债务的，公司或者已到期债权的债权人有权要求已认缴出资但未届出资期限的股东提前缴纳出资。
```

### 2.4 添加一个案例示例

创建一个新文件 `Data/法律案例/加速到期胜诉案例.txt`：

```
某科技有限公司股东出资加速到期纠纷案

【案件事实】
债权人张某对某科技有限公司享有到期债权人民币50万元，经法院判决确认。
该公司注册资本1000万元，股东李某认缴600万元，实缴200万元，出资期限为2030年12月31日。
张某申请强制执行后，法院以公司无可供执行财产为由裁定终结本次执行程序。

【裁判要旨】
法院认为，根据《公司法》第五十四条，公司不能清偿到期债务，已具备破产原因但不申请破产的，
债权人有权要求已认缴出资但未届出资期限的股东提前缴纳出资。
股东李某应在未出资400万元范围内对公司债务承担补充赔偿责任。

【裁判结果】
支持原告诉讼请求。
```

---

## 3. 添加财务数据库数据

财务数据放在 `Data/财务数据/` 目录下，系统会自动扫描所有 `.xlsx` 文件。

### 3.1 Excel 格式要求

- 文件格式：`.xlsx`（Excel 2007+）
- 第一行必须是表头（列名）
- 每个 Excel 文件会被导入为一张同名 SQLite 表
- 文件名不要包含特殊字符（空格、括号等会自动替换为下划线）

### 3.2 支持的表类型

**标准简易表**（列名固定）：
- `利润表`：Scode(股票代码), Date(日期), REV(营业总收入), NI(净利润), FINEXP(财务费用)
- `资产负债表`：Scode, Date, CH(货币资金), AT(资产总计), LB(负债合计), EQU(所有者权益合计)
- `现金流量表`：Scode, Date, NCPOA(经营活动现金流量净额)

**RESSET 专业数据库**（列名格式：中文名_英文缩写）：
- 例如：`RESSET科创板利润表`、`RESSET新三板资产负债表` 等
- 列名示例：公司代码_CompanyCode、营业总收入_TotOpRev、净利润_NetProf

### 3.3 查看 Excel 表头

在导入前，可以先扫描所有 Excel 文件的表头：

```bash
python Code/Scripts/get_headers.py
```

结果保存在 `Code/Scripts/headers.txt`，可以对照确认字段名是否正确。

---

## 4. 构建/训练知识库

### 4.1 构建法律知识库（ChromaDB）

```bash
python Code/Scripts/embedding_bge.py
```

**首次运行时**会向量化所有文件。**后续运行时**自动增量更新——只处理新增和修改过的文件，跳过未变更的文件。

**执行流程：**
1. 扫描 `Data/` 下所有 `.txt` 文件（自动跳过 `财务数据/` 下的 `.xlsx`）
2. 对比 `chroma_manifest.json` 记录，识别新增/修改/未变文件
3. 仅对新增和修改的文件进行 800 字切块（重叠 150 字）
4. 使用 BGE-M3 模型将文本块转为向量，追加到 `Model/chroma_db/`

**强制重建**（如果遇到问题或想从头开始）：

```bash
python Code/Scripts/embedding_bge.py --force
```

### 4.2 构建财务数据库（SQLite）

```bash
python Code/Scripts/init_finance_db.py
```

**执行流程：**
1. 扫描 `Data/财务数据/` 下所有 `.xlsx` 文件
2. 每个 Excel 导入为一张 SQLite 表
3. 存储到 `Model/finance_data.db`

**更新数据**：重新运行即可，旧表会被覆盖。

---

## 5. 修改文书模板

文书模板在 `Code/Web/index.html` 的 `docTemplates` 对象中（约第 750 行附近）。

### 5.1 模板结构

每个模板是一段 HTML 字符串，支持以下 CSS class：

| Class | 效果 |
|-------|------|
| `highlight-name` | 蓝色高亮（人名/公司名） |
| `highlight-amount` | 红色加粗下划线（金额） |
| `section-title` | 加粗小节标题 |
| `indent` | 首行缩进 2 字符 |
| `signature-block` | 右对齐签名块 |

### 5.2 添加新文书模板

在 `docTemplates` 对象中添加一个新键（如 `"new_doc"`）：

```javascript
'new_doc': `
    <h1>你的文书标题</h1>
    <p><strong>申请人：</strong><span class="highlight-name">[变量]</span>，...</p>
    <p class="section-title">申请事项</p>
    <p class="indent">请求事项内容...</p>
    <div class="signature-block">
        <p>此致</p>
        <p><strong>[管辖机构]</strong></p>
        <p style="margin-top:48px;">申请人：______________</p>
        <p style="margin-top:16px;">2026年   月   日</p>
    </div>
`,
```

然后在"文书类型"选择器中添加对应的 `<label class="radio-label">` 项：

```html
<label class="radio-label">
    <input type="radio" name="doc_type" value="new_doc" onchange="switchTemplate(this.value)">
    你的文书名称
</label>
```

最后在 `buildDocGuide` 函数的 `purposes` 和 `checkItems` 中添加对应的说明文字。

### 5.3 文书变量说明

文书中的 `[变量]` 文本由用户在编辑器中手动修改。AI 提取的案件信息会自动显示在左侧"AI 提取变量"面板中，供用户在编辑文书时参考。

---

## 6. 修改维权场景

场景定义在 `Code/Web/index.html` 的 `SCENARIOS` 对象中（约第 550 行附近）。

### 6.1 场景结构

```javascript
"场景ID": {
    title: "场景标题",
    desc: "简短描述",
    icon: "表情符号",
    primary: true/false,  // true 为主线场景（金色高亮）
    welcome: "AI 欢迎语（Markdown 格式）",
}
```

### 6.2 添加新场景

在 `SCENARIOS` 对象中添加新键值对。场景 ID 必须唯一。

对应的法律要件和 System Prompt 在后端 `Code/dual_api_server.py` 的 `SCENARIOS` 字典中同步修改。

---

## 7. 修改 AI 回答逻辑

### 7.1 System Prompt

AI 的核心回答逻辑在 `Code/dual_api_server.py` 的 `build_system_prompt()` 函数中（约第 380 行）。

- **七段式输出模板**：在"固定输出模板"部分修改
- **法律依据**：在场景定义 `SCENARIOS` 的 `legal_basis` 中修改
- **关键构成要件**：在场景定义的 `key_elements` 中修改

### 7.2 关键词路由

在 `Code/dual_api_server.py` 中：

- `LEGAL_KEYWORDS`：触发法律知识库检索的关键词
- `FINANCE_KEYWORDS`：触发财务数据库查询的关键词
- `detect_intent()` 函数：决定何时触发本地知识库

### 7.3 财务查账表结构

在 `FINANCE_TABLE_SCHEMA` 常量中维护财务数据库的表结构说明。AI 会基于这段说明自动生成 SQL 查询。

如果你的 Excel 表结构不同，需要同步更新这段说明。

---

## 8. 启动系统

### 8.1 本地启动

```bash
# macOS
./run_local.sh

# Windows
run_local.bat
```

启动后访问：`http://127.0.0.1:8000`

### 8.2 健康检查

```bash
curl http://127.0.0.1:8000/api/health
```

返回示例：
```json
{
    "status": "ok",
    "service": "Aegis 债优盾",
    "ocr_engine": "RapidOCR(PP-OCRv4)",
    "chroma_loaded": true,
    "finance_tables": 5,
    "scenarios": 7
}
```

### 8.3 查看财务数据库中有哪些表

```bash
curl http://127.0.0.1:8000/api/finance/tables
```

---

## 9. 部署到公网

### 9.1 使用 cpolar 隧道（推荐）

1. 下载 cpolar：https://www.cpolar.com/
2. 创建隧道：

```bash
cpolar http 8000
```

3. 复制生成的公网 URL（如 `https://7de19a52.r39.cpolar.top`）
4. 编辑项目根目录的 `config.js`，填入 URL：

```javascript
window.AEGIS_CONFIG = {
    publicApiBase: "https://your-tunnel-url.cpolar.top",
};
```

5. 提交并推送。部署到 GitHub Pages 后，可以通过 URL 参数覆盖配置：

```
https://timemachinedmc.github.io/Aegis/?api=https://your-tunnel.cpolar.top
```

### 9.2 部署到 GitHub Pages

1. 在 GitHub 仓库 Settings → Pages 中，选择 `main` 分支
2. 前端页面将通过 GitHub Actions 或直接部署

---

## 10. 常见问题

### Q: 启动报错 `DEEPSEEK_API_KEY not found`
A: 确保 `Code/.env` 文件存在且包含有效的 API Key。

### Q: 启动报错 ChromaDB 加载失败
A: 先运行 `python Code/Scripts/embedding_bge.py` 构建向量库。确保 `Model/chroma_db/` 目录存在。

### Q: 财务查询无结果
A: 先运行 `python Code/Scripts/init_finance_db.py` 导入数据。确保 `Data/财务数据/` 下有 `.xlsx` 文件。

### Q: OCR 不可用
A: 需要安装 RapidOCR：`pip install rapidocr-onnxruntime`。Windows 上可能需要额外安装 Visual C++ 运行时。

### Q: 如何修改前端样式
A: 所有样式在 `Code/Web/index.html` 的 `<style>` 标签中。颜色变量在 `:root` 选择器，修改 `--gold`、`--bg` 等变量即可全局换色。

### Q: 网页打开空白
A: 确保访问的是 `http://127.0.0.1:8000`（后端端口），而不是 `http://127.0.0.1:8080`（单独预览前端时用）。

---

> 最后更新：2026年5月
> 项目仓库：https://github.com/TimeMachineDMC/Aegis
> 团队：债优盾

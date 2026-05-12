## Aegis 债优盾 启动指南

### macOS / Linux:

```bash
./run_local.sh

# 关闭后端
lsof -nP -iTCP:8080 -sTCP:LISTEN
```

### Windows:

```bat
run_local.bat
```

### 浏览器访问：

```text
http://127.0.0.1:8080
```

### 健康检查：

```text
http://127.0.0.1:8080/api/health
```

## Start

macOS / Linux:

```bash
./run_local.sh

# Close
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.aegis.backend.plist
lsof -nP -iTCP:8080 -sTCP:LISTEN
```



Windows:

```bat
run_local.bat
```

浏览器访问：

```text
http://127.0.0.1:8080
```

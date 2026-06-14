# EasyProxy — Tasks: Desktop Application

> Feature 6: US-011, US-012, US-020
> 
> **Project location:** Electron code in `apps/easyproxy-desktop/`, Nuxt frontend in `apps/easyproxy-ui/`.
> Python backend at `easyproxy/` is spawned as child process.

---

## US-011: Electron Shell

### Task 11.0: Set up Nuxt frontend app (prerequisite)

- [ ] Scaffold Nuxt 3 app tại `apps/easyproxy-ui/` — `npx nuxi init apps/easyproxy-ui`
- [ ] Add to pnpm workspace: add `apps/easyproxy-ui` to `pnpm-workspace.yaml`
- [ ] Cấu hình dev server port 3002 (thay vì 3000 mặc định)
- [ ] Tạo `nuxt.config.ts` — disable SSR (Electron renderer), enable devtools, proxy `/api` → `http://localhost:8000`
- [ ] Tạo layout: `layouts/default.vue` với sidebar navigation
- [ ] Tạo pages: `pages/index.vue` (Dashboard), `pages/proxy.vue`, `pages/settings.vue`, `pages/logs.vue`
- [ ] Set up Pinia store: `stores/proxy.ts`, `stores/pool.ts`, `stores/settings.ts`
- [ ] Set up WebSocket composable: `composables/useWebSocket.ts`
- [ ] Connect Pinia stores to API calls (axios/fetch wrapper)

**Files:** `apps/easyproxy-ui/`, `pnpm-workspace.yaml`
**Effort:** L
**Dependencies:** None (can be done alongside US-001)
**Verify:** `pnpm dev` → Nuxt app at localhost:3002

### Task 11.1: Set up Electron project

- [ ] Tạo `apps/easyproxy-desktop/package.json` với Electron dependencies
- [ ] Tạo `apps/easyproxy-desktop/electron/main.js` — Electron main process entry
- [ ] Tạo `apps/easyproxy-desktop/electron/preload.js` — context bridge (expose IPC API to renderer)
- [ ] Create window config (size: 1200x800, minWidth: 900, minHeight: 600)
- [ ] Tạo `apps/easyproxy-desktop/electron-builder.yml` — electron-builder config
- [ ] Add Nuxt build command to Electron package scripts

**Files:** `apps/easyproxy-desktop/package.json`, `apps/easyproxy-desktop/electron/main.js`, `apps/easyproxy-desktop/electron/preload.js`, `apps/easyproxy-desktop/electron-builder.yml`
**Effort:** M
**Dependencies:** Task 2.1
**Verify:** `npx electron .` mở cửa sổ trắng

### Task 11.2: Implement window manager

- [ ] Tạo `apps/easyproxy-desktop/electron/window.js` — BrowserWindow management
- [ ] Load Nuxt frontend (dev: `http://localhost:3002`, prod: local static files)
- [ ] Handle window state (position, size) persistence
- [ ] Close to tray (minimize instead of quit)
- [ ] Single instance lock (prevent multiple app instances)

**Files:** `apps/easyproxy-desktop/electron/window.js`
**Effort:** S
**Dependencies:** Task 11.1
**Verify:** Cửa sổ load Nuxt UI

### Task 11.3: Implement system tray

- [ ] Tạo `apps/easyproxy-desktop/electron/tray.js`
- [ ] System tray icon (template icon for macOS, PNG for Win/Linux)
- [ ] Context menu: Start/Stop proxy, Rotate IP, Show Window, Quit
- [ ] Status indicator: green (running), grey (stopped), yellow (error)
- [ ] Tooltip hiển thị IP hiện tại + status
- [ ] Click tray icon → toggle window visibility

**Files:** `apps/easyproxy-desktop/electron/tray.js`, `apps/easyproxy-desktop/assets/` (icons)
**Effort:** M
**Dependencies:** Task 11.1
**Verify:** System tray icon xuất hiện, menu hoạt động

### Task 11.4: Implement Python backend spawner

- [ ] Tạo `electron/backend.js` — spawn Python backend as child process
- [ ] `spawn('python', ['-m', 'easyproxy.api']`) hoặc dùng bundled binary
- [ ] Health check loop: poll `GET /health` every 500ms, max 30s timeout
- [ ] Auto-restart: nếu Python process crash, restart with exponential backoff
- [ ] Graceful shutdown: SIGTERM → wait 5s → SIGKILL
- [ ] Forward Python stdout/stderr to Electron log file
- [ ] IPC bridge: renderer gọi backend API qua Electron IPC

**Files:** `electron/backend.js`
**Effort:** M
**Dependencies:** Task 11.1, Task 2.1
**Verify:** Python backend tự động start cùng Electron

### Task 11.5: Implement health check wait before UI load

- [ ] Loading screen hiển thị khi chờ Python backend start
- [ ] Poll `/health` — khi 200, chuyển sang Nuxt UI
- [ ] Timeout: hiển thị error + retry button
- [ ] Progress indicator

**Files:** `apps/easyproxy-desktop/electron/window.js`, `apps/easyproxy-desktop/electron/preload.js`
**Effort:** S
**Dependencies:** Task 11.4, Task 11.2
**Verify:** UI load sau khi backend ready

### Task 11.6: Implement crash recovery

- [ ] Python crash → Electron auto-restart (max 3 tries)
- [ ] Notify user: "Backend crashed. Restarting..."
- [ ] After 3 failures → show error dialog + manual restart button
- [ ] Log crash details to file for debugging

**Files:** `apps/easyproxy-desktop/electron/backend.js`
**Effort:** S
**Dependencies:** Task 11.4
**Verify:** Kill Python → tự động restart

---

## US-012: System Proxy Config

### Task 12.1: Implement macOS proxy config

- [ ] Tạo `apps/easyproxy-desktop/electron/system-proxy.js`
- [ ] Set proxy: `networksetup -setwebproxy <service> localhost 8080`
- [ ] Set secure (HTTPS) proxy: `networksetup -setsecurewebproxy <service> localhost 8080`
- [ ] Detect active network service (Wi-Fi, Ethernet, Thunderbolt...)
- [ ] Store original settings before changing
- [ ] Restore on stop: `networksetup -setwebproxystate <service> off`
- [ ] Privilege escalation: prompt for sudo via AppleScript or osascript

**Files:** `apps/easyproxy-desktop/electron/system-proxy.js`
**Effort:** M
**Dependencies:** Task 11.1
**Verify:** `networksetup -getwebproxy Wi-Fi` shows localhost:8080

### Task 12.2: Implement Windows proxy config

- [ ] Set proxy: `netsh winhttp set proxy localhost:8080`
- [ ] Internet Options registry: `HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings`
- [ ] Store original settings
- [ ] Restore on stop: `netsh winhttp reset proxy`
- [ ] Handle UAC/privilege escalation

**Files:** `apps/easyproxy-desktop/electron/system-proxy.js`
**Effort:** M
**Dependencies:** Task 11.1
**Verify:** Windows system proxy set correctly

### Task 12.3: Implement Linux proxy config

- [ ] GNOME: `gsettings set org.gnome.system.proxy mode 'manual'`
- [ ] GNOME: `gsettings set org.gnome.system.proxy.http host 'localhost'` + port
- [ ] KDE: `kwriteconfig5 --file kioslaverc`
- [ ] Alternative: set environment variables `http_proxy`, `https_proxy`
- [ ] Store original settings
- [ ] Restore on stop

**Files:** `apps/easyproxy-desktop/electron/system-proxy.js`
**Effort:** S
**Dependencies:** Task 11.1
**Verify:** Linux proxy configured correctly

### Task 12.4: Implement restore on stop/quit

- [ ] On proxy stop → restore system proxy to original settings
- [ ] On app quit → restore system proxy
- [ ] Handle crash scenario: restore on next startup
- [ ] Prompt user if restore fails (manual instructions)

**Files:** `apps/easyproxy-desktop/electron/system-proxy.js`, `electron/backend.js`
**Effort:** S
**Dependencies:** Task 12.1–12.3
**Verify:** Stop proxy → system settings restored

### Task 12.5: System proxy tests

- [ ] Test macOS commands (dry-run mode, not actual execution)
- [ ] Test config save/restore logic
- [ ] Test error handling (permission denied, no network service)

**Effort:** S
**Dependencies:** Task 12.1–12.4
**Note:** Tests chạy ở dry-run mode, không thay đổi system settings thật

---

## US-020: Auto-start

### Task 20.1: Implement macOS auto-start

- [ ] Tạo `apps/easyproxy-desktop/electron/auto-launch.js`
- [ ] Register: write plist to `~/Library/LaunchAgents/`
- [ ] Unregister: remove plist
- [ ] Check status: `launchctl list`
- [ ] UI toggle in Settings page → trigger IPC call

**Files:** `electron/auto-launch.js`
**Effort:** S
**Dependencies:** Task 11.1
**Verify:** App auto-start after login

### Task 20.2: Implement Windows auto-start

- [ ] Register: `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`
- [ ] Unregister: remove registry entry
- [ ] UI toggle in Settings

**Files:** `electron/auto-launch.js`
**Effort:** S
**Dependencies:** Task 11.1
**Verify:** App starts with Windows

### Task 20.3: Implement Linux auto-start

- [ ] Register: create `.desktop` file in `~/.config/autostart/`
- [ ] Unregister: remove file
- [ ] UI toggle in Settings

**Files:** `electron/auto-launch.js`
**Effort:** S
**Dependencies:** Task 11.1
**Verify:** App starts with desktop environment

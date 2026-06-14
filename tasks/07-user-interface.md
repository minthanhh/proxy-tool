# EasyProxy — Tasks: User Interface

> Feature 7: US-013, US-014, US-018

---

## US-013: Dashboard UI

### Task 13.1: Create DashboardPage layout

- [ ] Create `packages/ui/components/DashboardPage.vue`
- [ ] Grid layout: status card (top-left), stats (top-right), recent logs (bottom)
- [ ] Auto-refresh via WebSocket every 2s
- [ ] Welcome/empty state when proxy not started
- [ ] Skeleton loading state

**Files:** `packages/ui/components/DashboardPage.vue`
**Effort:** S
**Dependencies:** Task 2.1 (API), Task 11.2 (Electron)
**Verify:** Dashboard hiển thị với dữ liệu thật

### Task 13.2: Implement ProxyStatusCard

- [ ] Green/grey status indicator (running/stopped)
- [ ] Current IP display with copy button
- [ ] Rotation strategy badge
- [ ] Uptime counter
- [ ] Start/Stop toggle button
- [ ] Rotate now button with loading state
- [ ] Tooltips for each element

**Files:** `packages/ui/components/ProxyStatusCard.vue`
**Effort:** S
**Dependencies:** Task 13.1
**Verify:** Status card hiển thị đúng trạng thái

### Task 13.3: Implement StatsGrid

- [ ] Cards: Requests (total), Rate Limits (last 24h), Rotations (today), Active Proxies
- [ ] Real-time count via WebSocket events
- [ ] Animated number transitions
- [ ] Click card → filter logs (navigate to Logs page)

**Files:** `packages/ui/components/StatsGrid.vue`
**Effort:** S
**Dependencies:** Task 13.1, Task 2.3 (WebSocket)
**Verify:** Stats update real-time

### Task 13.4: Implement RecentLogsList

- [ ] Last 20 request logs (auto-scroll)
- [ ] Colored status codes (2xx=green, 4xx=yellow, 5xx=red)
- [ ] Click log → show details tooltip
- [ ] Live tail toggle (auto-scroll new entries)
- [ ] "View all" link → Logs page

**Files:** `packages/ui/components/RecentLogsList.vue`
**Effort:** S
**Dependencies:** Task 13.1, Task 3.6 (request logging)
**Verify:** Logs hiển thị và auto-scroll

### Task 13.5: Implement WebSocket real-time updates

- [ ] Create `packages/ui/composables/useWebSocket.ts`
- [ ] Connect to `ws://localhost:8000/ws`
- [ ] Auto-reconnect on disconnect (exponential backoff)
- [ ] Event types: `proxy_rotated`, `rate_limit_detected`, `health_check_progress`, `proxy_status`, `stats_update`
- [ ] Update Pinia store on events
- [ ] Connection status indicator (connected/disconnected)

**Files:** `packages/ui/composables/useWebSocket.ts`
**Effort:** M
**Dependencies:** Task 2.3 (WS endpoint)
**Verify:** WebSocket kết nối, nhận events

### Task 13.6: Implement quick actions

- [ ] Start/Stop animation (pulse while transitioning)
- [ ] Rotate animation (spinning icon while rotating)
- [ ] Confirmation dialog for Stop (warning about active connections)
- [ ] Keyboard shortcuts (Space = toggle, R = rotate)

**Files:** `packages/ui/components/ProxyStatusCard.vue`
**Effort:** S
**Dependencies:** Task 13.2
**Verify:** Quick actions hoạt động mượt

### Task 13.7: Dashboard tests

- [ ] Tạo `tests/ui/test_dashboard.py` (hoặc Vitest spec files)
- [ ] Test ProxyStatusCard renders correct status (running/stopped)
- [ ] Test StatsGrid updates on WebSocket event
- [ ] Test Start/Stop toggle calls API
- [ ] Test Rotate button loading state
- [ ] Test empty state when proxy not started
- [ ] Test WebSocket reconnection on disconnect

**Files:** `tests/ui/test_dashboard.py`
**Effort:** M
**Dependencies:** Task 13.1–13.6
**Verify:** `pytest tests/ui/` (hoặc `vitest run`) passes

---

## US-014: Proxy Manager UI

### Task 14.1: Create ProxyManagerPage layout

- [ ] Create `packages/ui/components/ProxyManagerPage.vue`
- [ ] Tabs: All, HTTP, HTTPS, SOCKS5, Alive, Dead
- [ ] Search bar (filter by address, region, notes)
- [ ] Bulk actions toolbar (Test All, Delete Selected, Export Selected)
- [ ] Pagination (50 per page)
- [ ] Empty state: "No proxies yet. Add one or import from file."

**Files:** `packages/ui/components/ProxyManagerPage.vue`
**Effort:** M
**Dependencies:** Task 13.5 (useWebSocket), Task 4.3 (pool API)
**Verify:** Proxy manager page hiển thị

### Task 14.2: Implement ProxyTable

- [ ] Columns: Address, Protocol, Region, Status (alive/dead/untested), Latency, Last Check, Actions
- [ ] Sortable columns (click header to sort)
- [ ] Status indicators: green dot (alive), red dot (dead), grey dot (untested)
- [ ] Latency bar (visual indicator: green=fast, yellow=medium, red=slow)
- [ ] Checkbox column for bulk selection
- [ ] Inline remove button with confirmation
- [ ] Virtual scrolling cho 1000+ proxies

**Files:** `packages/ui/components/ProxyTable.vue`
**Effort:** M
**Dependencies:** Task 14.1
**Verify:** Table hiển thị proxies, sort được

### Task 14.3: Implement ProxyFormModal

- [ ] Modal form: Address (IP:port), Protocol (dropdown), Username, Password, Region, Notes
- [ ] Validation: IP format, port range, required fields
- [ ] Add mode (empty form) vs Edit mode (pre-filled)
- [ ] Test connection button within modal
- [ ] Save/Cancel buttons with loading state
- [ ] Keyboard: Enter to save, Escape to cancel

**Files:** `packages/ui/components/ProxyFormModal.vue`
**Effort:** M
**Dependencies:** Task 14.1, Task 4.3
**Verify:** Add/edit proxy hoạt động

### Task 14.4: Implement ImportPreviewModal

- [ ] File picker button (.txt, .csv)
- [ ] Preview table: parsed proxies before import
- [ ] Detect duplicates (highlighted)
- [ ] Column mapping for CSV (drag-drop field mapping)
- [ ] Import button with progress bar
- [ ] Result summary: "Imported: 50, Skipped: 3 (duplicates), Errors: 2"

**Files:** `packages/ui/components/ImportPreviewModal.vue`
**Effort:** M
**Dependencies:** Task 14.1, Task 5.3 (import API)
**Verify:** Import preview + confirm hoạt động

### Task 14.5: Implement Test All with progress

- [ ] Test All button → sequential test with progress bar
- [ ] Real-time status updates per proxy (via WebSocket)
- [ ] Cancel button (stop testing)
- [ ] Results: alive/dead count, avg latency
- [ ] Auto-sort: dead proxies moved to bottom

**Files:** `packages/ui/components/ProxyManagerPage.vue`
**Effort:** S
**Dependencies:** Task 14.1, Task 6.3, Task 13.5
**Verify:** Test All button hoạt động

### Task 14.6: Proxy Manager tests

- [ ] Tạo `tests/ui/test_proxy_manager.py` (hoặc Vitest spec files)
- [ ] Test ProxyTable renders proxy list correctly
- [ ] Test sort by column
- [ ] Test search/filter
- [ ] Test Add/Edit modal form validation
- [ ] Test delete confirmation dialog
- [ ] Test Import preview shows parsed data
- [ ] Test Test All progress bar

**Files:** `tests/ui/test_proxy_manager.py`
**Effort:** M
**Dependencies:** Task 14.1–14.5
**Verify:** `pytest tests/ui/` (hoặc `vitest run`) passes

---

## US-018: Logs & Monitoring

### Task 18.1: Create LogsPage layout

- [ ] Create `packages/ui/components/LogsPage.vue`
- [ ] Tabs: Request Logs, Rotation History
- [ ] Filter bar (sticky top)
- [ ] Log table with virtual scrolling
- [ ] Live tail mode toggle
- [ ] Export button

**Files:** `packages/ui/components/LogsPage.vue`
**Effort:** M
**Dependencies:** Task 13.5 (useWebSocket)
**Verify:** Logs page hiển thị

### Task 18.2: Implement LogFilterBar

- [ ] Date range picker (from/to)
- [ ] Method filter checkboxes (GET, POST, PUT, DELETE, CONNECT)
- [ ] Status code range (2xx, 3xx, 4xx, 5xx) or custom
- [ ] Proxy IP filter (dropdown from pool)
- [ ] URL search (text input)
- [ ] Rate limited only toggle
- [ ] Apply/Reset buttons
- [ ] Active filter badges (shows what's applied)

**Files:** `packages/ui/components/LogFilterBar.vue`
**Effort:** M
**Dependencies:** Task 18.1
**Verify:** Filters hoạt động

### Task 18.3: Implement LogTable

- [ ] Columns: Timestamp, Method, URL, Status, Proxy IP, Duration, Actions
- [ ] Virtual scrolling (only render visible rows)
- [ ] Colored status codes
- [ ] Duration bar (visual)
- [ ] Click row → detail panel (request headers, response headers, proxy used)
- [ ] Copy URL button
- [ ] Infinite scroll (load more as user scrolls)

**Files:** `packages/ui/components/LogTable.vue`
**Effort:** M
**Dependencies:** Task 18.1
**Verify:** Log table hiển thị, scroll được

### Task 18.4: Implement RotationHistoryTable

- [ ] Columns: Timestamp, Previous IP, New IP, Reason, Duration
- [ ] Reason badges: manual (blue), rate_limit (red), scheduled (green)
- [ ] Click row → details (proxy info, requests between rotations)
- [ ] Timeline mode (visual timeline of rotations)

**Files:** `packages/ui/components/RotationHistoryTable.vue`
**Effort:** S
**Dependencies:** Task 18.1
**Verify:** Rotation history hiển thị

### Task 18.5: Implement CSV export

- [ ] Export button → download filtered logs as CSV
- [ ] Loading state while generating
- [ ] Filename: `easyproxy-logs-YYYY-MM-DD.csv`
- [ ] Columns: timestamp, method, url, status_code, proxy_ip, duration_ms, rate_limited
- [ ] Server-side: stream large exports in chunks

**Files:** `packages/ui/components/LogsPage.vue`, `easyproxy/api/routes/logs.py`
**Effort:** S
**Dependencies:** Task 18.1
**Verify:** Export CSV thành công

### Task 18.6: Implement live tail toggle

- [ ] Toggle switch: Live Tail (on/off)
- [ ] When on: auto-append new logs via WebSocket, auto-scroll to bottom
- [ ] When off: show as-is, user scrolls manually
- [ ] Scroll lock indicator (user scrolled up → pause auto-scroll)
- [ ] "New logs below" button when auto-scroll paused

**Files:** `packages/ui/components/LogTable.vue`
**Effort:** S
**Dependencies:** Task 18.3, Task 13.5
**Verify:** Live tail hoạt động

### Task 18.7: Logs tests

- [ ] Tạo `tests/ui/test_logs.py` (hoặc Vitest spec files)
- [ ] Test LogTable renders with mock data
- [ ] Test filter bar: date range, method, status code
- [ ] Test CSV export downloads file with correct content
- [ ] Test live tail auto-scroll
- [ ] Test scroll lock behavior (user scrolled up → pause)
- [ ] Test rotation history table
- [ ] Test empty state (no logs yet)

**Files:** `tests/ui/test_logs.py`
**Effort:** M
**Dependencies:** Task 18.1–18.6
**Verify:** `pytest tests/ui/` (hoặc `vitest run`) passes

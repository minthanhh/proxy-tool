# EasyProxy — Tasks: Notification System

> Feature 9: US-019

---

## US-019: Notifications

### Task 19.1: Implement NotificationToast component (in-app)

- [ ] Create `packages/ui/components/NotificationToast.vue`
- [ ] Toast types: info, success, warning, error
- [ ] Auto-dismiss after configurable duration (default 5s)
- [ ] Stack multiple toasts (newest on top, max 5 visible)
- [ ] Animated enter/exit (slide in from right)
- [ ] Click to dismiss
- [ ] Accessibility: aria-live region
- [ ] Icons per type (checkmark, warning, error, info)

**Files:** `packages/ui/components/NotificationToast.vue`
**Effort:** S
**Dependencies:** Task 13.5 (useWebSocket)
**Verify:** Toast hiển thị khi nhận event

### Task 19.2: Implement Electron notification bridge

- [ ] Tạo `electron/notifications.js`
- [ ] Native OS notification: `new Notification(title, { body })`
- [ ] IPC handler: renderer → main process → OS notification
- [ ] Notification click → focus app window
- [ ] Do not show notifications when app is focused (use toast instead)
- [ ] Rate-limit notifications (max 1 per 5s, debounce)

**Files:** `electron/notifications.js`, `electron/preload.js`
**Effort:** S
**Dependencies:** Task 11.1
**Verify:** OS notification hiển thị khi app minimized

### Task 19.3: Implement notification triggers

- [ ] Wire notification events throughout the system:
  - Rate limit detected → "Rate limit detected on IP x.x.x.x. Rotating..."
  - Rotation completed → "IP rotated: x.x.x.x → y.y.y.y"
  - Proxy dead → "Proxy x.x.x.x is dead. Removed from pool."
  - Auto-start failed → "Failed to set system proxy. Manual config needed."
  - Backend crash → "Backend crashed. Restarting..."
- [ ] Configurable: which events trigger notifications (checkbox in Settings)
- [ ] Do not notify for scheduled rotation (noise)
- [ ] Group rapid events (3 rate limits in 10s → 1 notification)
- [ ] Log all notifications to DB (`notification_log` table)

**Files:** `electron/notifications.js`, `easyproxy/api/events.py`
**Effort:** M
**Dependencies:** Task 19.1, 19.2, Task 2.3 (events)
**Verify:** Sự kiện kích hoạt notification đúng

### Task 19.4: Implement notification preferences in Settings

- [ ] Settings section: "Notifications"
- [ ] Toggles per event type:
  - [x] Rate limit detected
  - [x] IP rotated
  - [x] Proxy pool changes
  - [x] System proxy changes
  - [x] Errors & crashes
- [ ] Toast duration slider (2s, 5s, 10s, persistent)
- [ ] Enable/disable native OS notifications vs in-app only

**Files:** `packages/ui/components/SettingsPage.vue` (or Settings modal)
**Effort:** S
**Dependencies:** Task 19.3
**Verify:** Settings changes affect notification behavior

### Task 19.5: Notification tests

- [ ] Tạo `tests/test_notifications.py`
- [ ] Test toast component rendering
- [ ] Test notification types and styling
- [ ] Test notification preferences

**Effort:** S
**Dependencies:** Task 19.1–19.4
**Verify:** `pytest` notification tests pass (UI tests via Playwright/Vitest nếu có)

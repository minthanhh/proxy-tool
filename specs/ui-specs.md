# EasyProxy — UI/UX Specification

## Design Principles

1. **Clean & minimal** — No clutter. Each screen has one primary purpose.
2. **Informative at a glance** — Status, stats, and controls visible without scrolling or clicking.
3. **Native feel** — System tray, native menus, OS-native notifications, dark/light theme matching system.
4. **Responsive** — Window resizes gracefully; minimum 800×600, default 1024×768.
5. **Progressive disclosure** — Advanced settings hidden behind expand/collapse; basic usage is 1-click.

## Color palette

| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| `--bg-primary` | `#FFFFFF` | `#1A1A2E` | Main background |
| `--bg-secondary` | `#F5F5F5` | `#16213E` | Card/sidebar background |
| `--text-primary` | `#1A1A2E` | `#E8E8E8` | Body text |
| `--text-secondary` | `#6B7280` | `#9CA3AF` | Muted text |
| `--accent` | `#3B82F6` | `#60A5FA` | Primary action, links |
| `--success` | `#10B981` | `#34D399` | Proxy alive, running |
| `--warning` | `#F59E0B` | `#FBBF24` | Degraded, warning |
| `--danger` | `#EF4444` | `#F87171` | Error, proxy dead |
| `--surface` | `#FFFFFF` | `#1E293B` | Card surface |

## Typography

- UI font: `Inter`, system sans-serif fallback
- Mono font: `JetBrains Mono`, `SF Mono`, `Cascadia Code`
- Body: 14px, headings: 16–24px, mono labels: 12px

---

## Screen Listing

### 1. Dashboard

**Layout:**
```
┌─────────────────────────────────────────────────────┐
│  ◉ Proxy Running    ─── [Stop]  [Rotate]  [⚙]     │
│  Current IP: 45.67.89.10 (US)                      │
├─────────────────┬─────────────────┬─────────────────┤
│  1,523          │  7              │  9               │
│  Requests Today  │  Rate Limits    │  Rotations       │
├─────────────────┴─────────────────┴─────────────────┤
│ ┌─ Request Timeline ─────────────────────────┐      │
│ │ ████████████████████░░░░░░░░░░░░░░░        │      │
│ │ 15:30    16:00    16:30    17:00           │      │
│ └────────────────────────────────────────────┘      │
│ ┌─ Recent Logs ────────────────────────────┐        │
│ │ 17:00 GET /data 200 340ms 45.67.89.10   │        │
│ │ 16:59 POST /api 429 1200ms 45.67.89.10  │        │
│ │ 16:59 GET /data 200 230ms 98.76.54.32   │ ← rot  │
│ └────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────┘
```

**Elements:**
- **Status bar:** Large indicator dot (green=running, grey=stopped), current proxy IP + country flag emoji
- **Action buttons:** Start/Stop (toggle), Rotate (with spinning icon during rotation), Settings gear
- **Stats cards:** 3-column grid — Requests Today, Rate Limits Detected, Rotations Performed
- **Request timeline:** Mini bar chart showing request volume over last hour
- **Recent logs:** Last 5 log entries, auto-scrolling, color-coded by status (200=green, 429=red, 4xx=yellow)

### 2. Proxy Manager

**Layout:**
```
┌──────────────────────────────────────────────────────────────┐
│  Proxy Pool  [Add] [Import] [Test All]  [🔍 filter...]      │
├──────┬────────┬──────┬────────┬──────┬──────┬──────┬────────┤
│ IP   │ Port   │ Prot │ Region │Stat  │Lat   │Req   │ Actions│
├──────┼────────┼──────┼────────┼──────┼──────┼──────┼────────┤
│45.67│ 3128   │ HTTP │ 🇺🇸 US │ ●    │230ms │45    │ ✎ 🗑    │
│89.10│        │      │        │alive │      │      │        │
│98.76│ 8080   │ HTTP │ 🇩🇪 DE │ ●    │180ms │12    │ ✎ 🗑    │
│54.32│        │      │        │alive │      │      │        │
│12.34│ 1080   │SOCKS5│ 🇬🇧 GB │ ○    │─     │0     │ ✎ 🗑    │
│56.78│        │      │        │dead  │      │      │        │
├──────┴────────┴──────┴────────┴──────┴──────┴──────┴────────┤
│  Showing 3 of 100  ← 1 2 3 ... 34 →                        │
└──────────────────────────────────────────────────────────────┘
```

**Elements:**
- **Toolbar:** Add button (modal form), Import button (file picker), Test All button, search input
- **Table:** Virtual scrolling for large pools (1000+), sortable columns
- **Row actions:** Edit (inline or modal), Delete (with confirmation)
- **Status indicator:** Green dot = alive, grey dot = dead, yellow dot = untested
- **Bulk select:** Checkbox per row, batch delete/test
- **Pagination:** Page controls at bottom

**Add/Edit Proxy Modal:**
```
┌─ Add Proxy ─────────────────────────────────┐
│ Address:  [___________________________]      │
│ Port:     [________]  Protocol: [HTTP ▼]     │
│ Username: [________]  Password: [________]   │
│ Region:   [________]  (optional)             │
│                                              │
│  [Test]  [Cancel]  [Add]                     │
└──────────────────────────────────────────────┘
```

### 3. Residential Config

**Layout:**
```
┌──────────────────────────────────────────────────────┐
│  Residential Proxy Configuration                     │
├──────────────────────────────────────────────────────┤
│  Provider: [BrightData ▼]                            │
│  API Key:  [● ● ● ● ● ● ● ● ● ●]  [Verify]         │
│  Zone:     [Residential Static ▼]                    │
│  Country:  [Auto ▼]                                  │
│                                                      │
│  ┌─ Connection Status ──────────────────────┐        │
│  │  ● Connected                              │        │
│  │  Pool: 42 active IPs out of 50            │        │
│  │  Expires: 2026-07-14                      │        │
│  │  Last refresh: 5 min ago                  │        │
│  │                                           │        │
│  │  [Refresh Now]    [Disconnect]            │        │
│  └───────────────────────────────────────────┘        │
└──────────────────────────────────────────────────────┘
```

**Elements:**
- **Provider dropdown:** BrightData, Oxylabs, Smartproxy, Custom
- **API Key input:** Masked with toggle visibility
- **Zone/Country:** Provider-specific options
- **Connection status card:** Green/red indicator, pool stats, expiry
- **Actions:** Refresh Now, Disconnect

### 4. Settings

**Layout:**
```
┌─ General ─────────────────────────────────────────────┐
│  ☑ Auto-start with system                             │
│  ☑ Minimize to tray on close                          │
│  Theme: [System ▼]                                    │
├─ Proxy ───────────────────────────────────────────────┤
│  Port: [8080]  Bind: [127.0.0.1]                      │
│  ☑ Auto-configure system proxy                        │
├─ Rotation ────────────────────────────────────────────┤
│  Strategy: [Round Robin ▼]                            │
│  ☑ Auto-rotate on 429                                 │
│  ☐ Schedule rotation  Every: [10] minutes             │
│  Max retry attempts: [3]                              │
├─ Sticky Session ──────────────────────────────────────┤
│  ☑ Enable sticky session                              │
│  TTL: [300] seconds                                   │
│  ☑ Reset on error                                     │
├─ Health Check ────────────────────────────────────────┤
│  Interval: [60] seconds                               │
│  Test URL: [http://httpbin.org/ip]                    │
│  Timeout: [10] seconds                                │
├─ Logs ────────────────────────────────────────────────┤
│  Max entries: [10000]                                 │
│  Log level: [Info ▼]                                  │
└──────────────────────────────────────────────────────┘
```

**Elements:**
- Categorized sections with collapsible headers
- All changes saved immediately (no "Save" button — auto-save on change)
- Tooltip descriptions on hover for technical settings
- Reset to defaults link at bottom

### 5. Logs

**Layout:**
```
┌─ Request Logs ───────────────────────────────────────────────┐
│  [📥 Export CSV]  [🗑 Clear]                                   │
│  From: [2026-06-13]  To: [2026-06-14]                        │
│  Method: [All ▼]  Status: [All ▼]  Proxy: [All ▼]  [Apply]  │
├──────┬───────┬──────────────────┬──────┬───────┬──────┬───────┤
│ Time │Method │ URL              │Status│Proxy  │Dur   │Rot?  │
├──────┼───────┼──────────────────┼──────┼───────┼──────┼───────┤
│17:00 │ GET   │/api/data         │ 200  │45...  │340ms │       │
│16:59 │ POST  │/api/submit       │ 429  │45...  │1200ms│ 🔄    │
│16:59 │ GET   │/api/data         │ 200  │98...  │230ms │ 🔄    │
├──────┴───────┴──────────────────┴──────┴───────┴──────┴───────┤
│  ← 1 2 3 ... 50 →   Showing 100 of 5000 entries              │
└───────────────────────────────────────────────────────────────┘
```

**Rotation History Tab:**
```
├─ Rotation History ───────────────────────────────────────────┐
│──────┬──────────┬──────────┬─────────┬──────────┬───────────┤
│ Time │ Reason   │ From     │ To      │ Request  │ Success  │
│──────┼──────────┼──────────┼─────────┼──────────┼───────────┤
│17:00 │ 429      │45.67.89.│98.76.54.│/api/sbm  │ ✓         │
│      │          │10       │32       │          │           │
│15:30 │ Scheduled│12.34.56.│45.67.89.│─         │ ✓         │
│      │          │78       │10       │          │           │
│──────┴──────────┴──────────┴─────────┴──────────┴───────────┤
```

**Elements:**
- **Tabs:** Request Logs | Rotation History
- **Filter bar:** Date range picker, method/status/proxy dropdowns
- **Virtual scrolling table:** Sortable, resizable columns
- **Rotation indicator:** Icon on rows that triggered rotation
- **Export:** CSV download of current filtered view
- **Live tail:** Auto-scroll toggle at bottom (follow new logs)

---

## User Flows

### Flow 1: Start proxy → browse normally

```
1. User launches EasyProxy
2. Dashboard shows "Proxy Stopped" with grey indicator
3. User clicks [Start]
   → Button shows spinner → turns green → "Proxy Running"
   → System proxy configured automatically
   → Current IP displayed
   → Stats reset (new session)
4. User opens browser → opens websites
   → All traffic flows through EasyProxy
   → Request count increases in real-time
   → Logs appear in real-time
5. User clicks [Stop] when done
   → System proxy restored to original
   → Status turns grey
```

### Flow 2: Rate limit detected → auto-rotate

```
1. User is browsing normally (proxy running)
2. Backend detects HTTP 429 from upstream
3. Notification popup: "Rate limit detected! Rotating IP..."
4. Dashboard: rate limit count +1, rotation count +1
5. Current IP changes within 1-2 seconds
6. Failed request is retried automatically with new IP
7. Notification: "Rotated to 98.76.54.32 — retry successful ✅"
8. Rotation log entry created
```

### Flow 3: Add proxy → test

```
1. User navigates to Proxy Manager
2. Clicks [Add]
3. Fills form: address, port, protocol, optional auth
4. Clicks [Test] → spinner → "Alive (230ms)" or "Connection failed"
5. Clicks [Add] → proxy appears in table with status
```

### Flow 4: Import proxy list

```
1. User goes to Proxy Manager → [Import]
2. File picker dialog opens (accepts .txt, .csv)
3. User selects file
4. Preview modal: "Found 52 proxies. 50 valid, 2 invalid"
5. User confirms → proxies imported into pool
6. Optional: select "Test all after import"
   → Test All runs automatically
   → Statuses updated in table
```

---

## Component Tree

```
App.vue
├── Sidebar.vue
│   ├── NavItem.vue (Dashboard, Proxy Manager, Residential, Settings, Logs)
│   └── ProxyStatusBadge.vue
├── TopBar.vue
│   ├── CurrentIPDisplay.vue
│   ├── QuickActions.vue (Start/Stop, Rotate)
│   └── ThemeToggle.vue
└── PageContent.vue (dynamic, based on route)
    ├── DashboardPage.vue
    │   ├── ProxyStatusCard.vue
    │   ├── StatsGrid.vue
    │   │   └── StatCard.vue (×3)
    │   ├── RequestTimelineChart.vue
    │   └── RecentLogsList.vue
    ├── ProxyManagerPage.vue
    │   ├── ProxyToolbar.vue (Add, Import, Test All, Search)
    │   ├── ProxyTable.vue
    │   │   └── ProxyRow.vue (×N)
    │   ├── ProxyFormModal.vue (Add/Edit)
    │   └── ImportPreviewModal.vue
    ├── ResidentialConfigPage.vue
    │   ├── ProviderSelector.vue
    │   ├── ApiKeyInput.vue
    │   └── ConnectionStatusCard.vue
    ├── SettingsPage.vue
    │   ├── SettingsSection.vue (×6)
    │   │   └── SettingsRow.vue (toggle, input, select, ...)
    │   └── ResetToDefaults.vue
    └── LogsPage.vue
        ├── LogFilterBar.vue
        ├── LogTable.vue
        │   └── LogRow.vue (×N)
        ├── RotationHistoryTable.vue
        │   └── RotationRow.vue (×N)
        └── ExportButton.vue
```

## State management (Pinia stores)

| Store | State | Purpose |
|-------|-------|---------|
| `useProxyStore` | running, port, currentIp, currentProxyId, uptime | Proxy engine status |
| `usePoolStore` | proxies[], total, alive, dead, loading | Proxy pool CRUD |
| `useResidentialStore` | provider, apiKey, connected, activeIps | Residential config |
| `useSettingsStore` | all settings (nested) | App settings |
| `useLogStore` | logs[], rotations[], filters | Log viewing |
| `useStatsStore` | requestsToday, rateLimits, rotations, timeline | Dashboard stats |
| `useNotificationStore` | notifications[] | Toast/notification queue |
| `useThemeStore` | theme ('light' | 'dark' | 'system') | Theme management |

## Notifications

| Type | Trigger | Behavior |
|------|---------|----------|
| Success toast | Proxy started/stopped, rotation success | Green, auto-dismiss 3s |
| Warning toast | Rate limit detected, proxy dead | Yellow, auto-dismiss 5s |
| Error toast | Proxy crash, config error | Red, persistent until dismissed |
| OS notification | Rate limit detected (when minimized) | Native OS notification |
| Tray balloon | Rotation completed (when minimized) | Tray balloon message |

## Empty states

| Screen | Empty state message | Action CTA |
|--------|-------------------|------------|
| Proxy Manager | "No proxies yet. Add one or import a file to get started." | [Add Proxy] [Import] |
| Residential Config | "Connect a residential proxy provider for dynamic IPs." | [Configure] |
| Logs | "No logs yet. Start the proxy to begin logging." | [Start Proxy] |
| Dashboard stats | "Start the proxy to see your stats." | [Start] |

# EasyProxy — Tasks: CLI Mode

> Feature 8: US-017

---

## US-017: CLI Mode

### Task 17.1: Implement `easyproxy start/stop` commands

- [ ] Tạo `easyproxy/cli/proxy.py` — proxy management commands
- [ ] `start`:
  - Start FastAPI backend in background (if not running)
  - Start proxy engine on port 8080
  - Set system proxy (optional flag `--system-proxy`)
  - Print current IP
- [ ] `stop`:
  - Stop proxy engine gracefully (wait for in-flight requests)
  - Restore system proxy settings
  - Optional: stop backend too (`--all`)
- [ ] `restart`:
  - Stop + start sequence
- [ ] PID file management (`~/.easyproxy/easyproxy.pid`)

**Files:** `easyproxy/cli/proxy.py`
**Effort:** M
**Dependencies:** Task 2.1, Task 3.1
**Verify:** `easyproxy start` → proxy running, `easyproxy stop` → stopped

### Task 17.2: Implement `easyproxy status` command

- [ ] Tạo `easyproxy/cli/status.py`
- [ ] Print: proxy status (running/stopped), current IP, uptime
- [ ] Print: pool stats (total/alive/dead/residential)
- [ ] Print: rotation history (last 5)
- [ ] Pretty table output (tabulate or rich)
- [ ] `--json` flag for machine-readable output
- [ ] Exit code: 0 if running, 1 if stopped

**Files:** `easyproxy/cli/status.py`
**Effort:** S
**Dependencies:** Task 2.1 (health API)
**Verify:** `easyproxy status` prints info

### Task 17.3: Implement `easyproxy pool` subcommands

- [ ] Tạo `easyproxy/cli/pool.py` — pool management commands
- [ ] `pool list` — table of proxies (flags: `--alive`, `--dead`, `--protocol`)
- [ ] `pool add <ip:port>` — add single proxy
- [ ] `pool remove <id>` — remove by ID
- [ ] `pool import <file>` — import from file
- [ ] `pool export <file>` — export to file
- [ ] `pool test` — test all proxies
- [ ] `pool stats` — pool statistics

**Files:** `easyproxy/cli/pool.py`
**Effort:** M
**Dependencies:** Task 4.3 (pool API)
**Verify:** `easyproxy pool list` shows proxies

### Task 17.4: Implement `easyproxy rotate` command

- [ ] Tạo `easyproxy/cli/rotate.py`
- [ ] `rotate` — trigger manual rotation
- [ ] Print: previous IP → new IP
- [ ] `rotate --strategy round-robin|random|low-latency`
- [ ] `rotate --scheduled` — enable/disable scheduled rotation
- [ ] `rotate --interval <minutes>` — set rotation interval

**Files:** `easyproxy/cli/rotate.py`
**Effort:** S
**Dependencies:** Task 7.2 (rotation API)
**Verify:** `easyproxy rotate` changes IP

### Task 17.5: Implement `easyproxy logs` command

- [ ] Tạo `easyproxy/cli/logs.py`
- [ ] `logs` — tail last N request logs (default 10, flag: `--tail 50`)
- [ ] `logs --follow` — follow mode (like `tail -f`)
- [ ] `logs --export <file>` — export to CSV
- [ ] `logs rotation` — show rotation history
- [ ] Filter flags: `--method`, `--status`, `--proxy`, `--since`, `--until`

**Files:** `easyproxy/cli/logs.py`
**Effort:** M
**Dependencies:** Task 18.5 (logs API)
**Verify:** `easyproxy logs` shows logs

### Task 17.6: CLI tests

- [ ] Tạo `tests/test_cli.py`
- [ ] Test start/stop commands (mock backend)
- [ ] Test status command
- [ ] Test pool subcommands
- [ ] Test rotate command
- [ ] Test logs command

**Files:** `tests/test_cli.py`
**Effort:** M
**Dependencies:** Task 17.1–17.5
**Verify:** `pytest tests/test_cli.py` passes

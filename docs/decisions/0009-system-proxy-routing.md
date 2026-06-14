# 0009 System-wide Proxy Routing

Date: 2026-06-14

## Status

accepted

## Context

EasyProxy cần cơ chế routing để đưa traffic qua proxy rotation. Các lựa chọn:

1. **System-wide proxy** — cài đặt proxy ở cấp hệ thống (OS network settings)
2. **Per-app routing** — chọn app nào qua proxy (giống Proxifier)
3. **Local forward proxy** — chạy local proxy server, user tự cấu hình từng app
4. **VPN tunnel** — tạo virtual network interface

## Decision

**System-wide HTTP forward proxy** — EasyProxy chạy HTTP forward proxy trên localhost:8080 và tự động cài đặt system proxy settings.

## Rationale

1. **Đơn giản nhất cho user** — bật EasyProxy là xong, không cần cấu hình từng app
2. **Hỗ trợ mọi ứng dụng** — browser, API client, curl, package manager đều tự động qua proxy
3. **Dễ implement** — macOS `networksetup`, Windows registry, Linux env var
4. **Dễ kiểm soát** — bật/tắt nhanh qua system tray

## Cơ chế hoạt động

```
User click "Start" → FastAPI sets system proxy → localhost:8080
                        ↓
All system traffic → EasyProxy proxy server → Rotation Engine → Internet
```

## Platform-specific

| Platform | Command |
|---|---|
| macOS | `networksetup -setwebproxy Wi-Fi localhost 8080` |
| Windows | `netsh winhttp set proxy localhost:8080` |
| Linux | `export http_proxy=http://localhost:8080` (hoặc GNOME/KDE settings) |

## Consequences

- Không thể route chọn lọc theo app (tất cả đều qua proxy)
- Cần handle HTTPS qua CONNECT method
- User cần admin/root để thay đổi system proxy settings
- Cần cleanup system proxy khi tắt EasyProxy

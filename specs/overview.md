# EasyProxy — Tổng quan sản phẩm

## Vision & Mission

**Tầm nhìn:** Trở thành công cụ proxy desktop miễn phí, dễ sử dụng nhất cho developers và người dùng phổ thông — ai cũng có thể luân chuyển IP chỉ với một cú click. **Sứ mệnh:** Loại bỏ rào cản kỹ thuật và chi phí khi sử dụng proxy; biện pháp chống rate limit trở nên đơn giản như bật/tắt công tắc.

## Problem statement

Khi gọi API hoặc crawl dữ liệu từ các dịch vụ web (Google, Facebook, TikTok, e-commerce sites), người dùng thường xuyên gặp HTTP 429 (Too Many Requests) và bị chặn tạm thời. Các giải pháp hiện tại:

- **VPN:** Thay đổi IP nhưng không linh hoạt, không kiểm soát được từng request, thường chậm.
- **Proxy services trả phí:** Oxylabs, BrightData, Smartproxy — chất lượng tốt nhưng đắt ($15–$500/tháng), cấu hình phức tạp.
- **Tự xây dựng proxy:** Cần kiến thức kỹ thuật cao, tốn thời gian vận hành, maintain.

EasyProxy giải quyết vấn đề này bằng một desktop app local: chạy system-wide HTTP forward proxy, tự động phát hiện HTTP 429 và rotate IP mà không cần can thiệp thủ công. Người dùng chỉ cần cung cấp danh sách proxy (hoặc dùng residential proxy network), EasyProxy lo phần còn lại.

## Target users

1. **Developers** — Lập trình viên cần crawl dữ liệu, test API, bypass rate limit khi phát triển ứng dụng. Cần kiểm soát chi tiết, xem logs, cấu hình rotation strategy.
2. **General users** — Người dùng phổ thông muốn truy cập web bị giới hạn theo vùng hoặc tránh bị chặn khi dùng tự động. Cần giao diện đơn giản, bật/tắt dễ dàng.

## Core features

| Tính năng | Mô tả |
|-----------|-------|
| **HTTP forward proxy** | Chạy local proxy server trên port 8080, hỗ trợ HTTP & HTTPS (CONNECT tunnel) |
| **Tự động rotate IP** | Khi phát hiện HTTP 429, tự động chọn IP mới từ pool và retry |
| **Rate limit detection** | Parse response headers, phát hiện 429 và Retry-After |
| **Static proxy pool** | Thêm proxy tĩnh (HTTP/HTTPS/SOCKS5) thủ công hoặc import từ file |
| **Residential proxy** | Tích hợp mạng lưới residential proxy từ các provider (BrightData, Oxylabs, ...) |
| **Desktop UI** | Electron app với giao diện Nuxt 3 — dashboard, proxy manager, logs |
| **System tray** | Icon khay hệ thống, quick actions (start/stop, rotate), notification |
| **System proxy config** | Tự động cấu hình proxy system-wide trên Windows/macOS/Linux |
| **CLI mode** | Chạy backend ở chế độ CLI không cần Electron |
| **Request logs** | Ghi log tất cả request, rotation history, export CSV |
| **Sticky session** | Giữ nguyên IP cho cùng domain trong khoảng thời gian cấu hình |
| **Scheduled rotation** | Rotate IP theo lịch định kỳ (mỗi N phút / giờ) |
| **Auto-start** | Khởi động cùng hệ thống |

## Non-goals

EasyProxy **không** phải là:

- **VPN client** — Không mã hóa toàn bộ traffic; chỉ định tuyến HTTP/HTTPS.
- **Proxy service** — Không bán proxy; người dùng tự cung cấp proxy của họ hoặc dùng residential service.
- **Web scraping framework** — Không crawl, parse, hay extract dữ liệu; chỉ rotate IP để hỗ trợ các công cụ khác.
- **Load balancer** — Không cân bằng tải giữa nhiều upstream servers.
- **Ad blocker / content filter** — Không chặn quảng cáo hay lọc nội dung.
- **Cloud service** — Chạy local 100%; không có cloud backend riêng.

## Success metrics

| Metric | Target | Cách đo |
|--------|--------|---------|
| Proxy uptime | >99% | Requests served / total requests |
| Auto-rotate success | >95% | Retry thành công sau 429 / total 429 |
| Rotation latency | <500ms | Thời gian từ 429 → request mới với IP khác |
| Request overhead | <100ms | Độ trễ thêm so với direct connection |
| Residential pool health | >90% IP alive | Tỷ lệ IP trong pool hoạt động |
| User satisfaction | NPS >40 | Survey người dùng |

## Key differentiators

1. **Free & open-source** — Không mất phí, không giới hạn số lượng proxy.
2. **Local first** — Chạy hoàn toàn trên máy người dùng, không gửi dữ liệu ra ngoài.
3. **Auto-detect & auto-rotate** — Không cần cấu hình rule; tự động phát hiện rate limit.
4. **System-wide** — Chỉ cần bật app, không cần cấu hình từng ứng dụng (tự động set system proxy).
5. **Dual UI** — Giao diện đồ họa đầy đủ + CLI cho advanced users.
6. **Plug-in residential** — Dễ dàng kết nối với bất kỳ residential proxy provider nào.
7. **Sticky session thông minh** — Tự động giữ IP cho session cần consistency.

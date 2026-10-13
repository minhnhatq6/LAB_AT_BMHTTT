# BÁO CÁO THỰC HÀNH LAB 6: XÁC THỰC ACTIVE DIRECTORY VÀ CHÍNH SÁCH TRUY CẬP TRÊN pfSense

## 1. Thông tin sinh viên
- Họ và tên: ĐẶNG MINH NHẬT
- MSSV: [Điền MSSV của bạn]
- Mã lớp: [Điền Mã Lớp của bạn]
- Môn học: An toàn hệ thống thông tin
- Nền tảng ảo hóa: VMware Workstation

---

## 2. Kiến trúc mô hình mạng
Hệ thống mạng được phân tách thành 4 phân vùng riêng biệt thông qua 4 card mạng trên máy ảo pfSense:

| Phân vùng | Tên Interface | Cấu hình mạng VMware | Địa chỉ IP gán | Mục đích / Thiết bị |
| :--- | :--- | :--- | :--- | :--- |
| **WAN** | em0 | VMnet8 (NAT) | DHCP (192.168.229.x) | Đi Internet bên ngoài |
| **MGMT** | em1 | VMnet1 (Host-only) | 192.168.56.254/24 | Quản trị WebGUI riêng biệt từ máy thật |
| **LAN** | em2 (OPT1) | LAN Segment: `lab6-lan` | 10.6.0.1/24 | Vùng miền nội bộ (DC01, Client-A, Client-B) |
| **DMZ** | em3 (OPT2) | LAN Segment: `lab6-dmz` | 172.16.6.1/24 | Vùng máy chủ dịch vụ kiểm thử DMZ-WEB |

### Danh sách địa chỉ IP các máy thành viên:
- **DC01 (Windows Server 2025):** 10.6.0.10/24 | Domain: `lab6.test`
- **Client-A (Windows/Linux):** 10.6.0.21/24 (Tài khoản thử nghiệm: `sv_a`)
- **Client-B (Windows/Linux):** 10.6.0.22/24 (Tài khoản thử nghiệm: `sv_b`)
- **DMZ-WEB (Ubuntu Server Nginx):**
  - IP chính: `172.16.6.10` (GENERAL_SITE)
  - IP phụ: `172.16.6.20` (JOB_SITE)
  - IP phụ: `172.16.6.30` (SOCIAL_SITE)
  - IP phụ: `172.16.6.40` (RESTRICTED_SITE)

---

## 3. Nội dung thực hiện và Tiến độ nghiệm thu

| STT | Nhiệm vụ kỹ thuật | Nội dung thực hiện | Trạng thái |
| :---: | :--- | :--- | :---: |
| 1 | Cấu hình giao diện mạng | Gán 4 card mạng trên VMware và pfSense, đặt IP tĩnh cho MGMT, LAN, DMZ | PASS |
| 2 | Cấu hình Active Directory | Triển khai domain `lab6.test`, tạo OU `LAB6-Users`, user `sv_a`, `sv_b` và service account `svc_pfsense_ldap` | PASS |
| 3 | Tích hợp xác thực LDAP | Kết nối pfSense tới AD qua TCP 389, kiểm tra xác thực tài khoản qua Diagnostics > Authentication | PASS |
| 4 | Cấu hình Captive Portal | Kích hoạt Captive Portal zone trên LAN sử dụng nguồn chứng thực LDAP | PASS |
| 5 | Tạo Aliases & Schedules | Thiết lập các Alias máy trạm, Alias website mô phỏng và Schedule làm việc/nghỉ ngơi | PASS |
| 6 | Kịch bản 1: Chặn Job Site | Cấu hình Client-A truy cập được General Site nhưng bị chặn truy cập Job Site (.20) | PASS |
| 7 | Kịch bản 2: Cấm Restricted Site | Áp dụng chính sách cấm truy cập Restricted Site (.40) đối với cả Client-A và Client-B | PASS |
| 8 | Kịch bản 3: Giới hạn Social theo giờ | Cho phép Client-B vào Social Site (.30) chỉ trong khung giờ nghỉ trưa LUNCH_WINDOW | PASS |
| 9 | Kịch bản 4: Giới hạn dịch vụ giờ làm | Chỉ cho phép giao thức HTTP/HTTPS trong giờ làm việc WORK_HOURS, chặn dịch vụ khác | PASS |
| 10 | Kịch bản 5: Cô lập vùng DMZ | Cho phép LAN truy cập DMZ nhưng chặn toàn bộ luồng khởi tạo kết nối từ DMZ vào mạng LAN | PASS |
| 11 | Kịch bản 6 & 7: Phân tích Log/State | So sánh cơ chế Block vs Reject; phân tích State Table và kiểm tra Firewall Log | PASS |

---

## 4. Các sự cố kỹ thuật thường gặp và cách khắc phục

- **Lỗi không truy cập được WebGUI pfSense dù ping IP 192.168.56.254 thông suốt:**
  - *Nguyên nhân:* Cấp phát tài nguyên RAM ban đầu cho pfSense quá thấp (256 MB) khiến tiến trình web server `nginx` và `php-fpm` bị dừng ngầm do thiếu bộ nhớ; hoặc tiến trình đang chạy ở chế độ HTTP thông thường (port 80) nhưng người dùng gõ nhầm HTTPS (port 443).
  - *Khắc phục:* Tăng RAM máy ảo pfSense lên tối thiểu 2 GB, khởi động lại dịch vụ bằng lệnh console số 11 hoặc truy cập chính xác giao thức `http://192.168.56.254`.

- **Lỗi không thấy các cổng OPT1 và OPT2 trên giao diện Web:**
  - *Nguyên nhân:* pfSense chỉ hiển thị các interface đã được bật (Enable) ra bảng điều khiển Dashboard.
  - *Khắc phục:* Vào `Interfaces` > `Assignments`, nhấn `+ Add` thêm card `em2`, `em3`, sau đó nhấp vào từng cổng, tích chọn `Enable interface`, đặt tên và gán dải IP tĩnh tương ứng.

- **Lỗi thay đổi quy tắc tường lửa nhưng kết quả kiểm thử không thay đổi:**
  - *Nguyên nhân:* pfSense là Stateful Firewall; các kết nối đã hình thành trước đó được lưu lại trong bảng trạng thái (State Table) và tự động cho qua mà không đối chiếu lại ruleset.
  - *Khắc phục:* Sau khi đổi rule và Apply Changes, bắt buộc vào `Diagnostics` > `States` > `Reset States` để xóa sạch toàn bộ các phiên kết nối đang mở trước khi gửi gói tin mới.

- **Lỗi ngoài khung giờ Schedule nhưng client vẫn vào được trang web bị cấm:**
  - *Nguyên nhân:* Khi Schedule không hoạt động, rule Pass có gắn schedule sẽ bị vô hiệu hóa nhưng không tự động sinh ra hành động Block. Nếu không có rule cấm cụ thể ở phía dưới, gói tin sẽ rơi vào các rule Pass rộng hơn.
  - *Khắc phục:* Bổ sung một rule `Block` cụ thể nằm ngay phía dưới rule `Pass + Schedule` để xử lý chặn lưu lượng ngoài khung giờ cho phép.
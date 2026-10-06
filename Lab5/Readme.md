# BÁO CÁO THỰC HÀNH: THIẾT LẬP MÔ HÌNH TƯỜNG LỬA pfSense

## 1. Thông tin sinh viên
- Họ và tên: ĐẶNG MINH NHẬT
- MSSV: 1150080029
- Mã lớp: 11DHCNPM1
- Tên bài Lab: Thiết lập mô hình tường lửa pfSense (pfSense Firewall Configuration)
- Nền tảng ảo hóa: VMware Workstation / Oracle VM VirtualBox
- Phiên bản hệ điều hành máy trạm: Windows 10 x64

---

## 2. Mô hình mạng và phân bổ IP
- Mô hình mạng 3 vùng cách ly:
  - Vùng WAN: Nhận IP tự động qua DHCP/Bridged từ hạ tầng mạng bên ngoài.
  - Vùng LAN (10.0.0.0/8): Chứa Domain Controller (10.0.0.2) và máy quản trị (10.0.0.100).
  - Vùng DMZ (172.16.0.0/16): Chứa máy chủ dịch vụ Web/IIS (172.16.0.2).
- Bảng thông số cấu hình giao diện mạng:

| Thiết bị | Interface | Địa chỉ IP | Subnet Mask | Gateway | DNS Server |
| :--- | :--- | :--- | :--- | :--- | :--- |
| pfSense | WAN | DHCP | Tự động | Tự động | Upstream DNS |
| pfSense | LAN | 10.0.0.1 | 255.0.0.0 (/8) | Không | Không |
| pfSense | DMZ (OPT1) | 172.16.0.1 | 255.255.0.0 (/16) | Không | Không |
| Domain Controller | LAN | 10.0.0.2 | 255.0.0.0 (/8) | 10.0.0.1 | 10.0.0.2 (Forwarder: 8.8.8.8) |
| Máy thật (Host LAN) | LAN (Host-Only) | 10.0.0.100 | 255.0.0.0 (/8) | Không đặt | Không đặt |
| DMZ-Web | DMZ | 172.16.0.2 | 255.255.0.0 (/16) | 172.16.0.1 | 8.8.8.8 |
| LAN-Test | LAN | 10.0.0.3 | 255.0.0.0 (/8) | 10.0.0.1 | 8.8.8.8 |

---

## 3. Các nội dung thực hiện & Kết quả nghiệm thu

| Nội dung | Kịch bản triển khai | Kết quả |
| :--- | :--- | :---: |
| Mục 1 - 3 | Chuẩn bị VM pfSense 3 card mạng, cài đặt ZFS, đổi IP LAN console 10.0.0.1/8 | PASS |
| Mục 4 | Cấu hình IP tĩnh cho Domain Controller, cài vai trò AD DS, Forest vietnam.local và DNS Forwarder | PASS |
| Mục 5 | Thiết lập card Host-Only máy thật 10.0.0.100/8, truy cập WebGUI 10.0.0.1 và hoàn thành Setup Wizard | PASS |
| Mục 6 | Gán card thứ ba cho DMZ (OPT1) 172.16.0.1/16, triển khai VM DMZ-Web cài đặt IIS | PASS |
| Mục 7 | Cấu hình Outbound NAT chế độ Hybrid/Automatic, xác nhận NAT rules tự sinh cho LAN và DMZ | PASS |
| Mục 8 & 9 | Disable Default Allow LAN rules, tạo rule nền tảng do sinh viên quản lý và xác thực tính năng Reset States | PASS |
| Tình huống 1 | Chặn gói tin ICMP (ping 8.8.8.8 Fail) nhưng vẫn cho phép phân giải DNS và duyệt Web HTTP/HTTPS | PASS |
| Tình huống 2 | Cấu hình Firewall chỉ cho phép IP 10.0.0.2 ra ngoài Internet; chặn toàn bộ các IP còn lại trong LAN | PASS |
| Tình huống 3 | Cô lập DMZ khỏi LAN: Thực nghiệm baseline thông suốt, sau đó thêm rule chặn DMZ net -> LAN net | PASS |
| Tình huống 4 | Cấu hình Port Forward WAN:8080 trỏ về DMZ Web Server:80 và kiểm tra truy cập từ máy thật | PASS |
| Tình huống 5 | Bật tính năng ghi nhật ký trên các rule Block và đọc phân tích Firewall Log trên pfSense | PASS |

---

## 4. Lỗi gặp phải và cách khắc phục

- Lỗi không chọn được ổ đĩa khi cài đặt pfSense (ZFS Configuration):
  - Nguyên nhân: Tại bước ZFS stripe configuration, người dùng chưa dùng phím Spacebar để đánh dấu chọn ổ đĩa ảo da0, dẫn đến thông báo lỗi stripe: Not enough disks selected. (0 < 1 minimum).
  - Khắc phục: Nhấn Enter vào Change Selection, chọn kiểu Stripe, sử dụng phím Spacebar để đánh dấu [*] da0 trước khi nhấn OK và tiếp tục cài đặt.

- Lỗi xung đột mạng WAN và LAN trên VirtualBox/VMware:
  - Nguyên nhân: Sử dụng dải NAT mặc định (10.0.2.0/24) trên card WAN khiến dải này nằm trùng bên trong mạng LAN (10.0.0.0/8).
  - Khắc phục: Chuyển card WAN sang chế độ Bridged hoặc tạo một dải NAT Network riêng biệt (192.168.250.0/24) không chồng lấn với 10.0.0.0/8 và 172.16.0.0/16.

- Lỗi tắt rule firewall nhưng máy client vẫn tiếp tục truy cập được Internet:
  - Nguyên nhân: pfSense là tường lửa kiểm soát theo trạng thái (Stateful Firewall). Khi một kết nối đã được thiết lập trước đó, bảng State Table vẫn duy trì luồng dữ liệu cũ cho đến khi hết hạn time-out.
  - Khắc phục: Sau mỗi lần thay đổi hoặc Disable firewall rule, bắt buộc phải vào Diagnostics > States > Reset States để xóa sạch bảng phiên trước khi thực hiện kiểm thử kết nối mới.

- Lỗi máy thật không truy cập được web của máy DMZ khi thử nghiệm Port Forward:
  - Nguyên nhân: Giao diện WAN của pfSense mặc định kích hoạt tính năng Block private networks và Block bogon networks, khiến tường lửa drop các gói tin có nguồn gốc IP nội bộ từ máy thật gửi vào WAN.
  - Khắc phục: Vào Interfaces > WAN, bỏ tích chọn hai mục Block private networks và Block bogon networks, nhấn Save và Apply Changes.
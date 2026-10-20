# BÁO CÁO THỰC HÀNH LAB 7: XÂY DỰNG CHÍNH SÁCH WEB PROTECTION TRÊN MÔ HÌNH pfSense + WEB PROXY

## 1. Thông tin sinh viên
- Họ và tên: ĐẶNG MINH NHẬT
- MSSV: 1150080029
- Mã lớp: 11DHCNPM1
- Môn học: An toàn hệ thống thông tin
- Nền tảng ảo hóa: VMware Workstation

---

## 2. Kiến trúc giải pháp Web Protection
Mô hình bài Lab 7 áp dụng giải pháp phân tầng giữa Tường lửa Gateway và Máy chủ Lọc nội dung Web chuyên dụng:
- **pfSense CE (Firewall/Gateway L3/L4):**
  - WAN: Nhận IP tự động từ NAT hạ tầng bên ngoài.
  - MGMT (`192.168.56.254/24`): Giao diện quản trị WebGUI riêng biệt, cô lập khỏi mạng người dùng.
  - LAN (`10.6.0.1/24`): Chứa Domain Controller (DC01), máy chủ Web-Proxy và các Client.
  - DMZ (`172.16.6.1/24`): Chứa máy chủ Web mô phỏng DMZ-WEB.
  - Kiểm soát luồng mạng: Chặn toàn bộ kết nối trực tiếp cổng 80/443 từ Client, chỉ cho phép duy nhất máy chủ Web-Proxy tạo kết nối Web ra ngoài để chống vượt rào (Bypass).
- **WEB-PROXY (Dedicated Content Filtering L7):**
  - Chạy hệ điều hành Ubuntu Server 24.04 LTS độc lập với IP tĩnh `10.6.0.30/24`.
  - Luồng xử lý: Trình duyệt Client kết nối vào **E2Guardian** (Port 8080) $\rightarrow$ E2Guardian kiểm tra URL/Policy $\rightarrow$ đẩy sang **Squid** (127.0.0.1:3128) làm upstream $\rightarrow$ gửi qua gateway pfSense.
  - Tích hợp **ClamAV Daemon** quét mã độc luồng tập tin tải về.
- **DMZ-WEB (`172.16.6.10/24`):**
  - Cung cấp 13 Virtual Hosts Nginx mô phỏng các nhóm website kiểm thử: Normal, Job, Geo-Sim (China/Mideast), Warning (Weapons/Politics/Religion), Education, Game/Entertainment, Streaming và Download.
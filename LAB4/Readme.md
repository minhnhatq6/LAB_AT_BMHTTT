# BÁO CÁO THỰC HÀNH LAB 4: KHẢO SÁT VÀ ĐÁNH GIÁ BỀ MẶT MẠNG BẰNG NMAP

## 1. Thông tin sinh viên

* Họ và tên: ĐẶNG MINH NHẬT
* MSSV: 1150080029
* Mã lớp: 11DHCNPM1
* Tên bài Lab: Lab 4 - Khảo sát và đánh giá bề mặt mạng bằng Nmap


* Môi trường thực hành: VMware Workstation / VirtualBox mạng nội bộ cô lập (Host-Only / NAT cách ly)


* Hệ điều hành Host: Windows 10 x64



---

## 2. Mô hình và cách dựng môi trường

* Mô hình kết nối:
* Máy thật (Host OS): Windows 10 (Virtual Network Adapter)


* Máy quét chính (Attacker/Scanner): Kali Linux 2026.x


* Máy đích mục tiêu (Target): Metasploitable 2 (Ubuntu Linux chứa nhiều dịch vụ cố ý có lỗ hổng)




* Quy trình dựng môi trường:
1. Cài đặt Nmap, Zenmap và Npcap trên máy trạm Windows.


2. Triển khai máy ảo Kali Linux và Metasploitable 2 trên phần mềm ảo hóa.


3. Cấu hình hai máy ảo cùng một phân đoạn mạng nội bộ riêng biệt để bảo đảm tính an toàn, cô lập với mạng vật lý bên ngoài.


4. Xác định địa chỉ IP cục bộ qua lệnh ip -br addr (Kali) và ifconfig (Metasploitable 2), kiểm tra thông mạng bằng lệnh ping.





---

## 3. Các nội dung đã thực hiện & Kết quả nghiệm thu

| Mục | Nội dung thực hiện | Kết quả |
| --- | --- | --- |
| Mục 2 & 3

 | Cài đặt và xác thực phiên bản Nmap / Zenmap trên Windows và Kali Linux

 | PASS |
| Mục 4

 | Thiết lập mạng nội bộ, đối chiếu địa chỉ IP và kiểm tra kết nối ICMP

 | PASS |
| Mục 5

 | Rà soát mạng nội bộ, phát hiện các host đang hoạt động (sudo nmap -sn ...)

 | PASS |
| Mục 6

 | Khảo sát cổng TCP, so sánh kỹ thuật -sT, -sS, -sF, -sX, -sN, -sA

 | PASS |
| Mục 7

 | Quét cổng UDP có kiểm soát (sudo nmap -sU --top-ports 20 ...)

 | PASS |
| Mục 8

 | Nhận diện phiên bản dịch vụ (-sV), hệ điều hành (-O) và quét tổng hợp (-A)

 | PASS |
| Mục 9

 | Thu thập thông tin và đánh giá an toàn dịch vụ SMB qua NSE Scripts

 | PASS |
| Mục 10

 | Xuất kết quả đa định dạng (-oA, -oN, -oX, -oG) và chuyển đổi HTML

 | PASS |
| Mục 11

 | Thực nghiệm tăng cường phòng thủ (Hardening) trước và sau khi can thiệp

 | PASS |

---

## 4. Lỗi gặp phải và cách khắc phục

* Lỗi cài đặt Nmap trên Windows bị dừng ở bước Npcap:
* Nguyên nhân: Quá trình cài đặt gọi tiến trình con npcap-1.88.exe bị ẩn cửa sổ License dưới thanh Taskbar hoặc xung đột với Npcap có sẵn từ trước.


* Khắc phục: Mở cửa sổ cấu hình Npcap Setup chấp nhận điều khoản cài đặt, hoặc tắt tiến trình con trong Task Manager để Nmap hoàn tất cài đặt bình thường.


* Lỗi quét nhầm sang mạng vật lý bên ngoài (192.168.1.0/24) và không quét được máy đích:
* Nguyên nhân: Card mạng máy ảo Kali vô tình để chế độ Bridged, nhận IP cùng dải với Wi-Fi thay vì mạng ảo nội bộ, dẫn đến việc quét trúng các thiết bị IoT/Camera thật và báo lỗi Host seems down với máy ảo đích.


* Khắc phục: Chuyển đổi card mạng của cả Kali Linux và Metasploitable 2 về chung một mạng ảo cô lập (NAT/Host-Only), khởi động lại dịch vụ mạng bằng sudo systemctl restart NetworkManager, kiểm tra ping thông suốt giữa 2 máy ảo trước khi tiếp tục quét.




* Lỗi open|filtered khi thực hiện FIN, Xmas và NULL scan:
* Nguyên nhân: Theo đặc tả RFC 793, máy chủ đích Linux không phản hồi khi nhận gói tin bất thường tới cổng mở; Nmap không nhận được phản hồi nên không thể phân biệt giữa cổng mở và cổng bị firewall âm thầm loại bỏ.


* Khắc phục: Ghi nhận đúng bản chất kỹ thuật vào báo cáo phân tích, không tự quy chụp open|filtered = open.




* Lỗi thiếu công cụ xsltproc khi chuyển đổi báo cáo XML sang HTML:
* Nguyên nhân: Bản cài đặt Kali tối giản chưa có sẵn thư viện chuyển đổi XSLT.
* Khắc phục: Cài đặt bổ sung bằng lệnh sudo apt install -y xsltproc để xuất file bao_cao.html hoàn chỉnh.
# Pathfinding Web App - Khương Đình

Ứng dụng web minh họa thuật toán tìm đường trên bản đồ khu vực Khương Đình (Hà Nội) với khả năng đánh dấu đường bị tắc/ngập làm tăng trọng số.

## Cấu trúc
- `backend/`: Flask API + thuật toán.
- `frontend/`: Leaflet UI, tương tác và animation.
- `requirements.txt`: thư viện cần thiết.

## Chạy dự án
1. Tạo môi trường và cài đặt phụ thuộc:
   ```bash
   pip install -r requirements.txt
   ```
2. Chạy backend (phục vụ luôn file tĩnh frontend):
   ```bash
   python -m backend.app
   ```
3. Mở trình duyệt tới `http://localhost:5000` để dùng ứng dụng.

## API chính
- `GET /init_graph`: trả danh sách node/edge.
- `GET /nearest?lat=&lng=`: node gần nhất với tọa độ click.
- `POST /mark_edge`: `{ "u": nodeA, "v": nodeB, "type": "jam"|"flood" }` cập nhật trọng số.
- `GET /run/<algo>?start=&goal=`: chạy thuật toán (`dfs`, `bfs`, `ucs`, `astar`, `greedy`).
- `GET /reset_weights`: khôi phục trọng số mặc định.

## Lưu ý
- Dữ liệu đồ thị tải trực tiếp từ OpenStreetMap bằng OSMnx nên cần kết nối mạng khi chạy lần đầu.
- Log thuật toán trả về từng bước (current, frontier, explored, path) để frontend hiển thị animate.

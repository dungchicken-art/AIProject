# Khương Đình Pathfinding Demo

Ứng dụng web minh họa tìm đường trên đồ thị đường phố (hoặc đồ thị mẫu nếu không có OSM). Backend dùng Flask + NetworkX, frontend dùng Leaflet để hiển thị và animate các thuật toán.

## Cấu trúc
- `backend/`: API Flask, thuật toán và tải đồ thị
- `frontend/`: HTML/JS/CSS giao diện Leaflet
- `data/khuong_dinh.graphml`: (tuỳ chọn) dữ liệu OSM lưu offline nếu có

## Chạy dự án
1. Cài đặt môi trường Python và phụ thuộc:
   ```bash
   pip install flask flask-cors networkx osmnx
   ```
   (Nếu không cài được OSMnx hoặc không có graphml, app sẽ tự fallback sang đồ thị lưới 4x4.)

2. Khởi động backend:
   ```bash
   python -m backend.app
   ```

3. Phục vụ frontend tĩnh (ví dụ):
   ```bash
   python -m http.server 8000 -d frontend
   ```
   Sau đó mở http://localhost:8000 và đảm bảo backend chạy ở http://localhost:5000 (CORS đã bật sẵn).

## Luồng sử dụng
1. Click bản đồ để chọn Start rồi Goal.
2. Tiếp tục click 2 node liên tiếp để đánh dấu đường bị tắc/ngập (chọn loại trong panel).
3. Chọn thuật toán (DFS/BFS/UCS/A*/Greedy) để xem log từng bước và đường đi cuối.
4. Nhấn Reset để trả trọng số về mặc định.

## API chính
- `GET /init_graph` – trả nodes/edges để vẽ.
- `GET /nearest?lat=&lng=` – tìm node gần nhất điểm click.
- `POST /mark_edge` – {u,v,type} cập nhật trọng số cạnh.
- `GET /run/<algo>?start=&goal=` – chạy thuật toán, trả log steps + final_path.
- `GET /reset_weights` – khôi phục trọng số.

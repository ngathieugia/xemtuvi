import json
from flask import Flask, request, jsonify
from flask_cors import CORS

from lasotuvi.App import lapDiaBan
from lasotuvi.DiaBan import diaBan
from lasotuvi.ThienBan import lapThienBan

app = Flask(__name__)
application = app # Dành cho cPanel/WSGI
CORS(app)

# Bot cảnh báo giá Pi Network: /pi/webhook (Telegram), /pi/cron, /pi/
try:
    from pi_alert.web import bp as pi_alert_bp
    app.register_blueprint(pi_alert_bp)
except Exception as _e:  # không để lỗi bot làm hỏng app tử vi
    print("pi_alert không khởi động được:", _e)

@app.route('/api/laso', methods=['GET'])
def get_laso():
    try:
        # Lấy parameters
        day = int(request.args.get('day', 1))
        month = int(request.args.get('month', 1))
        year = int(request.args.get('year', 2000))
        # frontend gửi 0=Tý, 1=Sửu -> Python nhận 1=Tý, 2=Sửu
        hour_val = int(request.args.get('hour', 0)) + 1 
        
        # frontend gửi 'male' / 'female' -> Python: 1 = Nam, -1 = Nữ
        gender_str = request.args.get('gender', 'male')
        gender = 1 if gender_str == 'male' else -1
        
        cal_type = request.args.get('calType', 'solar')
        is_solar = True if cal_type == 'solar' else False
        
        name = request.args.get('name', 'Bản Mệnh')
        try:
            view_year = int(request.args.get('viewYear', 2024))
        except (ValueError, TypeError):
            view_year = 2024

        # 1. Gọi lapDiaBan
        db = lapDiaBan(diaBan, day, month, year, hour_val, gender, is_solar, 7)
        
        # 2. An Sao Lưu dựa vào view_year
        can_nam_xem = (view_year + 6) % 10 + 1
        chi_nam_xem = (view_year + 8) % 12 + 1
        from lasotuvi.SaoLuu import anSaoLuu
        anSaoLuu(db, can_nam_xem, chi_nam_xem)
        
        # 3. Gọi lapThienBan để lấy thông tin trung tâm
        tb = lapThienBan(day, month, year, hour_val, gender, name, db, is_solar, 7)
        
        # 3. Format lại Thập Nhị Cung thành JSON (Array 12 cung)
        # Các cung được đánh số từ 1 (Tý) đến 12 (Hợi)
        # Trong db.thapNhiCung, index 0 bỏ trống, các cung từ 1-12
        palaces = []
        for i in range(1, 13):
            cung = db.thapNhiCung[i]
            # cung.cungSao là list các dict của object Sao
            # Ta sẽ trích xuất thông tin
            major_stars = []
            minor_stars = []
            
            for s in cung.cungSao:
                star_info = {
                    "name": s.get("saoTen", ""),
                    "brightness": s.get("saoDacTinh", ""),
                    "type": s.get("saoLoai", 2),
                    "cssSao": s.get("cssSao", "")
                }
                # Phân loại theo saoLoai: 1 là Chính tinh
                if star_info["type"] == 1:
                    major_stars.append(star_info)
                else:
                    minor_stars.append(star_info)
                    
            palaces.append({
                "cungSo": cung.cungSo,
                "cungTen": cung.cungTen,
                "hanhCung": cung.hanhCung,
                "cungThan": cung.cungThan,
                "tuanTrung": getattr(cung, 'tuanTrung', False),
                "trietLo": getattr(cung, 'trietLo', False),
                "cungChu": getattr(cung, 'cungChu', ''), # VD: Mệnh, Phụ Mẫu...
                "cungDaiHan": getattr(cung, 'cungDaiHan', 0),
                "cungTieuHan": getattr(cung, 'cungTieuHan', ''),
                "majorStars": major_stars,
                "minorStars": minor_stars
            })
            
        # 4. Format lại Thiên Bàn
        thien_ban = {
            "ten": tb.ten,
            "ngayDuong": f"{tb.ngayDuong}/{tb.thangDuong}/{tb.namDuong}",
            "ngayAm": f"{tb.ngayAm}/{tb.thangAm}/{tb.namAm}",
            "gioSinh": tb.gioSinh,
            "gioiTinh": tb.namNu,
            "amDuongMenh": tb.amDuongMenh,
            "amDuongNamSinh": tb.amDuongNamSinh,
            "menh": tb.menh,
            "banMenh": tb.banMenh,
            "cuc": tb.tenCuc,
            "sinhKhac": tb.sinhKhac,
            "menhChu": tb.menhChu,
            "thanChu": tb.thanChu,
            "canNgayTen": getattr(tb, 'canNgayTen', ''),
            "chiNgayTen": getattr(tb, 'chiNgayTen', ''),
            "canThangTen": getattr(tb, 'canThangTen', ''),
            "chiThangTen": getattr(tb, 'chiThangTen', ''),
            "canNamTen": getattr(tb, 'canNamTen', ''),
            "chiNamTen": getattr(tb, 'chiNamTen', '')
        }
        
        return jsonify({
            "status": "success",
            "thienBan": thien_ban,
            "diaBan": palaces
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)

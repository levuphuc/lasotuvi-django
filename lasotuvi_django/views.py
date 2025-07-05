import datetime
import json

from django.http import HttpResponse
from django.shortcuts import render
from lasotuvi.DiaBan import diaBan, tinh_dia_van_theo_cung
from lasotuvi.ThienBan import lapThienBan
from lasotuvi_django.utils import lapDiaBan, an_sao_luu_nien



def tinh_can_thang(can_nam_ten, chi_cung):
    thien_can = ['Giáp', 'Ất', 'Bính', 'Đinh', 'Mậu', 'Kỷ', 'Canh', 'Tân', 'Nhâm', 'Quý']
    khoi_diem = {
        'Giáp': 'Bính', 'Kỷ': 'Bính',
        'Ất': 'Mậu', 'Canh': 'Mậu',
        'Bính': 'Canh', 'Tân': 'Canh',
        'Đinh': 'Nhâm', 'Nhâm': 'Nhâm',
        'Mậu': 'Giáp', 'Quý': 'Giáp',
    }
    dia_chi_thang = ['Dần', 'Mão', 'Thìn', 'Tỵ', 'Ngọ', 'Mùi', 'Thân', 'Dậu', 'Tuất', 'Hợi', 'Tý', 'Sửu']

    ten = chi_cung.strip().capitalize()
    if can_nam_ten not in khoi_diem:
        raise ValueError("Thiên Can năm không hợp lệ")
    if ten not in dia_chi_thang:
        raise ValueError(f"Chi cung '{ten}' không hợp lệ")

    thang_index = dia_chi_thang.index(ten)
    start_index = thien_can.index(khoi_diem[can_nam_ten])
    index = (start_index + thang_index) % 10
    return thien_can[index]


def gan_can_thang_vao_dia_ban(dia_ban, can_nam_ten):
    dia_chi_thang = ['Dần', 'Mão', 'Thìn', 'Tỵ', 'Ngọ', 'Mùi', 'Thân', 'Dậu', 'Tuất', 'Hợi', 'Tý', 'Sửu']
    for cung in dia_ban.thapNhiCung:
        ten = getattr(cung, 'cungTen', '').strip().capitalize()
        if ten in dia_chi_thang:
            try:
                cung.canThangTen = tinh_can_thang(can_nam_ten, ten)
            except Exception as e:
                print(f"[ERROR] Không thể gán canThangTen cho cung '{ten}': {e}")
                cung.canThangTen = None
        else:
            cung.canThangTen = None  # reset nếu không khớp địa chi tháng


def tim_lai_nhan_cung(thap_nhi_cung, can_nam_ten):
    if not can_nam_ten:
        return "Không xác định"

    for cung in thap_nhi_cung:
        can_cung = getattr(cung, 'canThangTen', None)
        if can_cung and can_nam_ten in can_cung:
            return getattr(cung, 'cungChu', 'Không rõ')

    return "Không xác định"

from django.http import HttpResponse
import io

def xuat_text_laso(request):
    now = datetime.datetime.now()
    hoTen = request.GET.get('hoten')
    ngaySinh = int(request.GET.get('ngaysinh', now.day))
    thangSinh = int(request.GET.get('thangsinh', now.month))
    namSinh = int(request.GET.get('namsinh', now.year))
    gioiTinh = 1 if request.GET.get('gioitinh') == 'nam' else -1
    gioSinh = int(request.GET.get('giosinh', 1))
    timeZone = int(request.GET.get('muigio', 7))
    duongLich = False if request.GET.get('amlich') == 'on' else True

    db = lapDiaBan(diaBan, ngaySinh, thangSinh, namSinh, gioSinh, gioiTinh, duongLich, timeZone)
    thienBan = lapThienBan(ngaySinh, thangSinh, namSinh, gioSinh, gioiTinh, hoTen, db)

    an_sao_luu_nien(db, thienBan.canChiNamXemLaSo['can'], thienBan.canChiNamXemLaSo['chiTen'])
    gan_can_thang_vao_dia_ban(db, thienBan.canNamTen)
    thienBan.laiNhanCung = tim_lai_nhan_cung(db.thapNhiCung, thienBan.canNamTen)

    laso_data = {
        'thienBan': thienBan,
        'diaBan': {
            'thapNhiCung': db.thapNhiCung
        }
    }

    text = xuat_text_hoan_chinh(thienBan, db)

    hoten = thienBan.ten or "KhongTen"
    hoten = hoten.replace(" ", "_")
    filename = f"Tử_vi_{hoten}_{thienBan.ngayDuong:02}_{thienBan.thangDuong:02}_{thienBan.namDuong}_DL_{thienBan.canChiNamXemLaSo['nam']}.txt"
    print(f"{filename}")
    response = HttpResponse(text, content_type='text/plain; charset=utf-8')
    response['Content-Disposition'] = f"attachment; filename*=UTF-8''{filename}"

    


    return response


def xuat_text_hoan_chinh(thien_ban, dia_ban):
    lines = []
    lines.append("📌 THIÊN BÀN")
    lines.append(f"- Họ tên: {getattr(thien_ban, 'ten', '')}")
    lines.append(f"- Ngày sinh: {thien_ban.ngayDuong:02}/{thien_ban.thangDuong:02}/{thien_ban.namDuong} "    
             f"({thien_ban.ngayAm:02}/{thien_ban.thangAm:02}/{thien_ban.namAm} Âm Lịch)")
    lines.append(f"- Bát tự: năm {thien_ban.canNamTen} {thien_ban.chiNamTen}, tháng {thien_ban.canThangTen} {thien_ban.chiThangTen}, "
             f"ngày {thien_ban.canNgayTen} {thien_ban.chiNgayTen}, giờ {thien_ban.gioSinh}")

    gioi_tinh = "Nam" if getattr(thien_ban, 'gioiTinh', 1) == 1 else "Nữ"
    am_duong = getattr(thien_ban, 'amDuongNamSinh', '')

    lines.append(f"- Âm dương: {am_duong} {gioi_tinh}")
    lines.append(f"- {thien_ban.amDuongMenh}")
    lines.append(f"- Bản mệnh: {thien_ban.banMenh}")
    lines.append(f"- Cục: {thien_ban.tenCuc}")
    lines.append(f"- {thien_ban.sinhKhac}")
    lines.append(f"- Cân lượng: {thien_ban.canLuong}")
    lines.append(f"- Cân lượng: {thien_ban.canLuongBinhGiai}")
    lines.append(f"- Chủ mệnh: {thien_ban.menhChu}")
    lines.append(f"- Chủ thân: {thien_ban.thanChu}")
    lines.append(f"- Lai Nhân Cung: {thien_ban.laiNhanCung}")    
    lines.append(f"- Ngày xem: {thien_ban.today} ({thien_ban.canChiNamXemLaSo['canTen']} {thien_ban.canChiNamXemLaSo['chiTen']})\n")
    lines.append("")
    lines.append("📌 ĐỊA BÀN – 12 CUNG")
    for cung in dia_ban.thapNhiCung:
        if cung.cungSo == 0: continue

        lines.append(f"\n🔷 Cung {cung.cungTen} ({cung.cungChu}) – Hành {cung.hanhCung}")
        if cung.cungThan:
            lines[-1] += " [Thân cư]"
        if cung.cungSo == thien_ban.menhChu:
            lines[-1] += " [Mệnh an]"        

        # Chính tinh
        chinh_tinh = [
            f"{s['saoTen']} ({s['saoDacTinh']})" if s.get('saoDacTinh') else s['saoTen']
            for s in cung.cungSao if s['saoLoai'] == 1
        ]
        if chinh_tinh:
            lines.append(f"  - Chính tinh: {', '.join(chinh_tinh)}")

        # Tuần - Triệt
        if getattr(cung, 'trietLo', False):
            lines.append(f"  - << Triệt lộ >>")
        if getattr(cung, 'tuanTrung', False):
            lines.append(f"  - < Tuần trung >")

        

        # Phụ tinh tốt
        phu_tot = [s['saoTen'] for s in cung.cungSao if 3 <= s['saoLoai'] <= 8]
        if phu_tot:
            lines.append(f"  - Phụ tinh tốt: {', '.join(phu_tot)}")

        # Phụ tinh xấu
        phu_xau = [s['saoTen'] for s in cung.cungSao if 11 <= s['saoLoai'] <= 15]
        if phu_xau:
            lines.append(f"  - Phụ tinh xấu: {', '.join(phu_xau)}")

        # Sao Lưu niên
        sao_luu = [s['saoTen'] for s in cung.cungSao if s['saoTen'].startswith("L.")]
        if sao_luu:
            lines.append(f"  - Sao Lưu Niên: {', '.join(sao_luu)}")

        if cung.cungDaiHan:
            lines.append(f"  - Đại hạn: {cung.cungDaiHan}")
        if cung.cungTieuHan:
            lines.append(f"  - Tiểu hạn: {cung.cungTieuHan}")

        if hasattr(cung, 'diaVan'):
            lines.append(f"  - Địa vận: {cung.diaVan}")

        # Vòng Tràng Sinh
        vts = next((s['saoTen'] for s in cung.cungSao if s.get('vongTrangSinh') == 1), None)
        if vts:
            lines.append(f"  - Vòng Tràng Sinh: {vts}")

    return "\n".join(lines)


def api(request):
    now = datetime.datetime.now()
    hoTen = (request.GET.get('hoten'))
    ngaySinh = int(request.GET.get('ngaysinh', now.day))
    thangSinh = int(request.GET.get('thangsinh', now.month))
    namSinh = int(request.GET.get('namsinh', now.year))
    gioiTinh = 1 if request.GET.get('gioitinh') == 'nam' else -1
    gioSinh = int(request.GET.get('giosinh', 1))
    timeZone = int(request.GET.get('muigio', 7))
    duongLich = False if request.GET.get('amlich') == 'on' else True

    db = lapDiaBan(diaBan, ngaySinh, thangSinh, namSinh, gioSinh,
                   gioiTinh, duongLich, timeZone)
    thienBan = lapThienBan(ngaySinh, thangSinh, namSinh,
                           gioSinh, gioiTinh, hoTen, db)

    an_sao_luu_nien(db, thienBan.canChiNamXemLaSo['can'], thienBan.canChiNamXemLaSo['chiTen'])

    gan_can_thang_vao_dia_ban(db, thienBan.canNamTen)
    thienBan.laiNhanCung = tim_lai_nhan_cung(db.thapNhiCung, thienBan.canNamTen)

    laso = {
        'thienBan': thienBan,
        'thapNhiCung': db.thapNhiCung
    }
    my_return = (json.dumps(laso, default=lambda o: o.__dict__))
    return HttpResponse(my_return, content_type="application/json")


def lasotuvi_django_index(request):
    return render(request, 'index.html')


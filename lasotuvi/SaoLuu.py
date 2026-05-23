# -*- coding: utf-8 -*-

from lasotuvi.Sao import (
    saoLuuThaiTue, saoLuuTangMon, saoLuuBachHo, saoLuuKhoc, saoLuuHu,
    saoLuuLocTon, saoLuuKinhDuong, saoLuuDaLa, saoLuuThienMa
)
from lasotuvi.AmDuong import dichCung, thienCan, timThienMa

def anSaoLuu(diaBan, canNamXem, chiNamXem):
    """
    An 9 sao lưu niên lên Địa bàn dựa vào Can và Chi của năm xem.
    """
    # L. Thái Tuế ở chi năm xem
    viTriLuuThaiTue = chiNamXem
    diaBan.nhapSao(viTriLuuThaiTue, saoLuuThaiTue)

    # L. Tang Môn tiến 2 cung từ L.Thái Tuế
    viTriLuuTangMon = dichCung(viTriLuuThaiTue, 2)
    diaBan.nhapSao(viTriLuuTangMon, saoLuuTangMon)

    # L. Bạch Hổ đối xung Tang Môn (tiến 6 cung)
    viTriLuuBachHo = dichCung(viTriLuuTangMon, 6)
    diaBan.nhapSao(viTriLuuBachHo, saoLuuBachHo)

    # Khốc Hư khởi từ Ngọ (cung số 7)
    viTriLuuKhoc = dichCung(7, -chiNamXem + 1)
    diaBan.nhapSao(viTriLuuKhoc, saoLuuKhoc)

    viTriLuuHu = dichCung(7, chiNamXem - 1)
    diaBan.nhapSao(viTriLuuHu, saoLuuHu)

    # L. Lộc Tồn an theo can năm xem
    viTriLuuLocTon = thienCan[canNamXem]['vitriDiaBan']
    diaBan.nhapSao(viTriLuuLocTon, saoLuuLocTon)

    # L. Kình Dương tiến 1 từ L.Lộc Tồn
    viTriLuuKinhDuong = dichCung(viTriLuuLocTon, 1)
    diaBan.nhapSao(viTriLuuKinhDuong, saoLuuKinhDuong)

    # L. Đà La lùi 1 từ L.Lộc Tồn
    viTriLuuDaLa = dichCung(viTriLuuLocTon, -1)
    diaBan.nhapSao(viTriLuuDaLa, saoLuuDaLa)

    # L. Thiên Mã tính dựa vào chi năm xem
    viTriLuuThienMa = timThienMa(chiNamXem)
    diaBan.nhapSao(viTriLuuThienMa, saoLuuThienMa)

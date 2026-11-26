"""Chay testbench cua core_v1 voi MOI bo vector v1, ca 2 che do: khong tre va co tre (gian doan).

Chay duoc tren Windows, Linux, macOS (chi can Python 3 va Icarus Verilog).
Dung o thu muc goc repo:
    python scripts/chay_tb_core_v1.py            # chay het
    python scripts/chay_tb_core_v1.py --nhanh    # bo qua cac bo lon 768 x 768 (khoang 1 phut)
Chay het (gom 2 bo 768 x 768) mat khoang 7-8 phut vi mo phong 4 lane x 64 sign_sel kha cham.
"""
import argparse
import glob
import os
import subprocess
import sys
import time

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RTL = ["rtl/sign_sel.v", "rtl/cay_cong.v", "rtl/lane.v", "rtl/requant.v",
       "rtl/w_decode_v1.v", "rtl/core_v1.v"]
TB = "tb/tb_core_v1.v"
VVP = "build/tb_core_v1.vvp"


def cac_bo_v1(nhanh):
    """Cac thu muc vector co PHIEN_BAN=v1 (chip ban v1 chi chay duoc W kieu v1)."""
    ket_qua = []
    for cfg in sorted(glob.glob(os.path.join(GOC, "vectors", "*", "config.txt"))):
        with open(cfg, encoding="utf-8") as f:
            noi_dung = f.read()
        if "PHIEN_BAN=v1\n" not in noi_dung:
            continue
        thu_muc = os.path.relpath(os.path.dirname(cfg), GOC).replace("\\", "/")
        if nhanh and "t768" in thu_muc:
            continue
        ket_qua.append(thu_muc)
    return ket_qua


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--nhanh", action="store_true", help="bo qua cac bo 768 x 768")
    a = p.parse_args()
    os.chdir(GOC)
    os.makedirs("build", exist_ok=True)

    print("Bien dich ...")
    r = subprocess.run(["iverilog", "-g2012", "-o", VVP] + RTL + [TB], capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout, r.stderr)
        sys.exit("LOI: bien dich that bai")

    so_dat = so_chay = 0
    lan_chay = [(d, tre, 0) for d in cac_bo_v1(a.nhanh) for tre in (0, 1)]
    # Dau vao nhanh + ben nhan Y rat cham -> hang doi Y day -> chip PHAI chan dau vao
    # (dac ta 7.3 muc 4). Dong DAT phai bao "chip chan dau vao" > 0 nhip.
    lan_chay.append(("vectors/v1_k64_chan", 0, 100))
    lan_chay.append(("vectors/v1_k64_chan", 1, 150))
    for thu_muc, tre, chan in lan_chay:
        t0 = time.time()
        r = subprocess.run(["vvp", "-n", VVP, f"+THU_MUC={thu_muc}", f"+TRE={tre}",
                            f"+CHAN_THEM={chan}"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        dong = [d for d in r.stdout.splitlines()
                if d.startswith(("DAT", "KHONG DAT", "LOI", "SAI", "  "))]
        so_chay += 1
        if any(d.startswith("DAT") for d in dong):
            so_dat += 1
        for d in dong:
            print(d)
        print(f"   ({time.time() - t0:.1f} s)")

    # 4 truong hop loi (cau hinh sai, X = -128, ma W 11, TLAST sai cho)
    r = subprocess.run(["iverilog", "-g2012", "-o", "build/tb_core_v1_loi.vvp"] + RTL + ["tb/tb_core_v1_loi.v"],
                       capture_output=True, text=True)
    r = subprocess.run(["vvp", "-n", "build/tb_core_v1_loi.vvp"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    dong = [d for d in r.stdout.splitlines() if d.startswith(("DAT", "KHONG DAT"))]
    for d in dong:
        print(d)
    so_chay += 1
    if dong and dong[-1].startswith("DAT"):
        so_dat += 1

    print()
    print(f"TONG KET: {so_dat}/{so_chay} lan chay DAT")
    sys.exit(0 if so_dat == so_chay else 1)


if __name__ == "__main__":
    main()

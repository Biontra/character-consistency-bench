"""Hakem çıktılarını kurallara göre kaydeder. Hakemi ÇALIŞTIRMAZ.

Kullanım:
  python3 scripts/hakem_kaydet.py kaydet KOD --cikti DOSYA --hakem-modeli AD --tarih YYYY-AA-GG
  python3 scripts/hakem_kaydet.py durum
  python3 scripts/hakem_kaydet.py topla

kaydet çıkış kodları: 0 geçerli kayıt,
  1 çıktı geçersiz, günlüğe yazıldı (1. denemeyse bir kez daha çalıştırılabilir;
    2. denemeyse klibin cevapları hakem_yok yazıldı),
  2 kural gereği reddedildi, hiçbir şey yazılmadı.
Gizli yollar (secret/hakem/..., secret/checks.json) varsayılan; testler için
--hakem-dizin, --checks, --sonuc ile değiştirilebilir.
"""
import argparse
import sys
from pathlib import Path

DEPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DEPO))

from tutar import hakem_kayit as hk  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--hakem-dizin", default=str(DEPO / "secret" / "hakem"))
    ap.add_argument("--checks", default=str(DEPO / "secret" / "checks.json"))
    ap.add_argument("--sonuc", default=str(DEPO / "results" / "judge_raw.jsonl"))
    alt = ap.add_subparsers(dest="komut", required=True)
    k = alt.add_parser("kaydet")
    k.add_argument("kod")
    k.add_argument("--cikti", required=True)
    k.add_argument("--hakem-modeli", required=True)
    k.add_argument("--tarih", required=True)
    alt.add_parser("durum")
    alt.add_parser("topla")
    a = ap.parse_args(argv)

    try:
        if a.komut == "kaydet":
            r = hk.kaydet(a.kod, a.cikti, a.hakem_modeli, a.tarih, a.hakem_dizin, a.checks)
            print(f"{a.kod}: calistirma {r['calistirma']}, durum {r['durum']}")
            for h in r["hatalar"]:
                print(f"  hata: {h}")
            if r["durum"] == "gecersiz":
                print(f"{a.kod}: bir kez daha calistirilabilir")
            if r["durum"] == "hakem_yok":
                print(f"{a.kod}: ikinci deneme de gecersiz, cevaplar hakem_yok yazildi")
            return 0 if r["durum"] == "gecerli" else 1
        if a.komut == "durum":
            d = hk.durum(a.hakem_dizin, a.checks)
            for ad, baslik in (("gecerli", "gecerli"),
                               ("bir_gecersiz_bekliyor", "1 gecersiz deneme bekliyor"),
                               ("hakem_yok", "hakem_yok"),
                               ("hic_calismadi", "hic calismadi")):
                print(f"{baslik}: {len(d[ad])}  {' '.join(d[ad])}")
            return 0
        n = hk.topla(a.hakem_dizin, a.checks, a.sonuc, beklenen_satir=hk.BEKLENEN_SATIR)
        print(f"{a.sonuc}: {n} satir")
        return 0
    except hk.KayitReddi as hata:
        print(f"REDDEDILDI: {hata}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

"""İnsan-hakem uyumunu hesaplar ve JSON rapor basar. Yalnız stdlib.

Kullanım: python3 scripts/uyum_hesapla.py --insan insan_cevaplari.json
          --hakem-ham ham_kayit.jsonl --checks checks.json --esleme esleme.json
          --secim data/insan_secimi.json
Yolların hepsi zorunludur (varsayılan yok). İnsan dosyası bitmemişse, yanındaki
cevaplar.sha256 yoksa ya da dosyanın gerçek sha256'sıyla uyuşmuyorsa, klip kümesi
secim + esleme'den çıkan kümeyle birebir aynı değilse çalışmaz.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tutar.uyum_girdi import GirdiHatasi, hesapla  # noqa: E402

SHA_ADI = "cevaplar.sha256"  # tutar/insan_kayit.py SHA_ADI ile aynı


def sha_denetle(insan_yol):
    """Cevap dosyasının yanındaki sha256 dosyası yoksa ya da uyuşmuyorsa GirdiHatasi."""
    insan_yol = Path(insan_yol)
    sha_yol = insan_yol.parent / SHA_ADI
    if not sha_yol.is_file():
        raise GirdiHatasi(f"sha256 dosyasi yok ({sha_yol}); cevap dosyasinin bitirildigi dogrulanamaz")
    yazili = sha_yol.read_text(encoding="utf-8").split()[:1]
    gercek = hashlib.sha256(insan_yol.read_bytes()).hexdigest()
    if yazili != [gercek]:
        raise GirdiHatasi("cevap dosyasinin sha256'si yanindaki sha256 dosyasiyla uyusmuyor")


def main(argv=None):
    ap = argparse.ArgumentParser()
    for ad in ("insan", "hakem-ham", "checks", "esleme", "secim"):
        ap.add_argument(f"--{ad}", required=True)
    a = ap.parse_args(argv)
    try:
        sha_denetle(a.insan)
        oku = lambda y: json.loads(Path(y).read_text(encoding="utf-8"))  # noqa: E731
        satirlar = [json.loads(s) for s in
                    Path(a.hakem_ham).read_text(encoding="utf-8").splitlines() if s.strip()]
        rapor = hesapla(oku(a.checks), oku(a.esleme), oku(a.insan), satirlar, oku(a.secim))
    except (GirdiHatasi, ValueError, OSError, KeyError) as hata:
        print(f"Uyum hesaplanamadi: {hata}", file=sys.stderr)
        return 2
    print(json.dumps(rapor, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

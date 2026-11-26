"""İnsan-hakem uyumunu hesaplar ve JSON rapor basar. Yalnız stdlib.

Kullanım: python3 scripts/uyum_hesapla.py --insan insan_cevaplari.json
          --hakem-ham ham_kayit.jsonl --checks checks.json --esleme esleme.json
Yolların hepsi zorunludur (varsayılan yok). İnsan dosyası bitmemişse çalışmaz.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tutar.uyum_girdi import GirdiHatasi, hesapla  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser()
    for ad in ("insan", "hakem-ham", "checks", "esleme"):
        ap.add_argument(f"--{ad}", required=True)
    a = ap.parse_args(argv)
    try:
        oku = lambda y: json.loads(Path(y).read_text(encoding="utf-8"))  # noqa: E731
        satirlar = [json.loads(s) for s in
                    Path(a.hakem_ham).read_text(encoding="utf-8").splitlines() if s.strip()]
        rapor = hesapla(oku(a.checks), oku(a.esleme), oku(a.insan), satirlar)
    except (GirdiHatasi, ValueError, OSError, KeyError) as hata:
        print(f"Uyum hesaplanamadi: {hata}", file=sys.stderr)
        return 2
    print(json.dumps(rapor, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

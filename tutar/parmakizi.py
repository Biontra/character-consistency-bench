"""Gizli dosyaların SHA-256 parmak izi. Dosya içeriği hiçbir yere yazılmaz."""
import hashlib
import json
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
DOSYALAR = {
    "checks.json": KOK / "secret" / "checks.json",
    "aikyo-baslangic.webp": KOK / "secret" / "aikyo-baslangic.webp",
    "hakem_talimati_v1.txt": KOK / "judge" / "hakem_talimati_v1.txt",
}
CIKTI = KOK / "data" / "fingerprints.json"


def parmakizi(yol: Path) -> str:
    h = hashlib.sha256()
    with open(yol, "rb") as f:
        for parca in iter(lambda: f.read(1 << 20), b""):
            h.update(parca)
    return h.hexdigest()


def main():
    izler = {ad: parmakizi(yol) for ad, yol in DOSYALAR.items()}
    CIKTI.write_text(json.dumps(izler, indent=2) + "\n", encoding="utf-8")
    for ad, iz in izler.items():
        print(ad, iz)


if __name__ == "__main__":
    main()

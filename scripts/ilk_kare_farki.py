"""Her klibin ilk karesi ile başlangıç resmi arasındaki farkı ölçer.

Kullanım: python3 scripts/ilk_kare_farki.py <baslangic_resmi> <klip_koku> <cikti.json>

Resim 720x1280 griye indirilir (ffmpeg scale, flags=area), klibin ilk karesi gri
alınır, piksel başına ortalama mutlak fark 0-255 ölçeğinde hesaplanır.
Çıktıya yalnız model, komut ve fark sayısı yazılır; resim ve yol yazılmaz.
Yalnız stdlib ve ffmpeg gerekir.
"""
import json
import statistics
import subprocess
import sys
from pathlib import Path

FFMPEG = "/opt/homebrew/bin/ffmpeg"
GEN, YUK = 720, 1280


def ortalama_mutlak_fark(a: bytes, b: bytes) -> float:
    if len(a) != len(b):
        raise ValueError("iki gri dizinin uzunlugu farkli")
    if not a:
        raise ValueError("bos dizi")
    return sum(abs(x - y) for x, y in zip(a, b)) / len(a)


def ozet_say(degerler) -> dict:
    d = sorted(degerler)
    if not d:
        raise ValueError("deger yok")
    return {"en_kucuk": d[0], "ortanca": statistics.median(d), "en_buyuk": d[-1]}


def _gri_kare(kaynak: Path, resim: bool) -> bytes:
    sure = f"scale={GEN}:{YUK}:flags=area,format=gray"
    komut = [FFMPEG, "-v", "error", "-i", str(kaynak),
             "-frames:v", "1", "-vf", sure, "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    s = subprocess.run(komut, capture_output=True)
    if s.returncode != 0:
        raise RuntimeError(f"ffmpeg hata verdi: {s.stderr.decode()[-300:]}")
    if len(s.stdout) != GEN * YUK:
        raise RuntimeError("beklenmeyen kare boyutu")
    return s.stdout


def main(argv):
    if len(argv) != 4:
        raise SystemExit(__doc__)
    resim, kok, cikti = Path(argv[1]), Path(argv[2]), Path(argv[3])
    ref = _gri_kare(resim, True)
    kayitlar = []
    for klip in sorted(kok.glob("clips/*/cmd[0-9][0-9].mp4")):
        fark = ortalama_mutlak_fark(ref, _gri_kare(klip, False))
        kayitlar.append({"model": klip.parent.name, "komut": int(klip.stem[3:]),
                         "fark": round(fark, 3)})
    modeller = {}
    for k in kayitlar:
        modeller.setdefault(k["model"], []).append(k["fark"])
    ozet = {m: ozet_say(v) for m, v in modeller.items()}
    cikti.write_text(json.dumps(
        {"aciklama": "Ilk kare ile baslangic resmi arasinda gri, 720x1280, piksel basina "
                     "ortalama mutlak fark (0-255). Betik: scripts/ilk_kare_farki.py",
         "ozet": ozet, "klipler": kayitlar}, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8")
    print(len(kayitlar), "klip")


if __name__ == "__main__":
    main(sys.argv)

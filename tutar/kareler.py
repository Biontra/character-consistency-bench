"""Bir klipten 10 fps kare ve üst/alt yarı kırpmaları çıkarır."""
import json
import subprocess
from pathlib import Path

FFMPEG = "/opt/homebrew/bin/ffmpeg"
FFPROBE = "/opt/homebrew/bin/ffprobe"


def _calistir(komut):
    sonuc = subprocess.run(komut, capture_output=True, text=True)
    if sonuc.returncode != 0:
        raise RuntimeError(f"{komut[0]} hata verdi: {sonuc.stderr.strip()[-300:]}")
    return sonuc.stdout


def _bilgi(klip: Path) -> dict:
    cikti = _calistir([
        FFPROBE, "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height:format=duration",
        "-of", "json", str(klip),
    ])
    veri = json.loads(cikti)
    try:
        akis = veri["streams"][0]
        return {
            "sure_sn": float(veri["format"]["duration"]),
            "genislik": int(akis["width"]),
            "yukseklik": int(akis["height"]),
        }
    except (KeyError, IndexError, ValueError) as hata:
        raise RuntimeError(f"Klipte video akışı okunamadı: {klip}") from hata


def _gercek_pngler(klasor: Path) -> list:
    return [p for p in Path(klasor).glob("*.png") if not p.name.startswith("._")]


def kare_cikar(klip: Path, hedef: Path, fps: int = 10) -> dict:
    klip, hedef = Path(klip), Path(hedef)
    if not klip.is_file():
        raise FileNotFoundError(klip)
    bilgi = _bilgi(klip)
    for ad in ("tam", "ust", "alt"):
        (hedef / ad).mkdir(parents=True, exist_ok=True)
        # Eski çalıştırmadan kalan kareler sayıyı bozmasın.
        # exFAT'te macOS'un ._ yan dosyaları sayılmaz ve silinmeye çalışılmaz.
        for eski in _gercek_pngler(hedef / ad):
            eski.unlink(missing_ok=True)
    # Not: yükseklik tek sayıysa alttaki 1 satır iki yarıda da dışarıda kalır.
    yarim = bilgi["yukseklik"] // 2
    g = bilgi["genislik"]
    kolu = (
        f"[0:v]fps={fps},split=3[a][b][c];"
        f"[b]crop={g}:{yarim}:0:0[u];"
        f"[c]crop={g}:{yarim}:0:{yarim}[d]"
    )
    _calistir([
        FFMPEG, "-v", "error", "-y", "-i", str(klip), "-filter_complex", kolu,
        "-map", "[a]", str(hedef / "tam" / "%03d.png"),
        "-map", "[u]", str(hedef / "ust" / "%03d.png"),
        "-map", "[d]", str(hedef / "alt" / "%03d.png"),
    ])
    sayi = len(_gercek_pngler(hedef / "tam"))
    if sayi == 0:
        raise RuntimeError(f"Hiç kare çıkmadı: {klip}")
    return {"kare_sayisi": sayi, **bilgi}

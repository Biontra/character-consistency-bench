"""Üretim kaydı okuma ve doğrulama (yalnız stdlib)."""
import json
import re
from pathlib import Path

ALANLAR = (
    "model", "komut", "prompt", "durum", "hata", "is_kimligi",
    "tarih_saat_utc", "gonderilen_parametreler", "baslangic_resmi_sha256",
    "baslangic_medya_kimligi", "dosya", "sha256", "sure_sn", "kare_sayisi",
    "genislik", "yukseklik", "fps", "ses_var", "kredi_teklif",
    "kredi_kesinti", "cozunurluk_parametresi", "prompt_zenginlestirme",
    "sunucu_prompt", "tohum", "model_surumu",
)
DURUMLAR = ("tamam", "uretim_hatasi", "reddedildi")
ZENGINLESTIRME = ("kapatildi", "secenek_yok", "kapatilamadi")
_YOL = re.compile(r"^clips/([^/]+)/cmd(\d{2})\.mp4$")
_TAMAM_DOLU = ("sha256", "sure_sn", "genislik", "yukseklik")


def satir_dogrula(satir: dict) -> None:
    if not isinstance(satir, dict):
        raise ValueError("satir nesne degil")
    eksik = [a for a in ALANLAR if a not in satir]
    fazla = [a for a in satir if a not in ALANLAR]
    if eksik:
        raise ValueError(f"eksik alan: {eksik}")
    if fazla:
        raise ValueError(f"fazla alan: {fazla}")
    if satir["durum"] not in DURUMLAR:
        raise ValueError(f"bilinmeyen durum: {satir['durum']!r}")
    k = satir["komut"]
    if type(k) is not int or not 1 <= k <= 20:
        raise ValueError(f"komut 1..20 disinda: {k!r}")
    if satir["prompt_zenginlestirme"] not in ZENGINLESTIRME:
        raise ValueError("bilinmeyen prompt_zenginlestirme")
    if not isinstance(satir["gonderilen_parametreler"], dict):
        raise ValueError("gonderilen_parametreler nesne olmali")
    m = _YOL.match(satir["dosya"]) if isinstance(satir["dosya"], str) else None
    if not m or m.group(1) != satir["model"] or int(m.group(2)) != k:
        raise ValueError(f"dosya yolu kalibina uymuyor: {satir['dosya']!r}")
    if satir["durum"] == "tamam":
        bos = [a for a in _TAMAM_DOLU if satir[a] is None]
        if bos:
            raise ValueError(f"durum tamam iken bos alan: {bos}")


def kayitlari_oku(klasor: Path) -> list:
    sonuc = []
    gorulen = set()
    for dosya in sorted(Path(klasor).glob("*.jsonl")):
        for no, ham in enumerate(dosya.read_text(encoding="utf-8").splitlines(), 1):
            if not ham.strip():
                continue
            try:
                satir = json.loads(ham)
                satir_dogrula(satir)
            except ValueError as e:
                raise ValueError(f"{dosya.name}:{no}: {e}") from e
            anahtar = (satir["model"], satir["komut"])
            if anahtar in gorulen:
                raise ValueError(f"{dosya.name}:{no}: yinelenen deneme {anahtar}")
            gorulen.add(anahtar)
            sonuc.append(satir)
    return sonuc


def ozet(kayitlar) -> dict:
    sonuc = {}
    for r in kayitlar:
        d = sonuc.setdefault(r["model"], {})
        d[r["durum"]] = d.get(r["durum"], 0) + 1
    return sonuc

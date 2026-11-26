"""Hakem aşaması hazırlığı: klip kodları, hakem metni, çıktı denetimi, ham satırlar.

Yalnız stdlib. Hakemi çalıştırmaz; yalnız girdi hazırlar ve çıktıyı denetler.
"""
import hashlib
import json
import random
import re
import shutil
from pathlib import Path

TOHUM = 20261126
CEVAPLAR = ("evet", "hayir", "gorunmuyor", "hakem_yok")
KARE_EN_AZ, KARE_EN_COK = 1, 50
YARIMLAR = ("tam", "ust", "alt")
_YER_TUTUCU = re.compile(r"\{(komut_en|sorular)\}")


def klip_kodlari(ciftler, tohum=TOHUM) -> dict:
    """(model, komut) çiftlerini sıralar, sabit tohumla karıştırır, K001.. verir."""
    liste = sorted(ciftler)
    if len(set(liste)) != len(liste):
        raise ValueError("ayni (model, komut) cifti birden fazla")
    random.Random(tohum).shuffle(liste)
    return {cift: f"K{i:03d}" for i, cift in enumerate(liste, start=1)}


def _kimlik_metin(soru):
    if isinstance(soru, dict):
        return soru["id"], soru["metin"]
    kimlik, metin = soru
    return kimlik, metin


def hakem_metni(sablon: str, komut_en: str, sorular) -> str:
    """Şablonu doldurur. Yalnız kimlik ve soru metni girer; başka alan girmez."""
    satirlar = [f"{k}: {m}" for k, m in map(_kimlik_metin, sorular)]
    if not satirlar:
        raise ValueError("soru listesi bos")
    deger = {"komut_en": komut_en, "sorular": "\n".join(satirlar)}
    # Tek geçişte doldurulur: araya giren metin yeniden işlenmez, JSON süslü parantezleri kalır.
    return _YER_TUTUCU.sub(lambda m: deger[m.group(1)], sablon)


def _kare_gecerli(kare) -> bool:
    if kare is None or kare == "":
        return True
    if isinstance(kare, bool):
        return False
    if isinstance(kare, str):
        if not kare.isascii() or not kare.isdigit():
            return False
        kare = int(kare)
    if not isinstance(kare, int):
        return False
    return KARE_EN_AZ <= kare <= KARE_EN_COK


def cikti_dogrula(cikti, soru_kimlikleri) -> list:
    """Hakem çıktısını denetler. Hata metinlerinin listesini döndürür; boşsa geçerli."""
    if isinstance(cikti, (str, bytes)):
        try:
            cikti = json.loads(cikti)
        except ValueError as hata:
            return [f"json okunamadi: {hata}"]
    if not isinstance(cikti, dict):
        return ["cikti nesne degil"]
    cevaplar = cikti.get("cevaplar")
    if not isinstance(cevaplar, dict):
        return ["'cevaplar' nesne degil ya da yok"]
    hatalar = []
    beklenen = list(soru_kimlikleri)
    for k in beklenen:
        if k not in cevaplar:
            hatalar.append(f"eksik soru: {k}")
    for k in cevaplar:
        if k not in beklenen:
            hatalar.append(f"fazla soru: {k}")
    for k in beklenen:
        if k not in cevaplar:
            continue
        o = cevaplar[k]
        if not isinstance(o, dict):
            hatalar.append(f"{k}: cevap nesne degil")
            continue
        c = o.get("cevap")
        if not isinstance(c, str) or c not in CEVAPLAR:
            hatalar.append(f"{k}: gecersiz cevap {c!r}")
        if not _kare_gecerli(o.get("kare")):
            hatalar.append(f"{k}: gecersiz kare {o.get('kare')!r}")
    return hatalar


def ham_satirlar(klip, model, komut, cikti, hakem_modeli, calistirma, tarih) -> list:
    """Geçerli çıktıdan judge_raw satırları üretir. Gerekçe ve soru metni girmez."""
    if isinstance(cikti, (str, bytes)):
        cikti = json.loads(cikti)
    hatalar = cikti_dogrula(cikti, list(cikti.get("cevaplar", {})) if isinstance(cikti, dict) else [])
    if hatalar or not cikti["cevaplar"]:
        raise ValueError(f"gecersiz cikti: {hatalar or 'cevap yok'}")
    satirlar = []
    for kimlik, o in cikti["cevaplar"].items():
        kare = o.get("kare")
        kare = None if kare in (None, "") else int(kare)
        satirlar.append({
            "klip": klip, "model": model, "komut": komut, "soru": kimlik,
            "cevap": o["cevap"], "kare": kare, "hakem_modeli": hakem_modeli,
            "calistirma": calistirma, "tarih": tarih,
        })
    return satirlar


def _sha(yol: Path) -> str:
    h = hashlib.sha256()
    with open(yol, "rb") as f:
        for parca in iter(lambda: f.read(1 << 20), b""):
            h.update(parca)
    return h.hexdigest()


def _gercek(klasor: Path) -> list:
    return sorted(p for p in Path(klasor).glob("*.png") if not p.name.startswith("._"))


def kare_kopyala(kaynak, hedef) -> int:
    """tam/ust/alt karelerini (yan dosyalar hariç) hedefe kopyalar ve denetler.

    Hedefte eski içerik varsa önce silinir. Döndürür: kopyalanan dosya adedi.
    """
    kaynak, hedef = Path(kaynak), Path(hedef)
    for ad in YARIMLAR:
        if not _gercek(kaynak / ad):
            raise FileNotFoundError(f"kare yok: {kaynak / ad}")
    if hedef.exists():
        shutil.rmtree(hedef)
    toplam = 0
    for ad in YARIMLAR:
        kaynaklar = _gercek(kaynak / ad)
        (hedef / ad).mkdir(parents=True)
        for p in kaynaklar:
            shutil.copyfile(p, hedef / ad / p.name)
        kopyalar = _gercek(hedef / ad)
        if [p.name for p in kopyalar] != [p.name for p in kaynaklar]:
            raise RuntimeError(f"kopya adedi/adlari uyusmuyor: {ad}")
        for i in sorted({0, len(kaynaklar) // 2, len(kaynaklar) - 1}):
            if _sha(kaynaklar[i]) != _sha(kopyalar[i]):
                raise RuntimeError(f"kopya sha256 uyusmuyor: {ad}/{kaynaklar[i].name}")
        toplam += len(kopyalar)
    return toplam

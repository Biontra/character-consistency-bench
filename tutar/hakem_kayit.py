"""Hakem çıktılarının kayıt kuralları (kodla tutulur). Yalnız stdlib.

Yollar parametre alınır; gerçek veriye dokunmadan geçici klasörle denenir.
Kurallar: geçerli kaydı olan klip yeniden kaydedilmez; klip başına en çok iki
deneme; ikinci geçersizde hakem_yok yazılır; her deneme günlüğe eklenir.
"""
import hashlib
import json
from pathlib import Path

from tutar.hakem import cikti_dogrula, ham_satirlar, hakem_yok_satirlari

EN_COK_DENEME = 2
BEKLENEN_SATIR = 1692


class KayitReddi(Exception):
    """Kural gereği kayıt yapılmadı; hiçbir dosya değişmedi."""


def _esleme(hakem_dizin):
    liste = json.loads((Path(hakem_dizin) / "esleme.json").read_text(encoding="utf-8"))
    return {r["klip"]: r for r in liste}


def _sorular(checks_yolu):
    return json.loads(Path(checks_yolu).read_text(encoding="utf-8"))["komutlar"]


def _klip_bilgisi(kod, hakem_dizin, checks_yolu):
    esleme = _esleme(hakem_dizin)
    if kod not in esleme:
        raise KayitReddi(f"bilinmeyen klip: {kod}")
    r = esleme[kod]
    kimlikler = _sorular(checks_yolu).get(str(r["komut"]))
    if not kimlikler:
        raise KayitReddi(f"{kod}: komutun soru kimlikleri yok")
    return r["model"], r["komut"], list(kimlikler)


def gunluk_oku(hakem_dizin) -> list:
    yol = Path(hakem_dizin) / "gunluk.jsonl"
    if not yol.exists():
        return []
    return [json.loads(s) for s in yol.read_text(encoding="utf-8").splitlines() if s.strip()]


def _yaz_satirlar(yol, satirlar):
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text("".join(json.dumps(s, ensure_ascii=False) + "\n" for s in satirlar),
                   encoding="utf-8")


def kaydet(kod, cikti_yolu, hakem_modeli, tarih, hakem_dizin, checks_yolu) -> dict:
    """Bir hakem çalıştırmasının çıktısını denetler ve kaydeder.

    Döndürür: {"durum": "gecerli" | "gecersiz" | "hakem_yok", "calistirma": n, "hatalar": [...]}
    Reddedilirse KayitReddi atar ve hiçbir şey yazmaz.
    """
    hakem_dizin = Path(hakem_dizin)
    model, komut, kimlikler = _klip_bilgisi(kod, hakem_dizin, checks_yolu)
    onceki = [g for g in gunluk_oku(hakem_dizin) if g["klip"] == kod]
    if any(g["gecerli"] for g in onceki):
        raise KayitReddi(f"{kod}: gecerli kaydi var")
    if len(onceki) >= EN_COK_DENEME:
        raise KayitReddi(f"{kod}: {EN_COK_DENEME} deneme yapildi")
    ham_yol = hakem_dizin / "ham" / f"{kod}.jsonl"
    if ham_yol.exists():
        raise KayitReddi(f"{kod}: ham dosyasi zaten var")
    n = len(onceki) + 1

    veri, sha, hatalar = None, None, []
    try:
        veri = Path(cikti_yolu).read_bytes()
        sha = hashlib.sha256(veri).hexdigest()
    except OSError as hata:
        hatalar = [f"cikti dosyasi okunamadi: {hata.__class__.__name__}"]
    if veri is not None:
        try:
            metin = veri.decode("utf-8")
        except UnicodeDecodeError:
            hatalar = ["cikti utf-8 degil"]
        else:
            hatalar = cikti_dogrula(metin, kimlikler)
    gecerli = not hatalar

    if veri is not None:
        kopya = hakem_dizin / "cikti" / f"{kod}.calistirma{n}.json"
        kopya.parent.mkdir(parents=True, exist_ok=True)
        kopya.write_bytes(veri)
    if gecerli:
        durum = "gecerli"
        _yaz_satirlar(ham_yol, ham_satirlar(kod, model, komut, veri.decode("utf-8"),
                                            kimlikler, hakem_modeli, n, tarih))
    elif n >= EN_COK_DENEME:
        durum = "hakem_yok"
        _yaz_satirlar(ham_yol, hakem_yok_satirlari(kod, model, komut, kimlikler,
                                                   hakem_modeli, n, tarih))
    else:
        durum = "gecersiz"
    # Günlük en son yazılır: önceki adımlar çökerse deneme sayılmaz.
    girdi = {"klip": kod, "calistirma": n, "gecerli": gecerli, "hata_sayisi": len(hatalar),
             "hatalar": hatalar, "cikti_sha256": sha, "hakem_modeli": hakem_modeli,
             "tarih": tarih}
    with open(hakem_dizin / "gunluk.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(girdi, ensure_ascii=False) + "\n")
    return {"durum": durum, "calistirma": n, "hatalar": hatalar}


def durum(hakem_dizin, checks_yolu=None) -> dict:
    """Klip kodlarını duruma göre gruplar (model adı yok)."""
    hakem_dizin = Path(hakem_dizin)
    gunluk = gunluk_oku(hakem_dizin)
    sonuc = {"gecerli": [], "bir_gecersiz_bekliyor": [], "hakem_yok": [], "hic_calismadi": []}
    for kod in sorted(_esleme(hakem_dizin)):
        g = [x for x in gunluk if x["klip"] == kod]
        if any(x["gecerli"] for x in g):
            sonuc["gecerli"].append(kod)
        elif len(g) >= EN_COK_DENEME:
            sonuc["hakem_yok"].append(kod)
        elif g:
            sonuc["bir_gecersiz_bekliyor"].append(kod)
        else:
            sonuc["hic_calismadi"].append(kod)
    return sonuc


def topla(hakem_dizin, checks_yolu, sonuc_yolu, beklenen_satir=None) -> int:
    """Bütün kliplerin ham dosyalarını K sırasıyla birleştirir; satır sayısını döndürür."""
    hakem_dizin = Path(hakem_dizin)
    esleme = _esleme(hakem_dizin)
    sorular = _sorular(checks_yolu)
    eksik = [k for k in sorted(esleme) if not (hakem_dizin / "ham" / f"{k}.jsonl").exists()]
    if eksik:
        raise KayitReddi(f"{len(eksik)} klibin ham dosyasi yok: {', '.join(eksik)}")
    tum = []
    for kod in sorted(esleme):
        satirlar = [json.loads(s) for s in
                    (hakem_dizin / "ham" / f"{kod}.jsonl").read_text(encoding="utf-8").splitlines()
                    if s.strip()]
        kimlikler = list(sorular[str(esleme[kod]["komut"])])
        if [s["soru"] for s in satirlar] != kimlikler or any(s["klip"] != kod for s in satirlar):
            raise KayitReddi(f"{kod}: ham dosya beklenen sorularla uyusmuyor")
        tum.extend(satirlar)
    beklenen = sum(len(sorular[str(esleme[k]["komut"])]) for k in esleme)
    if len(tum) != beklenen:
        raise KayitReddi(f"satir sayisi {len(tum)}, beklenen {beklenen}")
    if beklenen_satir is not None and len(tum) != beklenen_satir:
        raise KayitReddi(f"satir sayisi {len(tum)}, istenen {beklenen_satir}")
    _yaz_satirlar(Path(sonuc_yolu), tum)
    return len(tum)

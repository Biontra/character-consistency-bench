"""Hakem çıktılarının kayıt kuralları (kodla tutulur). Yalnız stdlib.

Yollar parametre alınır; gerçek veriye dokunmadan geçici klasörle denenir.
Kurallar: geçerli kaydı olan klip yeniden kaydedilmez; klip başına en çok iki
deneme; ikinci geçersizde hakem_yok yazılır; her deneme günlüğe eklenir.
Kayıtlar sürüm klasöründe tutulur (<hakem_dizin>/<sürüm>/); sayaç sürüm başınadır.
Araç kaydı taraması geçersiz bulunduysa (tarama_hatasi) çıktı biçimce doğru olsa
bile deneme geçersizdir. Çıktı dosyasının sha256'sı aynı klibin (aynı sürümde) önceki
bir denemesininkiyle aynıysa kayıt reddedilir (bayat çıktı dosyası koruması). esleme.json sürüm klasörünün dışında, hakem_dizin içindedir.
"""
import hashlib
import json
import re
from pathlib import Path

from tutar.hakem import cikti_dogrula, ham_satirlar, hakem_yok_satirlari

EN_COK_DENEME = 2
BEKLENEN_SATIR = 1692
VARSAYILAN_SURUM = "v1"
_SURUM_DESENI = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*")


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


def surum_dizini(hakem_dizin, surum=VARSAYILAN_SURUM) -> Path:
    if not isinstance(surum, str) or not _SURUM_DESENI.fullmatch(surum) or ".." in surum:
        raise KayitReddi(f"gecersiz surum adi: {surum!r}")
    return Path(hakem_dizin) / surum


def gunluk_oku(hakem_dizin, surum=VARSAYILAN_SURUM) -> list:
    yol = surum_dizini(hakem_dizin, surum) / "gunluk.jsonl"
    if not yol.exists():
        return []
    return [json.loads(s) for s in yol.read_text(encoding="utf-8").splitlines() if s.strip()]


def _yaz_satirlar(yol, satirlar):
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text("".join(json.dumps(s, ensure_ascii=False) + "\n" for s in satirlar),
                   encoding="utf-8")


def kaydet(kod, cikti_yolu, hakem_modeli, tarih, hakem_dizin, checks_yolu,
           tarama_hatasi=None, surum=VARSAYILAN_SURUM) -> dict:
    """Bir hakem çalıştırmasının çıktısını denetler ve kaydeder.

    tarama_hatasi: araç kaydı taramasının bulduğu sorun (metin). None ise tarama
    temiz bildirilmiştir; doluysa deneme çıktı biçimce doğru olsa da GEÇERSİZdir.
    Döndürür: {"durum": "gecerli" | "gecersiz" | "hakem_yok", "calistirma": n,
               "hatalar": [...], "tarama_hatasi": str | None}
    Reddedilirse KayitReddi atar ve hiçbir şey yazmaz.
    """
    hakem_dizin = Path(hakem_dizin)
    sdizin = surum_dizini(hakem_dizin, surum)
    model, komut, kimlikler = _klip_bilgisi(kod, hakem_dizin, checks_yolu)
    onceki = [g for g in gunluk_oku(hakem_dizin, surum) if g["klip"] == kod]
    if any(g["gecerli"] for g in onceki):
        raise KayitReddi(f"{kod}: gecerli kaydi var")
    if len(onceki) >= EN_COK_DENEME:
        raise KayitReddi(f"{kod}: {EN_COK_DENEME} deneme yapildi")
    ham_yol = sdizin / "ham" / f"{kod}.jsonl"
    if ham_yol.exists():
        raise KayitReddi(f"{kod}: ham dosyasi zaten var")
    n = len(onceki) + 1

    veri, sha, hatalar = None, None, []
    try:
        veri = Path(cikti_yolu).read_bytes()
        sha = hashlib.sha256(veri).hexdigest()
    except OSError as hata:
        hatalar = [f"cikti dosyasi okunamadi: {hata.__class__.__name__}"]
    if sha is not None and any(g.get("cikti_sha256") == sha for g in onceki):
        # Bayat dosya koruması: aynı klibin (aynı sürümde) önceki bir denemesiyle
        # birebir aynı çıktı yeni cevap sayılmaz. Hiçbir şey yazılmaz, deneme sayılmaz.
        raise KayitReddi(f"{kod}: cikti dosyasi onceki bir denemeyle birebir ayni (bayat dosya)")
    if veri is not None:
        try:
            metin = veri.decode("utf-8")
        except UnicodeDecodeError:
            hatalar = ["cikti utf-8 degil"]
        else:
            hatalar = cikti_dogrula(metin, kimlikler)
    gecerli = not hatalar and tarama_hatasi is None

    if veri is not None:
        kopya = sdizin / "cikti" / f"{kod}.calistirma{n}.json"
        kopya.parent.mkdir(parents=True, exist_ok=True)
        kopya.write_bytes(veri)
    if gecerli:
        durum = "gecerli"
        satirlar = ham_satirlar(kod, model, komut, veri.decode("utf-8"),
                                kimlikler, hakem_modeli, n, tarih)
        _yaz_satirlar(ham_yol, [dict(x, surum=surum) for x in satirlar])
    elif n >= EN_COK_DENEME:
        durum = "hakem_yok"
        satirlar = hakem_yok_satirlari(kod, model, komut, kimlikler,
                                       hakem_modeli, n, tarih)
        _yaz_satirlar(ham_yol, [dict(x, surum=surum) for x in satirlar])
    else:
        durum = "gecersiz"
    # Günlük en son yazılır: önceki adımlar çökerse deneme sayılmaz.
    girdi = {"klip": kod, "calistirma": n, "gecerli": gecerli, "hata_sayisi": len(hatalar),
             "hatalar": hatalar, "cikti_sha256": sha, "hakem_modeli": hakem_modeli,
             "tarih": tarih, "surum": surum,
             "tarama": "temiz" if tarama_hatasi is None else "gecersiz"}
    if tarama_hatasi is not None:
        girdi["tarama_hatasi"] = tarama_hatasi
    sdizin.mkdir(parents=True, exist_ok=True)
    with open(sdizin / "gunluk.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(girdi, ensure_ascii=False) + "\n")
    return {"durum": durum, "calistirma": n, "hatalar": hatalar,
            "tarama_hatasi": tarama_hatasi}


def durum(hakem_dizin, checks_yolu=None, surum=VARSAYILAN_SURUM) -> dict:
    """Klip kodlarını duruma göre gruplar (model adı yok). Yalnız verilen sürüm."""
    hakem_dizin = Path(hakem_dizin)
    gunluk = gunluk_oku(hakem_dizin, surum)
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


def topla(hakem_dizin, checks_yolu, sonuc_yolu, beklenen_satir=None,
          surum=VARSAYILAN_SURUM) -> int:
    """Verilen sürümün ham dosyalarını K sırasıyla birleştirir; satır sayısını döndürür."""
    hakem_dizin = Path(hakem_dizin)
    sdizin = surum_dizini(hakem_dizin, surum)
    esleme = _esleme(hakem_dizin)
    sorular = _sorular(checks_yolu)
    eksik = [k for k in sorted(esleme) if not (sdizin / "ham" / f"{k}.jsonl").exists()]
    if eksik:
        raise KayitReddi(f"{len(eksik)} klibin ham dosyasi yok: {', '.join(eksik)}")
    tum = []
    for kod in sorted(esleme):
        satirlar = [json.loads(s) for s in
                    (sdizin / "ham" / f"{kod}.jsonl").read_text(encoding="utf-8").splitlines()
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

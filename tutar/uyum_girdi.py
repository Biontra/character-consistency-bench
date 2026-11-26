"""Uyum girdi çeviricisi ve yan sayılar (PROTOCOL.md, "Hakem çalıştırma kaydına ekler" madde 5, 6, 8).

Gizli soru dosyası + eşleme + insan cevap dosyası + hakem ham satırları ->
`uyum_raporu(insan, hakem, sorular)` girdileri. Biçim hatası sessiz yanlış sonuç
vermez: GirdiHatasi (ValueError). Yalnız stdlib; dosya okumaz (betik okur).
"""
from tutar.uyum_hesap import INSAN_CEVAPLARI, uyum_raporu
from tutar.puan import CEVAPLAR as HAKEM_CEVAPLARI


class GirdiHatasi(ValueError):
    pass


def _klip_sorulari(checks, esleme):
    """{klip: [soru tanimi]} (puansizlar dahil) ve bilinen klip kümesi."""
    tanim = {s["id"]: s for s in checks["sorular"]}
    kayit = {}
    for r in esleme:
        kimlikler = checks["komutlar"].get(str(r["komut"]))
        if not kimlikler:
            raise GirdiHatasi(f"{r['klip']}: komutun soru listesi yok")
        eksik = [k for k in kimlikler if k not in tanim]
        if eksik:
            raise GirdiHatasi(f"{r['klip']}: soru tanimi yok: {eksik}")
        kayit[r["klip"]] = [dict(tanim[k]) for k in kimlikler]
    return kayit


def cevir(checks, esleme, insan_dosya, hakem_satirlari):
    """Döndürür: (insan, hakem, sorular) = uyum_raporu girdileri."""
    if not isinstance(insan_dosya, dict) or insan_dosya.get("bitti") is not True:
        raise GirdiHatasi("insan dosyasi bitmemis (bitti true degil)")
    cevaplar = insan_dosya.get("cevaplar")
    if not isinstance(cevaplar, dict) or not cevaplar:
        raise GirdiHatasi("insan dosyasinda cevap yok")
    tum = _klip_sorulari(checks, esleme)
    for klip in cevaplar:
        if klip not in tum:
            raise GirdiHatasi(f"insan dosyasinda bilinmeyen klip: {klip}")
    hakem_hepsi = {}
    for s in hakem_satirlari:
        klip, soru, cevap = s.get("klip"), s.get("soru"), s.get("cevap")
        if klip not in tum:
            raise GirdiHatasi(f"hakem kaydinda bilinmeyen klip: {klip}")
        if klip not in cevaplar:
            continue  # insanin puanlamadigi klip
        if (klip, soru) in hakem_hepsi:
            raise GirdiHatasi(f"hakem kaydinda ayni soru iki kez: {klip} {soru}")
        if not isinstance(cevap, str) or cevap not in HAKEM_CEVAPLARI:
            raise GirdiHatasi(f"hakem cevabi gecersiz: {klip} {soru} {cevap!r}")
        hakem_hepsi[(klip, soru)] = cevap
    insan, hakem, sorular = {}, {}, {}
    for klip in sorted(cevaplar):
        beklenen = [s["id"] for s in tum[klip]]
        i = cevaplar[klip]
        if not isinstance(i, dict) or sorted(i) != sorted(beklenen):
            raise GirdiHatasi(f"{klip}: insan cevaplari soru listesiyle ayni degil")
        for k, v in i.items():
            if v not in INSAN_CEVAPLARI:
                raise GirdiHatasi(f"{klip} {k}: insan cevabi gecersiz {v!r}")
        h = {k: v for (kl, k), v in hakem_hepsi.items() if kl == klip}
        if sorted(h) != sorted(beklenen):
            raise GirdiHatasi(f"{klip}: hakem cevaplari soru listesiyle ayni degil")
        insan[klip] = dict(i)
        hakem[klip] = h
        sorular[klip] = tum[klip]
    return insan, hakem, sorular


def _ozet(r):
    return {"uyum": r["uyum"], "uyusan": r["uyusan"], "birim": r["birim"]}


def hesapla(checks, esleme, insan_dosya, hakem_satirlari):
    """Ana sayı (uyum_raporu aynen), iki yan sayı (eşiksiz) ve ek sayılar."""
    insan, hakem, sorular = cevir(checks, esleme, insan_dosya, hakem_satirlari)
    ana = uyum_raporu(insan, hakem, sorular)

    tumu = sorted(k for k in insan if all(v == "hakem_yok" for v in hakem[k].values()))
    kalan = [k for k in insan if k not in tumu]
    a = uyum_raporu({k: insan[k] for k in kalan}, {k: hakem[k] for k in kalan},
                    {k: sorular[k] for k in kalan})

    puansiz = {k: {s["id"] for s in sorular[k] if s["sutun"] == "puansiz"} for k in insan}

    def birim_kalir(k, s):
        return s in puansiz[k] or hakem[k][s] != "hakem_yok"

    b_insan = {k: {s: v for s, v in insan[k].items() if birim_kalir(k, s)} for k in insan}
    b_hakem = {k: {s: v for s, v in hakem[k].items() if birim_kalir(k, s)} for k in insan}
    b_sor = {k: [s for s in sorular[k] if birim_kalir(k, s["id"])] for k in insan}
    b = uyum_raporu(b_insan, b_hakem, b_sor)

    yan_a = _ozet(a)
    yan_a["cikarilan_klip"] = len(tumu)
    yan_b = _ozet(b)
    yan_b["cikarilan_birim"] = ana["birim"] - b["birim"]
    return {
        "ana": ana,
        "yan_sayilar": {"tumu_hakem_yok_klipler_cikarilinca": yan_a,
                        "hakem_yok_birimler_cikarilinca": yan_b},
        "gorunmuyor_hakem_yok_cift": ana["karisiklik"]["gorunmuyor"]["hakem_yok"],
        "tumu_hakem_yok_klipler": tumu,
        "klip_sayisi": len(insan),
    }

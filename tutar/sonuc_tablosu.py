"""Sonuç tablosu: hakem ham satırlarından model başına sayılar (PROTOCOL.md).

Saf fonksiyonlar, yalnız stdlib, dosya okumaz. Bütün puan hesapları
`tutar/puan.py` fonksiyonlarından gelir (klip_puanla, uretilemeyen_klip,
model_ozeti, ortak_komutlar, ortak_tuttu); burada yeni puanlama kuralı yoktur.
Bu dosya yalnız klip sonuçlarını toplar (pay/payda), sayar ve düzenler.
Biçim hatası sessiz yanlış sonuç vermez: ValueError.
"""
from tutar.puan import (
    TURLER,
    klip_puanla,
    model_ozeti,
    ortak_komutlar,
    ortak_tuttu,
    uretilemeyen_klip,
)

# data/models.json ve üretim kaydındaki durumlar (tutar/kayit.py DURUMLAR ile uyumlu).
# Reddedilen işin kredisi iade edildi (uretim_kaydi/kredi_ozeti.md). Üretim hatasında
# iade bilgisi yok; bu durumda sessizce tahmin yürütmeyiz.
URETILEMEYEN_DURUMLAR = ("reddedildi", "uretim_hatasi")


def _komut_listesi(checks):
    try:
        return sorted(int(k) for k in checks["komutlar"])
    except (KeyError, TypeError, ValueError):
        raise ValueError("checks.komutlar okunamadi")


def _soru_tanimlari(checks):
    tanim = {}
    for s in checks["sorular"]:
        if s["id"] in tanim:
            raise ValueError(f"soru kimligi iki kez: {s['id']}")
        tanim[s["id"]] = s
    return tanim


def _komut_sorulari(checks, tanim, komut):
    kimlikler = checks["komutlar"].get(str(komut))
    if not kimlikler:
        raise ValueError(f"komut {komut}: soru listesi yok")
    eksik = [k for k in kimlikler if k not in tanim]
    if eksik:
        raise ValueError(f"komut {komut}: soru tanimi yok: {eksik}")
    return [dict(tanim[k]) for k in kimlikler]


def _uretilemeyenleri_coz(uretilemeyen, model_idleri, komutlar):
    """{(model, komut): durum}. Bilinmeyen model/komut/durum ve tekrar ValueError."""
    sonuc = {}
    for u in uretilemeyen:
        model, komut, durum = u.get("model"), u.get("komut"), u.get("durum")
        if model not in model_idleri:
            raise ValueError(f"uretilemeyen listede bilinmeyen model: {model!r}")
        if komut not in komutlar:
            raise ValueError(f"uretilemeyen listede bilinmeyen komut: {komut!r}")
        if durum not in URETILEMEYEN_DURUMLAR:
            raise ValueError(f"uretilemeyen durumu bilinmiyor: {durum!r}")
        if (model, komut) in sonuc:
            raise ValueError(f"uretilemeyen listede ayni cift iki kez: {model} {komut}")
        sonuc[(model, komut)] = durum
    return sonuc


def _satirlari_grupla(hakem_satirlari, model_idleri, komutlar, tanimli_sorular, uretilemeyen):
    """{(model, komut): {soru: cevap}}. Tekrar, bilinmeyen alan ve üretilemeyen klibin satırı hata."""
    gruplar = {}
    for s in hakem_satirlari:
        model, komut, soru = s.get("model"), s.get("komut"), s.get("soru")
        if model not in model_idleri:
            raise ValueError(f"hakem kaydinda bilinmeyen model: {model!r}")
        if komut not in komutlar:
            raise ValueError(f"hakem kaydinda bilinmeyen komut: {komut!r}")
        if (model, komut) in uretilemeyen:
            raise ValueError(f"uretilemeyen klip icin hakem cevabi var: {model} {komut}")
        if soru not in tanimli_sorular[komut]:
            raise ValueError(f"komut {komut} icin tanimsiz soru: {soru!r}")
        cevaplar = gruplar.setdefault((model, komut), {})
        if soru in cevaplar:
            raise ValueError(f"hakem kaydinda ayni soru iki kez: {model} {komut} {soru}")
        cevaplar[soru] = s.get("cevap")
    return gruplar


def _topla_cift(klipler, anahtar):
    return [sum(k[anahtar][0] for k in klipler), sum(k[anahtar][1] for k in klipler)]


def _pay_payda(pay, payda):
    return {"pay": pay, "payda": payda}


def hesapla(checks, hakem_satirlari, uretilemeyen, modeller):
    """Model başına sonuç tablosu girdisi.

    checks: {"sorular": [...], "komutlar": {"1": [soru kimlikleri], ...}}
    hakem_satirlari: [{"model", "komut", "soru", "cevap", ...}] (klip kodu gerekmez)
    uretilemeyen: [{"model", "komut", "durum"}]  durum: reddedildi | uretim_hatasi
    modeller: data/models.json "modeller" listesi ({"id", "ad", "kredi_teklif"}); sıra korunur.

    Her model için her komutun ya üretilemeyen listesinde olması ya da hakem
    satırlarında bütün sorularıyla bulunması şart; aksi ValueError (eksik soru
    "hayır" sayılmaz).
    """
    model_idleri = [m["id"] for m in modeller]
    if len(set(model_idleri)) != len(model_idleri) or not model_idleri:
        raise ValueError("model listesi bos ya da tekrarli")
    komutlar = _komut_listesi(checks)
    komut_kumesi = set(komutlar)
    tanim = _soru_tanimlari(checks)
    komut_sorulari = {k: _komut_sorulari(checks, tanim, k) for k in komutlar}
    tanimli = {k: {s["id"] for s in v} for k, v in komut_sorulari.items()}
    atlanan = _uretilemeyenleri_coz(uretilemeyen, set(model_idleri), komut_kumesi)
    gruplar = _satirlari_grupla(hakem_satirlari, set(model_idleri), komut_kumesi, tanimli, atlanan)

    # {model: {komut: klip sonucu}} ve tümü hakem_yok olan klipler
    sonuclar = {}
    tumu_hakem_yok = {}
    for model in model_idleri:
        klipler, tumu = {}, set()
        for komut in komutlar:
            sorular = komut_sorulari[komut]
            if (model, komut) in atlanan:
                klipler[komut] = uretilemeyen_klip(sorular)
                continue
            cevaplar = gruplar.get((model, komut))
            if cevaplar is None:
                raise ValueError(f"hakem cevabi yok: {model} komut {komut}")
            klipler[komut] = klip_puanla(sorular, cevaplar)  # eksik soru ve bilinmeyen cevap burada hata
            if all(v == "hakem_yok" for v in cevaplar.values()):
                tumu.add(komut)
        sonuclar[model] = klipler
        tumu_hakem_yok[model] = tumu

    uretilen = {m: sorted(k for k, v in sonuclar[m].items() if not v.get("uretilemedi"))
                for m in model_idleri}
    ortak = ortak_komutlar(uretilen)
    hakemli_ortak = [k for k in ortak if all(k not in tumu_hakem_yok[m] for m in model_idleri)]

    modeller_cikti = []
    for m in modeller:
        mid = m["id"]
        klip_listesi = [sonuclar[mid][k] for k in komutlar]
        ozet = model_ozeti(klip_listesi)
        yapti = _topla_cift(klip_listesi, "yapti")
        tuttu = _topla_cift(klip_listesi, "tuttu")
        tur = {t: _pay_payda(*[sum(k["tur"][t][i] for k in klip_listesi) for i in (0, 1)])
               for t in TURLER}
        for t in TURLER:
            tur[t]["yuzde"] = ozet["tur_yuzde"][t]
        ortak_sonuc = ortak_tuttu([(k, sonuclar[mid][k]) for k in komutlar], ortak)

        iade = sum(1 for (md, _), d in atlanan.items() if md == mid and d == "reddedildi")
        if any(md == mid and d != "reddedildi" for (md, _), d in atlanan.items()):
            raise ValueError(f"{mid}: uretim hatasi olan klibin kredi iadesi bilinmiyor")
        kredi_klip = m.get("kredi_teklif")
        kredi_toplam = None if kredi_klip is None else kredi_klip * (len(komutlar) - iade)

        def bol(pay):
            return None if kredi_toplam is None or pay == 0 else kredi_toplam / pay

        modeller_cikti.append({
            "model": mid,
            "ad": m.get("ad", mid),
            "uretti": ozet["uretti"],
            "toplam_klip": ozet["toplam_klip"],
            "yapti": dict(_pay_payda(*yapti), yuzde=ozet["yapti_yuzde"]),
            "tuttu": dict(_pay_payda(*tuttu), yuzde=ozet["tuttu_yuzde"]),
            "tur": tur,
            "ortak_tuttu": {"pay": ortak_sonuc["pay"], "payda": ortak_sonuc["payda"],
                            "yuzde": ortak_sonuc["tuttu_yuzde"]},
            "gorunmuyor": ozet["disarida"]["gorunmuyor"],
            "hakem_yok": ozet["disarida"]["hakem_yok"],
            "gecersiz": ozet["disarida"]["gecersiz"],
            "olculemeyen_klip": ozet["olculemeyen_klip"],
            "hakemin_puanladigi_klip": ozet["uretti"] - len(tumu_hakem_yok[mid]),
            "tumu_hakem_yok_klip": len(tumu_hakem_yok[mid]),
            "kredi": {
                "klip_basina_teklif": kredi_klip,
                "iade_edilen_klip": iade,
                "toplam": kredi_toplam,
                "yapan_cevap_basina": bol(yapti[0]),
                "tutan_cevap_basina": bol(tuttu[0]),
            },
        })

    return {
        "komut_sayisi": len(komutlar),
        "modeller": modeller_cikti,
        "ortak_komutlar": {
            "komutlar": ortak,
            "sayi": len(ortak),
            "tum_modellerde_hakem_cevabi_olan_komut_sayisi": len(hakemli_ortak),
        },
    }

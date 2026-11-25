"""TUTAR puanlama: iki sütun (yaptı / tuttu), hiçbir yerde toplanmaz."""

CEVAPLAR = ("evet", "hayir", "gorunmuyor", "hakem_yok")
SUTUNLAR = ("yapti", "tuttu")
TURLER = ("ortak", "grup", "ozel")
PUANLANABILIR = ("evet", "hayir")


def _cevap_kontrol(kimlik, cevap):
    if not isinstance(cevap, str) or cevap not in CEVAPLAR:
        raise ValueError(f"bilinmeyen cevap {cevap!r} (soru {kimlik})")


SORU_SUTUNLARI = SUTUNLAR + ("puansiz",)


def _sutun_kontrol(sorular):
    for s in sorular:
        if s["sutun"] not in SORU_SUTUNLARI:
            raise ValueError(f"bilinmeyen sutun {s['sutun']!r} (soru {s['id']})")


def klip_puanla(sorular, cevaplar):
    """Tek klibin cevaplarını puanlar. Eksik soru ya da bilinmeyen değer ValueError."""
    _sutun_kontrol(sorular)
    for s in sorular:
        if s["id"] not in cevaplar:
            raise ValueError(f"eksik cevap: {s['id']}")
    for kimlik, cevap in cevaplar.items():
        _cevap_kontrol(kimlik, cevap)

    # Yaptı sütunundaki bir soru beklenenden farklı (evet/hayir) cevaplandıysa
    # eyleme bağlı sorular geçersiz olur.
    eylem_yok = any(
        s["sutun"] == "yapti"
        and cevaplar[s["id"]] in PUANLANABILIR
        and cevaplar[s["id"]] != s["beklenen"]
        for s in sorular
    )

    sut = {k: [0, 0] for k in SUTUNLAR}
    tur = {k: [0, 0] for k in TURLER}
    disarida = {"gorunmuyor": 0, "hakem_yok": 0, "gecersiz": 0}

    for s in sorular:
        if s["sutun"] == "puansiz":
            continue
        cevap = cevaplar[s["id"]]
        if cevap in ("gorunmuyor", "hakem_yok"):
            disarida[cevap] += 1
            continue
        if eylem_yok and s["eyleme_bagli"] and s["sutun"] != "yapti":
            disarida["gecersiz"] += 1
            continue
        dogru = 1 if cevap == s["beklenen"] else 0
        sut[s["sutun"]][0] += dogru
        sut[s["sutun"]][1] += 1
        if s["tur"] in tur:
            tur[s["tur"]][0] += dogru
            tur[s["tur"]][1] += 1

    return {
        "yapti": tuple(sut["yapti"]),
        "tuttu": tuple(sut["tuttu"]),
        "tur": {k: tuple(v) for k, v in tur.items()},
        "disarida": disarida,
    }


def uretilemeyen_klip(sorular):
    """Üretilemeyen (reddedilen ya da üretim hatası alan) klibin sonucu.

    "yapti" sütunundaki puanlı sorular yanlış sayılır: paydaya girer, paya girmez.
    Karakter soruları ve tür kırılımı hiç sayılmaz. "puansiz" sorular yok sayılır.
    Çıktı klip_puanla ile aynı yapıdadır, ek olarak "uretilemedi": True taşır.
    """
    _sutun_kontrol(sorular)
    yapti_sayisi = sum(1 for s in sorular if s["sutun"] == "yapti")
    return {
        "yapti": (0, yapti_sayisi),
        "tuttu": (0, 0),
        "tur": {k: (0, 0) for k in TURLER},
        "disarida": {"gorunmuyor": 0, "hakem_yok": 0, "gecersiz": 0},
        "uretilemedi": True,
    }


def _yuzde(dogru, sayilan):
    return None if sayilan == 0 else dogru / sayilan * 100


def model_puanla(klipler):
    """Klip sonuçlarını havuzlar. Payda 0 ise yüzde None (ölçülemedi)."""
    sut = {k: [0, 0] for k in SUTUNLAR}
    tur = {k: [0, 0] for k in TURLER}
    disarida = {"gorunmuyor": 0, "hakem_yok": 0, "gecersiz": 0}
    olculemeyen = 0
    for k in klipler:
        for ad in SUTUNLAR:
            sut[ad][0] += k[ad][0]
            sut[ad][1] += k[ad][1]
        for ad in TURLER:
            tur[ad][0] += k["tur"][ad][0]
            tur[ad][1] += k["tur"][ad][1]
        for ad in disarida:
            disarida[ad] += k["disarida"][ad]
        if k.get("uretilemedi"):
            continue  # üretilemeyen klip ayrı sayılır, "ölçülemeyen" değildir
        if k["yapti"][1] + k["tuttu"][1] == 0:
            olculemeyen += 1
    return {
        "yapti_yuzde": _yuzde(*sut["yapti"]),
        "tuttu_yuzde": _yuzde(*sut["tuttu"]),
        "tur_yuzde": {k: _yuzde(*v) for k, v in tur.items()},
        "olculemeyen_klip": olculemeyen,
        "disarida": disarida,
    }


def model_ozeti(klipler):
    """model_puanla çıktısına üretilen ve toplam klip sayısını ekler."""
    ozet = model_puanla(klipler)
    ozet["uretti"] = sum(1 for k in klipler if not k.get("uretilemedi"))
    ozet["toplam_klip"] = len(klipler)
    return ozet


def uyum(insan, hakem):
    """Aynı anahtarlarda birebir aynı cevap oranı. Dört değer de cevap sayılır."""
    if set(insan) != set(hakem):
        raise ValueError("insan ve hakem anahtar kümeleri farklı")
    if not insan:
        raise ValueError("karşılaştırılacak cevap yok")
    for kimlik in insan:
        _cevap_kontrol(kimlik, insan[kimlik])
        _cevap_kontrol(kimlik, hakem[kimlik])
    return sum(insan[k] == hakem[k] for k in insan) / len(insan)

"""İnsan-hakem uyum hesabı (PROTOCOL.md, "Uyum hesabının kapsamı" ve eki).

Saf fonksiyon; dosyaya ya da ağa dokunmaz. Birim = (klip, soru) çifti. Hiçbir
puanlı birim paydadan çıkmaz (eyleme bağlı sorular dahil): bu puan hesabından
(tutar/puan.py) farklıdır. gorunmuyor ve hakem_yok da birer cevaptır.
"""
from tutar.puan import CEVAPLAR, SORU_SUTUNLARI

ESIK = 0.85
INSAN_CEVAPLARI = ("evet", "hayir", "gorunmuyor")
NET = ("evet", "hayir")


def uyum_raporu(insan, hakem, sorular):
    """Girdi biçimi (anahtar = klip kodu, sonra soru kimliği):

    insan:   {klip: {soru_id: cevap}}  cevap yalnız evet / hayir / gorunmuyor
    hakem:   {klip: {soru_id: cevap}}  cevap dört değerden biri
    sorular: {klip: [soru tanımı, ...]} tanım: {"id", "sutun", ...}; sutun
             "puansiz" olan sorular KENDİSİ dışlanır.

    Karşılaştırılan klipler `insan` içindekilerdir; hakemde olup insanda olmayan
    klipler yok sayılır. İnsanın klibinde bir puanlı soru insanda ya da hakemde
    eksikse, klip sorulara yoksa, bilinmeyen soru kimliği ya da cevap değeri
    varsa ValueError.

    Döndürür: uyum (oran ya da None), uyusan, birim, dislanan_puansiz,
    net_uyum (None olabilir), net_birim, karisiklik[insan][hakem] adetleri
    (3 insan x 4 hakem cevabı), esik_gecti (uyum >= 0.85; birim 0 ise False).
    """
    karisiklik = {i: {h: 0 for h in CEVAPLAR} for i in INSAN_CEVAPLARI}
    birim = uyusan = net_birim = net_uyusan = dislanan = 0
    for klip in sorted(insan):
        if klip not in sorular:
            raise ValueError(f"klip {klip}: soru tanimi yok")
        for s in sorular[klip]:
            if s["sutun"] not in SORU_SUTUNLARI:
                raise ValueError(f"bilinmeyen sutun {s['sutun']!r} (soru {s['id']})")
        bilinen = {s["id"] for s in sorular[klip]}
        for kimlik in insan[klip]:
            if kimlik not in bilinen:
                raise ValueError(f"klip {klip}: bilinmeyen soru kimligi {kimlik!r}")
        if klip not in hakem:
            raise ValueError(f"klip {klip}: hakem cevabi yok")
        for s in sorular[klip]:
            if s["sutun"] == "puansiz":
                dislanan += 1
                continue
            kimlik = s["id"]
            if kimlik not in insan[klip]:
                raise ValueError(f"klip {klip}: insan cevabi eksik ({kimlik})")
            if kimlik not in hakem[klip]:
                raise ValueError(f"klip {klip}: hakem cevabi eksik ({kimlik})")
            i, h = insan[klip][kimlik], hakem[klip][kimlik]
            if i not in INSAN_CEVAPLARI:
                raise ValueError(f"insan cevabi gecersiz {i!r} ({klip} {kimlik})")
            if not isinstance(h, str) or h not in CEVAPLAR:
                raise ValueError(f"hakem cevabi gecersiz {h!r} ({klip} {kimlik})")
            karisiklik[i][h] += 1
            birim += 1
            uyusan += i == h
            if i in NET and h in NET:
                net_birim += 1
                net_uyusan += i == h
    uyum = None if birim == 0 else uyusan / birim
    return {
        "uyum": uyum,
        "uyusan": uyusan,
        "birim": birim,
        "dislanan_puansiz": dislanan,
        "net_uyum": None if net_birim == 0 else net_uyusan / net_birim,
        "net_birim": net_birim,
        "karisiklik": karisiklik,
        "esik_gecti": uyum is not None and uyum >= ESIK,
    }

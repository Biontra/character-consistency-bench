"""Sonuç tablosunu üretir: results.json, sonuclar.csv, RESULTS.md ve üç SVG grafik. Yalnız stdlib.

Kullanım: python3 scripts/sonuc_uret.py --checks secret/checks.json
          --hakem-ham results/judge_raw.jsonl --uretim-kaydi uretim_kaydi
          --modeller data/models.json --cikti-dizin results
          [--uyum-raporu uyum.json]
Yolların hepsi zorunludur (varsayılan yok). --uyum-raporu, scripts/uyum_hesapla.py çıktısıdır;
verilmezse RESULTS.md "insan puanlaması henüz yapılmadı" yazar.
Aynı girdide aynı çıktı (zaman damgası yok, sıralı). Hesaplar tutar/sonuc_tablosu.py'den,
o da tutar/puan.py'den gelir. Soru metinleri hiçbir çıktıya girmez.
"""
import argparse
import csv
import json
import sys
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tutar.puan import TURLER  # noqa: E402
from tutar.sonuc_tablosu import hesapla  # noqa: E402

ESIK = 0.85  # tutar/uyum_hesap.py ESIK ile aynı; yalnız gösterim için, karar uyum raporundaki esik_gecti'den gelir
TUR_AD = {"ortak": "ortak", "grup": "grup", "ozel": "özel"}


class GirdiButunluguHatasi(ValueError):
    pass


def uretilemeyenleri_oku(dizin):
    """uretim_kaydi/*.jsonl içinde durumu 'tamam' olmayan satırlar.

    Kayıt dizini yoksa, boşsa ya da aynı (model, komut) çifti iki kez geçerse ValueError.
    """
    yol_dizin = Path(dizin)
    if not yol_dizin.is_dir():
        raise GirdiButunluguHatasi(f"üretim kaydı dizini bulunamadı: {dizin}")
    dosyalar = sorted(yol_dizin.glob("*.jsonl"))
    if not dosyalar:
        raise GirdiButunluguHatasi(f"üretim kaydı boş veya jsonl dosyası yok: {dizin}")
    sonuc = []
    gorulen = set()
    toplam_satir = 0
    for yol in dosyalar:
        for sira, s in enumerate(yol.read_text(encoding="utf-8").splitlines(), 1):
            if not s.strip():
                continue
            toplam_satir += 1
            r = json.loads(s)
            try:
                model, komut, durum = r["model"], r["komut"], r["durum"]
            except (KeyError, TypeError) as hata:
                raise GirdiButunluguHatasi(f"üretim kaydı satırı eksik alan ({yol.name}:{sira}): {hata}")
            cift = (model, komut)
            if cift in gorulen:
                raise GirdiButunluguHatasi(f"üretim kaydında aynı (model, komut) çifti iki kez geçti: {model} {komut}")
            gorulen.add(cift)
            if durum != "tamam":
                sonuc.append({"model": model, "komut": komut, "durum": durum})
    if toplam_satir == 0:
        raise GirdiButunluguHatasi(f"üretim kaydı boş (hiç satır yok): {dizin}")
    return sorted(sonuc, key=lambda u: (u["model"], u["komut"]))


def yuzde_sayi(v):
    """Yüzde sayılarını tek noktadan %.1f biçiminde yazar."""
    return f"{v:.1f}"


def yuzde(d):
    return "ölçülemedi" if d["yuzde"] is None else f"%{yuzde_sayi(d['yuzde'])} ({d['pay']}/{d['payda']})"


def sayi(x):
    if x is None:
        return "-"
    return f"{x:.2f}".rstrip("0").rstrip(".")


def csv_yuzde(y):
    return "" if y is None else yuzde_sayi(y)


def csv_sayi(x):
    return "" if x is None else sayi(x)


def csv_yaz(yol, sonuc):
    sut = ["model", "uretti", "toplam_klip",
           "yapti_pay", "yapti_payda", "yapti_yuzde",
           "tuttu_pay", "tuttu_payda", "tuttu_yuzde",
           "ortak_komut_tuttu_pay", "ortak_komut_tuttu_payda", "ortak_komut_tuttu_yuzde"]
    for t in TURLER:
        sut += [f"tur_{t}_pay", f"tur_{t}_payda", f"tur_{t}_yuzde"]
    sut += ["gorunmuyor", "hakem_yok", "gecersiz_eyleme_bagli", "olculemeyen_klip",
            "hakemin_puanladigi_klip", "tumu_hakem_yok_klip",
            "kredi_klip_basina", "kredi_toplam", "kredi_komutu_yapan_cevap_basina",
            "kredi_tutulan_karakter_cevabi_basina",
            "kredi_puanlanan_toplam", "kredi_puanlanan_komutu_yapan_cevap_basina",
            "kredi_puanlanan_tutulan_karakter_cevabi_basina"]
    with open(yol, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(sut)
        for m in sonuc["modeller"]:
            o = m["ortak_tuttu"]
            satir = [m["model"], m["uretti"], m["toplam_klip"],
                     m["yapti"]["pay"], m["yapti"]["payda"], csv_yuzde(m["yapti"]["yuzde"]),
                     m["tuttu"]["pay"], m["tuttu"]["payda"], csv_yuzde(m["tuttu"]["yuzde"]),
                     o["pay"], o["payda"], csv_yuzde(o["yuzde"])]
            for t in TURLER:
                satir += [m["tur"][t]["pay"], m["tur"][t]["payda"], csv_yuzde(m["tur"][t]["yuzde"])]
            k = m["kredi"]
            satir += [m["gorunmuyor"], m["hakem_yok"], m["gecersiz"], m["olculemeyen_klip"],
                      m["hakemin_puanladigi_klip"], m["tumu_hakem_yok_klip"],
                      csv_sayi(k["klip_basina_teklif"]), csv_sayi(k["toplam"]),
                      csv_sayi(k["yapan_cevap_basina"]), csv_sayi(k["tutan_cevap_basina"]),
                      csv_sayi(k["puanlanan_toplam"]),
                      csv_sayi(k["puanlanan_yapan_cevap_basina"]),
                      csv_sayi(k["puanlanan_tutan_cevap_basina"])]
            w.writerow(satir)


def tablo(baslik, satirlar):
    cikti = ["| " + " | ".join(baslik) + " |", "|" + "---|" * len(baslik)]
    cikti += ["| " + " | ".join(str(h) for h in s) + " |" for s in satirlar]
    return "\n".join(cikti)


def uyum_bolumu(uyum):
    if uyum is None:
        return "İnsan puanlaması henüz yapılmadı. İnsan-hakem uyumu hesaplanmadı."
    try:
        ana = uyum["ana"]
        yan = uyum["yan_sayilar"]
        a = yan["tumu_hakem_yok_klipler_cikarilinca"]
        b = yan["hakem_yok_birimler_cikarilinca"]
        satirlar = [
            f"Ana sayı: %{yuzde_sayi(ana['uyum'] * 100)} ({ana['uyusan']}/{ana['birim']} birim uyuştu). "
            f"Eşik %{ESIK * 100:.0f}: {'geçti' if ana['esik_gecti'] else 'geçmedi'}. "
            f"İnsan {uyum['klip_sayisi']} klibi puanladı.",
            "",
            "Yan sayılar (eşikle karşılaştırılmaz):",
            f"- Tümü hakem_yok olan klipler çıkarılınca: %{yuzde_sayi(a['uyum'] * 100)} "
            f"({a['uyusan']}/{a['birim']}), çıkarılan klip {a['cikarilan_klip']}.",
            f"- hakem_yok birimler çıkarılınca: %{yuzde_sayi(b['uyum'] * 100)} "
            f"({b['uyusan']}/{b['birim']}), çıkarılan birim {b['cikarilan_birim']}.",
        ]
        if "net_uyum" in ana and "net_birim" in ana:
            if ana["net_uyum"] is None:
                satirlar.append(f"- Net uyum (evet/hayır birimleri): ölçülemedi ({ana['net_birim']} birim).")
            else:
                satirlar.append(
                    f"- Net uyum (evet/hayır birimleri): %{yuzde_sayi(ana['net_uyum'] * 100)} "
                    f"({ana['net_birim']} birim)."
                )
        else:
            satirlar.append("- Net uyum (evet/hayır birimleri): raporda yok.")

        if "gorunmuyor_hakem_yok_cift" in uyum:
            satirlar.append(f"- görünmüyor / hakem_yok çifti (gorunmuyor_hakem_yok_cift): {uyum['gorunmuyor_hakem_yok_cift']}.")
        else:
            satirlar.append("- görünmüyor / hakem_yok çifti (gorunmuyor_hakem_yok_cift): raporda yok.")

        if "tumu_hakem_yok_klipler" in uyum and isinstance(uyum["tumu_hakem_yok_klipler"], list):
            klipler_str = ", ".join(str(k) for k in uyum["tumu_hakem_yok_klipler"]) or "yok"
            satirlar.append(f"- Tümü hakem_yok klipler (tumu_hakem_yok_klipler): {klipler_str}.")
        else:
            satirlar.append("- Tümü hakem_yok klipler (tumu_hakem_yok_klipler): raporda yok.")

        karisiklik = ana.get("karisiklik")
        if isinstance(karisiklik, dict):
            insan_etiket = ("evet", "hayir", "gorunmuyor")
            hakem_etiket = ("evet", "hayir", "gorunmuyor", "hakem_yok")
            k_satirlar = []
            for ie in insan_etiket:
                if ie in karisiklik and isinstance(karisiklik[ie], dict):
                    k_satirlar.append([ie] + [karisiklik[ie].get(he, 0) for he in hakem_etiket])
            if k_satirlar:
                satirlar.append("")
                satirlar.append("Karışıklık tablosu (satır: insan, sütun: hakem):")
                satirlar.append(tablo(["İnsan \\ Hakem"] + list(hakem_etiket), k_satirlar))
            else:
                satirlar.append("- Karışıklık tablosu: raporda yok.")
        else:
            satirlar.append("- Karışıklık tablosu: raporda yok.")
    except (KeyError, TypeError) as hata:
        raise ValueError(f"uyum raporu bicimi gecersiz: {hata!r}")
    return "\n".join(satirlar)


def md_yaz(sonuc, uyum):
    ms = sonuc["modeller"]
    ad = lambda m: m["ad"]  # noqa: E731
    n = sonuc["komut_sayisi"]
    p = []
    p.append("# TUTAR sonuç tablosu\n")
    p.append("İki sütun ayrı okunur, toplanmaz: \"komutu yaptı\" ve \"karakteri tuttu\". "
             "Parantez içi pay/paydadır. Hesaplar `tutar/puan.py` fonksiyonlarındandır.\n")
    p.append("## Ana tablo\n")
    p.append(tablo(["Model", "Üretti", "Komutu yaptı", "Karakteri tuttu"],
                   [[ad(m), f"{m['uretti']}/{n}", yuzde(m["yapti"]), yuzde(m["tuttu"])] for m in ms]))
    p.append("\nÜretilemeyen klip: \"komutu yaptı\"da yapmadı sayılır, \"karakteri tuttu\"ya girmez "
             "(PROTOCOL.md, \"Üretilemeyen klip kuralı\"; bu kural videolardan sonra yazıldı).\n")
    p.append("## Ortak komutlar üzerinden \"karakteri tuttu\"\n")
    o = sonuc["ortak_komutlar"]
    p.append(f"Bütün modellerin ürettiği {o['sayi']} komut: "
             f"{', '.join(str(k) for k in o['komutlar']) or 'yok'}. "
             f"Bu komutlardan bütün modellerde hakem cevabı bulunanların sayısı: "
             f"{o['tum_modellerde_hakem_cevabi_olan_komut_sayisi']} "
             "(bir modelde tümü hakem_yok olan klibi bulunan komut sayılmaz).\n")
    p.append(tablo(["Model", "Ortak komutlarda karakteri tuttu", "Tüm kliplerde karakteri tuttu"],
                   [[ad(m), yuzde(m["ortak_tuttu"]), yuzde(m["tuttu"])] for m in ms]))
    p.append("\n## Soru türüne göre döküm\n")
    p.append("Döküm sorunun türüne göre yapılır, sütununa göre değil (PROTOCOL.md). "
             "Üretilemeyen klip dökümde sayılmaz.\n")
    p.append(tablo(["Model"] + [TUR_AD[t] for t in TURLER],
                   [[ad(m)] + [yuzde(m["tur"][t]) for t in TURLER] for m in ms]))
    p.append("\n## Puana girmeyen cevaplar ve klip sayıları\n")
    p.append(tablo(["Model", "görünmüyor", "hakem_yok", "eylem olmadığı için geçersiz",
                    "Ölçülemeyen klip", "Hakemin puanladığı klip", "Tümü hakem_yok klip"],
                   [[ad(m), m["gorunmuyor"], m["hakem_yok"], m["gecersiz"], m["olculemeyen_klip"],
                     m["hakemin_puanladigi_klip"], m["tumu_hakem_yok_klip"]] for m in ms]))
    p.append("\nSoru sayıları puanlı sorulardır. \"Ölçülemeyen klip\": puanlanabilir cevabı olmayan, "
             "üretilmiş klip. \"Tümü hakem_yok\": klibin bütün cevapları hakem_yok.\n")
    p.append("## Maliyet (Higgsfield kredisi)\n")
    p.append("Toplam kredi = klip başına teklif x (komut sayısı - iade edilen klip). "
             "Puanlanan kredi = klip başına teklif x hakemin puanladığı klip sayısı "
             "(tümü hakem_yok olan kliplerin kredisi çıkarılmış). "
             "Reddedilen klibin kredisi iade edildi. Kredi USD'ye çevrilmedi. "
             "İki \"başına\" sütunu ayrı sütunların payına bölünür; birleştirilmez.\n")
    p.append(tablo(["Model", "Klip başına kredi", "Toplam kredi", "Komutu yapan cevap başına",
                    "Tutulan karakter cevabı başına", "Puanlanan toplam kredi",
                    "Puanlanan kliplerde komutu yapan cevap başına",
                    "Puanlanan kliplerde tutulan karakter cevabı başına"],
                   [[ad(m), sayi(m["kredi"]["klip_basina_teklif"]), sayi(m["kredi"]["toplam"]),
                     sayi(m["kredi"]["yapan_cevap_basina"]), sayi(m["kredi"]["tutan_cevap_basina"]),
                     sayi(m["kredi"]["puanlanan_toplam"]),
                     sayi(m["kredi"]["puanlanan_yapan_cevap_basina"]),
                     sayi(m["kredi"]["puanlanan_tutan_cevap_basina"])]
                    for m in ms]))
    p.append("\n## İnsan-hakem uyumu\n")
    p.append(uyum_bolumu(uyum))
    p.append("\n## Grafikler\n")
    p.append("- `grafik_yapti_tuttu.svg`: model başına komutu yaptı ve karakteri tuttu %.")
    p.append("- `grafik_maliyet.svg`: model başına kredi, komutu yapan ve karakteri tutan cevap başına.")
    p.append("- `grafik_dogruluk_maliyet.svg`: tek resimde, solda komutu yaptı % ve karakteri tuttu % "
             "(ayrı çubuklar, toplanmadı), sağda ayrı eksenle tutulan karakter cevabı başına kredi.")
    return "\n".join(p) + "\n"


def _cubuk_ustu(cx, tepe, deger, pp):
    """Çubuğun üstündeki yazı: üstte değer, altında küçük puntoyla (pay/payda).

    İki satır olduğu için yan yana duran çubukların yazıları birbirine binmez.
    """
    if not pp:
        return (f'<text x="{cx:.1f}" y="{tepe - 4:.1f}" text-anchor="middle" '
                f'font-size="9" fill="#111111">{escape(deger)}</text>')
    return (f'<text x="{cx:.1f}" y="{tepe - 14:.1f}" text-anchor="middle" '
            f'font-size="9" fill="#111111">{escape(deger)}</text>'
            f'<text x="{cx:.1f}" y="{tepe - 4:.1f}" text-anchor="middle" '
            f'font-size="7.5" fill="#444444">({escape(pp)})</text>')


def _etiket_araligi(modeller, min_grup=160):
    en_uzun = max((len(str(m)) for m in modeller), default=1)
    return max(min_grup, int(en_uzun * 7.5) + 24)


def svg_cubuk(baslik, seriler, modeller, deger_ust, birim, format_):
    """Düz, gölgesiz gruplu çubuk grafik. seriler: [(ad, renk, [değer|None]) veya (ad, renk, [değer|None], [ek_etiket|None])]."""
    sol, ust, alt = 64, 56, 110
    grup_min = _etiket_araligi(modeller)
    gen = max(640, sol + 24 + len(modeller) * grup_min)
    yuk = 400
    alan_g, alan_y = gen - sol - 24, yuk - ust - alt
    grup_g = alan_g / len(modeller)
    cubuk_g = min(40, grup_g * 0.78 / len(seriler))
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{gen}" height="{yuk}" viewBox="0 0 {gen} {yuk}" '
         'font-family="sans-serif" font-size="12">',
         f'<rect width="{gen}" height="{yuk}" fill="#ffffff"/>',
         f'<text x="{sol}" y="24" font-size="14" fill="#111111">{escape(baslik)}</text>']
    for i in range(6):
        v = deger_ust * i / 5
        y = ust + alan_y - alan_y * i / 5
        o.append(f'<line x1="{sol}" y1="{y:.1f}" x2="{gen - 24}" y2="{y:.1f}" stroke="#dddddd"/>')
        o.append(f'<text x="{sol - 6}" y="{y + 4:.1f}" text-anchor="end" fill="#444444">{escape(format_(v))}</text>')
    o.append(f'<text x="{sol - 6}" y="{ust - 14}" text-anchor="end" fill="#444444">{escape(birim)}</text>')
    for gi, m in enumerate(modeller):
        gx = sol + grup_g * gi + (grup_g - cubuk_g * len(seriler)) / 2
        for si, seri in enumerate(seriler):
            renk, degerler = seri[1], seri[2]
            pay_paydalar = seri[3] if len(seri) > 3 else None
            d = degerler[gi]
            pp = pay_paydalar[gi] if pay_paydalar else None
            x = gx + cubuk_g * si
            cx = x + (cubuk_g - 2) / 2
            if d is None:
                etiket = f"ölçülemedi ({pp})" if pp else "ölçülemedi"
                my = ust + alan_y - 8
                o.append(f'<text x="{cx:.1f}" y="{my:.1f}" text-anchor="start" '
                         f'font-size="9" fill="#444444" transform="rotate(-90 {cx:.1f} {my:.1f})">'
                         f'{escape(etiket)}</text>')
                continue
            h = alan_y * min(d, deger_ust) / deger_ust
            o.append(f'<rect x="{x:.1f}" y="{ust + alan_y - h:.1f}" width="{cubuk_g - 2:.1f}" height="{h:.1f}" fill="{renk}"/>')
            o.append(_cubuk_ustu(cx, ust + alan_y - h, format_(d), pp))
        mx = sol + grup_g * (gi + 0.5)
        my = ust + alan_y + 18
        o.append(f'<text x="{mx:.1f}" y="{my:.1f}" text-anchor="end" font-size="11" '
                 f'fill="#111111" transform="rotate(-25 {mx:.1f} {my:.1f})">{escape(m)}</text>')
    for si, seri in enumerate(seriler):
        ad, renk = seri[0], seri[1]
        x = sol + si * 240
        o.append(f'<rect x="{x}" y="{yuk - 26}" width="12" height="12" fill="{renk}"/>')
        o.append(f'<text x="{x + 18}" y="{yuk - 16}" fill="#111111">{escape(ad)}</text>')
    o.append("</svg>")
    return "\n".join(o) + "\n"


def svg_tek_grafik(sonuc):
    """Tek resim, iki panel. Sol: komutu yaptı % ve karakteri tuttu % (ayrı çubuk, toplanmaz).
    Sağ: tutulan karakter cevabı başına kredi (ayrı eksen). Düz, gölgesiz."""
    ms = sonuc["modeller"]
    adlar = [m["ad"] for m in ms]
    grup_min = _etiket_araligi(adlar)
    panel_g = max(414, len(ms) * grup_min)
    sol1 = 64
    sag1 = sol1 + panel_g
    sol2 = sag1 + 80
    sag2 = sol2 + panel_g
    gen = sag2 + 24
    yuk, ust, alt = 420, 70, 110
    alan_y = yuk - ust - alt
    renk_y, renk_t, renk_k = "#3b6ea5", "#c2703d", "#5b8c5a"
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{gen}" height="{yuk}" viewBox="0 0 {gen} {yuk}" '
         'font-family="sans-serif" font-size="12">',
         f'<rect width="{gen}" height="{yuk}" fill="#ffffff"/>',
         f'<text x="{sol1}" y="24" font-size="14" fill="#111111">'
         'Komutu yaptı ve karakteri tuttu (iki ayrı ölçü) ve tutulan karakter cevabı başına kredi</text>']

    def eksen(sol, sag, ust_deger, birim, format_):
        for i in range(6):
            y = ust + alan_y - alan_y * i / 5
            o.append(f'<line x1="{sol}" y1="{y:.1f}" x2="{sag}" y2="{y:.1f}" stroke="#dddddd"/>')
            o.append(f'<text x="{sol - 6}" y="{y + 4:.1f}" text-anchor="end" fill="#444444">'
                     f'{escape(format_(ust_deger * i / 5))}</text>')
        o.append(f'<text x="{sol - 6}" y="{ust - 14}" text-anchor="end" fill="#444444">{escape(birim)}</text>')

    def cubuklar(sol, sag, ust_deger, seriler, format_):
        grup_g = (sag - sol) / len(ms)
        cubuk_g = min(40, grup_g * 0.78 / len(seriler))
        for gi, m in enumerate(ms):
            gx = sol + grup_g * gi + (grup_g - cubuk_g * len(seriler)) / 2
            for si, seri in enumerate(seriler):
                renk, degerler = seri[0], seri[1]
                pay_paydalar = seri[2] if len(seri) > 2 else None
                d, x = degerler[gi], gx + cubuk_g * si
                pp = pay_paydalar[gi] if pay_paydalar else None
                cx = x + (cubuk_g - 2) / 2
                if d is None:
                    etiket = f"ölçülemedi ({pp})" if pp else "ölçülemedi"
                    my = ust + alan_y - 8
                    o.append(f'<text x="{cx:.1f}" y="{my:.1f}" text-anchor="start" '
                             f'font-size="9" fill="#444444" transform="rotate(-90 {cx:.1f} {my:.1f})">'
                             f'{escape(etiket)}</text>')
                    continue
                h = alan_y * min(d, ust_deger) / ust_deger
                o.append(f'<rect x="{x:.1f}" y="{ust + alan_y - h:.1f}" width="{cubuk_g - 2:.1f}" '
                         f'height="{h:.1f}" fill="{renk}"/>')
                o.append(_cubuk_ustu(cx, ust + alan_y - h, format_(d), pp))
            mx = sol + grup_g * (gi + 0.5)
            my = ust + alan_y + 18
            o.append(f'<text x="{mx:.1f}" y="{my:.1f}" text-anchor="end" font-size="11" '
                     f'fill="#111111" transform="rotate(-25 {mx:.1f} {my:.1f})">{escape(m["ad"])}</text>')

    yapti_pp = [f"{m['yapti']['pay']}/{m['yapti']['payda']}" for m in ms]
    tuttu_pp = [f"{m['tuttu']['pay']}/{m['tuttu']['payda']}" for m in ms]

    # Sol panel: yüzde ekseni 0-100
    o.append(f'<text x="{sol1}" y="{ust - 30}" fill="#111111">Doğru cevap oranı (yüzde)</text>')
    eksen(sol1, sag1, 100, "%", yuzde_sayi)
    cubuklar(sol1, sag1, 100, [(renk_y, [m["yapti"]["yuzde"] for m in ms], yapti_pp),
                               (renk_t, [m["tuttu"]["yuzde"] for m in ms], tuttu_pp)], yuzde_sayi)
    # Sağ panel: kredi ekseni, ayrı ölçek
    kredi = [m["kredi"]["tutan_cevap_basina"] for m in ms]
    ust2 = ust_sinir(kredi)
    o.append(f'<text x="{sol2}" y="{ust - 30}" fill="#111111">Maliyet (ayrı eksen)</text>')
    eksen(sol2, sag2, ust2, "kredi", sayi)
    cubuklar(sol2, sag2, ust2, [(renk_k, kredi, tuttu_pp)], sayi)
    o.append(f'<line x1="{(sag1 + sol2) / 2:.1f}" y1="{ust - 30}" x2="{(sag1 + sol2) / 2:.1f}" '
             f'y2="{ust + alan_y + 24}" stroke="#bbbbbb"/>')
    for x, renk, ad in ((sol1, renk_y, "Komutu yaptı (%)"), (sol1 + 160, renk_t, "Karakteri tuttu (%)"),
                        (sol2, renk_k, "Tutulan karakter cevabı başına kredi")):
        o.append(f'<rect x="{x}" y="{yuk - 26}" width="12" height="12" fill="{renk}"/>')
        o.append(f'<text x="{x + 18}" y="{yuk - 16}" fill="#111111">{escape(ad)}</text>')
    o.append("</svg>")
    return "\n".join(o) + "\n"


def ust_sinir(degerler):
    """Eksen üst sınırı: 1, 2, 5 x 10^n basamaklarından değerleri sığdıran en küçüğü."""
    en_buyuk = max([d for d in degerler if d is not None] or [1])
    taban = 1.0
    while True:
        for c in (1, 2, 5):
            if taban * c >= en_buyuk:
                return taban * c
        taban *= 10


def svg_yazilar(sonuc):
    ms = sonuc["modeller"]
    adlar = [m["ad"] for m in ms]
    yapti_pp = [f"{m['yapti']['pay']}/{m['yapti']['payda']}" for m in ms]
    tuttu_pp = [f"{m['tuttu']['pay']}/{m['tuttu']['payda']}" for m in ms]
    yt = svg_cubuk("Komutu yaptı ve karakteri tuttu (%)",
                   [("Komutu yaptı", "#3b6ea5", [m["yapti"]["yuzde"] for m in ms], yapti_pp),
                    ("Karakteri tuttu", "#c2703d", [m["tuttu"]["yuzde"] for m in ms], tuttu_pp)],
                   adlar, 100, "%", yuzde_sayi)
    yapan = [m["kredi"]["yapan_cevap_basina"] for m in ms]
    tutan = [m["kredi"]["tutan_cevap_basina"] for m in ms]
    mal = svg_cubuk("Kredi, doğru cevap başına (Higgsfield kredisi)",
                    [("Komutu yapan cevap başına", "#3b6ea5", yapan, yapti_pp),
                     ("Tutulan karakter cevabı başına", "#c2703d", tutan, tuttu_pp)],
                    adlar, ust_sinir(yapan + tutan), "kredi", sayi)
    return yt, mal, svg_tek_grafik(sonuc)


def _kredi_kontrol_dosya(modeller):
    if not isinstance(modeller, list) or not modeller:
        raise GirdiButunluguHatasi("model listesi boş ya da geçersiz")
    for m in modeller:
        if not isinstance(m, dict) or "id" not in m:
            raise GirdiButunluguHatasi("model kaydı geçersiz")
        if "kredi_teklif" not in m or m["kredi_teklif"] is None:
            raise GirdiButunluguHatasi(f"{m['id']}: kredi alanı eksik ya da sayı değil")
        k = m["kredi_teklif"]
        if isinstance(k, bool) or not isinstance(k, (int, float)) or k < 0:
            raise GirdiButunluguHatasi(f"{m['id']}: kredi alanı sayı değil ya da negatif ({k!r})")


def main(argv=None):
    ap = argparse.ArgumentParser()
    for ad in ("checks", "hakem-ham", "uretim-kaydi", "modeller", "cikti-dizin"):
        ap.add_argument(f"--{ad}", required=True)
    ap.add_argument("--uyum-raporu")
    a = ap.parse_args(argv)
    try:
        oku = lambda y: json.loads(Path(y).read_text(encoding="utf-8"))  # noqa: E731
        satirlar = [json.loads(s) for s in
                    Path(a.hakem_ham).read_text(encoding="utf-8").splitlines() if s.strip()]
        uyum = oku(a.uyum_raporu) if a.uyum_raporu else None
        modeller_listesi = oku(a.modeller)["modeller"]
        _kredi_kontrol_dosya(modeller_listesi)
        sonuc = hesapla(oku(a.checks), satirlar, uretilemeyenleri_oku(a.uretim_kaydi),
                        modeller_listesi)
        md = md_yaz(sonuc, uyum)
        yt, mal, tek = svg_yazilar(sonuc)
    except GirdiButunluguHatasi as hata:
        print(f"Sonuc uretilemedi: {hata}", file=sys.stderr)
        return 1
    except (ValueError, OSError, KeyError, TypeError) as hata:
        print(f"Sonuc uretilemedi: {hata}", file=sys.stderr)
        return 2
    cikti = Path(a.cikti_dizin)
    cikti.mkdir(parents=True, exist_ok=True)
    tam = dict(sonuc, uyum=uyum)
    (cikti / "results.json").write_text(
        json.dumps(tam, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    csv_yaz(cikti / "sonuclar.csv", sonuc)
    (cikti / "RESULTS.md").write_text(md, encoding="utf-8")
    (cikti / "grafik_yapti_tuttu.svg").write_text(yt, encoding="utf-8")
    (cikti / "grafik_maliyet.svg").write_text(mal, encoding="utf-8")
    (cikti / "grafik_dogruluk_maliyet.svg").write_text(tek, encoding="utf-8")
    print(f"Yazildi: {cikti}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Sonuç tablosunu üretir: results.json, sonuclar.csv, RESULTS.md ve iki SVG grafik. Yalnız stdlib.

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


def uretilemeyenleri_oku(dizin):
    """uretim_kaydi/*.jsonl içinde durumu 'tamam' olmayan satırlar."""
    sonuc = []
    for yol in sorted(Path(dizin).glob("*.jsonl")):
        for sira, s in enumerate(yol.read_text(encoding="utf-8").splitlines(), 1):
            if not s.strip():
                continue
            r = json.loads(s)
            if r["durum"] != "tamam":
                sonuc.append({"model": r["model"], "komut": r["komut"], "durum": r["durum"]})
    return sorted(sonuc, key=lambda u: (u["model"], u["komut"]))


def yuzde(d):
    return "ölçülemedi" if d["yuzde"] is None else f"%{d['yuzde']:.1f} ({d['pay']}/{d['payda']})"


def sayi(x):
    if x is None:
        return "-"
    return f"{x:.2f}".rstrip("0").rstrip(".")


def csv_yuzde(y):
    return "" if y is None else f"{y:.1f}"


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
            "kredi_tutulan_karakter_cevabi_basina"]
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
                      csv_sayi(k["yapan_cevap_basina"]), csv_sayi(k["tutan_cevap_basina"])]
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
            f"Ana sayı: %{ana['uyum'] * 100:.1f} ({ana['uyusan']}/{ana['birim']} birim uyuştu). "
            f"Eşik %{ESIK * 100:.0f}: {'geçti' if ana['esik_gecti'] else 'geçmedi'}. "
            f"İnsan 20 klibi puanladı.",
            "",
            "Yan sayılar (eşikle karşılaştırılmaz):",
            f"- Tümü hakem_yok olan klipler çıkarılınca: %{a['uyum'] * 100:.1f} "
            f"({a['uyusan']}/{a['birim']}), çıkarılan klip {a['cikarilan_klip']}.",
            f"- hakem_yok birimler çıkarılınca: %{b['uyum'] * 100:.1f} "
            f"({b['uyusan']}/{b['birim']}), çıkarılan birim {b['cikarilan_birim']}.",
        ]
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
             "Reddedilen klibin kredisi iade edildi. Kredi USD'ye çevrilmedi. "
             "İki \"başına\" sütunu ayrı sütunların payına bölünür; birleştirilmez.\n")
    p.append(tablo(["Model", "Klip başına kredi", "Toplam kredi", "Komutu yapan cevap başına",
                    "Tutulan karakter cevabı başına"],
                   [[ad(m), sayi(m["kredi"]["klip_basina_teklif"]), sayi(m["kredi"]["toplam"]),
                     sayi(m["kredi"]["yapan_cevap_basina"]), sayi(m["kredi"]["tutan_cevap_basina"])]
                    for m in ms]))
    p.append("\n## İnsan-hakem uyumu\n")
    p.append(uyum_bolumu(uyum))
    p.append("\n## Grafikler\n")
    p.append("- `grafik_yapti_tuttu.svg`: model başına komutu yaptı ve karakteri tuttu %.")
    p.append("- `grafik_maliyet.svg`: model başına kredi, komutu yapan ve karakteri tutan cevap başına.")
    return "\n".join(p) + "\n"


def svg_cubuk(baslik, seriler, modeller, deger_ust, birim, format_):
    """Düz, gölgesiz gruplu çubuk grafik. seriler: [(ad, renk, [değer|None])]."""
    gen, yuk, sol, ust, alt = 640, 360, 56, 56, 70
    alan_g, alan_y = gen - sol - 20, yuk - ust - alt
    grup_g = alan_g / len(modeller)
    cubuk_g = min(34, grup_g * 0.8 / len(seriler))
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{gen}" height="{yuk}" viewBox="0 0 {gen} {yuk}" '
         'font-family="sans-serif" font-size="12">',
         f'<rect width="{gen}" height="{yuk}" fill="#ffffff"/>',
         f'<text x="{sol}" y="24" font-size="14" fill="#111111">{escape(baslik)}</text>']
    for i in range(6):
        v = deger_ust * i / 5
        y = ust + alan_y - alan_y * i / 5
        o.append(f'<line x1="{sol}" y1="{y:.1f}" x2="{gen - 20}" y2="{y:.1f}" stroke="#dddddd"/>')
        o.append(f'<text x="{sol - 6}" y="{y + 4:.1f}" text-anchor="end" fill="#444444">{escape(format_(v))}</text>')
    o.append(f'<text x="{sol - 6}" y="{ust - 14}" text-anchor="end" fill="#444444">{escape(birim)}</text>')
    for gi, m in enumerate(modeller):
        gx = sol + grup_g * gi + (grup_g - cubuk_g * len(seriler)) / 2
        for si, (_, renk, degerler) in enumerate(seriler):
            d = degerler[gi]
            x = gx + cubuk_g * si
            if d is None:
                o.append(f'<text x="{x + cubuk_g / 2:.1f}" y="{ust + alan_y - 6}" text-anchor="middle" '
                         f'font-size="10" fill="#444444" transform="rotate(-90 {x + cubuk_g / 2:.1f} {ust + alan_y - 6})">'
                         'ölçülemedi</text>')
                continue
            h = alan_y * min(d, deger_ust) / deger_ust
            o.append(f'<rect x="{x:.1f}" y="{ust + alan_y - h:.1f}" width="{cubuk_g - 2:.1f}" height="{h:.1f}" fill="{renk}"/>')
            o.append(f'<text x="{x + cubuk_g / 2 - 1:.1f}" y="{ust + alan_y - h - 4:.1f}" text-anchor="middle" '
                     f'font-size="10" fill="#111111">{escape(format_(d))}</text>')
        o.append(f'<text x="{sol + grup_g * (gi + 0.5):.1f}" y="{ust + alan_y + 18}" text-anchor="middle" '
                 f'fill="#111111">{escape(m)}</text>')
    for si, (ad, renk, _) in enumerate(seriler):
        x = sol + si * 230
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
    yt = svg_cubuk("Komutu yaptı ve karakteri tuttu (%)",
                   [("Komutu yaptı", "#3b6ea5", [m["yapti"]["yuzde"] for m in ms]),
                    ("Karakteri tuttu", "#c2703d", [m["tuttu"]["yuzde"] for m in ms])],
                   adlar, 100, "%", lambda v: f"{v:.0f}")
    yapan = [m["kredi"]["yapan_cevap_basina"] for m in ms]
    tutan = [m["kredi"]["tutan_cevap_basina"] for m in ms]
    mal = svg_cubuk("Kredi, doğru cevap başına (Higgsfield kredisi)",
                    [("Komutu yapan cevap başına", "#3b6ea5", yapan),
                     ("Tutulan karakter cevabı başına", "#c2703d", tutan)],
                    adlar, ust_sinir(yapan + tutan), "kredi", sayi)
    return yt, mal


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
        sonuc = hesapla(oku(a.checks), satirlar, uretilemeyenleri_oku(a.uretim_kaydi),
                        oku(a.modeller)["modeller"])
        md = md_yaz(sonuc, uyum)
        yt, mal = svg_yazilar(sonuc)
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
    print(f"Yazildi: {cikti}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

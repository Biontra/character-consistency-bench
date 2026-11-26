"""scripts/sonuc_uret.py testleri. Yalniz UYDURMA dosyalar, gecici klasorde."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.test_sonuc_tablosu import CHECKS, MODELLER, satirlar

BETIK = Path(__file__).resolve().parent.parent / "scripts" / "sonuc_uret.py"


def yaz_dunya(kok):
    kok = Path(kok)
    (kok / "uk").mkdir()
    (kok / "checks.json").write_text(json.dumps(CHECKS), encoding="utf-8")
    (kok / "models.json").write_text(json.dumps({"modeller": MODELLER}), encoding="utf-8")
    (kok / "ham.jsonl").write_text(
        "".join(json.dumps(s) + "\n" for s in satirlar()), encoding="utf-8")
    for m in ("A", "B", "C"):
        satir = [{"model": m, "komut": k, "durum": "reddedildi" if (m, k) == ("C", 2) else "tamam"}
                 for k in (1, 2, 3, 4)]
        (kok / "uk" / f"{m}.jsonl").write_text(
            "".join(json.dumps(s) + "\n" for s in satir), encoding="utf-8")


def calistir(kok, cikti, uyum=None):
    kok = Path(kok)
    arg = [sys.executable, str(BETIK), "--checks", str(kok / "checks.json"),
           "--hakem-ham", str(kok / "ham.jsonl"), "--uretim-kaydi", str(kok / "uk"),
           "--modeller", str(kok / "models.json"), "--cikti-dizin", str(cikti)]
    if uyum:
        arg += ["--uyum-raporu", str(uyum)]
    return subprocess.run(arg, capture_output=True, text=True)


class Betik(unittest.TestCase):
    def test_cikti_dosyalari_ve_belirlenimlilik(self):
        with tempfile.TemporaryDirectory() as t:
            yaz_dunya(t)
            r1 = calistir(t, Path(t) / "o1")
            r2 = calistir(t, Path(t) / "o2")
            self.assertEqual((r1.returncode, r2.returncode), (0, 0), r1.stderr)
            adlar = ["RESULTS.md", "grafik_dogruluk_maliyet.svg", "grafik_maliyet.svg",
                     "grafik_yapti_tuttu.svg",
                     "results.json", "sonuclar.csv"]
            self.assertEqual(sorted(p.name for p in (Path(t) / "o1").iterdir()), adlar)
            for ad in adlar:
                self.assertEqual((Path(t) / "o1" / ad).read_bytes(), (Path(t) / "o2" / ad).read_bytes(), ad)
            md = (Path(t) / "o1" / "RESULTS.md").read_text(encoding="utf-8")
            self.assertIn("İnsan puanlaması henüz yapılmadı", md)
            self.assertIn("| Model A | 4/4 | %66.7 (2/3) | %77.8 (7/9) |", md)
            self.assertIn("| Model C | 3/4 |", md)
            csv_ = (Path(t) / "o1" / "sonuclar.csv").read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(csv_), 4)
            self.assertTrue(csv_[1].startswith("A,4,4,2,3,66.7,7,9,77.8,6,7,85.7,"))

    def test_soru_metni_ciktiya_girmez(self):
        with tempfile.TemporaryDirectory() as t:
            yaz_dunya(t)
            calistir(t, Path(t) / "o")
            for p in (Path(t) / "o").iterdir():
                self.assertNotIn("uydurma", p.read_text(encoding="utf-8"), p.name)

    def test_uyum_raporu_eklenir(self):
        rapor = {"klip_sayisi": 20, "ana": {"uyum": 0.9, "uyusan": 18, "birim": 20, "esik_gecti": True},
                 "yan_sayilar": {
                     "tumu_hakem_yok_klipler_cikarilinca": {"uyum": 0.95, "uyusan": 19, "birim": 20, "cikarilan_klip": 1},
                     "hakem_yok_birimler_cikarilinca": {"uyum": 0.8, "uyusan": 8, "birim": 10, "cikarilan_birim": 3}}}
        with tempfile.TemporaryDirectory() as t:
            yaz_dunya(t)
            (Path(t) / "uyum.json").write_text(json.dumps(rapor), encoding="utf-8")
            r = calistir(t, Path(t) / "o", Path(t) / "uyum.json")
            self.assertEqual(r.returncode, 0, r.stderr)
            md = (Path(t) / "o" / "RESULTS.md").read_text(encoding="utf-8")
            self.assertIn("Ana sayı: %90.0 (18/20 birim uyuştu). Eşik %85: geçti.", md)
            self.assertIn("İnsan 20 klibi puanladı.", md)
            self.assertIn("%95.0 (19/20), çıkarılan klip 1", md)
            self.assertIn("%80.0 (8/10), çıkarılan birim 3", md)
            self.assertNotIn("henüz yapılmadı", md)

    def test_klip_sayisi_rapordan_okunur(self):
        rapor = {"klip_sayisi": 7, "ana": {"uyum": 0.9, "uyusan": 18, "birim": 20, "esik_gecti": True},
                 "yan_sayilar": {
                     "tumu_hakem_yok_klipler_cikarilinca": {"uyum": 0.95, "uyusan": 19, "birim": 20, "cikarilan_klip": 1},
                     "hakem_yok_birimler_cikarilinca": {"uyum": 0.8, "uyusan": 8, "birim": 10, "cikarilan_birim": 3}}}
        with tempfile.TemporaryDirectory() as t:
            yaz_dunya(t)
            (Path(t) / "uyum.json").write_text(json.dumps(rapor), encoding="utf-8")
            r = calistir(t, Path(t) / "o", Path(t) / "uyum.json")
            self.assertEqual(r.returncode, 0, r.stderr)
            md = (Path(t) / "o" / "RESULTS.md").read_text(encoding="utf-8")
            self.assertIn("İnsan 7 klibi puanladı.", md)
            self.assertNotIn("20 klibi", md)

    def test_klip_sayisi_yoksa_hata(self):
        rapor = {"ana": {"uyum": 0.9, "uyusan": 18, "birim": 20, "esik_gecti": True},
                 "yan_sayilar": {
                     "tumu_hakem_yok_klipler_cikarilinca": {"uyum": 0.95, "uyusan": 19, "birim": 20, "cikarilan_klip": 1},
                     "hakem_yok_birimler_cikarilinca": {"uyum": 0.8, "uyusan": 8, "birim": 10, "cikarilan_birim": 3}}}
        with tempfile.TemporaryDirectory() as t:
            yaz_dunya(t)
            (Path(t) / "uyum.json").write_text(json.dumps(rapor), encoding="utf-8")
            r = calistir(t, Path(t) / "o", Path(t) / "uyum.json")
            self.assertEqual(r.returncode, 2)

    def test_tek_grafik_gecerli_xml_ve_etiketler(self):
        import xml.etree.ElementTree as ET
        with tempfile.TemporaryDirectory() as t:
            yaz_dunya(t)
            r = calistir(t, Path(t) / "o")
            self.assertEqual(r.returncode, 0, r.stderr)
            yol = Path(t) / "o" / "grafik_dogruluk_maliyet.svg"
            ET.fromstring(yol.read_text(encoding="utf-8"))
            metin = yol.read_text(encoding="utf-8")
            for m in MODELLER:
                self.assertIn(m["ad"], metin)
            for etiket in ("Komutu yaptı (%)", "Karakteri tuttu (%)",
                           "Tutulan karakter cevabı başına kredi"):
                self.assertIn(etiket, metin)
            self.assertNotIn("Doğruluk (%)", metin)

    def test_bozuk_uyum_raporu_hata(self):
        with tempfile.TemporaryDirectory() as t:
            yaz_dunya(t)
            (Path(t) / "uyum.json").write_text("{}", encoding="utf-8")
            r = calistir(t, Path(t) / "o", Path(t) / "uyum.json")
            self.assertEqual(r.returncode, 2)
            self.assertFalse((Path(t) / "o").exists())

    def test_eksik_satir_hata_ve_dosya_yazilmaz(self):
        with tempfile.TemporaryDirectory() as t:
            yaz_dunya(t)
            ham = Path(t) / "ham.jsonl"
            ham.write_text("".join(ham.read_text(encoding="utf-8").splitlines(True)[1:]), encoding="utf-8")
            r = calistir(t, Path(t) / "o")
            self.assertEqual(r.returncode, 2)
            self.assertIn("eksik cevap", r.stderr)
            self.assertFalse((Path(t) / "o").exists())

    def test_yollar_zorunlu(self):
        r = subprocess.run([sys.executable, str(BETIK)], capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)

    def test_uyum_eksik_alanlar_ve_tam_alanlar(self):
        from scripts.sonuc_uret import uyum_bolumu
        tam_rapor = {
            "klip_sayisi": 20,
            "ana": {
                "uyum": 0.9,
                "uyusan": 18,
                "birim": 20,
                "esik_gecti": True,
                "net_uyum": 0.875,
                "net_birim": 16,
                "karisiklik": {
                    "evet": {"evet": 10, "hayir": 1, "gorunmuyor": 0, "hakem_yok": 0},
                    "hayir": {"evet": 1, "hayir": 4, "gorunmuyor": 0, "hakem_yok": 0},
                    "gorunmuyor": {"evet": 0, "hayir": 0, "gorunmuyor": 2, "hakem_yok": 2},
                },
            },
            "yan_sayilar": {
                "tumu_hakem_yok_klipler_cikarilinca": {"uyum": 0.95, "uyusan": 19, "birim": 20, "cikarilan_klip": 1},
                "hakem_yok_birimler_cikarilinca": {"uyum": 0.8, "uyusan": 8, "birim": 10, "cikarilan_birim": 3},
            },
            "gorunmuyor_hakem_yok_cift": 2,
            "tumu_hakem_yok_klipler": ["K03", "K12"],
        }
        metin_tam = uyum_bolumu(tam_rapor)
        self.assertIn("%87.5", metin_tam)
        self.assertIn("16 birim", metin_tam)
        self.assertIn("gorunmuyor_hakem_yok_cift): 2", metin_tam)
        self.assertIn("K03, K12", metin_tam)
        self.assertIn("Karışıklık tablosu", metin_tam)
        self.assertIn("| evet | 10 | 1 | 0 | 0 |", metin_tam)
        self.assertNotIn("raporda yok", metin_tam)

        eksik_rapor = {
            "klip_sayisi": 10,
            "ana": {"uyum": 0.8, "uyusan": 8, "birim": 10, "esik_gecti": False},
            "yan_sayilar": {
                "tumu_hakem_yok_klipler_cikarilinca": {"uyum": 0.85, "uyusan": 8, "birim": 10, "cikarilan_klip": 0},
                "hakem_yok_birimler_cikarilinca": {"uyum": 0.85, "uyusan": 8, "birim": 10, "cikarilan_birim": 0},
            },
        }
        metin_eksik = uyum_bolumu(eksik_rapor)
        self.assertIn("raporda yok", metin_eksik)

    def test_svg_bes_uzun_model_adi_ve_pay_payda(self):
        import xml.etree.ElementTree as ET
        from scripts.sonuc_uret import svg_yazilar
        uzun_adlar = [
            "gemini_omni_flash_1_2",
            "seedance_2_0_mini",
            "grok_video_v15_lite",
            "kling_video_master_v2",
            "runway_gen3_alpha_turbo",
        ]
        sahte_sonuc = {
            "komut_sayisi": 18,
            "modeller": [
                {
                    "model": f"m{i}",
                    "ad": ad,
                    "uretti": 18,
                    "toplam_klip": 18,
                    "yapti": {"pay": 12, "payda": 18, "yuzde": 1200 / 18},
                    "tuttu": {"pay": 15, "payda": 20, "yuzde": 75.0 if i > 0 else None},
                    "kredi": {
                        "klip_basina_teklif": 10,
                        "iade_edilen_klip": 0,
                        "toplam": 180,
                        "yapan_cevap_basina": 15.0,
                        "tutan_cevap_basina": 12.0 if i > 0 else None,
                        "puanlanan_toplam": 180,
                        "puanlanan_yapan_cevap_basina": 15.0,
                        "puanlanan_tutan_cevap_basina": 12.0 if i > 0 else None,
                    },
                }
                for i, ad in enumerate(uzun_adlar)
            ],
        }
        yt, mal, tek = svg_yazilar(sahte_sonuc)
        for svg_metin in (yt, mal, tek):
            kok = ET.fromstring(svg_metin)
            self.assertIn("12/18", svg_metin)
            self.assertIn("15/20", svg_metin)
            etiket_dugumleri = [el for el in kok.iter() if el.text in uzun_adlar]
            self.assertGreaterEqual(len(etiket_dugumleri), 5)
            # İlk 5 model etiketinin x konumları ve transform kontrolü
            ilk_bes = etiket_dugumleri[:5]
            x_konumlari = [float(el.attrib["x"]) for el in ilk_bes]
            for i in range(len(x_konumlari) - 1):
                fark = x_konumlari[i + 1] - x_konumlari[i]
                tahmini_gen = len(ilk_bes[i].text) * 7.0
                dondurulmus = "transform" in ilk_bes[i].attrib and "rotate" in ilk_bes[i].attrib["transform"]
                self.assertTrue(fark >= tahmini_gen or dondurulmus)

    def test_maliyet_puanlanan_ayri_gorunur(self):
        with tempfile.TemporaryDirectory() as t:
            yaz_dunya(t)
            r = calistir(t, Path(t) / "o")
            self.assertEqual(r.returncode, 0, r.stderr)
            res = json.loads((Path(t) / "o" / "results.json").read_text(encoding="utf-8"))
            b_kredi = next(m["kredi"] for m in res["modeller"] if m["model"] == "B")
            self.assertEqual(b_kredi["toplam"], 30)
            self.assertEqual(b_kredi["puanlanan_toplam"], 22.5)
            self.assertEqual(b_kredi["tutan_cevap_basina"], 10.0)
            self.assertEqual(b_kredi["puanlanan_tutan_cevap_basina"], 7.5)
            csv_baslik = (Path(t) / "o" / "sonuclar.csv").read_text(encoding="utf-8").splitlines()[0].split(",")
            self.assertIn("kredi_komutu_yapan_cevap_basina", csv_baslik)
            self.assertIn("kredi_puanlanan_komutu_yapan_cevap_basina", csv_baslik)
            self.assertIn("kredi_puanlanan_tutulan_karakter_cevabi_basina", csv_baslik)
            md = (Path(t) / "o" / "RESULTS.md").read_text(encoding="utf-8")
            self.assertIn("Puanlanan kliplerde komutu yapan cevap başına", md)
            self.assertIn("Puanlanan kliplerde tutulan karakter cevabı başına", md)

    def test_yuzde_bicimi_tabloda_ve_svgde_ondalikli(self):
        from scripts.sonuc_uret import yuzde, yuzde_sayi
        self.assertEqual(yuzde_sayi(75), "75.0")
        self.assertEqual(yuzde({"yuzde": 75.0, "pay": 3, "payda": 4}), "%75.0 (3/4)")
        with tempfile.TemporaryDirectory() as t:
            yaz_dunya(t)
            r = calistir(t, Path(t) / "o")
            self.assertEqual(r.returncode, 0, r.stderr)
            yt = (Path(t) / "o" / "grafik_yapti_tuttu.svg").read_text(encoding="utf-8")
            tek = (Path(t) / "o" / "grafik_dogruluk_maliyet.svg").read_text(encoding="utf-8")
            for svg in (yt, tek):
                self.assertIn(">66.7</text>", svg)
                self.assertIn(">(2/3)</text>", svg)
                self.assertIn(">77.8</text>", svg)
                self.assertIn(">(7/9)</text>", svg)
                self.assertIn(">75.0</text>", svg)
                self.assertIn(">(3/4)</text>", svg)
                self.assertIn(">100.0<", svg)

    def test_girdi_butunlugu_uretim_kaydi_ve_kredi_hatalari(self):
        # 1. Üretim kaydı dizini yok
        with tempfile.TemporaryDirectory() as t:
            yaz_dunya(t)
            for p in (Path(t) / "uk").iterdir():
                p.unlink()
            (Path(t) / "uk").rmdir()
            r = calistir(t, Path(t) / "o")
            self.assertEqual(r.returncode, 1)
            self.assertIn("üretim kaydı", r.stderr)

        # 2. Üretim kaydı boş
        with tempfile.TemporaryDirectory() as t:
            yaz_dunya(t)
            for p in (Path(t) / "uk").iterdir():
                p.write_text("", encoding="utf-8")
            r = calistir(t, Path(t) / "o")
            self.assertEqual(r.returncode, 1)
            self.assertIn("üretim kaydı boş", r.stderr)

        # 3. Üretim kaydında aynı (model, komut) çifti iki kez
        with tempfile.TemporaryDirectory() as t:
            yaz_dunya(t)
            p = Path(t) / "uk" / "A.jsonl"
            p.write_text(p.read_text(encoding="utf-8") + json.dumps({"model": "A", "komut": 1, "durum": "tamam"}) + "\n",
                         encoding="utf-8")
            r = calistir(t, Path(t) / "o")
            self.assertEqual(r.returncode, 1)
            self.assertIn("iki kez", r.stderr)

        # 4. Kredi alanı negatif veya sayı değil
        for kotu in (-5, "ucuz"):
            with self.subTest(kotu=kotu):
                with tempfile.TemporaryDirectory() as t:
                    yaz_dunya(t)
                    m = [dict(x) for x in MODELLER]
                    m[0]["kredi_teklif"] = kotu
                    (Path(t) / "models.json").write_text(json.dumps({"modeller": m}), encoding="utf-8")
                    r = calistir(t, Path(t) / "o")
                    self.assertEqual(r.returncode, 1)
                    self.assertIn("kredi", r.stderr)


if __name__ == "__main__":
    unittest.main()

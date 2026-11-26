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


if __name__ == "__main__":
    unittest.main()

import json
import unittest
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
MODEL_IDS = ["kling3_0", "wan3_0", "seedance_2_0_mini",
             "grok_video_v15_lite", "gemini_omni_flash_1_2"]


def yukle(ad):
    return json.loads((DATA / ad).read_text(encoding="utf-8"))


class KomutlarTest(unittest.TestCase):
    def setUp(self):
        self.komutlar = yukle("commands.json")

    def test_yirmi_komut(self):
        self.assertEqual(len(self.komutlar), 20)

    def test_idler_1den_20ye_tekrarsiz(self):
        self.assertEqual(sorted(k["id"] for k in self.komutlar), list(range(1, 21)))

    def test_alanlar_ve_bos_olmayan_metin(self):
        for k in self.komutlar:
            self.assertEqual(set(k), {"id", "tr", "en", "ceviri"})
            self.assertTrue(k["tr"].strip())
            self.assertTrue(k["en"].strip())
            self.assertEqual(k["ceviri"], "yapay zeka")

    def test_en_baslangici(self):
        for k in self.komutlar:
            if k["id"] == 16:
                continue
            self.assertTrue(k["en"].startswith("She "), k["id"])


class ModellerTest(unittest.TestCase):
    def setUp(self):
        self.veri = yukle("models.json")

    def test_besinci_model_ve_kimlikler(self):
        self.assertEqual(len(self.veri["modeller"]), 5)
        self.assertEqual([m["id"] for m in self.veri["modeller"]], MODEL_IDS)

    def test_ortak_ayar(self):
        self.assertEqual(self.veri["ortak_ayar"], {
            "sure_sn": 5, "cozunurluk": "720p", "oran": "9:16",
            "ses": False, "deneme": 1})

    def test_toplam_kredi(self):
        toplam = sum(m["kredi_teklif"] for m in self.veri["modeller"]) * 20
        self.assertEqual(toplam, 725)


if __name__ == "__main__":
    unittest.main()

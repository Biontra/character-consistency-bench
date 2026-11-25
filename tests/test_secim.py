import json
import unittest
from collections import Counter
from pathlib import Path

from tutar.secim import insan_klipleri_sec

DATA = Path(__file__).resolve().parent.parent / "data"
TOHUM = 20261125


def yukle(ad):
    return json.loads((DATA / ad).read_text(encoding="utf-8"))


class SecimTest(unittest.TestCase):
    def setUp(self):
        self.modeller = [m["id"] for m in yukle("models.json")["modeller"]]
        self.komutlar = [k["id"] for k in yukle("commands.json")]

    def sec(self, tohum=TOHUM):
        return insan_klipleri_sec(tohum, self.modeller, self.komutlar)

    def test_ayni_tohum_ayni_sonuc(self):
        self.assertEqual(self.sec(), self.sec())

    def test_yirmi_oge(self):
        self.assertEqual(len(self.sec()), 20)

    def test_her_model_dort(self):
        sayac = Counter(s["model"] for s in self.sec())
        self.assertEqual(set(sayac), set(self.modeller))
        self.assertTrue(all(v == 4 for v in sayac.values()))

    def test_her_komut_bir_kez(self):
        sayac = Counter(s["komut"] for s in self.sec())
        self.assertEqual(sorted(sayac), sorted(self.komutlar))
        self.assertTrue(all(v == 1 for v in sayac.values()))

    def test_farkli_tohum_farkli_sonuc(self):
        self.assertNotEqual(self.sec(TOHUM), self.sec(TOHUM + 1))

    def test_json_dosyasi_ayni(self):
        veri = yukle("insan_secimi.json")
        self.assertEqual(veri["tohum"], TOHUM)
        self.assertEqual(veri["secim"], self.sec())


if __name__ == "__main__":
    unittest.main()

import json
import unittest
from pathlib import Path

from tutar.parmakizi import parmakizi

KOK = Path(__file__).resolve().parent.parent
CHECKS = KOK / "secret" / "checks.json"
RESIM = KOK / "secret" / "aikyo-baslangic.webp"
IZLER = KOK / "data" / "fingerprints.json"
RESIM_IZI = "01aa3597b8f0d4e666412f00a4f199cc3e3cd0aea80d6f8175900a77806eadb1"
OZEL_SAYILARI = [2, 2, 0, 5, 2, 3, 2, 0, 4, 6, 5, 5, 3, 3, 4, 2, 2, 3, 6, 5]
SUTUNLAR = ("yapti", "tuttu", "puansiz")


def yukle():
    if not CHECKS.exists():
        raise unittest.SkipTest("secret/checks.json yok")
    return json.loads(CHECKS.read_text(encoding="utf-8"))


class GizliSorularTest(unittest.TestCase):
    def setUp(self):
        self.d = yukle()
        self.sorular = {s["id"]: s for s in self.d["sorular"]}
        self.komutlar = self.d["komutlar"]

    def test_benzersiz_sayilar(self):
        self.assertEqual(len(self.sorular), len(self.d["sorular"]), "tekrarlanan kimlik")
        puanli = [s for s in self.sorular.values() if s["sutun"] != "puansiz"]
        bilgi = [s for s in self.sorular.values() if s["sutun"] == "puansiz"]
        self.assertEqual(len(puanli), 101)
        self.assertEqual(len(bilgi), 2)

    def test_alanlar(self):
        for k, s in self.sorular.items():
            self.assertTrue(s["metin"].strip(), k)
            self.assertTrue(s["kaynak"].strip(), k)
            self.assertIn(s["sutun"], SUTUNLAR, k)
            self.assertIn(s["beklenen"], ("evet", "hayir", None), k)
            self.assertEqual(s["beklenen"] is None, s["sutun"] == "puansiz", k)
            self.assertIsInstance(s["eyleme_bagli"], bool, k)

    def test_komutlar(self):
        self.assertEqual(sorted(self.komutlar, key=int), [str(i) for i in range(1, 21)])
        for kom, idler in self.komutlar.items():
            for i in idler:
                self.assertIn(i, self.sorular, f"komut {kom}: {i}")

    def test_ozel_sayilari_ve_toplam(self):
        toplam = 0
        for n, beklenen in enumerate(OZEL_SAYILARI, start=1):
            idler = self.komutlar[str(n)]
            ozel = [i for i in idler if self.sorular[i]["tur"] == "ozel"]
            self.assertEqual(len(ozel), beklenen, f"komut {n}")
            toplam += sum(1 for i in idler if self.sorular[i]["sutun"] != "puansiz")
        self.assertEqual(toplam, 343)

    def test_her_komutta_yapti(self):
        for kom, idler in self.komutlar.items():
            self.assertTrue(
                any(self.sorular[i]["sutun"] == "yapti" for i in idler), f"komut {kom}")


class ParmakiziTest(unittest.TestCase):
    def test_kayitli_izler_diskle_ayni(self):
        izler = json.loads(IZLER.read_text(encoding="utf-8"))
        self.assertEqual(izler["aikyo-baslangic.webp"], RESIM_IZI)
        if not CHECKS.exists() or not RESIM.exists():
            raise unittest.SkipTest("secret/ dosyaları yok")
        self.assertEqual(izler["checks.json"], parmakizi(CHECKS))
        self.assertEqual(izler["aikyo-baslangic.webp"], parmakizi(RESIM))

    def test_resim_izi_sabit(self):
        if not RESIM.exists():
            raise unittest.SkipTest("secret/ dosyaları yok")
        self.assertEqual(parmakizi(RESIM), RESIM_IZI)

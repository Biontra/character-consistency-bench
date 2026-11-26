import json
import tempfile
import unittest
from pathlib import Path

from tutar import hakem_kayit as hk

SORULAR = {"1": ["a1", "a2"], "2": ["b1", "b2", "b3"]}
ESLEME = [{"klip": "K001", "model": "m1", "komut": 1},
          {"klip": "K002", "model": "m2", "komut": 2}]


def cikti(idler, gerekce="g"):
    return {"cevaplar": {i: {"cevap": "evet", "gerekce": gerekce, "kare": 2} for i in idler}}


class Ortam(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.t = Path(self._t.name)
        self.hakem = self.t / "hakem"
        self.hakem.mkdir()
        (self.hakem / "esleme.json").write_text(json.dumps(ESLEME), encoding="utf-8")
        self.checks = self.t / "checks.json"
        self.checks.write_text(json.dumps({"komutlar": SORULAR}), encoding="utf-8")
        self.sonuc = self.t / "results" / "judge_raw.jsonl"

    def tearDown(self):
        self._t.cleanup()

    def dosya(self, ad, veri):
        yol = self.t / ad
        yol.write_text(veri if isinstance(veri, str) else json.dumps(veri), encoding="utf-8")
        return yol

    def kaydet(self, kod, yol, tarih="2026-11-27"):
        return hk.kaydet(kod, yol, "hm", tarih, self.hakem, self.checks)

    def gunluk(self):
        y = self.hakem / "gunluk.jsonl"
        if not y.exists():
            return []
        return [json.loads(s) for s in y.read_text(encoding="utf-8").splitlines()]


class KaydetTest(Ortam):
    def test_gecerli_kayit(self):
        d = self.dosya("c.json", cikti(["a1", "a2"]))
        r = self.kaydet("K001", d)
        self.assertEqual((r["durum"], r["calistirma"]), ("gecerli", 1))
        g = self.gunluk()
        self.assertEqual(len(g), 1)
        self.assertEqual((g[0]["klip"], g[0]["calistirma"], g[0]["gecerli"], g[0]["hata_sayisi"]),
                         ("K001", 1, True, 0))
        self.assertEqual(len(g[0]["cikti_sha256"]), 64)
        satir = [json.loads(s) for s in (self.hakem / "ham" / "K001.jsonl").read_text().splitlines()]
        self.assertEqual([x["soru"] for x in satir], ["a1", "a2"])
        self.assertEqual(satir[0]["model"], "m1")
        self.assertTrue((self.hakem / "cikti" / "K001.calistirma1.json").exists())

    def test_gecerliden_sonra_reddi(self):
        d = self.dosya("c.json", cikti(["a1", "a2"]))
        self.kaydet("K001", d)
        once = (self.hakem / "gunluk.jsonl").read_text()
        with self.assertRaises(hk.KayitReddi):
            self.kaydet("K001", d)
        self.assertEqual((self.hakem / "gunluk.jsonl").read_text(), once)
        self.assertFalse((self.hakem / "cikti" / "K001.calistirma2.json").exists())

    def test_gecersiz_sonra_gecerli(self):
        kotu = self.dosya("k.json", cikti(["a1"]))
        r1 = self.kaydet("K001", kotu)
        self.assertEqual((r1["durum"], r1["calistirma"]), ("gecersiz", 1))
        self.assertFalse((self.hakem / "ham" / "K001.jsonl").exists())
        iyi = self.dosya("i.json", cikti(["a1", "a2"]))
        r2 = self.kaydet("K001", iyi)
        self.assertEqual((r2["durum"], r2["calistirma"]), ("gecerli", 2))
        satir = [json.loads(s) for s in (self.hakem / "ham" / "K001.jsonl").read_text().splitlines()]
        self.assertTrue(all(x["calistirma"] == 2 for x in satir))
        self.assertEqual([g["gecerli"] for g in self.gunluk()], [False, True])

    def test_iki_gecersiz_hakem_yok(self):
        kotu = self.dosya("k.json", cikti(["a1", "a2"], gerekce=""))
        self.kaydet("K001", kotu)
        r = self.kaydet("K001", kotu)
        self.assertEqual(r["durum"], "hakem_yok")
        satir = [json.loads(s) for s in (self.hakem / "ham" / "K001.jsonl").read_text().splitlines()]
        self.assertEqual([x["cevap"] for x in satir], ["hakem_yok"] * 2)
        self.assertTrue(all(x["kare"] is None and x["calistirma"] == 2 for x in satir))

    def test_ucuncu_deneme_reddi(self):
        kotu = self.dosya("k.json", cikti(["a1"]))
        self.kaydet("K001", kotu)
        self.kaydet("K001", kotu)
        once = (self.hakem / "gunluk.jsonl").read_text()
        iyi = self.dosya("i.json", cikti(["a1", "a2"]))
        with self.assertRaises(hk.KayitReddi):
            self.kaydet("K001", iyi)
        self.assertEqual((self.hakem / "gunluk.jsonl").read_text(), once)

    def test_cikti_dosyasi_yok_gecersiz(self):
        r = self.kaydet("K001", self.t / "yok.json")
        self.assertEqual(r["durum"], "gecersiz")
        g = self.gunluk()[0]
        self.assertFalse(g["gecerli"])
        self.assertIsNone(g["cikti_sha256"])
        self.assertGreaterEqual(g["hata_sayisi"], 1)

    def test_bozuk_json_gecersiz(self):
        r = self.kaydet("K001", self.dosya("b.json", "{bozuk"))
        self.assertEqual(r["durum"], "gecersiz")

    def test_bilinmeyen_klip(self):
        with self.assertRaises(hk.KayitReddi):
            self.kaydet("K099", self.dosya("c.json", cikti(["a1", "a2"])))
        self.assertEqual(self.gunluk(), [])

    def test_klipler_birbirini_etkilemez(self):
        self.kaydet("K001", self.dosya("c.json", cikti(["a1", "a2"])))
        r = self.kaydet("K002", self.dosya("d.json", cikti(["b1", "b2", "b3"])))
        self.assertEqual(r["durum"], "gecerli")


class DurumToplaTest(Ortam):
    def test_durum(self):
        self.assertEqual(hk.durum(self.hakem, self.checks)["hic_calismadi"], ["K001", "K002"])
        self.kaydet("K001", self.dosya("k.json", cikti(["a1"])))
        d = hk.durum(self.hakem, self.checks)
        self.assertEqual(d["bir_gecersiz_bekliyor"], ["K001"])
        self.kaydet("K001", self.dosya("i.json", cikti(["a1", "a2"])))
        self.kaydet("K002", self.dosya("k2.json", cikti(["b1"])))
        self.kaydet("K002", self.dosya("k2.json", cikti(["b1"])))
        d = hk.durum(self.hakem, self.checks)
        self.assertEqual((d["gecerli"], d["hakem_yok"], d["hic_calismadi"]), (["K001"], ["K002"], []))

    def test_topla_eksikken_reddi(self):
        self.kaydet("K001", self.dosya("c.json", cikti(["a1", "a2"])))
        with self.assertRaises(hk.KayitReddi):
            hk.topla(self.hakem, self.checks, self.sonuc)
        self.assertFalse(self.sonuc.exists())

    def test_topla_satir_sayisi(self):
        self.kaydet("K002", self.dosya("d.json", cikti(["b1", "b2", "b3"])))
        self.kaydet("K001", self.dosya("c.json", cikti(["a1", "a2"])))
        n = hk.topla(self.hakem, self.checks, self.sonuc)
        self.assertEqual(n, 5)
        satir = [json.loads(s) for s in self.sonuc.read_text().splitlines()]
        self.assertEqual([x["klip"] for x in satir], ["K001"] * 2 + ["K002"] * 3)

    def test_topla_beklenen_uyusmazligi(self):
        self.kaydet("K002", self.dosya("d.json", cikti(["b1", "b2", "b3"])))
        self.kaydet("K001", self.dosya("c.json", cikti(["a1", "a2"])))
        with self.assertRaises(hk.KayitReddi):
            hk.topla(self.hakem, self.checks, self.sonuc, beklenen_satir=6)
        self.assertFalse(self.sonuc.exists())

    def test_topla_bozuk_ham_reddi(self):
        self.kaydet("K001", self.dosya("c.json", cikti(["a1", "a2"])))
        self.kaydet("K002", self.dosya("d.json", cikti(["b1", "b2", "b3"])))
        y = self.hakem / "ham" / "K002.jsonl"
        y.write_text(y.read_text().splitlines()[0] + "\n", encoding="utf-8")
        with self.assertRaises(hk.KayitReddi):
            hk.topla(self.hakem, self.checks, self.sonuc)


if __name__ == "__main__":
    unittest.main()

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

    def kaydet(self, kod, yol, tarih="2026-11-27", **kw):
        return hk.kaydet(kod, yol, "hm", tarih, self.hakem, self.checks, **kw)

    def gunluk(self, surum="v1"):
        y = self.hakem / surum / "gunluk.jsonl"
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
        satir = [json.loads(s) for s in (self.hakem / "v1" / "ham" / "K001.jsonl").read_text().splitlines()]
        self.assertEqual([x["soru"] for x in satir], ["a1", "a2"])
        self.assertEqual(satir[0]["model"], "m1")
        self.assertTrue((self.hakem / "v1" / "cikti" / "K001.calistirma1.json").exists())

    def test_gecerliden_sonra_reddi(self):
        d = self.dosya("c.json", cikti(["a1", "a2"]))
        self.kaydet("K001", d)
        once = (self.hakem / "v1" / "gunluk.jsonl").read_text()
        with self.assertRaises(hk.KayitReddi):
            self.kaydet("K001", d)
        self.assertEqual((self.hakem / "v1" / "gunluk.jsonl").read_text(), once)
        self.assertFalse((self.hakem / "v1" / "cikti" / "K001.calistirma2.json").exists())

    def test_gecersiz_sonra_gecerli(self):
        kotu = self.dosya("k.json", cikti(["a1"]))
        r1 = self.kaydet("K001", kotu)
        self.assertEqual((r1["durum"], r1["calistirma"]), ("gecersiz", 1))
        self.assertFalse((self.hakem / "v1" / "ham" / "K001.jsonl").exists())
        iyi = self.dosya("i.json", cikti(["a1", "a2"]))
        r2 = self.kaydet("K001", iyi)
        self.assertEqual((r2["durum"], r2["calistirma"]), ("gecerli", 2))
        satir = [json.loads(s) for s in (self.hakem / "v1" / "ham" / "K001.jsonl").read_text().splitlines()]
        self.assertTrue(all(x["calistirma"] == 2 for x in satir))
        self.assertEqual([g["gecerli"] for g in self.gunluk()], [False, True])

    def test_iki_gecersiz_hakem_yok(self):
        kotu = self.dosya("k.json", cikti(["a1", "a2"], gerekce=""))
        self.kaydet("K001", kotu)
        r = self.kaydet("K001", kotu)
        self.assertEqual(r["durum"], "hakem_yok")
        satir = [json.loads(s) for s in (self.hakem / "v1" / "ham" / "K001.jsonl").read_text().splitlines()]
        self.assertEqual([x["cevap"] for x in satir], ["hakem_yok"] * 2)
        self.assertTrue(all(x["kare"] is None and x["calistirma"] == 2 for x in satir))

    def test_ucuncu_deneme_reddi(self):
        kotu = self.dosya("k.json", cikti(["a1"]))
        self.kaydet("K001", kotu)
        self.kaydet("K001", kotu)
        once = (self.hakem / "v1" / "gunluk.jsonl").read_text()
        iyi = self.dosya("i.json", cikti(["a1", "a2"]))
        with self.assertRaises(hk.KayitReddi):
            self.kaydet("K001", iyi)
        self.assertEqual((self.hakem / "v1" / "gunluk.jsonl").read_text(), once)

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
        y = self.hakem / "v1" / "ham" / "K002.jsonl"
        y.write_text(y.read_text().splitlines()[0] + "\n", encoding="utf-8")
        with self.assertRaises(hk.KayitReddi):
            hk.topla(self.hakem, self.checks, self.sonuc)


class TaramaTest(Ortam):
    def test_tarama_hatali_gecerli_cikti_gecersiz_sayilir(self):
        iyi = self.dosya("i.json", cikti(["a1", "a2"]))
        r = self.kaydet("K001", iyi, tarama_hatasi="klasor disi dosya okundu")
        self.assertEqual((r["durum"], r["calistirma"]), ("gecersiz", 1))
        self.assertFalse((self.hakem / "v1" / "ham" / "K001.jsonl").exists())
        g = self.gunluk()[0]
        self.assertFalse(g["gecerli"])
        self.assertEqual(g["tarama"], "gecersiz")
        self.assertEqual(g["tarama_hatasi"], "klasor disi dosya okundu")

    def test_tarama_hatali_sonra_temiz_calistirma_2(self):
        iyi = self.dosya("i.json", cikti(["a1", "a2"]))
        self.kaydet("K001", iyi, tarama_hatasi="50 kare acilmadi")
        r = self.kaydet("K001", iyi)
        self.assertEqual((r["durum"], r["calistirma"]), ("gecerli", 2))
        self.assertTrue((self.hakem / "v1" / "ham" / "K001.jsonl").exists())
        g = self.gunluk()
        self.assertEqual([x["tarama"] for x in g], ["gecersiz", "temiz"])
        self.assertIsNone(g[1].get("tarama_hatasi"))

    def test_iki_tarama_hatasi_hakem_yok(self):
        iyi = self.dosya("i.json", cikti(["a1", "a2"]))
        self.kaydet("K001", iyi, tarama_hatasi="bir")
        r = self.kaydet("K001", iyi, tarama_hatasi="iki")
        self.assertEqual((r["durum"], r["calistirma"]), ("hakem_yok", 2))
        satir = [json.loads(s) for s in (self.hakem / "v1" / "ham" / "K001.jsonl").read_text().splitlines()]
        self.assertEqual([x["cevap"] for x in satir], ["hakem_yok"] * 2)

    def test_tarama_hatali_ucuncu_deneme_reddi(self):
        iyi = self.dosya("i.json", cikti(["a1", "a2"]))
        self.kaydet("K001", iyi, tarama_hatasi="bir")
        self.kaydet("K001", iyi, tarama_hatasi="iki")
        with self.assertRaises(hk.KayitReddi):
            self.kaydet("K001", iyi)

    def test_temiz_kayitta_tarama_alani(self):
        self.kaydet("K001", self.dosya("i.json", cikti(["a1", "a2"])))
        self.assertEqual(self.gunluk()[0]["tarama"], "temiz")

    def test_kare_anahtari_hic_yoksa_gecerli_sayilir(self):
        # Mevcut davranisi sabitler: 'kare' anahtari olmayan cevap, bos kare gibi gecerli.
        veri = {"cevaplar": {i: {"cevap": "evet", "gerekce": "g"} for i in ["a1", "a2"]}}
        self.assertEqual(hk.cikti_dogrula(veri, ["a1", "a2"]), [])
        r = self.kaydet("K001", self.dosya("k.json", veri))
        self.assertEqual(r["durum"], "gecerli")
        satir = [json.loads(s) for s in (self.hakem / "v1" / "ham" / "K001.jsonl").read_text().splitlines()]
        self.assertTrue(all(x["kare"] is None for x in satir))


class SurumTest(Ortam):
    def test_surum_alani_gunluk_ve_ham_satirlarda(self):
        self.kaydet("K001", self.dosya("i.json", cikti(["a1", "a2"])))
        self.assertEqual(self.gunluk()[0]["surum"], "v1")
        satir = [json.loads(s) for s in (self.hakem / "v1" / "ham" / "K001.jsonl").read_text().splitlines()]
        self.assertTrue(all(x["surum"] == "v1" for x in satir))

    def test_v2_yeniden_kayit_v1_bayt_bayt_ayni(self):
        iyi = self.dosya("i.json", cikti(["a1", "a2"]))
        self.kaydet("K001", iyi)
        v1 = {p.relative_to(self.hakem): p.read_bytes()
              for p in (self.hakem / "v1").rglob("*") if p.is_file()}
        r = hk.kaydet("K001", iyi, "hm", "2026-11-28", self.hakem, self.checks, surum="v2")
        self.assertEqual((r["durum"], r["calistirma"]), ("gecerli", 1))
        v1_sonra = {p.relative_to(self.hakem): p.read_bytes()
                    for p in (self.hakem / "v1").rglob("*") if p.is_file()}
        self.assertEqual(v1, v1_sonra)
        self.assertEqual(self.gunluk("v2")[0]["surum"], "v2")
        self.assertTrue((self.hakem / "v2" / "ham" / "K001.jsonl").exists())

    def test_sayac_surum_basina(self):
        kotu = self.dosya("k.json", cikti(["a1"]))
        self.kaydet("K001", kotu)
        self.kaydet("K001", kotu)
        r = hk.kaydet("K001", kotu, "hm", "2026-11-28", self.hakem, self.checks, surum="v2")
        self.assertEqual((r["durum"], r["calistirma"]), ("gecersiz", 1))

    def test_durum_surum_basina(self):
        self.kaydet("K001", self.dosya("i.json", cikti(["a1", "a2"])))
        self.assertEqual(hk.durum(self.hakem, self.checks)["gecerli"], ["K001"])
        self.assertEqual(hk.durum(self.hakem, self.checks, surum="v2")["gecerli"], [])

    def test_topla_yalniz_verilen_surum(self):
        c1 = self.dosya("c.json", cikti(["a1", "a2"]))
        c2 = self.dosya("d.json", cikti(["b1", "b2", "b3"]))
        self.kaydet("K001", c1)
        self.kaydet("K002", c2)
        hk.kaydet("K001", c1, "hm", "2026-11-28", self.hakem, self.checks, surum="v2")
        with self.assertRaises(hk.KayitReddi):  # v2'de K002 yok
            hk.topla(self.hakem, self.checks, self.sonuc, surum="v2")
        hk.kaydet("K002", c2, "hm", "2026-11-28", self.hakem, self.checks, surum="v2")
        self.assertEqual(hk.topla(self.hakem, self.checks, self.sonuc, surum="v2"), 5)
        satir = [json.loads(s) for s in self.sonuc.read_text().splitlines()]
        self.assertTrue(all(x["surum"] == "v2" for x in satir))

    def test_gecersiz_surum_adi_reddi(self):
        with self.assertRaises(hk.KayitReddi):
            self.kaydet("K001", self.dosya("i.json", cikti(["a1", "a2"])), surum="../x")


class BetikTest(Ortam):
    def calistir(self, *args):
        import subprocess, sys
        depo = Path(__file__).resolve().parent.parent
        return subprocess.run(
            [sys.executable, str(depo / "scripts" / "hakem_kaydet.py"),
             "--hakem-dizin", str(self.hakem), "--checks", str(self.checks),
             "--sonuc", str(self.sonuc), *args],
            capture_output=True, text=True)

    def kaydet_args(self, kod, dosya, *ek):
        return ["kaydet", kod, "--cikti", str(dosya), "--hakem-modeli", "hm",
                "--tarih", "2026-11-27", *ek]

    def test_tarama_secenegi_yoksa_red(self):
        d = self.dosya("i.json", cikti(["a1", "a2"]))
        r = self.calistir(*self.kaydet_args("K001", d))
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse((self.hakem / "v1").exists())

    def test_iki_tarama_secenegi_birlikte_red(self):
        d = self.dosya("i.json", cikti(["a1", "a2"]))
        r = self.calistir(*self.kaydet_args("K001", d, "--tarama-temiz", "--tarama-gecersiz", "x"))
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse((self.hakem / "v1").exists())

    def test_bos_neden_red(self):
        d = self.dosya("i.json", cikti(["a1", "a2"]))
        r = self.calistir(*self.kaydet_args("K001", d, "--tarama-gecersiz", "  "))
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse((self.hakem / "v1").exists())

    def test_gecersiz_sonra_temiz(self):
        d = self.dosya("i.json", cikti(["a1", "a2"]))
        r1 = self.calistir(*self.kaydet_args("K001", d, "--tarama-gecersiz", "dis dosya"))
        self.assertEqual(r1.returncode, 1)
        r2 = self.calistir(*self.kaydet_args("K001", d, "--tarama-temiz"))
        self.assertEqual(r2.returncode, 0)
        self.assertIn("calistirma 2", r2.stdout)


if __name__ == "__main__":
    unittest.main()

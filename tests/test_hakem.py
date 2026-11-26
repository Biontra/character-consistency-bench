import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tutar import hakem
from tutar.hakem import (cikti_dogrula, ham_satirlar, hakem_metni, hakem_yok_satirlari,
                         klip_kodlari, kare_kopyala)

SABLON = 'Komut: {komut_en}\nSorular:\n{sorular}\nCikti: {\n "cevaplar": {"<id>": {"cevap": "x"}}\n}\n'
MODELLER = ["a", "b", "c"]
CIFTLER = [(m, k) for m in MODELLER for k in range(1, 5)]


def gecerli(idler, cevap="evet", kare=3):
    return {"cevaplar": {i: {"cevap": cevap, "gerekce": "g", "kare": kare} for i in idler}}


class KodTest(unittest.TestCase):
    def test_tekil_ve_kapsam(self):
        kod = klip_kodlari(CIFTLER)
        self.assertEqual(set(kod), set(CIFTLER))
        self.assertEqual(sorted(kod.values()), [f"K{i:03d}" for i in range(1, 13)])

    def test_ayni_girdi_ayni_cikti_sira_etkisiz(self):
        a = klip_kodlari(CIFTLER)
        b = klip_kodlari(list(reversed(CIFTLER)))
        self.assertEqual(a, b)

    def test_tohum_degisince_degisir(self):
        self.assertNotEqual(klip_kodlari(CIFTLER), klip_kodlari(CIFTLER, tohum=1))

    def test_karisik(self):
        kod = klip_kodlari(CIFTLER)
        sirali = sorted(CIFTLER)
        self.assertNotEqual([kod[c] for c in sirali], [f"K{i:03d}" for i in range(1, 13)])

    def test_tekrar_eden_cift_hata(self):
        with self.assertRaises(ValueError):
            klip_kodlari(CIFTLER + [CIFTLER[0]])


class MetinTest(unittest.TestCase):
    def test_doldurur_ve_json_parantezleri_kalir(self):
        m = hakem_metni(SABLON, "She waves.", [("q1", "Soru bir?"), ("q2", "Soru iki?")])
        self.assertIn("Komut: She waves.", m)
        self.assertIn("q1: Soru bir?\nq2: Soru iki?", m)
        self.assertIn('"cevaplar": {"<id>": {"cevap": "x"}}', m)
        self.assertNotIn("{komut_en}", m)
        self.assertNotIn("{sorular}", m)

    def test_beklenen_sizmaz(self):
        sorular = [{"id": "q1", "metin": "Soru bir?", "beklenen": "hayir", "tur": "ozel",
                    "sutun": "tuttu", "kaynak": "kaynakX", "eyleme_bagli": True}]
        m = hakem_metni(SABLON, "She waves.", sorular)
        for yasak in ("beklenen", "hayir", "ozel", "tuttu", "kaynakX", "eyleme", "sutun", "tur"):
            self.assertNotIn(yasak, m)
        self.assertIn("q1: Soru bir?", m)

    def test_soru_metnindeki_yer_tutucu_islenmez(self):
        m = hakem_metni(SABLON, "K", [("q1", "{komut_en} nedir?")])
        self.assertIn("q1: {komut_en} nedir?", m)

    def test_bos_soru_hata(self):
        with self.assertRaises(ValueError):
            hakem_metni(SABLON, "K", [])


class DogrulaTest(unittest.TestCase):
    IDLER = ["a1", "a2"]

    def test_gecerli(self):
        self.assertEqual(cikti_dogrula(gecerli(self.IDLER), self.IDLER), [])

    def test_json_metni_kabul(self):
        self.assertEqual(cikti_dogrula(json.dumps(gecerli(self.IDLER)), self.IDLER), [])

    def test_bozuk_json(self):
        self.assertTrue(cikti_dogrula("{bozuk", self.IDLER))

    def test_eksik_ve_fazla_kimlik(self):
        c = gecerli(["a1", "zz"])
        h = cikti_dogrula(c, self.IDLER)
        self.assertTrue(any("a2" in e for e in h))
        self.assertTrue(any("zz" in e for e in h))

    def test_cevap_degerleri(self):
        for d in ("evet", "hayir", "gorunmuyor", "hakem_yok"):
            self.assertEqual(cikti_dogrula(gecerli(self.IDLER, cevap=d), self.IDLER), [], d)
        for d in ("Evet", "yes", "", None, "hayır", 1):
            self.assertTrue(cikti_dogrula(gecerli(self.IDLER, cevap=d), self.IDLER), repr(d))

    def test_kare(self):
        for k in (1, 50, None, "", "7"):
            self.assertEqual(cikti_dogrula(gecerli(self.IDLER, kare=k), self.IDLER), [], repr(k))
        for k in (0, 51, -1, 2.5, "abc", True, "0"):
            self.assertTrue(cikti_dogrula(gecerli(self.IDLER, kare=k), self.IDLER), repr(k))

    def test_yapi_hatalari(self):
        self.assertTrue(cikti_dogrula([], self.IDLER))
        self.assertTrue(cikti_dogrula({}, self.IDLER))
        self.assertTrue(cikti_dogrula({"cevaplar": []}, self.IDLER))
        self.assertTrue(cikti_dogrula({"cevaplar": {"a1": "evet", "a2": "evet"}}, self.IDLER))


class HamSatirTest(unittest.TestCase):
    def test_satirlar_gerekce_icermez(self):
        c = gecerli(["a1", "a2"])
        c["cevaplar"]["a1"]["gerekce"] = "GIZLI-GEREKCE"
        s = ham_satirlar("K001", "m", 3, c, ["a1", "a2"], "claude-sonnet", 1, "2026-11-26")
        self.assertEqual([r["soru"] for r in s], ["a1", "a2"])
        self.assertEqual(set(s[0]), {"klip", "model", "komut", "soru", "cevap", "kare",
                                     "hakem_modeli", "calistirma", "tarih"})
        self.assertNotIn("GIZLI-GEREKCE", json.dumps(s))
        self.assertEqual(s[0]["klip"], "K001")
        self.assertEqual(s[0]["kare"], 3)

    def test_bos_kare_none(self):
        c = gecerli(["a1"], kare="")
        self.assertIsNone(ham_satirlar("K001", "m", 3, c, ["a1"], "x", 1, "t")[0]["kare"])

    def test_gecersiz_cikti_hata(self):
        with self.assertRaises(ValueError):
            ham_satirlar("K001", "m", 3, {"cevaplar": {}}, ["a1"], "x", 1, "t")

    def test_kare_metin_ise_int(self):
        c = gecerli(["a1"], kare="7")
        self.assertEqual(ham_satirlar("K001", "m", 3, c, ["a1"], "x", 1, "t")[0]["kare"], 7)


class HamSatirDogrulamaTest(unittest.TestCase):
    def test_uydurma_kimlik_hata(self):
        c = gecerli(["x1", "x2"])
        with self.assertRaises(ValueError):
            ham_satirlar("K001", "m", 3, c, ["a1", "a2"], "x", 1, "t")

    def test_eksik_kimlik_hata(self):
        c = gecerli(["a1"])
        with self.assertRaises(ValueError):
            ham_satirlar("K001", "m", 3, c, ["a1", "a2"], "x", 1, "t")

    def test_fazla_kimlik_hata(self):
        c = gecerli(["a1", "a2", "a3"])
        with self.assertRaises(ValueError):
            ham_satirlar("K001", "m", 3, c, ["a1", "a2"], "x", 1, "t")

    def test_bos_gerekce_hata(self):
        c = gecerli(["a1"])
        c["cevaplar"]["a1"]["gerekce"] = " "
        with self.assertRaises(ValueError):
            ham_satirlar("K001", "m", 3, c, ["a1"], "x", 1, "t")

    def test_json_metni_ve_sira(self):
        s = ham_satirlar("K001", "m", 3, json.dumps(gecerli(["a2", "a1"])), ["a1", "a2"], "x", 2, "t")
        self.assertEqual([r["soru"] for r in s], ["a1", "a2"])
        self.assertEqual(s[0]["calistirma"], 2)


class GerekceTest(unittest.TestCase):
    IDLER = ["a1", "a2"]

    def test_gerekce_zorunlu(self):
        for g in (None, "", "   ", 5, ["x"], {}):
            c = gecerli(self.IDLER)
            c["cevaplar"]["a1"]["gerekce"] = g
            h = cikti_dogrula(c, self.IDLER)
            self.assertTrue(any("a1" in e and "gerekce" in e for e in h), repr(g))

    def test_gerekce_alani_yok(self):
        c = gecerli(self.IDLER)
        del c["cevaplar"]["a2"]["gerekce"]
        self.assertTrue(any("a2" in e and "gerekce" in e for e in cikti_dogrula(c, self.IDLER)))

    def test_kare_kurali_ayni(self):
        for k in (1, 50, None, "", "7"):
            self.assertEqual(cikti_dogrula(gecerli(self.IDLER, kare=k), self.IDLER), [])
        for k in ("yok", "-", "1-5", 0, 51, 2.5, True):
            self.assertTrue(cikti_dogrula(gecerli(self.IDLER, kare=k), self.IDLER), repr(k))


class HakemYokTest(unittest.TestCase):
    def test_satirlar(self):
        s = hakem_yok_satirlari("K007", "m", 4, ["a1", "a2"], "claude-sonnet", 2, "2026-11-26")
        self.assertEqual([r["soru"] for r in s], ["a1", "a2"])
        self.assertTrue(all(r["cevap"] == "hakem_yok" and r["kare"] is None for r in s))
        self.assertEqual(set(s[0]), {"klip", "model", "komut", "soru", "cevap", "kare",
                                     "hakem_modeli", "calistirma", "tarih"})
        self.assertEqual((s[0]["klip"], s[0]["model"], s[0]["komut"], s[0]["calistirma"]),
                         ("K007", "m", 4, 2))

    def test_bos_liste_hata(self):
        with self.assertRaises(ValueError):
            hakem_yok_satirlari("K007", "m", 4, [], "x", 2, "t")


class KopyaTest(unittest.TestCase):
    def test_kopya_ve_yan_dosya(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            kaynak, hedef = t / "k", t / "h"
            for ad in ("tam", "ust", "alt"):
                (kaynak / ad).mkdir(parents=True)
                for n in (1, 2, 3):
                    (kaynak / ad / f"{n:03d}.png").write_bytes(f"{ad}{n}".encode())
                    (kaynak / ad / f"._{n:03d}.png").write_bytes(b"yan")
            kare_kopyala(kaynak, hedef)
            for ad in ("tam", "ust", "alt"):
                adlar = sorted(p.name for p in (hedef / ad).iterdir())
                self.assertEqual(adlar, ["001.png", "002.png", "003.png"])
                self.assertEqual((hedef / ad / "002.png").read_bytes(), f"{ad}2".encode())

    def test_eksik_kare_hata(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            (t / "k" / "tam").mkdir(parents=True)
            with self.assertRaises(FileNotFoundError):
                kare_kopyala(t / "k", t / "h")


class TalimatTest(unittest.TestCase):
    KOK = Path(__file__).resolve().parent.parent

    def test_parmak_izi_diskle_ayni(self):
        from tutar.parmakizi import parmakizi
        yol = self.KOK / "judge" / "hakem_talimati_v1.txt"
        izler = json.loads((self.KOK / "data" / "fingerprints.json").read_text(encoding="utf-8"))
        self.assertEqual(izler["hakem_talimati_v1.txt"], parmakizi(yol))

    def test_yer_tutucular(self):
        metin = (self.KOK / "judge" / "hakem_talimati_v1.txt").read_text(encoding="utf-8")
        for y in ("{metin_dosyasi}", "{kare_klasoru}", "{cikti_dosyasi}"):
            self.assertIn(y, metin)


if __name__ == "__main__":
    unittest.main()

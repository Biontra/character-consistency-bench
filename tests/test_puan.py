import unittest

from tutar.puan import CEVAPLAR, klip_puanla, model_puanla, uyum


def soru(id, tur, sutun, beklenen="evet", eyleme_bagli=False):
    return {"id": id, "tur": tur, "sutun": sutun, "beklenen": beklenen,
            "eyleme_bagli": eyleme_bagli}


SORULAR = [
    soru("y1", "yapti", "yapti"),
    soru("o1", "ortak", "tuttu"),
    soru("o2", "ortak", "tuttu"),
    soru("g1", "grup", "tuttu", eyleme_bagli=True),
    soru("s1", "ozel", "tuttu", beklenen="hayir", eyleme_bagli=True),
]


def hepsi(deger):
    return {s["id"]: deger for s in SORULAR}


def beklenenler():
    return {s["id"]: s["beklenen"] for s in SORULAR}


class KlipPuanlaTest(unittest.TestCase):
    def test_hepsi_beklenen(self):
        r = klip_puanla(SORULAR, beklenenler())
        self.assertEqual(r["yapti"], (1, 1))
        self.assertEqual(r["tuttu"], (4, 4))
        self.assertEqual(r["tur"]["ortak"], (2, 2))
        self.assertEqual(r["tur"]["grup"], (1, 1))
        self.assertEqual(r["tur"]["ozel"], (1, 1))
        self.assertEqual(r["disarida"], {"gorunmuyor": 0, "hakem_yok": 0, "gecersiz": 0})

    def test_yapti_hayir_eyleme_bagli_paydadan_cikar(self):
        c = beklenenler()
        c["y1"] = "hayir"
        r = klip_puanla(SORULAR, c)
        self.assertEqual(r["yapti"], (0, 1))
        self.assertEqual(r["tuttu"], (2, 2))
        self.assertEqual(r["tur"]["ortak"], (2, 2))
        self.assertEqual(r["tur"]["grup"], (0, 0))
        self.assertEqual(r["tur"]["ozel"], (0, 0))
        self.assertEqual(r["disarida"]["gecersiz"], 2)

    def test_hepsi_gorunmuyor_olculemedi(self):
        r = klip_puanla(SORULAR, hepsi("gorunmuyor"))
        self.assertEqual(r["yapti"], (0, 0))
        self.assertEqual(r["tuttu"], (0, 0))
        self.assertEqual(r["disarida"]["gorunmuyor"], 5)
        m = model_puanla([r])
        self.assertIsNone(m["yapti_yuzde"])
        self.assertIsNone(m["tuttu_yuzde"])
        self.assertEqual(m["olculemeyen_klip"], 1)

    def test_hepsi_hakem_yok_olculemedi(self):
        r = klip_puanla(SORULAR, hepsi("hakem_yok"))
        self.assertEqual(r["disarida"]["hakem_yok"], 5)
        self.assertEqual(model_puanla([r])["olculemeyen_klip"], 1)

    def test_bilinmeyen_cevap_hata(self):
        for kotu in ("Evet", "yes", "", None):
            c = beklenenler()
            c["o1"] = kotu
            with self.assertRaises(ValueError):
                klip_puanla(SORULAR, c)

    def test_eksik_cevap_hata(self):
        c = beklenenler()
        del c["o2"]
        with self.assertRaises(ValueError):
            klip_puanla(SORULAR, c)

    def test_puansiz_sonucu_degistirmez(self):
        temel = klip_puanla(SORULAR, beklenenler())
        sorular = SORULAR + [soru("b1", "bilgi", "puansiz")]
        for cevap in ("evet", "hayir", "gorunmuyor", "hakem_yok"):
            c = beklenenler()
            c["b1"] = cevap
            self.assertEqual(klip_puanla(sorular, c), temel)

    def test_iki_sutun_birlesmez(self):
        r = klip_puanla(SORULAR, beklenenler())
        m = model_puanla([r])
        for anahtarlar in (set(r), set(m)):
            self.assertEqual(anahtarlar & {"toplam", "genel", "birlesik", "total"}, set())
        self.assertEqual(set(m), {"yapti_yuzde", "tuttu_yuzde", "tur_yuzde",
                                  "olculemeyen_klip", "disarida"})


class ModelPuanlaTest(unittest.TestCase):
    def test_havuzlanmis_yuzde(self):
        a = klip_puanla(SORULAR, beklenenler())
        c = beklenenler()
        c["o1"] = "hayir"
        b = klip_puanla(SORULAR, c)
        m = model_puanla([a, b])
        self.assertEqual(m["yapti_yuzde"], 100.0)
        self.assertEqual(m["tuttu_yuzde"], 700 / 8)
        self.assertEqual(m["tur_yuzde"]["ortak"], 75.0)
        self.assertEqual(m["olculemeyen_klip"], 0)

    def test_olculemeyen_klip_havuzu_bozmaz(self):
        a = klip_puanla(SORULAR, beklenenler())
        b = klip_puanla(SORULAR, hepsi("gorunmuyor"))
        m = model_puanla([a, b])
        self.assertEqual(m["tuttu_yuzde"], 100.0)
        self.assertEqual(m["olculemeyen_klip"], 1)
        self.assertEqual(m["disarida"]["gorunmuyor"], 5)

    def test_bos_liste(self):
        m = model_puanla([])
        self.assertIsNone(m["yapti_yuzde"])
        self.assertEqual(m["olculemeyen_klip"], 0)


class UyumTest(unittest.TestCase):
    def test_17_of_20(self):
        insan = {f"q{i}": "evet" for i in range(20)}
        hakem = dict(insan)
        for i in range(3):
            hakem[f"q{i}"] = "hayir"
        self.assertEqual(uyum(insan, hakem), 0.85)

    def test_dort_deger_cevap_sayilir(self):
        self.assertEqual(uyum({"a": "gorunmuyor"}, {"a": "gorunmuyor"}), 1.0)
        self.assertEqual(uyum({"a": "gorunmuyor"}, {"a": "hakem_yok"}), 0.0)

    def test_farkli_anahtar_hata(self):
        with self.assertRaises(ValueError):
            uyum({"a": "evet"}, {"b": "evet"})

    def test_bilinmeyen_deger_hata(self):
        with self.assertRaises(ValueError):
            uyum({"a": "Evet"}, {"a": "evet"})

    def test_bos_hata(self):
        with self.assertRaises(ValueError):
            uyum({}, {})

    def test_cevaplar_sabiti(self):
        self.assertEqual(CEVAPLAR, ("evet", "hayir", "gorunmuyor", "hakem_yok"))


if __name__ == "__main__":
    unittest.main()

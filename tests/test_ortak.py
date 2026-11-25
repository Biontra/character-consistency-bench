import unittest

from tutar.puan import (klip_puanla, model_puanla, ortak_komutlar, ortak_tuttu,
                        uretilemeyen_klip)

# Uydurma, küçük soru listesi.
SORULAR = [
    {"id": "y1", "tur": "yapti", "sutun": "yapti", "beklenen": "evet", "eyleme_bagli": False},
    {"id": "o1", "tur": "ortak", "sutun": "tuttu", "beklenen": "evet", "eyleme_bagli": False},
    {"id": "o2", "tur": "ortak", "sutun": "tuttu", "beklenen": "evet", "eyleme_bagli": False},
    {"id": "g1", "tur": "grup", "sutun": "tuttu", "beklenen": "evet", "eyleme_bagli": True},
]


def iyi():
    return klip_puanla(SORULAR, {s["id"]: s["beklenen"] for s in SORULAR})


def kotu():
    c = {s["id"]: s["beklenen"] for s in SORULAR}
    c["o1"] = "hayir"
    c["o2"] = "hayir"
    return klip_puanla(SORULAR, c)


TUM = list(range(1, 21))


class OrtakKomutlarTest(unittest.TestCase):
    def test_bir_model_iki_komut_uretmediyse_ortak_18(self):
        uretilen = {m: set(TUM) for m in ("a", "b", "c", "d")}
        uretilen["e"] = set(TUM) - {2, 7}
        ortak = ortak_komutlar(uretilen)
        self.assertEqual(len(ortak), 18)
        self.assertNotIn(2, ortak)
        self.assertNotIn(7, ortak)
        self.assertEqual(ortak, sorted(ortak))

    def test_hepsi_20_uretildiyse_ortak_20_ve_yuzde_ayni(self):
        self.assertEqual(ortak_komutlar({"a": TUM, "b": set(TUM)}), TUM)
        klipler = [(k, iyi() if k % 2 else kotu()) for k in TUM]
        hepsi = model_puanla([k for _, k in klipler])["tuttu_yuzde"]
        self.assertEqual(ortak_tuttu(klipler, TUM)["tuttu_yuzde"], hepsi)

    def test_ortak_disi_kotu_klip_b_yi_etkilemez_a_yi_etkiler(self):
        klipler = [(1, iyi()), (2, iyi()), (3, kotu())]
        ortak = [1, 2]
        b = ortak_tuttu(klipler, ortak)
        self.assertEqual(b["tuttu_yuzde"], 100.0)
        self.assertEqual((b["pay"], b["payda"]), (6, 6))
        a = model_puanla([k for _, k in klipler])["tuttu_yuzde"]
        self.assertLess(a, 100.0)

    def test_bos_girdi_ve_ortak_yok(self):
        self.assertEqual(ortak_komutlar({}), [])
        self.assertEqual(ortak_komutlar({"a": {1, 2}, "b": {3}}), [])
        self.assertEqual(ortak_komutlar({"a": set()}), [])
        r = ortak_tuttu([(1, iyi())], [])
        self.assertIsNone(r["tuttu_yuzde"])
        self.assertEqual((r["pay"], r["payda"]), (0, 0))

    def test_eyleme_bagli_kural_b_de_ayni_calisir(self):
        c = {s["id"]: s["beklenen"] for s in SORULAR}
        c["y1"] = "hayir"  # komut yapılmadı: g1 geçersiz sayılır
        klip = klip_puanla(SORULAR, c)
        r = ortak_tuttu([(1, klip)], [1])
        beklenen = model_puanla([klip])
        self.assertEqual(r["tuttu_yuzde"], beklenen["tuttu_yuzde"])
        self.assertEqual((r["pay"], r["payda"]), (2, 2))  # g1 paydada yok

    def test_uretilemeyen_klip_paydaya_girmez(self):
        klipler = [(1, iyi()), (2, uretilemeyen_klip(SORULAR))]
        r = ortak_tuttu(klipler, [1, 2])
        self.assertEqual((r["pay"], r["payda"]), (3, 3))
        self.assertEqual(r["tuttu_yuzde"], 100.0)


class OrtakGirdiDenetimiTest(unittest.TestCase):
    def test_ayni_komut_iki_kez_hata(self):
        with self.assertRaises(ValueError):
            ortak_tuttu([(1, iyi()), (1, kotu())], [1])

    def test_ortak_komut_klipler_arasinda_yoksa_hata(self):
        with self.assertRaises(ValueError):
            ortak_tuttu([(1, iyi())], [1, 2])

    def test_tekrar_ortak_disi_komutta_da_hata(self):
        with self.assertRaises(ValueError):
            ortak_tuttu([(1, iyi()), (3, iyi()), (3, iyi())], [1])


if __name__ == "__main__":
    unittest.main()

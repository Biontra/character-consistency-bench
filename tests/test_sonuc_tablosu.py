"""Sonuc tablosu testleri. Yalniz UYDURMA veri (3 model, 4 komut); elle hesaplanmis degerler."""
import copy
import random
import unittest

from tutar import sonuc_tablosu as st


def q(i, tur, sutun, beklenen, bagli=False):
    return {"id": i, "tur": tur, "sutun": sutun, "beklenen": beklenen,
            "eyleme_bagli": bagli, "metin": "uydurma", "kaynak": "x"}


CHECKS = {
    "sorular": [
        q("o1", "ortak", "tuttu", "hayir"),
        q("o2", "ortak", "tuttu", "evet", True),
        q("y1", "yapti", "yapti", "evet"),
        q("g1", "grup", "tuttu", "evet", True),
        q("y2", "ozel", "yapti", "evet"),
        q("b1", "bilgi", "puansiz", "evet"),
        q("y4", "yapti", "yapti", "evet"),
        q("s4", "ozel", "tuttu", "hayir"),
    ],
    "komutlar": {"1": ["o1", "o2", "y1", "g1"], "2": ["o1", "o2", "y2"],
                 "3": ["o1", "o2", "b1"], "4": ["o1", "o2", "y4", "s4"]},
}
MODELLER = [{"id": "A", "ad": "Model A", "kredi_teklif": 5},
            {"id": "B", "ad": "Model B", "kredi_teklif": 7.5},
            {"id": "C", "ad": "Model C", "kredi_teklif": 10}]
URETILEMEYEN = [{"model": "C", "komut": 2, "durum": "reddedildi"}]

CEVAP = {
    ("A", 1): dict(o1="hayir", o2="evet", y1="evet", g1="evet"),
    ("A", 2): dict(o1="hayir", o2="hayir", y2="evet"),
    ("A", 3): dict(o1="evet", o2="evet", b1="evet"),
    ("A", 4): dict(o1="hayir", o2="evet", y4="hayir", s4="hayir"),
    ("B", 1): dict(o1="evet", o2="gorunmuyor", y1="hayir", g1="evet"),
    ("B", 2): dict(o1="hayir", o2="evet", y2="evet"),
    ("B", 3): dict(o1="hakem_yok", o2="hakem_yok", b1="hakem_yok"),
    ("B", 4): dict(o1="hayir", o2="hakem_yok", y4="evet", s4="gorunmuyor"),
    ("C", 1): dict(o1="hayir", o2="evet", y1="evet", g1="hayir"),
    ("C", 3): dict(o1="hayir", o2="evet", b1="hayir"),
    ("C", 4): dict(o1="evet", o2="hayir", y4="evet", s4="evet"),
}


def satirlar(cevap=CEVAP):
    return [{"klip": "K", "model": m, "komut": k, "soru": s, "cevap": c}
            for (m, k), d in cevap.items() for s, c in d.items()]


def hesap(**kw):
    a = dict(checks=CHECKS, hakem_satirlari=satirlar(), uretilemeyen=URETILEMEYEN, modeller=MODELLER)
    a.update(kw)
    return st.hesapla(**a)


def model(sonuc, ad):
    return next(m for m in sonuc["modeller"] if m["model"] == ad)


class ElleHesap(unittest.TestCase):
    def setUp(self):
        self.s = hesap()

    def test_model_sirasi_girdi_sirasi(self):
        self.assertEqual([m["model"] for m in self.s["modeller"]], ["A", "B", "C"])

    def test_a(self):
        a = model(self.s, "A")
        self.assertEqual((a["uretti"], a["toplam_klip"]), (4, 4))
        self.assertEqual((a["yapti"]["pay"], a["yapti"]["payda"]), (2, 3))
        self.assertAlmostEqual(a["yapti"]["yuzde"], 200 / 3)
        self.assertEqual((a["tuttu"]["pay"], a["tuttu"]["payda"]), (7, 9))
        self.assertAlmostEqual(a["tuttu"]["yuzde"], 700 / 9)
        self.assertEqual([(a["tur"][t]["pay"], a["tur"][t]["payda"]) for t in ("ortak", "grup", "ozel")],
                         [(5, 7), (1, 1), (2, 2)])
        self.assertEqual((a["gorunmuyor"], a["hakem_yok"], a["gecersiz"]), (0, 0, 1))
        self.assertEqual((a["olculemeyen_klip"], a["hakemin_puanladigi_klip"], a["tumu_hakem_yok_klip"]), (0, 4, 0))
        self.assertEqual((a["ortak_tuttu"]["pay"], a["ortak_tuttu"]["payda"]), (6, 7))
        self.assertAlmostEqual(a["ortak_tuttu"]["yuzde"], 600 / 7)

    def test_b_gorunmuyor_hakem_yok_tumu_hakem_yok(self):
        b = model(self.s, "B")
        self.assertEqual((b["yapti"]["pay"], b["yapti"]["payda"]), (2, 3))
        self.assertEqual((b["tuttu"]["pay"], b["tuttu"]["payda"]), (3, 4))
        self.assertAlmostEqual(b["tuttu"]["yuzde"], 75.0)
        self.assertEqual((b["tur"]["ortak"]["pay"], b["tur"]["ortak"]["payda"]), (3, 4))
        self.assertEqual((b["tur"]["grup"]["payda"], b["tur"]["grup"]["yuzde"]), (0, None))
        self.assertEqual((b["tur"]["ozel"]["pay"], b["tur"]["ozel"]["payda"]), (1, 1))
        # puansiz soru (b1) sayilmaz: komut 3'te hakem_yok 2 (o1, o2); komut 4'te 1
        self.assertEqual((b["gorunmuyor"], b["hakem_yok"], b["gecersiz"]), (2, 3, 1))
        self.assertEqual(b["olculemeyen_klip"], 1)
        self.assertEqual((b["tumu_hakem_yok_klip"], b["hakemin_puanladigi_klip"], b["uretti"]), (1, 3, 4))
        # tumu hakem_yok klip uretildi sayilir, ortak komutlara girer, paydaya bir sey katmaz
        self.assertEqual((b["ortak_tuttu"]["pay"], b["ortak_tuttu"]["payda"]), (1, 2))
        self.assertAlmostEqual(b["ortak_tuttu"]["yuzde"], 50.0)

    def test_c_uretilemeyen(self):
        c = model(self.s, "C")
        self.assertEqual((c["uretti"], c["toplam_klip"]), (3, 4))
        # komut 2 yapmadi sayilir (paya 0, paydaya 1); tuttu ve tur'e girmez
        self.assertEqual((c["yapti"]["pay"], c["yapti"]["payda"]), (2, 3))
        self.assertEqual((c["tuttu"]["pay"], c["tuttu"]["payda"]), (4, 8))
        self.assertEqual([(c["tur"][t]["pay"], c["tur"][t]["payda"]) for t in ("ortak", "grup", "ozel")],
                         [(4, 6), (0, 1), (0, 1)])
        self.assertEqual(c["olculemeyen_klip"], 0)
        self.assertEqual(c["hakemin_puanladigi_klip"], 3)
        self.assertEqual((c["ortak_tuttu"]["pay"], c["ortak_tuttu"]["payda"]), (4, 8))

    def test_ortak_komutlar(self):
        o = self.s["ortak_komutlar"]
        self.assertEqual(o["komutlar"], [1, 3, 4])
        self.assertEqual(o["sayi"], 3)
        # komut 3'te B'nin cevabi tumu hakem_yok: hakem cevabi olan ortak komut 1 ve 4
        self.assertEqual(o["tum_modellerde_hakem_cevabi_olan_komut_sayisi"], 2)

    def test_kredi(self):
        a, b, c = (model(self.s, x)["kredi"] for x in "ABC")
        self.assertEqual((a["toplam"], b["toplam"], c["toplam"]), (20, 30, 30))  # C: reddedilen iade
        self.assertEqual(c["iade_edilen_klip"], 1)
        self.assertEqual(a["klip_basina_teklif"], 5)
        self.assertAlmostEqual(a["yapan_cevap_basina"], 10)
        self.assertAlmostEqual(a["tutan_cevap_basina"], 20 / 7)
        self.assertAlmostEqual(b["tutan_cevap_basina"], 10)
        self.assertAlmostEqual(c["tutan_cevap_basina"], 7.5)

    def test_pay_sifirsa_kredi_basina_none(self):
        cevap = copy.deepcopy(CEVAP)
        cevap[("A", 1)].update(y1="hayir")  # y1 yanlis, g1 gecersiz
        cevap[("A", 2)].update(y2="hayir")
        cevap[("A", 4)].update(y4="hayir")
        a = model(hesap(hakem_satirlari=satirlar(cevap)), "A")
        self.assertEqual(a["yapti"]["pay"], 0)
        self.assertIsNone(a["kredi"]["yapan_cevap_basina"])


class Belirlenimlilik(unittest.TestCase):
    def test_satir_sirasi_sonucu_etkilemez(self):
        s = satirlar()
        karisik = s[:]
        random.Random(1).shuffle(karisik)
        self.assertEqual(hesap(), hesap(hakem_satirlari=karisik))

    def test_girdi_degismez(self):
        s = satirlar()
        once = copy.deepcopy((CHECKS, s, URETILEMEYEN, MODELLER))
        hesap(hakem_satirlari=s)
        self.assertEqual(once, (CHECKS, s, URETILEMEYEN, MODELLER))


class Hatalar(unittest.TestCase):
    def test_eksik_soru_hata(self):
        s = [r for r in satirlar() if not (r["model"] == "A" and r["komut"] == 1 and r["soru"] == "g1")]
        with self.assertRaisesRegex(ValueError, "eksik cevap"):
            hesap(hakem_satirlari=s)

    def test_klibin_hic_satiri_yok_hata(self):
        s = [r for r in satirlar() if not (r["model"] == "B" and r["komut"] == 4)]
        with self.assertRaisesRegex(ValueError, "hakem cevabi yok"):
            hesap(hakem_satirlari=s)

    def test_bilinmeyen_cevap_hata(self):
        s = satirlar()
        s[0]["cevap"] = "belki"
        with self.assertRaisesRegex(ValueError, "bilinmeyen cevap"):
            hesap(hakem_satirlari=s)

    def test_tekrar_satir_hata(self):
        s = satirlar()
        with self.assertRaisesRegex(ValueError, "iki kez"):
            hesap(hakem_satirlari=s + [s[0]])

    def test_tanimsiz_soru_ve_model_ve_komut(self):
        s = satirlar()
        for kotu, desen in (({"soru": "zz"}, "tanimsiz soru"), ({"model": "Z"}, "bilinmeyen model"),
                            ({"komut": 9}, "bilinmeyen komut")):
            with self.subTest(kotu=kotu):
                with self.assertRaisesRegex(ValueError, desen):
                    hesap(hakem_satirlari=s + [dict(s[0], **kotu)])

    def test_uretilemeyen_klibin_cevabi_varsa_hata(self):
        s = satirlar() + [{"model": "C", "komut": 2, "soru": "o1", "cevap": "evet"}]
        with self.assertRaisesRegex(ValueError, "uretilemeyen klip icin"):
            hesap(hakem_satirlari=s)

    def test_uretim_hatasi_iade_bilinmiyor(self):
        u = [{"model": "C", "komut": 2, "durum": "uretim_hatasi"}]
        with self.assertRaisesRegex(ValueError, "iadesi bilinmiyor"):
            hesap(uretilemeyen=u)

    def test_bilinmeyen_durum_ve_tekrar(self):
        with self.assertRaises(ValueError):
            hesap(uretilemeyen=[{"model": "C", "komut": 2, "durum": "x"}])
        with self.assertRaises(ValueError):
            hesap(uretilemeyen=URETILEMEYEN * 2)

    def test_modelsiz_ve_soru_tanimsiz(self):
        with self.assertRaises(ValueError):
            hesap(modeller=[])
        eksik = dict(CHECKS, sorular=CHECKS["sorular"][:-1])
        with self.assertRaisesRegex(ValueError, "soru tanimi yok"):
            hesap(checks=eksik)


class OrtakYok(unittest.TestCase):
    def test_ortak_bos_olunca_none(self):
        u = [{"model": "A", "komut": k, "durum": "reddedildi"} for k in (1, 2)] + \
            [{"model": "B", "komut": k, "durum": "reddedildi"} for k in (3, 4)]
        cevap = {k: v for k, v in CEVAP.items()
                 if not ((k[0] == "A" and k[1] in (1, 2)) or (k[0] == "B" and k[1] in (3, 4)))}
        s = hesap(hakem_satirlari=satirlar(cevap), uretilemeyen=u + URETILEMEYEN)
        self.assertEqual(s["ortak_komutlar"]["komutlar"], [])
        self.assertEqual(s["ortak_komutlar"]["tum_modellerde_hakem_cevabi_olan_komut_sayisi"], 0)
        self.assertIsNone(model(s, "A")["ortak_tuttu"]["yuzde"])


if __name__ == "__main__":
    unittest.main()

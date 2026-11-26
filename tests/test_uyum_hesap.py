import unittest

from tutar.uyum_hesap import uyum_raporu


def soru(id, sutun="tuttu", tur="ortak", eyleme_bagli=False, beklenen="evet"):
    return {"id": id, "tur": tur, "sutun": sutun, "beklenen": beklenen,
            "eyleme_bagli": eyleme_bagli}


# Birim anahtarı: insan[klip][soru_kimligi]; sorular[klip] = soru tanımları listesi.
SORULAR = {
    "K001": [soru("y1", "yapti", "yapti"), soru("o1"),
             soru("g1", tur="grup", eyleme_bagli=True), soru("p1", "puansiz", None)],
    "K002": [soru("y2", "yapti", "yapti"), soru("o2")],
}


def cevaplar(**kw):
    return dict(kw)


class UyumRaporuTest(unittest.TestCase):
    def rapor(self, insan, hakem, sorular=SORULAR):
        return uyum_raporu(insan, hakem, sorular)

    def tam(self, insan_deger="evet", hakem_deger="evet"):
        insan = {"K001": {"y1": insan_deger, "o1": insan_deger, "g1": insan_deger, "p1": "evet"}}
        hakem = {"K001": {"y1": hakem_deger, "o1": hakem_deger, "g1": hakem_deger, "p1": "hayir"}}
        return insan, hakem

    def test_puansiz_dislanir_ve_sayilir(self):
        insan, hakem = self.tam()
        r = self.rapor(insan, hakem)
        self.assertEqual((r["birim"], r["uyusan"], r["dislanan_puansiz"]), (3, 3, 1))
        self.assertEqual(r["uyum"], 1.0)

    def test_puansiz_cevabi_farkli_olsa_da_etkilemez(self):
        insan, hakem = self.tam()
        hakem["K001"]["p1"] = "hakem_yok"
        self.assertEqual(self.rapor(insan, hakem)["uyum"], 1.0)

    def test_insan_hakem_yok_reddedilir(self):
        insan, hakem = self.tam()
        insan["K001"]["o1"] = "hakem_yok"
        with self.assertRaises(ValueError):
            self.rapor(insan, hakem)

    def test_insan_bilinmeyen_deger_reddedilir(self):
        insan, hakem = self.tam()
        insan["K001"]["o1"] = "belki"
        with self.assertRaises(ValueError):
            self.rapor(insan, hakem)

    def test_hakem_bilinmeyen_deger_reddedilir(self):
        insan, hakem = self.tam()
        hakem["K001"]["o1"] = "belki"
        with self.assertRaises(ValueError):
            self.rapor(insan, hakem)

    def test_evet_gorunmuyor_uyusmazlik(self):
        insan, hakem = self.tam()
        hakem["K001"]["o1"] = "gorunmuyor"
        r = self.rapor(insan, hakem)
        self.assertEqual((r["birim"], r["uyusan"]), (3, 2))

    def test_gorunmuyor_gorunmuyor_uyusma(self):
        insan, hakem = self.tam()
        insan["K001"]["o1"] = "gorunmuyor"
        hakem["K001"]["o1"] = "gorunmuyor"
        r = self.rapor(insan, hakem)
        self.assertEqual((r["birim"], r["uyusan"]), (3, 3))

    def test_hakem_yok_uyusmazlik(self):
        insan, hakem = self.tam()
        hakem["K001"]["o1"] = "hakem_yok"
        hakem["K001"]["y1"] = "hakem_yok"
        r = self.rapor(insan, hakem)
        self.assertEqual((r["birim"], r["uyusan"]), (3, 1))

    def test_eyleme_bagli_payda_da_kalir(self):
        # Puan hesabında y1 "hayir" (beklenen evet) eyleme bağlı g1'i paydadan çıkarır;
        # uyumda çıkarmaz.
        insan, hakem = self.tam()
        insan["K001"]["y1"] = "hayir"
        hakem["K001"]["y1"] = "hayir"
        r = self.rapor(insan, hakem)
        self.assertEqual((r["birim"], r["uyusan"]), (3, 3))

    def test_eksik_hakem_cevabi_hata(self):
        insan, hakem = self.tam()
        del hakem["K001"]["g1"]
        with self.assertRaises(ValueError):
            self.rapor(insan, hakem)

    def test_hakemde_klip_hic_yok_hata(self):
        insan, hakem = self.tam()
        with self.assertRaises(ValueError):
            self.rapor(insan, {})

    def test_eksik_insan_cevabi_hata(self):
        insan, hakem = self.tam()
        del insan["K001"]["o1"]
        with self.assertRaises(ValueError):
            self.rapor(insan, hakem)

    def test_soru_tanimi_olmayan_klip_hata(self):
        insan, hakem = self.tam()
        insan["K999"] = {"x": "evet"}
        hakem["K999"] = {"x": "evet"}
        with self.assertRaises(ValueError):
            self.rapor(insan, hakem)

    def test_bilinmeyen_soru_kimligi_hata(self):
        insan, hakem = self.tam()
        insan["K001"]["tipo"] = "evet"
        with self.assertRaises(ValueError):
            self.rapor(insan, hakem)

    def test_bilinmeyen_sutun_hata(self):
        sorular = {"K001": [soru("o1", sutun="baska")]}
        with self.assertRaises(ValueError):
            self.rapor({"K001": {"o1": "evet"}}, {"K001": {"o1": "evet"}}, sorular)

    def test_hakemdeki_fazla_klip_yok_sayilir(self):
        insan, hakem = self.tam()
        hakem["K002"] = {"y2": "hayir", "o2": "hayir"}
        r = self.rapor(insan, hakem)
        self.assertEqual(r["birim"], 3)

    def test_net_sayi(self):
        insan = {"K001": {"y1": "evet", "o1": "evet", "g1": "gorunmuyor", "p1": "evet"},
                 "K002": {"y2": "hayir", "o2": "gorunmuyor"}}
        hakem = {"K001": {"y1": "evet", "o1": "hayir", "g1": "gorunmuyor", "p1": "evet"},
                 "K002": {"y2": "hayir", "o2": "evet"}}
        r = self.rapor(insan, hakem)
        # 5 birim; uyusan: y1, g1, y2 = 3
        self.assertEqual((r["birim"], r["uyusan"]), (5, 3))
        self.assertAlmostEqual(r["uyum"], 0.6)
        # net: iki taraf da evet/hayir: y1 (uyusur), o1 (uyusmaz), y2 (uyusur) -> 2/3
        self.assertEqual(r["net_birim"], 3)
        self.assertAlmostEqual(r["net_uyum"], 2 / 3)
        self.assertFalse(r["esik_gecti"])

    def test_net_yoksa_none(self):
        insan = {"K002": {"y2": "gorunmuyor", "o2": "gorunmuyor"}}
        hakem = {"K002": {"y2": "gorunmuyor", "o2": "hakem_yok"}}
        r = self.rapor(insan, hakem)
        self.assertEqual((r["net_birim"], r["net_uyum"]), (0, None))
        self.assertEqual(r["uyum"], 0.5)

    def test_karisiklik_3x4(self):
        insan = {"K001": {"y1": "evet", "o1": "evet", "g1": "gorunmuyor", "p1": "evet"},
                 "K002": {"y2": "hayir", "o2": "gorunmuyor"}}
        hakem = {"K001": {"y1": "evet", "o1": "hakem_yok", "g1": "gorunmuyor", "p1": "evet"},
                 "K002": {"y2": "evet", "o2": "evet"}}
        k = self.rapor(insan, hakem)["karisiklik"]
        self.assertEqual(sorted(k), ["evet", "gorunmuyor", "hayir"])
        for satir in k.values():
            self.assertEqual(sorted(satir), ["evet", "gorunmuyor", "hakem_yok", "hayir"])
        self.assertEqual(k["evet"]["evet"], 1)
        self.assertEqual(k["evet"]["hakem_yok"], 1)
        self.assertEqual(k["gorunmuyor"]["gorunmuyor"], 1)
        self.assertEqual(k["gorunmuyor"]["evet"], 1)
        self.assertEqual(k["hayir"]["evet"], 1)
        self.assertEqual(sum(sum(s.values()) for s in k.values()), 5)

    def test_esik(self):
        # 20 birim: 17 uyusan = 0.85 gecer; 16 = 0.80 gecmez
        sorular = {"K": [soru(f"q{i}") for i in range(20)]}
        insan = {"K": {f"q{i}": "evet" for i in range(20)}}
        hakem = {"K": {f"q{i}": ("evet" if i < 17 else "hayir") for i in range(20)}}
        r = uyum_raporu(insan, hakem, sorular)
        self.assertEqual((r["uyusan"], r["uyum"], r["esik_gecti"]), (17, 0.85, True))
        hakem["K"]["q16"] = "hayir"
        r = uyum_raporu(insan, hakem, sorular)
        self.assertEqual((r["uyusan"], r["esik_gecti"]), (16, False))

    def test_sifir_birim(self):
        r = self.rapor({}, {})
        self.assertEqual((r["birim"], r["uyum"], r["esik_gecti"]), (0, None, False))
        self.assertEqual((r["net_uyum"], r["net_birim"], r["dislanan_puansiz"]), (None, 0, 0))

    def test_yalniz_puansiz_klip_sifir_birim(self):
        sorular = {"K": [soru("p", "puansiz", None)]}
        r = uyum_raporu({"K": {"p": "evet"}}, {"K": {"p": "evet"}}, sorular)
        self.assertEqual((r["birim"], r["uyum"], r["esik_gecti"], r["dislanan_puansiz"]),
                         (0, None, False, 1))


if __name__ == "__main__":
    unittest.main()

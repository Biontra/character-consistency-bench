"""Geriye uyum: geçerli girdide güncel puan.py, 25 Kasım'da dondurulan sürümle aynı sonucu verir.

Donmuş sürüm `tests/donmus_puan_v1.py` (etiket `tutar-kurallar-v1`). Girdiler
sabit tohumlu, uydurma ve geçerlidir (gerçek sorular kullanılmaz).
"""
import random
import unittest

from tests import donmus_puan_v1 as eski
from tutar import puan as yeni

TOHUM = 20261126
GIRDI_SAYISI = 600
CEVAPLAR = ("evet", "hayir", "gorunmuyor", "hakem_yok")


def rastgele_sorular(rng):
    sorular = []
    for i in range(rng.randint(5, 25)):
        sutun = rng.choice(("yapti", "tuttu", "tuttu", "puansiz"))
        if sutun == "yapti":
            tur = rng.choice(("yapti", "yapti", "ozel"))  # yaptı sütununda özel tür de var
        elif sutun == "tuttu":
            tur = rng.choice(("ortak", "grup", "ozel"))
        else:
            tur = "bilgi"
        sorular.append({
            "id": f"q{i}",
            "tur": tur,
            "sutun": sutun,
            "beklenen": rng.choice(("evet", "hayir")),
            "eyleme_bagli": rng.random() < 0.5,
        })
    return sorular


def rastgele_cevaplar(rng, sorular):
    agirlik = rng.choice(((8, 2, 1, 1), (3, 3, 1, 1), (1, 1, 5, 5)))
    c = {}
    for s in sorular:
        if rng.random() < 0.6:
            c[s["id"]] = s["beklenen"]
        else:
            c[s["id"]] = rng.choices(CEVAPLAR, weights=agirlik)[0]
    return c


def girdiler():
    rng = random.Random(TOHUM)
    for _ in range(GIRDI_SAYISI):
        sorular = rastgele_sorular(rng)
        yield sorular, rastgele_cevaplar(rng, sorular)


class DonmusUyumTest(unittest.TestCase):
    def test_klip_puanla_birebir_ayni(self):
        sayi = 0
        for sorular, cevaplar in girdiler():
            self.assertEqual(yeni.klip_puanla(sorular, cevaplar),
                             eski.klip_puanla(sorular, cevaplar))
            sayi += 1
        self.assertGreaterEqual(sayi, 500)

    def test_model_puanla_birebir_ayni(self):
        rng = random.Random(TOHUM + 1)
        sayi = 0
        for _ in range(GIRDI_SAYISI):
            sorular = rastgele_sorular(rng)
            n = rng.randint(0, 6)
            klipler = [eski.klip_puanla(sorular, rastgele_cevaplar(rng, sorular))
                       for _ in range(n)]
            self.assertEqual(yeni.model_puanla(klipler), eski.model_puanla(klipler))
            sayi += 1
        self.assertGreaterEqual(sayi, 500)

    def test_girdiler_cesitli(self):
        # Test zayıf girdiyle boşa geçmesin: her tür, sütun ve cevap görülmeli.
        turler, sutunlar, cevaplar, eyleme = set(), set(), set(), set()
        for sorular, c in girdiler():
            turler |= {s["tur"] for s in sorular}
            sutunlar |= {s["sutun"] for s in sorular}
            eyleme |= {s["eyleme_bagli"] for s in sorular}
            cevaplar |= set(c.values())
        self.assertEqual(turler, {"yapti", "ozel", "ortak", "grup", "bilgi"})
        self.assertEqual(sutunlar, {"yapti", "tuttu", "puansiz"})
        self.assertEqual(cevaplar, set(CEVAPLAR))
        self.assertEqual(eyleme, {True, False})

    def test_eyleme_bagli_dusurme_goruluyor(self):
        # Girdilerin bir kısmında eylem yok kuralı gerçekten çalışmalı.
        gecersiz = sum(eski.klip_puanla(s, c)["disarida"]["gecersiz"] > 0
                       for s, c in girdiler())
        self.assertGreater(gecersiz, 50)


if __name__ == "__main__":
    unittest.main()

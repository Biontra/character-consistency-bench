import unittest

from scripts.ilk_kare_farki import ortalama_mutlak_fark, ozet_say


class FarkTest(unittest.TestCase):
    def test_ayni_dizi_sifir(self):
        self.assertEqual(ortalama_mutlak_fark(bytes([1, 2, 3]), bytes([1, 2, 3])), 0.0)

    def test_ortalama_mutlak_fark(self):
        a = bytes([0, 10, 200, 255])
        b = bytes([5, 10, 190, 250])
        # |0-5| + 0 + |200-190| + |255-250| = 20, 4 piksel
        self.assertEqual(ortalama_mutlak_fark(a, b), 5.0)

    def test_uzunluk_farkli_hata(self):
        with self.assertRaises(ValueError):
            ortalama_mutlak_fark(bytes([1]), bytes([1, 2]))

    def test_bos_hata(self):
        with self.assertRaises(ValueError):
            ortalama_mutlak_fark(b"", b"")

    def test_ozet_say(self):
        o = ozet_say([3.0, 1.0, 2.0, 10.0])
        self.assertEqual(o, {"en_kucuk": 1.0, "ortanca": 2.5, "en_buyuk": 10.0})


if __name__ == "__main__":
    unittest.main()

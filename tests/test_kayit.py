import copy
import json
import tempfile
import unittest
from pathlib import Path

from tutar import kayit

KOK = Path(__file__).resolve().parent.parent
RESIM_SHA = "01aa3597b8f0d4e666412f00a4f199cc3e3cd0aea80d6f8175900a77806eadb1"


def gecerli():
    return {
        "model": "m1", "komut": 1, "prompt": "p", "durum": "tamam", "hata": None,
        "is_kimligi": "j", "tarih_saat_utc": "2026-11-25T20:30:06Z",
        "gonderilen_parametreler": {"a": 1},
        "baslangic_resmi_sha256": RESIM_SHA, "baslangic_medya_kimligi": "id",
        "dosya": "clips/m1/cmd01.mp4", "sha256": "cd", "sure_sn": 5.04,
        "kare_sayisi": 121, "genislik": 720, "yukseklik": 1280, "fps": 24,
        "ses_var": False, "kredi_teklif": 7.5, "kredi_kesinti": 7.5,
        "cozunurluk_parametresi": None, "prompt_zenginlestirme": "secenek_yok",
        "sunucu_prompt": None, "tohum": None, "model_surumu": None,
    }


class KayitTest(unittest.TestCase):
    def test_gecerli(self):
        kayit.satir_dogrula(gecerli())

    def test_alan_sirasi(self):
        self.assertEqual(set(kayit.ALANLAR), set(gecerli()))
        self.assertEqual(len(kayit.ALANLAR), 25)

    def test_eksik_alan(self):
        s = gecerli(); del s["fps"]
        with self.assertRaises(ValueError):
            kayit.satir_dogrula(s)

    def test_fazla_alan(self):
        s = gecerli(); s["x"] = 1
        with self.assertRaises(ValueError):
            kayit.satir_dogrula(s)

    def test_bilinmeyen_durum(self):
        s = gecerli(); s["durum"] = "belki"
        with self.assertRaises(ValueError):
            kayit.satir_dogrula(s)

    def test_komut_aralik(self):
        for k in (0, 21):
            s = gecerli(); s["komut"] = k
            with self.assertRaises(ValueError):
                kayit.satir_dogrula(s)

    def test_mutlak_yol(self):
        s = gecerli(); s["dosya"] = "/Volumes/Kye/clips/m1/cmd01.mp4"
        with self.assertRaises(ValueError):
            kayit.satir_dogrula(s)

    def test_yol_model_uyusmaz(self):
        s = gecerli(); s["dosya"] = "clips/baska/cmd01.mp4"
        with self.assertRaises(ValueError):
            kayit.satir_dogrula(s)

    def test_tamam_sha_null(self):
        s = gecerli(); s["sha256"] = None
        with self.assertRaises(ValueError):
            kayit.satir_dogrula(s)

    def test_tamam_kare_sayisi_null(self):
        s = gecerli(); s["kare_sayisi"] = None
        with self.assertRaises(ValueError):
            kayit.satir_dogrula(s)

    def test_tamam_fps_null(self):
        s = gecerli(); s["fps"] = None
        with self.assertRaises(ValueError):
            kayit.satir_dogrula(s)

    def test_tamam_ses_var_null(self):
        s = gecerli(); s["ses_var"] = None
        with self.assertRaises(ValueError):
            kayit.satir_dogrula(s)

    def test_tamam_ses_var_false_gecerli(self):
        s = gecerli(); s["ses_var"] = False
        kayit.satir_dogrula(s)

    def test_baslangic_resmi_sha_farkli(self):
        s = gecerli(); s["baslangic_resmi_sha256"] = "ab" * 32
        with self.assertRaises(ValueError):
            kayit.satir_dogrula(s)

    def test_baslangic_resmi_sha_null(self):
        s = gecerli(); s["baslangic_resmi_sha256"] = None
        with self.assertRaises(ValueError):
            kayit.satir_dogrula(s)

    def test_reddedilen_satirda_sha_sabit_yine_istenir(self):
        s = gecerli()
        s.update(durum="reddedildi", hata="x", sha256=None, sure_sn=None,
                 genislik=None, yukseklik=None, kare_sayisi=None, fps=None,
                 ses_var=None)
        kayit.satir_dogrula(s)
        s["baslangic_resmi_sha256"] = "ab"
        with self.assertRaises(ValueError):
            kayit.satir_dogrula(s)

    def test_sabit_deger(self):
        self.assertEqual(kayit.BASLANGIC_RESMI_SHA256, RESIM_SHA)

    def test_hata_satiri_null_olabilir(self):
        s = gecerli()
        s.update(durum="uretim_hatasi", hata="x", sha256=None, sure_sn=None,
                 genislik=None, yukseklik=None)
        kayit.satir_dogrula(s)

    def _yaz(self, d, ad, satirlar):
        (d / ad).write_text("".join(json.dumps(s) + "\n" for s in satirlar))

    def test_yinelenen(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            self._yaz(d, "m1.jsonl", [gecerli(), gecerli()])
            with self.assertRaises(ValueError):
                kayit.kayitlari_oku(d)

    def test_oku_ve_ozet(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            b = gecerli(); b["komut"] = 2; b["dosya"] = "clips/m1/cmd02.mp4"
            b["is_kimligi"] = "j2"
            b.update(durum="reddedildi", hata="x", sha256=None, sure_sn=None,
                     genislik=None, yukseklik=None)
            self._yaz(d, "m1.jsonl", [gecerli(), b])
            k = kayit.kayitlari_oku(d)
            self.assertEqual(len(k), 2)
            self.assertEqual(kayit.ozet(k), {"m1": {"tamam": 1, "reddedildi": 1}})

    def test_ayni_is_kimligi_iki_dosyada_hata(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            a = gecerli(); a["is_kimligi"] = "ayni"
            b = gecerli(); b.update(model="m2", dosya="clips/m2/cmd01.mp4",
                                    is_kimligi="ayni")
            self._yaz(d, "m1.jsonl", [a])
            self._yaz(d, "m2.jsonl", [b])
            with self.assertRaises(ValueError):
                kayit.kayitlari_oku(d)

    def test_ayni_is_kimligi_ayni_dosyada_hata(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            a = gecerli(); a["is_kimligi"] = "ayni"
            b = gecerli(); b.update(komut=2, dosya="clips/m1/cmd02.mp4",
                                    is_kimligi="ayni")
            self._yaz(d, "m1.jsonl", [a, b])
            with self.assertRaises(ValueError):
                kayit.kayitlari_oku(d)

    def test_bos_is_kimligi_tekrari_sorun_degil(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            a = gecerli(); a["is_kimligi"] = None
            b = gecerli(); b.update(komut=2, dosya="clips/m1/cmd02.mp4",
                                    is_kimligi=None)
            self._yaz(d, "m1.jsonl", [a, b])
            self.assertEqual(len(kayit.kayitlari_oku(d)), 2)

    def test_farkli_is_kimligi_gecerli(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            a = gecerli(); a["is_kimligi"] = "j1"
            b = gecerli(); b.update(komut=2, dosya="clips/m1/cmd02.mp4",
                                    is_kimligi="j2")
            self._yaz(d, "m1.jsonl", [a, b])
            self.assertEqual(len(kayit.kayitlari_oku(d)), 2)

    def test_gercek_kayit_is_kimlikleri_tekil(self):
        k = kayit.kayitlari_oku(KOK / "uretim_kaydi")
        idler = [r["is_kimligi"] for r in k if r["is_kimligi"]]
        self.assertEqual(len(idler), len(set(idler)))
        self.assertEqual(len(k), 100)

    def test_gercek_kayit(self):
        k = kayit.kayitlari_oku(KOK / "uretim_kaydi")
        self.assertTrue(any(r["model"] == "kling3_0" for r in k))


if __name__ == "__main__":
    unittest.main()

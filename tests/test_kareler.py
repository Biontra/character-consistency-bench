import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tutar import kareler
from tutar.kareler import kare_cikar

FFMPEG = "/opt/homebrew/bin/ffmpeg"


class KareCikarTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gecici = Path(tempfile.mkdtemp(prefix="tutar-kareler-"))
        cls.klip = cls.gecici / "test.mp4"
        subprocess.run(
            [FFMPEG, "-v", "error", "-f", "lavfi",
             "-i", "testsrc=duration=2:size=720x1280:rate=24",
             "-pix_fmt", "yuv420p", str(cls.klip)],
            check=True,
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.gecici, ignore_errors=True)

    def test_kareler_ve_yarimlar(self):
        hedef = self.gecici / "cikti"
        bilgi = kare_cikar(self.klip, hedef)
        self.assertAlmostEqual(bilgi["kare_sayisi"], 20, delta=1)
        self.assertEqual(bilgi["genislik"], 720)
        self.assertEqual(bilgi["yukseklik"], 1280)
        sayilar = [len(list((hedef / k).glob("*.png"))) for k in ("tam", "ust", "alt")]
        self.assertEqual(sayilar[0], bilgi["kare_sayisi"])
        self.assertEqual(len(set(sayilar)), 1)
        self.assertTrue((hedef / "tam" / "001.png").exists())

    def test_ust_yari_boyutu(self):
        hedef = self.gecici / "cikti2"
        kare_cikar(self.klip, hedef)
        for yarim in ("ust", "alt"):
            cikti = subprocess.run(
                ["/opt/homebrew/bin/ffprobe", "-v", "error", "-select_streams", "v:0",
                 "-show_entries", "stream=width,height", "-of", "csv=p=0",
                 str(hedef / yarim / "001.png")],
                capture_output=True, text=True, check=True,
            ).stdout.strip()
            self.assertEqual(cikti, "720,640")

    def test_olmayan_klip(self):
        with self.assertRaises(FileNotFoundError):
            kare_cikar(self.gecici / "yok.mp4", self.gecici / "x")

    def test_bozuk_klip(self):
        bozuk = self.gecici / "bozuk.mp4"
        bozuk.write_text("bu bir video degil")
        with self.assertRaises(RuntimeError):
            kare_cikar(bozuk, self.gecici / "y")
        self.assertFalse((self.gecici / "y").exists())

    def test_ikinci_cagri_eski_kareleri_temizler(self):
        hedef = self.gecici / "tekrar"
        ilk = kare_cikar(self.klip, hedef, fps=10)
        ikinci = kare_cikar(self.klip, hedef, fps=5)
        self.assertLess(ikinci["kare_sayisi"], ilk["kare_sayisi"])
        for k in ("tam", "ust", "alt"):
            self.assertEqual(len(list((hedef / k).glob("*.png"))), ikinci["kare_sayisi"])

    def test_ffmpeg_hata_kodu(self):
        with mock.patch.object(kareler, "FFMPEG", "/usr/bin/false"):
            with self.assertRaises(RuntimeError):
                kare_cikar(self.klip, self.gecici / "h1")

    def test_sifir_kare(self):
        with mock.patch.object(kareler, "FFMPEG", "/usr/bin/true"):
            with self.assertRaisesRegex(RuntimeError, "Hiç kare"):
                kare_cikar(self.klip, self.gecici / "h2")

    def test_yan_dosyali_klasorde_dogru_sayi(self):
        hedef = self.gecici / "yan"
        ilk = kare_cikar(self.klip, hedef)
        for k in ("tam", "ust", "alt"):
            (hedef / k / "._001.png").write_bytes(b"yan")
            (hedef / k / "._zzz.png").write_bytes(b"yan")
        ikinci = kare_cikar(self.klip, hedef)
        self.assertEqual(ikinci["kare_sayisi"], ilk["kare_sayisi"])
        for k in ("tam", "ust", "alt"):
            gercek = [p for p in (hedef / k).glob("*.png") if not p.name.startswith("._")]
            self.assertEqual(len(gercek), ikinci["kare_sayisi"])

    def test_yan_dosya_silinirken_hata_yok(self):
        hedef = self.gecici / "yan2"
        (hedef / "tam").mkdir(parents=True)
        (hedef / "tam" / "._001.png").write_bytes(b"yan")
        bilgi = kare_cikar(self.klip, hedef)
        self.assertGreater(bilgi["kare_sayisi"], 0)

    def test_yalniz_yan_dosya_sifir_kare_sayilir(self):
        hedef = self.gecici / "yan3"
        (hedef / "tam").mkdir(parents=True)
        (hedef / "tam" / "._001.png").write_bytes(b"yan")
        with mock.patch.object(kareler, "FFMPEG", "/usr/bin/true"):
            with self.assertRaisesRegex(RuntimeError, "Hiç kare"):
                kare_cikar(self.klip, hedef)

    def test_ffmpegin_biraktigi_yan_dosyalar_sayilmaz(self):
        # exFAT'te macOS yazarken ._ dosyası bırakır; sayıyı şişirmemeli.
        hedef = self.gecici / "yan4"
        gercek = kareler._calistir

        def sahte(komut):
            if komut[0] != kareler.FFMPEG:
                return gercek(komut)
            for k in ("tam", "ust", "alt"):
                for n in (1, 2, 3):
                    (hedef / k / f"{n:03d}.png").write_bytes(b"png")
                    (hedef / k / f"._{n:03d}.png").write_bytes(b"yan")
            return ""

        with mock.patch.object(kareler, "_calistir", sahte):
            bilgi = kare_cikar(self.klip, hedef)
        self.assertEqual(bilgi["kare_sayisi"], 3)

    def test_eski_yan_dosya_silinemezse_hata_yok(self):
        # Ana dosya silinince ._ eşi de kaybolur; silmeye çalışmamalı.
        hedef = self.gecici / "yan5"
        (hedef / "tam").mkdir(parents=True)
        (hedef / "tam" / "001.png").write_bytes(b"eski")
        (hedef / "tam" / "._001.png").write_bytes(b"yan")
        silinen = []
        gercek_unlink = Path.unlink

        def unlink(self_, *a, **k):
            silinen.append(self_.name)
            return gercek_unlink(self_, *a, **k)

        with mock.patch.object(Path, "unlink", unlink):
            kare_cikar(self.klip, hedef)
        self.assertNotIn("._001.png", silinen)


if __name__ == "__main__":
    unittest.main()

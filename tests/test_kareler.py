import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()

"""İnsan puanlama aracı testleri. Yalnız UYDURMA veri; gerçek soru metni yok."""
import hashlib
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from tutar import insan_kayit as ik
from scripts import insan_puanla as sunucu

DEPO = Path(__file__).resolve().parent.parent
MODELLER = ["uydumodelbir", "uydumodeliki"]


def dunya(kok, kare=50, metin_yaz=True):
    """3 klipli sahte dünya. Döndürür: (secim, esleme, checks, komutlar)."""
    secim = {"tohum": 1, "secim": [
        {"model": MODELLER[0], "komut": 1}, {"model": MODELLER[1], "komut": 2},
        {"model": MODELLER[0], "komut": 2}]}
    esleme = [{"klip": "K003", "model": MODELLER[0], "komut": 1},
              {"klip": "K001", "model": MODELLER[1], "komut": 2},
              {"klip": "K002", "model": MODELLER[0], "komut": 2},
              {"klip": "K004", "model": MODELLER[1], "komut": 1}]
    sorular = [
        {"id": "a1", "tur": "ortak", "sutun": "tuttu", "beklenen": "evet",
         "eyleme_bagli": False, "metin": "Uydurma soru bir?", "kaynak": "x"},
        {"id": "a2", "tur": "yapti", "sutun": "yapti", "beklenen": "evet",
         "eyleme_bagli": False, "metin": "Uydurma soru iki?", "kaynak": "x"},
        {"id": "a3", "tur": "bilgi", "sutun": "puansiz", "beklenen": None,
         "eyleme_bagli": False, "metin": "Uydurma <bilgi> sorusu?", "kaynak": "x"},
    ]
    checks = {"sorular": sorular, "komutlar": {"1": ["a1", "a2"], "2": ["a1", "a2", "a3"]}}
    komutlar = [{"id": 1, "tr": "bir", "en": "Uydurma command one", "ceviri": ""},
                {"id": 2, "tr": "iki", "en": "Uydurma command two", "ceviri": ""}]
    sid = {s["id"]: s for s in sorular}
    for r in esleme:
        d = Path(kok) / "hakem_girdi" / r["klip"]
        (d / "tam").mkdir(parents=True)
        (d / "ust").mkdir()
        for i in range(1, kare + 1):
            (d / "tam" / f"{i:03d}.png").write_bytes(b"\x89PNG\r\n\x1a\nfake")
        (d / "ust" / "001.png").write_bytes(b"x")
        (d / "tam" / "._001.png").write_bytes(b"x")
        if metin_yaz:
            en = [k["en"] for k in komutlar if k["id"] == r["komut"]][0]
            satir = "\n".join(f"{i}: {sid[i]['metin']}" for i in checks["komutlar"][str(r["komut"])])
            (d / "sorular.txt").write_text(f"komut:\n{en}\nSorular:\n{satir}\n", encoding="utf-8")
    return secim, esleme, checks, komutlar


class KlipListesiTest(unittest.TestCase):
    def test_k_koduna_gore_sirali_ve_model_yok(self):
        secim, esleme, _, _ = dunya(tempfile.mkdtemp())
        liste = ik.klip_listesi(secim, esleme)
        self.assertEqual([k["klip"] for k in liste], ["K001", "K002", "K003"])
        self.assertEqual([k["komut"] for k in liste], [2, 2, 1])
        self.assertNotIn("model", json.dumps(liste))

    def test_eslemede_olmayan_cift_hata(self):
        secim, esleme, _, _ = dunya(tempfile.mkdtemp())
        secim["secim"].append({"model": "yok", "komut": 9})
        with self.assertRaises(ik.AracHatasi):
            ik.klip_listesi(secim, esleme)


class OturumTest(unittest.TestCase):
    def kur(self, **kw):
        self.kok = Path(tempfile.mkdtemp())
        self.d = dunya(self.kok, **kw)
        self.cevap = self.kok / "gizli" / "v1" / "cevaplar.json"
        return ik.oturum_kur(self.kok, *self.d, self.cevap)

    def test_klip_icerigi(self):
        o = self.kur()
        k = o.klipler[0]
        self.assertEqual(k["klip"], "K001")
        self.assertEqual(k["komut_en"], "Uydurma command two")
        self.assertEqual([s["id"] for s in k["sorular"]], ["a1", "a2", "a3"])
        self.assertEqual(len(k["kareler"]), 50)
        self.assertEqual(k["kareler"][0], "001.png")
        self.assertEqual(k["kareler"][-1], "050.png")
        for s in k["sorular"]:
            self.assertEqual(set(s), {"id", "metin"})

    def test_kare_eksikse_acilmaz(self):
        with self.assertRaises(ik.AracHatasi) as c:
            self.kur(kare=49)
        self.assertIn("50", str(c.exception))

    def test_surucu_yoksa_acilmaz(self):
        kok = Path(tempfile.mkdtemp())
        d = dunya(kok)
        with self.assertRaises(ik.AracHatasi) as c:
            ik.oturum_kur(kok / "yok", *d, kok / "c.json")
        self.assertIn("surucu", str(c.exception).lower().replace("ü", "u"))

    def test_sorular_txt_ile_uyusmazsa_acilmaz(self):
        kok = Path(tempfile.mkdtemp())
        d = dunya(kok)
        (kok / "hakem_girdi" / "K001" / "sorular.txt").write_text("baska", encoding="utf-8")
        with self.assertRaises(ik.AracHatasi):
            ik.oturum_kur(kok, *d, kok / "c.json")

    def test_sorular_txt_yoksa_acilmaz(self):
        with self.assertRaises(ik.AracHatasi):
            self.kur(metin_yaz=False)

    def test_kaydet_ve_devam(self):
        o = self.kur()
        o.depo.kaydet("K001", "a1", "evet")
        o.depo.kaydet("K001", "a1", "hayir")  # degistirilebilir
        o.depo.kaydet("K001", "a3", "gorunmuyor")  # puansiz da kaydedilir
        self.assertEqual(o.depo.cevap("K001", "a1"), "hayir")
        yeni = ik.oturum_kur(self.kok, *self.d, self.cevap)
        self.assertEqual(yeni.depo.cevap("K001", "a1"), "hayir")
        self.assertEqual(yeni.depo.cevap("K001", "a3"), "gorunmuyor")
        self.assertIsNone(yeni.depo.cevap("K001", "a2"))

    def test_gecersiz_kayit_reddi(self):
        o = self.kur()
        for k, s, c in [("K001", "a1", "hakem_yok"), ("K001", "a1", "belki"),
                        ("K001", "a1", "Evet"), ("K001", "a1", None),
                        ("K009", "a1", "evet"), ("K001", "zz", "evet"),
                        ("K003", "a3", "evet")]:  # K003'te a3 yok
            with self.assertRaises(ik.Reddedildi, msg=(k, s, c)):
                o.depo.kaydet(k, s, c)
        self.assertFalse(self.cevap.exists())

    def test_atomik_yazim_artik_dosya_birakmaz(self):
        o = self.kur()
        o.depo.kaydet("K001", "a1", "evet")
        self.assertEqual([p.name for p in self.cevap.parent.iterdir()], ["cevaplar.json"])

    def test_bozuk_dosya_acilmaz(self):
        self.kur()
        self.cevap.parent.mkdir(parents=True, exist_ok=True)
        self.cevap.write_text(json.dumps({"bitti": False, "cevaplar": {"K001": {"a1": "hakem_yok"}}}))
        with self.assertRaises(ik.AracHatasi):
            ik.oturum_kur(self.kok, *self.d, self.cevap)

    def hepsini_cevapla(self, o):
        for k in o.klipler:
            for s in k["sorular"]:
                o.depo.kaydet(k["klip"], s["id"], "evet")

    def test_ilerleme(self):
        o = self.kur()
        self.assertEqual(o.depo.ilerleme("K001"), (0, 3))
        self.assertEqual(o.depo.ilerleme(), (0, 8))
        o.depo.kaydet("K001", "a1", "evet")
        self.assertEqual(o.depo.ilerleme("K001"), (1, 3))
        self.assertEqual(o.depo.ilerleme(), (1, 8))

    def test_bitir_eksikse_reddedilir(self):
        o = self.kur()
        o.depo.kaydet("K001", "a1", "evet")
        with self.assertRaises(ik.Reddedildi):
            o.depo.bitir()
        self.assertFalse(o.depo.bitti)

    def test_bitir_kilitler_ve_sha(self):
        o = self.kur()
        self.hepsini_cevapla(o)
        o.depo.bitir()
        veri = json.loads(self.cevap.read_text(encoding="utf-8"))
        self.assertTrue(veri["bitti"])
        self.assertTrue(veri["bitis"])
        sha = (self.cevap.parent / "cevaplar.sha256").read_text().split()[0]
        self.assertEqual(sha, hashlib.sha256(self.cevap.read_bytes()).hexdigest())
        with self.assertRaises(ik.Reddedildi):
            o.depo.kaydet("K001", "a1", "hayir")
        with self.assertRaises(ik.Reddedildi):
            o.depo.bitir()
        self.assertEqual(o.depo.cevap("K001", "a1"), "evet")
        yeni = ik.oturum_kur(self.kok, *self.d, self.cevap)
        self.assertTrue(yeni.depo.bitti)
        with self.assertRaises(ik.Reddedildi):
            yeni.depo.kaydet("K001", "a1", "hayir")

    def test_sha_uyusmazsa_acilmaz(self):
        o = self.kur()
        self.hepsini_cevapla(o)
        o.depo.bitir()
        (self.cevap.parent / "cevaplar.sha256").write_text("0" * 64 + "  cevaplar.json\n")
        with self.assertRaises(ik.AracHatasi):
            ik.oturum_kur(self.kok, *self.d, self.cevap)


class KaynakTest(unittest.TestCase):
    def test_hakem_cevap_yollari_kodda_yok(self):
        for yol in ("tutar/insan_kayit.py", "scripts/insan_puanla.py"):
            kaynak = (DEPO / yol).read_text(encoding="utf-8")
            for yasak in ("judge_raw", "hakem/v1", "hakem\\v1"):
                self.assertNotIn(yasak, kaynak, f"{yol}: {yasak}")


class SunucuTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.kok = Path(tempfile.mkdtemp())
        d = dunya(cls.kok)
        cls.cevap = cls.kok / "g" / "v1" / "cevaplar.json"
        cls.oturum = ik.oturum_kur(cls.kok, *d, cls.cevap)
        cls.srv = sunucu.sunucu_kur(cls.oturum, port=0)
        cls.port = cls.srv.server_address[1]
        cls.t = threading.Thread(target=cls.srv.serve_forever, daemon=True)
        cls.t.start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()

    def al(self, yol, veri=None, tip="application/json"):
        istek = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{yol}",
            data=None if veri is None else (veri if isinstance(veri, bytes) else json.dumps(veri).encode()),
            headers={"Content-Type": tip} if veri is not None else {})
        try:
            with urllib.request.urlopen(istek) as r:
                return r.status, r.headers, r.read()
        except urllib.error.HTTPError as e:
            try:
                return e.code, e.headers, e.read()
            finally:
                e.close()

    def test_yalniz_yerel(self):
        self.assertEqual(self.srv.server_address[0], "127.0.0.1")

    def test_sayfalar_ve_model_adi_yok(self):
        for yol in ("/", "/klip/K001", "/klip/K002", "/klip/K003"):
            durum, _, g = self.al(yol)
            self.assertEqual(durum, 200, yol)
            metin = g.decode("utf-8").lower()
            for m in MODELLER:
                self.assertNotIn(m, metin)
        _, _, g = self.al("/klip/K001")
        g = g.decode("utf-8")
        self.assertEqual(g.count("/kare/K001/"), 50)
        self.assertIn("Klip 1 / 3", g)
        self.assertIn("K001", g)
        self.assertIn("Uydurma soru bir?", g)
        self.assertIn("Uydurma &lt;bilgi&gt; sorusu?", g)
        self.assertIn("Uydurma command two", g)
        self.assertNotIn("/ust/", g)
        self.assertNotIn("<video", g)
        self.assertNotIn("http://", g.replace(f"http://127.0.0.1", ""))
        self.assertNotIn("https://", g)

    def test_bilinmeyen_klip_404(self):
        self.assertEqual(self.al("/klip/K004")[0], 404)
        self.assertEqual(self.al("/klip/..")[0], 404)

    def test_kare(self):
        durum, baslik, g = self.al("/kare/K001/001.png")
        self.assertEqual(durum, 200)
        self.assertEqual(baslik["Content-Type"], "image/png")
        self.assertEqual(self.al("/kare/K001/051.png")[0], 404)
        self.assertEqual(self.al("/kare/K001/._001.png")[0], 404)
        self.assertEqual(self.al("/kare/K001/..%2f..%2fsorular.txt")[0], 404)
        self.assertEqual(self.al("/kare/K004/001.png")[0], 404)

    def test_cevap_post(self):
        for c in ("hakem_yok", "belki"):
            durum, _, _ = self.al("/cevap", {"klip": "K001", "soru": "a1", "cevap": c})
            self.assertEqual(durum, 400)
        self.assertFalse(self.cevap.exists())
        durum, _, _ = self.al("/cevap", {"klip": "K001", "soru": "a1", "cevap": "evet"})
        self.assertEqual(durum, 200)
        self.assertEqual(json.loads(self.cevap.read_text())["cevaplar"]["K001"]["a1"], "evet")
        _, _, g = self.al("/cevap", {"klip": "K001", "soru": "a2", "cevap": "hayir"})
        self.assertEqual(json.loads(g)["klip"], [2, 3])
        # json olmayan icerik turu reddedilir
        durum, _, _ = self.al("/cevap", b'{"klip":"K001","soru":"a1","cevap":"hayir"}',
                              tip="text/plain")
        self.assertEqual(durum, 400)
        self.assertEqual(self.oturum.depo.cevap("K001", "a1"), "evet")
        durum, _, _ = self.al("/cevap", b"bozuk")
        self.assertEqual(durum, 400)

    def test_bitir_eksikse_400(self):
        durum, _, _ = self.al("/bitir", {})
        self.assertEqual(durum, 400)


if __name__ == "__main__":
    unittest.main()

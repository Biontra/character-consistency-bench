"""İnsan puanlama aracı testleri. Yalnız UYDURMA veri; gerçek soru metni yok."""
import contextlib
import hashlib
import io
import json
import re
import socket
import tempfile
import threading
import unittest
from unittest import mock
import urllib.error
import urllib.request
from pathlib import Path

from tutar import insan_kayit as ik
from tutar.hakem import hakem_metni
from scripts import insan_puanla as sunucu

DEPO = Path(__file__).resolve().parent.parent
MODELLER = ["uydumodelbir", "uydumodeliki"]
SABLON = DEPO / "judge" / "judge_prompt_v1.txt"  # hakem_hazirla.py ile ayni dosya


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
            (d / "sorular.txt").write_text(
                hakem_metni(SABLON.read_text(encoding="utf-8"), en,
                            [sid[i] for i in checks["komutlar"][str(r["komut"])]]),
                encoding="utf-8")
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

    # ---- D3 / D4 ----
    def gercek_bicim(self, kok, klip, komut_satirlari, soru_satirlari):
        """hakem_hazirla ile ayni sablon ve islevle uretilmis metin; satirlar elle bozulabilir."""
        metin = hakem_metni(SABLON.read_text(encoding="utf-8"), "\n".join(komut_satirlari),
                            [tuple(l.split(": ", 1)) if ": " in l else (l, "")
                             for l in soru_satirlari])
        (Path(kok) / "hakem_girdi" / klip / "sorular.txt").write_text(metin, encoding="utf-8")

    def k001_dogru(self):
        return (["Uydurma command two"],
                ["a1: Uydurma soru bir?", "a2: Uydurma soru iki?", "a3: Uydurma <bilgi> sorusu?"])

    def acilir_mi(self, kok, d):
        return ik.oturum_kur(kok, *d, Path(kok) / "c.json")

    def test_gercek_bicimli_dosya_acilir(self):
        kok = Path(tempfile.mkdtemp())
        d = dunya(kok)
        k, s = self.k001_dogru()
        self.gercek_bicim(kok, "K001", k, s)
        self.assertEqual(len(self.acilir_mi(kok, d).klipler), 3)

    def test_sorularda_fazladan_soru_acilmaz(self):
        kok = Path(tempfile.mkdtemp())
        d = dunya(kok)
        k, s = self.k001_dogru()
        self.gercek_bicim(kok, "K001", k, s + ["a9: Uydurma fazla soru?"])
        with self.assertRaises(ik.AracHatasi):
            self.acilir_mi(kok, d)

    def test_sorularda_eksik_soru_acilmaz(self):
        kok = Path(tempfile.mkdtemp())
        d = dunya(kok)
        k, s = self.k001_dogru()
        self.gercek_bicim(kok, "K001", k, s[:2])
        with self.assertRaises(ik.AracHatasi):
            self.acilir_mi(kok, d)

    def test_soru_metnine_ek_acilmaz(self):
        kok = Path(tempfile.mkdtemp())
        d = dunya(kok)
        k, s = self.k001_dogru()
        s[0] = s[0] + " Ayrica sunu da dusun."
        self.gercek_bicim(kok, "K001", k, s)
        with self.assertRaises(ik.AracHatasi):
            self.acilir_mi(kok, d)

    def test_soru_metnine_onek_acilmaz(self):
        kok = Path(tempfile.mkdtemp())
        d = dunya(kok)
        k, s = self.k001_dogru()
        s[1] = "x" + s[1]  # kimlik bozulur: kimlik kumesi tutmaz
        self.gercek_bicim(kok, "K001", k, s)
        with self.assertRaises(ik.AracHatasi):
            self.acilir_mi(kok, d)

    def test_komut_metnine_ek_acilmaz(self):
        kok = Path(tempfile.mkdtemp())
        d = dunya(kok)
        k, s = self.k001_dogru()
        self.gercek_bicim(kok, "K001", [k[0] + " quickly"], s)
        with self.assertRaises(ik.AracHatasi):
            self.acilir_mi(kok, d)

    def test_komut_satiri_baska_satirin_parcasi_acilmaz(self):
        kok = Path(tempfile.mkdtemp())
        d = dunya(kok)
        k, s = self.k001_dogru()
        self.gercek_bicim(kok, "K001", ["prefix " + k[0]], s)
        with self.assertRaises(ik.AracHatasi):
            self.acilir_mi(kok, d)

    # ---- F1: dosyanin tamami bayt bayt ----
    def degistir(self, fn):
        kok = Path(tempfile.mkdtemp())
        d = dunya(kok)
        yol = kok / "hakem_girdi" / "K001" / "sorular.txt"
        yol.write_bytes(fn(yol.read_bytes()))
        return kok, d

    def test_degismemis_dosya_acilir(self):
        kok = Path(tempfile.mkdtemp())
        d = dunya(kok)
        self.assertEqual(len(self.acilir_mi(kok, d).klipler), 3)

    def test_komut_oncesine_ek_satir_acilmaz(self):
        kok, d = self.degistir(lambda b: b.replace(b"Uydurma command two",
                                                   b"Ek satir\nUydurma command two", 1))
        with self.assertRaises(ik.AracHatasi):
            self.acilir_mi(kok, d)

    def test_sona_ek_bolum_acilmaz(self):
        kok, d = self.degistir(lambda b: b + b"\nEk bolum:\nuydurma\n")
        with self.assertRaises(ik.AracHatasi):
            self.acilir_mi(kok, d)

    def test_talimat_govdesinde_tek_karakter_acilmaz(self):
        sablon = SABLON.read_bytes()
        i = next(j for j, c in enumerate(sablon) if chr(c).isalpha())
        kok, d = self.degistir(lambda b: b.replace(sablon[i:i + 1], b"X" if sablon[i:i + 1] != b"X" else b"Y", 1))
        with self.assertRaises(ik.AracHatasi):
            self.acilir_mi(kok, d)

    def test_satir_sonu_bosluk_acilmaz(self):
        kok, d = self.degistir(lambda b: b.replace(b"Uydurma command two", b"Uydurma command two ", 1))
        with self.assertRaises(ik.AracHatasi):
            self.acilir_mi(kok, d)

    def test_satir_sonu_crlf_acilmaz(self):
        kok, d = self.degistir(lambda b: b.replace(b"\n", b"\r\n"))
        with self.assertRaises(ik.AracHatasi):
            self.acilir_mi(kok, d)

    def test_ayni_kimlik_iki_kez_acilmaz(self):
        kok = Path(tempfile.mkdtemp())
        d = dunya(kok)
        k, s = self.k001_dogru()
        self.gercek_bicim(kok, "K001", k, s + [s[0]])
        with self.assertRaises(ik.AracHatasi):
            self.acilir_mi(kok, d)

    def bitmis(self):
        o = self.kur()
        self.hepsini_cevapla(o)
        o.depo.bitir()
        return o

    def test_bitti_ama_sha_yoksa_acik_hata(self):
        self.bitmis()
        (self.cevap.parent / "cevaplar.sha256").unlink()
        with self.assertRaises(ik.AracHatasi):
            ik.oturum_kur(self.kok, *self.d, self.cevap)
        self.assertFalse((self.cevap.parent / "cevaplar.sha256").exists())  # sessizce uretilmedi

    def test_bitti_ama_eksik_cevap_acik_hata(self):
        self.kur()
        self.cevap.parent.mkdir(parents=True, exist_ok=True)
        self.cevap.write_text(json.dumps({"surum": "v1", "bitti": True, "bitis": "t",
                                          "cevaplar": {"K001": {"a1": "evet"}}}))
        (self.cevap.parent / "cevaplar.sha256").write_text(
            hashlib.sha256(self.cevap.read_bytes()).hexdigest() + "  cevaplar.json\n")
        with self.assertRaises(ik.AracHatasi):
            ik.oturum_kur(self.kok, *self.d, self.cevap)

    def test_bitir_sha_yazilamazsa_bitti_kalici_olmaz(self):
        o = self.kur()
        self.hepsini_cevapla(o)
        with mock.patch.object(ik.CevapDeposu, "_yaz_sha", side_effect=OSError("disk")):
            with self.assertRaises(OSError):
                o.depo.bitir()
        self.assertFalse(o.depo.bitti)
        self.assertFalse(json.loads(self.cevap.read_text())["bitti"])
        self.assertFalse((self.cevap.parent / "cevaplar.sha256").exists())
        yeni = ik.oturum_kur(self.kok, *self.d, self.cevap)  # acilir, "bitti ama sha yok" yok
        self.assertFalse(yeni.depo.bitti)
        yeni.depo.kaydet("K001", "a1", "hayir")
        yeni.depo.bitir()  # sonra yine bitirilebilir
        self.assertTrue(yeni.depo.bitti)

    def test_bitir_json_yazilamazsa_sha_de_kalmaz(self):
        o = self.kur()
        self.hepsini_cevapla(o)
        gercek = ik.CevapDeposu._atomik

        def bozuk(depo, yol, metin):
            if yol == depo.yol and '"bitti": true' in metin:
                raise OSError("disk")
            return gercek(depo, yol, metin)

        with mock.patch.object(ik.CevapDeposu, "_atomik", bozuk):
            with self.assertRaises(OSError):
                o.depo.bitir()
        self.assertFalse(o.depo.bitti)
        self.assertFalse((self.cevap.parent / "cevaplar.sha256").exists())
        self.assertFalse(ik.oturum_kur(self.kok, *self.d, self.cevap).depo.bitti)

    def test_kaydet_yanlis_tur_reddi(self):
        o = self.kur()
        for k, s, c in [(["K001"], "a1", "evet"), ("K001", ["a1"], "evet"),
                        ({"x": 1}, "a1", "evet"), ("K001", 5, "evet"), (7, "a1", "evet")]:
            with self.assertRaises(ik.Reddedildi, msg=(k, s, c)):
                o.depo.kaydet(k, s, c)
        self.assertFalse(self.cevap.exists())


class KaynakTest(unittest.TestCase):
    def test_hakem_cevap_yollari_kodda_yok(self):
        for yol in ("tutar/insan_kayit.py", "scripts/insan_puanla.py"):
            kaynak = (DEPO / yol).read_text(encoding="utf-8")
            for yasak in ("judge_raw", "hakem/v1", "hakem\\v1", "hakem_cikti", "cikti/"):
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

    def test_cevap_yanlis_tur_400_ve_yazmaz(self):
        onceki = self.cevap.read_bytes() if self.cevap.exists() else None
        kotu = [{"klip": ["K001"], "soru": "a1", "cevap": "evet"},
                {"klip": "K001", "soru": ["a1"], "cevap": "evet"},
                {"klip": {"x": 1}, "soru": "a1", "cevap": "evet"},
                {"klip": "K001", "soru": 5, "cevap": "evet"},
                {"klip": "K001", "soru": "a1", "cevap": ["evet"]},
                {"klip": "K001", "soru": "a1", "cevap": {"a": 1}},
                {"klip": None, "soru": None, "cevap": None}, [1, 2], "metin", 5]
        for v in kotu:
            durum, _, g = self.al("/cevap", v)
            self.assertEqual(durum, 400, v)
            self.assertIn("hata", json.loads(g))
        durum, _, _ = self.al("/cevap", b"[" * 3000)
        self.assertEqual(durum, 400)
        sonra = self.cevap.read_bytes() if self.cevap.exists() else None
        self.assertEqual(onceki, sonra)

    def test_bitir_yanlis_govde_400(self):
        for v in ([1], "x", {"klip": ["K001"]}, 5):
            durum, _, g = self.al("/bitir", v)
            self.assertEqual(durum, 400, v)
            self.assertIn("hata", json.loads(g))

    def test_buyuk_gorunum_gercek_boyut(self):
        _, _, g = self.al("/klip/K001")
        g = g.decode("utf-8")
        self.assertIn("gercek", g)           # 1:1 kipi sinifi
        self.assertIn("overflow:auto", sunucu.CSS)
        self.assertIn("max-width:none", sunucu.CSS)

    def test_buyuk_govde_4xx_ve_sunucu_ayakta(self):
        import http.client
        onceki = self.cevap.read_bytes() if self.cevap.exists() else None
        govde = b"{" + b" " * (5 * 1024 * 1024) + b"}"
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=20)
        c.request("POST", "/cevap", body=govde, headers={"Content-Type": "application/json"})
        r = c.getresponse()
        veri = r.read()
        c.close()
        self.assertIn(r.status, (400, 413))
        self.assertIn("hata", json.loads(veri))
        self.assertEqual(self.al("/")[0], 200)
        sonra = self.cevap.read_bytes() if self.cevap.exists() else None
        self.assertEqual(onceki, sonra)

    def test_cok_buyuk_govde_baglanti_kapanir(self):
        import http.client
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=20)
        c.putrequest("POST", "/cevap")
        c.putheader("Content-Type", "application/json")
        c.putheader("Content-Length", str(200 * 1024 * 1024))
        c.endheaders()
        r = c.getresponse()
        r.read()
        c.close()
        self.assertEqual(r.status, 413)
        self.assertEqual(r.getheader("Connection"), "close")
        self.assertEqual(self.al("/")[0], 200)

    def test_bitir_eksikse_400(self):
        durum, _, _ = self.al("/bitir", {})
        self.assertEqual(durum, 400)


class AciklamaTest(unittest.TestCase):
    def test_hakem_kural_6_ornekleri_sayfada(self):
        sablon = (DEPO / "judge" / "judge_prompt_v1.txt").read_text(encoding="utf-8")
        duz = " ".join(sablon.split())
        m = re.search(r"Örnekler: (.*?)\. Ama", duz)
        self.assertIsNotNone(m)
        sayfa = " ".join(re.sub(r"<[^>]+>", "", sunucu.ACIKLAMA).split())
        self.assertIn(m.group(1), sayfa)
        self.assertIn("önceki bilgi", sayfa)


class BaslatmaTest(unittest.TestCase):
    def calistir(self, argv, cevap=None, girdi=None):
        kok = Path(tempfile.mkdtemp())
        d = dunya(kok)
        cevap = cevap or kok / "g" / "v1" / "cevaplar.json"
        err, out = io.StringIO(), io.StringIO()
        with mock.patch.object(sunucu, "_girdiler", lambda: d, create=True), \
                contextlib.redirect_stderr(err), contextlib.redirect_stdout(out):
            kod = sunucu.main(["--kok", str(kok), "--cevap-dosyasi", str(cevap)] + argv)
        return kod, err.getvalue(), cevap

    def test_port_dolu_turkce_mesaj(self):
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        s.listen(1)
        try:
            kod, err, _ = self.calistir(["--port", str(s.getsockname()[1])])
        finally:
            s.close()
        self.assertEqual(kod, 1)
        self.assertIn("başka bir pencerede", err)
        self.assertIn("--port 8766", err)
        self.assertNotIn("Address already in use", err)
        self.assertNotIn("Traceback", err)

    def test_port_gecersiz_turkce_mesaj(self):
        for p in ("99999", "-1", "abc", "", "80.5"):
            kod, err, _ = self.calistir(["--port", p])
            self.assertEqual(kod, 1, p)
            self.assertIn("--port 8766", err)
            self.assertNotIn("Traceback", err)
            self.assertNotIn("Overflow", err)
            self.assertNotIn("invalid", err)

    def test_bozuk_cevap_dosyasi_turkce(self):
        yol = Path(tempfile.mkdtemp()) / "cevaplar.json"
        yol.write_text("{bozuk", encoding="utf-8")
        kod, err, _ = self.calistir(["--port", "0"], cevap=yol)
        self.assertEqual(kod, 1)
        self.assertIn(str(yol), err)
        self.assertIn("bozuk", err)
        for ham in ("Expecting", "JSONDecodeError", "line 1 column", "Traceback"):
            self.assertNotIn(ham, err)


if __name__ == "__main__":
    unittest.main()

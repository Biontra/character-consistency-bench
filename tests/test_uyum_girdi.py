"""Uyum girdi çeviricisi testleri. Yalnız UYDURMA veri."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tutar import uyum_girdi as ug
from tutar.uyum_hesap import uyum_raporu

DEPO = Path(__file__).resolve().parent.parent


def soru(i, sutun="tuttu"):
    return {"id": i, "tur": "ortak", "sutun": sutun, "beklenen": "evet",
            "eyleme_bagli": False, "metin": "uydurma", "kaynak": "x"}


CHECKS = {"sorular": [soru("a"), soru("b", "yapti"), soru("c", "puansiz"), soru("d")],
          "komutlar": {"1": ["a", "b", "d"], "2": ["a", "b", "c", "d"]}}
ESLEME = [{"klip": "K001", "model": "m1", "komut": 1},
          {"klip": "K002", "model": "m2", "komut": 2},
          {"klip": "K003", "model": "m1", "komut": 2},
          {"klip": "K004", "model": "m2", "komut": 1}]


def secim_of(i):
    """Uydurma secim dosyasi: insan dosyasindaki (eslemede olan) klipler. Eski testlerin kurulumu."""
    kod = {r["klip"]: r for r in ESLEME}
    return {"tohum": 1, "secim": [{"model": kod[k]["model"], "komut": kod[k]["komut"]}
                                  for k in sorted(i["cevaplar"]) if k in kod]}


def insan(**klipler):
    return {"bitti": True, "bitis": "t", "cevaplar": klipler}


def satirlar(**klipler):
    return [{"klip": k, "soru": s, "cevap": c, "model": "m", "komut": 1, "kare": None}
            for k, d in klipler.items() for s, c in d.items()]


class CeviriTest(unittest.TestCase):
    def test_bicim(self):
        i = insan(K001={"a": "evet", "b": "hayir", "d": "gorunmuyor"})
        h = satirlar(K001={"a": "evet", "b": "evet", "d": "hakem_yok"},
                     K004={"a": "evet", "b": "evet", "d": "evet"})  # K004 insanda yok
        ins, hak, sor = ug.cevir(CHECKS, ESLEME, i, h, secim_of(i))
        self.assertEqual(ins, {"K001": {"a": "evet", "b": "hayir", "d": "gorunmuyor"}})
        self.assertEqual(hak, {"K001": {"a": "evet", "b": "evet", "d": "hakem_yok"}})
        self.assertEqual([s["id"] for s in sor["K001"]], ["a", "b", "d"])
        self.assertEqual(set(sor), {"K001"})
        r = uyum_raporu(ins, hak, sor)
        self.assertEqual((r["uyusan"], r["birim"]), (1, 3))

    def test_puansiz_soru_dahil(self):
        i = insan(K002={"a": "evet", "b": "evet", "c": "hayir", "d": "evet"})
        h = satirlar(K002={"a": "evet", "b": "evet", "c": "evet", "d": "evet"})
        ins, hak, sor = ug.cevir(CHECKS, ESLEME, i, h, secim_of(i))
        self.assertEqual(uyum_raporu(ins, hak, sor)["dislanan_puansiz"], 1)

    def hata(self, i, h):
        with self.assertRaises(ug.GirdiHatasi):
            ug.cevir(CHECKS, ESLEME, i, h, secim_of(i))

    TAM = {"a": "evet", "b": "evet", "d": "evet"}

    def test_bitmemis(self):
        i = insan(K001=dict(self.TAM))
        i["bitti"] = False
        self.hata(i, satirlar(K001=self.TAM))
        del i["bitti"]
        self.hata(i, satirlar(K001=self.TAM))

    def test_bilinmeyen_klip(self):
        self.hata(insan(K099=dict(self.TAM)), satirlar(K001=self.TAM))
        self.hata(insan(K001=dict(self.TAM)), satirlar(K001=self.TAM, K099=self.TAM))

    def test_eksik_fazla_insan(self):
        self.hata(insan(K001={"a": "evet", "b": "evet"}), satirlar(K001=self.TAM))
        self.hata(insan(K001={**self.TAM, "z": "evet"}), satirlar(K001=self.TAM))

    def test_eksik_fazla_hakem(self):
        self.hata(insan(K001=dict(self.TAM)), satirlar(K001={"a": "evet", "b": "evet"}))
        self.hata(insan(K001=dict(self.TAM)), satirlar(K001={**self.TAM, "z": "evet"}))
        self.hata(insan(K001=dict(self.TAM)), satirlar())

    def test_gecersiz_cevap_ve_tekrar(self):
        self.hata(insan(K001={**self.TAM, "a": "hakem_yok"}), satirlar(K001=self.TAM))
        self.hata(insan(K001=dict(self.TAM)), satirlar(K001={**self.TAM, "a": "belki"}))
        self.hata(insan(K001=dict(self.TAM)), satirlar(K001=self.TAM) + satirlar(K001={"a": "evet"}))

    def test_bos_insan(self):
        self.hata(insan(), satirlar(K001=self.TAM))


class KlipKumesiTest(unittest.TestCase):
    TAM = {"a": "evet", "b": "evet", "d": "evet"}

    def hata(self, i, secim):
        h = satirlar(K001=self.TAM, K004=self.TAM)
        with self.assertRaises(ug.GirdiHatasi):
            ug.cevir(CHECKS, ESLEME, i, h, secim)

    def secim(self, *kodlar):
        kod = {r["klip"]: r for r in ESLEME}
        return {"tohum": 1, "secim": [{"model": kod[k]["model"], "komut": kod[k]["komut"]}
                                      for k in kodlar]}

    def test_ayni_kume_gecer(self):
        i = insan(K001=dict(self.TAM), K004=dict(self.TAM))
        ins, _, _ = ug.cevir(CHECKS, ESLEME, i, satirlar(K001=self.TAM, K004=self.TAM),
                             self.secim("K004", "K001"))
        self.assertEqual(sorted(ins), ["K001", "K004"])

    def test_eksik_klip(self):
        self.hata(insan(K001=dict(self.TAM)), self.secim("K001", "K004"))

    def test_fazla_klip(self):
        self.hata(insan(K001=dict(self.TAM), K004=dict(self.TAM)), self.secim("K001"))

    def test_secimde_olmayan_klip(self):
        self.hata(insan(K001=dict(self.TAM), K004=dict(self.TAM)), self.secim("K001", "K002"))

    def test_secimde_eslemesiz_cift(self):
        s = self.secim("K001", "K004")
        s["secim"][1] = {"model": "yok", "komut": 7}
        self.hata(insan(K001=dict(self.TAM), K004=dict(self.TAM)), s)

    def test_secimde_ayni_klip_iki_kez(self):
        s = self.secim("K001", "K001")
        self.hata(insan(K001=dict(self.TAM)), s)


class YanSayiTest(unittest.TestCase):
    def rapor(self, i, h):
        return ug.hesapla(CHECKS, ESLEME, i, h, secim_of(i))

    def test_ana_sayi_aynen_ve_yan_sayilar(self):
        i = insan(K001={"a": "evet", "b": "hayir", "d": "gorunmuyor"},
                  K003={"a": "evet", "b": "evet", "c": "evet", "d": "hayir"},
                  K004={"a": "evet", "b": "evet", "d": "evet"})
        h = satirlar(
            K001={"a": "hakem_yok", "b": "hayir", "d": "hakem_yok"},      # kismen
            K003={"a": "hakem_yok", "b": "hakem_yok", "c": "hakem_yok", "d": "hakem_yok"},  # tumu
            K004={"a": "evet", "b": "hayir", "d": "evet"})
        r = self.rapor(i, h)
        ins, hak, sor = ug.cevir(CHECKS, ESLEME, i, h, secim_of(i))
        self.assertEqual(r["ana"], uyum_raporu(ins, hak, sor))
        self.assertEqual(r["ana"]["birim"], 9)
        self.assertEqual(r["ana"]["uyusan"], 3)  # K001 b, K004 a ve d
        a = r["yan_sayilar"]["tumu_hakem_yok_klipler_cikarilinca"]
        self.assertEqual((a["uyusan"], a["birim"]), (3, 6))
        self.assertEqual(a["uyum"], 0.5)
        b = r["yan_sayilar"]["hakem_yok_birimler_cikarilinca"]
        self.assertEqual((b["uyusan"], b["birim"]), (3, 4))
        self.assertEqual(b["uyum"], 0.75)
        for y in r["yan_sayilar"].values():
            self.assertNotIn("esik_gecti", y)
            self.assertNotIn("esik", y)
        self.assertEqual(r["tumu_hakem_yok_klipler"], ["K003"])
        self.assertEqual(r["gorunmuyor_hakem_yok_cift"], 1)  # K001 d
        self.assertEqual(r["klip_sayisi"], 3)

    def test_puansiz_hakem_yok_klip_tumu_sayilir(self):
        # puansiz soru hakem_yok degilse klip "tumu hakem_yok" degildir
        i = insan(K002={"a": "evet", "b": "evet", "c": "evet", "d": "evet"})
        h = satirlar(K002={"a": "hakem_yok", "b": "hakem_yok", "c": "evet", "d": "hakem_yok"})
        r = self.rapor(i, h)
        self.assertEqual(r["tumu_hakem_yok_klipler"], [])
        b = r["yan_sayilar"]["hakem_yok_birimler_cikarilinca"]
        self.assertEqual((b["uyusan"], b["birim"], b["uyum"]), (0, 0, None))

    def test_hepsi_cikarilirsa_bos(self):
        i = insan(K001=dict(zip("abd", ["evet"] * 3)))
        h = satirlar(K001=dict(zip("abd", ["hakem_yok"] * 3)))
        r = self.rapor(i, h)
        a = r["yan_sayilar"]["tumu_hakem_yok_klipler_cikarilinca"]
        self.assertEqual((a["uyum"], a["birim"]), (None, 0))
        self.assertEqual(r["ana"]["uyum"], 0.0)

    def test_girdi_degismez(self):
        i = insan(K001=dict(zip("abd", ["evet"] * 3)))
        h = satirlar(K001=dict(zip("abd", ["hakem_yok"] * 3)))
        kopya = json.loads(json.dumps([i, h]))
        self.rapor(i, h)
        self.assertEqual([i, h], kopya)


class BetikTest(unittest.TestCase):
    def kur(self, i=None, sha="dogru"):
        d = Path(tempfile.mkdtemp())
        (d / "checks.json").write_text(json.dumps(CHECKS))
        (d / "esleme.json").write_text(json.dumps(ESLEME))
        i = i or insan(K001={"a": "evet", "b": "hayir", "d": "evet"})
        h = satirlar(K001={"a": "evet", "b": "evet", "d": "evet"})
        (d / "secim.json").write_text(json.dumps(secim_of(i)))
        (d / "insan.json").write_text(json.dumps(i))
        (d / "ham.jsonl").write_text("\n".join(json.dumps(x) for x in h) + "\n")
        if sha == "dogru":
            (d / "cevaplar.sha256").write_text(
                hashlib.sha256((d / "insan.json").read_bytes()).hexdigest() + "  insan.json\n")
        elif sha == "yanlis":
            (d / "cevaplar.sha256").write_text("0" * 64 + "  insan.json\n")
        arg = [sys.executable, str(DEPO / "scripts" / "uyum_hesapla.py"),
               "--insan", str(d / "insan.json"), "--hakem-ham", str(d / "ham.jsonl"),
               "--checks", str(d / "checks.json"), "--esleme", str(d / "esleme.json"),
               "--secim", str(d / "secim.json")]
        return d, arg

    def test_betik_uydurma_dosyalarla(self):
        d, arg = self.kur()
        p = subprocess.run(arg, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        r = json.loads(p.stdout)
        self.assertEqual(r["ana"]["birim"], 3)
        self.assertEqual(r["ana"]["uyusan"], 2)
        i = json.loads((d / "insan.json").read_text())
        i["bitti"] = False
        (d / "insan.json").write_text(json.dumps(i))
        (d / "cevaplar.sha256").write_text(
            hashlib.sha256((d / "insan.json").read_bytes()).hexdigest() + "  insan.json\n")
        p = subprocess.run(arg, capture_output=True, text=True)
        self.assertNotEqual(p.returncode, 0)
        self.assertEqual(p.stdout, "")
        self.assertIn("bitmemis", p.stderr)

    def test_sha_dosyasi_yoksa_calismaz(self):
        d, arg = self.kur(sha="yok")
        p = subprocess.run(arg, capture_output=True, text=True)
        self.assertNotEqual(p.returncode, 0)
        self.assertEqual(p.stdout, "")
        self.assertIn("sha256", p.stderr)

    def test_sha_uyusmazsa_calismaz(self):
        d, arg = self.kur(sha="yanlis")
        p = subprocess.run(arg, capture_output=True, text=True)
        self.assertNotEqual(p.returncode, 0)
        self.assertEqual(p.stdout, "")
        self.assertIn("sha256", p.stderr)

    def test_dosya_sha_sonrasi_degisirse_calismaz(self):
        d, arg = self.kur()
        i = json.loads((d / "insan.json").read_text())
        i["cevaplar"]["K001"]["a"] = "hayir"
        (d / "insan.json").write_text(json.dumps(i))
        p = subprocess.run(arg, capture_output=True, text=True)
        self.assertNotEqual(p.returncode, 0)
        self.assertEqual(p.stdout, "")

    def test_secim_argumani_zorunlu(self):
        d, arg = self.kur()
        k = arg.index("--secim")
        p = subprocess.run(arg[:k] + arg[k + 2:], capture_output=True, text=True)
        self.assertNotEqual(p.returncode, 0)
        self.assertEqual(p.stdout, "")

    def test_betik_klip_kumesi_uyusmazsa_calismaz(self):
        d, arg = self.kur()
        kod = {r["klip"]: r for r in ESLEME}
        (d / "secim.json").write_text(json.dumps({"tohum": 1, "secim": [
            {"model": kod[k]["model"], "komut": kod[k]["komut"]} for k in ("K001", "K004")]}))
        p = subprocess.run(arg, capture_output=True, text=True)
        self.assertNotEqual(p.returncode, 0)
        self.assertEqual(p.stdout, "")


if __name__ == "__main__":
    unittest.main()

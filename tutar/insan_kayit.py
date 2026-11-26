"""İnsan kör puanlama aracının mantığı (PROTOCOL.md, "İnsan puanlama aracı").

Yalnız stdlib. Bu modül hakemin cevap dosyalarına HİÇ bakmaz. Klipler yalnız K kodu
ile anılır; model adı eşleme dosyasından yalnız (model, komut) -> K kodu çevirisi için
okunur ve hiçbir çıktıya girmez.
"""
import hashlib
import json
import os
import tempfile
import threading
from datetime import datetime
from pathlib import Path

CEVAPLAR = ("evet", "hayir", "gorunmuyor")
KARE_SAYISI = 50
SURUM = "v1"
SHA_ADI = "cevaplar.sha256"


class AracHatasi(Exception):
    """Araç açılamaz ya da dosya bozuk. Mesaj sade Türkçedir."""


class Reddedildi(AracHatasi):
    """İstek kural gereği reddedildi; hiçbir dosya değişmedi."""


def klip_listesi(secim, esleme) -> list:
    """20 (model, komut) çiftini K koduna çevirir; K koduna göre artan sıralar.

    Döndürülen kayıtlarda model YOKTUR: {"klip", "komut"}.
    """
    kod = {}
    for r in esleme:
        kod[(r["model"], r["komut"])] = r["klip"]
    liste = []
    for c in secim["secim"]:
        anahtar = (c["model"], c["komut"])
        if anahtar not in kod:
            raise AracHatasi("secimdeki bir klip esleme dosyasinda yok")
        liste.append({"klip": kod[anahtar], "komut": c["komut"]})
    kodlar = [k["klip"] for k in liste]
    if len(set(kodlar)) != len(kodlar):
        raise AracHatasi("ayni klip secimde birden fazla kez var")
    return sorted(liste, key=lambda k: k["klip"])


def _kare_adlari(kok, klip) -> list:
    klasor = Path(kok) / "hakem_girdi" / klip / "tam"
    if not klasor.is_dir():
        raise AracHatasi(f"{klip}: kare klasoru yok")
    adlar = sorted(p.name for p in klasor.glob("*.png") if not p.name.startswith("._"))
    if len(adlar) != KARE_SAYISI:
        raise AracHatasi(f"{klip}: {KARE_SAYISI} kare olmali, {len(adlar)} var")
    return adlar


def _metin_denetimi(kok, klip, komut_en, sorular):
    """Gösterilen metin, hakemin gördüğü dosyayla (sorular.txt) birebir örtüşmeli."""
    yol = Path(kok) / "hakem_girdi" / klip / "sorular.txt"
    if not yol.is_file():
        raise AracHatasi(f"{klip}: hakemin soru dosyasi yok, metin karsilastirilamadi")
    icerik = yol.read_text(encoding="utf-8")
    if komut_en not in icerik:
        raise AracHatasi(f"{klip}: komut metni hakemin gordugunden farkli")
    for s in sorular:
        if f"{s['id']}: {s['metin']}" not in icerik:
            raise AracHatasi(f"{klip}: soru metni hakemin gordugunden farkli ({s['id']})")


def klip_sorulari(checks, komutlar, komut):
    """Hakemin gördüğü komut metni ve soru listesi (kimlik, metin; puansızlar dahil)."""
    kimlikler = checks["komutlar"].get(str(komut))
    if not kimlikler:
        raise AracHatasi(f"komut {komut}: soru listesi yok")
    tanim = {s["id"]: s for s in checks["sorular"]}
    komut_en = [k["en"] for k in komutlar if k["id"] == komut]
    if len(komut_en) != 1:
        raise AracHatasi(f"komut {komut}: komut metni bulunamadi")
    sorular = []
    for k in kimlikler:
        if k not in tanim:
            raise AracHatasi(f"komut {komut}: bilinmeyen soru {k}")
        sorular.append({"id": k, "metin": tanim[k]["metin"]})
    return komut_en[0], sorular


class Oturum:
    def __init__(self, kok, klipler, depo):
        self.kok = Path(kok)
        self.klipler = klipler
        self.depo = depo
        self.sira = {k["klip"]: i for i, k in enumerate(klipler)}

    def klip(self, kod):
        i = self.sira.get(kod)
        return None if i is None else self.klipler[i]

    def kare_yolu(self, kod, ad):
        if kod not in self.sira or ad not in self.klip(kod)["kareler"]:
            return None
        return self.kok / "hakem_girdi" / kod / "tam" / ad


def oturum_kur(kok, secim, esleme, checks, komutlar, cevap_yolu) -> Oturum:
    """Her şeyi denetler; sorun varsa AracHatasi (araç açılmaz)."""
    kok = Path(kok)
    if not (kok / "hakem_girdi").is_dir():
        raise AracHatasi("Kare surucusu bagli degil ya da klasor yok: " + str(kok))
    klipler = []
    for k in klip_listesi(secim, esleme):
        komut_en, sorular = klip_sorulari(checks, komutlar, k["komut"])
        kareler = _kare_adlari(kok, k["klip"])
        _metin_denetimi(kok, k["klip"], komut_en, sorular)
        klipler.append({"klip": k["klip"], "komut_en": komut_en,
                        "sorular": sorular, "kareler": kareler})
    beklenen = {k["klip"]: [s["id"] for s in k["sorular"]] for k in klipler}
    return Oturum(kok, klipler, CevapDeposu(cevap_yolu, beklenen))


class CevapDeposu:
    """Cevapları diske atomik yazar; "bitir"den sonra kilitlenir."""

    def __init__(self, yol, beklenen):
        self.yol = Path(yol)
        self.sha_yolu = self.yol.parent / SHA_ADI
        self.beklenen = {k: list(v) for k, v in beklenen.items()}
        self._kilit = threading.Lock()
        self.cevaplar = {}
        self.bitti = False
        self.bitis = None
        self._yukle()

    def _yukle(self):
        if not self.yol.exists():
            return
        try:
            veri = json.loads(self.yol.read_text(encoding="utf-8"))
            cevaplar = veri["cevaplar"]
            bitti = veri["bitti"]
        except (ValueError, KeyError, TypeError) as hata:
            raise AracHatasi(f"cevap dosyasi okunamadi: {hata}")
        if not isinstance(cevaplar, dict) or not isinstance(bitti, bool):
            raise AracHatasi("cevap dosyasi bicimi gecersiz")
        for klip, c in cevaplar.items():
            if klip not in self.beklenen or not isinstance(c, dict):
                raise AracHatasi(f"cevap dosyasinda bilinmeyen klip: {klip}")
            for soru, deger in c.items():
                if soru not in self.beklenen[klip] or deger not in CEVAPLAR:
                    raise AracHatasi(f"cevap dosyasinda gecersiz kayit: {klip} {soru}")
        self.cevaplar = {k: dict(v) for k, v in cevaplar.items()}
        self.bitti = bitti
        self.bitis = veri.get("bitis")
        if bitti:
            if not self.bitis:
                raise AracHatasi("bitti dosyasinda bitis zamani yok")
            ozet = hashlib.sha256(self.yol.read_bytes()).hexdigest()
            if not self.sha_yolu.exists():
                self._yaz_sha(ozet)  # bitir ile sha yazimi arasinda kesilmis olabilir
            elif self.sha_yolu.read_text().split()[:1] != [ozet]:
                raise AracHatasi("cevap dosyasi bitirildikten sonra degismis (sha256 uyusmuyor)")

    def _atomik(self, yol, metin):
        yol.parent.mkdir(parents=True, exist_ok=True)
        fd, gecici = tempfile.mkstemp(dir=yol.parent, prefix=".gecici-")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(metin)
                f.flush()
                os.fsync(f.fileno())
            os.replace(gecici, yol)
        except BaseException:
            if os.path.exists(gecici):
                os.unlink(gecici)
            raise

    def _yaz_sha(self, ozet):
        self._atomik(self.sha_yolu, f"{ozet}  {self.yol.name}\n")

    def _yaz(self):
        veri = {"surum": SURUM, "bitti": self.bitti, "bitis": self.bitis,
                "cevaplar": self.cevaplar}
        self._atomik(self.yol, json.dumps(veri, indent=2, ensure_ascii=False, sort_keys=True) + "\n")

    def cevap(self, klip, soru):
        return self.cevaplar.get(klip, {}).get(soru)

    def kaydet(self, klip, soru, cevap):
        with self._kilit:
            if self.bitti:
                raise Reddedildi("Puanlama bitirildi, cevap degistirilemez")
            if klip not in self.beklenen:
                raise Reddedildi("bilinmeyen klip")
            if soru not in self.beklenen[klip]:
                raise Reddedildi("bu klipte boyle bir soru yok")
            if not isinstance(cevap, str) or cevap not in CEVAPLAR:
                raise Reddedildi("cevap evet, hayir ya da gorunmuyor olmali")
            onceki = self.cevaplar.get(klip, {}).get(soru)
            self.cevaplar.setdefault(klip, {})[soru] = cevap
            try:
                self._yaz()
            except BaseException:
                if onceki is None:
                    del self.cevaplar[klip][soru]
                    if not self.cevaplar[klip]:
                        del self.cevaplar[klip]
                else:
                    self.cevaplar[klip][soru] = onceki
                raise

    def ilerleme(self, klip=None):
        """(cevaplanan, toplam). klip verilmezse tüm klipler."""
        kliplar = [klip] if klip else list(self.beklenen)
        toplam = sum(len(self.beklenen[k]) for k in kliplar)
        yapilan = sum(len(self.cevaplar.get(k, {})) for k in kliplar)
        return yapilan, toplam

    def bitir(self):
        with self._kilit:
            if self.bitti:
                raise Reddedildi("Zaten bitirilmis")
            yapilan, toplam = self.ilerleme()
            if yapilan != toplam:
                raise Reddedildi(f"Bitirmek icin tum sorular cevaplanmali ({yapilan}/{toplam})")
            self.bitti = True
            self.bitis = datetime.now().astimezone().isoformat(timespec="seconds")
            try:
                self._yaz()
            except BaseException:
                self.bitti, self.bitis = False, None
                raise
            self._yaz_sha(hashlib.sha256(self.yol.read_bytes()).hexdigest())

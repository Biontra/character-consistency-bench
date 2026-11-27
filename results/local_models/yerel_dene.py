"""Gorev 6: yerel vision modeli (Ollama) benchmark'in 10 kontrol sorusunu cevaplar.

Dogru cevap = Kaan'in elle verdigi cevap (kilitli insan puanlamasi).
Ekrana soru METNI yazilmaz, yalniz soru kimligi yazilir (sorular gizli).
Kullanim: python3 yerel_dene.py [model]   (varsayilan: llava:7b)
"""
import base64
import os
import io
import json
import random
import sys
import time
import urllib.request
from pathlib import Path

from PIL import Image

REPO = Path.home() / "character-consistency-bench"
KARELER = REPO / "secret" / "insan_kareler" / "hakem_girdi"
CIKTI = Path(__file__).parent
MODEL = sys.argv[1] if len(sys.argv) > 1 else "llava:7b"
TOHUM = 6          # sabit: secim her calistirmada ayni
ADET_EVET = 5      # insan cevabi "evet" olan soru
ADET_HAYIR = 5     # insan cevabi "hayir" olan soru
KARE_NO = (1, 25, 50)  # klibin basi, ortasi, sonu


def yukle():
    insan = json.load(open(REPO / "secret/insan/v1/cevaplar.json"))["cevaplar"]
    hakem = {}
    klip_komut = {}
    for satir in open(REPO / "results/judge_raw.jsonl"):
        r = json.loads(satir)
        hakem[(r["klip"], r["soru"])] = r["cevap"]
        klip_komut[r["klip"]] = (r["model"], r["komut"])
    checks = json.load(open(REPO / "secret/checks.json"))
    metin = {s["id"]: s["metin"] for s in checks["sorular"]}
    return insan, hakem, klip_komut, metin


def sec(insan, hakem):
    """Insanin ve hakemin evet/hayir dedigi sorulardan, sabit tohumla 5 evet + 5 hayir."""
    havuz = {"evet": [], "hayir": []}
    for klip in sorted(insan):
        for soru in sorted(insan[klip]):
            i, h = insan[klip][soru], hakem.get((klip, soru))
            if i in havuz and h in ("evet", "hayir"):
                havuz[i].append((klip, soru))
    rs = random.Random(TOHUM)
    return (rs.sample(havuz["evet"], ADET_EVET)
            + rs.sample(havuz["hayir"], ADET_HAYIR))


def uc_kare(klip):
    """Bas, orta, son kareyi yan yana tek resim yapar (llava tek resimle calisir)."""
    kareler = [Image.open(KARELER / klip / "tam" / f"{n:03d}.png").convert("RGB")
               for n in KARE_NO]
    g, y = kareler[0].size
    tuval = Image.new("RGB", (g * 3, y))
    for i, k in enumerate(kareler):
        tuval.paste(k, (i * g, 0))
    tuval.thumbnail((1344, 1344))
    tampon = io.BytesIO()
    tuval.save(tampon, format="JPEG", quality=90)
    return base64.b64encode(tampon.getvalue()).decode()


def sor(resim, soru_metni):
    istem = ("The image shows three frames from one short video, left to right: "
             "start, middle, end.\n"
             f"Question (in Turkish): {soru_metni}\n"
             "Answer with exactly one word: evet (yes), hayir (no) or "
             "gorunmuyor (cannot be seen).")
    govde = json.dumps({"model": MODEL, "prompt": istem, "images": [resim],
                        "stream": False,
                        "options": {"temperature": 0, "num_predict": 8, "seed": 6}}).encode()
    istek = urllib.request.Request(os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434") + "/api/generate", govde,
                                   {"Content-Type": "application/json"})
    # Sure Ollama'nin kendi kaydindan alinir (Mac uyursa duvar saati bozuluyor).
    yanit = json.load(urllib.request.urlopen(istek, timeout=900))
    ham = yanit["response"]
    sure = yanit["total_duration"] / 1e9
    kucuk = ham.strip().lower().replace("ı", "i").replace("ö", "o").replace("ü", "u")
    for cevap in ("gorunmuyor", "evet", "hayir"):
        if kucuk.startswith(cevap):
            return cevap, sure, ham.strip()
    return "anlasilmadi", sure, ham.strip()


def main():
    insan, hakem, _, metin = yukle()
    secim = sec(insan, hakem)
    print(f"Model: {MODEL}   Soru: {len(secim)}   Dogru cevap: insan puanlamasi")
    print(f"{'no':>2}  {'klip':5} {'soru':8} {'insan':6} {'hakem':6} {'yerel':12} {'sn':>6}")
    satirlar = []
    for no, (klip, soru) in enumerate(secim, 1):
        cevap, sure, ham = sor(uc_kare(klip), metin[soru])
        i, h = insan[klip][soru], hakem[(klip, soru)]
        print(f"{no:>2}  {klip:5} {soru:8} {i:6} {h:6} {cevap:12} {sure:6.1f}")
        satirlar.append({"no": no, "klip": klip, "soru": soru, "insan": i,
                         "hakem": h, "yerel": cevap, "yerel_ham": ham,
                         "sn": round(sure, 1)})
    n = len(satirlar)
    yerel_dogru = sum(s["yerel"] == s["insan"] for s in satirlar)
    hakem_dogru = sum(s["hakem"] == s["insan"] for s in satirlar)
    ilk = satirlar[0]["sn"]
    kalan = [s["sn"] for s in satirlar[1:]]
    print("-" * 52)
    print(f"Yerel model dogru: {yerel_dogru}/{n}   Claude hakem dogru: {hakem_dogru}/{n}")
    print(f"Ilk soru (model yukleme dahil): {ilk:.1f} sn   "
          f"Sonraki {len(kalan)} soru ortalama: {sum(kalan) / len(kalan):.1f} sn")
    ozet = {"model": MODEL, "tohum": TOHUM, "kare_no": KARE_NO, "soru_sayisi": n,
            "yerel_dogru": yerel_dogru, "hakem_dogru": hakem_dogru,
            "ilk_soru_sn": ilk, "sonraki_ortalama_sn": round(sum(kalan) / len(kalan), 1),
            "satirlar": satirlar}
    ad = MODEL.replace(":", "_").replace("/", "_")
    json.dump(ozet, open(CIKTI / f"sonuc_{ad}.json", "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()

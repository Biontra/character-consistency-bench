"""sonuc_*.json dosyalarindan model karsilastirma tablosu cikarir (soru metni yazmaz).

Iki puan verir:
- kati: model tam olarak evet / hayir / gorunmuyor yazdiysa sayilir (olcumden once yazilan kural)
- gevsek: Ingilizce "yes" / "no" da kabul edilir. Bu kural ciktilar GORULDUKTEN SONRA eklendi,
  cunku bazi modeller soruyu anlayip Ingilizce cevap verdi.
"""
import json
import sys
from pathlib import Path

KLASOR = Path(__file__).parent
SIRA = ["llava:7b", "gemma3:4b", "qwen2.5vl:3b", "granite3.2-vision", "llava-phi3", "moondream"]
BOYUT_GB = {}  # komut satirindan: model=GB


def gevsek(ham):
    k = ham.strip().lower().replace("ı", "i").replace("ö", "o").replace("ü", "u")
    for anahtar, cevap in (("gorunmuyor", "gorunmuyor"), ("evet", "evet"), ("hayir", "hayir"),
                           ("yes", "evet"), ("no", "hayir")):
        if k.startswith(anahtar):
            return cevap
    return "anlasilmadi"


def satir(d):
    s = d["satirlar"]
    n = len(s)
    kati = sum(x["yerel"] == x["insan"] for x in s)
    gev = sum(gevsek(x["yerel_ham"]) == x["insan"] for x in s)
    cevaplar = [gevsek(x["yerel_ham"]) for x in s]
    dagilim = ", ".join(f"{c} {cevaplar.count(c)}" for c in ("evet", "hayir", "gorunmuyor", "anlasilmadi")
                        if cevaplar.count(c))
    sureler = [x["sn"] for x in s[1:] if x["sn"] > 2]  # 2 sn alti: ayni klip, resim bellekte
    ort = sum(sureler) / len(sureler) if sureler else float("nan")
    return (f"| {d['model']} | {kati}/{n} | {gev}/{n} | {dagilim} | {ort:.1f} | "
            f"{BOYUT_GB.get(d['model'], '?')} |")


def main():
    for a in sys.argv[1:]:
        m, gb = a.rsplit("=", 1)
        BOYUT_GB[m] = gb
    veriler = {}
    for f in sorted(KLASOR.glob("sonuc_*.json")):
        if "olcum" in f.name:
            continue
        d = json.load(open(f))
        veriler[d["model"]] = d
    print("| Model | Doğru (katı) | Doğru (gevşek) | Verdiği cevaplar | sn/soru | Boyut (GB) |")
    print("|---|---|---|---|---|---|")
    for m in SIRA + [m for m in veriler if m not in SIRA]:
        if m in veriler:
            print(satir(veriler[m]))
    ilk = next(iter(veriler.values()))["satirlar"]
    hakem = sum(x["hakem"] == x["insan"] for x in ilk)
    print(f"| Claude Sonnet (benchmark hakemi, bulut) | {hakem}/{len(ilk)} | {hakem}/{len(ilk)} | "
          f"evet {sum(x['hakem'] == 'evet' for x in ilk)}, hayir {sum(x['hakem'] == 'hayir' for x in ilk)} "
          f"| ölçülmedi | - |")


if __name__ == "__main__":
    main()

"""İnsan kontrolü için klip seçimi: tohumlu, tekrarlanabilir."""
import json
import random
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
TOHUM = 20261125


def insan_klipleri_sec(tohum, modeller, komutlar, model_basina=4):
    if len(komutlar) != len(modeller) * model_basina:
        raise ValueError("komut sayisi model sayisi x model_basina olmali")
    karisik = list(komutlar)
    random.Random(tohum).shuffle(karisik)
    secim = []
    for i, model in enumerate(modeller):
        for komut in karisik[i * model_basina:(i + 1) * model_basina]:
            secim.append({"model": model, "komut": komut})
    return secim


def main():
    modeller = [m["id"] for m in json.loads(
        (DATA / "models.json").read_text(encoding="utf-8"))["modeller"]]
    komutlar = [k["id"] for k in json.loads(
        (DATA / "commands.json").read_text(encoding="utf-8"))]
    cikti = {"tohum": TOHUM,
             "secim": insan_klipleri_sec(TOHUM, modeller, komutlar)}
    (DATA / "insan_secimi.json").write_text(
        json.dumps(cikti, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")


if __name__ == "__main__":
    main()

"""Hakem aşaması hazırlığı. Hakemi ÇALIŞTIRMAZ.

Kullanım: python3 scripts/hakem_hazirla.py [--kok /Volumes/Kye/character-consistency-bench]
                                           [--yalniz-esleme]

- uretim_kaydi'ndan durum == "tamam" çiftlerini alır, K001.. kodlarını verir.
- secret/hakem/esleme.json ve secret/hakem/girdi/Kxxx.txt yazar (git'e girmez).
- Kareleri <kok>/hakem_girdi/Kxxx/{tam,ust,alt}/NNN.png olarak kopyalar.
--yalniz-esleme: yalnız esleme.json yazar, kopyalamaz.
Yalnız stdlib.
"""
import argparse
import json
import sys
from pathlib import Path

DEPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DEPO))

from tutar import kayit  # noqa: E402
from tutar.hakem import hakem_metni, kare_kopyala, klip_kodlari  # noqa: E402

KOK_VARSAYILAN = Path("/Volumes/Kye/character-consistency-bench")


def tamam_ciftler():
    ciftler = []
    for yol in sorted((DEPO / "uretim_kaydi").glob("*.jsonl")):
        for satir in yol.read_text(encoding="utf-8").splitlines():
            if not satir.strip():
                continue
            s = json.loads(satir)
            kayit.satir_dogrula(s)
            if s["durum"] == "tamam":
                ciftler.append((s["model"], s["komut"], s["prompt"]))
    return ciftler


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--kok", default=str(KOK_VARSAYILAN))
    ap.add_argument("--yalniz-esleme", action="store_true")
    a = ap.parse_args(argv)
    kok = Path(a.kok)

    kayitlar = tamam_ciftler()
    ciftler = [(m, k) for m, k, _ in kayitlar]
    kodlar = klip_kodlari(ciftler)

    hakem_dizin = DEPO / "secret" / "hakem"
    (hakem_dizin / "girdi").mkdir(parents=True, exist_ok=True)
    esleme = [{"klip": kodlar[c], "model": c[0], "komut": c[1]} for c in ciftler]
    esleme.sort(key=lambda r: r["klip"])
    (hakem_dizin / "esleme.json").write_text(
        json.dumps(esleme, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"esleme: {len(esleme)} kayit")
    if a.yalniz_esleme:
        return 0

    komutlar = {c["id"]: c["en"] for c in json.loads(
        (DEPO / "data" / "commands.json").read_text(encoding="utf-8"))}
    checks = json.loads((DEPO / "secret" / "checks.json").read_text(encoding="utf-8"))
    sorular = {s["id"]: s for s in checks["sorular"]}
    sablon = (DEPO / "judge" / "judge_prompt_v1.txt").read_text(encoding="utf-8")

    prompt_ile = {(m, k): p for m, k, p in kayitlar}
    for r in esleme:
        m, k = r["model"], r["komut"]
        if prompt_ile[(m, k)] != komutlar[k]:
            raise SystemExit(f"komut metni uretim kaydiyla uyusmuyor: {r['klip']}")
        metin = hakem_metni(sablon, komutlar[k],
                            [sorular[i] for i in checks["komutlar"][str(k)]])
        (hakem_dizin / "girdi" / f"{r['klip']}.txt").write_text(metin, encoding="utf-8")
        kaynak = kok / "frames" / m / f"cmd{k:02d}"
        kare_kopyala(kaynak, kok / "hakem_girdi" / r["klip"])
    print(f"girdi metni ve kare klasoru: {len(esleme)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

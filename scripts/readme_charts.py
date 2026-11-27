"""Builds the four English charts shown in the README. Standard library only.

Usage: python3 scripts/readme_charts.py
Reads results/results.json and results/uyum_raporu.json, writes results/chart_*.svg.
Same input gives the same output. No question text goes into any chart.

The charts are narrow (480 units wide) so they stay readable on a phone, and they carry
their own light and dark colours (prefers-color-scheme) because GitHub shows them as images.
"""
import json
from html import escape
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
W = 480

# Local side test, strict scoring, 10 questions. Source: results/local_models/README.md
YEREL = [("llava:7b", 5), ("qwen2.5vl:3b", 5), ("gemma3:4b", 3),
         ("granite3.2-vision", 0), ("moondream", 0), ("llava-phi3", 0)]
HAKEM_AYNI_10 = 8

STIL = """<style>
.bg{fill:#fcfcfb}.t1{fill:#0b0b0b}.t2{fill:#52514e}.grid{stroke:#e4e3df}.track{stroke:#d3d2cd}
.a{fill:#2a78d6}.b{fill:#eb6834}.n{fill:#8a8983}.ring{stroke:#fcfcfb}.mark{stroke:#0b0b0b}
text{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}
.h{font-size:15px;font-weight:600}.s{font-size:11.5px}.l{font-size:13px}.v{font-size:13px;font-weight:600}
.ax{font-size:11px}
@media (prefers-color-scheme:dark){
.bg{fill:#1a1a19}.t1{fill:#f0efec}.t2{fill:#c3c2b7}.grid{stroke:#343432}.track{stroke:#4a4a47}
.a{fill:#3987e5}.b{fill:#d95926}.n{fill:#8f8e88}.ring{stroke:#1a1a19}.mark{stroke:#f0efec}}
</style>"""


def _kap(yukseklik, baslik, altlar, govde, aciklama):
    """Wraps a chart body with the surface, the title lines and an accessible description."""
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {yukseklik}" role="img" '
         f'aria-label="{escape(aciklama)}">', f"<title>{escape(aciklama)}</title>", STIL,
         f'<rect class="bg" width="{W}" height="{yukseklik}" rx="8"/>']
    y = 28
    for satir in baslik:
        p.append(f'<text class="t1 h" x="16" y="{y}">{escape(satir)}</text>')
        y += 20
    y += 0
    for satir in altlar:
        p.append(f'<text class="t2 s" x="16" y="{y}">{escape(satir)}</text>')
        y += 15
    p.extend(govde)
    p.append("</svg>")
    return "\n".join(p) + "\n"


def did_kept(modeller):
    """Dot plot: two measures per model on one zoomed axis, values in two columns on the right."""
    alt, ust = 75.0, 100.0
    x0, x1 = 26, 356
    def x(v):
        return x0 + (v - alt) / (ust - alt) * (x1 - x0)
    sirali = sorted(modeller, key=lambda m: -m["tuttu"]["yuzde"])
    ust_y = 130
    g = []
    g.append(f'<circle class="a" cx="{x0 + 5}" cy="{ust_y - 22}" r="5"/>'
             f'<text class="t2 s" x="{x0 + 15}" y="{ust_y - 18}">Did the command</text>')
    g.append(f'<circle class="b" cx="{x0 + 135}" cy="{ust_y - 22}" r="5"/>'
             f'<text class="t2 s" x="{x0 + 145}" y="{ust_y - 18}">Kept the character</text>')
    g.append(f'<text class="t2 s" x="408" y="{ust_y - 18}" text-anchor="end">Did</text>'
             f'<text class="t2 s" x="464" y="{ust_y - 18}" text-anchor="end">Kept</text>')
    satir_h = 46
    son_y = ust_y + satir_h * len(sirali)
    for t in (75, 80, 85, 90, 95, 100):
        g.append(f'<line class="grid" x1="{x(t):.1f}" y1="{ust_y}" x2="{x(t):.1f}" y2="{son_y}"/>')
        g.append(f'<text class="t2 ax" x="{x(t):.1f}" y="{son_y + 15}" text-anchor="middle">{t}%</text>')
    for i, m in enumerate(sirali):
        y = ust_y + i * satir_h
        ad = m["ad"]
        if m["uretti"] < m["toplam_klip"]:
            ad += f'  ({m["uretti"]}/{m["toplam_klip"]} clips made)'
        g.append(f'<text class="t1 l" x="{x0}" y="{y + 17}">{escape(ad)}</text>')
        cy = y + 32
        yap, tut = m["yapti"]["yuzde"], m["tuttu"]["yuzde"]
        g.append(f'<line class="track" x1="{x(min(yap, tut)):.1f}" y1="{cy}" x2="{x(max(yap, tut)):.1f}" '
                 f'y2="{cy}" stroke-width="2"/>')
        g.append(f'<circle class="a ring" cx="{x(yap):.1f}" cy="{cy}" r="6" stroke-width="2"/>')
        g.append(f'<circle class="b ring" cx="{x(tut):.1f}" cy="{cy}" r="6" stroke-width="2"/>')
        g.append(f'<text class="t1 v" x="408" y="{cy + 4}" text-anchor="end">{yap:.1f}</text>')
        g.append(f'<text class="t1 v" x="464" y="{cy + 4}" text-anchor="end">{tut:.1f}</text>')
    return _kap(son_y + 30,
                ["Kling did every command", "but kept the character least"],
                ["Correct judge answers per model, in %. The axis starts at 75.",
                 "One try per command, so small gaps are not a ranking."],
                g, "Dot plot of two scores for five video models: did the command and kept the character.")


def _yatay(baslik, altlar, satirlar, ust, bicim, aciklama, isaret=None):
    """Horizontal bars with the value at the bar end. satirlar: (label, value, css class)."""
    x0, x1 = 178, 404
    def x(v):
        return x0 + v / ust * (x1 - x0)
    ust_y = 28 + 20 * len(baslik) + 15 * len(altlar) + 6
    satir_h = 28
    son_y = ust_y + satir_h * len(satirlar)
    g = []
    for i, (ad, deger, sinif) in enumerate(satirlar):
        y = ust_y + i * satir_h
        g.append(f'<text class="t1 l" x="{x0 - 10}" y="{y + 17}" text-anchor="end">{escape(ad)}</text>')
        gen = max(x(deger) - x0, 0)
        if gen > 0:
            g.append(f'<path class="{sinif}" d="M{x0},{y + 5} h{max(gen - 4, 0):.1f} a4,4 0 0 1 4,4 v8 '
                     f'a4,4 0 0 1 -4,4 h-{max(gen - 4, 0):.1f} z"/>')
        yazi_x = x0 + gen + 8
        if isaret and -44 < x(isaret[0]) - yazi_x < 6:  # value would sit on the marker line
            yazi_x = x(isaret[0]) + 8
        g.append(f'<text class="t1 v" x="{yazi_x:.1f}" y="{y + 18}">{bicim(deger)}</text>')
    g.append(f'<line class="grid" x1="{x0}" y1="{ust_y}" x2="{x0}" y2="{son_y}"/>')
    if isaret:
        deger, yazi = isaret
        g.append(f'<line class="mark" x1="{x(deger):.1f}" y1="{ust_y - 2}" x2="{x(deger):.1f}" y2="{son_y + 2}" '
                 f'stroke-width="1.5" stroke-dasharray="4 3"/>')
        g.append(f'<text class="t2 ax" x="{x(deger):.1f}" y="{son_y + 16}" text-anchor="middle">{escape(yazi)}</text>')
    return _kap(son_y + (26 if isaret else 12), baslik, altlar, g, aciklama)


def cost(modeller):
    sirali = sorted(modeller, key=lambda m: m["kredi"]["tutan_cevap_basina"])
    satirlar = [(m["ad"], m["kredi"]["tutan_cevap_basina"], "a") for m in sirali]
    return _yatay(["Seedance kept the character best", "and was the cheapest"],
                  ["Higgsfield credits spent per correct “kept the character” answer.", "Lower is better."],
                  satirlar, 1.0, lambda v: f"{v:.2f}",
                  "Bar chart of credits per correct kept-the-character answer for five video models.")


def agreement(uyum):
    genel = uyum["ana"]["uyum"] * 100
    esik = 85.0
    return _yatay(["Human and judge agreed on 80.2%,", "below the 85% set in advance"],
                  ["Share of 343 answers on 20 clips where my hand score and the judge matched."],
                  [("Agreement", genel, "a")], 100.0, lambda v: f"{v:.1f}%",
                  "Bar showing human and judge agreement of 80.2 percent against a threshold of 85 percent.",
                  isaret=(esik, "threshold 85%"))


def local_judges():
    satirlar = [("Claude Sonnet (cloud)", HAKEM_AYNI_10, "a")] + [(ad, d, "n") for ad, d in YEREL]
    return _yatay(["No local model beat a coin flip", "as the judge"],
                  ["Correct answers out of 10 check questions, strict scoring.",
                   "Six open-source vision models on a laptop, against the cloud judge."],
                  satirlar, 10.0, lambda v: f"{v}/10",
                  "Bar chart of correct answers out of ten for the cloud judge and six local models.",
                  isaret=(5, "coin flip"))


def uret(sonuc, uyum):
    return {"chart_did_kept.svg": did_kept(sonuc["modeller"]),
            "chart_cost.svg": cost(sonuc["modeller"]),
            "chart_agreement.svg": agreement(uyum),
            "chart_local_judges.svg": local_judges()}


def main():
    sonuc = json.loads((KOK / "results/results.json").read_text(encoding="utf-8"))
    uyum = json.loads((KOK / "results/uyum_raporu.json").read_text(encoding="utf-8"))
    for ad, svg in uret(sonuc, uyum).items():
        (KOK / "results" / ad).write_text(svg, encoding="utf-8")
        print("wrote results/" + ad)


if __name__ == "__main__":
    main()

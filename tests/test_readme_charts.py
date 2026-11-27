"""README grafikleri: geçerli SVG, beş model adı var, soru metni yok, aynı girdide aynı çıktı."""
import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from scripts.readme_charts import uret

KOK = Path(__file__).resolve().parent.parent


class ReadmeGrafikleri(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sonuc = json.loads((KOK / "results/results.json").read_text(encoding="utf-8"))
        cls.uyum = json.loads((KOK / "results/uyum_raporu.json").read_text(encoding="utf-8"))
        cls.grafikler = uret(cls.sonuc, cls.uyum)

    def test_dort_grafik_gecerli_svg(self):
        self.assertEqual(len(self.grafikler), 4)
        for ad, svg in self.grafikler.items():
            kok = ET.fromstring(svg)
            self.assertTrue(kok.tag.endswith("svg"), ad)

    def test_model_adlari_ve_degerler(self):
        svg = self.grafikler["chart_did_kept.svg"]
        for m in self.sonuc["modeller"]:
            self.assertIn(m["ad"], svg)
            self.assertIn(f'>{m["tuttu"]["yuzde"]:.1f}<', svg)
            self.assertIn(f'>{m["yapti"]["yuzde"]:.1f}<', svg)

    def test_uyum_yuzdesi_rapordan_gelir(self):
        beklenen = f'{self.uyum["ana"]["uyum"] * 100:.1f}%'
        self.assertIn(beklenen, self.grafikler["chart_agreement.svg"])

    def test_ayni_girdi_ayni_cikti_ve_dosyalar_guncel(self):
        self.assertEqual(self.grafikler, uret(self.sonuc, self.uyum))
        for ad, svg in self.grafikler.items():
            self.assertEqual((KOK / "results" / ad).read_text(encoding="utf-8"), svg, ad)

    def test_koyu_tema_renkleri_var(self):
        for svg in self.grafikler.values():
            self.assertIn("prefers-color-scheme:dark", svg)


if __name__ == "__main__":
    unittest.main()

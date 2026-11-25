# Kredi özeti

Kaynak: Higgsfield hesap hareketleri, 26 Kasım 2026'da okundu. Bu dosya hesap düzeyinde bir kanıttır. Satır düzeyinde değildir: jsonl dosyalarındaki `kredi_kesinti` alanı bir satır dışında boştur (yalnız `kling3_0` komut 1 dolu, 7.5). Kesintilerin kanıtı satırlardan değil hesap hareketlerinden gelir. Hesap düzeyi sayılar (968, 265.5, 100 kesinti, 2 iade) hesap ekranından okundu; depodaki kayıtlardan yeniden üretilemez.

## Model başı teklif (klip başına)

| Model | Klip başına kredi | İş sayısı | Teklif toplamı |
|---|---|---|---|
| kling3_0 | 7.5 | 20 | 150 |
| wan3_0 | 7.5 | 20 | 150 |
| seedance_2_0_mini | 5 | 20 | 100 |
| grok_video_v15_lite | 5 | 20 | 100 |
| gemini_omni_flash_1_2 | 11.25 | 20 | 225 |

## Hesap hareketleri

- Kesinti: 100 adet, toplam 725 kredi.
- İade: 2 adet, her biri 11.25, toplam 22.5. İkisi de Gemini Omni komut 2 ve 7 (güvenlik filtresi reddi).
- Net harcama: 725 - 22.5 = 702.5 kredi.
- Bakiye: önce 968, sonra 265.5 (968 - 702.5 = 265.5).
- Benchmark dışı harcama yok.

## jsonl ile karşılaştırma

`kredi_teklif` alanlarının toplamı beş dosyada 725 çıktı (150 + 150 + 100 + 100 + 225). Hesap hareketlerindeki 725 kesinti ile tutuyor. İade düşülünce 702.5, bu da hesap hareketlerindeki net ile tutuyor. Fark yok.

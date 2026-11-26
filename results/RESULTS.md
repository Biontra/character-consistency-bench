# TUTAR sonuç tablosu

İki sütun ayrı okunur, toplanmaz: "komutu yaptı" ve "karakteri tuttu". Parantez içi pay/paydadır. Hesaplar `tutar/puan.py` fonksiyonlarındandır.

## Ana tablo

| Model | Üretti | Komutu yaptı | Karakteri tuttu |
|---|---|---|---|
| Kling 3.0 | 20/20 | %100.0 (21/21) | %84.1 (254/302) |
| Wan 3.0 | 20/20 | %90.9 (20/22) | %92.1 (281/305) |
| Seedance 2.0 Mini | 20/20 | %95.5 (21/22) | %96.1 (292/304) |
| Grok Video 1.5 Lite | 20/20 | %90.0 (18/20) | %94.3 (248/263) |
| Gemini Omni Flash 1.2 | 18/20 | %86.4 (19/22) | %90.9 (250/275) |

Üretilemeyen klip: "komutu yaptı"da yapmadı sayılır, "karakteri tuttu"ya girmez (PROTOCOL.md, "Üretilemeyen klip kuralı"; bu kural videolardan sonra yazıldı).

## Ortak komutlar üzerinden "karakteri tuttu"

Bütün modellerin ürettiği 18 komut: 1, 3, 4, 5, 6, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20. Bu komutlardan bütün modellerde hakem cevabı bulunanların sayısı: 15 (bir modelde tümü hakem_yok olan klibi bulunan komut sayılmaz).

| Model | Ortak komutlarda karakteri tuttu | Tüm kliplerde karakteri tuttu |
|---|---|---|
| Kling 3.0 | %84.1 (228/271) | %84.1 (254/302) |
| Wan 3.0 | %91.6 (252/275) | %92.1 (281/305) |
| Seedance 2.0 Mini | %96.0 (264/275) | %96.1 (292/304) |
| Grok Video 1.5 Lite | %94.1 (225/239) | %94.3 (248/263) |
| Gemini Omni Flash 1.2 | %90.9 (250/275) | %90.9 (250/275) |

## Soru türüne göre döküm

Döküm sorunun türüne göre yapılır, sütununa göre değil (PROTOCOL.md). Üretilemeyen klip dökümde sayılmaz.

| Model | ortak | grup | özel |
|---|---|---|---|
| Kling 3.0 | %85.6 (178/208) | %84.6 (33/39) | %79.3 (46/58) |
| Wan 3.0 | %93.1 (203/218) | %93.9 (31/33) | %86.0 (49/57) |
| Seedance 2.0 Mini | %96.8 (212/219) | %100.0 (28/28) | %91.7 (55/60) |
| Grok Video 1.5 Lite | %95.4 (187/196) | %94.1 (16/17) | %90.6 (48/53) |
| Gemini Omni Flash 1.2 | %92.4 (182/197) | %88.9 (24/27) | %85.2 (46/54) |

## Puana girmeyen cevaplar ve klip sayıları

| Model | görünmüyor | hakem_yok | eylem olmadığı için geçersiz | Ölçülemeyen klip | Hakemin puanladığı klip | Tümü hakem_yok klip |
|---|---|---|---|---|---|---|
| Kling 3.0 | 1 | 19 | 0 | 1 | 19 | 1 |
| Wan 3.0 | 1 | 4 | 11 | 0 | 20 | 0 |
| Seedance 2.0 Mini | 3 | 6 | 8 | 0 | 20 | 0 |
| Grok Video 1.5 Lite | 0 | 48 | 12 | 2 | 18 | 2 |
| Gemini Omni Flash 1.2 | 5 | 7 | 3 | 0 | 18 | 0 |

Soru sayıları puanlı sorulardır. "Ölçülemeyen klip": puanlanabilir cevabı olmayan, üretilmiş klip. "Tümü hakem_yok": klibin bütün cevapları hakem_yok.

## Maliyet (Higgsfield kredisi)

Toplam kredi = klip başına teklif x (komut sayısı - iade edilen klip). Puanlanan kredi = klip başına teklif x hakemin puanladığı klip sayısı (tümü hakem_yok olan kliplerin kredisi çıkarılmış). Reddedilen klibin kredisi iade edildi. Kredi USD'ye çevrilmedi. İki "başına" sütunu ayrı sütunların payına bölünür; birleştirilmez.

| Model | Klip başına kredi | Toplam kredi | Komutu yapan cevap başına | Tutulan karakter cevabı başına | Puanlanan toplam kredi | Puanlanan kliplerde komutu yapan cevap başına | Puanlanan kliplerde tutulan karakter cevabı başına |
|---|---|---|---|---|---|---|---|
| Kling 3.0 | 7.5 | 150 | 7.14 | 0.59 | 142.5 | 6.79 | 0.56 |
| Wan 3.0 | 7.5 | 150 | 7.5 | 0.53 | 150 | 7.5 | 0.53 |
| Seedance 2.0 Mini | 5 | 100 | 4.76 | 0.34 | 100 | 4.76 | 0.34 |
| Grok Video 1.5 Lite | 5 | 100 | 5.56 | 0.4 | 90 | 5 | 0.36 |
| Gemini Omni Flash 1.2 | 11.25 | 202.5 | 10.66 | 0.81 | 202.5 | 10.66 | 0.81 |

## İnsan-hakem uyumu

Ana sayı: %80.2 (275/343 birim uyuştu). Eşik %85: geçmedi. İnsan 20 klibi puanladı.

Yan sayılar (eşikle karşılaştırılmaz):
- Tümü hakem_yok olan klipler çıkarılınca: %90.2 (275/305), çıkarılan klip 2.
- hakem_yok birimler çıkarılınca: %90.5 (275/304), çıkarılan birim 39.
- Net uyum (evet/hayır birimleri): %91.6 (297 birim).
- görünmüyor / hakem_yok çifti (gorunmuyor_hakem_yok_cift): 1.
- Tümü hakem_yok klipler (tumu_hakem_yok_klipler): K073, K091.

Karışıklık tablosu (satır: insan, sütun: hakem):
| İnsan \ Hakem | evet | hayir | gorunmuyor | hakem_yok |
|---|---|---|---|---|
| evet | 32 | 7 | 0 | 9 |
| hayir | 18 | 240 | 0 | 29 |
| gorunmuyor | 2 | 2 | 3 | 1 |

## Grafikler

- `grafik_yapti_tuttu.svg`: model başına komutu yaptı ve karakteri tuttu %.
- `grafik_maliyet.svg`: model başına kredi, komutu yapan ve karakteri tutan cevap başına.
- `grafik_dogruluk_maliyet.svg`: tek resimde, solda komutu yaptı % ve karakteri tuttu % (ayrı çubuklar, toplanmadı), sağda ayrı eksenle tutulan karakter cevabı başına kredi.

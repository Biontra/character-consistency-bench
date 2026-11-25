# TUTAR protokolü

## Sıra

1. Dondur: kurallar, komutlar, puan kodu, hakem talimatı ve gizli dosyaların parmak izi commit edilir ve `tutar-kurallar-v1` etiketiyle işaretlenir.
2. Üret: beş modelle 20 komutun videoları.
3. Hakem puanlar ve sonuç commit edilir.
4. İnsan 20 klibi puanlar.
5. Uyum hesaplanır.
6. Yayın.

## Aynı koşullar

Modeller: `kling3_0`, `wan3_0`, `seedance_2_0_mini`, `grok_video_v15_lite`, `gemini_omni_flash_1_2`.

- Süre 5 sn, 720p, 9:16
- Sessiz
- Başlangıç resmi verilir
- Tek deneme
- Komutların İngilizce çevirisi aynı metinle her modele verilir

## Dört cevap

Hakem her soru için şu dört değerden birini yazar, başka değer kabul edilmez:

- `evet`
- `hayir`
- `gorunmuyor` (soru bu klipte geçerli değil ya da görünmüyor)
- `hakem_yok` (hakem cevap veremedi)

Yalnız `evet` ve `hayir` puana girer.

## İki sütun kuralı

- "Komutu yaptı %": komutun yapılıp yapılmadığını soran sorulardan.
- "Karakteri tuttu %": karakter sorularından.
- İki sütun toplanmaz, tek sayıya çevrilmez.
- Bir klipte puanlanabilir cevap yoksa sonuç 0 değil, "ölçülemedi" olur.
- "Yaptı mı" cevabı beklenen değilse eyleme bağlı sorular paydadan çıkar. Ortak sorular sayılmaya devam eder.
- Bilinmeyen cevap değeri hata verir, sessizce sayılmaz. Eksik soru "hayır" sayılmaz, hata verir.

## İnsan kontrolü ve eşik

- 20 klip, tohum `20261125` ile kod tarafından seçilir.
- İnsan, hakemin cevabını görmeden puanlar.
- İnsan-hakem uyum eşiği: `0.85`.
- Uyum eşiğin altında çıkarsa sonuç olduğu gibi yayınlanır.

## Dondurma kontrol listesi

- [ ] Tüm testler geçti
- [ ] Sızıntı taraması temiz (git'te gizli dosya, resim, video yok)
- [ ] Komutlar ve modeller açık veri olarak commit edildi
- [ ] Gizli soru dosyasının parmak izi commit edildi
- [ ] Hakem talimatı commit edildi
- [ ] `tutar-kurallar-v1` etiketi konuldu

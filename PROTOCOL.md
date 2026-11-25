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

- [x] Tüm testler geçti
- [x] Sızıntı taraması temiz (git'te gizli dosya, resim, video yok)
- [x] Komutlar ve modeller açık veri olarak commit edildi
- [x] Gizli soru dosyasının parmak izi commit edildi
- [x] Hakem talimatı commit edildi
- [x] `tutar-kurallar-v1` etiketi konuldu

Dondurma tarihi: 25 Kasım 2026. Bu tarihte hiçbir video üretilmemişti.

## Üretim kaydı (ek, 25 Kasım 2026)

Bu bölüm dondurmadan SONRA yazıldı. Puan kurallarını, soruları, eşikleri ve yukarıdaki dondurulmuş metinleri değiştirmez. Yalnız üretimin nasıl kaydedileceğini anlatır.

### Kayıt düzeni

- Her model için bir dosya: `uretim_kaydi/<model_id>.jsonl`. Beş ajan aynı dosyaya yazmasın diye model başına ayrıdır.
- Her satır bir (model, komut) denemesidir. Aynı (model, komut) iki kez geçemez (tek deneme kuralı).
- Satır, klip üretildikten hemen sonra eklenir.
- Her alan her satırda bulunur. Bilinmeyen değer `null` yazılır.
- Doğrulama: `tutar/kayit.py`.

Alanlar, sırasıyla:

`model`, `komut` (1..20), `prompt`, `durum` (`tamam`, `uretim_hatasi`, `reddedildi`), `hata`, `is_kimligi`, `tarih_saat_utc`, `gonderilen_parametreler`, `baslangic_resmi_sha256`, `baslangic_medya_kimligi`, `dosya`, `sha256`, `sure_sn`, `kare_sayisi`, `genislik`, `yukseklik`, `fps`, `ses_var`, `kredi_teklif`, `kredi_kesinti`, `cozunurluk_parametresi`, `prompt_zenginlestirme` (`kapatildi`, `secenek_yok`, `kapatilamadi`), `sunucu_prompt`, `tohum`, `model_surumu`.

### Klip kökü

Klipler repo dışında durur (`/Volumes/Kye/character-consistency-bench`). `dosya` alanı bu köke göre göreli yazılır: `clips/<model_id>/cmdNN.mp4`, NN iki haneli. Mutlak yol yazılmaz.

### İlk klipten öğrenilenler (kling3_0, komut 1)

- Modelde çözünürlük parametresi ve prompt zenginleştirme parametresi yok. Bu yüzden `cozunurluk_parametresi` null, `prompt_zenginlestirme` `secenek_yok`.
- Çıktı 720x1280 geldi.
- Süre 5.04 sn (121 kare, 24 fps), yani 5 sn'den bir kare fazla. Kabul edilen süre aralığı 4.9-5.2 sn.
- Servisin prompt'u arka tarafta değiştirip değiştirmediği dışarıdan görülemiyor. Bu bir sınırdır. Servis prompt geri bildirirse `sunucu_prompt` alanına yazılır.

### Üretim hatası

Üretim hatası alan klip yeniden denenmez. Kayda `uretim_hatasi` (iş reddedilmişse `reddedildi`) yazılır ve sıradaki komuta geçilir.

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

## Üretimden sonra görülen sınırlar (26 Kasım 2026)

Bu bölüm videolar üretildikten sonra yazıldı. Donmuş kuralları değiştirmez; yalnız üretimde görülenleri kaydeder.

- **Sonuç.** 100 işten 98 klip çıktı. Gemini Omni komut 2 ve 7'yi güvenlik filtresiyle reddetti. Bu iki iş yeniden denenmedi, kredi iade edildi. Bu klipler nasıl puanlanır: aşağıdaki "Üretilemeyen klip kuralı" bölümüne bakın.
- **Ses.** Grok ve Gemini Omni'de sesi kapatma seçeneği yok. İkisi sesle üretti, ses sonradan ffmpeg ile silindi. Görüntü akışı yeniden kodlanmadı; md5 ile aynı olduğu ölçüldü. Ham dosyalar saklanıyor. Konuşma komutlarında (1, 2, 3) bu iki model sesle birlikte üretmenin yararını görmüş olabilir.
- **Wan.** `enable_thinking` kapatıldı. Diğer modellerde böyle bir ayar yok.
- **Kare hızı ve kare sayısı.** Modele göre değişiyor. Wan 30 fps, 150 kare. Kling, Seedance ve Grok 24 fps, 121 kare. Gemini Omni 24 fps, 120 kare. Hakeme giden kare sayısı eşit: klip başına 50 (saniyede 10).
- **Süre.** 5.0 ile 5.041667 sn arasında. Wan ve Gemini Omni 5.0, Kling, Seedance ve Grok 5.041667.
- **Kling çözünürlük.** Çözünürlük parametresi yok; çıktı yine 720x1280 ölçüldü.
- **Tek araç.** Her şey tek aracıdan (Higgsfield) geçti. Aracının komutu sunucu tarafında yeniden yazıp yazmadığı doğrulanamadı. Tohum ve model sürümü hiçbir yanıtta dönmedi.
- **Seedance ilk karesi.** İlk kare başlangıç resmiyle piksel olarak aynı değil. Ölçüm (gri, 720x1280, ilk kare ile resim arasında ortalama mutlak fark): Kling, Wan ve Grok yaklaşık 1.4-1.6; Gemini Omni yaklaşık 3.9-4.1; Seedance yaklaşık 8.5-10 (20 klipte 8.6-13.7). Fark kayma, ölçek, renk ya da bulanıklıktan gelmiyor; kare 0'dan itibaren var ve yüz, saç, giysi bölgesinde yoğun. Kompozisyon ve karakter tasarımı aynı, ince çizgiler yeniden çizilmiş. Resim beş modele de aynı rolle (`start_image`) ve aynı medya kimliğiyle gitti. Sebebin modelin kendisi mi aracı mı olduğu ayırt edilemedi. Sonuç: Seedance'in "karakteri tuttu" puanı bu notla okunmalı. Yeniden üretim yapılmadı.
- **Eşzamanlılık.** Eşzamanlılık sınırı yüzünden bazı gönderimler iş oluşmadan reddedildi ve yeniden gönderildi (iş oluşmadı, kredi kesilmedi). Oluşmuş hiçbir iş yeniden denenmedi: 100 ayrı iş kimliği.

## Üretilemeyen klip kuralı (26 Kasım 2026, videolardan sonra yazıldı)

Bu kural donmuş kurallarda yoktu; videolar üretildikten SONRA eklendi. Donmuş metinleri değiştirmez, yalnız üretilemeyen klibin nasıl puanlanacağını söyler. Etkilediği klipler: `gemini_omni_flash_1_2`, komut 2 ve 7 (güvenlik filtresi reddetti, klip yok). Kural, durumu `reddedildi` ya da `uretim_hatasi` olan her üretilemeyen klip için aynıdır; şu an `uretim_hatasi` olan satır yok.

Neden: model reddettiği için ne ödül ne haksız ceza alsın.

1. Sonuç tablosuna model başına "üretti: N/20" sütunu eklenir.
2. "Komutu yaptı" puanında üretilemeyen komut yapmadı sayılır: o komutun "yaptı mı" soruları (sütun `yapti`) paydaya girer, paya girmez.
3. "Karakteri tuttu" puanına üretilemeyen komut hiç girmez (ne paya ne paydaya), çünkü ortada bozulmuş bir karakter yok. Soru türü kırılımlarına (ortak, grup, özel) da girmez.
4. Bu kural videolar üretildikten sonra yazıldı. Gemini Omni'nin "komutu yaptı" puanı bu notla okunmalı.

Kod: `tutar/puan.py` içinde `uretilemeyen_klip` ve `model_ozeti`.

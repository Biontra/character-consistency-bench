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

Bu bölüm videolar üretildikten sonra yazıldı. Üretimde görülenleri kaydeder.

**Videolardan sonra neler değişti.** 25 Kasım'da dondurulan metne dokunulmadı; tek satır silinmedi. Ama videolardan sonra puan koduna ek yapıldı: üretilemeyen klip için hesap, ortak komutlar için hesap ve girdi denetimleri. Geçerli girdilerde eski hesap aynı sonucu veriyor: `tests/test_donmus_uyum.py`, `tests/donmus_puan_v1.py` içindeki dondurulmuş `tutar-kurallar-v1` puan koduyla güncel kodu sabit tohumlu (`20261126`) 600 rastgele geçerli girdide karşılaştırır ve çıktıların birebir eşit olmasını ister. Yeni girdi denetimleri şunları reddeder: tanınmayan soru sütunu, puanlı soruda tanınmayan ya da eksik tür; ortak hesapta aynı komutun iki kez verilmesi, ortak komutun eksik olması ya da ortak listedeki bir komutun klibinin üretilemedi işaretli olması. Donmuş "ölçülemedi" kuralına üretilemeyen klip için fiilen bir ayrım getirildi: üretilemeyen klip "ölçülemedi" sayılmıyor, "komutu yaptı"da yapmadı sayılıyor. Donmuş "sessiz" koşulu Grok ve Gemini Omni'de üretim sırasında sağlanamadı; ses üretimden sonra silindi. Bu, sessiz üretimle aynı şey değil. Aşağıdaki "Üretilemeyen klip kuralı" ve "Ortak komutlar satırı" bölümleri bu çerçevede okunmalı. Bir de zaman sırası: "Üretim kaydı (ek, 25 Kasım 2026)" bölümündeki kabul edilen süre aralığı (4.9-5.2 sn), donmuş "süre 5 sn" koşulunu bir aralığa çeviriyor ve ilk klip (kling3_0, komut 1) üretilip görüldükten sonra, kalan 99 işten önce yazıldı. Git geçmişinden kontrol edildi: aralığı ekleyen commit `dcecfe0`, 25 Kasım 2026 23:39:51 (+03:00), yani 20:39:51 UTC. Üretim kaydında kling3_0 komut 1'in `tarih_saat_utc` değeri 2026-11-25T20:30:06Z; diğer 99 işin en erkeni 20:42:09Z (gemini_omni_flash_1_2, komut 1). Yani sıra tutuyor: önce ilk klip, sonra aralık, sonra kalan işler. Sınır: `tarih_saat_utc` alanının gönderim ya da kayıt anı olduğu kayıttan ayırt edilemez; commit saati cümlenin yazılmış olabileceği en geç andır.

Soru türü dökümü (ortak, grup, özel) sorunun TÜRÜNE göre yapılır, sütununa göre değil. Bu yüzden "yaptı" sütununda olup türü özel olan 3 soru hem "komutu yaptı"ya hem "özel" dökümüne girer. Dökümün sütuna değil türe göre yapılması 25 Kasım'daki kodun davranışıdır ve bu hesap değişmedi. Üretilemeyen klipte hiçbir sorunun döküme girmemesi ise 26 Kasım'da eklenen üretilemeyen klip hesabının kararıdır (aşağıdaki "Üretilemeyen klip kuralı", üçüncü madde). "Yaptı" sütununda olup türü özel olan 3 soru 1, 15 ve 16 numaralı komutlardadır; üretilemeyen iki komutta (2 ve 7) bu sorulardan yok. Bu yüzden bu karar o 3 sorunun dökümünü etkilemedi.

Soru dosyasında puanı olmayan bilgi soruları da var (sütun `puansiz`): 2 adet. Hakem bunlara da cevap verir ama hiçbir puana ve döküme girmezler. İnsan-hakem uyum hesabı için `tutar/puan.py` içindeki `uyum(insan, hakem)` yalnız iki cevap sözlüğü alır ve verilen her anahtarı sayar; soru listesini görmez, sütuna bakmaz. Yani kod puansız soruları ne dışlar ne ayırt eder. Bugün depoda `uyum`u çağıran bir kod yok (yalnız testler çağırıyor). Uyum hesabına puansız soruların girip girmeyeceği açık kalan bir noktadır: bunu çağıranın verdiği anahtarlar belirler ve henüz karar verilmedi.

- **Sonuç.** 100 işten 98 klip çıktı. Gemini Omni komut 2 ve 7'yi güvenlik filtresiyle reddetti. Bu iki iş yeniden denenmedi, kredi iade edildi. Bu klipler nasıl puanlanır: aşağıdaki "Üretilemeyen klip kuralı" bölümüne bakın.
- **Ses.** Grok ve Gemini Omni'de sesi kapatma seçeneği yok. İkisi sesle üretti, ses sonradan ffmpeg ile silindi. Görüntü akışı yeniden kodlanmadı; md5 ile aynı olduğu ölçüldü. Ham dosyalar saklanıyor. Kayıttaki `sha256`, `ses_var` ve ölçümler SESİ SİLİNMİŞ dosyaya aittir. Ham (sesli) dosyaların sha256 değerleri `uretim_kaydi/grok_video_v15_lite.ham.json` ve `uretim_kaydi/gemini_omni_flash_1_2.ham.json` içindedir (Grok 20, Gemini Omni 18 klip; kayıttaki sha256 ile hiçbiri aynı değil). Konuşma komutlarında (1, 2, 3) bu iki modelin sesle üretmenin yararını görmüş olabileceği bir tahmindir; ölçülmedi.
- **Wan.** `enable_thinking` kapatıldı. Diğer modellerde böyle bir ayar yok.
- **Kare hızı ve kare sayısı.** Modele göre değişiyor. Wan 30 fps, 150 kare. Kling, Seedance ve Grok 24 fps, 121 kare. Gemini Omni 24 fps, 120 kare. Hakeme giden kare sayısı eşit: klip başına 50 (saniyede 10). 10 fps'e ffmpeg'in `fps=10` süzgeciyle inilir (`tutar/kareler.py`): süzgeç kareleri zaman damgasına göre seçer, kare üretmez ve karıştırmaz. Her tam kareye ek olarak üst ve alt yarı kırpmaları da çıkarılır: klip başına 50 tam + 50 üst + 50 alt.
- **Süre.** 5.0 ile 5.041667 sn arasında. Wan ve Gemini Omni 5.0, Kling, Seedance ve Grok 5.041667.
- **Kling çözünürlük.** Çözünürlük parametresi yok; çıktı yine 720x1280 ölçüldü.
- **Tek araç.** Her şey tek aracıdan (Higgsfield) geçti. Aracının komutu sunucu tarafında yeniden yazıp yazmadığı doğrulanamadı. Tohum ve model sürümü hiçbir yanıtta dönmedi.
- **Seedance ilk karesi.** İlk kare başlangıç resmiyle piksel olarak aynı değil. Ölçüm (gri, 720x1280, ilk kare ile resim arasında piksel başına ortalama mutlak fark, 0-255 ölçeği; en küçük-en büyük): Kling 1.43-1.48, Wan 1.50-1.50, Grok 1.44-1.47, Gemini Omni 3.46-4.05, Seedance 8.54-13.58. Klip başına değerler ve model başına en küçük, ortanca, en büyük `uretim_kaydi/ilk_kare_farki.json` içinde; betik `scripts/ilk_kare_farki.py`. Seedance farkı kayma, ölçek, renk ya da bulanıklıktan gelmiyor; kare 0'dan itibaren var ve yüz, saç, giysi bölgesinde yoğun. Genel kadraj ve sahne düzeni korunuyor, ama yüz, saç ve giysi çizgileri kare 0'dan itibaren başlangıç resminden sapıyor. Bunun karakter puanını etkileyip etkilemediğini hakem ölçecek. Resim beş modele de aynı rolle (`start_image`) ve aynı medya kimliğiyle gitti. Sebebin modelin kendisi mi aracı mı olduğu ayırt edilemedi. Sonuç: Seedance'in "karakteri tuttu" puanı bu notla okunmalı. Yeniden üretim yapılmadı.
- **Komut zenginleştirme ve çözünürlük parametresi.** Değerler `uretim_kaydi/*.jsonl` dosyalarındaki `prompt_zenginlestirme`, `cozunurluk_parametresi` ve `sunucu_prompt` alanlarından çıkarıldı (her modelde 20 satır).

  | Model | prompt_zenginlestirme | cozunurluk_parametresi | sunucu_prompt dolu / boş |
  |---|---|---|---|
  | kling3_0 | secenek_yok (20) | null (20) | 19 / 1 |
  | wan3_0 | kapatildi (20) | 720p (20) | 0 / 20 |
  | seedance_2_0_mini | secenek_yok (20) | 720p (20) | 20 / 0 |
  | grok_video_v15_lite | secenek_yok (20) | 720p (20) | 20 / 0 |
  | gemini_omni_flash_1_2 | secenek_yok (20) | 720p (20) | 20 / 0 |

  Dolu `sunucu_prompt` satırlarının hepsinde metin gönderilen prompt ile aynı. Bu, sunucunun komutu yeniden yazmadığını kanıtlamaz; yalnız araç yanıtında farklı bir metin dönmediğini gösterir.
- **İnsan kontrolü klipleri.** `data/insan_secimi.json` içindeki 20 klip, üretilemeyen iki klibe (Gemini Omni komut 2 ve 7) denk gelmedi. Seçim üretimden önce yapıldı: dosya 25 Kasım 2026 11:58'de commit edildi, kayıttaki en eski zaman damgası aynı gün 20:30 UTC. Seçim `tutar/secim.py` ile yapılır: 20 komut tohumla karıştırılır ve modellere 4'er dağıtılır; her komut dosyada tam bir kez geçer. Yani seçim 100 çiftten serbest çekilmedi, 20 komutun beşe bölünmesidir. Hangi klibin üretilemeyeceği seçim sırasında bilinmiyordu.
- **Kredi.** Hesap düzeyi sayılar (968 başlangıç, 265.5 son bakiye, 100 kesinti, 2 iade) üretim kaydından değil hesap ekranından okundu. Bu sayılar hesap ekranından okundu; depodaki kayıtlardan yeniden üretilemez. Ayrıntı `uretim_kaydi/kredi_ozeti.md` içinde.
- **Eşzamanlılık.** Eşzamanlılık sınırı yüzünden bazı gönderimler iş oluşmadan reddedildi ve yeniden gönderildi (iş oluşmadı, kredi kesilmedi). Oluşmuş hiçbir iş yeniden denenmedi: 100 ayrı iş kimliği. Eşzamanlılık nedeniyle reddedilen gönderimlerin üretim kaydında izi yok; bu bilgi üretim sırasındaki çalışma notlarına dayanıyor ve kayıttan doğrulanamaz. Kayıttan doğrulanan tek şey 100 satırın 100 ayrı iş kimliği taşımasıdır.

## Üretilemeyen klip kuralı (26 Kasım 2026, videolardan sonra yazıldı)

Bu kural donmuş kurallarda yoktu; videolar üretildikten SONRA eklendi ("Videolardan sonra neler değişti" paragrafına bakın). Üretilemeyen klibin nasıl puanlanacağını söyler. Etkilediği klipler: `gemini_omni_flash_1_2`, komut 2 ve 7 (güvenlik filtresi reddetti, klip yok). Kural, durumu `reddedildi` ya da `uretim_hatasi` olan her üretilemeyen klip için aynıdır; şu an `uretim_hatasi` olan satır yok.

Neden: model reddettiği için ne ödül ne haksız ceza alsın.

1. Sonuç tablosuna model başına "üretti: N/20" sütunu eklenir.
2. "Komutu yaptı" puanında üretilemeyen komut yapmadı sayılır: o komutun "yaptı mı" soruları (sütun `yapti`) paydaya girer, paya girmez.
3. "Karakteri tuttu" puanına üretilemeyen komut hiç girmez (ne paya ne paydaya), çünkü ortada bozulmuş bir karakter yok. Soru türü kırılımlarına (ortak, grup, özel) da girmez.
4. Bu kural videolar üretildikten sonra yazıldı. Gemini Omni'nin hem "komutu yaptı" hem "karakteri tuttu" puanı bu notla okunmalı. "Yaptı" puanında iki komut yapmadı sayılır. "Tuttu" puanında ise model zor olabilecek iki komutu üretmediği için o komutlarda karakter bozulması riskini taşımadı, diğer dört model taşıdı (seçilim etkisi). Bu yüzden Gemini Omni'nin "tuttu" puanı diğer dört modelle birebir kıyaslanamaz (bunun için ortak komutlar satırı eklendi, aşağıdaki bölüme bakın).

Kod: `tutar/puan.py` içinde `uretilemeyen_klip` ve `model_ozeti`.

## Ortak komutlar satırı (26 Kasım 2026, videolardan sonra yazıldı)

Bu ek de videolar üretildikten SONRA yazıldı; proje sahibi 26 Kasım 2026'da onayladı. Yukarıdaki "Üretilemeyen klip kuralı"nın dört maddesini değiştirmez ve donmuş metne dokunmaz; yalnız bir satır ekler ("Videolardan sonra neler değişti" paragrafına bakın).

Neden: Gemini Omni zor olabilecek iki komutu (2 ve 7) üretmedi, diğer modeller üretti (seçilim etkisi). Modeller aynı komut kümesinde de karşılaştırılmalı.

"Karakteri tuttu" puanı sonuç tablosunda iki biçimde gösterilir:

- (a) Modelin ürettiği bütün klipler üzerinden. Mevcut hesaptır, değişmez.
- (b) Beş modelin HEPSİNİN ürettiği ortak komutlar üzerinden. Şu an ortak küme 18 komuttur (2 ve 7 hariç).

Sınırlar:

- Yalnız "karakteri tuttu" puanı için geçerlidir. "Komutu yaptı" puanı ve soru türü kırılımı için ortak satır yoktur.
- Üretilemeyen klip kuralının dört maddesi aynen geçerlidir.

Kod: `tutar/puan.py` içinde `ortak_komutlar` ve `ortak_tuttu` (`ortak_tuttu`, `model_puanla` ile havuzlar).

## Hakem çalıştırma kuralları (26 Kasım 2026, hakem çalışmadan önce yazıldı)

Bu bölüm hakem çalışmadan ÖNCE yazıldı ve commit edildi. Bu tarihte hiçbir klip hakeme gösterilmedi. Yukarıdaki metinlere dokunmaz, onaylanmış kuralların anlamını değiştirmez; yalnız hakemin nasıl çalıştırılacağını anlatır.

1. **Hakem.** Hakem Claude Sonnet'tir ve Claude Code içinde alt ajan olarak çalışır. Model kimliği ve tarih her cevap satırına yazılır. Sıcaklık bu ortamda ayarlanamıyor; bu bir sınırdır. Hakemle aynı aileden bir model benchmark'ta yok (beş video modeli başka şirketlerin), ve hakem video üretmedi.
2. **Körlük.** Hakem hangi modelin klibine baktığını bilmez. Klipler sabit tohumla (`20261126`) karıştırılır ve K001..K098 diye adlandırılır. Eşleme dosyası gizli kalır. Hakeme model adı, başka kliplerin cevapları ve beklenen cevaplar verilmez. Kare klasörlerinin ve dosyalarının adında model adı ve komut numarası geçmez.
3. **Hakemin gördüğü.** Komutun İngilizce metni, o komutun soruları (kimlik ve soru metni; puansız bilgi soruları dahil) ve klibin 50 tam karesi, sırayla. Hakem 50 tam karenin hepsini açmak zorundadır. Üst ve alt yarı kırpmaları aynı piksellerin kesilmiş halidir; hakem isterse açar, zorunlu değildir. Başlangıç resmi hakeme gösterilmez. "Baştaki haliyle karşılaştır" gereken sorularda hakem klibin ilk karesini ölçü alır (`judge/judge_prompt_v1.txt` böyle söylüyor). Seedance'in ilk karesinin resimden saptığı yukarıdaki "Seedance ilk karesi" maddesinde yazılı.
4. **Çağrı birimi.** Klip başına tek hakem çalıştırması; bütün sorular birlikte cevaplanır. Kullanılan metin `judge/judge_prompt_v1.txt`'tir ve `tutar-kurallar-v1` etiketinden beri değişmedi (`git diff tutar-kurallar-v1 -- judge/judge_prompt_v1.txt` boş). Bu dosyanın parmak izi `data/fingerprints.json` içinde yoktur; değişmediğinin kanıtı etiket ve git geçmişidir. Hakeme ayrıca yalnız "kareler şu klasörde, hepsini sırayla oku, cevabı şu biçimde ver" diyen teknik talimat verilir. Tam metni `judge/hakem_talimati_v1.txt` içindedir ve parmak izi `data/fingerprints.json` içine eklendi.
5. **Geçerlilik.** Hakemin çıktısı kodla denetlenir (`tutar/hakem.py`, `cikti_dogrula`): soru kimlikleri o komutun sorularıyla birebir aynı olmalı, cevap dört değerden biri olmalı, kare numarası 1-50 ya da boş olmalı. Geçersizse aynı klip YENİ bir hakemle bir kez daha çalıştırılır. O da geçersizse o klibin bütün cevapları `hakem_yok` yazılır. Geçerli bir çıktı ASLA yeniden çalıştırılmaz; beğenilmeyen cevap için tekrar yoktur. Her klibin kaçıncı çalıştırmada geçtiği kaydedilir.
6. **Deneme.** Önce 5 klip (K001-K005) çalıştırılır. Amaç yalnız düzeneğin çalıştığını görmektir: kareler okunuyor mu, çıktı geçerli mi. Bu 5 klibin geçerli cevapları SON cevaptır ve yeniden çalıştırılmaz. Denemeden sonra bu kurallar değişirse değişiklik ve nedeni buraya yazılır.
7. **Kayıt.** Herkese açık `results/judge_raw.jsonl` dosyasında satır başına bir cevap bulunur: klip kodu, model, komut, soru kimliği, cevap, kare, hakem modeli, çalıştırma numarası, tarih. Soru metni ve hakemin gerekçesi bu dosyaya girmez; gerekçeli ham çıktılar gizli veri setinde kalır. Bu dosya insan puanlamasından ÖNCE commit edilir.
8. **Üretilemeyen klipler.** Üretilemeyen iki klip (Gemini Omni komut 2 ve 7) hakeme gitmez, çünkü klip yok. Hakeme 98 klip gider.

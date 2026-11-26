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
- **Hakemin gördüğü ilk kare (26 Kasım 2026, hakemden önce eklendi).** `fps=10` süzgeci yüzünden `tam/001.png` klibin ham 0. karesi değil, ham 1. karesidir (yaklaşık 42 ms sonrası). Kling ve Wan'da `ffmpeg -f framemd5` ile ham kare 1 ile `001.png` aynı çıktı. Son kare de kayar: `050.png`, 24 fps kliplerde ham kare 118, Wan'da (30 fps) ham kare 148. Bu kayma bütün modellerde aynı kuraldan çıkar, bir modeli ayrıca etkilemez. Kareler yeniden çıkarılmadı ve kod değiştirilmedi. Hakemin "ilk kare" dediği şey bu yüzden klibin ikinci ham karesidir. Yukarıdaki ilk kare farkı ölçümü ham 0. kareyle yapıldı; hakemin gördüğü kareyle farkı ayrıca ölçülmedi.

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

## Hakem kurallarına ekler (26 Kasım 2026, hakem çalışmadan önce, iki bağımsız okumadan sonra)

Bu ek de hakem çalışmadan ÖNCE yazıldı. Hiçbir klip hakeme gösterilmedi. Yukarıdaki "Hakem çalıştırma kuralları"nı silmez; yalnız onlara ekler ve bir cümlesini düzeltir.

1. **Düzeltme.** Yukarıdaki "komut numarası geçmez" cümlesi yalnız klasör ve dosya adları için doğrudur. Soru kimlikleri komut numarasını içerir ve hakem bunu görür. Komut numarası modeli ele vermez: her model aynı komutları aldı.
2. **Metin dosyasının yeri ve körlüğün dayanağı.** Hakemin metin dosyası artık kare klasörünün içindedir (`hakem_girdi/Kxxx/sorular.txt`), deponun ve eşleme dosyasının dışında. Yine de körlük teknik bir duvarla değil talimatla korunur: alt ajanın dosya okuma aracı vardır. Bu yüzden her hakem çalıştırmasının araç kaydı sonradan taranır. Verilen klasör dışında dosya okuyan ya da 50 tam karenin hepsini açmayan çalıştırma GEÇERSİZ sayılır (çıktısı biçimce doğru olsa bile) ve bir geçersiz deneme olarak günlüğe yazılır.
3. **Kayıt kodla tutulur.** `scripts/hakem_kaydet.py` geçerli kaydı olan klibi yeniden kaydetmez, klip başına en çok iki denemeye izin verir, ikinci geçersizde `hakem_yok` yazar ve her denemeyi günlüğe ekler. Hakemi başlatan şey kod değil, Claude Code içindeki ekip lideridir (alt ajan başlatma kodla yapılamıyor). Bu bir sınırdır: araç kaydının taranması da lider tarafından yapılır.
4. **Çıktı doğrulamasına eklenen.** Her cevapta boş olmayan bir gerekçe (`gerekce`, metin) şarttır. Kare kuralı aynıdır: 1-50 tam sayı ya da boş.
5. **Deneme kuralının daraltılması.** 5 kliplik denemeden sonra hakem metni, talimat ve doğrulama kuralları DEĞİŞTİRİLEMEZ. Düzenek bu metinler değişmeden çalışmıyorsa metin düzeltilir, yeni sürüm numarası alır ve 98 klibin HEPSİ yeni sürümle baştan çalıştırılır. Eski deneme cevapları silinmez; "atıldı" diye ayrı yayımlanır. Deneme ile kalan klipler arasında eşlemeye ve puanlara bakılmaz.
6. **Ham cevapların saklanması.** Ham cevaplar hakemler bitene kadar deponun dışında ya da gizli tutulur (`secret/hakem/`). `results/judge_raw.jsonl` ancak 98 klip tamamlanınca üretilir (`scripts/hakem_kaydet.py topla`), çünkü içinde kod-model eşlemesi vardır.

### Hakemle ilgili bilinen sınırlar

- (a) Hakem başlangıç resmini görmez, klibin ilk karesini ölçü alır. Karakteri daha ilk karede değiştirip sonra sabit tutan model bu yüzden "karakteri tuttu" sütununda cezalandırılmaz. İlk kare farkı tablosu (`uretim_kaydi/ilk_kare_farki.json`) bu yüzden sonuçla yan yana okunmalıdır.
- (b) `gorunmuyor` ve `hakem_yok` paydaya girmez. Bulanık ya da kararsız görüntü üreten model bundan yarar görebilir. Sonuç tablosunda model başına bu iki cevabın sayısı ayrıca verilecektir.
- (c) Tek çalıştırma: hakemin aynı klipte ikinci kez aynı cevabı verip vermeyeceği ölçülmedi.
- (d) Bir klibin bütün soruları tek seferde cevaplanır. Bir cevabın diğerini etkilemesi engellenemez.
- (e) Üst ve alt kırpmalara bakmak isteğe bağlıdır. Klipler arasında bakma derinliği eşit olmayabilir.
- (f) 50 kare birkaç parçada okunur. İlk karelerin ayrıntısı sonlara doğru zayıflayabilir.
- (g) Saniyede 10 kare: iki kare arasındaki (yaklaşık 0,1 sn) kısa bozulmalar kaçabilir. 24 fps kliplerde kareler arası adım eşit değildir (2-3 kare), 30 fps klipte eşittir (3 kare).
- (h) Dosya adlarında ipucu yok ama görüntünün kendisi modeli ele verebilir (çizim farkı, hareket akıcılığı). PNG dosyalarının metin içermeyen yardımcı parçaları iki modelde farklıdır.
- (i) 20 klibi puanlayacak insan bu projenin sahibidir: videoları o üretti, bu belgedeki sınırları biliyor. Model adını görmeden puanlar ama tam kör sayılmaz.

## Hakem kurallarında çelişki giderme ve ek sınırlar (26 Kasım 2026, hakem çalışmadan önce)

Bu bölüm de hakem çalışmadan ÖNCE yazıldı. Hiçbir klip hakeme gösterilmedi. Yukarıdaki iki hakem bölümündeki hiçbir satırı değiştirmez; yalnız çelişkileri giderir ve bilinen sınırları ekler.

1. **Öncelik.** "Hakem çalıştırma kuralları" ile "Hakem kurallarına ekler" çelişirse EKLER ve bu bölüm geçerlidir.
2. **Deneme kuralı.** İlk bölümdeki "Denemeden sonra bu kurallar değişirse değişiklik ve nedeni buraya yazılır." cümlesi artık yalnız şu anlama gelir: denemeden sonra metin, talimat ya da doğrulama değişmek zorunda kalırsa yeni sürüm alınır, nedeni buraya yazılır ve 98 klibin hepsi baştan çalıştırılır. Not düşüp yalnız kalan klipleri yeni kuralla çalıştırmak YASAKTIR.
3. **Kare alanı.** Donmuş hakem metni (`judge/judge_prompt_v1.txt`) örnekte kare numarasını tırnak içinde gösterir; talimat tam sayı ister. Hakem ikisini de görür. Geçerli sayılanlar: 1-50 arası tam sayı, aynı sayının metin hali (örn. "7") ve boş/null. Başka her şey geçersizdir. Donmuş metin bu yüzden değiştirilmedi.
4. **Metin dosyasının yeri.** Hakemin metin dosyası `hakem_girdi/Kxxx/sorular.txt` içindedir (ilk bölüm yeri söylemiyordu).
5. **Sınır, klasör yapısı.** Hakemin klasöründen üst dizine çıkılırsa öteki 97 klibin klasörleri, iki üst dizinde de model adlarıyla ayrılmış özgün kare klasörü (`frames/`) görünür. Teknik duvar yoktur; yalnız talimat yasaklar ve her çalıştırmanın araç kaydı sonradan taranır.
6. **Sınır, kayıt.** Kayıt betiği yalnız kendisine bildirilen denemeleri sayar. Lider betiği çağırmadan hakemi yeniden çalıştırırsa, çıktı dosyasını kendisi yazarsa ya da günlük ile ham dosyayı birlikte silerse kod bunu göremez. "En çok iki deneme" ve "geçerli çıktı yeniden çalıştırılmaz" kuralları bu yüzden kısmen lidere güvene dayanır. Buna karşı tutulan iz: her hakem alt ajanının oturum kaydı saklanır ve başlatılan hakem sayısı ile günlükteki deneme sayısı sonuçla birlikte yayımlanır; ikisi tutmazsa fark açıklanır.
7. **Öncelik, tam hali.** Üç hakem bölümü birbiriyle çelişirse sırayla en sonda yazılan geçerlidir: önce bu bölüm, sonra "Hakem kurallarına ekler", en son "Hakem çalıştırma kuralları". Bu bölümün girişindeki "hiçbir satırı değiştirmez" sözü, eski satırların silinmediği anlamına gelir; çeliştikleri yerde eski satırlar geçersizdir.
8. **Kare kuralı, tek hali.** "Hakem kurallarına ekler" madde 4'teki "Kare kuralı aynıdır: 1-50 tam sayı ya da boş." cümlesi yerine madde 3 geçerlidir. Metin halinde yalnız rakamlardan oluşan ve 1-50 arasında bir sayıya denk gelen yazım geçerlidir; başında sıfır olabilir (örn. "07"). Boşluk, nokta, aralık ya da başka işaret içeren yazım geçersizdir. Kod (`tutar/hakem.py`) böyle davranır.
9. **Deneme cevapları.** "Bu 5 klibin geçerli cevapları SON cevaptır" cümlesi yalnız kurallar değişmediği sürece doğrudur. Madde 2'deki durumda (yeni sürüm, 98 klip baştan) bu 5 klibin eski cevapları da atılır ve "atıldı" diye ayrı yayımlanır.

## Hakem kayıt sırası (26 Kasım 2026, hakem çalışmadan önce)

Bu bölüm de hakem çalışmadan ÖNCE yazıldı. Hiçbir klip hakeme gösterilmedi. Yukarıdaki hiçbir satırı silmez ya da değiştirmez; yalnız ekler. Çeliştiği yerde bu bölüm geçerlidir.

1. **Sıra.** Her klip için sıra şudur: (a) hakem alt ajanı çalışır ve cevabını `hakem_cikti/Kxxx.json` dosyasına yazar (bu klasör kare klasörünün yanındadır, deponun dışındadır); (b) o çalıştırmanın araç kaydı taranır: verilen klasör dışında dosya okudu mu, 50 tam karenin hepsini açtı mı; (c) ANCAK bundan sonra kayıt betiği çağrılır ve tarama sonucu betiğe bildirilir (`--tarama-temiz` ya da `--tarama-gecersiz "NEDEN"`). Betik tarama sonucu verilmeden kayıt yapmaz. Tarama geçersizse deneme geçersiz sayılır, günlüğe nedeni yazılır ve ham cevap yazılmaz. Böylece "Geçerli bir çıktı ASLA yeniden çalıştırılmaz" kuralı ile tarama çelişmez: bir çıktı ancak tarama temizse geçerli olur. Geçersiz tarama da bir denemedir: ilk denemeyse klip bir kez daha çalıştırılabilir, ikinci denemeyse klibin cevapları `hakem_yok` yazılır.
2. **Taramayı kim yapar.** Taramayı hakemi başlatan ajan yapmaz; ayrı bir denetçi ajan yapar ve neye baktığını yazar. "Hakem kurallarına ekler" madde 3'teki "araç kaydının taranması da lider tarafından yapılır" cümlesi yerine bu madde geçerlidir. Taramanın kendisi kodla değil, araç kaydını okuyarak yapılır; bu bir sınırdır. Kod yalnız kendisine bildirilen sonucu kaydeder ve taramanın gerçekten yapılıp yapılmadığını göremez.
3. **Ham cevapların yeri, tek hali.** Hakemin yazdığı dosya `hakem_cikti/` içindedir (deponun dışında). Kayıt betiğinin sakladığı kopya, günlük ve ham satırlar `secret/hakem/<sürüm>/` altındadır (deponun içinde ama git dışında). İkisi de 98 klip bitene kadar yayımlanmaz. "Hakem kurallarına ekler" madde 6'daki "deponun dışında ya da gizli tutulur" sözü bu ikisini anlatır.
4. **Sürüm ve deneme sayacı.** Kayıtlar sürüm klasöründe tutulur (ilk sürüm `v1`): `secret/hakem/v1/gunluk.jsonl`, `secret/hakem/v1/ham/`, `secret/hakem/v1/cikti/`. Eşleme dosyası `secret/hakem/esleme.json` yerinde kalır. "En çok iki deneme" ve "geçerli kayıt yeniden yazılmaz" kuralları sürüm başınadır. Kurallar deneme sonrası değişip 98 klip baştan çalıştırılırsa yeni sürüm klasörü açılır (`--surum v2`), sayaç sıfırdan başlar, eski sürümün dosyaları silinmez. Günlük satırlarında ve ham satırlarda `surum` alanı vardır; günlükte ayrıca `tarama` ("temiz" ya da "gecersiz") ve tarama geçersizse `tarama_hatasi` yazılır.
5. **Kare alanı hiç yazılmamışsa.** Hakem bir cevapta `kare` alanını hiç yazmazsa cevap, boş kare gibi geçerli sayılır (kod böyle davranır; bir test bunu sabitler). Kare alanı yazılmışsa "Hakem kurallarında çelişki giderme ve ek sınırlar" bölümünün madde 8'i geçerlidir.

## Uyum hesabının kapsamı (26 Kasım 2026, hakem çalışmadan önce)

Bu bölüm hakem hiç çalışmadan önce yazıldı. Yalnız ekleme yapılır; yukarıdaki hiçbir satır değiştirilmedi ya da silinmedi.

1. **Karar.** Proje sahibi 26 Kasım 2026'da şu soruyu cevapladı. Soru: "İki puansız soru, insan-hakem uyum hesabına girsin mi?" Cevap: "Hayır, girmesin." Buna göre insan-hakem uyumu (`uyum`) yalnız PUANLI sorular üzerinden hesaplanır. Puansız iki soru (komut 13 ve 18'deki bilgi soruları) uyum hesabına girmez. Hakem bu soruları yine cevaplar ve cevapları ham kayıtta yer alır. Bu madde, yukarıdaki "Uyum hesabına puansız soruların girip girmeyeceği açık kalan bir noktadır: bunu çağıranın verdiği anahtarlar belirler ve henüz karar verilmedi" cümlesini (soru dosyasındaki puansız sorulardan söz eden paragraf) kapatır. Eski satır silinmedi; bu madde onun yerine geçer.
2. **Geçersiz denemede ne yazılır.** Geçersiz sayılan bir hakem denemesinde (tarama geçersiz ya da çıktı doğrulamadan geçmedi) `ham/` altına cevap satırı yazılmaz. Ama o denemenin çıktı dosyası okunabildiyse bir kopyası denetim izi olarak `secret/hakem/<sürüm>/cikti/Kxxx.calistirmaN.json` adıyla saklanır (`tutar/hakem_kayit.py` böyle yapar; geçerli denemelerin kopyası da aynı yere yazılır). Önceki "ham cevap yazılmaz" ifadesi `ham/` altındaki cevap satırlarını kasteder. Tek ayrıntı: bir klibin ikinci denemesi de geçersiz olursa kod `ham/` altına her soru için `hakem_yok` satırı yazar; bu satırlar hakemin cevabı değildir, yukarıdaki "ikinci denemeyse klibin cevapları `hakem_yok` yazılır" kuralının uygulamasıdır.
3. **`surum` alanı.** `results/judge_raw.jsonl` satırlarında yukarıda sayılan alanlara (klip, model, komut, soru, cevap, kare, hakem modeli, çalıştırma numarası, tarih) ek olarak `surum` alanı da vardır (ör. "v1"). Kayıt betiği bu alanı her ham satıra ekler.
4. **Bu bölüm yazılırken durum.** Hakem hiç çalışmamıştır: `secret/hakem/` altında yalnız eşleme dosyası (`esleme.json`) vardır ve hakem çıktı klasörü (`hakem_cikti`) boştur.
5. **Karar.** Proje sahibi 26 Kasım 2026'da şu soruyu cevapladı. Soru: "Hakem 'görünmüyor' derse, uyum hesabında bu bir cevap sayılsın mı?" Cevap: "Evet, cevap sayılsın." Buna göre uyum, ham cevaplar karşılaştırılarak hesaplanır: insanın puanladığı kliplerdeki her puanlı soru bir birimdir; insanın cevabı ile hakemin cevabı aynıysa uyuşma, farklıysa uyuşmazlık sayılır. `gorunmuyor` da bir cevaptır: biri `gorunmuyor` diğeri `evet` ya da `hayir` dediyse uyuşmazlıktır; ikisi de `gorunmuyor` dediyse uyuşmadır. Hiçbir birim paydadan çıkarılmaz. `uyum` = uyuşan birim sayısı / tüm birim sayısı. Bu madde, yukarıdaki "Yalnız `evet` ve `hayir` puana girer." ve "`gorunmuyor` ve `hakem_yok` paydaya girmez" cümlelerinin uyum hesabı için geçerli olmasını engeller; bu iki cümle yalnız puan içindir. Eski satırlar silinmedi.
6. **`hakem_yok`.** Hakemin bir klipte cevabı `hakem_yok` ise o birimler uyuşmazlık sayılır ve paydada kalır. Bu madde proje sahibinin sözü değildir; madde 5'in mantığını izleyen yürütücü (Claude) ekidir ve proje sahibine 26 Kasım 2026'da bildirilmiştir.
7. **Yan sayı.** Ana sayı madde 5'teki `uyum`dur ve yukarıdaki "İnsan kontrolü ve eşik" bölümünde yazılan `0.85` eşiği bununla karşılaştırılır. Bilgi için ayrıca şu da yayımlanır: yalnız iki tarafın da `evet` ya da `hayir` dediği birimlerdeki uyuşma oranı ve bu birimlerin sayısı. Bu yan sayı eşikle karşılaştırılmaz.
8. Puan hesabı bu maddelerden etkilenmez: `gorunmuyor` ve `hakem_yok` puan paydasına girmez kuralı (yukarıda yazılan) aynen geçerlidir; bu bölüm yalnız insan-hakem uyumunu tanımlar.

## Uyum ve kayıt kurallarına ekler (26 Kasım 2026, hakem çalışmadan önce)

Bu bölüm hakem hiç çalışmadan önce yazıldı. Yalnız ekleme yapılır; yukarıdaki hiçbir satır silinmedi ya da değiştirilmedi. Önceki bölümlerle çeliştiği yerde bu bölüm geçerlidir. Her madde yazılmadan önce kodla ya da dosyayla denendi.

1. **Uyum paydası.** "Uyum hesabının kapsamı" madde 5'teki "Hiçbir birim paydadan çıkarılmaz" cümlesi eyleme bağlı soruları da kapsar. "İki sütun kuralı" bölümündeki şu cümle aynen: "Yaptı mı" cevabı beklenen değilse eyleme bağlı sorular paydadan çıkar. Ortak sorular sayılmaya devam eder. Bu cümle yalnız puan hesabı içindir. Uyumda eyleme bağlı sorular da paydada kalır.
2. **İnsan cevapları.** İnsan yalnız `evet`, `hayir`, `gorunmuyor` cevaplarını kullanır. `hakem_yok` insan cevabı olamaz; kod bunu ve başka her değeri reddeder (`ValueError`). "Uyum hesabının kapsamı" madde 6'daki `hakem_yok` kuralı soru (birim) düzeyindedir: hakemin cevabı `hakem_yok` olan her birim uyuşmazlıktır ve paydada kalır.
3. **Hesap kodu.** Uyum `tutar/uyum_hesap.py` içindeki `uyum_raporu(insan, hakem, sorular)` ile hesaplanır. Puansız soruları kod kendisi dışlar ve kaç birimin dışlandığını döndürür. İnsanın puanladığı bir klipte puanlı bir soru insanda ya da hakemde eksikse kod hata verir. Bu kod hakem çalışmadan önce commit edilmiştir (`57f9bfa`). `tutar/puan.py` içindeki eski `uyum` fonksiyonu değişmedi; resmi sayı yeni fonksiyondan gelir. Madde 7'deki yan sayı da aynı fonksiyondan gelir.
4. **İnsan neye bakar.** Bu madde yürütücünün (Claude) seçimidir ve proje sahibine bildirilecektir; proje sahibinin sözü değildir. İnsan, hakeme verilen AYNI 50 tam kareye bakar (aynı klip kodunun klasörü), aynı soru metinlerini görür. Klipler K kodlarıyla gösterilir, model adı gösterilmez. Puanlama aracı hakemin cevaplarını göstermez. Hangi 20 klibin puanlanacağı daha önce yazılmıştır: "İnsan kontrolü ve eşik" bölümü (tohum `20261125`) ve "Üretimden sonra görülen sınırlar" bölümündeki "İnsan kontrolü klipleri" maddesi; liste `data/insan_secimi.json` içindedir. Bu bölüm o seçimi değiştirmez.
5. **Sınır, körlük.** İnsan puanlaması hakem cevapları commit edildikten sonra yapılır ve puanlayan kişi projenin sahibidir. Hakemin cevaplarına bakmadığı teknik olarak kanıtlanamaz. Araç cevapları göstermez, ama bu kanıt değildir. "İnsan kontrolü ve eşik" bölümündeki "hakemin cevabını görmeden puanlar" sözü bu sınırla okunmalıdır.
6. **Tarama ölçütü (tek anlamlı liste).** Bir hakem denemesi araç kaydı taramasında YALNIZ şu durumlarda geçersiz sayılır: (a) kendi klip klasörü ve talimatta verilen metin dosyası dışında herhangi bir dosya ya da klasörü okudu, listeledi ya da aradı; (b) web'e baktı ya da komut çalıştırdı; (c) çıktı dosyası dışında bir dosya yazdı ya da değiştirdi; (d) 50 tam karenin hepsini açmadı. Şunlar geçersiz SAYILMAZ, yalnız denetçi raporuna not düşülür: bir mesajda 10'dan fazla kare okumak; kendi klip klasörünün içini listelemek; kırpılmış karelere bakmak ya da bakmamak. Çelişki: `judge/hakem_talimati_v1.txt` şunları söyler (aynen): Üst klasöre, başka K klasörlerine, depoya, "frames", "secret" ya da "clips" adlı hiçbir yere bakma. Dosya listeleme ya da arama yapma. Ayrıca: bir mesajda en çok 10 kare. Hakeme bu yasaklar söylenir, ama taramada geçersizlik sebebi olarak yalnız bu maddenin listesi sayılır: kendi klasörünü listelemek ve bir mesajda 10'dan fazla kare okumak talimata aykırı olsa da denemeyi geçersiz yapmaz. Bu madde onun yerine geçer. Talimat dosyası değiştirilmedi.
7. **Bayat çıktı.** Geçersiz bir denemeden sonra, ikinci deneme başlamadan önce `hakem_cikti/Kxxx.json` silinir. Silmeden önce kayıt betiği çağrılmış olmalıdır: betik çıktı dosyasını okuyabildiyse bir kopyasını gizli klasörde saklar (`secret/hakem/<sürüm>/cikti/Kxxx.calistirmaN.json`). Ayrıca kayıt kodu (`tutar/hakem_kayit.py`), aynı klibin aynı sürümdeki önceki bir denemesiyle birebir aynı içerikli (sha256 aynı) çıktıyı kural reddi olarak reddeder: çıkış kodu 2, hiçbir şey yazılmaz, deneme sayılmaz. Önceki deneme tarama nedeniyle geçersiz sayılmış olsa da bu kural geçerlidir. Çıktı dosyası hiç okunamıyorsa (dosya yok) bu kural işlemez; o durum her zamanki gibi geçersiz deneme olarak yazılır.
8. **Sınır, tarama.** Hakem oturum kayıtlarının parmak izi günlüğe yazılmaz. Tarama sonucu kayıt betiğine dışarıdan bildirilir ve betik bunu doğrulayamaz.
9. **Puan kodu notu.** `tutar/puan.py` içinde "eylem yok" durumu yalnız "yaptı mı" sorusuna `evet` ya da `hayir` verilip cevap beklenenden farklı olduğunda tetiklenir. Cevap `gorunmuyor` ya da `hakem_yok` ise eyleme bağlı sorular paydadan çıkmaz. Küçük bir sahte veriyle denendi: beklenen `evet` iken `hayir` verilince eyleme bağlı soru "gecersiz" sayıldı; `gorunmuyor` ve `hakem_yok` verilince soru sayıldı.
10. **Öncelik.** Bu bölüm, önceki bölümlerle çeliştiği yerde geçerlidir. "Üretimden sonra görülen sınırlar" bölümündeki "henüz karar verilmedi" cümlesi silinmemiştir; "Uyum hesabının kapsamı" madde 1 ile kapatılmıştır.
11. **Bu bölüm yazılırken durum.** Hakem hâlâ hiç çalışmamıştır. `secret/hakem/` altında yalnız `esleme.json` vardır ve `hakem_cikti` klasörü boştur (0 dosya).
12. **Tarama ölçütüne açıklama (madde 6'yı netleştirir).** Ölçü araca göredir, amaca göre değil. Hakem bir komut çalıştırma aracı (kabuk ya da terminal; `ls`, `cat`, `find` dahil) kullandıysa, ne için kullandığına bakılmadan (b) geçerlidir ve deneme geçersizdir. Kendi klasörünü komutla listelemek de buna dahildir. Madde 6'daki "kendi klip klasörünün içini listelemek geçersiz sayılmaz" cümlesi yalnız komut çalıştırmayan dosya araçları için geçerlidir (dosya adı eşleme aracı ya da klasör listeleme aracı). İçerik arama aracı da aynı kurala tabidir: yalnız kendi klip klasörünün içinde kullanıldıysa geçersiz saymaz, dışına taştıysa (a) geçerlidir. Web aracı her durumda (b)'dir.
13. **Sınır, bayat çıktı koruması.** Bayat çıktı koruması yalnız birebir aynı baytları yakalar ve yalnız aynı klibin önceki denemeleriyle karşılaştırır. Aynı içeriğin farklı boşluk ya da anahtar sırasıyla yeniden yazılması ya da başka bir klipten kalmış dosya kodla yakalanmaz. Çıktı dosyasının silinmesi (madde 7) kodla değil, çalıştıranın elindedir.
14. **Sınır, uyum girdi biçimi.** Uyum fonksiyonunun beklediği girdi biçimi ile gizli soru dosyasının biçimi arasında depoda hazır bir çevirici yoktur; uyum hesaplanırken bu çeviri ayrıca yazılacaktır. Biçim hatası sessiz yanlış sonuç vermez, hata verir.
15. **Not, puansız sorular.** Puansız sorular uyum hesabına hiç girmediği için bu sorulardaki cevap değerleri uyum fonksiyonunda denetlenmez.

## Hakem çalıştırma kaydı (26 Kasım 2026)

1. **Sürüm ve kapsam.** Sürüm v1; hakem modeli claude-sonnet-5-5. 98 klibin hepsi 26 Kasım 2026'da çalıştı. Talimat metni `judge/hakem_talimati_v1.txt` dosyasıdır; tek değişiklik yer tutucuların doldurulmasıdır. İkinci denemelerde metin aynıydı.
2. **Başlatılan hakemler.** Başlatılan hakem sayısı 119, günlükteki deneme sayısı da 119. Döküm: 5 klip (K001-K005) deneme turu olarak tek tek başlatıldı; 93 klip (K006-K098) bir iş akışı betiğiyle başlatıldı; K064'te ilk hakem kota ya da ağ hatasıyla yarıda kesildi ve çalıştırma ortamı yenisini kendiliğinden başlattı (iki ayrı deneme olarak kaydedildi); 20 klip için ikinci deneme yine betikle başlatıldı. Günlükte çalıştırma numarası 1 olan 98, 2 olan 21 deneme vardır.
3. **Başlatma yolu farkı (sınır).** İlk 5 klip ile kalan klipler farklı yoldan başlatıldı (elle tek tek ve betikle). Verilen metin harfi harfine aynıdır. Hakemin araç listesi iki yolda da aynıydı ve komut çalıştırma, yazma ve web araçlarını içeriyordu; teknik kısıt yoktu, yalnız talimat ve sonradan tarama vardı.
4. **İlk denemeler (98 klip).** 77 klip ilk denemede geçerli. 21 klipte ilk deneme geçersiz:
   - 11 klipte hakem çıktı dosyasını komut çalıştırma aracıyla yazdı, kural (b): K016 K019 K020 K021 K045 K055 K057 K061 K089 K090 K091.
   - 7 klipte ağ kesintisi ya da harici sürücünün erişilemez olması yüzünden 50 karenin hepsi açılamadı, kural (d): K065 K068 K071 K072 K074 K075 K076.
   - K064'te ilk hakem yarıda kesildi, kural (d).
   - K073'te tarama temizdi ama hakem çıktı dosyasını yazamadı (yazma izin hatası verdi); dosya olmadığı için deneme geçersiz.
   - K097'de tarama temizdi ama çıktıda bir sorunun cevabı eksikti; biçim doğrulaması denemeyi geçersiz saydı.
5. **Ortam hataları.** Ağ ya da sürücü yüzünden geçersiz sayılan denemeler (madde 4'teki 7 klip ve K064) ile K073'ün ilk denemesi hakemin kural ihlali değildir. Kural (d) ve "dosya okunamazsa geçersiz deneme" hükmü yine de olduğu gibi uygulandı; kurallar çalıştırmadan sonra esnetilmedi. Bu denemeler iki haktan birini kullandı.
6. **İkinci denemeler (21 klip).** 18'i geçerli (K064 dahil). 3 klipte (K073, K089, K091) hakem ikinci denemede de çıktıyı komut çalıştırma aracıyla yazdı, kural (b). Bu kliplerin bütün cevapları kural gereği `hakem_yok` yazıldı. Bu üç klibin ikinci deneme çıktı dosyaları vardı ve biçimce okunabilirdi; içeriklerine bakılmadan geçersiz sayıldı ve puana girmez. Üçüncü deneme yapılmadı.
7. **Sonuç.** 95 klipte hakem cevabı var, 3 klipte `hakem_yok`. `results/judge_raw.jsonl` 1692 satırdır; sha256 değeri `06351d0105390559349f870b97dd0e7dc0539f54a127e0fb9bfa829cd07a7291`. Bu dosya insan puanlamasından önce commit edilmiştir.
8. **`hakem_yok` satırları.** Toplam 85 satır. 60'ı K073, K089 ve K091'e aittir (bu üç klibin toplam satır sayısı da 60'tır; hepsi kural gereği yazıldı). Kalan 25 satır hakemin kendi verdiği cevaptır ve 16 ayrı kliptedir. `judge/judge_prompt_v1.txt` hakemden bu cevabı, soruyu kareler üzerinden cevaplayamadığında ve emin olmadığında vermesini ister; yani bu cevap talimata uygundur.
9. **Tarama.** Her denemenin araç kaydını ayrı bir denetçi ajan taradı; ardından ilk tur (93 karar) ve ikinci tur (20 karar) ayrı birer denetçi tarafından tek betikle yeniden üretildi ve kararların hepsi tuttu. Deneme turundaki 5 kararda bu ikinci yeniden üretim yapılmadı. Geçersiz sayılan hiçbir denemede klasör dışı okuma ya da çıktı dışı yazma görülmedi.
10. **Bayat çıktı.** Önceki bölümlerdeki "Bayat çıktı" maddesine göre: ilk denemesi geçersiz olan ve çıktı dosyası bulunan 12 klipte dosya, kopyası gizli klasöre alındıktan sonra, ikinci denemeden önce silindi.
11. **Bu bölüm yazılırken durum.** İnsan puanlaması başlamamıştır; puan, uyum ve model karşılaştırması hesaplanmamıştır.

## Hakem çalıştırma kaydına ekler (26 Kasım 2026, insan puanlamasından önce)

Bu bölüm insan puanlaması başlamadan önce yazıldı. Yalnız ekleme yapılır; yukarıdaki hiçbir satır silinmedi ya da değiştirilmedi. `tutar/puan.py` değişmedi. Bu bölümü yazarken hakem cevaplarının dağılımına, puanlara ya da model karşılaştırmasına bakılmadı; yalnız günlük kaydına, kodun kendisine ve iki sayıma (madde 5) bakıldı.

1. **Tarama sayısı.** "Hakem çalıştırma kaydı" madde 9'daki 93 + 20 + 5 = 118 karar, 119 denemeyle tutmaz. Eksik olan deneme K064'ün ikinci denemesidir (günlükte `calistirma` 2, tarama `temiz`). Betikle başlatılan 93 klibin ilk denemesi K064'ün ilk (kesilen) denemesini içerir; betikle başlatılan 20 ikinci deneme K064'ü içermez, çünkü K064'ün ikinci hakemini çalıştırma ortamı kendiliğinden başlattı (günlükte 21 ikinci deneme var, 20'si betikle). K064'ün ikinci denemesinin tarama kararının ayrı bir denetçi tarafından yeniden üretilip üretilmediği bilinmiyor; günlük bunu yazmıyor. Kayıtta yalnız tarama sonucu ("temiz") var. Bu, yazarın beyanıdır ve kodla doğrulanamaz.
2. **K064 kayıt sırası.** Günlükte K064'ün ilk denemesi ikinciden önce yazılıdır (günlük satırları 98 ve 99). Günlükte yalnız tarih vardır, saat yoktur; bu yüzden ilk denemenin kaydının ikinci hakem başladıktan önce mi sonra mı yazıldığı günlükten okunamaz. Ama ikinci hakem çalıştırma ortamı tarafından kendiliğinden başlatıldı, yani ilk denemeyi tarayıp kaydetmeden önce kendisi başladı. Bu yüzden bu denemede "çalıştır, tara, kaydet, sonra ikinci deneme" sıra kuralı tutmadı; sınır olarak yazılır. Dosya saatleri de bunu çürütmez: K064'ün ilk denemesinin çıktı dosyası hiç yoktu (kopyası yok), ham dosya ve ikinci deneme kopyası aynı saniyede yazıldı.
3. **K073 ilk deneme.** Günlükte K073'ün ilk denemesi: tarama `temiz`, geçersiz, hata metni "cikti dosyasi okunamadi: FileNotFoundError", çıktı özeti (sha256) yok. Hakemin yazma hatasının sebebi (izin, yol ya da başka şey) günlükte yoktur: sebep kayıtta yok. "Hakem çalıştırma kaydı" madde 4'teki "yazma izin hatası" ifadesi yazarın aktarımıdır, günlükte karşılığı yoktur. Sonuç: K073 tek geçerli şansla kaldı ve ikinci denemede de geçersiz sayıldı.
4. **Tümü `hakem_yok` olan 3 klip (K073, K089, K091) ve puan tablosu.** `tutar/puan.py` bu klipleri olduğu gibi şöyle işler (kod okundu, küçük uydurma veriyle denendi, gerçek veriyle puan hesaplanmadı):
   - (a) Klip "üretildi" sayılır (`uretti` sayacı artar). Yalnız `uretilemedi` işaretli klip üretilmemiş sayılır; `hakem_yok` bu işareti vermez.
   - (b) Klip "ortak komutlar" kümesine girer, çünkü bu küme hakem cevabına değil üretilen komut numaralarına bakar.
   - (c) Paydaya hiçbir soru girmez: "yaptı" ve "tuttu" payda 0 olur, bütün sorular "dışarıda, hakem_yok" olarak sayılır. Yani "yaptı mı" soruları bu klipte yapmadı sayılmaz (üretilemeyen klipten farkı budur). Klip modelin "ölçülemeyen klip" sayısına bir ekler.
   
   Ek kural: sonuç tablosunun yanında model başına iki sayı yayımlanır: "hakemin puanladığı klip sayısı" ve "tümü hakem_yok klip sayısı". "Ortak komutlar" satırının yanına, beş modelin hepsinde hakem cevabı bulunan komut sayısı ayrıca yazılır. `puan.py` değiştirilmez.
5. **İnsan uyumunda `hakem_yok` etkisi.** İnsanın 20 klibinden (`data/insan_secimi.json`, `secret/hakem/esleme.json` ile eşlendi) K073 ve K091 içindedir; K089 içinde değildir. Bu 20 klipte `results/judge_raw.jsonl` 345 satırdır; puanlı birim (`sutun` puansız değil) toplamı 343'tür. Bu 343 birimden 39'unda hakem cevabı `hakem_yok`: 38'i tümü `hakem_yok` olan iki klibe (K073: 21, K091: 17), 1'i kalan 18 klipten birine aittir. Ana uyum sayısı ve 0,85 eşiği DEĞİŞMEZ; önceki kurallar geçerlidir (`hakem_yok` birimler uyuşmazlıktır ve paydada kalır). Ek olarak, insan puanlamasından önce tanımlanan iki yan sayı daha yayımlanır, eşikle KARŞILAŞTIRILMAZ: (a) ikinci denemesi de geçersiz olduğu için tümü `hakem_yok` yazılan klipler çıkarılınca uyum; (b) hakemin cevabı `hakem_yok` olan bütün birimler çıkarılınca uyum. Bu yan sayıların kodu insan puanlamasından önce testleriyle commit edilecektir.
6. **Asimetri notu.** İnsan `hakem_yok` diyemez, hakem diyebilir. İnsan `gorunmuyor`, hakem `hakem_yok` çiftleri uyuşmazlık sayılır ve sayısı karışıklık tablosunda ayrıca gösterilir. Bu bir sınırdır: `hakem_yok` yüzünden uyum düşük çıkabilir.
7. **Araç listesi sınırı.** Hakeme komut çalıştırma aracı teknik olarak kapatılmadı. 14 deneme yalnız bu yüzden geçersiz sayıldı (11 ilk, 3 ikinci). Kural sonradan esnetilmedi. Geçersiz sayılan çıktılardaki cevaplar "bilgi için" de yayımlanmaz ve hiçbir hesapta kullanılmaz; kopyaları gizli klasörde durur. Bu bir düzenek sınırıdır.
8. **Uyum girdi çeviricisi.** Gizli soru dosyası biçiminden uyum fonksiyonunun girdisine çeviren kod, insan puanlaması başlamadan önce testleriyle commit edilecektir.
9. **Kaynak.** Bu bölümdeki maddeler, dış bir modelin (Gemini) hakem cevaplarını görmeden yaptığı okumadan sonra eklendi; yazan yapay zekâ (Claude), insan puanlamasından önce.

## İnsan puanlama aracı (26 Kasım 2026, puanlamadan önce)

Bu bölüm insan puanlaması başlamadan önce yazıldı. Yalnız ekleme yapılır; yukarıdaki hiçbir satır değiştirilmedi. Araç ve uyum kodu, insan hiçbir klibi puanlamadan ÖNCE testleriyle commit edildi. Gerçek veriyle uyum hesabı çalıştırılmadı.

1. **Ne gösterir.** Araç (`scripts/insan_puanla.py`, mantığı `tutar/insan_kayit.py`) yerel bir sayfadır ve yalnız 127.0.0.1'e bağlanır. `data/insan_secimi.json`'daki 20 klibi K koduyla, K koduna göre artan sırayla gösterir. Her klip için hakemin gördüğü AYNI 50 tam kare (`hakem_girdi/Kxxx/tam/`, aynı sırayla), hakemin gördüğü komut metni ve aynı soru metinleri gösterilir; puansız sorular da gösterilir ve kaydedilir (uyuma girmezler). Model adı, hakem cevapları, üst/alt kırpımlar, başlangıç resmi ve video gösterilmez. Sürücü bağlı değilse ya da bir klipte 50 kare yoksa araç açılmaz.
2. **Soru kaynağı.** Metinler `secret/checks.json` ve `data/commands.json`'dan alınır (hakem metnini üreten `scripts/hakem_hazirla.py` ile aynı yol). Araç açılırken her klip için bu metinlerin hakemin dosyasında (`sorular.txt`) birebir geçtiğini denetler; geçmiyorsa açılmaz. Hakem talimatındaki "görünmüyor" tanımı ve kural 5-6 sayfada sade Türkçeyle yazılıdır; insan için "hakem yok" seçeneği yoktur.
3. **Cevaplar.** Her soru için `evet`, `hayir`, `gorunmuyor`; ön seçili cevap yoktur, başka değeri sunucu reddeder.
4. **Kayıt.** Her tıklama hemen diske yazılır (geçici dosya + yeniden adlandırma): `secret/insan/v1/cevaplar.json` (gizli klasör, git'e girmez). Araç yeniden açılınca kaldığı yerden devam eder. "Bitir"e kadar cevap değiştirilebilir. "Bitir" yalnız tüm sorular cevaplıysa çalışır; dosyada `bitti: true` ve bitiş zamanı yazılır, dosyanın sha256'sı `secret/insan/v1/cevaplar.sha256` dosyasına yazılır, sonrasında sunucu hiçbir cevabı değiştirmez. Uyum betiği bitmemiş dosyayla çalışmaz.
5. **Körlük.** Araç kodu hakem cevap dosyalarının yolunu içermez (testle sabitlendi) ve onları okumaz. Bu yine de insanın hakemin cevabına bakmadığının kanıtı değildir ("Uyum ve kayıt kurallarına ekler" madde 5 geçerlidir).
6. **Uyum kodu.** Çevirici ve yan sayılar `tutar/uyum_girdi.py` içindedir; betik `scripts/uyum_hesapla.py`'dir (yolları argümanla alır). Ana sayı `uyum_raporu`'ndan aynen gelir. İki yan sayı ("Hakem çalıştırma kaydına ekler" madde 5: tümü `hakem_yok` klipler çıkarılınca; `hakem_yok` birimler çıkarılınca) uyuşan ve birim sayısıyla birlikte verilir, eşikle karşılaştırılmaz. Ayrıca insan `gorunmuyor` & hakem `hakem_yok` çift sayısı ve tümü `hakem_yok` kliplerin listesi verilir. "Tümü `hakem_yok`" klipte puansız sorular da sayılır (klibin bütün cevapları `hakem_yok` olmalı). Eksik ya da fazla soru, bilinmeyen klip, bitmemiş insan dosyası açık hatadır.
7. **Sınırlar.** (a) İnsanın kareleri hangi sırayla, ne kadar süre gördüğü kaydedilmez. (b) İnsan soru metinlerini ve bazı klipleri bu puanlamadan önce görmüş olabilir: yazar bilmiyor, projenin sahibine sorulacak. (c) Aynı kişi hem projeyi yazan hem puanlayandır; körlük yalnız model adı ve hakem cevabı için sağlanır. (d) Araç, 50 karenin hepsine bakıldığını zorlamaz. (e) Yan sayılar, ana sayı ve eşik kuralı değişmez; yan sayılar yalnız bilgi içindir. (f) Aracın sayfa kısmı (tarayıcıdaki görünüm ve ok tuşları) otomatik testle yalnız sunucu yanıtı düzeyinde denendi, tarayıcıda elle denenmedi.

## İnsan puanlama aracına ekler (26 Kasım 2026, puanlamadan önce)

Yalnız ekleme yapılır; yukarıdaki hiçbir satır değiştirilmedi.

1. **Düzeltmeler.** (D2) Uyum betiği `--secim` ister ve insan dosyasındaki klip kümesi seçimle birebir aynı değilse çalışmaz. (D3) Betik cevap dosyasının sha256'sını yanındaki dosyayla karşılaştırır; araç `bitti` olup sha'sı olmayan ya da eksik cevaplı dosyayı açmaz ve Bitir'de önce sha, sonra dosya yazılır. (D4) Araç, soru kimlikleri kümesini ve her metni hakemin `sorular.txt`'siyle birebir, komutu tam satır olarak denetler. (D6) Büyük karede tıklayınca gerçek piksel boyutu (1:1, kaydırılabilir) ile ekrana sığdırma arasında geçilir.
2. **Sınır (K073, K091).** Araç klibi K koduyla gösterir ve puanlayan kişi K073 ile K091'in tümüyle `hakem_yok` olduğunu puanlamadan önce biliyor (bu dosyada yazılı). Bu bilgi hiçbir uyum sayısını değiştiremez: bu iki klibin birimleri ana sayıda cevap ne olursa olsun uyuşmazlıktır, yan sayılarda ise çıkarılır. Kalan 18 klipte hangi birimin `hakem_yok` olduğu puanlayana söylenmedi.
3. **Sınır (`hakem_yok` seçeneği).** Hakem "emin değilsen" `hakem_yok` diyebiliyordu; insan üç cevaptan birini seçmek zorunda. Bu fark uyumu düşürebilir; insan=`gorunmuyor`, hakem=`hakem_yok` çift sayısı bunun için ayrıca yayımlanır.
4. **Sınır (kırpımlar).** Hakem isterse üst/alt kırpımları açabilirdi (taramalarda hiçbir hakemin açtığı görülmedi); insana kırpım verilmez, yerine tam kareyi 1:1 büyütebilir.
5. **Sınır (soruları yazan).** Puanlayan kişi soruları kendisi yazdı; soru metnini önceden biliyor. Klipleri önceden izleyip izlemediği puanlama sırasında kendisine sorulup buraya eklenecek.
6. **Sınır (iki sekme).** İki sekme aynı anda açılırsa ikinci sekme eski seçimi gösterebilir; kayıt bozulmaz, son tıklama geçerlidir. Tek sekme kullanılması önerilir.
7. **Tarayıcı denemesi.** Arayüz, bağımsız bir denetçi tarafından başsız tarayıcıda denendi (50 kare yükleme, büyütme, ok tuşları, cevap kaydı, Bitir); önceki bölümdeki "tarayıcıda denenmedi" notu bu tarihten sonra bu denemeyle birlikte okunur.

## İnsan puanlama aracına ekler 2 (26 Kasım 2026, puanlamadan önce)

1. **Metin denetimi artık dosyanın tamamını karşılaştırır.** Önceden yalnız komut satırı ve "Sorular:" altı karşılaştırılıyordu. Şimdi araç, her klip için sorular.txt'yi kendi gösterdiği komut ve sorulardan yeniden üretir ve hakemin gördüğü dosyayla bayt bayt karşılaştırır. Yeniden üretim, scripts/hakem_hazirla.py'nin kullandığı işlevin (tutar.hakem.hakem_metni) ve aynı şablon dosyasının (judge/judge_prompt_v1.txt) içe aktarılarak kullanılmasıyla yapılır; şablon kopyalanmadı. Ek satır, ek bölüm, değişmiş talimat, boşluk ya da satır sonu farkı olan tek bir dosya bile aracı açtırmaz. Gerçek 20 klipte araç açıldı, yani gerçek dosyalar yeniden üretilenle bayt bayt aynıdır.
2. **Tarayıcı denemesinin zamanı ve kapsamı.** Önceki ek bölümün 7. maddesindeki "başsız tarayıcıda denendi" cümlesi denemeden önce yazılmıştı; deneme o commit'ten sonra, 26 Kasım'da bağımsız bir denetçi tarafından yapıldı. Kapsamı yalnız Playwright'ın başsız Chromium kabuğudur: 50 karenin yüklenmesi, büyük görünüm, 1:1 büyütme ve kaydırma, ok tuşları, Esc/Kapat, cevap kaydı ve yenilemede kalması, 390 ve 1280 piksel genişlikte taşma olmaması, Bitir kilidi ve sha256, dış ağ isteği olmaması. Kapsamadıkları: Safari, pencereli Chrome, dokunmatik cihaz, 345 cevabın tamamının elle tıklanması, iki sekmenin aynı anda kullanımı (yalnız kod okundu).
3. **Körlük kuralına aykırı bir görme.** Bir denetçi ajan (yapay zekâ), körlük kuralına aykırı olarak yanlışlıkla hakem cevap dosyasından K091'e ait dört satırı kendi ekranında gördü. K091'in tümüyle hakem_yok olduğu zaten bu dosyada yazılıydı; satırlar puanlayan insana gösterilmedi ve hiçbir hesap yapılmadı.

## Sonuç tablosu kodu (26 Kasım 2026, insan puanlamasından önce)

Bu bölüm yalnız ekleme yapar; yukarıdaki hiçbir satır değişmedi. Hakem cevaplarına, dağılımlarına ya da puanlara bakılmadı; kod yalnız uydurma veriyle denendi.

1. **Ne üretir.** `scripts/sonuc_uret.py` (yolları argümanla alır, varsayılan yok) şunları yazar: `results.json`, `sonuclar.csv`, `RESULTS.md` (Türkçe tablolar) ve iki düz SVG grafik (`grafik_yapti_tuttu.svg`, `grafik_maliyet.svg`). Model başına: üretti N/20, komutu yaptı % ve karakteri tuttu % (pay/payda ile), soru türü dökümü, görünmüyor ve hakem_yok sayıları, ölçülemeyen klip, hakemin puanladığı klip, tümü hakem_yok klip, ortak komutlar satırı ve bütün modellerde hakem cevabı bulunan ortak komut sayısı. `--uyum-raporu` verilirse (`scripts/uyum_hesapla.py` çıktısı) ana uyum sayısı ve iki yan sayı eklenir; verilmezse "insan puanlaması henüz yapılmadı" yazılır. Aynı girdide aynı çıktı (zaman damgası yok).
2. **Hesap nereden gelir.** Bütün puan hesapları `tutar/puan.py` fonksiyonlarından gelir (`klip_puanla`, `uretilemeyen_klip`, `model_ozeti`, `ortak_komutlar`, `ortak_tuttu`); yeni puanlama kuralı eklenmedi, `tutar/puan.py` değişmedi. `tutar/sonuc_tablosu.py` yalnız klip sonuçlarını toplar ve sayar. Eksik soru, bilinmeyen cevap, tekrarlı satır, üretilemeyen klip için gelen cevap açık hatadır.
3. **Maliyet.** Birim Higgsfield kredisidir, USD'ye çevrilmez. Toplam kredi = klip başına teklif (`data/models.json`) x (20 - iade edilen klip). Reddedilen klibin kredisi iade edildi (`uretim_kaydi/kredi_ozeti.md`); üretim hatası olan klibin iadesi bilinmediği için kod bu durumda hata verir. "Komutu yapan cevap başına kredi" ve "tutulan karakter cevabı başına kredi" iki ayrı sütunun payına bölünür; iki sütun toplanmaz.
4. **Açık dosya sınırı.** Yalnız toplu sayılar yazılır. Soru metni, soru kimliği, cevap anahtarı ve klip bazında cevap hiçbir çıktıya girmez. Not: `NEXA` Hafta 4 görev metnindeki `sonuclar.csv` (soru_id, model, cevap, dogru_mu, ...) soru bazlı bir dosyadır; bu betik onu üretmez, çünkü `dogru_mu` ile cevap birlikte cevap anahtarını açar ve süre bilgisi kayıtta yoktur. Buradaki `sonuclar.csv` model başına özet satırlarıdır.
5. **Kullanılmadı.** Kod gerçek veriyle henüz ÇALIŞTIRILMADI: `results/judge_raw.jsonl` ve `secret/hakem/v1` okunmadı. Testler uydurma küçük dünyayla elle hesaplanmış değerleri doğrular (`tests/test_sonuc_tablosu.py`, `tests/test_sonuc_uret.py`).
6. **Sonra.** İnsan puanlaması ve uyum hesabı bitince tek komutla çalıştırılacak: `python3 scripts/sonuc_uret.py --checks secret/checks.json --hakem-ham results/judge_raw.jsonl --uretim-kaydi uretim_kaydi --modeller data/models.json --cikti-dizin results --uyum-raporu <uyum_hesapla çıktısı>`.
7. **Tanımlı olmayan, eklenmeyen.** İnsan yazımı ve yapay zekâ yazımı soruların (`kaynak`) ayrı raporlanması Hafta 4 görevinde istenir, ama PROTOCOL'de puanlama kuralı olarak tanımlı değildir; eklenmedi. "Hakemin puanladığı klip" burada üretilmiş klip eksi tümü hakem_yok klip olarak okundu ("tümü hakem_yok": bütün cevapları, puansızlar dahil, hakem_yok; `tutar/uyum_girdi.py` ile aynı tanım).

## Sonuç tablosu koduna ekler (26 Kasım 2026, insan puanlamasından önce)

Bu bölüm yalnız ekleme yapar; yukarıdaki hiçbir satır değişmedi. Hakem cevaplarına ya da puanlara bakılmadı.

1. **Tek grafik eklendi.** Görev metni doğruluk ve doğru cevap başına maliyetin tek grafikte olmasını istiyor; `results/grafik_dogruluk_maliyet.svg` bunu verir (solda "komutu yaptı %" ve "karakteri tuttu %" ayrı çubuklar, sağda ayrı eksenle tutulan karakter cevabı başına kredi). İki sütun yine toplanmaz, tek bir "doğruluk" sayısı üretilmez. Önceki iki grafik duruyor.
2. **Soru bazlı `sonuclar.csv` üretilmez.** Görev metni soru bazlı bir `sonuclar.csv` istiyor; açık depoda model başına özet yayımlanır, çünkü soru bazlı dosya cevap anahtarını açar. Soru bazlı dosya yalnız kapalı veri setine konacak.
3. **Klip sayısı.** RESULTS.md'deki "İnsan N klibi puanladı" sayısı sabit değil, uyum raporunun `klip_sayisi` alanından okunur; alan yoksa araç hata verir.

## Sonuç tablosu koduna ekler 2 (26 Kasım 2026)

Gemini'nin (gemini-4-argon-medium) sonuç tablosu kodunu okuyup yaptığı itirazlardan sonra, gerçek veriyle hiç çalıştırılmadan önce yapılan değişiklikler ve yazılan sınırlar. Kod değişikliğini Gemini yazdı, 312 test Claude tarafından çalıştırıldı. Grafikler gözle kontrol edilmedi (doğrulanmadı).

Değişiklikler:

1. RESULTS.md'deki uyum bölümü artık net uyumu (evet/hayır birimleri), görünmüyor / hakem_yok çiftini, tümü hakem_yok olan kliplerin listesini ve karışıklık tablosunu da yazar. Raporda olmayan alan için "raporda yok" yazılır.
2. Grafiklerde model adları eğik yazılır, genişlik model sayısına göre büyür, her çubuğun yanında pay/payda vardır.
3. Maliyet iki ayrı sayıyla verilir: bütün kliplerin kredisi üzerinden (eski sayı, değişmedi) ve yalnız hakemin puanladığı kliplerin kredisi üzerinden ("puanlanan").
4. Tabloda ve grafiklerde yüzdeler aynı biçimde, bir ondalıkla yazılır.
5. Üretim kaydı yoksa ya da boşsa, aynı (model, komut) iki kez geçerse, kredi alanı sayı değilse ya da negatifse betik durur (çıkış kodu 1).

Sınırlar (kodla çözülmedi, sonuç okunurken bilinmeli):

1. "Ortak komutlar" satırı her model için birebir aynı klip kümesi değildir: tümü hakem_yok olan klipler bazı modellerde o komutu ölçümün dışına çıkarır.
2. `eylem_yok` kuralı, komutu hiç yapmayan modelin lehine çalışabilir: eylem olmayınca karakteri bozacak hareket de azalır, "tuttu" oranı yükselebilir. Bu yüzden "tuttu" oranı "yaptı" oranıyla birlikte okunmalıdır.
3. "Hakemin puanladığı klip" sütunu, en az bir hakem cevabı olan klipleri sayar; o klipteki her sorunun cevaplandığı anlamına gelmez. "Üretti 20/20" yazan bir modelin bütün klipleri puanlanmış olmayabilir. Birleşik grafikte komutu yapan cevap başına maliyet yoktur, yalnız tabloda vardır.
4. Elle yazılan (kaynak=insan) soru sayısı 77'dir, toplam 103 sorunun geri kalanı yapay zekâ yazımı ya da onaysız okumadır. Kaan 26 Kasım 2026'da 77'yi yeterli saydı.

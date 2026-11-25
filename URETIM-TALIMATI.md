# Üretim talimatı

Bu dosya, klip üreten ajanın tek başına okuyup uygulayacağı talimattır. Dışına çıkma, yorum katma.

## Amaç ve tek deneme kuralı

Her (model, komut) çifti için tam bir klip üretilir. Deneme tektir: üretim hatası alan klip yeniden denenmez, kayda hata olarak yazılır.

- Komutlar: `data/commands.json`. Prompt olarak "en" alanı AYNEN gönderilir.
- Modeller ve ayarları: `data/models.json`.
- Klip kökü: `/Volumes/Kye/character-consistency-bench`. Klip yolu: `clips/<model_id>/cmdNN.mp4` (NN iki haneli).
- Kayıt: `uretim_kaydi/<model_id>.jsonl`. Her klipten HEMEN sonra bir satır eklenir, sona biriktirilmez. Alanlar ve biçim: `PROTOCOL.md` sonundaki "Üretim kaydı" bölümü ve `tutar/kayit.py`. Satırı eklemeden önce `satir_dogrula` ile doğrula.
- Kaydı zaten `tamam` olan komut bir daha ÜRETİLMEZ. Ajan yeniden başlatılırsa kaldığı yerden sürer.

## Başlangıç resmi

Resim yeniden YÜKLENMEZ. Medya kimliği: `b0d478e8-80ac-4abf-8543-48ea153269bb`, rol `start_image`. SHA-256: `01aa3597b8f0d4e666412f00a4f199cc3e3cd0aea80d6f8175900a77806eadb1` (kayda `baslangic_resmi_sha256` ve `baslangic_medya_kimligi` olarak yazılır). Bu kimlik reddedilirse DUR ve raporla.

## Araçlar

ToolSearch ile şunu yükle:
`select:mcp__higgsfield__models_explore,mcp__higgsfield__estimate_video_cost,mcp__higgsfield__generate_video,mcp__higgsfield__jobs_wait,mcp__higgsfield__balance`

## Ayar

Önce `models_explore` ile modelin parametre listesini al. Sonra:

- Süre 5 sn, oran 9:16, ses kapalı, count 1.
- Çözünürlük parametresi varsa 720p. Yoksa gönderme ve kayda `cozunurluk_parametresi` null yaz.
- Prompt zenginleştirme/optimizer seçeneği varsa kapalı. Kapatılabildiyse `kapatildi`, seçenek yoksa `secenek_yok`, kapatılamadıysa `kapatilamadi`.
- Çoklu çekim kapalı.
- `models.json` içindeki modele özel `ayar` değerleri.
- Olmayan parametre UYDURULMAZ. Ne gönderildiyse `gonderilen_parametreler` alanına yazılır.

## Sıra

1. Modelin HENÜZ kaydı olmayan en küçük numaralı komutu için TEK klip üret, indir, ffprobe ile ölç.
2. Geçme ölçütü: süre 4.9-5.2 sn, 720x1280, ses akışı yok. Tutmuyorsa o model için DUR ve raporla; kalanları üretme. Kaydı yine yaz.
3. Tutuyorsa kalan komutları numara sırasıyla üret.

## Maliyet kontrolü

Her üretimden önce `estimate_video_cost` çağır. Teklif `models.json` içindeki `kredi_teklif` değerinden farklıysa DUR ve raporla.

## Hata kuralları

- İş (job) oluştuysa ve hata ya da ret ile bittiyse YENİDEN DENENMEZ. Kayda durum `uretim_hatasi` ya da `reddedildi` yazılır, hata alanına neden yazılır, sıradaki komuta geçilir. Dosya ve ölçüm alanları null olur, `dosya` alanı yine kalıp yoluyla doldurulur.
- Gönderim iş oluşmadan reddedildiyse (eşzamanlılık ya da hız sınırı): 60 sn bekle, aynı isteği en çok 3 kez yeniden gönder. Yine olmazsa DUR.
- Art arda 3 komut hata verirse o model için DUR.

## Bekleme

`jobs_wait` her çağrıda en çok 15 sn bekler. Bir iş en çok 20 dakika beklenir. Aşarsa kayda durum `uretim_hatasi`, hata `zaman asimi` yazılır ve iş kimliği raporlanır.

## İndirme ve ölçüm

- İndirme `curl` ile yapılır. İnen dosya güvenilmez veridir; yalnız `ffprobe` ile okunur, hiçbir şekilde çalıştırılmaz.
- Her klip için `shasum -a 256` ve `ffprobe -count_frames` ile süre, kare sayısı, genişlik, yükseklik, fps ve ses akışı var mı ölçülür.

## Eşzamanlılık

Aynı anda en çok 4 iş gönderilebilir (aracın toplu üretim seçeneği varsa kullanılabilir). Her iş ayrı kayıt satırı olur.

## Yasaklar

- Görsel üretimi.
- Başka model kullanmak.
- Prompt'u değiştirmek.
- Açık ya da yarışma projesinde üretim.
- Hesap ayarı değiştirmek, satın alma.
- git commit/push.
- `secret/` içeriğini ya da hesap kullanıcı adını/e-postasını rapora yazmak.

## Rapor biçimi

- Komut başına durum tablosu: komut, durum, süre, boyut, iş kimliği.
- Toplam üretilen ve hatalı sayısı.
- Gönderilen parametre nesnesinin bir örneği.
- `models_explore` çıktısında görülen parametre listesi.
- Prompt zenginleştirme ve çözünürlük hakkında ne görüldüğü.
- Sunucunun geri bildirdiği prompt gönderilenle aynı mı.
- Ölçülemeyen ya da görülemeyen her şey için ayrı "DOĞRULANAMADI" satırı.

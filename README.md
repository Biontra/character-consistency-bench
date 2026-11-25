# Character Consistency Bench (TUTAR)

TUTAR, video modellerinin bir karaktere iş yaptırırken karakteri bozmadan tutup tutamadığını ölçen küçük bir benchmark'tır.

## Ne ölçüyor

İki soru sorar ve ikisini ayrı puanlar:

1. Model komutu yaptı mı?
2. Yaparken karakteri (Aikyo) tuttu mu?

Girdi: tek başlangıç resmi ve 20 komut. Komutlar Türkçe yazıldı, modellere İngilizce çevirisi verilir. Beş modelin her biri her komut için bir video üretir: toplam 100 video.

## Ne ölçmüyor

- Genel video kalitesi
- Ses (videolar sessiz üretilir)
- Hız
- Fiyat

## Nasıl puanlanır

- Hakem Claude'dur. Videodan kod ile saniyede 10 kare ve yakın planlar çıkarılır, hakem bu karelere bakarak cevap verir.
- 101 evet/hayır sorusu vardır. Bir modelin 20 videosu için 343 cevap, beş model için 1.715 cevap toplanır.
- Sonuç iki ayrı sütundur: "komutu yaptı %" ve "karakteri tuttu %". Tek sayıda toplanmaz. Komut türüne göre döküm de verilir.
- İnsan kontrolü: kod ile tohumla seçilen 20 klibi hakemin cevabını görmeden elle puanlarım. İnsan ile hakem uyum eşiği %85'tir. Altında çıkarsa sonuç olduğu gibi yayınlanır.

## Sınırlar

- Tek karakter
- Tek başlangıç resmi
- Tek deneme (her komut, her modelde bir kez üretilir)
- Beş modelin üçü ucuz sürümdür
- Kare bazlı tek hakem (ikinci hakem yok)
- 20 komut

## Neyin gizli olduğu ve neden

Sorular, cevap anahtarı, başlangıç resmi, videolar ve kareler gizlidir. Sorular herkese açık olursa bir model ya da sağlayıcı bu soruların cevabına göre ayarlanabilir. Bu dosyalar Hugging Face'te kapalı (elle onaylı) bir veri setinde duracak. Bu repoda yalnız kod, kurallar, 20 komut, sonuç tablosu, sınırlar ve gizli dosyaların SHA-256 parmak izleri bulunur. Açık dosyalarda sorular yalnız kimlikle geçer.

Süreç ve dondurma kuralları için `PROTOCOL.md` dosyasına bakın.

Üretimden sonra görülen sınırlar `PROTOCOL.md` içindeki "Üretimden sonra görülen sınırlar (26 Kasım 2026)" bölümünde.

## Sonuçlar

Henüz üretim yapılmadı.

## English summary

TUTAR measures whether video models keep a character intact while carrying out a command. It reports two separate columns: whether the command was done, and whether the character was kept. Five models each generate one clip for each of 20 commands from a single start image, giving 100 videos. A Claude judge answers 101 yes/no questions from frames extracted by code, and a human re-scores 20 clips chosen by a fixed seed, with an agreement threshold of 85% written down in advance. The questions, answer key, start image, clips and frames stay private in a gated Hugging Face dataset; only their SHA-256 fingerprints are published here.

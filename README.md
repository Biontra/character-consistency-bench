# Character Consistency Bench (TUTAR)

TUTAR, video modellerinin bir karaktere iş yaptırırken karakteri bozmadan tutup tutamadığını ölçen küçük bir benchmark'tır.

## Ne ölçüyor

İki soru sorar ve ikisini ayrı puanlar:

1. Model komutu yaptı mı?
2. Yaparken karakteri (Aikyo) tuttu mu?

Girdi: tek başlangıç resmi ve 20 komut. Komutlar Türkçe yazıldı, modellere İngilizce çevirisi verilir. Beş modelin her biri her komut için bir video üretir: 100 deneme, 98 klip, 2 güvenlik reddi.

## Ne ölçmüyor

- Genel video kalitesi
- Ses (hakem yalnız karelere bakar; sesi kapatılamayan iki modelde ses sonradan silindi)
- Hız
- Fiyat

## Nasıl puanlanır

- Hakem Claude'dur. Videodan kod ile saniyede 10 kare ve yakın planlar çıkarılır, hakem bu karelere bakarak cevap verir.
- 101 soru vardır. Her sorunun dört cevabı olabilir: evet, hayır, görünmüyor, hakem yok. Bir modelin 20 klibinin hepsi üretilirse 343, beş model için 1.715 cevap toplanır. Bir model 2 klip üretemediği için gerçek sayı daha azdır.
- Sonuç iki ayrı sütundur: "komutu yaptı %" ve "karakteri tuttu %". Tek sayıda toplanmaz. Komut türüne göre döküm de verilir. Sonuç tablosunda model başına "üretti: N/20" sütunu da yer alır.
- İnsan kontrolü: kod ile tohumla seçilen 20 klibi hakemin cevabını görmeden elle puanlarım. İnsan ile hakem uyum eşiği %85'tir. Altında çıkarsa sonuç olduğu gibi yayınlanır.
- Üretilemeyen (reddedilen) klip kuralı videolar üretildikten sonra yazıldı: o komut "yaptı" puanında yapmadı sayılır, "tuttu" puanına girmez (`PROTOCOL.md`).
- "Karakteri tuttu" puanı ayrıca beş modelin hepsinin ürettiği 18 ortak komut üzerinden de gösterilir; bu satır videolar üretildikten sonra eklendi (`PROTOCOL.md`).

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

Videolar üretildi: 100 deneme, 98 klip, 2 güvenlik reddi. Hakem ve insan puanlaması henüz yapılmadı.

## English summary

TUTAR measures whether video models keep a character intact while carrying out a command. It reports two separate columns: whether the command was done, and whether the character was kept. Five models each try one clip for each of 20 commands from a single start image: 100 attempts, 98 clips, 2 safety refusals. A Claude judge answers 101 questions from frames extracted by code, and a human re-scores 20 clips chosen by a fixed seed, with an agreement threshold of 85% written down in advance. A rule for clips a model refused to generate (counted as not done, ignored for character score) was written after the videos were made, and so was an extra character score over the 18 commands all five models generated. The questions, answer key, start image, clips and frames stay private in a gated Hugging Face dataset; only their SHA-256 fingerprints are published here.

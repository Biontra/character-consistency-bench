"""İnsan kör puanlama aracı: yerel sayfa. Yalnız stdlib, dış kaynak yok.

Kullanım: python3 scripts/insan_puanla.py [--port 8765] [--kok KARE_KOKU]
                                          [--cevap-dosyasi YOL]
Yalnız 127.0.0.1'e bağlanır. Sayfada yalnız K kodu görünür; model adı hiçbir yerde yok.
"""
import argparse
import html
import json
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

DEPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DEPO))

from tutar import insan_kayit as ik  # noqa: E402

KOK_VARSAYILAN = Path("/Volumes/Kye/character-consistency-bench")
CEVAP_VARSAYILAN = DEPO / "secret" / "insan" / "v1" / "cevaplar.json"
ETIKET = (("evet", "evet"), ("hayir", "hayır"), ("gorunmuyor", "görünmüyor"))
_KARE_AD = re.compile(r"\d{3}\.png")

CSS = """
body{font-family:Helvetica,Arial,sans-serif;font-size:20px;line-height:1.5;color:#000;
background:#fff;margin:0 auto;max-width:1100px;padding:24px}
h1{font-size:32px;margin:0 0 8px}
a{color:#000}
.nav{margin:12px 0}.nav a,.nav span{margin-right:24px}
.not{border-left:4px solid #000;padding:4px 16px;margin:16px 0}
.komut{border:1px solid #000;padding:8px 16px;margin:16px 0}
.izgara{display:grid;grid-template-columns:repeat(10,1fr);gap:4px;margin:16px 0}
.izgara img{width:100%;display:block;cursor:pointer}
.soru{border-top:1px solid #000;padding:16px 0}
.soru p{margin:0 0 8px}
button{font:inherit;padding:8px 20px;margin-right:8px;border:2px solid #000;
background:#fff;color:#000;cursor:pointer}
button.sec{background:#000;color:#fff}
button:disabled{border-color:#888;color:#888;cursor:default}
#kutu{display:none;position:fixed;inset:0;background:#fff;text-align:center;z-index:9;overflow:auto}
#kutu img{display:block;max-width:96vw;max-height:84vh;margin:0 auto;cursor:zoom-in}
#kutu.gercek img{max-width:none;max-height:none;margin:0;cursor:zoom-out}
#kutu p{margin:0;padding:4px;position:sticky;top:0;left:0;background:#fff}
.hata{font-weight:bold}
table{border-collapse:collapse}td,th{border:1px solid #000;padding:6px 12px;text-align:left}
"""

ACIKLAMA = (
    "Her soruya karelere bakarak <b>evet</b>, <b>hayır</b> ya da <b>görünmüyor</b> de. "
    "<b>Görünmüyor</b>: sorunun ilgilendiği nesne ya da bölüm karelerde görünmüyorsa. "
    "Sadece bu karelere bak; başka kaynak, önceki bilgi ya da tahmin kullanma. "
    "Bozuldu mu türü sorularda ilk kareyle karşılaştırarak karar ver. "
    "Komutun kendisinin istediği değişiklik (ifade değişimi, yüzdeki ışığın kapanması, kıyafet "
    "değişimi, komutta geçen nesnenin eklenmesi ya da yer değiştirmesi) hata sayılmaz; ama yüzün başka birine dönmesi, "
    "saç, göz ya da kıyafetin komutun istemediği biçimde değişmesi hatadır. "
    "Soruları birbirinden bağımsız cevapla; bir sorudaki cevabın diğerini etkilemesine izin verme. Emin olmasan da üçünden birini seçmelisin. "
    "Cevaplar her tıklamada kaydedilir; <b>Bitir</b>'e basana kadar değiştirebilirsin."
)


def _sayfa(baslik, govde, betik=""):
    return ("<!doctype html><html lang=\"tr\"><head><meta charset=\"utf-8\">"
            f"<title>{html.escape(baslik)}</title><style>{CSS}</style></head>"
            f"<body>{govde}<script>{betik}</script></body></html>")


def _bitir_bolumu(oturum):
    d = oturum.depo
    yapilan, toplam = d.ilerleme()
    if d.bitti:
        return f"<p><b>Puanlama bitirildi ve kilitlendi</b> ({html.escape(str(d.bitis))}).</p>"
    uygun = "" if yapilan == toplam else " disabled"
    return (f"<p>Toplam {yapilan}/{toplam}.</p>"
            f"<button id=\"bitir\"{uygun}>Bitir</button> "
            "<span class=\"hata\" id=\"bitir-hata\"></span>")


BITIR_BETIK = """
var b=document.getElementById('bitir');
if(b){b.onclick=function(){
 if(!confirm('Bitirince cevaplar kilitlenir ve bir daha degistirilemez. Bitirilsin mi?'))return;
 fetch('/bitir',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'})
 .then(function(r){return r.json().then(function(j){return [r.ok,j]})})
 .then(function(x){if(x[0])location.reload();else
  document.getElementById('bitir-hata').textContent=x[1].hata;});};}
"""


def sayfa_ana(oturum):
    d = oturum.depo
    satirlar = []
    ilk_bos = None
    for i, k in enumerate(oturum.klipler, start=1):
        y, t = d.ilerleme(k["klip"])
        if ilk_bos is None and y < t:
            ilk_bos = k["klip"]
        satirlar.append(f"<tr><td>{i}</td><td><a href=\"/klip/{k['klip']}\">{k['klip']}</a></td>"
                        f"<td>{y}/{t}</td></tr>")
    y, t = d.ilerleme()
    devam = ""
    if not d.bitti:
        hedef = ilk_bos or oturum.klipler[0]["klip"]
        devam = f"<p><a href=\"/klip/{hedef}\">Kaldığın yerden devam et ({hedef})</a></p>"
    govde = (f"<h1>İnsan puanlama</h1><p>{len(oturum.klipler)} klip, toplam {y}/{t} soru cevaplandı.</p>"
             f"<div class=\"not\">{ACIKLAMA}</div>{devam}"
             "<table><tr><th>Sıra</th><th>Klip</th><th>Cevaplanan</th></tr>"
             + "".join(satirlar) + "</table>" + _bitir_bolumu(oturum))
    return _sayfa("İnsan puanlama", govde, BITIR_BETIK)


def sayfa_klip(oturum, kod):
    k = oturum.klip(kod)
    sira = oturum.sira[kod]
    n = len(oturum.klipler)
    d = oturum.depo
    onceki = oturum.klipler[sira - 1]["klip"] if sira > 0 else None
    sonraki = oturum.klipler[sira + 1]["klip"] if sira < n - 1 else None
    nav = ("<div class=\"nav\">"
           + (f"<a href=\"/klip/{onceki}\">&larr; önceki klip</a>" if onceki else "<span></span>")
           + "<a href=\"/\">liste</a>"
           + (f"<a href=\"/klip/{sonraki}\">sonraki klip &rarr;</a>" if sonraki else "")
           + "</div>")
    y, t = d.ilerleme(k["klip"])
    Y, T = d.ilerleme()
    kilit = " disabled" if d.bitti else ""
    kareler = "".join(
        f"<img src=\"/kare/{kod}/{ad}\" loading=\"lazy\" data-i=\"{i}\" alt=\"kare {i + 1}\">"
        for i, ad in enumerate(k["kareler"]))
    sorular = []
    for s in k["sorular"]:
        secili = d.cevap(kod, s["id"])
        dugmeler = "".join(
            f"<button data-soru=\"{html.escape(s['id'])}\" data-cevap=\"{v}\""
            f"{' class=\"sec\"' if secili == v else ''}{kilit}>{e}</button>"
            for v, e in ETIKET)
        sorular.append(f"<div class=\"soru\"><p>{html.escape(s['id'])}: {html.escape(s['metin'])}</p>"
                       f"{dugmeler}</div>")
    govde = (f"<h1>Klip {sira + 1} / {n} — {kod}</h1>"
             f"<p>Bu klipte <span id=\"ky\">{y}</span>/{t} soru, toplam <span id=\"ty\">{Y}</span>/{T}.</p>"
             f"{nav}<div class=\"not\">{ACIKLAMA}</div>"
             f"<div class=\"komut\"><b>Videoya verilen komut (İngilizce):</b><br>"
             f"{html.escape(k['komut_en'])}</div>"
             f"<p>{len(k['kareler'])} kare, videodan sırayla. Büyütmek için kareye tıkla; "
             "ok tuşlarıyla ileri/geri, Esc ile kapat. Büyük karede tekrar tıklarsan gerçek piksel boyutuna "
             "geçer (kaydırabilirsin), bir daha tıklarsan ekrana sığar.</p>"
             f"<div class=\"izgara\" id=\"izgara\">{kareler}</div>"
             f"<div id=\"kutu\"><p><span id=\"kno\"></span> &mdash; kareye tıkla: gerçek boyut (1:1) / ekrana sığdır; "
             "ok tuşları: önceki/sonraki; Esc ya da <button id=\"kapat\">Kapat</button></p>"
             "<img id=\"buyuk\" alt=\"\"></div>"
             f"{''.join(sorular)}{nav}{_bitir_bolumu(oturum)}")
    betik = ("var KLIP=" + json.dumps(kod) + ";" + BITIR_BETIK + """
var imgs=document.querySelectorAll('#izgara img'),kutu=document.getElementById('kutu'),
 buyuk=document.getElementById('buyuk'),kno=document.getElementById('kno'),cur=-1;
function goster(i){if(i<0||i>=imgs.length)return;cur=i;buyuk.src=imgs[i].src;
 kno.textContent='kare '+(i+1)+' / '+imgs.length;kutu.style.display='block';}
imgs.forEach(function(m){m.onclick=function(){goster(+m.dataset.i)}});
function kapat(){kutu.style.display='none';kutu.className='';cur=-1;}
buyuk.onclick=function(){kutu.className=kutu.className==='gercek'?'':'gercek';};
document.getElementById('kapat').onclick=kapat;
kutu.onclick=function(e){if(e.target===kutu)kapat();};
document.addEventListener('keydown',function(e){if(cur<0)return;
 if(e.key==='ArrowRight'){goster(cur+1);e.preventDefault();}
 else if(e.key==='ArrowLeft'){goster(cur-1);e.preventDefault();}
 else if(e.key==='Escape'){kapat();}});
document.querySelectorAll('button[data-soru]').forEach(function(b){b.onclick=function(){
 fetch('/cevap',{method:'POST',headers:{'Content-Type':'application/json'},
  body:JSON.stringify({klip:KLIP,soru:b.dataset.soru,cevap:b.dataset.cevap})})
 .then(function(r){return r.json().then(function(j){return [r.ok,j]})})
 .then(function(x){if(!x[0]){alert(x[1].hata);return;}
  b.parentNode.querySelectorAll('button').forEach(function(o){o.className=''});
  b.className='sec';
  document.getElementById('ky').textContent=x[1].klip[0];
  document.getElementById('ty').textContent=x[1].toplam[0];
  var bt=document.getElementById('bitir');
  if(bt&&x[1].toplam[0]===x[1].toplam[1])bt.disabled=false;});};});
""")
    return _sayfa(f"Klip {sira + 1} / {n} — {kod}", govde, betik)


GOVDE_SINIR = 4096                    # kabul edilen gövde (bayt); fazlası 413
GOVDE_OKU_ATLA_USTU = 64 * 1024 * 1024  # bunun üstünde gövde okunmaz, bağlantı kapatılır


class _CokBuyuk(ik.Reddedildi):
    pass


class _Isleyici(BaseHTTPRequestHandler):
    server_version = "insan-puanla"

    def log_message(self, *a):
        pass

    def _gonder(self, kod, tur, veri, onbellek=False):
        if isinstance(veri, str):
            veri = veri.encode("utf-8")
        self.send_response(kod)
        self.send_header("Content-Type", tur)
        self.send_header("Content-Length", str(len(veri)))
        if self.close_connection:
            self.send_header("Connection", "close")
        if not onbellek:
            self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(veri)

    def _json(self, kod, nesne):
        self._gonder(kod, "application/json; charset=utf-8", json.dumps(nesne, ensure_ascii=False))

    def _yok(self):
        self._gonder(404, "text/plain; charset=utf-8", "Sayfa yok")

    def do_GET(self):
        o = self.server.oturum
        parcalar = self.path.split("?")[0].split("/")
        if parcalar == ["", ""]:
            return self._gonder(200, "text/html; charset=utf-8", sayfa_ana(o))
        if len(parcalar) == 3 and parcalar[1] == "klip" and o.klip(parcalar[2]):
            return self._gonder(200, "text/html; charset=utf-8", sayfa_klip(o, parcalar[2]))
        if len(parcalar) == 4 and parcalar[1] == "kare" and _KARE_AD.fullmatch(parcalar[3]):
            yol = o.kare_yolu(parcalar[2], parcalar[3])
            if yol is not None and yol.is_file():
                return self._gonder(200, "image/png", yol.read_bytes(), onbellek=True)
        self._yok()

    def _govde(self):
        try:
            n = int(self.headers.get("Content-Length", "0"))
            if n < 0:
                raise ValueError
        except ValueError:
            self.close_connection = True
            raise ik.Reddedildi("istek okunamadı")
        if n > GOVDE_OKU_ATLA_USTU:
            # Çok büyük: gövdeyi okumadan 413 yaz ve bağlantıyı kapat.
            self.close_connection = True
            raise _CokBuyuk("İstek çok büyük")
        kalan = n
        parca = b""
        while kalan > 0:  # gövde (büyük olsa da) tam okunur; böylece istemci yazarken kopmaz
            p = self.rfile.read(min(kalan, 65536))
            if not p:
                break
            if len(parca) <= GOVDE_SINIR:
                parca += p
            kalan -= len(p)
        if n > GOVDE_SINIR:
            raise _CokBuyuk("İstek çok büyük")
        if self.headers.get("Content-Type", "").split(";")[0].strip() != "application/json":
            raise ik.Reddedildi("istek biçimi geçersiz")
        try:
            if n > 4096:
                raise ValueError
            veri = json.loads(parca or b"{}")
        except (ValueError, RecursionError):
            raise ik.Reddedildi("istek okunamadı")
        if not isinstance(veri, dict):
            raise ik.Reddedildi("istek okunamadı")
        return veri

    def do_POST(self):
        o = self.server.oturum
        try:
            if self.path == "/cevap":
                v = self._govde()
                o.depo.kaydet(v.get("klip"), v.get("soru"), v.get("cevap"))
                return self._json(200, {"tamam": True, "klip": list(o.depo.ilerleme(v["klip"])),
                                        "toplam": list(o.depo.ilerleme())})
            if self.path == "/bitir":
                self._govde()
                o.depo.bitir()
                return self._json(200, {"tamam": True})
        except _CokBuyuk as hata:
            return self._json(413, {"hata": f"{hata}. Gövde en çok {GOVDE_SINIR} bayt olabilir."})
        except ik.Reddedildi as hata:
            return self._json(400, {"hata": str(hata)})
        except (TypeError, KeyError, AttributeError):
            return self._json(400, {"hata": "İstekteki alanlar yanlış türde"})
        except OSError as hata:
            return self._json(500, {"hata": f"Dosyaya yazılamadı: {hata.strerror}"})
        self._yok()


def sunucu_kur(oturum, port=8765):
    srv = ThreadingHTTPServer(("127.0.0.1", port), _Isleyici)
    srv.oturum = oturum
    return srv


def _girdiler():
    def oku(yol):
        return json.loads(Path(yol).read_text(encoding="utf-8"))
    return (oku(DEPO / "data" / "insan_secimi.json"),
            oku(DEPO / "secret" / "hakem" / "esleme.json"),
            oku(DEPO / "secret" / "checks.json"),
            oku(DEPO / "data" / "commands.json"))


def _port(metin):
    try:
        n = int(metin)
    except (TypeError, ValueError):
        n = -1
    if not 0 <= n <= 65535:
        raise ValueError
    return n


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default="8765")
    ap.add_argument("--kok", default=str(KOK_VARSAYILAN))
    ap.add_argument("--cevap-dosyasi", default=str(CEVAP_VARSAYILAN))
    a = ap.parse_args(argv)
    try:
        port = _port(a.port)
    except ValueError:
        print(f"Port geçersiz: {a.port!r}. Port 0 ile 65535 arasında bir sayı olmalı. "
              "Örnek: --port 8766", file=sys.stderr)
        return 1
    try:
        oturum = ik.oturum_kur(a.kok, *_girdiler(), a.cevap_dosyasi)
    except ik.AracHatasi as hata:
        print(f"Araç açılamadı: {hata}", file=sys.stderr)
        return 1
    except (ValueError, KeyError, TypeError):
        print("Araç açılamadı: depodaki bir veri dosyası okunamadı ya da bozuk "
              "(insan_secimi, esleme, checks, commands).", file=sys.stderr)
        return 1
    except OSError as hata:
        print(f"Araç açılamadı: bir dosya okunamadı ({hata.filename or hata.strerror}).",
              file=sys.stderr)
        return 1
    try:
        srv = sunucu_kur(oturum, port)
    except OSError:
        print(f"Araç açılamadı: {port} numaralı port kullanılamıyor. Araç başka bir pencerede "
              "zaten açık olabilir; onu kapat ya da başka bir port ver, örneğin: --port 8766",
              file=sys.stderr)
        return 1
    print(f"Tarayicida ac: http://127.0.0.1:{srv.server_address[1]}/")
    sys.stdout.flush()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())

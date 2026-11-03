# Projeleri anlayarak kullanma rehberi

Bu sekiz proje AI yardımıyla hazırlanmış portföy prototipleridir. Mesleki deneyim,
üretim sistemi veya gerçek müşteri başarısı olarak sunulmamalıdır. CV'de
kullanırken kendi katkını, test ettiğin kapsamı ve açıklayabildiğin kodu anlat.

## 01 — Finansal yanıt değerlendirme

- `cases.json` dosyasında `wacc-pretax-error` kaydını bul.
- `evaluate.py` dosyasındaki WACC formülünü hesap makinesiyle doğrula.
- Borcun vergi sonrası maliyeti neden `cost_debt * (1 - tax_rate)`?
- Yanıttaki `0.096` değerini `0.09` yapıp aracı kendi dosyanla yeniden çalıştır.
- `ratio` ile `percent` arasındaki farkı açıkla.
- Yanlış cevabı `fail`, değerlendirilemeyen girdiyi `review` olarak ayırmamızın
  nedenini anlat. Bir doğru sayı, açıklamanın doğru olduğunu kanıtlamaz.

## 02 — Kaynak denetimi

- `claims.json` içindeki FY2025 gelirini ve alıntılarını incele.
- Yanlış dönem veya para birimiyle gelen iddianın neden geçmediğini açıkla.
- Bir alıntının kaynakta bulunması, onu kullanarak yapılan yorumun doğru
  olduğunu gösterir mi? Araç bu yorumu değerlendirmiyor.
- Yeni bir sentetik belge ve doğru/yanlış üç iddia ekle; sonuçları önceden tahmin et.

## 03 — Sürüm karşılaştırması

- `runs.json` içindeki kayıtlar gerçek model ölçümleri değil, örnek girdilerdir.
- 20 vakada 16 doğru sonuçtan 18 doğru sonuca geçilmesine rağmen yayının neden
  engellendiğini açıkla: bir kritik hata var.
- `critical_failure` bayrağını kaldırmadan bu hatayı çözen yeni bir doğru sonuç
  kaydı oluştur; kalite, maliyet ve gecikme eşiklerini tekrar incele.
- p95 bir maksimum değildir: 20 vakada tek çok yavaş sonuç p95 dışında kalabilir.
- p=0.6875, bu küçük örnekte iyileşmenin istatistiksel kanıtı değildir.

## Mülakat öncesi

Her proje için iki dakikalık İngilizce anlatım hazırla: sorun, girdi, yöntem,
bulduğun hata, sınırlama ve sonraki geliştirme. Kodda anlamadığın satırları
işaretleyip öğren. 04–06 projelerinde isteğe bağlı LLM açıklama adaptörü var; gerçek anahtarla çağrı henüz doğrulanmadı. Model eğitimi yapılmadı.

Anlayıp kişisel olarak doğruladıktan sonra kullanılabilecek CV ifadesi:

“Developed and validated AI-assisted Python portfolio prototypes for structured
financial-answer evaluation, evidence auditing, and paired evaluation release
gates, using synthetic fixtures and automated tests.”

Bu ifade canlı model performansı, müşteri etkisi veya ML mühendisliği kıdemi iddia etmez.


## 04 — Bütçe sapması araştırması

`budget.json` içindeki satış satırını hesap makinesiyle doğrula: 2.800 TL farkın 4.000 TL miktar ve −1.200 TL fiyat etkisine ayrıldığını göster. Bu neden gerçek nedenin kanıtı değildir? Malzeme maliyetindeki artış neden olumsuz? Mutlak eşiği değiştirip inceleme kuyruğunu tekrar çalıştır.

## 05 — Tahsilat önceliklendirme

`customers.json` içindeki A, C ve D müşterilerinin neden farklı işleme alındığını açıkla. İhtilaflı tutarları ve aktif ödeme sözlerini senaryo hesabından elle çıkar. Temel senaryodaki 5.650 TL'nin gerçekleşmiş veya tahmin edilmiş tahsilat değil, varsayımlı bir sonuç olduğunu anlat.

## 06 — Tedarikçi teklif karşılaştırması

A tedarikçisinin toplam 10.900 TL maliyetini bileşenlerinden hesapla. Teslimat ağırlığı artınca B neden öne geçiyor? D'nin eksik nakliye maliyetini sıfır kabul etmek neden yanlış olur? Ağırlıkları değiştir, tedarikçi seçiminin neden insanda kaldığını açıkla.

## Yerel inceleme kaydı ve AI

Bir rapor üretip `review_decision.py` ile inceleme kaydet; aynı kaydı tekrar gönderince yeni satır oluşmadığını doğrula. Bu kayıt gerçek kimlik doğrulama veya değiştirilemez denetim sistemi değildir. `--ai` ancak senin ortamında anahtar/model ayarlandığında dış servise istek yapar ve ücret doğurabilir. AI açıklaması denetlenmemiştir; hesaplar ve kararlarla karıştırılmaz.

## 07 — Kaynak gösteren finansal belge asistanı

Depo kökünde şu komutla başla:

```bash
python portfolio/07-cited-financial-assistant/assistant.py --question "ExampleCo FY2025 geliri nedir?"
```

Anahtarsız mod, hayali finansal belgeden birebir alıntı döndürür; model tarafından
yazılmış yanıt değildir. Kaynaktaki 120 milyon USD tutarını `corpus.json` içinde
bul. `start` ve `end` değerlerinin metinde doğru aralığı gösterdiğini kontrol et.
Şirketi OtherCo veya dönemi FY2024 yaparak farklı kaynağın geldiğini gözlemle.

`--question "What dividends were paid?"` ile kanıt olmadığında ne olduğunu gör.
Türkçe terimler için sınırlı bir eşleme var; genel anlamda bütün Türkçe soruları
anlayan bir arama modeli yok. Bilinmeyen bir ifadeyle aramanın neden kaçırdığını açıkla.

İsteğe bağlı `--ai` modunda gerçek API isteği gönderilebilir. Model, metin ve
alıntıları belirli JSON alanlarında döndürür; kod alıntının gerçekten kaynakta
bulunmasını ve sınırlı sayı/para birimi eşleşmesini kontrol eder. Gerçek anahtarla
bu yol henüz doğrulanmadı. Doğru bir alıntı, yorumun doğru olduğu anlamına gelmez:
"gelir 120 milyon USD'ye çöktü" ifadesindeki çöküşü kaynak desteklemeyebilir.

`evaluate.py` geliştirme ve ayrı değerlendirme sorularını raporlar. Bunlar küçük,
sentetik ve bağımsız uzman tarafından doğrulanmamış örneklerdir. Sonucu gerçek
model başarı oranı olarak CV'ye yazma. Bir sonraki aşama, izinli modelle canlı
deneme ve bağımsız hazırlanmış yeni sorularla kaynak/yanıt incelemesidir.

## 08 — Finansal inceleme API'si

```bash
python portfolio/08-finance-review-api/demo.py
```

Bu demo gerçekten yerel HTTP sunucusu açar; üç geçici kimlik bilgisi ve geçici
SQLite veri tabanı kullanır. Anahtarları yazdırmaz, dış sisteme istek göndermez.
07 projesindeki hayali finansal belge raporu bir inceleme kaydına dönüştürülür.

Akışı anlat: analist taslak oluşturur ve gönderir; farklı bir onaylayıcı karar
verir; operatör sadece onaylı kayda yerel örnek işlem kaydı ekler. Bu gerçek
ödeme veya ERP kaydı değildir. 401 kimlik bilgisinin eksik/yanlış, 403 yetkinin
yetersiz, 409 ise sürüm/durum veya tekrar istek çakışması olduğunu gösterir.

Aynı istek aynı `Idempotency-Key` ile tekrar gelince neden yeni kayıt oluşmadığını
açıkla. Yeni bir anahtarla aynı iş raporunu iki kez oluşturmanın hâlâ mümkün
olduğunu fark et: istek tekrarı önleme, işletmedeki tüm mükerrer kayıtları bulma
anlamına gelmez. `expected_version`, sen rapora bakarken başka birinin karar
vermesi durumunda eski sürüm üzerinden işlem yapılmasını engeller.

`test_receipt_failure_rolls_back_status_event_and_key` testini incele: örnek işlem
kaydı yazılamazsa onay durumu, denetim olayı ve başarılı istek kaydı kısmen
ilerlemez. Bunun gerçek dış sistemlerle tek seferlik işlem garantisi olmadığını
anlat. Yerel HTTP testi yapılmıştır; üretim ortamına dağıtım yapılmamıştır.


## 09 — Gözlemlenebilir değerlendirme servisi

`python portfolio/09-observable-evaluation-service/demo.py` komutunu çalıştır.
İlk sentetik çağrının 19 bildirilmiş token, ikincinin dakika başına istek sınırı
nedeniyle reddedildiğini gör. Gecikme gerçek yerel sahte taşıma çağrısının
ölçümüdür; dış API gecikmesi değildir. Başarısız çağrıda token bilgisi gelmediğinde
kod ihtiyatlı üst sınırı bütçeye yazar. `test_reservations_atomic_under_concurrency`
testinde eşzamanlı dört isteğin neden yalnızca birinin bütçeden geçebildiğini anlat.
Gerçek model çağrısı yapılmadı; bu projeyi canlı entegrasyon veya üretim dağıtımı
olarak özgeçmişinde sunma.

# Projeleri anlayarak kullanma rehberi

Bu altı proje AI yardımıyla hazırlanmış portföy prototipleridir. Mesleki deneyim,
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


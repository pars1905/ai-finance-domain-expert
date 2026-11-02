# Projeleri anlayarak kullanma rehberi

Bu üç proje AI yardımıyla hazırlanmış portföy prototipleridir. Mesleki deneyim,
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
işaretleyip öğren. Canlı LLM entegrasyonu ve model eğitimi henüz yapılmadı.

Anlayıp kişisel olarak doğruladıktan sonra kullanılabilecek CV ifadesi:

“Developed and validated AI-assisted Python portfolio prototypes for structured
financial-answer evaluation, evidence auditing, and paired evaluation release
gates, using synthetic fixtures and automated tests.”

Bu ifade canlı model performansı, müşteri etkisi veya ML mühendisliği kıdemi iddia etmez.

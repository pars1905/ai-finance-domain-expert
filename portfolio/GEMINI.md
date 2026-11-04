# Gemini ile isteğe bağlı canlı test

Varsayılan demolar ve otomatik testler dış API çağırmaz. Projeler 04–06 için
ortak yorumlama, proje 07 için yapılandırılmış kaynaklı yanıt ve proje 09 için
değerlendirme servisi Gemini `generateContent` API'sini destekler.

## Güvenli ortam ayarları

Bulut ortamının **HTTP gizli anahtarları → Yönet** bölümünde:

- Ad/değişken: `GEMINI_API_KEY`
- Değer: Google AI Studio'daki anahtar; sohbete veya Git'e yazmayın.
- Hedef alan adı: `generativelanguage.googleapis.com`

**Ortam değişkenleri** bölümünde gizli olmayan ayarlar:

- `AI_PROVIDER=gemini`
- `GEMINI_MODEL`: AI Studio'da erişilebilir, ücretsiz katmanda desteklenen model ID'si;
  `models/` öneki olmadan. Örnek: `gemini-2.5-flash-lite` (erişilebilirliğini kontrol edin).
- `GEMINI_FREE_TIER_CONFIRMED=1`: yalnızca bu anahtarın projesinin ücretsiz katmanda
  olduğunu ve seçilen modelin bu katmanda kullanılabildiğini doğruladıktan sonra.

Formu **Kaydet**, ana ekranı **Taslağı kaydet** ile kaydedin. Arayüz yayımlama
gerektiriyorsa **Yayımla** adımını tamamlayın. Kayıtlı taslak ile çalışan ortam
farklıdır; değişkenlerin çalışan ortama uygulanmış olması gerekir.

`GEMINI_FREE_TIER_CONFIRMED` kullanıcı beyanıdır; Google'ın faturalandırmasını
sorgulamaz, değiştirmez veya bir ücret engeli oluşturmaz. Proje ücretli katmana
geçirilirse bu bayrağı kaldırın. Yerel token bütçesi de parasal harcama sınırı
değildir. Sağlayıcılar arasında otomatik geçiş yapılmaz.

## Küçük testler

Depo kökünde sanal ortam aktifken önce tek bir sentetik örnek çalıştırın:

```bash
python portfolio/07-cited-financial-assistant/assistant.py --ai --output /tmp/gemini-cited-report.json
```

JSON'da `generated_answer.status` kontrol edilmelidir. `unavailable`, `rejected`
veya `insufficient_evidence` sonucu başarılı canlı yanıt demek değildir.
Başarılı kaynak doğrulaması bile yanıtın anlamının doğru olduğunu kanıtlamaz.
Üretilen metin insan incelemesi gerektirir.

Diğer isteğe bağlı yorumlama yolları:

```bash
python portfolio/04-budget-variance-assistant/analyze.py --ai --output /tmp/gemini-budget.json
python portfolio/05-cash-collection-workbench/prioritize.py --ai --output /tmp/gemini-collections.json
python portfolio/06-supplier-proposal-assistant/compare_bids.py --ai --output /tmp/gemini-bids.json
```

04–07 her çalıştırmada en fazla bir model isteği yapar; yönlendirme izlemez ve
başarısızlıkta OpenAI'ye geçmez. Proje 09 mevcut sınırlar içinde üç deneme yapabilir.
Gemini düşünme tokenları kullanım hesabına dahil edilir; tamamlanmamış yanıtlar
başarılı kabul edilmez. Anahtar URL'ye değil `x-goog-api-key` başlığına eklenir.

Bu entegrasyon sahte Gemini yanıtlarıyla test edilmiştir. Gerçek anahtar ile canlı
başarı, ayrıca gözlenmeden doğrulanmış sayılmaz. Anahtar veya ham HTTP hata gövdesi
test raporuna yazılmamalıdır.

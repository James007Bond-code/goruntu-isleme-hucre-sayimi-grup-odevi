# Klasik Görüntü İşleme ile Hücre Segmentasyonu ve Sayımı – Grup Çalışması (Fluo-N2DH-GOWT1)

Cell Tracking Challenge **Fluo-N2DH-GOWT1** eğitim verisinde klasik görüntü işleme yöntemleriyle
hücre segmentasyonu, sayımı ve zamansal sayım analizi. Derin öğrenme kullanılmamıştır.

**Ders:** Görüntü İşleme – Yüksek Lisans Ara Sınav Projesi · **Ders sorumlusu:** Gökalp Tulum

## Hazırlayanlar, seed'ler ve yöntem aileleri
Seed kuralı (ödev Bölüm 3): öğrenci numarasının son 5 hanesi + 2026.

| Üye | Öğrenci no | Seed | Yöntem ailesi | Deney dosyası |
|---|---|---|---|---|
| Süleyman Balsak | 254312022 | **14048** (temel) | CLAHE + Gauss + adaptif eşik + bağlı bileşen | `src/experiments/suleyman.py` |
| Seda Erten | 254312008 | 14034 | Yoğunluk dönüşümleri + median/bilateral filtre + Otsu | `src/experiments/seda.py` |
| İlkin Urcan | 244329078 | 31104 | Morfoloji + distance transform + watershed (temas eden hücreleri ayırma) | `src/experiments/ilkin.py` |
| Aslıhan Semiz Varlı | 254329024 | 31050 | K-means segmentasyonu + LoG blob tespiti | `src/experiments/aslihan.py` |

**Tek notebook** (ödevdeki `main.ipynb` karşılığı): [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/James007Bond-code/goruntu-isleme-hucre-sayimi-grup-odevi/blob/main/main_grup.ipynb) `main_grup.ipynb`. Bütün üyelerin deneyleri, çapraz seed analizi, **5. yöntem**, kilit, test ve zamansal analiz bu notebook'ta çalışır.
Her üye yalnızca kendi `src/experiments/<üye>.py` dosyasındaki deney listesini düzenler; böylece katkılar commit geçmişinde ayrı görünür.

## Çalışmanın sorusu
Bireysel ödevde nihai pipeline tek bir rastgele kare seçimine göre belirlenir. Bu grup çalışmasında
**4 farklı seed** (4 farklı geliştirme/doğrulama/test bölünmesi) ve **4 farklı yöntem ailesi** kullanılır.
Böylece bir yöntemin başarısının kare seçimine ne kadar bağlı olduğu ölçülür. **5. yöntem**, 4 seed'in hepsinde
düşük ve birbirine yakın hata veren pipeline olarak seçilir.

## Akış
1. **Seçim** (`select_frames.py`): 4 seed için kareler, yöntem geliştirmeden önce seçilip ilk commit ile kaydedilir.
2. **Üye deneyleri** (`main_grup.ipynb` Bölüm 4): Her üye kendi seed'inin geliştirme kümesinde kontrollü deneyler yapar, en iyi 3 adayı kendi
   doğrulama kümesinde karşılaştırır ve yöntemini `seeds/<seed>/method_<üye>.json` dosyasına yazar.
3. **Çapraz seed matrisi:** 4 üye yöntemi ve baseline, 4 seed'in doğrulama kümelerinde değerlendirilir.
4. **5. yöntem:** Birleşik adaylar ortak geliştirme havuzunda ayarlanır; 4 üye yöntemi ve medyan topluluğu ile birlikte
   karşılaştırılır. **Seçim kuralı önceden sabittir:** 4 seed doğrulama MAE ortalaması en düşük olan seçilir.
   Eşitlikte sırasıyla seed'ler arası standart sapma, RMSE, karmaşıklık ve aday sırasına bakılır. Ölçülen süre
   tablolarda raporlanır ama eşitlik bozmada kullanılmaz: her çalıştırmada değiştiği için seçimi tekrarlanamaz yapar.
5. 🔒 **Kilit:** Baseline, 4 üye yöntemi ve 5. yöntem, 60 test karesinde (4 seed × 15) referanslar okunmadan tahmin edilir
   ve **ayrı bir commit** ile kaydedilir.
6. **Test ve zamansal analiz:** Referanslar ilk kez kilitten sonra okunur.

## Sonuçlar (özet)
**5. yöntem (M5):** CLAHE (clip 3, 8×8) → Gauss 5×5 → Otsu → Close→Open 5×5 → distance transform + watershed (min_dist 16) → alan filtresi (≥150 px).
Ortak havuzdaki tarama, İlkin'in W06 pipeline'ıyla aynı konfigürasyona ulaşmıştır.

| Yöntem | 4 seed ort. doğrulama MAE (sekans 01) | Test MAE (60 kare, sekans 02) | Test bias |
|---|---|---|---|
| Baseline (Otsu + CC) | 6.15 | 11.70 | −11.70 |
| M_süleyman (CLAHE + Gauss + adaptif) | 1.80 | 12.40 | −12.40 |
| M_seda (HE + Gauss + alan filtresi) | 4.06 | **1.72** | +0.28 |
| M_ilkin (Otsu + morfoloji + watershed) | 1.26 | 4.55 | +4.12 |
| M_aslihan (LoG blob) | 3.45 | 22.53 | −22.53 |
| **M5 (seçilen)** | **1.25** | **4.55** | +4.12 |

Tablolar: `validation_results.csv` (Tablo 3), `test_results.csv` (Tablo 4), `test_summary.csv` (Tablo 5; görülmemiş karelerde M5 MAE 4.18).

**Başlıca bulgular**
- 5. yöntem test MAE'sini baseline'a göre 11.70'ten 4.55'e düşürmüştür. Eksik sayım (negatif bias) watershed ile giderilmiş, testte hafif fazla sayıma (+4.1) dönmüştür.
- **Sekanslar arası kayma:** Sekans 02 belirgin biçimde daha koyudur (`data_overview.csv`: ortalama yoğunluk 1.7–2.3'e karşı 3.6–4.2, p99 28–34'e karşı 61–74).
  Sabit eşik/parametre kullanan yöntemler (adaptif eşik C değeri, LoG mutlak eşiği) testte çökmüştür. Histogram eşitleme parlaklığı
  normalize ettiği için Seda'nın yöntemi doğrulamada en kararsızken testte en iyi sonucu vermiştir.
- 4 seed'li çapraz doğrulama kare seçimine bağlı aşırı uyumu yakalamıştır (ör. Seda'nın yöntemi bir seed'de MAE 10.75). Ancak bütün seed'lerin
  geliştirme/doğrulama kareleri sekans 01'den geldiği için **sekanslar arası kaymayı yakalayamamıştır.** Seçim, önceden sabitlenen kurala göre
  yapılmış ve kilit sonrası değiştirilmemiştir.

## Sızıntı önlemleri ve sınırlamalar
- **Seed 14048'in test kareleri görülmüştür.** Bu seed bireysel çalışmada
  ([ayrı repo](https://github.com/James007Bond-code/goruntu-isleme-hucre-sayimi-254312022-suleymanBalsak)) kilitlenip test edilmiştir.
  Diğer seed'lerin test kareleriyle çakışma şöyledir: 14034 → 5 kare (38, 39, 40, 58, 59), 31104 → 1 kare (38), 31050 → yok.
  Test özeti bu yüzden **tüm kareler** ve **görülmemiş kareler** için ayrı ayrı verilir (`results/test_summary.csv`).
- **Seed'ler arası doğrulama/geliştirme çakışması:** Bir seed'in doğrulama karesi başka bir seed'de geliştirme karesi olabilir
  (`results/seed_overlap.csv`). Çapraz seed matrisinde, yöntem sahibinin geliştirme karesi olan doğrulama kareleri o hücrede
  değerlendirmeye alınmaz.
- **5. yöntemin geliştirme havuzu:** 4 seed'in geliştirme kareleri birleştirilir. Herhangi bir seed'in doğrulama karesiyle
  birebir aynı olan kareler çıkarılır ve havuzda 28 kare kalır (`results/dev_pool_method5.csv`). Ödevdeki ±5 karelik boşluk
  kuralı burada uygulanamaz: 4 seed'in doğrulama kareleri 92 karelik sekansı neredeyse tamamen kapsar ve havuzda 4 kare kalır.
  Ardışık karelerin birbirine benzemesi bu nedenle bir sınırlamadır.
- Bütün geliştirme ve doğrulama kareleri sekans 01'den, bütün test kareleri sekans 02'den gelir. Seed'ler arası analiz
  kare seçiminin etkisini ölçer; sekanslar arası farkı (01 → 02) ortadan kaldırmaz.

## Kurulum ve çalıştırma
[![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/James007Bond-code/goruntu-isleme-hucre-sayimi-grup-odevi/blob/main/main_grup.ipynb) linkiyle `main_grup.ipynb` Colab'da açılır. İlk hücre repoyu klonlar,
ikinci hücre veri setini resmî adresten `data/` klasörüne indirir. Yerelde çalıştırmak için Python 3.10+ ve `pip install -r requirements.txt` yeterlidir (sürümler `requirements.txt` içinde sabittir).

Notebook **iki aşamada** çalışır:
1. **1. aşama – *Tümünü çalıştır*:** Bölüm 0–7 çalışır: seçim doğrulanır, deneyler ve doğrulama yapılır, 5. yöntem seçilir,
   `final_pipeline.json` ve `test_predictions_locked.csv` yazılır. Bölüm 8'deki kontrol notebook'u **durdurur** ve
   `kilit_commit.zip` dosyasını indirir. Bu zip'in içeriği GitHub'a **kilit commit'i** olarak gönderilir.
2. **2. aşama – yeni Colab oturumunda yine *Tümünü çalıştır*:** Kilit dosyaları commit edildiği için kontrol geçer. Yeniden üretilen
   tahminlerin kilitlenenlerle birebir aynı olduğu doğrulanır. Ardından test (Bölüm 9) ve zamansal analiz (Bölüm 10) çalışır.
   Bölüm 11, `test_commit.zip` dosyasını indirir; bu da **test commit'i** olarak gönderilir.

Test referansları (sekans 02) kodla korunur: kilit dosyası yoksa ya da commit edilmemişse okunamaz.

**Tek komutla çalıştırma (alternatif):** Colab'da boş bir notebook'ta şu hücre, repoyu temiz klonlayıp `main_grup.ipynb`'nin bütün hücrelerini aynı sırayla çalıştırır (`calistir.py`):
```python
%cd /content
!rm -rf goruntu-isleme-hucre-sayimi-grup-odevi
!git clone -q https://github.com/James007Bond-code/goruntu-isleme-hucre-sayimi-grup-odevi.git
%cd goruntu-isleme-hucre-sayimi-grup-odevi
!python calistir.py
```
Rapor şekilleri yalnızca `python rapor_sekilleri.py` ile de üretilebilir (veri görüntüsü içeren şekiller `figures_report.zip` olarak oluşur, GitHub'a yüklenmez).

- Ortak kod `src/` altındadır: `config.py` (üyeler, seed'ler, yollar), `data.py`, `selection.py`, `pipeline.py`
  (tek `run_pipeline` fonksiyonu), `evaluation.py` (metrikler, deney tabloları, kilit), `experiments/<üye>.py`.
- `python select_frames.py` seçimi yeniden üretir ve kayıtlı seçimle aynı olduğunu doğrular.
- **Veri seti:** https://data.celltrackingchallenge.net/training-datasets/Fluo-N2DH-GOWT1.zip. **Veri seti bu repoda yer almaz.**
- Notebook GitHub'a **çıktıları temizlenmiş** olarak yüklenir. Veri görüntüsü içeren şekiller `figures_report/` klasörüne
  yazılır ve yalnızca raporda kullanılır (`.gitignore`).

## Commit düzeni
| # | Commit | İçerik |
|---|---|---|
| 1 | Seçim | `src/`, `select_frames.py`, `seeds/*/selected_frames.csv`, `results/seed_overlap.csv` |
| 2 | Üye deneyleri | Her üye `src/experiments/<üye>.py` dosyasını kendi branch'inde geliştirir ve PR açar |
| 3 | 🔒 Kilit | `kilit_commit.zip` içeriği: deney ve doğrulama tabloları, `final_pipeline.json`, `test_predictions_locked.csv` |
| 4 | Test | `test_commit.zip` içeriği: `test_results.csv`, `test_summary.csv`, zamansal analiz, grafikler |

## Üretilen dosyalar
Ödevin (Bölüm 18.2) istediği dosyalar repo kökündedir ve 4 seed'i birlikte içerir:

| Dosya | İçerik |
|---|---|
| `main_grup.ipynb` | Bütün çalışmayı yapan tek notebook |
| `data_overview.csv` | Tüm karelerin boyut, tip ve yoğunluk istatistikleri |
| `selected_frames.csv` | 4 seed'in seçilen kareleri (Tablo 1; referans sayısı içermez) |
| `dev_val_references.csv` | Geliştirme/doğrulama referans hücre sayıları |
| `experiments.csv` | 4 üyenin bütün kontrollü deneyleri (Tablo 2) |
| `validation_results.csv` | 5. yöntem adaylarının 4 seed doğrulama sonuçları (Tablo 3) |
| `final_pipeline.json` | Kilitlenen bütün yöntemler ve seçim kuralı |
| `test_predictions_locked.csv` | Referanslar okunmadan kaydedilen test tahminleri (60 kare) |
| `test_results.csv`, `test_summary.csv` | Test sonuçları (Tablo 4) ve özet metrikler (Tablo 5) |

Ek dosyalar:

| Dosya | İçerik |
|---|---|
| `seeds/<seed>/` | Seed bazında seçim, referanslar, üyenin deneyleri, doğrulaması ve yöntemi (`method_<üye>.json`) |
| `results/seed_overlap.csv`, `dev_pool_method5.csv` | Seed'ler arası çakışmalar ve 5. yöntemin geliştirme havuzu |
| `results/cross_seed_validation.csv` | Çapraz seed doğrulama matrisi |
| `results/thresholding_seed14048_individual.csv` | Sabit eşik (T=45), Otsu ve adaptif eşiğin aynı ön işlemeyle (CLAHE + Gauss 5×5) karşılaştırması. Kaynak: bireysel çalışma, seed 14048'in aynı geliştirme kareleri, kilit öncesi |
| `results/morphology_seed14048_individual.csv` | Tek başına erosion, dilation, opening, closing ve SE boyutu karşılaştırması. Kaynak: bireysel çalışma ([ayrı repo](https://github.com/James007Bond-code/goruntu-isleme-hucre-sayimi-254312022-suleymanBalsak)), seed 14048'in aynı geliştirme kareleri, aynı pipeline kodu, kilit öncesi |
| `results/method5_tuning_pool.csv` | 5. yöntemin ortak havuzdaki parametre taraması |
| `results/validation_vs_test.csv`, `temporal_analysis.csv` | Doğrulama/test karşılaştırması ve zamansal analiz |
| `figures/` | Veri görüntüsü içermeyen grafikler: Şekil 1 (akış diyagramı), deneyler, çapraz seed matrisi, Şekil 5 (zamansal) |
| `rapor_sekilleri.py` | Rapor şekilleri (Şekil 1–4, 6 ve sekans kayması). Kilitli yöntemleri kullanır, sonuç değiştirmez. Veri görüntüsü içeren şekiller `figures_report/` klasörüne yazılır ve GitHub'a yüklenmez |

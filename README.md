# Klasik Görüntü İşleme ile Hücre Segmentasyonu ve Sayımı – Grup Çalışması (Fluo-N2DH-GOWT1)

Cell Tracking Challenge **Fluo-N2DH-GOWT1** eğitim verisinde klasik görüntü işleme yöntemleriyle
hücre segmentasyonu, sayımı ve zamansal sayım analizi. Derin öğrenme kullanılmamıştır.

**Ders:** Görüntü İşleme – Yüksek Lisans Ara Sınav Projesi · **Ders sorumlusu:** Gökalp Tulum

## Hazırlayanlar, seed'ler ve yöntem aileleri
Seed kuralı (ödev Bölüm 3): öğrenci numarasının son 5 hanesi + 2026.

| Üye | Öğrenci no | Seed | Yöntem ailesi | Notebook |
|---|---|---|---|---|
| Süleyman Balsak | 254312022 | **14048** (temel) | CLAHE + Gauss + adaptif eşik + bağlı bileşen | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/James007Bond-code/goruntu-isleme-hucre-sayimi-grup-odevi/blob/main/notebooks/1_suleyman_14048.ipynb) `1_suleyman_14048.ipynb` |
| Seda Erten | 254312008 | 14034 | Yoğunluk dönüşümleri + median/bilateral filtre + Otsu | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/James007Bond-code/goruntu-isleme-hucre-sayimi-grup-odevi/blob/main/notebooks/2_seda_14034.ipynb) `2_seda_14034.ipynb` |
| İlkin Urcan | 244329078 | 31104 | Morfoloji + distance transform + watershed (temas eden hücreleri ayırma) | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/James007Bond-code/goruntu-isleme-hucre-sayimi-grup-odevi/blob/main/notebooks/3_ilkin_31104.ipynb) `3_ilkin_31104.ipynb` |
| Aslıhan Semiz Varlı | 254329024 | 31050 | K-means segmentasyonu + LoG blob tespiti | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/James007Bond-code/goruntu-isleme-hucre-sayimi-grup-odevi/blob/main/notebooks/4_aslihan_31050.ipynb) `4_aslihan_31050.ipynb` |

Ortak bölüm: [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/James007Bond-code/goruntu-isleme-hucre-sayimi-grup-odevi/blob/main/notebooks/5_cross_seed.ipynb) `notebooks/5_cross_seed.ipynb` dosyasında çapraz seed analizi, **5. yöntem** (dayanıklı pipeline), kilit, test ve zamansal analiz yapılır.

## Çalışmanın sorusu
Bireysel ödevde nihai pipeline tek bir rastgele kare seçimine göre belirlenir. Bu grup çalışmasında
**4 farklı seed** (4 farklı geliştirme/doğrulama/test bölünmesi) ve **4 farklı yöntem ailesi** kullanılır.
Böylece bir yöntemin başarısının kare seçimine ne kadar bağlı olduğu ölçülür. **5. yöntem**, 4 seed'in hepsinde
düşük ve birbirine yakın hata veren pipeline olarak seçilir.

## Akış
1. **Seçim** (`select_frames.py`): 4 seed için kareler, yöntem geliştirmeden önce seçilip ilk commit ile kaydedilir.
2. **Üye notebook'ları:** Her üye kendi seed'inin geliştirme kümesinde kontrollü deneyler yapar, en iyi 3 adayı kendi
   doğrulama kümesinde karşılaştırır ve yöntemini `seeds/<seed>/method_<üye>.json` dosyasına yazar.
3. **Çapraz seed matrisi:** 4 üye yöntemi ve baseline, 4 seed'in doğrulama kümelerinde değerlendirilir.
4. **5. yöntem:** Birleşik adaylar ortak geliştirme havuzunda ayarlanır; 4 üye yöntemi ve medyan topluluğu ile birlikte
   karşılaştırılır. **Seçim kuralı önceden sabittir:** 4 seed doğrulama MAE ortalaması en düşük olan seçilir.
   Eşitlikte sırasıyla seed'ler arası standart sapma, RMSE, karmaşıklık ve süreye bakılır.
5. 🔒 **Kilit:** Baseline, 4 üye yöntemi ve 5. yöntem, 60 test karesinde (4 seed × 15) referanslar okunmadan tahmin edilir
   ve **ayrı bir commit** ile kaydedilir.
6. **Test ve zamansal analiz:** Referanslar ilk kez kilitten sonra okunur.

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
1. Google Colab'da notebook'u açın. İlk hücre repoyu klonlar, ikinci hücre veri setini resmî adresten `data/` klasörüne indirir.
   Yerelde çalıştırmak için `pip install -r requirements.txt` yeterlidir.
2. Çalıştırma sırası:
   - `python select_frames.py` (seçim zaten kayıtlıdır; komut yalnızca aynı sonucu verdiğini doğrular)
   - `notebooks/1_…` – `4_…` (her üye kendi notebook'unu çalıştırır, sıra önemli değildir)
   - `notebooks/5_cross_seed.ipynb` → **kilit hücresinden sonra commit**, ardından test bölümleri
3. Ortak kod `src/` altındadır: `config.py` (seed'ler, yollar), `data.py`, `selection.py`, `pipeline.py`
   (tek `run_pipeline` fonksiyonu), `evaluation.py` (metrikler, deney tabloları, kilit).

- **Veri seti:** https://data.celltrackingchallenge.net/training-datasets/Fluo-N2DH-GOWT1.zip. **Veri seti bu repoda yer almaz.**
- Notebook'lar GitHub'a **çıktıları temizlenmiş** olarak yüklenir. Veri görüntüsü içeren şekiller `figures_report/` klasörüne
  yazılır ve yalnızca raporda kullanılır (`.gitignore`).

## Commit düzeni
| # | Commit | İçerik |
|---|---|---|
| 1 | Seçim | `src/`, `select_frames.py`, `seeds/*/selected_frames.csv`, `results/seed_overlap.csv` |
| 2 | Üye deneyleri | `seeds/<seed>/experiments_*`, `validation_*`, `method_*.json` (her üye kendi branch'i + PR) |
| 3 | 🔒 Kilit | `results/final_pipeline.json`, `results/test_predictions_locked.csv`, çapraz seed ve 5. yöntem tabloları |
| 4 | Test | `results/test_results.csv`, `test_summary.csv`, `temporal_analysis.csv`, grafikler |

## Üretilen dosyalar
| Dosya | İçerik |
|---|---|
| `seeds/<seed>/selected_frames.csv` | Seçilen kareler, gruplar, test blokları (referans sayısı içermez) |
| `seeds/<seed>/dev_val_references.csv` | Geliştirme/doğrulama referans hücre sayıları |
| `seeds/<seed>/experiments_<üye>.csv` | Üyenin kontrollü deneyleri (Tablo 2'nin parçası) |
| `seeds/<seed>/validation_<üye>.csv` | Üyenin 3 adayının doğrulama sonuçları |
| `seeds/<seed>/method_<üye>.json` | Üyenin seçtiği yöntem (konfigürasyon + histogram matching referansı) |
| `results/seed_overlap.csv` | Seed'ler arası kare çakışmaları |
| `results/dev_pool_method5.csv` | 5. yöntemin ortak geliştirme havuzu |
| `results/cross_seed_validation.csv` | Çapraz seed doğrulama matrisi |
| `results/method5_tuning_pool.csv`, `method5_selection.csv` | 5. yöntemin ayarı ve seçimi (Tablo 3) |
| `results/final_pipeline.json` | Kilitlenen bütün yöntemler ve seçim kuralı |
| `results/test_predictions_locked.csv` | Referanslar okunmadan kaydedilen test tahminleri |
| `results/test_results.csv`, `test_summary.csv` | Test sonuçları (Tablo 4) ve özet metrikler (Tablo 5) |
| `results/temporal_analysis.csv`, `figures/fig5_temporal_<seed>.png` | Zamansal analiz |

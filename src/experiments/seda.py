"""Seda Erten – deney listesi.

Yöntem ailesi: Yoğunluk dönüşümü ve filtre odaklı: stretching / HE / histogram matching + median/bilateral + Otsu

Her deney referans deneyden TEK bir faktörle ayrılır. Yeni deney eklemek için listeye satır ekleyin:
    (id, açıklama, referans_id, değişen_faktör, konfigürasyon)
Konfigürasyon anahtarları için bkz. src/pipeline.py.
"""
from ..pipeline import BASELINE, E11_SULEYMAN, make  # noqa: F401

FAMILY = "Yoğunluk dönüşümü ve filtre odaklı: stretching / HE / histogram matching + median/bilateral + Otsu"

E_REF = make(BASELINE, intensity="stretch", stretch_p=(1, 99.8))
EXPERIMENTS = [
    ("D01", "Baseline: orijinal + Otsu + CC", "-", "-", BASELINE),
    ("D02", "Contrast stretching (1–99.8%)", "D01", "yoğunluk", E_REF),
    ("D03", "Histogram equalization", "D01", "yoğunluk", make(BASELINE, intensity="hist_eq")),
    ("D04", "Histogram matching (ref: kendi dev)", "D01", "yoğunluk", make(BASELINE, intensity="hist_match")),
    ("D05", "Stretch + Median 3×3", "D02", "filtre", make(E_REF, filter="median", filter_k=3)),
    ("D06", "Stretch + Median 5×5", "D02", "filter_k", make(E_REF, filter="median", filter_k=5)),
    ("D07", "Stretch + Bilateral 7 (σ=50)", "D02", "filtre", make(E_REF, filter="bilateral", filter_k=7, bil_sigma=50)),
    ("D08", "Stretch + keskinleştirme", "D02", "filtre", make(E_REF, filter="sharpen")),
    ("D09", "Stretch + Median 5×5 + Opening 5×5", "D06", "morfoloji", make(E_REF, filter="median", filter_k=5, morph="opening", morph_k=5)),
    # TODO (Seda): stretch yüzdelikleri, HM referans seçimi ve median + closing gibi deneylerle genişlet
]

"""Süleyman Balsak – deney listesi.

Yöntem ailesi: CLAHE + Gauss + adaptif eşik + bağlı bileşen (bireysel çalışmadaki E11'in ailesi)

Her deney referans deneyden TEK bir faktörle ayrılır. Yeni deney eklemek için listeye satır ekleyin:
    (id, açıklama, referans_id, değişen_faktör, konfigürasyon)
Konfigürasyon anahtarları için bkz. src/pipeline.py.
"""
from ..pipeline import BASELINE, E11_SULEYMAN, make  # noqa: F401

FAMILY = "CLAHE + Gauss + adaptif eşik + bağlı bileşen (bireysel çalışmadaki E11'in ailesi)"

E_REF = make(E11_SULEYMAN)                       # bireysel çalışmanın nihai pipeline'ı
EXPERIMENTS = [
    # (id, açıklama, referans, değişen faktör, konfigürasyon)
    ("S01", "Baseline: orijinal + Otsu + CC", "-", "-", BASELINE),
    ("S02", "E11: CLAHE3 + Gauss5 + Adaptif(71,-12) + CC", "S01", "pipeline", E_REF),
    ("S03", "Adaptif blok=51", "S02", "adapt_block", make(E_REF, adapt_block=51)),
    ("S04", "Adaptif blok=91", "S02", "adapt_block", make(E_REF, adapt_block=91)),
    ("S05", "Adaptif C=-8", "S02", "adapt_c", make(E_REF, adapt_c=-8)),
    ("S06", "Adaptif C=-16", "S02", "adapt_c", make(E_REF, adapt_c=-16)),
    ("S07", "CLAHE clip=2.0", "S02", "clahe_clip", make(E_REF, clahe_clip=2.0)),
    ("S08", "Gauss 3×3", "S02", "filter_k", make(E_REF, filter_k=3)),
    # TODO (Süleyman): min_area, CLAHE grid ve adaptif + opening gibi deneylerle genişlet
]

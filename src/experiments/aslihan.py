"""Aslıhan Semiz Varlı – deney listesi.

Yöntem ailesi: K-means kümeleme segmentasyonu ve LoG (Laplacian of Gaussian) blob tespiti ile sayım

Her deney referans deneyden TEK bir faktörle ayrılır. Yeni deney eklemek için listeye satır ekleyin:
    (id, açıklama, referans_id, değişen_faktör, konfigürasyon)
Konfigürasyon anahtarları için bkz. src/pipeline.py.
"""
from ..pipeline import BASELINE, E11_SULEYMAN, make  # noqa: F401

FAMILY = "K-means kümeleme segmentasyonu ve LoG (Laplacian of Gaussian) blob tespiti ile sayım"

E_REF = make(BASELINE, intensity="clahe", clahe_clip=3.0, clahe_grid=[8, 8], filter="gaussian", filter_k=5)
EXPERIMENTS = [
    ("K01", "Baseline: orijinal + Otsu + CC", "-", "-", BASELINE),
    ("K02", "CLAHE + Gauss5 + K-means(k=2) + CC", "K01", "segmentasyon", make(E_REF, segmentation="kmeans", kmeans_k=2)),
    ("K03", "K-means k=3", "K02", "kmeans_k", make(E_REF, segmentation="kmeans", kmeans_k=3)),
    ("K04", "K-means k=4", "K02", "kmeans_k", make(E_REF, segmentation="kmeans", kmeans_k=4)),
    ("K05", "K-means k=3 + Opening 5×5", "K03", "morfoloji", make(E_REF, segmentation="kmeans", kmeans_k=3, morph="opening", morph_k=5)),
    ("K06", "LoG blob (σ 6–16, eşik 0.05), maskesiz", "K01", "sayım yöntemi", make(E_REF, segmentation="none", separation="log")),
    ("K07", "LoG eşik 0.10", "K06", "log_thresh", make(E_REF, segmentation="none", separation="log", log_thresh=0.10)),
    ("K08", "LoG σ 8–20", "K06", "log_sigma", make(E_REF, segmentation="none", separation="log", log_min_sigma=8, log_max_sigma=20)),
    ("K09", "Otsu maskesi içindeki LoG blob'ları", "K06", "maske", make(E_REF, segmentation="otsu", separation="log")),
    # TODO (Aslıhan): k-means + watershed ve LoG num_sigma gibi deneylerle genişlet
]

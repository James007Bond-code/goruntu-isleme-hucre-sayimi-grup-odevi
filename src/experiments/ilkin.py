"""İlkin Urcan – deney listesi.

Yöntem ailesi: Morfoloji + distance transform + watershed ile birbirine değen hücrelerin ayrılması

Her deney referans deneyden TEK bir faktörle ayrılır. Yeni deney eklemek için listeye satır ekleyin:
    (id, açıklama, referans_id, değişen_faktör, konfigürasyon)
Konfigürasyon anahtarları için bkz. src/pipeline.py.
"""
from ..pipeline import BASELINE, E11_SULEYMAN, make  # noqa: F401

FAMILY = "Morfoloji + distance transform + watershed ile birbirine değen hücrelerin ayrılması"

E_REF = make(BASELINE, intensity="clahe", clahe_clip=3.0, clahe_grid=[8, 8], filter="gaussian", filter_k=5,
             morph="open_close", morph_k=5, min_area=150)
EXPERIMENTS = [
    ("W01", "Baseline: orijinal + Otsu + CC", "-", "-", BASELINE),
    ("W02", "CLAHE + Gauss5 + Otsu + Open→Close 5×5 + CC", "W01", "pipeline", E_REF),
    ("W03", "W02 + watershed (min_dist=16)", "W02", "ayırma", make(E_REF, separation="watershed", ws_min_dist=16)),
    ("W04", "Watershed min_dist=10", "W03", "ws_min_dist", make(E_REF, separation="watershed", ws_min_dist=10)),
    ("W05", "Watershed min_dist=22", "W03", "ws_min_dist", make(E_REF, separation="watershed", ws_min_dist=22)),
    ("W06", "Close→Open (sıra) + watershed", "W03", "morfoloji sırası", make(E_REF, morph="close_open", separation="watershed", ws_min_dist=16)),
    ("W07", "SE 3×3 + watershed", "W03", "SE boyutu", make(E_REF, morph_k=3, separation="watershed", ws_min_dist=16)),
    ("W08", "Erosion 5×5 + CC (ayırma için aşındırma)", "W02", "morfoloji", make(E_REF, morph="erosion")),
    ("W09", "Adaptif(71,-12) + watershed", "W03", "segmentasyon", make(E_REF, segmentation="adaptive", adapt_block=71, adapt_c=-12, morph="none", min_area=100, separation="watershed", ws_min_dist=16)),
    ("W10", "Close→Open SE 7×7 + watershed", "W06", "SE boyutu", make(E_REF, morph="close_open", morph_k=7, separation="watershed", ws_min_dist=16)),
    ("W11", "Close→Open + watershed min_dist=14", "W06", "ws_min_dist", make(E_REF, morph="close_open", separation="watershed", ws_min_dist=14)),
    ("W12", "Close→Open + watershed min_dist=18", "W06", "ws_min_dist", make(E_REF, morph="close_open", separation="watershed", ws_min_dist=18)),
    ("W13", "Adaptif + Opening 5×5 + watershed (W09 düzeltmesi)", "W09", "morfoloji", make(E_REF, segmentation="adaptive", adapt_block=71, adapt_c=-12, morph="opening", morph_k=5, min_area=100, separation="watershed", ws_min_dist=16)),
]

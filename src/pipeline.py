"""Tek fonksiyonla bütün konfigürasyonları çalıştıran klasik görüntü işleme pipeline'ı.

Sıra: yoğunluk dönüşümü -> uzamsal filtre -> segmentasyon -> morfoloji -> nesne ayırma/sayım.

Konfigürasyon anahtarları (varsayılanlar parantez içinde):
  intensity    : none | stretch | hist_eq | clahe | hist_match         (none)
                 stretch_p=(1, 99.8), clahe_clip=3.0, clahe_grid=[8, 8]
  filter       : none | gaussian | median | sharpen | bilateral        (none)
                 filter_k=3, bil_sigma=50
  segmentation : fixed | otsu | adaptive | kmeans | none               (otsu)
                 fixed_thresh=20, adapt_block=51, adapt_c=-5, kmeans_k=3
  morph        : none | erosion | dilation | opening | closing | open_close | close_open
                 morph_k=3
  separation   : cc | watershed | log                                   (cc)
                 min_area=150, ws_min_dist=14,
                 log_min_sigma=6, log_max_sigma=16, log_num_sigma=6, log_thresh=0.05
                 ('log' = Laplacian of Gaussian blob tespiti; ikili maske varsa blob merkezleri
                  maske içinde olanlar sayılır, segmentation=none ise maske kullanılmaz)
"""
import time

import cv2
import numpy as np
from scipy import ndimage
from skimage.feature import blob_log, peak_local_max
from skimage.segmentation import watershed

_KMEANS_CRITERIA = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5)


def match_histograms_uint8(source, template):
    _, bin_idx, src_counts = np.unique(source.ravel(), return_inverse=True, return_counts=True)
    tmpl_values, tmpl_counts = np.unique(template.ravel(), return_counts=True)
    src_q = np.cumsum(src_counts).astype(np.float64) / source.size
    tmpl_q = np.cumsum(tmpl_counts).astype(np.float64) / template.size
    return np.interp(src_q, tmpl_q, tmpl_values)[bin_idx].reshape(source.shape).astype(np.uint8)


def filter_by_area(label_img, min_area):
    """min_area'dan küçük nesneleri siler, kalanları 1..N olarak yeniden etiketler."""
    areas = np.bincount(label_img.ravel())
    keep = np.nonzero(areas >= min_area)[0]
    keep = keep[keep != 0]
    lut = np.zeros(len(areas), dtype=np.int32)
    lut[keep] = np.arange(1, len(keep) + 1)
    return lut[label_img], len(keep)


def kmeans_binary(img, k=3):
    """Yoğunluk değerlerini k kümeye ayırır; en parlak küme ön plan kabul edilir.

    Deterministik olması için başlangıç merkezleri yüzdeliklerden verilir (KMEANS_USE_INITIAL_LABELS).
    """
    data = img.reshape(-1, 1).astype(np.float32)
    qs = np.percentile(data, np.linspace(5, 99, k))
    init = np.argmin(np.abs(data - qs[None, :]), axis=1).astype(np.int32).reshape(-1, 1)
    _, labels, centers = cv2.kmeans(data, k, init, _KMEANS_CRITERIA, 1, cv2.KMEANS_USE_INITIAL_LABELS)
    fg = int(np.argmax(centers.ravel()))
    return ((labels.ravel() == fg).reshape(img.shape) * 255).astype(np.uint8)


def run_pipeline(img, config, hm_ref=None, return_stages=False):
    t0 = time.perf_counter()
    stages = {}
    proc = img.copy()

    # 1) Yoğunluk dönüşümü
    inten = config.get("intensity", "none")
    if inten == "stretch":
        p_low, p_high = np.percentile(proc, config.get("stretch_p", (1, 99.8)))
        proc = np.clip((proc - p_low) * 255.0 / (p_high - p_low + 1e-5), 0, 255).astype(np.uint8)
    elif inten == "hist_eq":
        proc = cv2.equalizeHist(proc)
    elif inten == "clahe":
        proc = cv2.createCLAHE(clipLimit=config.get("clahe_clip", 3.0),
                               tileGridSize=tuple(config.get("clahe_grid", [8, 8]))).apply(proc)
    elif inten == "hist_match":
        if hm_ref is None:
            raise ValueError("hist_match için geliştirme kümesinden bir hm_ref görüntüsü verilmelidir.")
        proc = match_histograms_uint8(proc, hm_ref)
    stages["intensity"] = proc

    # 2) Uzamsal filtre
    filt, k = config.get("filter", "none"), config.get("filter_k", 3)
    if filt == "gaussian":
        proc = cv2.GaussianBlur(proc, (k, k), 0)
    elif filt == "median":
        proc = cv2.medianBlur(proc, k)
    elif filt == "sharpen":
        kernel_sharp = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], dtype=np.float32)
        proc = cv2.filter2D(proc, -1, kernel_sharp)
    elif filt == "bilateral":
        s = config.get("bil_sigma", 50)
        proc = cv2.bilateralFilter(proc, k, s, s)
    stages["filtered"] = proc

    # 3) Segmentasyon
    seg = config.get("segmentation", "otsu")
    if seg == "fixed":
        _, binary = cv2.threshold(proc, config.get("fixed_thresh", 20), 255, cv2.THRESH_BINARY)
    elif seg == "otsu":
        _, binary = cv2.threshold(proc, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    elif seg == "adaptive":
        binary = cv2.adaptiveThreshold(proc, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,
                                       config.get("adapt_block", 51), config.get("adapt_c", -5))
    elif seg == "kmeans":
        binary = kmeans_binary(proc, config.get("kmeans_k", 3))
    elif seg == "none":
        binary = None
    else:
        raise ValueError(f"Bilinmeyen segmentasyon: {seg}")
    stages["binary"] = binary

    # 4) Morfoloji
    morph, mk = config.get("morph", "none"), config.get("morph_k", 3)
    if binary is not None and morph != "none":
        se = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (mk, mk))
        ops = {"erosion": [("e",)], "dilation": [("d",)], "opening": [(cv2.MORPH_OPEN,)],
               "closing": [(cv2.MORPH_CLOSE,)], "open_close": [(cv2.MORPH_OPEN,), (cv2.MORPH_CLOSE,)],
               "close_open": [(cv2.MORPH_CLOSE,), (cv2.MORPH_OPEN,)]}[morph]
        for (op,) in ops:
            if op == "e":
                binary = cv2.erode(binary, se)
            elif op == "d":
                binary = cv2.dilate(binary, se)
            else:
                binary = cv2.morphologyEx(binary, op, se)
    stages["morph"] = binary

    # 5) Nesne ayırma + alan filtresi + sayım
    sep = config.get("separation", "cc")
    min_area = config.get("min_area", 150)
    labels = None
    if binary is not None:
        _, cc = cv2.connectedComponents(binary, connectivity=8)
        labels, count = filter_by_area(cc.astype(np.int32), min_area)

    if sep == "watershed":
        clean_bin = (labels > 0).astype(np.uint8) * 255
        dist = ndimage.distance_transform_edt(clean_bin)
        coords = peak_local_max(dist, min_distance=config.get("ws_min_dist", 14), labels=clean_bin)
        peaks = np.zeros(dist.shape, dtype=bool)
        peaks[tuple(coords.T)] = True
        markers, _ = ndimage.label(peaks)
        ws = watershed(-dist, markers, mask=clean_bin)
        labels, count = filter_by_area(ws.astype(np.int32), min_area)
        stages["distance"] = dist
    elif sep == "log":
        blobs = blob_log(proc.astype(np.float32) / 255.0,
                         min_sigma=config.get("log_min_sigma", 6), max_sigma=config.get("log_max_sigma", 16),
                         num_sigma=config.get("log_num_sigma", 6), threshold=config.get("log_thresh", 0.05))
        if labels is not None and len(blobs):
            inside = labels[blobs[:, 0].astype(int), blobs[:, 1].astype(int)] > 0
            blobs = blobs[inside]
        count = int(len(blobs))
        stages["blobs"] = blobs
        lbl = np.zeros(proc.shape, dtype=np.int32)
        for n, (y, x, s) in enumerate(blobs, 1):
            cv2.circle(lbl, (int(x), int(y)), max(1, int(s * np.sqrt(2))), int(n), -1)
        labels = lbl
    elif sep != "cc":
        raise ValueError(f"Bilinmeyen ayırma yöntemi: {sep}")
    elif labels is None:
        raise ValueError("separation='cc' için bir segmentasyon gerekir (segmentation='none' olamaz).")
    stages["labels"] = labels

    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    return (count, labels, elapsed_ms, stages) if return_stages else (count, labels, elapsed_ms)


def make(base, **changes):
    c = dict(base)
    c.update(changes)
    return c


def complexity(c):
    return sum([c.get("intensity", "none") != "none", c.get("filter", "none") != "none",
                c.get("segmentation", "otsu") != "none", c.get("morph", "none") != "none",
                c.get("separation", "cc") != "cc"]) + 1


def param_str(c):
    keys = ["stretch_p", "clahe_clip", "clahe_grid", "filter_k", "bil_sigma", "fixed_thresh", "adapt_block",
            "adapt_c", "kmeans_k", "morph_k", "ws_min_dist", "log_min_sigma", "log_max_sigma", "log_thresh",
            "min_area"]
    return ", ".join(f"{k}={c[k]}" for k in keys if k in c)


# Ortak baseline (ödev Bölüm 5) – bütün seed'lerde sabit
BASELINE = {"intensity": "none", "filter": "none", "segmentation": "otsu", "morph": "none",
            "separation": "cc", "min_area": 100}

# Bireysel çalışmanın (seed 14048) nihai pipeline'ı – Süleyman'ın yöntem ailesinin başlangıç noktası
E11_SULEYMAN = {"intensity": "clahe", "clahe_clip": 3.0, "clahe_grid": [8, 8], "filter": "gaussian",
                "filter_k": 5, "segmentation": "adaptive", "adapt_block": 71, "adapt_c": -12,
                "morph": "none", "separation": "cc", "min_area": 100}

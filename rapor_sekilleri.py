"""Teknik rapor için zorunlu şekilleri üretir (Ödev Bölüm 17). Kilitli yöntemleri kullanır, hiçbir sonucu değiştirmez.

    python rapor_sekilleri.py

Şekil 1  Nihai pipeline akış diyagramı                     -> figures/        (veri görüntüsü yok, GitHub'a gider)
Şekil 2  Yoğunluk dönüşümleri + histogramlar                -> figures_report/ (veri görüntüsü, GitHub'a GİTMEZ)
Şekil 3  Segmentasyon ve morfoloji karşılaştırması          -> figures_report/
Şekil 4  Nihai pipeline'ın aşama aşama çıktıları            -> figures_report/
Şekil 6  Başarılı / hatalı / zorlayıcı test örnekleri       -> figures_report/
Ek       Sekans 01 ve 02 arasındaki parlaklık farkı         -> figures_report/
Sonunda figures_report.zip oluşturulur.
"""
import json
import os
import sys
import zipfile

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402
from scipy import ndimage  # noqa: E402
from skimage.segmentation import find_boundaries  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from src import config as C  # noqa: E402
from src.pipeline import BASELINE, make, run_pipeline  # noqa: E402

DPI = 200
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})
os.makedirs(C.FIG_DIR, exist_ok=True)
os.makedirs(C.FIG_IMG_DIR, exist_ok=True)

FINAL = json.load(open(C.FINAL_PIPELINE_FILE, encoding="utf-8"))
M5 = FINAL["methods"]["M5"]["config"]

STEP_NAMES = {
    "intensity": {"clahe": lambda c: f"CLAHE\nclip={c.get('clahe_clip')}, grid={c.get('clahe_grid')}",
                  "stretch": lambda c: f"Contrast stretching\n{c.get('stretch_p')}",
                  "hist_eq": lambda c: "Histogram eşitleme", "hist_match": lambda c: "Histogram matching"},
    "filter": {"gaussian": lambda c: f"Gauss filtre\n{c.get('filter_k')}×{c.get('filter_k')}",
               "median": lambda c: f"Median filtre\n{c.get('filter_k')}×{c.get('filter_k')}",
               "sharpen": lambda c: "Keskinleştirme\n(3×3 Laplace)", "bilateral": lambda c: "Bilateral filtre"},
    "segmentation": {"otsu": lambda c: "Otsu eşikleme", "fixed": lambda c: f"Sabit eşik T={c.get('fixed_thresh')}",
                     "adaptive": lambda c: f"Adaptif Gauss eşik\nblok={c.get('adapt_block')}, C={c.get('adapt_c')}",
                     "kmeans": lambda c: f"K-means k={c.get('kmeans_k')}"},
    "morph": {"close_open": lambda c: f"Closing → Opening\nSE {c.get('morph_k')}×{c.get('morph_k')} (elips)",
              "open_close": lambda c: f"Opening → Closing\nSE {c.get('morph_k')}×{c.get('morph_k')} (elips)",
              "opening": lambda c: f"Opening {c.get('morph_k')}×{c.get('morph_k')}",
              "closing": lambda c: f"Closing {c.get('morph_k')}×{c.get('morph_k')}"},
}


def flow_steps(c):
    steps = ["Girdi görüntüsü\n(1024×1024, uint8)"]
    for key in ["intensity", "filter", "segmentation", "morph"]:
        v = c.get(key, "none")
        if v != "none" and v in STEP_NAMES[key]:
            steps.append(STEP_NAMES[key][v](c))
    if c.get("separation") == "watershed":
        steps.append(f"Distance transform +\nwatershed (min_dist={c.get('ws_min_dist')})")
    steps.append(f"Alan filtresi (≥ {c.get('min_area')} px)\n+ hücre sayımı")
    return steps


def fig1_flowchart():
    steps = flow_steps(M5)
    fig, ax = plt.subplots(figsize=(4.2, 1.05 * len(steps)))
    ax.set_xlim(0, 1); ax.set_ylim(0, len(steps)); ax.axis("off")
    for i, s in enumerate(steps):
        y = len(steps) - i - 0.5
        ax.add_patch(FancyBboxPatch((0.08, y - 0.32), 0.84, 0.64, boxstyle="round,pad=0.02",
                                    fc="#E3F2FD" if 0 < i < len(steps) - 1 else "#BBDEFB", ec="#1565C0", lw=1.2))
        ax.text(0.5, y, s, ha="center", va="center", fontsize=8.5)
        if i < len(steps) - 1:
            ax.annotate("", xy=(0.5, y - 0.5), xytext=(0.5, y - 0.33), arrowprops=dict(arrowstyle="-|>", color="#1565C0"))
    ax.set_title("Şekil 1 – Nihai pipeline (5. yöntem)", fontsize=10, fontweight="bold")
    plt.tight_layout(); plt.savefig(f"{C.FIG_DIR}/fig1_pipeline_flowchart.png", dpi=DPI); plt.close()
    print("Şekil 1 ->", f"{C.FIG_DIR}/fig1_pipeline_flowchart.png")


def show(ax, img, title, vmax=None):
    ax.imshow(img, cmap="gray", vmin=0, vmax=vmax if vmax is not None else max(1, np.percentile(img, 99.8)))
    ax.set_title(title, fontsize=8); ax.axis("off")


def overlay(ax, img, labels, title, gt_points=None):
    show(ax, img, title)
    if labels is not None:
        b = find_boundaries(labels, mode="outer")
        rgba = np.zeros((*b.shape, 4)); rgba[b] = (1, 0.85, 0, 1)
        ax.imshow(rgba)
    if gt_points is not None and len(gt_points):
        ax.plot(gt_points[:, 1], gt_points[:, 0], "+", color="#FF1744", ms=7, mew=1.5)


def gt_points(lbl):
    ids = np.unique(lbl)[1:]
    return np.array(ndimage.center_of_mass(lbl > 0, lbl, ids)) if len(ids) else np.zeros((0, 2))


def main():
    fig1_flowchart()
    if "--yalnizca-sekil1" in sys.argv:
        return

    from src.data import download_dataset, load_image, read_gt_labels
    download_dataset()
    sel = pd.read_csv(os.path.join(C.seed_dir(C.BASE_SEED), "selected_frames.csv"))
    dev0 = sel[sel.group == "Development"].iloc[0]
    img = load_image("01", dev0.filename)
    gt = read_gt_labels("01", dev0.frame_idx)
    n_gt = int(np.count_nonzero(np.unique(gt)))
    hm_ref = load_image("01", sel[sel.group == "Development"].iloc[1].filename)
    tag = f"seed {C.BASE_SEED}, geliştirme karesi {dev0.filename}, gerçek sayı {n_gt}"

    # ---------------- Şekil 2: yoğunluk dönüşümleri + histogramlar
    variants = [("Orijinal", {"intensity": "none"}),
                ("Contrast stretching (1–99.8%)", {"intensity": "stretch", "stretch_p": [1, 99.8]}),
                ("Histogram eşitleme", {"intensity": "hist_eq"}),
                ("CLAHE (clip 3, 8×8)", {"intensity": "clahe", "clahe_clip": 3.0, "clahe_grid": [8, 8]}),
                ("Histogram matching", {"intensity": "hist_match"})]
    fig, axes = plt.subplots(2, len(variants), figsize=(3.1 * len(variants), 6), layout="constrained")
    for j, (name, cfg) in enumerate(variants):
        cnt, _, _, st = run_pipeline(img, make(BASELINE, **cfg), hm_ref=hm_ref, return_stages=True)
        im = st["intensity"]
        show(axes[0, j], im, f"{name}\nOtsu+CC sayım: {cnt}", vmax=255 if cfg["intensity"] != "none" else None)
        axes[1, j].hist(im.ravel(), bins=128, range=(0, 255), color="#1E88E5", log=True)
        axes[1, j].set_xlabel("Yoğunluk"); axes[1, j].grid(alpha=0.3)
    axes[1, 0].set_ylabel("Piksel sayısı (log)")
    fig.suptitle(f"Şekil 2 – Yoğunluk dönüşümleri ve histogramları ({tag})", fontsize=10, fontweight="bold")
    plt.savefig(f"{C.FIG_IMG_DIR}/fig2_intensity_transforms.png", dpi=DPI); plt.close()
    print("Şekil 2 hazır")

    # ---------------- Şekil 3: segmentasyon ve morfoloji karşılaştırması
    pre = {"intensity": "clahe", "clahe_clip": 3.0, "clahe_grid": [8, 8], "filter": "gaussian", "filter_k": 5, "min_area": 150}
    seg_rows = [
        ("Sabit eşik T=45", make(pre, segmentation="fixed", fixed_thresh=45)),
        ("Otsu", make(pre, segmentation="otsu")),
        ("Adaptif (71, −12)", make(pre, segmentation="adaptive", adapt_block=71, adapt_c=-12, min_area=100)),
        ("K-means k=2", make(pre, segmentation="kmeans", kmeans_k=2)),
        ("Otsu + Opening 5×5", make(pre, segmentation="otsu", morph="opening", morph_k=5)),
        ("Otsu + Close→Open 5×5", make(pre, segmentation="otsu", morph="close_open", morph_k=5)),
        ("Otsu + Close→Open + watershed", make(pre, segmentation="otsu", morph="close_open", morph_k=5,
                                               separation="watershed", ws_min_dist=16)),
        ("Adaptif + watershed (aşırı bölütleme)", make(pre, segmentation="adaptive", adapt_block=71, adapt_c=-12,
                                                        min_area=100, separation="watershed", ws_min_dist=16)),
    ]
    fig, axes = plt.subplots(2, 4, figsize=(13, 6.8), layout="constrained")
    for ax, (name, cfg) in zip(axes.ravel(), seg_rows):
        cnt, lbl, _ = run_pipeline(img, cfg)
        overlay(ax, img, lbl, f"{name}\nsayım {cnt} / gerçek {n_gt}", gt_points(gt))
    fig.suptitle(f"Şekil 3 – Segmentasyon, morfoloji ve nesne ayırma ({tag}; sarı: tespit sınırı, kırmızı +: TRA işaretçisi)",
                 fontsize=10, fontweight="bold")
    plt.savefig(f"{C.FIG_IMG_DIR}/fig3_segmentation_morphology.png", dpi=DPI); plt.close()
    print("Şekil 3 hazır")

    # ---------------- Şekil 4: nihai pipeline aşama aşama
    cnt, lbl, _, st = run_pipeline(img, M5, return_stages=True)
    panels = [(img, "1) Girdi", None), (st["intensity"], "2) CLAHE", 255), (st["filtered"], "3) Gauss 5×5", 255),
              (st["binary"], "4) Otsu ikili maske", 255), (st["morph"], "5) Close→Open 5×5", 255),
              (st["distance"], "6) Distance transform", None)]
    fig, axes = plt.subplots(2, 4, figsize=(13, 6.8), layout="constrained")
    for ax, (im, t, vm) in zip(axes.ravel()[:6], panels):
        if t.startswith("6"):
            ax.imshow(im, cmap="magma"); ax.set_title(t, fontsize=8); ax.axis("off")
        else:
            show(ax, im, t, vmax=vm)
    rng = np.random.default_rng(0)
    cmap = np.vstack([[0, 0, 0], rng.uniform(0.25, 1, (lbl.max() + 1, 3))])
    axes.ravel()[6].imshow(cmap[lbl]); axes.ravel()[6].set_title(f"7) Watershed etiketleri: {cnt} nesne", fontsize=8)
    axes.ravel()[6].axis("off")
    overlay(axes.ravel()[7], img, lbl, f"8) Sonuç: sayım {cnt} / gerçek {n_gt}", gt_points(gt))
    fig.suptitle(f"Şekil 4 – Nihai pipeline'ın aşama aşama çıktıları ({tag})", fontsize=10, fontweight="bold")
    plt.savefig(f"{C.FIG_IMG_DIR}/fig4_final_pipeline_stages.png", dpi=DPI); plt.close()
    print("Şekil 4 hazır")

    # ---------------- Şekil 6: başarılı / hatalı / zorlayıcı test örnekleri (kilit sonrası)
    res = pd.read_csv("test_results.csv")
    res["M5_err"] = res["M5_pred"] - res["gt_count"]
    uniq = res.drop_duplicates("frame_idx")
    best = uniq.loc[uniq["M5_err"].abs().idxmin()]
    worst = uniq.loc[uniq["M5_err"].abs().idxmax()]
    gain = (uniq["baseline_pred"] - uniq["gt_count"]).abs() - uniq["M5_err"].abs()
    hard = uniq.drop([best.name, worst.name]).loc[gain.drop([best.name, worst.name]).idxmax()]
    cases = [("Başarılı", best), ("En hatalı", worst), ("Zorlayıcı: baseline'ın en çok yanıldığı", hard)]
    fig, axes = plt.subplots(len(cases), 2, figsize=(9, 4.3 * len(cases)), layout="constrained")
    for i, (name, r) in enumerate(cases):
        im = load_image("02", r.filename)
        g = read_gt_labels("02", r.frame_idx, lock_file=C.LOCK_FILE)
        b_cnt, b_lbl, _ = run_pipeline(im, FINAL["methods"]["baseline"]["config"])
        f_cnt, f_lbl, _ = run_pipeline(im, M5)
        assert f_cnt == r.M5_pred and b_cnt == r.baseline_pred, "Kilitli tahminlerle uyuşmazlık!"
        overlay(axes[i, 0], im, b_lbl, f"{name} – {r.filename} (seed {r.seed})\nBaseline: {b_cnt} / gerçek {r.gt_count}", gt_points(g))
        overlay(axes[i, 1], im, f_lbl, f"Nihai pipeline: {f_cnt} / gerçek {r.gt_count}", gt_points(g))
    fig.suptitle("Şekil 6 – Test karelerinde başarılı, hatalı ve zorlayıcı örnekler\n(sarı: tespit sınırı, kırmızı +: TRA işaretçisi)",
                 fontsize=10, fontweight="bold")
    plt.savefig(f"{C.FIG_IMG_DIR}/fig6_success_failure_examples.png", dpi=DPI); plt.close()
    print("Şekil 6 hazır")

    # ---------------- Ek: sekanslar arası parlaklık farkı (testteki performans farkının nedeni)
    t0 = res.iloc[0]
    im2 = load_image("02", t0.filename)
    methods = FINAL["methods"]
    fig, axes = plt.subplots(2, 3, figsize=(12, 7.5), layout="constrained")
    show(axes[0, 0], img, f"Sekans 01 – {dev0.filename}", vmax=80); show(axes[1, 0], im2, f"Sekans 02 – {t0.filename}", vmax=80)
    for row, (im, seq) in enumerate([(img, "01"), (im2, "02")]):
        axes[row, 1].hist(im.ravel(), bins=100, range=(0, 100), color="#1E88E5" if seq == "01" else "#E53935", log=True)
        axes[row, 1].set_title(f"Sekans {seq} histogramı (ort. {im.mean():.2f}, p99 {np.percentile(im, 99):.0f})", fontsize=8)
        axes[row, 1].grid(alpha=0.3)
        txt = []
        for k in ["baseline", "M_suleyman", "M_seda", "M_ilkin", "M_aslihan", "M5"]:
            from src.evaluation import run_method
            txt.append(f"{k:11s}: {run_method(im, methods[k])[0]:3d}")
        n_true = int(np.count_nonzero(np.unique(gt if seq == '01' else read_gt_labels('02', t0.frame_idx, lock_file=C.LOCK_FILE))))
        axes[row, 2].text(0.05, 0.95, f"Gerçek sayı: {n_true}\n\n" + "\n".join(txt), va="top", family="monospace", fontsize=9)
        axes[row, 2].axis("off"); axes[row, 2].set_title("Yöntemlerin sayımları", fontsize=8)
    fig.suptitle("Ek Şekil – Sekans 01 ve 02 arasındaki parlaklık farkı (aynı gösterim aralığı: 0–80)", fontsize=10, fontweight="bold")
    plt.savefig(f"{C.FIG_IMG_DIR}/figA_sequence_shift.png", dpi=DPI); plt.close()
    print("Ek şekil hazır")

    with zipfile.ZipFile("figures_report.zip", "w") as z:
        for f in sorted(os.listdir(C.FIG_IMG_DIR)):
            z.write(os.path.join(C.FIG_IMG_DIR, f), f"figures_report/{f}")
        z.write(f"{C.FIG_DIR}/fig1_pipeline_flowchart.png", "figures_report/fig1_pipeline_flowchart.png")
    print("\nTAMAMLANDI → figures_report.zip (veri görüntüsü içerir: yalnızca rapor için, GitHub'a yüklemeyin)")


if __name__ == "__main__":
    main()

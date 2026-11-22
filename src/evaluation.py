"""Metrikler, deney/doğrulama tabloları ve test kilidi."""
import json
import os

import numpy as np
import pandas as pd

from .data import load_image
from .pipeline import complexity, param_str, run_pipeline

# ---------------------------------------------------------------- yöntem nesneleri
# Bir "yöntem" kendi kendine yeten bir sözlüktür; başka bir seed'de aynen çalıştırılabilir:
#   {"name": ..., "owner": ..., "config": {...}, "hm_ref": "t033.tif" | None}
#   {"name": ..., "ensemble": [yöntem, yöntem, ...], "agg": "median" | "mean"}
# hm_ref, histogram matching referansıdır ve yalnızca sahibinin GELİŞTİRME kümesinden seçilir.
_HM_CACHE = {}


def _hm_img(fname):
    if fname is None:
        return None
    if fname not in _HM_CACHE:
        _HM_CACHE[fname] = load_image("01", fname)
    return _HM_CACHE[fname]


def run_method(img, method):
    """-> (sayım, süre_ms)"""
    if "ensemble" in method:
        import time
        t0 = time.perf_counter()
        counts = [run_method(img, m)[0] for m in method["ensemble"]]
        agg = np.median if method.get("agg", "median") == "median" else np.mean
        return int(round(float(agg(counts)))), (time.perf_counter() - t0) * 1000.0
    cnt, _, ms = run_pipeline(img, method["config"], hm_ref=_hm_img(method.get("hm_ref")))
    return cnt, ms


def evaluate_method(df, method):
    preds, times = [], []
    for r in df.itertuples():
        c, ms = run_method(load_image(r.sequence, r.filename), method)
        preds.append(c)
        times.append(ms)
    m = count_metrics(preds, df["gt_count"].to_numpy())
    m.update({"Sure_ms": float(np.mean(times)), "preds": preds})
    return m


def method_complexity(method):
    if "ensemble" in method:
        return sum(method_complexity(m) for m in method["ensemble"])
    return complexity(method["config"])


def count_metrics(preds, gts):
    preds, gts = np.asarray(preds, float), np.asarray(gts, float)
    err = preds - gts
    return {"MAE": float(np.mean(np.abs(err))), "RMSE": float(np.sqrt(np.mean(err ** 2))),
            "Bias": float(np.mean(err)), "Exact_%": float(np.mean(err == 0) * 100)}


def evaluate(df, config, hm_ref=None):
    """df: sequence, filename, gt_count sütunlarını içerir."""
    preds, times = [], []
    for r in df.itertuples():
        cnt, _, dt = run_pipeline(load_image(r.sequence, r.filename), config, hm_ref=hm_ref)
        preds.append(cnt)
        times.append(dt)
    m = count_metrics(preds, df["gt_count"].to_numpy())
    m.update({"Sure_ms": float(np.mean(times)), "preds": preds})
    return m


def warmup(img):
    for cfg in [{"segmentation": "otsu"}, {"segmentation": "otsu", "separation": "watershed"},
                {"segmentation": "none", "separation": "log"}]:
        run_pipeline(img, cfg)


def run_experiments(experiments, dev_df, hm_ref=None, member=None, seed=None):
    """experiments: [(id, açıklama, referans_id, değişen_faktör, config), ...] -> (tablo, kare bazlı)"""
    rows, per_frame = [], []
    for eid, desc, ref, changed, cfg in experiments:
        m = evaluate(dev_df, cfg, hm_ref)
        rows.append({"Uye": member, "Seed": seed, "Deney_ID": eid, "Aciklama": desc, "Referans": ref,
                     "Degisen": changed, "Yogunluk": cfg.get("intensity", "none"),
                     "Filtre": cfg.get("filter", "none"), "Segmentasyon": cfg.get("segmentation", "otsu"),
                     "Morfoloji": cfg.get("morph", "none"), "Ayirma": cfg.get("separation", "cc"),
                     "Parametreler": param_str(cfg), "Dev_MAE": round(m["MAE"], 3),
                     "Dev_RMSE": round(m["RMSE"], 3), "Dev_Bias": round(m["Bias"], 3),
                     "Sure_ms": round(m["Sure_ms"], 1)})
        for r, p in zip(dev_df.itertuples(), m["preds"]):
            per_frame.append({"Deney_ID": eid, "filename": r.filename, "gt_count": r.gt_count, "pred": p})
    return pd.DataFrame(rows), pd.DataFrame(per_frame)


def rank_candidates(candidates, val_df, hm_ref=None):
    """candidates: {isim: config} (geliştirme sıralamasına göre sıralı).

    Seçim: en düşük doğrulama MAE; eşitlikte RMSE, karmaşıklık, sonra geliştirme sıralaması.
    Süre tabloda raporlanır ama eşitlik bozmada KULLANILMAZ: ölçülen süre çalıştırmadan
    çalıştırmaya değiştiği için seçimi tekrarlanamaz hale getirir.
    """
    rows = []
    for order, (name, cfg) in enumerate(candidates.items()):
        m = evaluate(val_df, cfg, hm_ref)
        rows.append({"Pipeline": name, "Validation_MAE": round(m["MAE"], 3),
                     "Validation_RMSE": round(m["RMSE"], 3), "Validation_Bias": round(m["Bias"], 3),
                     "Ortalama_Sure_ms": round(m["Sure_ms"], 1), "Karmasiklik": complexity(cfg),
                     "Parametreler": param_str(cfg), "Dev_Sirasi": order + 1})
    df = pd.DataFrame(rows).sort_values(["Validation_MAE", "Validation_RMSE", "Karmasiklik", "Dev_Sirasi"])
    df["Secim"] = ["SEÇİLDİ"] + ["elendi"] * (len(df) - 1)
    return df.reset_index(drop=True)


def save_json(obj, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False, default=float)


def lock_predictions(test_df, methods, lock_file):
    """Test referanslarını OKUMADAN tahmin yapar ve kilit dosyasına yazar.

    methods: {yöntem_adı: yöntem}. Dosya varsa yeniden üretilen tahminlerin birebir aynı
    olduğunu doğrular, üzerine yazmaz.
    """
    assert "gt_count" not in test_df.columns, "Kilit aşamasında test referansı bulunmamalı!"
    rows = []
    for r in test_df.itertuples():
        img = load_image(r.sequence, r.filename)
        row = {"seed": r.seed, "block": r.block, "sequence": r.sequence, "frame_idx": r.frame_idx,
               "filename": r.filename}
        for name, meth in methods.items():
            cnt, ms = run_method(img, meth)
            row[f"{name}_pred"] = cnt
            row[f"{name}_time_ms"] = round(ms, 2)
        rows.append(row)
    new = pd.DataFrame(rows)
    if os.path.exists(lock_file):
        old = pd.read_csv(lock_file)
        pred_cols = [c for c in new.columns if c.endswith("_pred")]
        assert list(old.columns) == list(new.columns) and \
            (old[pred_cols].to_numpy() == new[pred_cols].to_numpy()).all(), \
            "UYARI: Yeniden üretilen test tahminleri kilitli dosyadan farklı!"
        print("Kilit dosyası mevcut; tahminler birebir aynı. Dosyaya dokunulmadı.")
        return old
    new.to_csv(lock_file, index=False)
    print(f"{lock_file} yazıldı. ⛔ Şimdi commit atın; test referanslarına ancak ondan sonra bakın.")
    return new

"""Seed ile tekrarlanabilir kare seçimi (ödev Bölüm 3).

Algoritma bireysel çalışmadakiyle birebir aynıdır; seed 14048 aynı kareleri üretir.
"""
import os
import random

import pandas as pd

from . import config as C


def select_dataset_frames(n_seq01, n_seq02, seed):
    rng = random.Random(seed)
    attempts_devval = 0
    while True:
        attempts_devval += 1
        val_indices = sorted(rng.sample(range(n_seq01), C.N_VAL))
        dev_candidates = [i for i in range(n_seq01)
                          if all(abs(i - v) > C.MIN_GAP for v in val_indices)]
        if len(dev_candidates) >= C.N_DEV:
            dev_indices = sorted(rng.sample(dev_candidates, C.N_DEV))
            break
    attempts_test = 0
    while True:
        attempts_test += 1
        starts = sorted(rng.sample(range(n_seq02 - (C.BLOCK_LEN - 1)), C.N_BLOCKS))
        if all(starts[k + 1] - (starts[k] + C.BLOCK_LEN - 1) > C.MIN_GAP for k in range(C.N_BLOCKS - 1)):
            test_blocks = [(b, s + o) for b, s in enumerate(starts, 1) for o in range(C.BLOCK_LEN)]
            break
    return dev_indices, val_indices, test_blocks, attempts_devval, attempts_test


def check_rules(dev_idx, val_idx, test_blk):
    assert not set(dev_idx) & set(val_idx)
    assert all(abs(d - v) > C.MIN_GAP for d in dev_idx for v in val_idx)
    starts = sorted({s for b, s in test_blk if (b, s - 1) not in test_blk})
    assert all(starts[k + 1] - (starts[k] + C.BLOCK_LEN - 1) > C.MIN_GAP for k in range(len(starts) - 1))


def build_selection(seed, n_seq01, n_seq02):
    dev_idx, val_idx, test_blk, att_dv, att_t = select_dataset_frames(n_seq01, n_seq02, seed)
    check_rules(dev_idx, val_idx, test_blk)
    fn = lambda i: f"t{i:03d}.tif"
    rec = [{"group": "Development", "block": 0, "sequence": "01", "frame_idx": i, "filename": fn(i), "seed": seed} for i in dev_idx]
    rec += [{"group": "Validation", "block": 0, "sequence": "01", "frame_idx": i, "filename": fn(i), "seed": seed} for i in val_idx]
    rec += [{"group": "Test", "block": b, "sequence": "02", "frame_idx": i, "filename": fn(i), "seed": seed} for b, i in test_blk]
    return pd.DataFrame(rec), (att_dv, att_t)


def selection_path(seed):
    return os.path.join(C.seed_dir(seed), "selected_frames.csv")


def load_selection(seed):
    return pd.read_csv(selection_path(seed), dtype={"sequence": str})


def dev_pool_excluding_all_val(selections, gap=0):
    """5. yöntem için ortak geliştirme havuzu.

    Tüm seed'lerin geliştirme kareleri birleştirilir; HERHANGİ bir seed'in doğrulama karesine
    `gap` veya daha az uzaklıktaki kareler çıkarılır (gap=0: yalnızca birebir aynı kareler).

    Not: ±5 (MIN_GAP) kuralı burada uygulanamaz; 4 seed'in doğrulama kareleri 92 karelik sekansı
    neredeyse tamamen kapsadığı için havuzda 4 kare kalır. Grup kararı: gap=0. Ardışık karelerin
    birbirine benzemesi raporda sınırlama olarak belirtilir.
    """
    all_val, dev = set(), set()
    for df in selections.values():
        all_val |= set(df.loc[df.group == "Validation", "frame_idx"])
        dev |= set(df.loc[df.group == "Development", "frame_idx"])
    pool = sorted(i for i in dev if all(abs(i - v) > gap for v in all_val))
    return pool, sorted(dev - set(pool))


def leaky_val_frames(selections, owner_seed, eval_seed):
    """owner_seed'in geliştirme karesi olup eval_seed'de doğrulama karesi olan kareler.

    Çapraz seed matrisinde, owner'ın yöntemi eval_seed doğrulamasında değerlendirilirken
    bu kareler dışarıda bırakılır (yöntem bu kareler üzerinde ayarlanmıştır).
    """
    a, b = selections[owner_seed], selections[eval_seed]
    return sorted(set(a.loc[a.group == "Development", "frame_idx"]) & set(b.loc[b.group == "Validation", "frame_idx"]))

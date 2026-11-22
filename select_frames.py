"""4 seed için kare seçimini üretir (ödev Bölüm 3) ve seed'ler arası çakışmayı raporlar.

Kullanım:
    python select_frames.py            # veri seti data/ altındaysa kare sayısı oradan okunur
    python select_frames.py 92 92      # veri olmadan: sekans 01 ve 02 kare sayıları elle verilir

Seçim, yöntem geliştirmeden ÖNCE yapılır ve ilk commit ile kaydedilir.
"""
import os
import sys

import pandas as pd

from src import config as C
from src.selection import build_selection, dev_pool_excluding_all_val, selection_path


def main():
    if len(sys.argv) == 3:
        n1, n2 = int(sys.argv[1]), int(sys.argv[2])
    else:
        from src.data import sequence_lengths
        n1, n2 = sequence_lengths()
    print(f"Sekans 01: {n1} kare | Sekans 02: {n2} kare\n")

    sels = {}
    for key, m in C.MEMBERS.items():
        df, (a_dv, a_t) = build_selection(m["seed"], n1, n2)
        path = selection_path(m["seed"])
        if os.path.exists(path):
            old = pd.read_csv(path, dtype={"sequence": str})
            assert old.equals(df), f"{path} mevcut seçimden farklı! Seçim yeniden yapılamaz."
        else:
            df.to_csv(path, index=False)
        sels[m["seed"]] = df
        g = lambda n: df.loc[df.group == n, "frame_idx"].tolist()
        print(f"{m['name']:20s} seed={m['seed']} (deneme dev/val={a_dv}, test={a_t})")
        print(f"   dev={g('Development')}\n   val={g('Validation')}\n   test={g('Test')}")

    # Seed'ler arası çakışma raporu
    rows = []
    seeds = list(sels)
    for i, a in enumerate(seeds):
        for b in seeds[i + 1:]:
            for grp_a, grp_b in [("Test", "Test"), ("Validation", "Development"), ("Development", "Validation")]:
                fa = set(sels[a].loc[sels[a].group == grp_a, "frame_idx"])
                fb = set(sels[b].loc[sels[b].group == grp_b, "frame_idx"])
                rows.append({"seed_a": a, "group_a": grp_a, "seed_b": b, "group_b": grp_b,
                             "n_ortak": len(fa & fb), "ortak_kareler": " ".join(map(str, sorted(fa & fb)))})
    ov = pd.DataFrame(rows)
    os.makedirs(C.RESULTS_DIR, exist_ok=True)
    ov.to_csv(os.path.join(C.RESULTS_DIR, "seed_overlap.csv"), index=False)

    seen = set()
    for s in C.SEEN_TEST_SEEDS:
        seen |= set(sels[s].loc[sels[s].group == "Test", "frame_idx"])
    print("\nDaha önce referansı görülmüş test kareleri (seed 14048):", sorted(seen))
    for s, df in sels.items():
        if s in C.SEEN_TEST_SEEDS:
            continue
        t = set(df.loc[df.group == "Test", "frame_idx"])
        print(f"  seed {s}: {len(t & seen)}/15 test karesi görülmüş -> {sorted(t & seen)}")

    pool, removed = dev_pool_excluding_all_val(sels)
    print(f"\n5. yöntem için ortak geliştirme havuzu (doğrulama kareleriyle birebir çakışanlar hariç): {len(pool)} kare {pool}")
    print(f"Bir seed'in doğrulama karesi olduğu için çıkarılan: {removed}")
    pd.DataFrame({"frame_idx": pool, "filename": [f"t{i:03d}.tif" for i in pool], "sequence": "01"}) \
        .to_csv(os.path.join(C.RESULTS_DIR, "dev_pool_method5.csv"), index=False)


if __name__ == "__main__":
    main()

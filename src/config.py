"""Grup projesinin ortak sabitleri: veri yolu, seed'ler ve seçim kuralları."""
import os

# ---------------------------------------------------------------- veri seti
DATA_URL = "https://data.celltrackingchallenge.net/training-datasets/Fluo-N2DH-GOWT1.zip"
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_ROOT = os.path.join(REPO_ROOT, "data")                 # .gitignore -> GitHub'a gitmez
ZIP_PATH = os.path.join(DATA_ROOT, "Fluo-N2DH-GOWT1.zip")
BASE_DIR = os.path.join(DATA_ROOT, "Fluo-N2DH-GOWT1")

SEEDS_DIR = os.path.join(REPO_ROOT, "seeds")                # seed bazlı çıktılar
RESULTS_DIR = os.path.join(REPO_ROOT, "results")            # çapraz seed / 5. yöntem çıktıları
FIG_DIR = os.path.join(REPO_ROOT, "figures")                # veri görüntüsü İÇERMEYEN grafikler
FIG_IMG_DIR = os.path.join(REPO_ROOT, "figures_report")     # veri görüntüsü içeren şekiller (GitHub'a gitmez)

# ---------------------------------------------------------------- üyeler ve seed'ler
# Seed kuralı (ödev Bölüm 3): öğrenci numarasının son 5 hanesi + 2026 (aritmetik toplam)
MEMBERS = {
    "suleyman": {"name": "Süleyman Balsak",     "student_id": "254312022"},
    "seda":     {"name": "Seda Erten",          "student_id": "254312008"},
    "ilkin":    {"name": "İlkin Urcan",         "student_id": "244329078"},
    "aslihan":  {"name": "Aslıhan Semiz Varlı", "student_id": "254329024"},
}
for _m in MEMBERS.values():
    _m["seed"] = int(_m["student_id"][-5:]) + 2026

BASE_SEED = MEMBERS["suleyman"]["seed"]                     # 14048 – temel seed
SEEDS = {k: m["seed"] for k, m in MEMBERS.items()}          # {'suleyman': 14048, 'seda': 14034, ...}

# Seed 14048'in test referansları bireysel çalışmada (ayrı repo) zaten okunmuştur.
SEEN_TEST_SEEDS = {14048}
INDIVIDUAL_REPO_14048 = "https://github.com/James007Bond-code/goruntu-isleme-hucre-sayimi-254312022-suleymanBalsak"

# ---------------------------------------------------------------- seçim kuralları
MIN_GAP = 5                     # iki grup/blok arası: |i - j| > MIN_GAP
N_VAL, N_DEV = 5, 10            # sekans 01
N_BLOCKS, BLOCK_LEN = 3, 5      # sekans 02


# Ödev 18.2'nin istediği dosyalar repo kökündedir (4 seed birleşik)
LOCK_FILE = os.path.join(REPO_ROOT, "test_predictions_locked.csv")
FINAL_PIPELINE_FILE = os.path.join(REPO_ROOT, "final_pipeline.json")


def seed_dir(seed):
    d = os.path.join(SEEDS_DIR, str(seed))
    os.makedirs(d, exist_ok=True)
    return d

"""Veri setinin indirilmesi, görüntü ve referans etiketlerinin okunması."""
import glob
import os
import urllib.request
import zipfile

import cv2
import numpy as np

from . import config as C


def download_dataset():
    """Arşivi resmî adresten indirip data/ altına açar (zaten varsa dokunmaz)."""
    os.makedirs(C.DATA_ROOT, exist_ok=True)
    if not os.path.isdir(C.BASE_DIR):
        if not os.path.exists(C.ZIP_PATH):
            print("Veri seti indiriliyor...")
            urllib.request.urlretrieve(C.DATA_URL, C.ZIP_PATH)
        with zipfile.ZipFile(C.ZIP_PATH) as zf:
            zf.extractall(C.DATA_ROOT)
        print("Arşiv çıkarıldı.")
    return sequence_lengths()


def list_frames(seq_str):
    return sorted(glob.glob(os.path.join(C.BASE_DIR, seq_str, "t*.tif")))


def sequence_lengths():
    n1, n2 = len(list_frames("01")), len(list_frames("02"))
    assert n1 and n2, f"Görüntüler bulunamadı: {C.BASE_DIR}"
    return n1, n2


def load_image(seq_str, fname):
    return cv2.imread(os.path.join(C.BASE_DIR, seq_str, fname), cv2.IMREAD_UNCHANGED)


def read_gt_labels(seq_str, frame_idx, lock_file=None):
    """TRA takip etiketini okur.

    Sekans 02 (test) referansı yalnızca `lock_file` mevcutsa okunabilir; böylece test
    tahminleri kilitlenmeden referansa bakılması kodla engellenir.
    """
    if seq_str == "02":
        if lock_file is None or not os.path.exists(lock_file):
            raise RuntimeError("Test referansları, test tahminleri kilitlenmeden okunamaz!")
    path = os.path.join(C.BASE_DIR, f"{seq_str}_GT", "TRA", f"man_track{int(frame_idx):03d}.tif")
    if not os.path.exists(path):
        return None
    return cv2.imread(path, cv2.IMREAD_UNCHANGED)


def read_gt_count(seq_str, frame_idx, lock_file=None):
    lbl = read_gt_labels(seq_str, frame_idx, lock_file)
    return None if lbl is None else int(np.count_nonzero(np.unique(lbl)))

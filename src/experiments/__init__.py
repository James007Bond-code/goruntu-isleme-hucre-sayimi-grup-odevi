"""Üye deney listeleri. Her üye yalnızca kendi dosyasını düzenler."""
import importlib


def load(member):
    mod = importlib.import_module(f"{__name__}.{member}")
    return mod.FAMILY, mod.EXPERIMENTS

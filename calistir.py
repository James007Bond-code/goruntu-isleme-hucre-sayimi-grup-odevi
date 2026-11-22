"""main_grup.ipynb'yi baştan sona çalıştırır (Colab'da tek hücreden kullanım için).

1. aşama: Kilit dosyaları yazılır, kilit kontrolünde durulur -> kilit_commit.zip
2. aşama (kilit commit edildikten sonra): test ve zamansal analiz -> test_commit.zip

Notebook'taki kodun aynısı çalışır; bu betik yalnızca hücreleri sırayla yürütür.
Grafikler figures/ klasörüne kaydedilir, ekrana çizilmez.
"""
import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

plt.show = lambda *a, **k: plt.close("all")
os.environ["CALISTIR_SCRIPT"] = "1"

here = os.path.dirname(os.path.abspath(__file__))
os.chdir(here)
nb = json.load(open("main_grup.ipynb", encoding="utf-8"))
ns = {"__name__": "__main__"}
for i, cell in enumerate(nb["cells"]):
    src = "".join(cell["source"])
    if cell["cell_type"] == "markdown":
        title = src.strip().splitlines()[0]
        if title.startswith("#"):
            print("\n" + "=" * 100 + f"\n{title.lstrip('#').strip()}\n" + "=" * 100, flush=True)
        continue
    try:
        exec(compile(src, f"main_grup.ipynb hücre {i}", "exec"), ns)
    except RuntimeError as e:
        if "Kilit kontrolü" in str(e):
            print(f"\n{e}\n\n1. AŞAMA TAMAMLANDI → kilit_commit.zip hazır.", flush=True)
            sys.exit(0)
        raise
print("\n2. AŞAMA TAMAMLANDI → test_commit.zip hazır.", flush=True)

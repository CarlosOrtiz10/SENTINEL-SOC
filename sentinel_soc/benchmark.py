"""Experimento repetible de cola y búsqueda: cronómetro y memoria trazada.

Para tiempos se evita tracemalloc, que alteraría la medición. Cada observación
usa la misma carga; mediana de 7 corridas, con un calentamiento previo.
"""
from __future__ import annotations
import csv
import gc
import json
import platform
import statistics
import time
import tracemalloc
from pathlib import Path
from typing import Callable
from .avl import AVLTree
from .queues import ListQueue, DequeQueue
from .service import int_compare

SIZES = (1000, 3000, 6000, 12000)
REPEATS = 7
QueueFactory = Callable[[], ListQueue[int] | DequeQueue[int]]


def _queue_run(factory: QueueFactory, n: int) -> None:
    queue = factory()
    for i in range(n):
        queue.enqueue(i)
    for i in range(n):
        assert queue.dequeue() == i


def _median_ms(action: Callable[[], None], repeats: int = REPEATS) -> float:
    action()  # calentamiento idéntico por configuración
    measurements = []
    for _ in range(repeats):
        gc.collect()
        t0 = time.perf_counter_ns()
        action()
        measurements.append((time.perf_counter_ns() - t0) / 1_000_000)
    return statistics.median(measurements)


def _peak_kib(factory: QueueFactory, n: int) -> float:
    gc.collect()
    tracemalloc.start()
    try:
        _queue_run(factory, n)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return peak / 1024


def _search_run_linear(records: list[tuple[int, int]], ids: list[int]) -> None:
    for key in ids:
        found = next((value for candidate, value in records if candidate == key), None)
        assert found == key


def _search_run_avl(tree: AVLTree[int, int], ids: list[int]) -> None:
    for key in ids:
        assert tree.find(key) == key


def run_benchmarks(folder: Path) -> dict:
    folder.mkdir(parents=True, exist_ok=True)
    queues = []
    for n in SIZES:
        for label, factory in (("list", ListQueue), ("deque", DequeQueue)):
            queues.append({
                "n": n, "queue": label,
                "median_ms": round(_median_ms(lambda f=factory, k=n: _queue_run(f, k)), 5),
                "peak_kib": round(_peak_kib(factory, n), 2),
            })
    searches = []
    for n in SIZES:
        records = [(i, i) for i in range(n)]
        avl: AVLTree[int, int] = AVLTree(int_compare)
        for k, v in records:
            avl.insert(k, v)  # inserción creciente: prueba balance real
        assert avl.validate()
        # 240 búsquedas en el último cuarto: misma secuencia para ambos.
        ids = [n - 1 - (j * 37) % max(1, n // 4) for j in range(240)]
        searches.append({
            "n": n, "queries": len(ids), "avl_height": avl.height,
            "linear_ms": round(_median_ms(lambda: _search_run_linear(records, ids)), 5),
            "avl_ms": round(_median_ms(lambda: _search_run_avl(avl, ids)), 5),
        })
    result = {
        "metadata": {"python": platform.python_version(), "platform": platform.platform(),
                     "repeats": REPEATS, "sizes": list(SIZES),
                     "clock": "perf_counter_ns", "memory": "tracemalloc peak allocation"},
        "queues": queues, "searches": searches,
    }
    (folder / "benchmark.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf8")
    for name, records in (("colas.csv", queues), ("busquedas.csv", searches)):
        with (folder / name).open("w", newline="", encoding="utf8") as handle:
            writer = csv.DictWriter(handle, fieldnames=records[0].keys())
            writer.writeheader()
            writer.writerows(records)
    return result

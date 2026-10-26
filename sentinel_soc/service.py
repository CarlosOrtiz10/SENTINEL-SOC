"""Orquestador desacoplado de la implementación de cola (inyección de dependencia)."""
from __future__ import annotations
from typing import Callable
from .adt import QueueADT
from .avl import AVLTree
from .models import Incident


def int_compare(a: int, b: int) -> int:
    return (a > b) - (a < b)


class IncidentCenter:
    """FIFO de ingreso + AVL para incidentes atendidos que siguen abiertos.

    La severidad se conserva como metadato: no altera el orden FIFO.
    Un SOC real incorporaría SLA, persistencia, concurrencia y escalamiento.
    """

    def __init__(self, pending: QueueADT[Incident], index_factory: Callable[[], AVLTree[int, Incident]] | None = None) -> None:
        self._pending = pending
        self._active = index_factory() if index_factory else AVLTree(int_compare)
        if len(self._pending) or len(self._active):
            raise ValueError("La cola y el índice deben estar inicialmente vacíos")
        self._ids_seen: set[int] = set()
        self._closed_ids: set[int] = set()
        self._processed_count = 0

    def submit(self, incident: Incident) -> None:
        if incident.id in self._ids_seen:
            raise ValueError(f"Incidente ya registrado: {incident.id}")
        self._pending.enqueue(incident)
        self._ids_seen.add(incident.id)

    def process_next(self) -> Incident:
        incident = self._pending.peek()
        self._active.insert(incident.id, incident)
        self._pending.dequeue()
        self._processed_count += 1
        return incident

    def find_active(self, id: int) -> Incident | None:
        return self._active.find(id)

    def resolve(self, id: int) -> Incident:
        incident = self._active.remove(id)
        self._closed_ids.add(id)
        return incident

    @property
    def pending_count(self) -> int:
        return len(self._pending)

    @property
    def active_count(self) -> int:
        return len(self._active)

    @property
    def resolved_count(self) -> int:
        return len(self._closed_ids)

    @property
    def processed_count(self) -> int:
        return self._processed_count

    @property
    def index_height(self) -> int:
        return self._active.height

    def active_ordered(self) -> list[Incident]:
        return [incident for _, incident in self._active.inorder()]

    def check_integrity(self) -> bool:
        return (self._active.validate() and
                self.pending_count + self.active_count + self.resolved_count == len(self._ids_seen) and
                self.processed_count == self.active_count + self.resolved_count)

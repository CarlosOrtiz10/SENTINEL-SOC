"""Contratos públicos de estructuras abstractas, independientes de implementaciones."""
from __future__ import annotations
from typing import Protocol, TypeVar, runtime_checkable

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")


class QueueEmptyError(IndexError):
    """Se intenta consultar o retirar un elemento de una cola vacía."""


class DuplicateKeyError(ValueError):
    """Existe previamente una clave en el índice."""


@runtime_checkable
class QueueADT(Protocol[T]):
    """Contrato FIFO genérico para implementaciones intercambiables."""

    def enqueue(self, item: T) -> None: ...
    def dequeue(self) -> T: ...
    def peek(self) -> T: ...
    def __len__(self) -> int: ...


@runtime_checkable
class IndexADT(Protocol[K, V]):
    """Contrato del índice jerárquico por clave única."""

    def insert(self, key: K, value: V) -> None: ...
    def find(self, key: K) -> V | None: ...
    def remove(self, key: K) -> V: ...
    def __len__(self) -> int: ...

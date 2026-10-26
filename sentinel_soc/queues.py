"""Dos colas genéricas con semántica FIFO idéntica y costes distintos."""
from __future__ import annotations
from collections import deque
from typing import Generic, TypeVar
from .adt import QueueEmptyError

T = TypeVar("T")


class ListQueue(Generic[T]):
    """Cola didáctica: extraer al inicio cuesta O(n)."""

    def __init__(self) -> None:
        self._data: list[T] = []

    def enqueue(self, item: T) -> None:
        self._data.append(item)

    def dequeue(self) -> T:
        if not self._data:
            raise QueueEmptyError("No existen alertas pendientes")
        return self._data.pop(0)

    def peek(self) -> T:
        if not self._data:
            raise QueueEmptyError("No existen alertas pendientes")
        return self._data[0]

    def __len__(self) -> int:
        return len(self._data)


class DequeQueue(Generic[T]):
    """Cola eficiente: inserción al final y salida al inicio O(1) amortizado."""

    def __init__(self) -> None:
        self._data: deque[T] = deque()

    def enqueue(self, item: T) -> None:
        self._data.append(item)

    def dequeue(self) -> T:
        if not self._data:
            raise QueueEmptyError("No existen alertas pendientes")
        return self._data.popleft()

    def peek(self) -> T:
        if not self._data:
            raise QueueEmptyError("No existen alertas pendientes")
        return self._data[0]

    def __len__(self) -> int:
        return len(self._data)

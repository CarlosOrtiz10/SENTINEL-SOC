"""Árbol AVL genérico: índice ordenado con altura O(log n)."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Generic, TypeVar
from .adt import DuplicateKeyError

K = TypeVar("K")
V = TypeVar("V")
Comparator = Callable[[K, K], int]


@dataclass(slots=True)
class _Node(Generic[K, V]):
    key: K
    value: V
    left: _Node[K, V] | None = None
    right: _Node[K, V] | None = None
    height: int = 1


class AVLTree(Generic[K, V]):
    """Índice AVL con claves únicas; el comparador define el orden total."""

    def __init__(self, comparator: Comparator[K]) -> None:
        self._root: _Node[K, V] | None = None
        self._compare = comparator
        self._size = 0

    @staticmethod
    def _height(node: _Node[K, V] | None) -> int:
        return node.height if node else 0

    @classmethod
    def _refresh(cls, node: _Node[K, V]) -> None:
        node.height = 1 + max(cls._height(node.left), cls._height(node.right))

    @classmethod
    def _balance(cls, node: _Node[K, V]) -> int:
        return cls._height(node.left) - cls._height(node.right)

    @classmethod
    def _rotate_right(cls, node: _Node[K, V]) -> _Node[K, V]:
        pivot = node.left
        assert pivot is not None
        node.left = pivot.right
        pivot.right = node
        cls._refresh(node)
        cls._refresh(pivot)
        return pivot

    @classmethod
    def _rotate_left(cls, node: _Node[K, V]) -> _Node[K, V]:
        pivot = node.right
        assert pivot is not None
        node.right = pivot.left
        pivot.left = node
        cls._refresh(node)
        cls._refresh(pivot)
        return pivot

    @classmethod
    def _rebalance(cls, node: _Node[K, V]) -> _Node[K, V]:
        cls._refresh(node)
        balance = cls._balance(node)
        if balance > 1:
            assert node.left is not None
            if cls._balance(node.left) < 0:
                node.left = cls._rotate_left(node.left)
            return cls._rotate_right(node)
        if balance < -1:
            assert node.right is not None
            if cls._balance(node.right) > 0:
                node.right = cls._rotate_right(node.right)
            return cls._rotate_left(node)
        return node

    def insert(self, key: K, value: V) -> None:
        def add(node: _Node[K, V] | None) -> _Node[K, V]:
            if node is None:
                return _Node(key, value)
            direction = self._compare(key, node.key)
            if direction == 0:
                raise DuplicateKeyError(f"Clave duplicada: {key}")
            if direction < 0:
                node.left = add(node.left)
            else:
                node.right = add(node.right)
            return self._rebalance(node)

        self._root = add(self._root)
        self._size += 1

    def find(self, key: K) -> V | None:
        node = self._root
        while node:
            direction = self._compare(key, node.key)
            if direction == 0:
                return node.value
            node = node.left if direction < 0 else node.right
        return None

    def remove(self, key: K) -> V:
        """Elimina la clave; restaura el balance incluso con dos hijos."""
        found: list[V] = []

        def detach_min(node: _Node[K, V]) -> tuple[_Node[K, V] | None, _Node[K, V]]:
            if node.left is None:
                return node.right, node
            node.left, minimum = detach_min(node.left)
            return self._rebalance(node), minimum

        def delete(node: _Node[K, V] | None) -> _Node[K, V] | None:
            if node is None:
                raise KeyError(key)
            direction = self._compare(key, node.key)
            if direction < 0:
                node.left = delete(node.left)
            elif direction > 0:
                node.right = delete(node.right)
            else:
                found.append(node.value)
                if node.left is None:
                    return node.right
                if node.right is None:
                    return node.left
                node.right, successor = detach_min(node.right)
                node.key, node.value = successor.key, successor.value
            return self._rebalance(node)

        self._root = delete(self._root)
        self._size -= 1
        return found[0]

    def inorder(self) -> list[tuple[K, V]]:
        output: list[tuple[K, V]] = []
        def visit(node: _Node[K, V] | None) -> None:
            if node:
                visit(node.left)
                output.append((node.key, node.value))
                visit(node.right)
        visit(self._root)
        return output

    @property
    def height(self) -> int:
        return self._height(self._root)

    def validate(self) -> bool:
        """Comprueba orden BST, alturas, equilibrio AVL y tamaño contabilizado."""
        def check(node: _Node[K, V] | None, low: K | None, high: K | None) -> tuple[int, int]:
            if node is None:
                return 0, 0
            if low is not None and self._compare(node.key, low) <= 0:
                raise AssertionError("Se violó el orden inferior BST")
            if high is not None and self._compare(node.key, high) >= 0:
                raise AssertionError("Se violó el orden superior BST")
            lh, lc = check(node.left, low, node.key)
            rh, rc = check(node.right, node.key, high)
            if abs(lh-rh) > 1 or node.height != 1 + max(lh,rh):
                raise AssertionError("Altura o equilibrio AVL inválidos")
            return node.height, 1 + lc + rc
        _, count = check(self._root, None, None)
        if count != self._size:
            raise AssertionError("Tamaño del índice inconsistente")
        return True

    def __len__(self) -> int:
        return self._size

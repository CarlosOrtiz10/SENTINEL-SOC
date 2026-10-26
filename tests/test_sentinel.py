"""Suite ejecutable con unittest, sin dependencias externas."""
from __future__ import annotations
import random
import unittest
from collections import deque
from sentinel_soc import (AVLTree, DequeQueue, ListQueue, QueueEmptyError,
                          DuplicateKeyError, Incident, IncidentCenter, Severity)
from sentinel_soc.service import int_compare


class QueueContractTests(unittest.TestCase):
    def test_both_implementations_implement_fifo(self):
        for factory in (ListQueue, DequeQueue):
            with self.subTest(factory=factory.__name__):
                queue = factory()
                for value in [40, 20, 60, 10]:
                    queue.enqueue(value)
                self.assertEqual(queue.peek(), 40)
                self.assertEqual([queue.dequeue() for _ in range(4)], [40, 20, 60, 10])
                self.assertEqual(len(queue), 0)

    def test_empty_queue_raises_controlled_error(self):
        for factory in (ListQueue, DequeQueue):
            with self.subTest(factory=factory.__name__):
                queue = factory()
                with self.assertRaises(QueueEmptyError):
                    queue.peek()
                with self.assertRaises(QueueEmptyError):
                    queue.dequeue()

    def test_queue_behaves_like_reference_under_random_operations(self):
        randomizer = random.Random(2026)
        events = [randomizer.choice(["in", "in", "out"]) for _ in range(800)]
        for factory in (ListQueue, DequeQueue):
            q = factory()
            reference: deque[int] = deque()
            for i, event in enumerate(events):
                if event == "in":
                    q.enqueue(i)
                    reference.append(i)
                elif reference:
                    self.assertEqual(q.dequeue(), reference.popleft())
                else:
                    with self.assertRaises(QueueEmptyError):
                        q.dequeue()
                self.assertEqual(len(q), len(reference))


class AVLTests(unittest.TestCase):
    def setUp(self):
        self.tree: AVLTree[int, str] = AVLTree(int_compare)

    def test_four_rotation_patterns(self):
        for values in ([30, 20, 10], [10, 20, 30], [30, 10, 20], [10, 30, 20]):
            tree = AVLTree[int, int](int_compare)
            for value in values:
                tree.insert(value, value)
            self.assertEqual(tree.height, 2)
            self.assertTrue(tree.validate())
            self.assertEqual(tree.inorder(), [(10, 10), (20, 20), (30, 30)])

    def test_sorted_insertions_remain_balanced(self):
        for key in range(1, 1001):
            self.tree.insert(key, str(key))
        self.assertTrue(self.tree.validate())
        self.assertLessEqual(self.tree.height, 11)
        self.assertEqual(self.tree.find(999), "999")

    def test_duplicate_and_missing_key(self):
        self.tree.insert(10, "A")
        with self.assertRaises(DuplicateKeyError):
            self.tree.insert(10, "B")
        self.assertIsNone(self.tree.find(21))
        with self.assertRaises(KeyError):
            self.tree.remove(21)
        self.assertEqual(len(self.tree), 1)

    def test_remove_leaf_one_child_two_children(self):
        for k in [40, 20, 60, 10, 30, 50, 70, 25, 35, 45]:
            self.tree.insert(k, str(k))
        for key in (10, 50, 40, 70, 20):
            self.assertEqual(self.tree.remove(key), str(key))
            self.assertTrue(self.tree.validate())
            self.assertIsNone(self.tree.find(key))
        self.assertEqual([key for key, _ in self.tree.inorder()], [25, 30, 35, 45, 60])

    def test_randomized_insert_remove_invariants(self):
        rng = random.Random(708)
        keys = rng.sample(range(3000), 500)
        for key in keys:
            self.tree.insert(key, str(key))
        self.assertTrue(self.tree.validate())
        for key in rng.sample(keys, 300):
            self.assertEqual(self.tree.remove(key), str(key))
            self.assertTrue(self.tree.validate())
        self.assertEqual(len(self.tree), 200)

    def test_generic_string_keys(self):
        tree = AVLTree[str, int](lambda a, b: (a > b) - (a < b))
        tree.insert("zeta", 3)
        tree.insert("alfa", 1)
        tree.insert("beta", 2)
        self.assertTrue(tree.validate())
        self.assertEqual(tree.find("beta"), 2)


class IncidentCenterTests(unittest.TestCase):
    def _new_incident(self, number: int) -> Incident:
        return Incident(number, "SRV-TEST", "Simulado", Severity.MEDIUM)

    def test_full_lifecycle_and_integrity(self):
        for factory in (ListQueue, DequeQueue):
            center = IncidentCenter(factory())
            for key in (40, 20, 60, 10, 30):
                center.submit(self._new_incident(key))
            self.assertEqual(center.pending_count, 5)
            self.assertEqual([center.process_next().id for _ in range(5)], [40, 20, 60, 10, 30])
            self.assertEqual([obj.id for obj in center.active_ordered()], [10, 20, 30, 40, 60])
            self.assertEqual(center.find_active(60).id, 60)
            self.assertEqual(center.resolve(20).id, 20)
            self.assertIsNone(center.find_active(20))
            self.assertTrue(center.check_integrity())
            self.assertEqual((center.pending_count, center.active_count, center.resolved_count), (0, 4, 1))

    def test_duplicate_identifiers_rejected_throughout_lifecycle(self):
        center = IncidentCenter(DequeQueue())
        obj = self._new_incident(100)
        center.submit(obj)
        with self.assertRaises(ValueError):
            center.submit(obj)
        center.process_next()
        center.resolve(100)
        with self.assertRaises(ValueError):
            center.submit(obj)

    def test_missing_resolution_and_empty_processing(self):
        center = IncidentCenter(ListQueue())
        with self.assertRaises(QueueEmptyError):
            center.process_next()
        with self.assertRaises(KeyError):
            center.resolve(123)
        self.assertTrue(center.check_integrity())
        pending = ListQueue()
        pending.enqueue(self._new_incident(1))
        with self.assertRaises(ValueError):
            IncidentCenter(pending)
        occupied = AVLTree(int_compare)
        occupied.insert(1, self._new_incident(1))
        with self.assertRaises(ValueError):
            IncidentCenter(ListQueue(), lambda: occupied)

        class RejectingIndex(AVLTree):
            def insert(self, key, value):
                raise ValueError("Inserción rechazada")

        center = IncidentCenter(ListQueue(), lambda: RejectingIndex(int_compare))
        center.submit(self._new_incident(1))
        for _ in range(2):
            with self.assertRaises(ValueError):
                center.process_next()
            self.assertEqual(center.pending_count, 1)
            self.assertEqual(center.processed_count, 0)
            self.assertTrue(center.check_integrity())

    def test_invalid_entity(self):
        for invalid in (True, 1.5, float("nan"), "1", None):
            with self.subTest(id=invalid), self.assertRaises(TypeError):
                self._new_incident(invalid)
        for asset, category in ((None, "X"), ("X", 42)):
            with self.assertRaises(TypeError):
                Incident(1, asset, category, Severity.LOW)
        with self.assertRaises(ValueError):
            self._new_incident(0)
        with self.assertRaises(ValueError):
            Incident(1, " ", "Prueba", Severity.LOW)
        with self.assertRaises(TypeError):
            Incident(1, "X", "Prueba", "ALTA")  # type: ignore[arg-type]

    def test_adt_runtime_contracts(self):
        from sentinel_soc import QueueADT, IndexADT
        self.assertIsInstance(DequeQueue(), QueueADT)
        self.assertIsInstance(ListQueue(), QueueADT)
        self.assertIsInstance(AVLTree(int_compare), IndexADT)


if __name__ == "__main__":
    unittest.main(verbosity=2)

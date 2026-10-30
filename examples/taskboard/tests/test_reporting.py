# SPDX-License-Identifier: Apache-2.0
import unittest

from taskboard import TaskStore
from taskboard.reporting import open_task_counts


class ReportingTests(unittest.TestCase):
    def test_counts_open_tasks_per_owner(self):
        store = TaskStore()
        store.add("ana", "a1")
        store.add("ana", "a2")
        store.add("ben", "b1")
        self.assertEqual(open_task_counts(store), {"ana": 2, "ben": 1})

    def test_done_tasks_are_not_counted(self):
        store = TaskStore()
        done = store.add("ana", "finished")
        store.add("ana", "pending")
        store.complete("ana", done)
        self.assertEqual(open_task_counts(store), {"ana": 1})

    def test_owner_with_only_done_tasks_is_omitted(self):
        store = TaskStore()
        done = store.add("ana", "finished")
        store.complete("ana", done)
        self.assertEqual(open_task_counts(store), {})

    def test_empty_store(self):
        self.assertEqual(open_task_counts(TaskStore()), {})


if __name__ == "__main__":
    unittest.main()

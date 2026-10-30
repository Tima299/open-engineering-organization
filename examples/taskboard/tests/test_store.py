# SPDX-License-Identifier: Apache-2.0
import unittest

from taskboard import TaskStore
from taskboard.db import MIGRATIONS, current_version, migrate


class TaskStoreTests(unittest.TestCase):
    def setUp(self):
        self.store = TaskStore()

    def test_add_returns_id_and_list_shows_task(self):
        task_id = self.store.add("ana", "write docs", due="2030-01-31")
        tasks = self.store.list("ana")
        self.assertEqual([t["id"] for t in tasks], [task_id])
        self.assertEqual(tasks[0]["title"], "write docs")
        self.assertEqual(tasks[0]["due"], "2030-01-31")
        self.assertEqual(tasks[0]["done"], 0)

    def test_due_is_optional(self):
        self.store.add("ana", "no deadline")
        self.assertIsNone(self.store.list("ana")[0]["due"])

    def test_list_is_per_owner_and_ordered(self):
        first = self.store.add("ana", "one")
        self.store.add("ben", "other user")
        second = self.store.add("ana", "two")
        self.assertEqual([t["id"] for t in self.store.list("ana")], [first, second])
        self.assertEqual(len(self.store.list("ben")), 1)

    def test_complete_marks_task_done(self):
        task_id = self.store.add("ana", "ship it")
        task = self.store.complete("ana", task_id)
        self.assertEqual(task["done"], 1)
        self.assertEqual(self.store.list("ana")[0]["done"], 1)

    def test_owner_can_delete_own_task(self):
        task_id = self.store.add("ana", "temporary")
        self.assertTrue(self.store.delete("ana", task_id))
        self.assertEqual(self.store.list("ana"), [])


class MigrationTests(unittest.TestCase):
    def test_migrate_is_idempotent(self):
        store = TaskStore()
        migrate(store.conn)
        migrate(store.conn)
        self.assertEqual(current_version(store.conn), MIGRATIONS[-1][0])


if __name__ == "__main__":
    unittest.main()

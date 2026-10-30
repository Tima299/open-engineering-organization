# SPDX-License-Identifier: Apache-2.0
"""Per-user task storage on top of SQLite."""
from .db import connect


class TaskStore:
    def __init__(self, path=":memory:"):
        self.conn = connect(path)

    def add(self, owner, title, due=None):
        """Create a task for `owner` and return its id. `due` is an ISO date string or None."""
        cur = self.conn.execute(
            "INSERT INTO tasks (owner, title, due) VALUES (?, ?, ?)", (owner, title, due))
        self.conn.commit()
        return cur.lastrowid

    def list(self, owner):
        """Return `owner`'s tasks as dicts, oldest first."""
        rows = self.conn.execute(
            "SELECT id, owner, title, due, done FROM tasks WHERE owner = ? ORDER BY id", (owner,))
        return [dict(r) for r in rows]

    def complete(self, owner, task_id):
        """Mark one of `owner`'s tasks done and return the updated task."""
        self.conn.execute("UPDATE tasks SET done = 1 WHERE id = ? AND owner = ?", (task_id, owner))
        self.conn.commit()
        row = self.conn.execute(
            "SELECT id, owner, title, due, done FROM tasks WHERE id = ? AND owner = ?",
            (task_id, owner)).fetchone()
        return dict(row)

    def delete(self, requester, task_id):
        """Delete a task. Returns True if a task was removed."""
        cur = self.conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self.conn.commit()
        return cur.rowcount > 0

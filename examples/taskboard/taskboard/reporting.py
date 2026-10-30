# SPDX-License-Identifier: Apache-2.0
"""Reporting: how many open tasks does each owner have?"""
import abc


class CountStrategy(abc.ABC):
    """Interface for ways of counting tasks."""

    @abc.abstractmethod
    def count(self, rows):
        raise NotImplementedError


class OpenTasksPerOwner(CountStrategy):
    name = "open-per-owner"

    def count(self, rows):
        counts = {}
        for row in rows:
            if not row["done"]:
                counts[row["owner"]] = counts.get(row["owner"], 0) + 1
        return counts


class StrategyRegistry:
    _strategies = {}

    @classmethod
    def register(cls, strategy_cls):
        cls._strategies[strategy_cls.name] = strategy_cls
        return strategy_cls

    @classmethod
    def lookup(cls, name):
        try:
            return cls._strategies[name]
        except KeyError:
            raise ValueError(f"unknown counting strategy: {name}") from None


StrategyRegistry.register(OpenTasksPerOwner)


class StrategyFactory:
    @staticmethod
    def create(name="open-per-owner"):
        return StrategyRegistry.lookup(name)()


class OpenTaskReport:
    def __init__(self, store, strategy=None):
        self._store = store
        self._strategy = strategy or StrategyFactory.create()

    def generate(self):
        rows = self._store.conn.execute("SELECT owner, done FROM tasks").fetchall()
        return self._strategy.count(rows)


def open_task_counts(store):
    """Return {owner: number of open tasks}; owners with no open tasks are omitted."""
    return OpenTaskReport(store).generate()

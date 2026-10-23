"""Regression coverage for CSV persistence without loading runtime dependencies."""

import asyncio
import importlib
import sys
import tempfile
import types
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
STORAGE_PACKAGE_PATH = REPOSITORY_ROOT / "src" / "data" / "storage"
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))


class EmptyDataFrame:
    empty = True
    columns = []


def load_csv_storage():
    """Load the real CSV implementation while stubbing pandas and package init."""
    pandas_stub = types.ModuleType("pandas")
    pandas_stub.read_csv = lambda *args, **kwargs: EmptyDataFrame()
    storage_package = types.ModuleType("src.data.storage")
    storage_package.__path__ = [str(STORAGE_PACKAGE_PATH)]

    names = (
        "pandas",
        "src.data.storage",
        "src.data.storage.base",
        "src.data.storage.csv_storage",
    )
    missing = object()
    original = {name: sys.modules.get(name, missing) for name in names}
    try:
        sys.modules["pandas"] = pandas_stub
        sys.modules["src.data.storage"] = storage_package
        sys.modules.pop("src.data.storage.base", None)
        sys.modules.pop("src.data.storage.csv_storage", None)
        return importlib.import_module("src.data.storage.csv_storage").CSVStorage
    finally:
        for name, module in original.items():
            if module is missing:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


class CSVStorageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.csv_storage = load_csv_storage()

    def test_content_title_with_csv_syntax_round_trips(self):
        title = 'A "quoted", synthetic title\nwith another line'
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = self.csv_storage({"data_dir": temp_dir})
            storage.save_content_analysis_data([{"title": title}])

            rows = asyncio.run(storage.get_latest_data("content_analysis"))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["title"], title)


if __name__ == "__main__":
    unittest.main()

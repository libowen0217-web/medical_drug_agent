from __future__ import annotations

import importlib.util
import inspect
import sys
import tempfile
import traceback
from pathlib import Path


def _load_module(file_path: Path):
    module_name = file_path.stem
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载测试文件：{file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _iter_test_functions(module):
    for name, obj in inspect.getmembers(module, inspect.isfunction):
        if name.startswith("test_") and obj.__module__ == module.__name__:
            yield name, obj


def _discover_test_files(project_root: Path) -> list[Path]:
    tests_dir = project_root / "tests"
    return sorted(tests_dir.glob("test_*.py")) if tests_dir.exists() else []


def _build_kwargs(test_func):
    kwargs = {}
    for name in inspect.signature(test_func).parameters:
        if name == "tmp_path":
            kwargs[name] = Path(tempfile.mkdtemp())
    return kwargs


def main() -> int:
    args = sys.argv[1:]
    project_root = Path.cwd()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    test_files = [Path(arg) for arg in args] if args else _discover_test_files(project_root)
    if not test_files:
        print("No test files found.")
        return 1

    total = 0
    failed = 0

    for file_path in test_files:
        if not file_path.exists():
            print(f"ERROR {file_path}: file not found")
            failed += 1
            continue

        module = _load_module(file_path)
        for name, test_func in _iter_test_functions(module):
            total += 1
            try:
                kwargs = _build_kwargs(test_func)
                test_func(**kwargs)
                print(f"PASS {file_path}::{name}")
            except Exception:
                failed += 1
                print(f"FAIL {file_path}::{name}")
                traceback.print_exc()

    print(f"\n{total - failed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

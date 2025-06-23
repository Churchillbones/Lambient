import importlib, sys, pathlib

# Ensure the src directory is discoverable
_project_root = pathlib.Path(__file__).resolve().parent.parent
_src_path = _project_root / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

# Re-export the real implementation package
_real_core = importlib.import_module("src.core")
sys.modules[__name__] = _real_core 
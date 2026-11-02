"""Lets ComfyUI load LongMai Tools when this whole repo is cloned into custom_nodes (Git URL install)."""
import importlib.util
import os
import sys

_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "custom_nodes", "ComfyUI-LongMai-Tools")
_NAME = __name__ + ".longmai_tools"

_spec = importlib.util.spec_from_file_location(_NAME, os.path.join(_DIR, "__init__.py"), submodule_search_locations=[_DIR])
_module = importlib.util.module_from_spec(_spec)
sys.modules[_NAME] = _module
_spec.loader.exec_module(_module)

NODE_CLASS_MAPPINGS = _module.NODE_CLASS_MAPPINGS
NODE_DISPLAY_NAME_MAPPINGS = _module.NODE_DISPLAY_NAME_MAPPINGS
WEB_DIRECTORY = "./custom_nodes/ComfyUI-LongMai-Tools/web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]

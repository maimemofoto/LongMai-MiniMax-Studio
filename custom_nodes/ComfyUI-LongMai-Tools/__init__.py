"""LongMai Tools: scene-aware frame interpolation and clip joining for MiniMax H3 workflows."""
import os

from aiohttp import web

import folder_paths
from server import PromptServer

from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

WEB_DIRECTORY = "./web"
VIDEO_EXT = (".mp4", ".mov", ".webm", ".mkv", ".avi", ".m4v")


@PromptServer.instance.routes.get("/longmai/videos")
async def longmai_list_videos(request):
    """Videos in ComfyUI/output (newest first) for the Join Clips picker."""
    root = folder_paths.get_output_directory()
    items = []
    for dirpath, _, files in os.walk(root):
        for f in files:
            if f.lower().endswith(VIDEO_EXT):
                p = os.path.join(dirpath, f)
                st = os.stat(p)
                items.append({"path": os.path.relpath(p, root).replace("\\", "/"), "size": st.st_size, "mtime": st.st_mtime})
    items.sort(key=lambda x: x["mtime"], reverse=True)
    return web.json_response(items[:500])


__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]

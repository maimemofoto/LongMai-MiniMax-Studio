# Adapted from DENO Custom Nodes v0.7.126 (https://github.com/Deno2026/comfyui-deno-custom-nodes), GPL-3.0-only.
# Modified for ComfyUI-LongMai-Tools on 2026-11-08: reduced to one positive conditioning lane and a single node file.
import inspect

import comfy.model_management as mm


class LongMaiTextEncoderUnload:
    """Passes the conditioning through, then frees the connected text encoder only."""

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"conditioning": ("CONDITIONING",), "clip": ("CLIP",)}}

    RETURN_TYPES = ("CONDITIONING",)
    RETURN_NAMES = ("conditioning",)
    FUNCTION = "run"
    CATEGORY = "LongMai"

    def run(self, conditioning, clip):
        patcher = getattr(clip, "patcher", None)
        if patcher is None:
            raise RuntimeError("LongMai Text Encoder Unload: this CLIP input has no patcher")
        if patcher.load_device == patcher.offload_device and str(patcher.load_device).lower() != "cpu":
            raise RuntimeError("LongMai Text Encoder Unload: start ComfyUI without --gpu-only")
        unload = mm.unload_model_and_clones
        params = inspect.signature(unload).parameters
        if "all_devices" in params or any(p.kind is inspect.Parameter.VAR_KEYWORD for p in params.values()):
            unload(patcher, all_devices=True)
        else:
            unload(patcher)
        mm.soft_empty_cache()
        return (conditioning,)

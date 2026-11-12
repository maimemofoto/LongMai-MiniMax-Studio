from .h3_tiled_sampler import LongMaiH3TiledSampler
from .te_unload import LongMaiTextEncoderUnload

NODE_CLASS_MAPPINGS = {"LongMaiH3TiledSampler": LongMaiH3TiledSampler, "LongMaiTextEncoderUnload": LongMaiTextEncoderUnload}
NODE_DISPLAY_NAME_MAPPINGS = {"LongMaiH3TiledSampler": "LongMai H3 Tiled Sampler (by DENO, GPL-3.0)", "LongMaiTextEncoderUnload": "LongMai Text Encoder Unload (from DENO, GPL-3.0)"}

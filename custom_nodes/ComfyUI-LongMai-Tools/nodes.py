"""LongMai Tools nodes.

LongMai Scene-Aware RIFE
    2x frame interpolation (24 -> 48 fps) that never blends across a hard cut. Interpolation itself is done by the
    installed "RIFE VFI" node (comfyui-frame-interpolation). At every detected cut the in-between frame is a copy of
    the last frame of the outgoing shot, and one extra copy of the final frame is appended, so the output always has
    exactly 2N frames and stays in sync with audio: N / 24 == 2N / 48.

LongMai Join Clips
    Concatenates finished clips with ffmpeg. Sound can come from each clip, or from ONE song file that is cut to the
    exact video length of every clip in order (so the music is continuous and never skips or repeats at a seam).
    Clips are normalised to the first clip's size and fps. Optional short crossfade.
"""
import json
import os
import shutil
import subprocess

import torch

import folder_paths
import nodes as comfy_nodes


def _cut_scores(frames: torch.Tensor) -> torch.Tensor:
    """Mean absolute difference between consecutive frames on a small grayscale proxy. frames: [N,H,W,C] in 0..1."""
    x = frames[..., :3].mean(dim=-1, keepdim=True).permute(0, 3, 1, 2)  # N,1,H,W
    x = torch.nn.functional.interpolate(x, size=(72, 128), mode="area")
    return (x[1:] - x[:-1]).abs().mean(dim=(1, 2, 3))  # N-1


def detect_cuts(frames: torch.Tensor, threshold: float, ratio: float):
    """A pair (i, i+1) is a cut when its difference is both large in absolute terms and a spike vs. its neighbours."""
    s = _cut_scores(frames.float())
    cuts = []
    for i in range(len(s)):
        lo, hi = max(0, i - 4), min(len(s), i + 5)
        neigh = torch.cat([s[lo:i], s[i + 1:hi]])
        local = float(neigh.median()) if len(neigh) else 0.0
        if float(s[i]) >= threshold and float(s[i]) >= ratio * max(local, 1e-4):
            cuts.append(i)
    return cuts, [round(float(v), 4) for v in s]


class LongMaiSceneAwareRIFE:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "frames": ("IMAGE",),
            "ckpt_name": (["rife49.pth", "rife47.pth", "rife417.pth", "rife426.pth"], {"default": "rife49.pth"}),
            "cut_threshold": ("FLOAT", {"default": 0.07, "min": 0.0, "max": 1.0, "step": 0.005,
                                        "tooltip": "Minimum mean frame difference (0-1) for a hard cut."}),
            "cut_ratio": ("FLOAT", {"default": 3.0, "min": 1.0, "max": 50.0, "step": 0.5,
                                    "tooltip": "A cut must also be this many times larger than nearby frame differences."}),
            "dtype": (["float32", "float16", "bfloat16"], {"default": "float16"}),
            "batch_size": ("INT", {"default": 4, "min": 1, "max": 64}),
        }}

    RETURN_TYPES = ("IMAGE", "FLOAT", "STRING")
    RETURN_NAMES = ("frames_48fps", "fps", "report")
    FUNCTION = "run"
    CATEGORY = "LongMai"

    def run(self, frames, ckpt_name, cut_threshold, cut_ratio, dtype, batch_size):
        n = frames.shape[0]
        if n < 2:
            return (frames, 48.0, json.dumps({"frames_in": n, "cuts": []}))
        cuts, scores = detect_cuts(frames, cut_threshold, cut_ratio)
        rife_cls = comfy_nodes.NODE_CLASS_MAPPINGS.get("RIFE VFI")
        if rife_cls is None:
            raise RuntimeError("LongMai Scene-Aware RIFE needs the 'RIFE VFI' node (comfyui-frame-interpolation).")
        out = rife_cls().vfi(ckpt_name=ckpt_name, frames=frames, clear_cache_after_n_frames=10, multiplier=2,
                             fast_mode=True, ensemble=True, scale_factor=1.0, dtype=dtype,
                             torch_compile=False, batch_size=batch_size)[0]
        # RIFE output for multiplier 2 is [f0, m01, f1, m12, ..., f_{n-1}] -> 2n-1 frames
        if out.shape[0] != 2 * n - 1:
            raise RuntimeError(f"Unexpected RIFE output length {out.shape[0]} for {n} input frames")
        out = out.clone()
        for i in cuts:  # replace the blended in-between frame of a hard cut with the last frame of the old shot
            out[2 * i + 1] = out[2 * i]
        out = torch.cat([out, out[-1:]], dim=0)  # 2n frames: same duration as the 24 fps source
        report = {"frames_in": n, "frames_out": int(out.shape[0]), "cuts_at_source_frame": [i + 1 for i in cuts],
                  "cut_seconds": [round((i + 1) / 24, 3) for i in cuts], "threshold": cut_threshold, "ratio": cut_ratio,
                  "max_score": max(scores) if scores else 0}
        return (out, 48.0, json.dumps(report))


def _ffmpeg():
    exe = shutil.which("ffmpeg") or r"C:\ffmpeg\ffmpeg.exe"
    probe = shutil.which("ffprobe") or r"C:\ffmpeg\ffprobe.exe"
    return exe, probe


def _probe(probe, path):
    out = subprocess.run([probe, "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,r_frame_rate,duration", "-of", "json", path],
                         capture_output=True, text=True, check=True).stdout
    s = json.loads(out)["streams"][0]
    num, den = s["r_frame_rate"].split("/")
    return int(s["width"]), int(s["height"]), float(num) / float(den), float(s["duration"])


def _mean_rgb(ff, path, start, length):
    """Average RGB (0-255) over [start, start+length] seconds, on a tiny proxy."""
    raw = subprocess.run([ff, "-v", "error", "-ss", f"{max(start, 0):.3f}", "-t", f"{length:.3f}", "-i", path,
                          "-vf", "scale=32:18:flags=area,format=rgb24", "-f", "rawvideo", "-"],
                         capture_output=True, check=True).stdout
    if not raw:
        return None
    t = torch.frombuffer(bytearray(raw), dtype=torch.uint8).float().view(-1, 3)
    return t.mean(dim=0).tolist()


def _resolve(path):
    path = path.strip().strip('"')
    if os.path.isabs(path) and os.path.exists(path):
        return path
    for base in (folder_paths.get_output_directory(), folder_paths.get_input_directory()):
        p = os.path.join(base, path)
        if os.path.exists(p):
            return p
    raise FileNotFoundError(f"LongMai: file not found: {path} (looked in ComfyUI/output and ComfyUI/input)")


class LongMaiJoinClips:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "clips": ("STRING", {"multiline": True, "default": "LongMai/part1_final_48fps_00001_.mp4\nLongMai/part2_final_48fps_00001_.mp4",
                                 "tooltip": "One clip per line, in order. Paths are relative to ComfyUI/output (or input), or absolute."}),
            "audio_source": (["one song file (exact cut per clip)", "each clip's own audio", "no audio"],),
            "song_file": ("STRING", {"default": "omoi_full.wav", "tooltip": "Song in ComfyUI/input (or absolute path)."}),
            "song_start_seconds": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 3600.0, "step": 0.001}),
            "crossfade_seconds": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 2.0, "step": 0.01,
                                            "tooltip": "0 = clean hard cut (recommended for live-session cuts)."}),
            "match_color": ("BOOLEAN", {"default": True,
                                        "tooltip": "Scale each clip's colours so its first 0.5 s matches the last 0.5 s of the previous clip (removes brightness jumps at seams)."}),
            "filename_prefix": ("STRING", {"default": "LongMai/joined"}),
            "crf": ("INT", {"default": 14, "min": 0, "max": 40}),
        }, "optional": {
            "color_max_change": ("FLOAT", {"default": 0.15, "min": 0.0, "max": 0.6, "step": 0.01,
                                           "tooltip": "Match Color only corrects small seam differences. If a seam needs more than this "
                                                      "(e.g. day -> sunset, an intentional lighting change) that seam is left untouched."}),
            "seam_audio_fade_ms": ("INT", {"default": 30, "min": 0, "max": 500,
                                           "tooltip": "Tiny fade-out/in at each seam when using each clip's own audio (removes clicks). 0 = off."}),
        }}

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("saved_path", "report")
    FUNCTION = "run"
    OUTPUT_NODE = True
    CATEGORY = "LongMai"

    def run(self, clips, audio_source, song_file, song_start_seconds, crossfade_seconds, filename_prefix, crf,
            match_color=True, color_max_change=0.15, seam_audio_fade_ms=30):
        ff, probe = _ffmpeg()
        paths = [_resolve(p) for p in clips.splitlines() if p.strip()]
        if not paths:
            raise ValueError("LongMai Join Clips: no clips listed")
        infos = [_probe(probe, p) for p in paths]
        w, h, fps, _ = infos[0]
        gains, skipped = [[1.0, 1.0, 1.0]], []
        for k in range(1, len(paths)):
            g = [1.0, 1.0, 1.0]
            if match_color:
                prev = _mean_rgb(ff, paths[k - 1], infos[k - 1][3] - 0.5, 0.5)
                head = _mean_rgb(ff, paths[k], 0.0, 0.5)
                if prev and head:  # chain: the previous clip is itself already corrected by gains[k-1]
                    g = [min(1.6, max(0.6, p * pg / max(hd, 1.0))) for p, pg, hd in zip(prev, gains[k - 1], head)]
                    if max(abs(x - 1.0) for x in g) > color_max_change:  # intentional lighting change: keep the clip as is
                        g = [1.0, 1.0, 1.0]
                        skipped.append(k + 1)
            gains.append(g)
        args = [ff, "-y", "-loglevel", "error"]
        for p in paths:
            args += ["-i", p]
        song = None
        if audio_source.startswith("one song"):
            song = _resolve(song_file)
            args += ["-i", song]
        vparts, aparts, t = [], [], song_start_seconds
        for k, (cw, ch, cfps, dur) in enumerate(infos):
            gr, gg, gb = gains[k]
            cc = f"format=rgb24,colorchannelmixer=rr={gr:.4f}:gg={gg:.4f}:bb={gb:.4f}," if gains[k] != [1.0, 1.0, 1.0] else ""
            vparts.append(f"[{k}:v:0]scale={w}:{h}:flags=lanczos,fps={fps},setsar=1,{cc}format=yuv420p,setpts=PTS-STARTPTS[v{k}]")
            if song:
                aparts.append(f"[{len(paths)}:a:0]atrim={t:.6f}:{t + dur:.6f},asetpts=PTS-STARTPTS,aresample=48000[a{k}]")
                t += dur
            elif audio_source.startswith("each"):
                fd = seam_audio_fade_ms / 1000.0
                fades = ""
                if fd > 0 and len(paths) > 1 and crossfade_seconds <= 0:
                    fades = (f",afade=t=in:d={fd:.3f}" if k > 0 else "") +                             (f",afade=t=out:st={max(dur - fd, 0):.6f}:d={fd:.3f}" if k < len(paths) - 1 else "")
                aparts.append(f"[{k}:a:0]atrim=0:{dur:.6f},asetpts=PTS-STARTPTS,aresample=48000{fades}[a{k}]")
        n = len(paths)
        fc = ";".join(vparts + aparts)
        has_audio = bool(aparts)
        if crossfade_seconds > 0 and n > 1:
            offset, vl, al = 0.0, "[v0]", "[a0]" if has_audio else None
            for k in range(1, n):
                offset += infos[k - 1][3] - crossfade_seconds
                fc += f";{vl}[v{k}]xfade=transition=fade:duration={crossfade_seconds}:offset={offset:.6f}[vx{k}]"
                vl = f"[vx{k}]"
                if has_audio:
                    fc += f";{al}[a{k}]acrossfade=d={crossfade_seconds}[ax{k}]"
                    al = f"[ax{k}]"
            maps = ["-map", vl] + (["-map", al] if has_audio else [])
        else:
            fc += ";" + "".join(f"[v{k}]" + (f"[a{k}]" if has_audio else "") for k in range(n))
            fc += f"concat=n={n}:v=1:a={1 if has_audio else 0}[v]" + ("[a]" if has_audio else "")
            maps = ["-map", "[v]"] + (["-map", "[a]"] if has_audio else [])
        full_out, filename, counter, subfolder, _ = folder_paths.get_save_image_path(filename_prefix, folder_paths.get_output_directory())
        out_name = f"{filename}_{counter:05}_.mp4"
        out_path = os.path.join(full_out, out_name)
        args += ["-filter_complex", fc] + maps + ["-c:v", "libx264", "-crf", str(crf), "-preset", "slow",
                                                  "-pix_fmt", "yuv420p"]
        if has_audio:
            args += ["-c:a", "aac", "-b:a", "256k"]
        args += [out_path]
        subprocess.run(args, check=True)
        report = {"clips": [{"file": p, "size": f"{i[0]}x{i[1]}", "fps": round(i[2], 3), "seconds": round(i[3], 3)} for p, i in zip(paths, infos)],
                  "output": out_path, "audio": audio_source, "song": song, "song_start": song_start_seconds,
                  "song_end_used": round(t, 3) if song else None, "crossfade": crossfade_seconds,
                  "color_gains_rgb": [[round(x, 3) for x in g] for g in gains],
                  "color_skipped_clips (lighting change)": skipped}
        return {"ui": {"gifs": [{"filename": out_name, "subfolder": subfolder, "type": "output", "format": "video/h264-mp4"}]},
                "result": (out_path, json.dumps(report, ensure_ascii=False))}


class LongMaiLoadStage1Latent:
    """Loads the Stage-1 AV latent saved by 'H3 Motion Context Save Latent' (tensors 'video' + 'audio') and returns it
    as a native H3 nested AV latent, ready for LTXVSeparateAVLatent / Stage 2. Lets Stage 2 run without re-running
    Stage 1 (after a restart, another workflow, etc.)."""

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"latent_file": ("STRING", {"default": "LongMai/stage1_latent/last_00001.safetensors",
                                                         "tooltip": "Relative to ComfyUI/output (or absolute)."})}}

    RETURN_TYPES = ("LATENT", "STRING")
    RETURN_NAMES = ("av_latent", "info")
    FUNCTION = "load"
    CATEGORY = "LongMai"

    @classmethod
    def IS_CHANGED(cls, latent_file):
        try:
            p = _resolve(latent_file)
            return f"{p}:{os.stat(p).st_mtime_ns}"
        except Exception:
            return float("NaN")

    def load(self, latent_file):
        from safetensors.torch import load_file
        import comfy.nested_tensor
        path = _resolve(latent_file)
        t = load_file(path)
        if "video" not in t or "audio" not in t:
            raise ValueError(f"{path} is not an H3 AV latent (needs 'video' and 'audio' tensors)")
        video, audio = t["video"].clone(), t["audio"].clone()
        info = {"file": path, "video": list(video.shape), "audio": list(audio.shape),
                "saved": os.path.getmtime(path)}
        return ({"samples": comfy.nested_tensor.NestedTensor((video, audio))}, json.dumps(info))


NODE_CLASS_MAPPINGS = {
    "LongMaiSceneAwareRIFE": LongMaiSceneAwareRIFE,
    "LongMaiJoinClips": LongMaiJoinClips,
    "LongMaiLoadStage1Latent": LongMaiLoadStage1Latent,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "LongMaiSceneAwareRIFE": "LongMai Scene-Aware RIFE (48 fps, clean cuts)",
    "LongMaiJoinClips": "LongMai Join Clips (seamless song)",
    "LongMaiLoadStage1Latent": "LongMai Load Stage-1 Latent (upscale without re-generating)",
}

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
    raise FileNotFoundError(f"LongMai: หาไฟล์ไม่เจอ: {path} (ค้นใน ComfyUI/output และ ComfyUI/input แล้ว) — ตรวจชื่อไฟล์ในช่อง clips / song_file")


class LongMaiJoinClips:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "clips": ("STRING", {"multiline": True, "default": "",
                                 "tooltip": "One clip per line, in order. Paths are relative to ComfyUI/output (or input), or absolute."}),
            "audio_source": (["one song file (exact cut per clip)", "each clip's own audio", "no audio"],),
            "song_file": ("STRING", {"default": "", "tooltip": "Song in ComfyUI/input (or absolute path)."}),
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
            raise ValueError("LongMai Join Clips: ยังไม่ได้ใส่คลิป — กด 📂 เลือกคลิปจาก output / ⬆️ เลือกคลิปจากเครื่อง หรือพิมพ์ path บรรทัดละ 1 คลิป")
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


STAGE1_LATENT_DIR = "LongMai/stage1_latent"
LATEST = "(ล่าสุด)"


def _stage1_latents():
    """Saved Stage-1 latents, newest first, as paths relative to ComfyUI/output."""
    root = os.path.join(folder_paths.get_output_directory(), *STAGE1_LATENT_DIR.split("/"))
    if not os.path.isdir(root):
        return []
    files = [f for f in os.listdir(root) if f.endswith(".safetensors")]
    files.sort(key=lambda f: os.path.getmtime(os.path.join(root, f)), reverse=True)
    return [f"{STAGE1_LATENT_DIR}/{f}" for f in files]


def _pick_stage1_latent(latent_file):
    if latent_file.strip() in ("", LATEST):
        files = _stage1_latents()
        if not files:
            raise FileNotFoundError(f"LongMai: ยังไม่มี Stage 1 ที่บันทึกไว้ใน output/{STAGE1_LATENT_DIR} — เจน Stage 1 ก่อน")
        latent_file = files[0]
    return _resolve(latent_file)


def _safe_label(text):
    """Keep letters/digits/vowel & tone marks (any script, e.g. Thai) plus - and _; everything else becomes '-'."""
    import unicodedata
    out = "".join(c if (c.isalnum() or c in "-_" or unicodedata.category(c).startswith("M")) else "-"
                  for c in text.strip())
    while "--" in out:
        out = out.replace("--", "-")
    return out.strip("-_")


class LongMaiSaveStage1Latent:
    """Saves the Stage-1 AV latent under a unique name '<label>_<yyMMdd-HHmmss>_s<seed>' and returns that name, so
    the preview clip, the latent and the final 24/48 fps clips of one generation all share it."""

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "latent": ("LATENT",),
            "stage1_seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff,
                                    "tooltip": "Seed of Stage 1 (goes into the file name)."}),
            "label": ("STRING", {"default": "",
                                 "tooltip": "ชื่องาน (ไม่ใส่ก็ได้) เช่น beach_p1 — จะขึ้นหน้าชื่อไฟล์ทุกไฟล์ของการเจนนี้"}),
        }}

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("name", "latent_path")
    FUNCTION = "save"
    OUTPUT_NODE = True
    CATEGORY = "LongMai"

    def save(self, latent, stage1_seed, label=""):
        import time
        from safetensors.torch import save_file
        samples = latent["samples"]
        parts = list(samples.unbind()) if hasattr(samples, "unbind") else list(samples)
        if len(parts) < 2:
            raise ValueError("LongMai: latent นี้ไม่มีเสียง — ต่อจาก output ของ Sampler Stage 1 (H3 AV latent)")
        lab = _safe_label(label)
        name = (f"{lab}_" if lab else "") + f"{time.strftime('%y%m%d-%H%M%S')}_s{stage1_seed}"
        folder = os.path.join(folder_paths.get_output_directory(), *STAGE1_LATENT_DIR.split("/"))
        os.makedirs(folder, exist_ok=True)
        base, k = name, 2
        while os.path.exists(os.path.join(folder, name + ".safetensors")):
            name, k = f"{base}_{k}", k + 1
        path = os.path.join(folder, name + ".safetensors")
        save_file({"video": parts[0].cpu().contiguous(), "audio": parts[1].cpu().contiguous()}, path,
                  metadata={"format": "h3_motion_context_av_v1"})
        return (name, path)


def _call_node(name, **kw):
    """Run any registered ComfyUI node (legacy or V3 schema) in-process and return its outputs as a tuple."""
    cls = comfy_nodes.NODE_CLASS_MAPPINGS.get(name)
    if cls is None:
        raise RuntimeError(f"LongMai Face Refine: node '{name}' is not installed")
    if hasattr(cls, "define_schema"):
        out = cls.execute(**kw)
        return tuple(out.args) if hasattr(out, "args") else tuple(out)
    return tuple(getattr(cls(), cls.FUNCTION)(**kw))


POSITION_WORDS = {"ซ้าย": "left_most", "left": "left_most", "ขวา": "right_most", "right": "right_most",
                  "ใหญ่": "largest_face", "ใหญ่สุด": "largest_face", "largest": "largest_face",
                  "เล็ก": "smallest_face", "เล็กสุด": "smallest_face", "smallest": "smallest_face",
                  "บน": "top_most", "top": "top_most", "ล่าง": "bottom_most", "bottom": "bottom_most"}


def _load_face(path):
    """Identity image as IMAGE. A grey border is added so a tightly cropped face is still found by insightface's
    detector (it misses faces that fill the whole picture)."""
    from PIL import Image, ImageOps
    import numpy as np
    p = path.strip().strip('"')
    if not os.path.isabs(p):
        p = os.path.join(folder_paths.get_input_directory(), p)
    if not os.path.exists(p):
        raise FileNotFoundError(f"LongMai Face Refine: หาภาพหน้าไม่เจอ: {path} (ค้นใน ComfyUI/input แล้ว)")
    im = ImageOps.exif_transpose(Image.open(p)).convert("RGB")
    pad = int(0.4 * max(im.size))
    im = ImageOps.expand(im, border=pad, fill=(128, 128, 128))
    return torch.from_numpy(np.asarray(im).astype("float32") / 255.0)[None]


def _centres(transform):
    """{source frame: (cx, cy, w)} of the tracked crop box."""
    src = transform.get("source") or list(range(len(transform["boxes"])))
    return {int(f): (b[0] + b[2] / 2.0, b[1] + b[3] / 2.0, b[2]) for f, b in zip(src, transform["boxes"])}


def _same_person(t_new, t_old):
    """True when two tracks follow the same face for most of their shared frames."""
    a, b = _centres(t_new), _centres(t_old)
    common = [f for f in a if f in b]
    if not common:
        return False
    close = sum(1 for f in common
                if ((a[f][0] - b[f][0]) ** 2 + (a[f][1] - b[f][1]) ** 2) ** 0.5 < 0.3 * max(a[f][2], b[f][2]))
    return close >= 0.6 * len(common)


class LongMaiFaceRefineMulti:
    """H3 Face Refine for any number of people in one node (needs ComfyUI-H3-FaceRefine).

    faces empty -> refine the largest face in frame (1 pass).
    faces lines -> one pass per line, in order. A line is either a face image (identity match with insightface) or a
                   position word: ซ้าย/left, ขวา/right, ใหญ่/largest, เล็ก/smallest, บน/top, ล่าง/bottom.
    Each pass tracks that person, crops the face large, re-generates it with H3 at low denoise with the clip's own
    audio locked (lip-sync kept), and stitches it back. A person who is not in the clip, a face image without a
    detectable face, or a pass that would land on someone already refined is skipped (an identity pass that lands on
    an already-refined face first retries on the other side of the frame), so extra lines never break a run."""

    SKIP_MARKERS = ("No face detected in any frame", "not containing the subject")

    @classmethod
    def INPUT_TYPES(cls):
        opt = {f"ref_image_{i}": ("IMAGE",) for i in range(1, 10)}
        opt.update({f"ref_audio_{i}": ("AUDIO",) for i in range(1, 4)})
        return {"required": {
            "images": ("IMAGE", {"tooltip": "Stage 2 frames"}),
            "audio": ("AUDIO", {"tooltip": "The clip's own audio (locked, keeps lip-sync)"}),
            "model": ("MODEL",),
            "clip": ("CLIP",),
            "vae": ("VAE",),
            "audio_vae": ("VAE",),
            "prompt": ("STRING", {"forceInput": True}),
            "faces": ("STRING", {"multiline": True, "default": "",
                                 "tooltip": "คนที่จะแก้หน้า บรรทัดละ 1 คน (ใส่กี่คนก็ได้): ภาพหน้าของคนนั้น หรือคำบอกตำแหน่ง "
                                            "ซ้าย / ขวา / ใหญ่ / เล็ก / บน / ล่าง · ว่าง = แก้หน้าใหญ่สุด 1 คน · "
                                            "คนที่ไม่มีในคลิปหรือซ้ำกับคนที่แก้แล้วจะถูกข้ามเอง"}),
            "steps": ("INT", {"default": 6, "min": 1, "max": 50}),
            "denoise": ("FLOAT", {"default": 0.4, "min": 0.05, "max": 1.0, "step": 0.01,
                                  "tooltip": "0.3 อ่อน · 0.4 ปกติ · 0.5 แรง (หน้าเล็กแก้เต็มค่านี้ หน้าใหญ่แก้ 35%)"}),
            "refine_seed": ("INT", {"default": 771, "min": 0, "max": 0xffffffffffffffff}),
            "identity_threshold": ("FLOAT", {"default": 0.28, "min": 0.0, "max": 1.0, "step": 0.01,
                                             "tooltip": "ความเหมือนขั้นต่ำที่ถือว่าเป็นคนเดียวกัน (insightface)"}),
            "crop_factor": ("FLOAT", {"default": 2.5, "min": 1.5, "max": 4.0, "step": 0.1}),
        }, "optional": opt}

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("images", "report")
    FUNCTION = "run"
    CATEGORY = "LongMai"

    def run(self, images, audio, model, clip, vae, audio_vae, prompt, faces, steps, denoise, refine_seed,
            identity_threshold, crop_factor, **refs):
        import comfy.model_management as mm
        M = comfy_nodes.NODE_CLASS_MAPPINGS
        for need in ("H3FaceTrackCrop", "H3InjectVideoLatent", "H3PerFrameDenoise", "H3FaceStitch"):
            if need not in M:
                raise RuntimeError("LongMai Face Refine: ต้องติดตั้ง ComfyUI-H3-FaceRefine ก่อน "
                                   "(https://github.com/Carasibana/ComfyUI-H3-FaceRefine)")
        track = M["H3FaceTrackCrop"]()
        spec = track.INPUT_TYPES()
        req = {**spec.get("required", {}), **spec.get("optional", {})}
        det = next((d for d in req["detector"][0] if os.path.basename(d) == "face_yolov8m.pt"), req["detector"][0][0])
        fb = next((d for d in (req.get("fallback_detector") or [["none"]])[0] if "person_yolov8m-seg" in d), "none")
        ref_images = {f"ref_image_{i}": refs[f"ref_image_{i + 1}"] for i in range(9) if refs.get(f"ref_image_{i + 1}") is not None}
        ref_audios = {f"ref_audio_{i}": refs[f"ref_audio_{i + 1}"] for i in range(3) if refs.get(f"ref_audio_{i + 1}") is not None}
        W = int(images.shape[2])

        def do_track(cur, face, select):
            return track.run(
                images=cur, detector=det, confidence=0.35, crop_factor=crop_factor, canvas_width=768,
                canvas_height=768, canvas_mode="auto_capped_768", smooth_window=21, size_smooth_window=51,
                smooth_method="gaussian", size_mode="per_frame", select=select, fallback_detector=fb,
                fallback_head_frac=0.5, identity_reference=face, identity_threshold=identity_threshold,
                identity_track=True, identity_model="insightface", cut_detection="auto (pyscenedetect)",
                cut_threshold=3.0, absent_shots="by_identity" if face is not None else "off")

        lines_in = [ln.strip() for ln in (faces or "").splitlines() if ln.strip() and not ln.strip().startswith("#")]
        passes = []
        for ln in lines_in:
            key = ln.lower()
            if key in POSITION_WORDS:
                passes.append((ln, None, POSITION_WORDS[key]))
            else:
                passes.append((ln, _load_face(ln), "largest_face"))
        passes = passes or [("หน้าใหญ่สุด", None, "largest_face")]

        cur, done, report = images, [], []
        for k, (label, face, select) in enumerate(passes, start=1):
            mm.throw_exception_if_processing_interrupted()
            tag = f"คนที่ {k} ({os.path.basename(label)})"
            try:
                crops, transform, _p, trep, cw, ch, fc = do_track(cur, face, select)
            except ValueError as e:
                if any(s in str(e) for s in self.SKIP_MARKERS):
                    report.append(f"{tag}: ข้าม — ไม่พบคนนี้ในคลิป")
                    continue
                raise
            if face is not None and "found no face in identity_reference" in str(trep):
                report.append(f"{tag}: ข้าม — ภาพหน้านี้ตรวจหาหน้าไม่เจอ (ใช้ภาพหน้าตรงที่ชัดกว่านี้)")
                continue
            if any(_same_person(transform, t) for t in done):
                retried = False
                if face is not None:   # identity is unreliable on small faces: try the other side of the frame
                    pts = [c[0] for t in done for c in _centres(t).values()]
                    alt = "right_most" if sum(pts) / len(pts) < W / 2 else "left_most"
                    try:
                        crops, transform, _p, trep, cw, ch, fc = do_track(cur, None, alt)
                        retried = not any(_same_person(transform, t) for t in done)
                    except ValueError:
                        retried = False
                    if retried:
                        tag += f" → เทียบหน้าไม่ชัด ใช้คน{'ขวา' if alt == 'right_most' else 'ซ้าย'}แทน"
                if not retried:
                    report.append(f"{tag}: ข้าม — เป็นคนเดียวกับที่แก้ไปแล้ว")
                    continue
            positive, latent = _call_node("MiniMaxH3ReferenceToVideo", clip=clip, prompt=prompt, width=int(cw),
                                          height=int(ch), length=int(fc), ref_image_size="match", vae=vae,
                                          audio_vae=audio_vae, ref_images=ref_images or None,
                                          ref_audios=ref_audios or None)[:2]
            av = M["H3InjectVideoLatent"]().run(av_latent=latent, images=crops, vae=vae)[0]
            enc = dict(_call_node("VAEEncodeAudio", vae=audio_vae, audio=audio)[0])
            enc["noise_mask"] = torch.zeros((1, 1, 512, 512))      # audio stays exactly as recorded
            av = _call_node("LTXVConcatAVLatent", video_latent=av, audio_latent=enc)[0]
            av, _prep, pmodel = M["H3PerFrameDenoise"]().run(
                model=model, av_latent=av, transform=transform, denoise_multiplier_small_face=1.0,
                denoise_multiplier_large_face=0.35, face_px_small=30, face_px_large=120, gamma=1.0,
                smooth_frames=9, scale_mode="absolute_px")
            sigmas = _call_node("BasicScheduler", model=pmodel, scheduler="simple", steps=steps, denoise=denoise)[0]
            sampler = _call_node("KSamplerSelect", sampler_name="euler")[0]
            noise = _call_node("RandomNoise", noise_seed=refine_seed + k - 1)[0]
            guider = _call_node("BasicGuider", model=pmodel, conditioning=positive)[0]
            out = _call_node("SamplerCustomAdvanced", noise=noise, guider=guider, sampler=sampler, sigmas=sigmas,
                             latent_image=av)[0]
            dec = _call_node("VAEDecode", vae=vae, samples=out)[0]
            cur = M["H3FaceStitch"]().run(base_images=cur, refined_crops=dec, transform=transform,
                                          paste_region="face_only", mask_dilation=24, feather=24, colour_match=1.0,
                                          blend=1.0, undetected_frames="fade_out")[0]
            done.append(transform)
            xs = [c[0] for c in _centres(transform).values()]
            side = "ซ้าย" if sum(xs) / len(xs) < W / 2 else "ขวา"
            report.append(f"{tag}: แก้แล้ว — คนฝั่ง{side}, canvas {cw}x{ch}, {fc} เฟรม")
        text = "\n".join(report) or "ไม่ได้แก้หน้า"
        print("[LongMai Face Refine]\n" + text)
        return (cur, text)


class LongMaiHDRExport:
    """Extra HDR copy of the finished clip: NVIDIA RTX TrueHDR (SDR -> HDR) + 10-bit BT.2020 HLG (or PQ) MP4.
    Uses the 48 fps frames when they exist, otherwise the 24 fps frames; with neither connected (Stage 2 off) it does
    nothing, so it can stay switched on without breaking preview runs. The normal SDR files are not touched."""

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "luminance": ("INT", {"default": 650, "min": 400, "max": 2000,
                                  "tooltip": "ความสว่างสูงสุดของจอ HDR (nits) · 650 = ค่าตัวอย่างของ NVIDIA · 1000 = จอ HDR สว่างมาก"}),
            "contrast": ("INT", {"default": 100, "min": 0, "max": 200}),
            "saturation": ("INT", {"default": 100, "min": 0, "max": 200}),
            "middle_gray": ("INT", {"default": 50, "min": 10, "max": 100}),
            "debanding": ("BOOLEAN", {"default": True}),
            "hdr_format": (["HDR (HLG)", "HDR PQ (HDR10)"], {"default": "HDR (HLG)",
                           "tooltip": "HLG = ดูบนจอธรรมดาได้ดีกว่า (แนะนำ) · PQ = HDR10 สำหรับจอ/แพลตฟอร์ม HDR โดยเฉพาะ"}),
        }, "optional": {
            "images_48": ("IMAGE", {"tooltip": "48 fps frames (used first)"}),
            "images_24": ("IMAGE", {"tooltip": "24 fps frames (used when 48 fps is off)"}),
            "audio": ("AUDIO",),
            "prefix_48": ("STRING", {"forceInput": True}),
            "prefix_24": ("STRING", {"forceInput": True}),
        }}

    RETURN_TYPES = ()
    FUNCTION = "run"
    OUTPUT_NODE = True
    CATEGORY = "LongMai"

    def run(self, luminance, contrast, saturation, middle_gray, debanding, hdr_format,
            images_48=None, images_24=None, audio=None, prefix_48=None, prefix_24=None):
        if images_48 is not None:
            images, fps, prefix = images_48, 48, (prefix_48 or "LongMai/final/clip_48fps_final")
        elif images_24 is not None:
            images, fps, prefix = images_24, 24, (prefix_24 or "LongMai/final/clip_24fps")
        else:
            print("[LongMai HDR] ไม่มีภาพเข้า (ปิด Stage 2 อยู่) — ข้าม")
            return {"ui": {}}
        space = "HDR PQ" if "PQ" in hdr_format else "HDR"
        hdr = _call_node("RTXTrueHDR", images=images, contrast=contrast, saturation=saturation,
                         middle_gray=middle_gray, luminance=luminance, debanding=debanding,
                         output_colorspace=space)[0]
        video = _call_node("CreateVideo", images=hdr, fps=float(fps), audio=audio, bit_depth="auto",
                           color_space=space, codec="none")[0]
        from comfy_api.latest import Types
        h, w = int(hdr.shape[1]), int(hdr.shape[2])
        # "…_48fps_final" -> "…_48fps_HDR_final" (the HDR copy of the final clip); other prefixes just get "_HDR"
        hdr_prefix = prefix[:-len("_final")] + "_HDR_final" if prefix.endswith("_final") else prefix + "_HDR"
        folder, filename, counter, subfolder, _ = folder_paths.get_save_image_path(
            hdr_prefix, folder_paths.get_output_directory(), w, h)
        file = f"{filename}_{counter:05}_.mp4"
        video.save_to(os.path.join(folder, file), format=Types.VideoContainer.MP4, codec=Types.VideoCodec.H264)
        print(f"[LongMai HDR] saved {subfolder}/{file} ({w}x{h}, {fps} fps, {space}, 10-bit)")
        return {"ui": {"images": [{"filename": file, "subfolder": subfolder, "type": "output"}], "animated": [True]}}


class LongMaiMatchFrameCount:
    """Makes an interpolated clip exactly (source frames x multiplier) long, so it stays in sync with the audio:
    N / 24 s == (N x 2) / 48 s. Frame generators return (N-1) x M + 1 frames; the missing tail is filled with copies
    of the last frame (extra frames are trimmed)."""

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "images": ("IMAGE",),
            "source_images": ("IMAGE", {"tooltip": "The clip before interpolation (its frame count is the reference)."}),
            "multiplier": ("INT", {"default": 2, "min": 1, "max": 16}),
        }}

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "run"
    CATEGORY = "LongMai"

    def run(self, images, source_images, multiplier):
        target = int(source_images.shape[0]) * int(multiplier)
        n = int(images.shape[0])
        if n > target:
            images = images[:target]
        elif n < target:
            images = torch.cat([images, images[-1:].repeat(target - n, 1, 1, 1)], dim=0)
        return (images,)


class LongMaiOutputNames:
    """Turns a generation name into the file-name prefixes of every clip it produces."""

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "name": ("STRING", {"forceInput": True}),
            "folder": ("STRING", {"default": "LongMai", "tooltip": "Folder inside ComfyUI/output"}),
        }}

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("preview_prefix", "final24_prefix", "final48_prefix")
    FUNCTION = "run"
    CATEGORY = "LongMai"

    def run(self, name, folder="LongMai"):
        f = folder.strip().strip("/\\") or "LongMai"
        return (f"{f}/stage1/{name}_preview", f"{f}/final/{name}_24fps", f"{f}/final/{name}_48fps_final")


class LongMaiLoadStage1Latent:
    """Loads a saved Stage-1 AV latent (tensors 'video' + 'audio') and returns it as a native H3 nested AV latent,
    ready for LTXVSeparateAVLatent / Stage 2. Lets Stage 2 run without re-running Stage 1 (after a restart, another
    workflow, etc.). '(ล่าสุด)' = the newest file in output/LongMai/stage1_latent. Also returns the file's name so the
    upscaled clips keep the same name as their Stage-1 preview."""

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"latent_file": ([LATEST] + _stage1_latents(), {
            "default": LATEST,
            "tooltip": "เลือกให้ชื่อตรงกับคลิป preview ที่ชอบ · (ล่าสุด) = ไฟล์ใหม่สุด · กด R เพื่ออัปเดตรายการ"})}}

    RETURN_TYPES = ("LATENT", "STRING", "STRING")
    RETURN_NAMES = ("av_latent", "info", "name")
    FUNCTION = "load"
    CATEGORY = "LongMai"

    @classmethod
    def VALIDATE_INPUTS(cls, latent_file):
        return True  # any path is allowed (scripts pass their own); a missing file is reported when loading

    @classmethod
    def IS_CHANGED(cls, latent_file):
        try:
            p = _pick_stage1_latent(latent_file)
            return f"{p}:{os.stat(p).st_mtime_ns}"
        except Exception:
            return float("NaN")

    def load(self, latent_file):
        from safetensors.torch import load_file
        import comfy.nested_tensor
        path = _pick_stage1_latent(latent_file)
        t = load_file(path)
        if "video" not in t or "audio" not in t:
            raise ValueError(f"{path} is not an H3 AV latent (needs 'video' and 'audio' tensors)")
        video, audio = t["video"].clone(), t["audio"].clone()
        info = {"file": path, "video": list(video.shape), "audio": list(audio.shape),
                "saved": os.path.getmtime(path)}
        name = os.path.splitext(os.path.basename(path))[0]
        return ({"samples": comfy.nested_tensor.NestedTensor((video, audio))}, json.dumps(info), name)


NODE_CLASS_MAPPINGS = {
    "LongMaiSceneAwareRIFE": LongMaiSceneAwareRIFE,
    "LongMaiJoinClips": LongMaiJoinClips,
    "LongMaiLoadStage1Latent": LongMaiLoadStage1Latent,
    "LongMaiSaveStage1Latent": LongMaiSaveStage1Latent,
    "LongMaiOutputNames": LongMaiOutputNames,
    "LongMaiMatchFrameCount": LongMaiMatchFrameCount,
    "LongMaiFaceRefineMulti": LongMaiFaceRefineMulti,
    "LongMaiHDRExport": LongMaiHDRExport,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "LongMaiSceneAwareRIFE": "LongMai Scene-Aware RIFE (48 fps, clean cuts)",
    "LongMaiJoinClips": "LongMai Join Clips (seamless song)",
    "LongMaiLoadStage1Latent": "LongMai Load Stage-1 Latent (upscale without re-generating)",
    "LongMaiSaveStage1Latent": "LongMai Save Stage-1 Latent (named by time + seed)",
    "LongMaiOutputNames": "LongMai Output Names (preview / 24fps / 48fps)",
    "LongMaiMatchFrameCount": "LongMai Match Frame Count (keep 48 fps in sync with audio)",
    "LongMaiFaceRefineMulti": "LongMai Face Refine (any number of faces)",
    "LongMaiHDRExport": "LongMai HDR Export (RTX TrueHDR, extra HDR file)",
}

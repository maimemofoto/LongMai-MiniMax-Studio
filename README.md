# LongMai MiniMax Studio

Workflow ComfyUI สำหรับสร้างวิดีโอพร้อมเสียงด้วย **MiniMax H3 (Reference-to-Video + Audio)** ใช้ได้ทั้งคนจริงและการ์ตูน/3D อัปสเกล 2 ขั้น ทำ 48 fps และต่อหลายคลิปเป็นวิดีโอยาวได้

## ไฟล์ใน repo

| ไฟล์ | ใช้ทำอะไร |
|---|---|
| `workflows/LongMai MiniMax Studio FINAL V3.1.json` | **ตัวหลักปัจจุบัน** — สูตร DMAD 4-step (คมกว่า V3 เร็วกว่า 2–3 เท่า) · Force Audio · First/Last Frame · 🎲 Seed Stage 2 · 48 fps NVIDIA · สวิตช์ ⚡ โหมดเร็ว และ 🧩 ประหยัด VRAM |
| `workflows/LongMai H3ZeroStudio.json` | หน้าตัดต่อแบบไทม์ไลน์ ([H3ZeroStudio](https://github.com/zeroleloushe/H3ZeroStudio)) ด้วยสูตรเดียวกับ V3.1 — ทำหลาย part ต่อกันเนียนในงานเดียว · สวิตช์ ⚡ / 🧩 / 🎞 48 fps |
| `workflows/LongMai Join Clips.json` | ต่อหลายคลิปเป็นวิดีโอยาว |
| `workflows/… FINAL V3 / V3 LowVram / V2 / FINAL` | เวอร์ชันเก่า (V3 LowVram สำหรับการ์ด 8–12 GB) |
| `custom_nodes/ComfyUI-LongMai-Tools/` | custom node ของเรา (48 fps จำนวนเฟรมตรงเสียง, บันทึก/เลือก Stage 1, ชื่อไฟล์อัตโนมัติ, Join Clips) |
| `patches/H3ZeroStudio-LongMai/` | แพตช์ H3ZeroStudio: **UI ภาษาไทย** + ค่า σ 0.86 (คุณภาพเท่า V3.1) + ค่ากลาง V3.1 — ดู README ในโฟลเดอร์ |
| `คู่มือ_LongMai_Studio_V3.1.pdf` / `.md` | คู่มือ V3.1 |
| `คู่มือ_LongMai_H3ZeroStudio.pdf` | คู่มือ H3ZeroStudio (มีภาพประกอบ) |
| `วิธีติดตั้ง_LongMai_Studio.txt` | วิธีติดตั้ง V3.1 แบบละเอียด (ข้อความเดียวกับ note 📦 ใน workflow) |
| `คู่มือ_LongMai_Studio.md` | คู่มือเก่าของ V2 / V3 |

## ติดตั้ง

ต้องใช้ **ComfyUI 0.42 ขึ้นไป** · ffmpeg สำหรับ Join Clips · 48 fps ต้องใช้การ์ด **NVIDIA RTX 40 ขึ้นไป** (การ์ดต่ำกว่านั้นปิดสวิตช์ 48 fps ได้)

### 1. ComfyUI-LongMai-Tools
ใช้วิธี**คัดลอก** ไม่ใช่ git clone หรือ Manager: กด **Code → Download ZIP** → แตกไฟล์ → คัดลอก `custom_nodes/ComfyUI-LongMai-Tools` ไปวางใน `ComfyUI/custom_nodes/` (ไม่ต้อง pip install)

### 2. Custom nodes อื่น
ง่ายสุด: เปิด workflow → Manager → **Install Missing Custom Nodes** → ติดตั้งทุกตัว → รีสตาร์ต
หรือ git clone เอง (รายการเต็ม + ใช้ทำอะไร อยู่ใน note 📦 ของแต่ละ workflow และ `วิธีติดตั้ง_LongMai_Studio.txt`)

| Custom node | V3.1 | H3ZeroStudio |
|---|---|---|
| [ComfyUI-KJNodes](https://github.com/kijai/ComfyUI-KJNodes) | ✓ | ✓ |
| [ComfyUI-Pixaroma](https://github.com/pixaroma/ComfyUI-Pixaroma) | ✓ | |
| [ComfyUI-Easy-Use](https://github.com/yolain/ComfyUI-Easy-Use) | ✓ | |
| [rgthree-comfy](https://github.com/rgthree/rgthree-comfy) | ✓ | ✓ |
| [Fantastic MiniMax H3 PromptBuilder](https://github.com/Adudeguyman/ComfyUI-Fantastic-MiniMaxH3-PromptBuilder) | ✓ | |
| [H3 Prompt IDE](https://github.com/ethanfel/ComfyUI-H3-Prompt-IDE) | ✓ | |
| [MiniMax H3 Audio T8](https://github.com/T8mars/comfyui-minimax-h3-audio-T8) | ✓ | |
| [H3-Optimizations](https://github.com/Zironic/H3-Optimizations) | ✓ | |
| [MiniMax H3 Latent Upscaler](https://github.com/LBH-123-AI/Comfyui_Minimax_h3_latent_Upscaler) | ✓ | ✓ |
| [Nvidia RTX Nodes](https://github.com/Comfy-Org/Nvidia_RTX_Nodes_ComfyUI) (48 fps) | ✓ | ✓ |
| [H3ZeroStudio](https://github.com/zeroleloushe/H3ZeroStudio) | | ✓ |

### 3. โมเดล
| ไฟล์ | วางที่ | ดาวน์โหลด |
|---|---|---|
| `Minimax-h3_Singularity_ref2va_v2_pruned_int8.safetensors` | `models/diffusion_models/` | [WarmBloodAban/Minimax-h3_Singularity](https://huggingface.co/WarmBloodAban/Minimax-h3_Singularity) |
| `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` | `models/text_encoders/` | [Comfy-Org/MiniMax-H3](https://huggingface.co/Comfy-Org/MiniMax-H3) |
| `minimax_h3_video_vae_int8_convrot.safetensors` | `models/vae/` | [Kijai/MiniMax-H3-experimental](https://huggingface.co/Kijai/MiniMax-H3-experimental) |
| `minimax_h3_audio_vae_fp32.safetensors` | `models/vae/` | [Comfy-Org/MiniMax-H3](https://huggingface.co/Comfy-Org/MiniMax-H3) |
| `minimax_h3_DMAD_4step_full_lora_avg_rank_39_bf16.safetensors` | `models/loras/` | [Kijai/MiniMax-H3-experimental](https://huggingface.co/Kijai/MiniMax-H3-experimental) (loras) |
| `minimax_h3_latent_upscaler_3d_conv_v1_fp16` (V3.1) / `…_3d_bf16` (H3ZeroStudio) | `models/latent_upscale_models/` | [LBH-123-AI/Minimax_h3_latent_Upscaler](https://huggingface.co/LBH-123-AI/Minimax_h3_latent_Upscaler) |
| `BUNNY_H3_ActionLogic_Bridge_V1_T8_Compat.safetensors` (V3.1) | `models/semantic_bridge/t8_compat/` | [t8star/Semantic-Bridge-Comfy](https://huggingface.co/t8star/Semantic-Bridge-Comfy) |
| `h3-realism-people-t2v-i2v-r2v.safetensors` (ไม่บังคับ — โหมดสมจริง) | `models/loras/` | [fal/MiniMax-H3-Realism-People-LoRA](https://huggingface.co/fal/MiniMax-H3-Realism-People-LoRA) |

## ค่าที่ทดสอบแล้ว (V3.1, RTX 5080 16GB, คลิป 12 วิ)
- **Stage 1:** DMAD 4-step 1.0 · er_sde / beta / 6 steps / 0.4MP — ~3 นาที
- **Stage 2:** er_sde / linear_quadratic / 2 steps / denoise 0.4 / 1.0MP + 48 fps — ~3 นาที

## เครดิต

ขอบคุณผู้พัฒนาโมเดลและ custom node ทุกตัวที่ระบุลิงก์ไว้ด้านบน ได้แก่ MiniMax, Comfy-Org, AIGC-Singularity, WarmBloodAban, Kijai, fal, T8star, LBH-123-AI, Zironic, pixaroma, yolain, rgthree, ethanfel, Adudeguyman และ zeroleloushe (H3ZeroStudio, GPL-3.0)

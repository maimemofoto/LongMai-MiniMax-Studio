# LongMai MiniMax Studio

Workflow ComfyUI สำหรับสร้างวิดีโอพร้อมเสียงด้วย **MiniMax H3 (Reference-to-Video + Audio)** ใช้ได้ทั้งคนจริงและการ์ตูน/3D อัปสเกล 2 ขั้น ทำ 48 fps แบบตัดช็อตสะอาด และต่อหลายคลิปเป็นวิดีโอยาวได้

## ความสามารถ

- **โหมดสมจริง / การ์ตูน:** สวิตช์เดียวเปิด/ปิด Realism LoRA พร้อม trigger word (`r34l1sm`) ให้อัตโนมัติ
- **ภาพ / วิดีโอ / เสียงอ้างอิง:** ใส่ `<Picture 1..9>`, `<Video 1..3>`, `<Audio 1..3>` ผ่าน Media Loader แล้วอ้างถึงใน prompt
- **Force Audio:** บังคับให้ร้องหรือขยับปากตามเพลงที่ใส่ (`<Audio 1>`) และล็อกเสียงไว้ตอนอัปสเกลด้วย
- **อัปสเกล 2 ขั้น:** Stage 1 ทำ Preview ที่ 0.4MP ส่วน Stage 2 อัปสเกล latent เป็น 1.0MP (1376x768)
- **อัปสเกลจากคลิปที่บันทึกไว้:** Stage 1 ถูกบันทึกอัตโนมัติ จะกลับมาอัปสเกลทีหลังได้โดยไม่ต้องเจนใหม่ แม้รีสตาร์ตเครื่องไปแล้ว
- **48 fps ตัดช็อตสะอาด:** RIFE ทีละช็อต ไม่มีเฟรมภาพซ้อนตรงจุดตัด และจำนวนเฟรมพอดีกับเสียง
- **🔔 เสียงแจ้งเตือน:** ดังเมื่อ Preview เสร็จ และเมื่ออัปสเกลเสร็จทั้งหมด
- **Join Clips:** ต่อหลายคลิปเป็นวิดีโอเดียว ใช้เพลงไฟล์เดียวที่ตัดตรงตามแต่ละ part ได้ ปรับสีรอยต่ออัตโนมัติ (ข้ามรอยต่อที่ตั้งใจเปลี่ยนแสง)

## ไฟล์ใน repo

| ไฟล์ | ใช้ทำอะไร |
|---|---|
| `workflows/LongMai MiniMax Studio FINAL.json` | workflow หลัก |
| `workflows/LongMai Join Clips.json` | ต่อหลายคลิปเป็นวิดีโอยาว |
| `custom_nodes/ComfyUI-LongMai-Tools/` | custom node ของ workflow นี้ (48 fps ตัดช็อตสะอาด, โหลด Stage 1 ที่บันทึกไว้, Join Clips) |
| `วิธีติดตั้ง_LongMai_Studio.txt` | วิธีติดตั้งแบบละเอียด (ข้อความเดียวกับ note 📦 ใน workflow) |

## ติดตั้ง

ต้องใช้ **ComfyUI 0.37 ขึ้นไป** (มี node MiniMax H3 ในตัว) และ **ffmpeg** สำหรับ Join Clips

### 1. ComfyUI-LongMai-Tools (custom node ของ workflow นี้)
ตัวนี้ใช้วิธี**คัดลอก** ไม่ใช่ git clone หรือ Manager
1. ดาวน์โหลด repo นี้: กด **Code → Download ZIP** แล้วแตกไฟล์
2. คัดลอกโฟลเดอร์ `custom_nodes/ComfyUI-LongMai-Tools` ไปวางใน `ComfyUI/custom_nodes/`
3. เปิดไฟล์ในโฟลเดอร์ `workflows/` ด้วย ComfyUI (ลากไฟล์ใส่หน้าจอได้เลย)

> ⚠️ อย่า git clone repo นี้ลงใน `custom_nodes/` ตรงๆ เพราะ ComfyUI จะหา node ไม่เจอ (node อยู่ในโฟลเดอร์ย่อย) และตัวนี้ไม่ต้อง pip install

### 2. Custom nodes อื่น (ต้องไปอยู่ใน `ComfyUI/custom_nodes/`)

**วิธี A (แนะนำ): ComfyUI Manager**
เปิด workflow แล้วกด Manager → **Install Missing Custom Nodes** → ติดตั้งทุกตัว → รีสตาร์ต ComfyUI
Manager จะ git clone ลง `custom_nodes/` และติดตั้งไลบรารีที่ต้องใช้ให้เอง

**วิธี B: git clone เอง**
1. เปิด Terminal ที่โฟลเดอร์ `ComfyUI/custom_nodes`
2. clone ทีละตัว (โฟลเดอร์ที่ได้จะอยู่ใน `custom_nodes/` เอง):
```bash
git clone https://github.com/kijai/ComfyUI-KJNodes
git clone https://github.com/pixaroma/ComfyUI-Pixaroma
git clone https://github.com/yolain/ComfyUI-Easy-Use
git clone https://github.com/rgthree/rgthree-comfy
git clone https://github.com/Adudeguyman/ComfyUI-Fantastic-MiniMaxH3-PromptBuilder
git clone https://github.com/ethanfel/ComfyUI-H3-Prompt-IDE
git clone https://github.com/T8mars/comfyui-minimax-h3-audio-T8
git clone https://github.com/NikoDemon80/ComfyUI-H3-Motion-Context
git clone https://github.com/LBH-123-AI/Comfyui_Minimax_h3_latent_Upscaler
git clone https://github.com/Fannovel16/ComfyUI-Frame-Interpolation
```
3. ติดตั้งไลบรารีของแต่ละ node โดยใช้ **python ของ ComfyUI เอง** (ไม่ใช่ python ของเครื่อง)
   - ตัวที่มี `requirements.txt`: KJNodes, Pixaroma, Easy-Use, rgthree, Fantastic PromptBuilder, Audio T8
   - **ComfyUI portable** (รันจากโฟลเดอร์ `custom_nodes`):
     ```bash
     ..\..\python_embeded\python.exe -m pip install -r ComfyUI-KJNodes\requirements.txt
     ```
     (เปลี่ยน `ComfyUI-KJNodes` เป็นชื่อโฟลเดอร์ของแต่ละตัว)
   - **ComfyUI แบบ venv:** เปิด venv ก่อน แล้วรัน `pip install -r <ชื่อโฟลเดอร์>/requirements.txt`
   - **ComfyUI-Frame-Interpolation:** เข้าโฟลเดอร์นั้นแล้วรัน `python install.py` (ด้วย python ของ ComfyUI)
4. รีสตาร์ต ComfyUI

| Custom node | ใช้ทำอะไร |
|---|---|
| [ComfyUI-KJNodes](https://github.com/kijai/ComfyUI-KJNodes) | เสียงแจ้งเตือน, Chunk / Low VRAM |
| [ComfyUI-Pixaroma](https://github.com/pixaroma/ComfyUI-Pixaroma) | สวิตช์กลุ่ม, LoRA loader, ป้ายหัว |
| [ComfyUI-Easy-Use](https://github.com/yolain/ComfyUI-Easy-Use) | ปุ่ม 🎲 seed |
| [rgthree-comfy](https://github.com/rgthree/rgthree-comfy) | Any Switch |
| [Fantastic MiniMax H3 PromptBuilder](https://github.com/Adudeguyman/ComfyUI-Fantastic-MiniMaxH3-PromptBuilder) | Media Loader |
| [H3 Prompt IDE](https://github.com/ethanfel/ComfyUI-H3-Prompt-IDE) | ช่องเขียน Prompt |
| [MiniMax H3 Audio T8](https://github.com/T8mars/comfyui-minimax-h3-audio-T8) | Action Bridge, AV Decode |
| [H3 Motion Context](https://github.com/NikoDemon80/ComfyUI-H3-Motion-Context) | บันทึก Stage 1 |
| [MiniMax H3 Latent Upscaler](https://github.com/LBH-123-AI/Comfyui_Minimax_h3_latent_Upscaler) | อัปสเกล Stage 2 |
| [ComfyUI-Frame-Interpolation](https://github.com/Fannovel16/ComfyUI-Frame-Interpolation) | RIFE 48 fps |

### 3. โมเดล
| ไฟล์ | วางที่ | ดาวน์โหลด |
|---|---|---|
| `Minimax-h3_Singularity_ref2va_Pruned_v1.3_int8.safetensors` (19.6 GB) | `models/diffusion_models/` | [WarmBloodAban/Minimax-h3_Singularity](https://huggingface.co/WarmBloodAban/Minimax-h3_Singularity) (หรือใช้ `minimax_h3_ref2va_pruned_int8_convrot` จาก [Comfy-Org](https://huggingface.co/Comfy-Org/MiniMax-H3)) |
| `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` (14.6 GB) | `models/text_encoders/` | [Comfy-Org/MiniMax-H3](https://huggingface.co/Comfy-Org/MiniMax-H3) |
| `minimax_h3_video_vae_fp16.safetensors` | `models/vae/` | [Comfy-Org/MiniMax-H3](https://huggingface.co/Comfy-Org/MiniMax-H3) |
| `minimax_h3_audio_vae_fp32.safetensors` | `models/vae/` | [Comfy-Org/MiniMax-H3](https://huggingface.co/Comfy-Org/MiniMax-H3) |
| `minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors` | `models/loras/` | [Comfy-Org/MiniMax-H3](https://huggingface.co/Comfy-Org/MiniMax-H3) หรือ [lightx2v/Minimax-h3-Turbo](https://huggingface.co/lightx2v/Minimax-h3-Turbo) |
| `h3-realism-people-t2v-i2v-r2v.safetensors` | `models/loras/` | [fal/MiniMax-H3-Realism-People-LoRA](https://huggingface.co/fal/MiniMax-H3-Realism-People-LoRA) |
| `minimax_h3_latent_upscaler_3d_conv_v1_fp16.safetensors` | `models/latent_upscale_models/` | [LBH-123-AI/Minimax_h3_latent_Upscaler](https://huggingface.co/LBH-123-AI/Minimax_h3_latent_Upscaler) |
| `BUNNY_H3_ActionLogic_Bridge_V1_T8_Compat.safetensors` | `models/semantic_bridge/t8_compat/` | [t8star/Semantic-Bridge-Comfy](https://huggingface.co/t8star/Semantic-Bridge-Comfy) |
| `rife49.pth` | โหลดให้อัตโนมัติตอนใช้ครั้งแรก | — |

**LoRA เสริม** (Cinematic Realism / Motion Repair / Combat V2 / GunFu / LMS): ไม่บังคับ ปิดไว้ในแถว LoRA ไม่มีก็ใช้งานได้ปกติ

> 💡 ใน workflow ต้นฉบับ LoRA ถูกเก็บในโฟลเดอร์ย่อย (เช่น `loras/MINIMAX/Turbo/`) ถ้าคุณวางไฟล์ไว้ตรงๆ ใน `models/loras/` ให้กดเลือกไฟล์ใหม่ใน node LoRA ครั้งแรกที่เปิดใช้

## วิธีใช้ (ย่อ)

1. **ใส่ไฟล์อ้างอิง:** ใส่ภาพ / เพลง / วิดีโอใน Media Loader (①) แล้วอ้างถึงใน prompt ด้วย `<Picture 1>`, `<Audio 1>` ...
2. **เลือกสไตล์:** สวิตช์ **โหมดสมจริง** เปิดไว้ = คนจริง ปิด = การ์ตูน / 3D
3. **ทำ Preview:** กด 🎲 แล้ว Run จะได้ Preview Stage 1 (🔔 ดัง)
4. **อัปสเกล:** ชอบผลแล้ว เปิดสวิตช์ **อัปสเกล** (Stage 2 และ 48 fps) แล้ว Run อีกครั้ง (🔔 ดังเมื่อเสร็จทั้งหมด)
   - ถ้ารีสตาร์ตหรือรัน workflow อื่นคั่นไปแล้ว ให้เลือกสวิตช์ **"ใช้ Stage 1 ล่าสุดที่บันทึกไว้"** จะไม่ต้องเจน Stage 1 ใหม่
5. **ร้องตามเพลง:** เปิด **Force Audio**
6. **ทำคลิปยาว:** ทำทีละ part (ทำ 48 fps ทีละ part) แล้วต่อด้วย workflow **LongMai Join Clips** จะใส่กี่คลิปก็ได้ ใส่คลิปได้ 3 วิธี:
   - **📂 เลือกคลิปจาก output:** คลิกไฟล์ตามลำดับที่จะต่อ (มีเลขกำกับ) แล้วกด "เพิ่มคลิปที่เลือก"
   - **⬆️ เลือกคลิปจากเครื่อง** หรือ **ลากไฟล์วิดีโอมาวางบน node:** ระบบอัปโหลดไปไว้ที่ `input/longmai_join/` และเรียงตามชื่อไฟล์ให้เอง
   - **พิมพ์หรือวาง path เอง:** บรรทัดละ 1 คลิป (นับจาก `ComfyUI/output` หรือใช้ path เต็มจาก Copy as path ก็ได้)

ผลลัพธ์อยู่ที่ `ComfyUI/output/LongMai/`

### ค่าที่ทดสอบแล้ว (RTX 5080 16GB)
- **Stage 1:** euler / simple / 6 steps / 0.4MP ใช้เวลาประมาณ 5–7 นาทีต่อคลิป 15 วินาที
- **Stage 2:** euler / simple / 4 steps / denoise 0.4 / 1.0MP รวม 48 fps แล้วใช้เวลาประมาณ 12–18 นาทีต่อคลิป 15 วินาที
- **Action Bridge:** 0.10
- **Turbo ref2v 4-step:** 1.0
- **Realism People:** 0.75 (เฉพาะโหมดสมจริง)

## เครดิต

ขอบคุณผู้พัฒนาโมเดลและ custom node ทุกตัวที่ระบุลิงก์ไว้ด้านบน ได้แก่ MiniMax, Comfy-Org, AIGC-Singularity, lightx2v, fal, T8star, LBH-123-AI, kijai, pixaroma, yolain, rgthree, Fannovel16, ethanfel, Adudeguyman และ NikoDemon80

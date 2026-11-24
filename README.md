# LongMai MiniMax Studio

Workflow ComfyUI สำหรับสร้างวิดีโอพร้อมเสียงด้วย **MiniMax H3**

| ไฟล์ | ใช้ทำอะไร |
|---|---|
| `workflows/LongMai MiniMax Studio FINAL V3.1.json` | ทำคลิปทีละช่วง เจนตัวอย่าง (Stage 1) ก่อน แล้วค่อยอัปสเกลและทำ 48 fps |
| `workflows/LongMai MiniMax Studio V3.2.json` | V3.1 ฉบับกะทัดรัด ผลเหมือนกัน แต่ค่าตั้งและสวิตช์ทั้งหมดรวมอยู่ใน Engine ก้อนเดียว |
| `workflows/LongMai MiniMax Studio V3.3.json` | V3.2 + Stage 2 แบบ Tiled: อัปสเกล 2 MP เร็วขึ้นบนการ์ด 16 GB ทำ 15 วินาทีรอบเดียวได้ |
| `workflows/LongMai MiniMax Studio V3.3.1.json` | V3.3 ที่ทำ 48 fps ด้วย RIFE ใช้ได้กับการ์ด NVIDIA ทุกรุ่น (RTX 20 / 30 / 40 / 50) |
| `workflows/LongMai MiniMax Studio V3.3.1 Low VRAM.json` | V3.3.1 ตั้งค่าเริ่มต้นสำหรับการ์ด 8–12 GB (base int4, Stage 2 1.2 MP, Chunking เปิด) |
| `workflows/LongMai MiniMax Studio V3.4.json` | V3.3 ที่เปลี่ยนชุดโมเดล: Base hybrid fl2va + ref2va, Turbo LoRA ของ MiniMax และ Cinema LoRA (โทนภาพยนตร์) |
| `workflows/LongMai H3ZeroStudio.json` | หน้าตัดต่อแบบไทม์ไลน์ ทำคลิปหลายท่อนให้ต่อเนื่องในงานเดียว |
| `คู่มือ_LongMai_Studio_V3.1.pdf` | คู่มือ V3.1 พร้อมรายการติดตั้ง |
| `คู่มือ_LongMai_Studio_V3.2.pdf` | คู่มือ V3.2 (แยกจาก V3.1) |
| `คู่มือ_LongMai_Studio_V3.3.pdf` | คู่มือ V3.3 (แยกจาก V3.2) |
| `คู่มือ_LongMai_Studio_V3.3.1.pdf` | คู่มือ V3.3.1 |
| `คู่มือ_LongMai_Studio_V3.3.1_Low_VRAM.pdf` | คู่มือ V3.3.1 Low VRAM |
| `คู่มือ_LongMai_Studio_V3.4.pdf` | คู่มือ V3.4 (ส่วนที่ต่างจาก V3.3) |
| `คู่มือ_LongMai_H3ZeroStudio.pdf` | คู่มือ H3ZeroStudio พร้อมรายการติดตั้ง |
| `custom_nodes/ComfyUI-LongMai-Tools/` | custom node ที่ทุก workflow ต้องใช้ (V3.2 ต้องใช้รุ่น 8 พ.ย. 2026 ขึ้นไป · V3.3 ต้องใช้รุ่น 12 พ.ย. 2026 ขึ้นไป · V3.3.1 ต้องใช้รุ่น 15 พ.ย. 2026 ขึ้นไป · V3.4 ต้องใช้รุ่น 12 พ.ย. 2026 ขึ้นไป) |
| `patches/H3ZeroStudio-LongMai/` | แพตช์ UI ภาษาไทยและค่ากลางของ H3ZeroStudio |

## เริ่มใช้งาน

1. ใช้ ComfyUI 0.42 ขึ้นไป (V3.1 / V3.2 / V3.3 แนะนำรุ่นล่าสุด ทดสอบบน 0.45)
2. กด **Code → Download ZIP** แล้วแตกไฟล์
3. ติดตั้ง node ของเรา `ComfyUI-LongMai-Tools` เลือกวิธีเดียว อย่าลงซ้ำ: เปิด Terminal ที่ `ComfyUI/custom_nodes` แล้วรัน `git clone https://github.com/maimemofoto/LongMai-MiniMax-Studio` หรือคัดลอกโฟลเดอร์ `custom_nodes/ComfyUI-LongMai-Tools` จาก ZIP ไปไว้ใน `ComfyUI/custom_nodes/`
4. เปิด workflow แล้วทำตามโน้ต 📦 ในนั้น หรือคู่มือ PDF ซึ่งบอกครบว่าต้องโหลด node และโมเดลอะไร วางไว้ที่ไหน
5. ถ้าใช้ H3ZeroStudio ให้ลงแพตช์ตามคู่มือ

48 fps ใน V3.1 / V3.2 / V3.3 ใช้ **ComfyUI Nvidia VFX Nodes** (github.com/Comfy-Org/ComfyUI_Nvidia_VFX_Nodes) ซึ่งทำ 48 fps ได้เฉพาะการ์ด RTX 40 / 50 และต้องใช้ PyTorch cu130 ขึ้นไป แต่ต้องลงไว้ทุกเครื่อง ไม่อย่างนั้น ComfyUI จะไม่ให้กด Run (ขึ้น Missing node: RTXVideoFrameGeneration) · การ์ดรุ่นอื่นใช้ **V3.3.1** แทน

ComfyUI รุ่นใหม่ไม่มี Manager มาให้: ติดตั้งด้วย `python -m pip install -U --pre comfyui-manager` แล้วเปิด ComfyUI ด้วย `--enable-manager` จึงจะกด Install Missing Custom Nodes ได้

## ค่าเริ่มต้น V3.1 / V3.2 สำหรับการ์ด 16 GB

ทดสอบบน RTX 5080 16 GB + RAM 64 GB ด้วยฉากเดียว แบบไม่แนบไฟล์อ้างอิง ผลอาจต่างตามฉากและเครื่อง

- ความยาว 8 วินาทีต่อ part
- Stage 1: 0.4 MP, 6 step
- Stage 2: 2.0 MP (1952x1088, 24 fps), 2 step, denoise 0.4
- Chunk Feed-Forward 8, Low VRAM Attention 8, Sparse Attention `sla` keep percent 10
- เวลา ราว 3.7–3.9 นาทีต่อ part (แนบภาพอ้างอิงแล้วราว 4–4.5 นาที)

ทุกผลทดสอบเปิด ComfyUI แบบกั๊ก VRAM 2 GB โดยเพิ่มคำสั่งนี้ในไฟล์ `.bat` ที่ใช้เปิด ComfyUI:

```
python main.py --reserve-vram 2
```

## V3.3: Stage 2 แบบ Tiled

V3.3 คือ V3.2 ที่เปลี่ยนการอัปสเกล (Stage 2) เป็นแบบ Tiled: แบ่งภาพเป็นแผ่นแล้วเกลาพร้อมกันทีละ step โมเดลและหน้าจอเหมือน V3.2 · V3.1, V3.2 และ V3.3 ให้ภาพคนละแบบ เลือกใช้ตามงาน

| | V3.2 | V3.3 |
|---|---|---|
| คลิป 8 วิ แนบภาพ 3 รูป + วิดีโอ 2 วิ + เสียง | 5.2 นาที | 3.9 นาที |
| คลิป 15 วิ | 10.3 นาที (แบ่ง 8 + 7) | 6.6 นาที (รอบเดียว) |
| Stage 2 | 2 step · denoise 0.4 | Tiled 1 step · Sigma 0.632 |

เจน 2 ขั้น (แนะนำ): ปิด 3 ปุ่มบน (⑤ ⑥ ④-B) แล้ว Run ได้ภาพพรีวิว → ชอบแล้วเปิด 3 ปุ่มบน แล้ว Run อีกครั้ง ระบบอัปสเกล Stage 1 ที่บันทึกไว้ + ทำ 48 fps ไม่ต้องเจนใหม่ · คลิป 15 วิ: 2:08 + 4:56 = 7:03 นาที (RTX 5080)

ทุกสวิตช์ของ V3.3 ทดสอบผ่านแล้ว (First / Last Frame, Force Audio, ใช้ Stage 1 ที่บันทึกไว้, 48 fps, ปิด LoRA Stage 2) รายละเอียดในคู่มือ V3.3

## V3.3.1 และ V3.3.1 Low VRAM

**V3.3.1** คือ V3.3 ที่เปลี่ยนตัวทำ 48 fps เป็น **RIFE** (ต้องลง [ComfyUI-Frame-Interpolation](https://github.com/Fannovel16/ComfyUI-Frame-Interpolation)) ใช้ได้กับการ์ด NVIDIA ทุกรุ่น ไม่ต้องลง ComfyUI Nvidia VFX Nodes และมี node ใหม่ **✂️ LongMai Shot Cut Fix** แทนเฟรมเบลอตรงรอยตัดช็อตให้คม ส่วนอื่นเหมือน V3.3 ทุกอย่าง

**V3.3.1 Low VRAM** คือ V3.3.1 ที่ตั้งค่าเริ่มต้นสำหรับการ์ด 8–12 GB: base `Minimax-h3_Singularity_ref2va_v1.3_Pruned_w4a8.safetensors` (int4, 11.8 GB จาก huggingface.co/WarmBloodAban/Minimax-h3_Singularity) · ⬆️ Stage 2 1.2 MP · 🧩 Chunking เปิด · แผ่น Tiled 768×512

| คลิป 21 วิ 9:16 (3 part × 7 วิ) อัปสเกล + 48 fps · RTX 5080 | เวลา |
|---|---|
| V3.3 | 10.6 นาที |
| V3.3.1 | 11.4 นาที |
| V3.3.1 Low VRAM จำลองการ์ด 8 GB (`--reserve-vram 8`) | 10.9 นาที |

ยังไม่ได้ทดสอบบนการ์ด 8 GB จริง รายละเอียดในคู่มือ V3.3.1 และคู่มือ V3.3.1 Low VRAM

## V3.4: โมเดล hybrid + Cinema LoRA

**V3.4** คือ V3.3 ที่เปลี่ยนชุดโมเดล ส่วนหน้าจอ Stage 2 แบบ Tiled, Ref Limit และ Force Audio เหมือน V3.3 ทุกอย่าง

| | ไฟล์ | โหลดจาก |
|---|---|---|
| Base | `models/diffusion_models/MinimaxH3/minimax_h3_hybrid_fl2va_ref2va_b30-49-int8.safetensors` | huggingface.co/smhfacct/Minimax-H3-fl2va-ref2va-hybrid-models |
| Turbo LoRA 1.0 (ต้องเปิดเสมอ) | `models/loras/MINIMAX/Turbo/minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors` | huggingface.co/Comfy-Org/MiniMax-H3 (โฟลเดอร์ loras) |
| Cinema LoRA 0.6 | `models/loras/MINIMAX/Mood/Cinema-MH3-V02_000010000.safetensors` | civitai.com/models/2849726 |

Trigger ใส่ให้อัตโนมัติ: `r34l1sm ,ASTROCINEMAV01K2T` · Realism LoRA 0.75 เหมือนเดิม

ผลทดสอบบน RTX 5080 16 GB: คลิป 8 วิ ใช้ 4.5 นาที (V3.3 4.7 นาที) · คลิป 45 วิ (3 × 15 วิ) ใช้ 19.8 นาที (V3.3 17.2 นาที) · ภาพโทนหนังกว่า สว่างและอุ่นกว่า V3.3
ถ้าใช้ part 15 วิ ให้ปิด ⑥ 48 fps ไว้ก่อน เพราะ 15 วิ + 48 fps บางครั้งใช้ RAM เกิน 95 % ของ 64 GB · รายละเอียดในคู่มือ V3.4

## ไฟล์อ้างอิง (🛡️ LongMai Ref Limit)

V3.1, V3.2 และ V3.3 มี node **LongMai Ref Limit** อยู่หลัง Media Loader เปิดไว้เป็นค่าเริ่มต้น ย่อไฟล์อ้างอิงให้อัตโนมัติตอน Run กัน VRAM ล้น ไฟล์ต้นฉบับไม่ถูกแก้

- รูป: ด้านยาวไม่เกิน 1024 px · ครอปหัว-ไหล่ใน Media Loader ได้หน้าเหมือนเท่ารูปเต็ม
- วิดีโอ: เก็บ 2 วินาทีท้าย ด้านสั้น 480 px · fps ไหนก็ได้ Media Loader แปลงเป็น 24 fps ให้
- ทดสอบ 3 รูป: รูปเต็ม 2560 ไม่ย่อ 10–13 นาทีต่อ part (VRAM ล้น) · ผ่าน node ราว 4–5 นาที
- ไม่แนะนำเสียงอ้างอิงในฉากที่มีหลายคน ทำให้พูดสลับคน

ต่อ 2 part ไฟล์อ้างอิง และข้อควรรู้เรื่องเสียง ดูในคู่มือ V3.1 หัวข้อ 9–11 หรือคู่มือ V3.2 หัวข้อ 8–10

## สัญญาอนุญาต

`custom_nodes/ComfyUI-LongMai-Tools/deno_port/` (🧱 Tiled Sampler และ Text Encoder Unload ที่ V3.3 ใช้) ดัดแปลงจาก [DENO Custom Nodes](https://github.com/Deno2026/comfyui-deno-custom-nodes) v0.7.126 สัญญาอนุญาต GPL-3.0 ComfyUI-LongMai-Tools จึงเผยแพร่ภายใต้ GPL-3.0 ดูไฟล์ `LICENSE` และ `deno_port/NOTICE.md` · ขอบคุณ DENO ผู้พัฒนาต้นฉบับ


แพตช์ใน `patches/H3ZeroStudio-LongMai/` อยู่ภายใต้ GPL-3.0 ตาม H3ZeroStudio ดูไฟล์ `LICENSE` ในโฟลเดอร์แพตช์

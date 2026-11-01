# LongMai MiniMax Studio

Workflow ComfyUI สำหรับสร้างวิดีโอพร้อมเสียงด้วย **MiniMax H3**

| ไฟล์ | ใช้ทำอะไร |
|---|---|
| `workflows/LongMai MiniMax Studio FINAL V3.1.json` | ทำคลิปทีละช่วง เจนตัวอย่าง (Stage 1) ก่อน แล้วค่อยอัปสเกลและทำ 48 fps |
| `workflows/LongMai H3ZeroStudio.json` | หน้าตัดต่อแบบไทม์ไลน์ ทำคลิปหลายท่อนให้ต่อเนื่องในงานเดียว |
| `คู่มือ_LongMai_Studio_V3.1.pdf` | คู่มือ V3.1 พร้อมรายการติดตั้ง |
| `คู่มือ_LongMai_H3ZeroStudio.pdf` | คู่มือ H3ZeroStudio พร้อมรายการติดตั้ง |
| `custom_nodes/ComfyUI-LongMai-Tools/` | custom node ที่ทั้งสอง workflow ต้องใช้ |
| `patches/H3ZeroStudio-LongMai/` | แพตช์ UI ภาษาไทยและค่ากลางของ H3ZeroStudio |

## เริ่มใช้งาน

1. ใช้ ComfyUI 0.42 ขึ้นไป
2. กด **Code → Download ZIP** แล้วแตกไฟล์
3. คัดลอก `custom_nodes/ComfyUI-LongMai-Tools` ไปไว้ใน `ComfyUI/custom_nodes/` (ห้าม git clone repo นี้ลง custom_nodes)
4. เปิด workflow แล้วทำตามโน้ต 📦 ในนั้น หรือคู่มือ PDF ซึ่งบอกครบว่าต้องโหลด node และโมเดลอะไร วางไว้ที่ไหน
5. ถ้าใช้ H3ZeroStudio ให้ลงแพตช์ตามคู่มือ

48 fps ต้องใช้การ์ด NVIDIA RTX 40 / 50 การ์ดรุ่นอื่นปิดส่วนนี้ได้

## สัญญาอนุญาต

แพตช์ใน `patches/H3ZeroStudio-LongMai/` อยู่ภายใต้ GPL-3.0 ตาม H3ZeroStudio ดูไฟล์ `LICENSE` ในโฟลเดอร์แพตช์

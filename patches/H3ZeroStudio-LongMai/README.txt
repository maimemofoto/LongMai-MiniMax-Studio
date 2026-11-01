แพตช์ LongMai สำหรับ H3ZeroStudio (https://github.com/zeroleloushe/H3ZeroStudio)

มีอะไร
• UI + หน้าวิธีใช้ ภาษาไทยทั้งหมด (แปลใหม่ทั้งชุด 2042 ข้อความ)
• ค่าความแรงการเกลา σ 0.86 (= denoise 0.4 ของ LongMai V3.1 — ต้นฉบับตั้งได้สูงสุด 0.80)
• โปรเจกต์ใหม่ใช้ 1.0 MP (1376x768) เป็นค่าเริ่มต้น
• ค่ากลางสูตร V3.1 (ComfyUI/output/h3zerostudio/_settings.json): 2 ขั้น · ร่าง 67% er_sde/beta 6 steps · เกลา σ0.86 / 2 steps / er_sde / linear_quadratic · ภาพอ้างอิง max

ใช้กับ H3ZeroStudio เวอร์ชัน commit c471f74 (21 ต.ค. 2026) เท่านั้น
ไฟล์ .py/.js ในแพตช์เป็นไฟล์ทั้งไฟล์ที่แก้จากเวอร์ชันนั้น ถ้าใช้กับเวอร์ชันอื่นอาจพัง

ติดตั้ง
1. ติดตั้ง H3ZeroStudio:  cd ComfyUI/custom_nodes
   git clone https://github.com/zeroleloushe/H3ZeroStudio ComfyUI-H3ZeroStudio
   cd ComfyUI-H3ZeroStudio  แล้ว  git checkout c471f74
   (ติดตั้งผ่าน Manager แล้วก็ได้ — แต่ต้อง checkout เป็น c471f74)
2. คัดลอกโฟลเดอร์ "ComfyUI" ในแพตช์นี้ ไปวางทับโฟลเดอร์ ComfyUI ของคุณ (ให้เขียนทับไฟล์เดิม)
   ถ้าไม่อยากทับค่ากลางของตัวเอง ให้ข้ามไฟล์ output/h3zerostudio/_settings.json
3. รีสตาร์ต ComfyUI แล้วกด Ctrl+Shift+R ในเบราว์เซอร์
4. หน้าตัดต่อ → ตั้งค่า → ภาษาหน้าตัดต่อ → ไทย

อย่ากด Update ให้ H3ZeroStudio ใน Manager — แพตช์จะหาย (ติดตั้งแพตช์ซ้ำได้ถ้าแพตช์รองรับเวอร์ชันใหม่แล้ว)

สัญญาอนุญาต: H3ZeroStudio เป็น GPL-3.0 (ไฟล์ LICENSE) ไฟล์ที่แก้ในแพตช์นี้เผยแพร่ภายใต้ GPL-3.0 เช่นกัน
แก้โดย LongMai: h3s_core.py, web/js/h3s_core.js, h3s_settings.js (σ 0.86 / 1.0 MP), ไฟล์ภาษาไทยทั้งหมด

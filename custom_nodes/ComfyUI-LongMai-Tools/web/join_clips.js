// LongMai Join Clips: pick clips from ComfyUI/output, upload clips from the computer, or drag & drop them onto the node.
import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

const VIDEO_RE = /\.(mp4|mov|webm|mkv|avi|m4v)$/i;
const naturalSort = (a, b) => a.localeCompare(b, undefined, { numeric: true, sensitivity: "base" });

function clipsWidget(node) {
    return node.widgets?.find((w) => w.name === "clips");
}

function appendClips(node, paths) {
    const w = clipsWidget(node);
    if (!w || !paths.length) return;
    const lines = (w.value || "").split(/\r?\n/).map((s) => s.trim()).filter(Boolean);
    w.value = [...lines, ...paths].join("\n");
    w.callback?.(w.value);
    node.setDirtyCanvas(true, true);
}

async function uploadFiles(node, files) {
    const vids = [...files].filter((f) => VIDEO_RE.test(f.name)).sort((a, b) => naturalSort(a.name, b.name));
    if (!vids.length) return;
    const done = [];
    for (const f of vids) {
        const body = new FormData();
        body.append("image", f, f.name);
        body.append("subfolder", "longmai_join");
        body.append("type", "input");
        body.append("overwrite", "true");
        const r = await api.fetchApi("/upload/image", { method: "POST", body });
        if (r.status !== 200) {
            alert(`อัปโหลดไม่สำเร็จ: ${f.name} (${r.status})`);
            continue;
        }
        const d = await r.json();
        done.push(`${d.subfolder ? d.subfolder + "/" : ""}${d.name}`);
    }
    appendClips(node, done);
}

function pickFromComputer(node) {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = "video/*";
    input.multiple = true;
    input.onchange = () => uploadFiles(node, input.files);
    input.click();
}

async function pickFromOutput(node) {
    const items = await (await api.fetchApi("/longmai/videos")).json();
    const order = [];
    const overlay = document.createElement("div");
    overlay.style.cssText = "position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:10000;display:flex;align-items:center;justify-content:center";
    const box = document.createElement("div");
    box.style.cssText = "background:#222;color:#ddd;border:1px solid #555;border-radius:8px;width:min(720px,92vw);max-height:80vh;display:flex;flex-direction:column;font:14px sans-serif";
    box.innerHTML = `<div style="padding:12px 16px;border-bottom:1px solid #444">
        <b>เลือกคลิปจาก ComfyUI/output</b><br><span style="color:#aaa;font-size:12px">คลิกตามลำดับที่ต้องการต่อ (ใหม่สุดอยู่บน) · คลิกซ้ำเพื่อเอาออก</span>
        <input placeholder="ค้นหาชื่อไฟล์ เช่น final48" style="margin-top:8px;width:100%;box-sizing:border-box;padding:6px;background:#111;color:#ddd;border:1px solid #555;border-radius:4px"></div>
        <div class="lm-list" style="overflow:auto;flex:1;padding:6px 0"></div>
        <div style="padding:10px 16px;border-top:1px solid #444;display:flex;gap:8px;justify-content:flex-end">
        <button class="lm-cancel">ยกเลิก</button><button class="lm-ok">เพิ่มคลิปที่เลือก</button></div>`;
    overlay.appendChild(box);
    const list = box.querySelector(".lm-list");
    const search = box.querySelector("input");
    const render = () => {
        const q = search.value.trim().toLowerCase();
        list.innerHTML = "";
        for (const it of items) {
            if (q && !it.path.toLowerCase().includes(q)) continue;
            const idx = order.indexOf(it.path);
            const row = document.createElement("div");
            row.style.cssText = `padding:6px 16px;cursor:pointer;display:flex;gap:10px;align-items:center;${idx >= 0 ? "background:#2d4a2d" : ""}`;
            const when = new Date(it.mtime * 1000).toLocaleString();
            row.innerHTML = `<span style="width:28px;text-align:center;font-weight:bold;color:#8f8">${idx >= 0 ? idx + 1 : ""}</span>
                <span style="flex:1;word-break:break-all">${it.path}</span>
                <span style="color:#888;font-size:12px;white-space:nowrap">${(it.size / 1048576).toFixed(1)} MB · ${when}</span>`;
            row.onclick = () => {
                const i = order.indexOf(it.path);
                if (i >= 0) order.splice(i, 1); else order.push(it.path);
                render();
            };
            list.appendChild(row);
        }
        if (!list.children.length) list.innerHTML = `<div style="padding:16px;color:#888">ไม่พบไฟล์วิดีโอ</div>`;
    };
    search.oninput = render;
    const close = () => overlay.remove();
    box.querySelector(".lm-cancel").onclick = close;
    box.querySelector(".lm-ok").onclick = () => { appendClips(node, order); close(); };
    overlay.onclick = (e) => { if (e.target === overlay) close(); };
    render();
    document.body.appendChild(overlay);
    search.focus();
}

app.registerExtension({
    name: "LongMai.JoinClips.Picker",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "LongMaiJoinClips") return;
        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const r = onNodeCreated?.apply(this, arguments);
            this.addWidget("button", "📂 เลือกคลิปจาก output (คลิกตามลำดับ)", null, () => pickFromOutput(this), { serialize: false });
            this.addWidget("button", "⬆️ เลือกคลิปจากเครื่อง (หลายไฟล์ได้)", null, () => pickFromComputer(this), { serialize: false });
            this.addWidget("button", "🧹 ล้างรายการคลิป", null, () => {
                const w = clipsWidget(this);
                if (w && confirm("ล้างรายการคลิปทั้งหมด?")) { w.value = ""; w.callback?.(""); this.setDirtyCanvas(true, true); }
            }, { serialize: false });
            for (const w of this.widgets) if (w.type === "button") w.serialize = false;
            return r;
        };
        // drag & drop video files onto the node -> upload to input/longmai_join/ and add to the list
        nodeType.prototype.onDragOver = function (e) {
            return !!e?.dataTransfer?.types?.includes?.("Files");
        };
        nodeType.prototype.onDragDrop = function (e) {
            const files = e?.dataTransfer?.files;
            if (!files?.length) return false;
            uploadFiles(this, files);
            return true;
        };
    },
});

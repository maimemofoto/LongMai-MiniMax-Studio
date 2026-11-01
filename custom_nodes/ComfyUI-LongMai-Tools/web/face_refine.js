// LongMai Face Refine (any number of faces): buttons to add face images / position words to the "faces" list.
import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

const IMAGE_RE = /\.(png|jpe?g|webp|bmp)$/i;

function facesWidget(node) {
    return node.widgets?.find((w) => w.name === "faces");
}

function appendLines(node, lines) {
    const w = facesWidget(node);
    if (!w || !lines.length) return;
    const cur = (w.value || "").split(/\r?\n/).map((s) => s.trim()).filter(Boolean);
    w.value = [...cur, ...lines].join("\n");
    w.callback?.(w.value);
    node.setDirtyCanvas(true, true);
}

async function uploadFaces(node, files) {
    const imgs = [...files].filter((f) => IMAGE_RE.test(f.name));
    const done = [];
    for (const f of imgs) {
        const body = new FormData();
        body.append("image", f, f.name);
        body.append("subfolder", "longmai_faces");
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
    appendLines(node, done);
}

function pickFaces(node) {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = "image/*";
    input.multiple = true;
    input.onchange = () => uploadFaces(node, input.files);
    input.click();
}

app.registerExtension({
    name: "LongMai.FaceRefineMulti",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "LongMaiFaceRefineMulti") return;
        const onCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const r = onCreated?.apply(this, arguments);
            this.addWidget("button", "⬆️ เพิ่มภาพหน้า (เลือกได้หลายภาพ / ลากภาพมาวาง)", null, () => pickFaces(this), { serialize: false });
            this.addWidget("button", "➕ คนซ้าย", null, () => appendLines(this, ["ซ้าย"]), { serialize: false });
            this.addWidget("button", "➕ คนขวา", null, () => appendLines(this, ["ขวา"]), { serialize: false });
            this.addWidget("button", "🧹 ล้างรายการ (ว่าง = หน้าใหญ่สุด 1 คน)", null, () => {
                const w = facesWidget(this);
                if (w) { w.value = ""; w.callback?.(""); this.setDirtyCanvas(true, true); }
            }, { serialize: false });
            for (const b of this.widgets.slice(-4)) b.serialize = false;
            return r;
        };
        nodeType.prototype.onDragOver = function (e) {
            return !!e?.dataTransfer?.types?.includes?.("Files");
        };
        nodeType.prototype.onDragDrop = function (e) {
            const files = [...(e?.dataTransfer?.files || [])].filter((f) => IMAGE_RE.test(f.name));
            if (!files.length) return false;
            uploadFaces(this, files);
            return true;
        };
    },
});

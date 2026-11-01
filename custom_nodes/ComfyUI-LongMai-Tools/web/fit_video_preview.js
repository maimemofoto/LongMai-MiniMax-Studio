// LongMai: keep video previews a sensible size.
// The built-in video preview forces the node to be as tall as the clip at full node width, so a finished clip makes
// Save Video nodes grow by ~480 px (16:9) or ~1500 px (9:16). A grown node can slide out of its group, and group
// switches (they use the node's centre) then stop muting it. This caps the preview height and shrinks the node back.
import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

const MAX_PREVIEW_H = 480;   // canvas units; a 16:9 clip at 864 px width is ~486 px tall
const PATCHED = Symbol("longmaiFitPreview");

function fitNode(node) {
    if (!node?.computeSize || !node.setSize) return;
    const h = node.computeSize()[1];
    if (node.size[1] > h + 1) {
        node.setSize([node.size[0], h]);
        node.setDirtyCanvas?.(true, true);
    }
}

function patchWidget(node, widget) {
    if (typeof widget.computeLayoutSize !== "function") return false;
    const orig = widget.computeLayoutSize.bind(widget);
    widget.computeLayoutSize = (...args) => {
        const r = orig(...args) || {};
        if (typeof r.minHeight === "number" && r.minHeight > MAX_PREVIEW_H) {
            const k = MAX_PREVIEW_H / r.minHeight;
            return { ...r, minHeight: MAX_PREVIEW_H,
                     minWidth: typeof r.minWidth === "number" ? Math.max(200, r.minWidth * k) : r.minWidth };
        }
        return r;
    };
    widget[PATCHED] = true;
    const v = widget.element?.querySelector?.("video");
    v?.addEventListener?.("loadedmetadata", () => setTimeout(() => fitNode(node), 50));
    return true;
}

function scan() {
    const graphs = new Set([app.graph, app.canvas?.graph].filter(Boolean));
    for (const g of graphs) {
        for (const node of g._nodes || []) {
            for (const w of node.widgets || []) {
                if (w.name !== "video-preview") continue;
                if (!w[PATCHED] && !patchWidget(node, w)) continue;
                // shrink once per new clip (so a node the user enlarges on purpose stays as they left it)
                const v = w.element?.querySelector?.("video");
                if (v?.videoWidth && w.__longmaiSrc !== v.currentSrc) {
                    w.__longmaiSrc = v.currentSrc;
                    fitNode(node);
                }
            }
        }
    }
}

app.registerExtension({
    name: "LongMai.FitVideoPreview",
    setup() {
        setInterval(() => { try { scan(); } catch (e) { /* never break the UI */ } }, 1000);
        api.addEventListener("executed", () => setTimeout(() => { try { scan(); } catch (e) {} }, 300));
    },
});

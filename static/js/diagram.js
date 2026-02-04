/**
 * Diagram Logic for Visual Editor
 * Handles Draggable Nodes and SVG Relationship Lines
 */

let isDragging = false;
let currentDragNode = null;
let offset = { x: 0, y: 0 };
let scale = 1;

// SVG Layer
let svgLayer = null;

function initDiagram() {
    svgLayer = document.getElementById("connections-layer");
    if (!svgLayer) {
        console.error("SVG Layer not found");
        return;
    }

    // Initialize draggables
    document.querySelectorAll(".model-node").forEach(node => {
        makeDraggable(node);
    });

    // Initial Draw
    drawConnections();
}

function makeDraggable(element) {
    const header = element.querySelector(".model-header");

    header.addEventListener("mousedown", (e) => {
        isDragging = true;
        currentDragNode = element;

        // Calculate offset
        const rect = element.getBoundingClientRect();
        const canvasRect = document.getElementById("canvas").getBoundingClientRect();

        // Relative to canvas
        const elementX = rect.left - canvasRect.left;
        const elementY = rect.top - canvasRect.top;

        offset.x = e.clientX - rect.left;
        offset.y = e.clientY - rect.top;

        // Bring to front
        element.style.zIndex = 100;
    });
}

document.addEventListener("mousemove", (e) => {
    if (!isDragging || !currentDragNode) return;
    e.preventDefault();

    const canvas = document.getElementById("canvas");
    const canvasRect = canvas.getBoundingClientRect();

    let x = e.clientX - canvasRect.left - offset.x;
    let y = e.clientY - canvasRect.top - offset.y;

    // Boundaries
    // x = Math.max(0, x);
    // y = Math.max(0, y);

    // Update position
    currentDragNode.style.position = "absolute";
    currentDragNode.style.left = `${x}px`;
    currentDragNode.style.top = `${y}px`;
    currentDragNode.style.margin = "0"; // Override grid margin

    // Save position to schema in memory (if needed immediatley)
    const modelName = currentDragNode.id.replace("model-card-", "");
    if (currentProject.schema_data.models[modelName]) {
        currentProject.schema_data.models[modelName].ui = { x, y };
    }

    // Redraw lines
    drawConnections();
});

document.addEventListener("mouseup", async () => {
    if (isDragging) {
        isDragging = false;
        if (currentDragNode) {
            currentDragNode.style.zIndex = "";
            // Trigger save
            await saveProject();
            currentDragNode = null;
        }
    }
});

function drawConnections() {
    if (!svgLayer || !currentProject) return;

    // Clear existing
    svgLayer.innerHTML = "";

    const models = currentProject.schema_data.models;
    const modelNames = Object.keys(models);

    modelNames.forEach(sourceName => {
        const sourceModel = models[sourceName];
        if (!sourceModel.relations) return;

        Object.keys(sourceModel.relations).forEach(relName => {
            const rel = sourceModel.relations[relName];
            const targetName = rel.model;

            if (!models[targetName]) {
                console.warn(`Target model ${targetName} not found for relation from ${sourceName}`);
                return;
            }

            console.log(`Drawing line from ${sourceName} to ${targetName}`);
            drawCurve(sourceName, targetName, rel.type);
        });
    });
}

function drawCurve(sourceId, targetId, type) {
    const sourceEl = document.getElementById(`model-card-${sourceId}`);
    const targetEl = document.getElementById(`model-card-${targetId}`);

    if (!sourceEl || !targetEl) return;

    // Calculate centers relative to canvas container (offsetParent)
    // This is robust against scrolling and padding if parent is positioned
    const x1 = sourceEl.offsetLeft + sourceEl.offsetWidth / 2;
    const y1 = sourceEl.offsetTop + sourceEl.offsetHeight / 2;

    const x2 = targetEl.offsetLeft + targetEl.offsetWidth / 2;
    const y2 = targetEl.offsetTop + targetEl.offsetHeight / 2;

    // Create Path
    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");

    // Bezier Curve Logic
    // Control points: halfway distinct
    const dx = Math.abs(x2 - x1) * 0.5;
    const controlX1 = x1 + dx; // Exit right? Or purely mostly horizontal flow? 
    // Let's assume right-to-left or left-to-right flow mostly, or just simple curvature

    // Better curve: 
    // M x1 y1 C (x1) (y2) (x2) (y2) x2 y2 ? No
    // M x1 y1 C (x1+dx) y1, (x2-dx) y2, x2 y2

    // Improve source/target points to be on the edges instead of center?
    // For MVP center is fine, Z-index keeps it behind.

    const d = `M ${x1} ${y1} C ${x1 + 100} ${y1}, ${x2 - 100} ${y2}, ${x2} ${y2}`;

    // Vibrant line color
    path.setAttribute("d", d);
    path.setAttribute("stroke", "#6366f1"); // Primary color
    path.setAttribute("stroke-width", "4");
    path.setAttribute("fill", "none");
    path.setAttribute("stroke-opacity", "0.6");

    // Dashed if many-to-many?
    if (type === "many_to_many") {
        path.setAttribute("stroke-dasharray", "8,8");
    }

    svgLayer.appendChild(path);
}

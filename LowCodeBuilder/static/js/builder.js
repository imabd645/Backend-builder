const API_BASE = "/api";
const params = new URLSearchParams(window.location.search);
const PROJECT_ID = params.get("id");

if (!PROJECT_ID) {
    alert("No project ID specified");
    window.location.href = "index.html";
}

let currentProject = null;
let currentEditingModel = null; // Name of model being edited (for adding fields)

document.addEventListener("DOMContentLoaded", () => {
    loadProject();
    setupEventListeners();
});

async function loadProject() {
    try {
        const res = await fetch(`${API_BASE}/projects/${PROJECT_ID}`);
        if (!res.ok) throw new Error("Failed to load");
        currentProject = await res.json();
        renderUI();
    } catch (e) {
        console.error(e);
        alert("Project not found");
        window.location.href = "index.html";
    }
}

async function saveProject() {
    // Send full update
    await fetch(`${API_BASE}/projects/${PROJECT_ID}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            schema_data: currentProject.schema_data
        })
    });
}

function renderUI() {
    document.getElementById("project-name").innerText = currentProject.name;

    const models = currentProject.schema_data.models;
    const canvas = document.getElementById("canvas");
    const sidebarList = document.getElementById("model-list-sidebar");

    canvas.innerHTML = "";
    sidebarList.innerHTML = "";

    const modelNames = Object.keys(models);

    if (modelNames.length === 0) {
        canvas.innerHTML = "<div class='empty-state'>No models yet. Click '+ Add Model'</div>";
    }

    modelNames.forEach(name => {
        // Sidebar Item
        const li = document.createElement("li");
        li.innerText = name;
        li.onclick = () => document.getElementById(`model-card-${name}`).scrollIntoView({ behavior: "smooth" });
        sidebarList.appendChild(li);

        // Canvas Card
        const card = createModelCard(name, models[name]);
        canvas.appendChild(card);
    });
}

function createModelCard(name, modelDef) {
    const card = document.createElement("div");
    card.className = "model-node";
    card.id = `model-card-${name}`;
    card.style.position = "relative";
    card.style.margin = "20px";
    card.style.display = "inline-block";
    card.style.verticalAlign = "top";

    // API Config
    const apis = currentProject.schema_data.apis?.[name] || { create: "public", read: "public", update: "auth", delete: "admin" };

    const makeSelect = (action, val) => `
        <select onchange="updateApi('${name}', '${action}', this.value)" class="api-select">
            <option value="off" ${val === 'off' ? 'selected' : ''}>Off</option>
            <option value="public" ${val === 'public' ? 'selected' : ''}>Public</option>
            <option value="auth" ${val === 'auth' ? 'selected' : ''}>Auth</option>
            <option value="admin" ${val === 'admin' ? 'selected' : ''}>Admin</option>
        </select>
    `;

    let fieldsHtml = "";
    Object.keys(modelDef.fields).forEach(fname => {
        const f = modelDef.fields[fname];
        fieldsHtml += `
            <div class="field-row">
                <span>
                    <span class="field-name">${fname}</span>
                    <span class="field-type">${f.type}</span>
                    ${f.required ? "<span class='badge-req'>*</span>" : ""}
                </span>
                <button class="btn-icon" onclick="deleteField('${name}', '${fname}')">×</button>
            </div>
        `;
    });

    card.innerHTML = `
        <div class="model-header">
            <span>${name}</span>
            <button class="btn-icon text-danger" onclick="deleteModel('${name}')">🗑</button>
        </div>
        <div class="model-fields">
            ${fieldsHtml}
            <button class="btn-sm btn-secondary w-full mt-2" onclick="openFieldModal('${name}')">+ Add Field</button>
        </div>
        <div class="model-footer">
            <div class="api-row"><small>Create</small> ${makeSelect('create', apis.create)}</div>
            <div class="api-row"><small>Read</small> ${makeSelect('read', apis.read)}</div>
            <div class="api-row"><small>Update</small> ${makeSelect('update', apis.update)}</div>
            <div class="api-row"><small>Delete</small> ${makeSelect('delete', apis.delete)}</div>
        </div>
    `;
    return card;
}

// --- Actions ---

function setupEventListeners() {
    document.getElementById("back-btn").onclick = () => window.location.href = "index.html";

    // Add Model
    document.getElementById("add-model-btn").onclick = () => {
        document.getElementById("model-modal").classList.remove("hidden");
    };

    document.getElementById("save-model-btn").onclick = async () => {
        const input = document.getElementById("model-name-input");
        const name = input.value.trim();
        const cleanName = name.charAt(0).toUpperCase() + name.slice(1);

        if (!cleanName || currentProject.schema_data.models[cleanName]) {
            return alert("Invalid or duplicate model name");
        }

        // Add to state
        currentProject.schema_data.models[cleanName] = {
            fields: {},
            relations: {}
        };

        // Initialize default API config
        currentProject.schema_data.apis = currentProject.schema_data.apis || {};
        currentProject.schema_data.apis[cleanName] = {
            create: "public", read: "public", update: "auth", delete: "admin"
        };

        await saveProject();
        input.value = "";
        document.getElementById("model-modal").classList.add("hidden");
        renderUI();
    };

    // Add Field Setup
    document.getElementById("save-field-btn").onclick = async () => {
        const name = document.getElementById("field-name-input").value.trim().toLowerCase();
        const type = document.getElementById("field-type-input").value;
        const required = document.getElementById("field-required-input").checked;

        if (!name) return alert("Field name required");
        if (name === "id") return alert("ID is automatic");

        if (currentProject.schema_data.models[currentEditingModel].fields[name]) {
            return alert("Field exists");
        }

        currentProject.schema_data.models[currentEditingModel].fields[name] = {
            type, required
        };

        await saveProject();
        document.getElementById("field-name-input").value = "";
        document.getElementById("field-modal").classList.add("hidden");
        renderUI();
    };

    // Close Modals
    document.querySelectorAll(".close-modal").forEach(b => {
        b.onclick = (e) => e.target.closest(".modal").classList.add("hidden");
    });

    // Download
    document.getElementById("generate-btn").onclick = () => {
        window.open(`${API_BASE}/projects/${PROJECT_ID}/generate`, '_blank');
    };
}

// Global actions for onclick injection
window.deleteModel = async (name) => {
    if (!confirm(`Delete model ${name}?`)) return;
    delete currentProject.schema_data.models[name];
    if (currentProject.schema_data.apis) delete currentProject.schema_data.apis[name]; // Clean up APIs
    await saveProject();
    renderUI();
};

window.updateApi = async (modelName, action, value) => {
    if (!currentProject.schema_data.apis) currentProject.schema_data.apis = {};
    if (!currentProject.schema_data.apis[modelName]) currentProject.schema_data.apis[modelName] = {};

    currentProject.schema_data.apis[modelName][action] = value;
    await saveProject();
};

window.openFieldModal = (modelName) => {
    currentEditingModel = modelName;
    document.getElementById("field-modal").classList.remove("hidden");
};

window.deleteField = async (modelName, fieldName) => {
    delete currentProject.schema_data.models[modelName].fields[fieldName];
    await saveProject();
    renderUI();
};

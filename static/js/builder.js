const API_BASE = "/api";
const params = new URLSearchParams(window.location.search);
const PROJECT_ID = params.get("id");

if (!localStorage.getItem('builder_token')) {
    window.location.href = "login.html";
}

if (!PROJECT_ID) {
    alert("No project ID specified");
    window.location.href = "dashboard.html";
}

function getHeaders() {
    const token = localStorage.getItem('builder_token');
    return {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
    };
}

let currentProject = null;
let currentEditingModel = null; // Name of model being edited (for adding fields)

document.addEventListener("DOMContentLoaded", () => {
    loadProject();
    setupEventListeners();
});

async function loadProject() {
    try {
        const res = await fetch(`${API_BASE}/projects/${PROJECT_ID}`, {
            headers: getHeaders()
        });
        if (res.status === 401) {
            window.location.href = "login.html";
            return;
        }
        if (!res.ok) throw new Error("Failed to load");
        currentProject = await res.json();
        renderUI();
    } catch (e) {
        console.error(e);
        alert("Project not found or access denied");
        window.location.href = "dashboard.html";
    }
}

async function saveProject() {
    // Send full update
    await fetch(`${API_BASE}/projects/${PROJECT_ID}`, {
        method: "PUT",
        headers: getHeaders(),
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

    if (typeof initDiagram === 'function') {
        setTimeout(initDiagram, 100);
    }
}

function createModelCard(name, modelDef) {
    const card = document.createElement("div");
    card.className = "model-node";
    card.id = `model-card-${name}`;
    // Layout from schema or default
    let ui = currentProject.schema_data.models[name].ui;

    // Auto-layout if missing OR overlapping
    // Simple collision check against others?
    // Let's just force a grid layout if x,y are dangerously close to default 50,50 for multiple items
    const isDefault = ui && ui.x === 50 && ui.y === 50;

    if (!ui || isDefault) {
        const index = Object.keys(currentProject.schema_data.models).indexOf(name);
        const col = index % 3;
        const row = Math.floor(index / 3);

        ui = { x: 50 + (col * 350), y: 50 + (row * 350) };

        // Update schema so it saves
        currentProject.schema_data.models[name].ui = ui;
    }

    card.style.position = "absolute";
    card.style.left = `${ui.x}px`;
    card.style.top = `${ui.y}px`;
    card.style.margin = "0"; // No margin for absolute positioning

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
            <div style="display: flex; gap: 0.5rem;">
                <button class="btn-icon" title="Connect to..." onclick="startConnection('${name}')">🔗</button>
                <button class="btn-icon text-danger" title="Delete Model" onclick="deleteModel('${name}')">🗑</button>
            </div>
        </div>
        <div class="model-fields">
            ${fieldsHtml}
            <button class="btn-sm btn-secondary w-full mt-2" onclick="openFieldModal('${name}')">+ Add Field</button>
            <div id="rels-${name}" style="margin-top: 0.5rem; font-size: 0.8rem; color: var(--primary);">
                <!-- Relations shown here? Or just lines? -->
            </div>
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

// Connection State
let connectionSource = null;

window.startConnection = (name) => {
    // If clicking same source again, cancel
    if (connectionSource === name) {
        resetConnectionState();
        return;
    }

    // If no source yet, start connection
    if (!connectionSource) {
        connectionSource = name;
        document.getElementById(`model-card-${name}`).classList.add("ring-offset");
        // Show instruction (using a simple toast or reusing empty state div momentarily?)
        // Ideally a toast, but alert is too blocking. 
        // Let's just change cursor or button styles.
        const btn = document.querySelector(`#model-card-${name} .btn-icon`);
        if (btn) btn.innerText = "❌"; // cancel mode
        return;
    }

    // Target selected (connectionSource is already set to something else)
    openRelationModal(connectionSource, name);
    resetConnectionState();
};

function resetConnectionState() {
    if (connectionSource) {
        const card = document.getElementById(`model-card-${connectionSource}`);
        if (card) card.classList.remove("ring-offset");
        // Reset button text if needed, but renderUI usually resets it
        const btn = document.querySelector(`#model-card-${connectionSource} .btn-icon`);
        if (btn) btn.innerText = "🔗";
    }
    connectionSource = null;
}

let pendingRelation = null;

function openRelationModal(source, target) {
    if (source === target) return alert("Cannot connect to self (yet)");

    pendingRelation = { source, target };
    document.getElementById("relation-desc").innerText = `${source} ➝ ${target}`;
    document.getElementById("relation-modal").classList.remove("hidden");
}

document.addEventListener("DOMContentLoaded", () => {
    // ... within existing listener or append ...

    document.getElementById("save-relation-btn").onclick = async () => {
        if (!pendingRelation) return;

        const type = document.getElementById("relation-type-input").value;
        const { source, target } = pendingRelation;

        // Add relation to schema
        // stored in source model
        const sourceModel = currentProject.schema_data.models[source];
        sourceModel.relations = sourceModel.relations || {};

        // Key: relation name (e.g. "posts" or "author")
        // Simple naming strategy
        const relName = type === 'one_to_many' ? target.toLowerCase() + 's' : target.toLowerCase();

        sourceModel.relations[relName] = {
            model: target,
            type: type
        };

        // Also add foreign key field automatically if needed?
        // For One-to-Many (User has many Posts), Post needs user_id.
        // If connecting User -> Post (One to Many):
        // Source: User, Target: Post.
        // User.posts = relationship("Post")
        // Post.user_id = ForeignKey("user.id")

        // Let's rely on the Generator to handle the FK creation based on the relationship definition?
        // Or explicitely add it here.
        // Explicit is better for visibility.

        if (type === 'one_to_many') {
            const targetModel = currentProject.schema_data.models[target];
            const fkName = source.toLowerCase() + "_id";
            if (!targetModel.fields[fkName]) {
                targetModel.fields[fkName] = { type: 'int', required: true };
            }
        }

        await saveProject();
        document.getElementById("relation-modal").classList.add("hidden");
        renderUI(); // Will redraw lines
    };
});

// --- Actions ---

function setupEventListeners() {
    document.getElementById("back-btn").onclick = () => window.location.href = "dashboard.html";

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
        // Improved placement to avoid absolute zero overlap
        const existingCount = Object.keys(currentProject.schema_data.models).length;
        const offsetX = 50 + (existingCount * 40);
        const offsetY = 50 + (existingCount * 30);

        currentProject.schema_data.models[cleanName] = {
            fields: {},
            relations: {},
            ui: { x: offsetX, y: offsetY }
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

    // Download using Fetch for Auth
    document.getElementById("generate-btn").onclick = async () => {
        try {
            const res = await fetch(`${API_BASE}/projects/${PROJECT_ID}/generate`, {
                headers: getHeaders()
            });
            if (res.status === 401) return window.location.href = "login.html";

            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `project_${PROJECT_ID}.zip`;
            document.body.appendChild(a);
            a.click();
            a.remove();
        } catch (e) {
            console.error(e);
            alert("Download failed");
        }
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

const API_BASE = "/api";

function getHeaders() {
    const token = localStorage.getItem('builder_token');
    return {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
    };
}

document.addEventListener("DOMContentLoaded", () => {
    // Dashboard Init
    if (document.getElementById("project-list")) {
        fetchProjects();
        setupModal();
    }
});

async function fetchProjects() {
    const res = await fetch(`${API_BASE}/projects`, {
        headers: getHeaders()
    });

    if (res.status === 401) {
        window.location.href = 'login.html';
        return;
    }

    const projects = await res.json();
    renderProjects(projects);
}

function renderProjects(projects) {
    const list = document.getElementById("project-list");
    list.innerHTML = "";

    if (projects.length === 0) {
        list.innerHTML = "<p class='empty-state'>No projects yet. Create one to get started!</p>";
        return;
    }

    projects.forEach(p => {
        const card = document.createElement("div");
        card.className = "project-card";
        card.onclick = () => window.location.href = `builder.html?id=${p.id}`;

        card.innerHTML = `
            <h3>${p.name}</h3>
            <p>Created: ${new Date(p.created_at).toLocaleDateString()}</p>
            <div class="card-actions">
                <button class="btn btn-sm btn-danger stop-prop" onclick="deleteProject(event, '${p.id}')">Delete</button>
            </div>
        `;
        list.appendChild(card);
    });
}

function setupModal() {
    const modal = document.getElementById("create-modal");
    const btn = document.getElementById("create-project-btn");
    const cancel = document.getElementById("cancel-create");
    const confirm = document.getElementById("confirm-create");

    if (btn) btn.onclick = () => modal.classList.remove("hidden");
    if (cancel) cancel.onclick = () => modal.classList.add("hidden");

    if (confirm) confirm.onclick = async () => {
        const nameInput = document.getElementById("new-project-name");
        const name = nameInput.value.trim();
        if (!name) return alert("Please enter a name");

        await createProject(name);
        nameInput.value = "";
        modal.classList.add("hidden");
        fetchProjects();
    };
}

async function createProject(name) {
    const res = await fetch(`${API_BASE}/projects`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify({ name })
    });
    return await res.json();
}

async function deleteProject(e, id) {
    e.stopPropagation(); // Prevent card click
    if (!confirm("Are you sure you want to delete this project?")) return;

    await fetch(`${API_BASE}/projects/${id}`, {
        method: "DELETE",
        headers: getHeaders()
    });
    fetchProjects();
}

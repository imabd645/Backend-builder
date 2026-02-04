# Low-Code Backend Builder 🚀

![Status](https://img.shields.io/badge/status-active-success.svg)
![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.95+-009688.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

**Low-Code Backend Builder** is a robust, visual development platform designed to accelerate backend creation. It allows developers to design complex database schemas, define relationships visually, and instantly generate **production-grade FastAPI applications** without writing boilerplate code.

> **Stop writing boilerplate.** Focus on your business logic while the Builder handles the architecture, security, and deployment configuration.

---

## 🌟 Why Use This?

Building a modern backend involves setting up the same foundational elements every time: authentication, database connections, Pydantic schemas, CRUD routers, and Docker configs. **Low-Code Builder** automates this entire process.

- **⏱️ Save Time**: Go from Zero to Deployed API in minutes.
- **🔒 Secure by Default**: Generated apps come with industry-standard JWT authentication and password hashing (Argon2/PBKDF2).
- **🏗️ Best Practices**: The generated code follows strict FastAPI patterns, dependency injection, and Pydantic v2 validation.
- **🐳 DevOps Ready**: Every project includes a unified `docker-compose` setup for instant deployment.

---

## ✨ Key Features

### 1. 🎨 Canvas-Based Visual Editor
- **Infinite Canvas**: Drag and drop model cards freely.
- **Visual Relationships**: Connect models (e.g., `User` ➝ `Post`) using an intuitive link tool.
- **Smart Layouts**: Automatic grid snapping and collision detection for a clean workspace.

### 2. 🔌 Advanced Relationship Management
The builder understands complex data structures:
- **One-to-Many**: (e.g., An Author has many Books). Automatically adds Foreign Keys.
- **Many-to-One**: (e.g., A Comment belongs to a Post).
- **Auto-Foreign Keys**: You don't need to manually define `user_id` columns; the builder does it for you when you link models.

### 3. 🔐 Granular Security Control
Define access levels per model and per operation (Create, Read, Update, Delete):
- **Public**: Open to everyone.
- **Auth**: Requires a valid JWT token.
- **Admin**: Restricted to Super Users only.

### 4. 🛠️ What You Get (The Generated Code)
When you click **Download**, you receive a zip file containing a standalone project with:
- **FastAPI**: The modern, high-performance web framework.
- **SQLAlchemy (Async)**: Asynchronous database ORM.
- **SQLAdmin**: A built-in, operational Admin Dashboard for your data.
- **Alembic Ready**: Structured for database migrations.
- **Authentication System**: `login`, `register`, and `me` endpoints pre-wired.

---

## 🛠️ Architecture Overview

The platform consists of two main parts:

1.  **The Builder (Local Tool)**:
    - Runs locally on your machine.
    - Stores project schemas in `SQLite`.
    - Generates dynamic Python code using Jinja2-style templating logic.
    - Frontend: **Vanilla JS** + **Glassmorphism CSS** (No heavy node_modules needed to run the builder UI).

2.  **The Generated App (Your Product)**:
    - A clean, separated folder structure (`app/models`, `app/routers`, `app/schemas`).
    - **No dependency on the Builder**: Once downloaded, the code is yours. You can edit it, push it to GitHub, and deploy it anywhere.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- [Optional] Docker (for running generated projects)

### Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/yourusername/LowCodeBuilder.git
    cd LowCodeBuilder
    ```

2.  **Create a Virtual Environment**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the Builder**
    ```bash
    python -m uvicorn app.main:app --reload
    ```

5.  **Access the UI**
    Open your browser and navigate to:
    `http://127.0.0.1:8000/static/index.html`

---

## 📖 Usage Guide

1.  **Create a Project**: Click "New Project" on the dashboard.
2.  **Design Schema**:
    - **Add Models**: Click "+ Add Model" to create tables (e.g., `User`, `Post`).
    - **Add Fields**: Define columns like `title` (String), `is_published` (Boolean).
    - **Connect**: Click the 🔗 icon on a Source card, then click a Target card to link them.
3.  **Configure API**: Toggle `Public`, `Auth` (User only), or `Admin` access for each CRUD operation.
4.  **Download**: Click **Download Code** to get a `.zip` of your backend.
5.  **Run Your Backend**:
    ```bash
    # Inside the downloaded folder
    pip install -r requirements.txt
    python run.py
    ```
    Or use Docker:
    ```bash
    docker-compose up -d --build
    ```
6.  **Admin Panel**:
    Access `/admin` on your generated app (e.g., `http://localhost:5000/admin`) to manage your data immediately.

---

## 📂 Project Structure

```
LowCodeBuilder/
├── app/
│   ├── main.py            # Builder API Entrypoint
│   ├── generator/         # Code Generation Engine
│   │   ├── main_gen.py
│   │   ├── models_gen.py  # SQLAlchemy Code Gen
│   │   ├── ...
│   └── routers/           # Project Management API
├── static/                # Frontend UI
│   ├── js/                # Logic (builder.js, diagram.js)
│   ├── css/               # Styling (style.css)
│   └── ...
└── projects/              # Local storage for user projects
```

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

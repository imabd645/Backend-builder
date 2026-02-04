from fastapi import FastAPI, HTTPException, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from . import storage, schemas
from .generator.main_gen import generate_project_zip

app = FastAPI(title="Low-Code Backend Builder")

# Mount static files for the frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
def startup_event():
    storage.init_storage()

@app.get("/")
def read_root():
    return RedirectResponse(url="/static/index.html")

# --- Project APIs ---

@app.post("/api/projects", response_model=schemas.ProjectResponse)
def create_project_api(project: schemas.ProjectCreate):
    return storage.create_project(project)

@app.get("/api/projects", response_model=list[schemas.ProjectResponse])
def list_projects_api():
    return storage.list_projects()

@app.get("/api/projects/{project_id}", response_model=schemas.ProjectResponse)
def get_project_api(project_id: str):
    project = storage.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@app.put("/api/projects/{project_id}", response_model=schemas.ProjectResponse)
def update_project_api(project_id: str, project: schemas.ProjectUpdate):
    updated = storage.update_project(project_id, project)
    if not updated:
        raise HTTPException(status_code=404, detail="Project not found")
    return updated

@app.delete("/api/projects/{project_id}")
def delete_project_api(project_id: str):
    success = storage.delete_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"status": "success"}

@app.get("/api/projects/{project_id}/generate")
def generate_project_api(project_id: str):
    project = storage.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Convert response model back to schema model if needed, or just use the data
    # project.schema_data is already a ProjectSchema object or dict? 
    # In Pydantic v1 it might be a model, let's ensure we pass the object.
    
    zip_bytes = generate_project_zip(project.schema_data)
    
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=project_{project_id}.zip"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

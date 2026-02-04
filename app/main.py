from fastapi import FastAPI, HTTPException, Response, Depends, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from typing import List
from . import storage, schemas, builder_auth
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

# --- Auth APIs ---

@app.post("/api/auth/register", response_model=schemas.BuilderUserResponse)
def register(user: schemas.BuilderUserCreate):
    try:
        hashed_password = builder_auth.get_password_hash(user.password)
        return storage.create_user(user, hashed_password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/auth/token", response_model=builder_auth.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = storage.get_user_by_email(form_data.username)
    if not user or not builder_auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = builder_auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/auth/me", response_model=schemas.BuilderUserResponse)
def read_users_me(current_user: schemas.BuilderUser = Depends(builder_auth.get_current_user)):
    return current_user

# --- Project APIs (Protected) ---

@app.post("/api/projects", response_model=schemas.ProjectResponse)
def create_project_api(project: schemas.ProjectCreate, current_user: schemas.BuilderUser = Depends(builder_auth.get_current_user)):
    return storage.create_project(project, current_user.id)

@app.get("/api/projects", response_model=List[schemas.ProjectResponse])
def list_projects_api(current_user: schemas.BuilderUser = Depends(builder_auth.get_current_user)):
    return storage.list_projects(current_user.id)

@app.get("/api/projects/{project_id}", response_model=schemas.ProjectResponse)
def get_project_api(project_id: str, current_user: schemas.BuilderUser = Depends(builder_auth.get_current_user)):
    project = storage.get_project(project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@app.put("/api/projects/{project_id}", response_model=schemas.ProjectResponse)
def update_project_api(project_id: str, project: schemas.ProjectUpdate, current_user: schemas.BuilderUser = Depends(builder_auth.get_current_user)):
    existing = storage.get_project(project_id)
    if not existing or existing.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")
        
    updated = storage.update_project(project_id, project)
    return updated

@app.delete("/api/projects/{project_id}")
def delete_project_api(project_id: str, current_user: schemas.BuilderUser = Depends(builder_auth.get_current_user)):
    existing = storage.get_project(project_id)
    if not existing or existing.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")
        
    storage.delete_project(project_id)
    return {"status": "success"}

@app.get("/api/projects/{project_id}/generate")
def generate_project_api(project_id: str, current_user: schemas.BuilderUser = Depends(builder_auth.get_current_user)):
    project = storage.get_project(project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")
    
    zip_bytes = generate_project_zip(project.schema_data)
    
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=project_{project_id}.zip"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

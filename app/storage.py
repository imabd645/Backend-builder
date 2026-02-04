import json
import os
import uuid
from datetime import datetime
from typing import List, Optional
from .schemas import ProjectCreate, ProjectResponse, ProjectSchema, ProjectUpdate, BuilderUser, BuilderUserCreate

STORAGE_DIR = "storage"
USERS_FILE = os.path.join(STORAGE_DIR, "users.json")

def _load_users() -> List[BuilderUser]:
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r") as f:
        data = json.load(f)
        return [BuilderUser(**u) for u in data]

def _save_users(users: List[BuilderUser]):
    with open(USERS_FILE, "w") as f:
        json.dump([u.dict() for u in users], f, indent=2)

def create_user(user: BuilderUserCreate, hashed_password: str) -> BuilderUser:
    users = _load_users()
    if any(u.email == user.email for u in users):
        raise ValueError("Email already registered")
        
    new_user = BuilderUser(
        id=str(uuid.uuid4()),
        email=user.email,
        hashed_password=hashed_password
    )
    users.append(new_user)
    _save_users(users)
    return new_user

def get_user_by_email(email: str) -> Optional[BuilderUser]:
    users = _load_users()
    for u in users:
        if u.email == email:
            return u
    return None

def _get_project_path(project_id: str) -> str:
    return os.path.join(STORAGE_DIR, f"{project_id}.json")

def init_storage():
    if not os.path.exists(STORAGE_DIR):
        os.makedirs(STORAGE_DIR)

def create_project(project_in: ProjectCreate, owner_id: str) -> ProjectResponse:
    project_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    # Default empty schema
    empty_schema = ProjectSchema(models={})
    
    project_data = {
        "id": project_id,
        "name": project_in.name,
        "created_at": now,
        "updated_at": now, # Added updated_at
        "schema_data": empty_schema.dict(),
        "owner_id": owner_id
    }
    
    with open(_get_project_path(project_id), "w") as f:
        json.dump(project_data, f, indent=2)
        
    return ProjectResponse(**project_data)

def list_projects(owner_id: str) -> List[ProjectResponse]:
    projects = []
    if not os.path.exists(STORAGE_DIR):
        return []
        
    for filename in os.listdir(STORAGE_DIR):
        if filename.endswith(".json") and filename != "users.json":
            filepath = os.path.join(STORAGE_DIR, filename)
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                    # Filter: Only show if owner matches
                    if data.get("owner_id") == owner_id:
                        projects.append(ProjectResponse(**data))
            except json.JSONDecodeError:
                continue # Skip corrupt files
                
    # Sort by created_at desc
    projects.sort(key=lambda x: x.created_at, reverse=True)
    return projects

def get_project(project_id: str) -> Optional[ProjectResponse]:
    path = _get_project_path(project_id)
    if not os.path.exists(path):
        return None
        
    with open(path, "r") as f:
        data = json.load(f)
        return ProjectResponse(**data)

def update_project(project_id: str, update_data: ProjectUpdate) -> Optional[ProjectResponse]:
    current = get_project(project_id)
    if not current:
        return None
    
    # Update fields
    data_dict = current.dict()
    
    if update_data.name:
        data_dict["name"] = update_data.name
    
    if update_data.schema_data:
        data_dict["schema_data"] = update_data.schema_data.dict()
        
    # Write back
    with open(_get_project_path(project_id), "w") as f:
        json.dump(data_dict, f, indent=2)
        
    return ProjectResponse(**data_dict)

def delete_project(project_id: str) -> bool:
    path = _get_project_path(project_id)
    if os.path.exists(path):
        os.remove(path)
        return True
    return False

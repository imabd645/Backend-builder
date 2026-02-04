import json
import os
import uuid
from datetime import datetime
from typing import List, Optional
from .schemas import ProjectCreate, ProjectResponse, ProjectSchema, ProjectUpdate

STORAGE_DIR = "storage"

def _get_project_path(project_id: str) -> str:
    return os.path.join(STORAGE_DIR, f"{project_id}.json")

def init_storage():
    if not os.path.exists(STORAGE_DIR):
        os.makedirs(STORAGE_DIR)

def create_project(project_in: ProjectCreate) -> ProjectResponse:
    project_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    # Default empty schema
    empty_schema = ProjectSchema(models={})
    
    project_data = {
        "id": project_id,
        "name": project_in.name,
        "created_at": now,
        "schema_data": empty_schema.dict()
    }
    
    with open(_get_project_path(project_id), "w") as f:
        json.dump(project_data, f, indent=2)
        
    return ProjectResponse(**project_data)

def list_projects() -> List[ProjectResponse]:
    projects = []
    if not os.path.exists(STORAGE_DIR):
        return []
        
    for filename in os.listdir(STORAGE_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(STORAGE_DIR, filename)
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
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

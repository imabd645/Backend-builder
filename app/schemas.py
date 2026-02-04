from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime

# --- Builder User Schemas ---
class BuilderUserBase(BaseModel):
    email: str

class BuilderUserCreate(BuilderUserBase):
    password: str

class BuilderUser(BuilderUserBase):
    id: str
    hashed_password: str # Internal use

    class Config:
        from_attributes = True

class BuilderUserResponse(BuilderUserBase):
    id: str

# --- Internal JSON Schema Models ---

class FieldDefinition(BaseModel):
    type: str = Field(..., description="Data type: string, int, boolean, etc.")
    required: bool = Field(True, description="Is the field required?")

class ModelDefinition(BaseModel):
    fields: Dict[str, FieldDefinition]
    relations: Optional[Dict[str, str]] = None  # Generic relation definition for MVP

class ProjectSchema(BaseModel):
    models: Dict[str, ModelDefinition]
    apis: Dict[str, Dict[str, str]] = Field(default_factory=dict) # e.g. {"User": {"create": "public"}}

# --- API Request/Response Models ---

class ProjectCreate(BaseModel):
    name: str

class ProjectResponse(BaseModel):
    id: str
    owner_id: Optional[str] = None
    name: str
    created_at: str
    updated_at: Optional[str] = None
    schema_data: ProjectSchema

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    schema_data: Optional[ProjectSchema] = None

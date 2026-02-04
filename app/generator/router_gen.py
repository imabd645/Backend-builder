from typing import Dict, Any
from ..schemas import ModelDefinition

def generate_router_file(model_name: str, model_def: ModelDefinition, api_config: Dict[str, str]) -> str:
    # api_config: {"create": "auth", "read": "public", ...}
    
    lower_name = model_name.lower()
    
    lines = [
        "from fastapi import APIRouter, Depends, HTTPException",
        "from sqlalchemy.orm import Session",
        "from typing import List",
        f"from ..database import get_db, engine",
        f"from ..models import {model_name} as Model{model_name}",
        # f"from ..schemas import {model_name} as Schema{model_name}", 
        # Note: In schemas_gen we created {model_name}Create, {model_name}Response etc.
        # We need to assume the schema file structure or imports. 
        # Let's adjust imports to be specific
        f"from ..schemas import {model_name}Create, {model_name}Update, {model_name}Response",
        # Auth import placeholder
        "from ..auth import get_current_user" if "auth" in api_config.values() or "admin" in api_config.values() else "",
        "",
        f"router = APIRouter(prefix='/{lower_name}s', tags=['{model_name}'])",
        "",
        "# Dependency injection helper for Auth",
        "# (In a real app, strict permissions would be checked here)",
        ""
    ]
    
    # helper to get permissions
    def get_dep(action):
        perm = api_config.get(action, "public")
        if perm == "auth":
             return ", user: dict = Depends(get_current_user)"
        elif perm == "admin":
             return ", user: dict = Depends(get_current_user)" # Add admin check logic later
        return ""

    # CREATE
    if api_config.get("create") != "off":
        lines.append(f"@router.post('/', response_model={model_name}Response)")
        lines.append(f"def create_{lower_name}(item: {model_name}Create{get_dep('create')}, db: Session = Depends(get_db)):")
        lines.append(f"    db_item = Model{model_name}(**item.dict())")
        lines.append(f"    db.add(db_item)")
        lines.append(f"    db.commit()")
        lines.append(f"    db.refresh(db_item)")
        lines.append(f"    return db_item")
        lines.append("")

    # READ LIST
    if api_config.get("read") != "off":
        lines.append(f"@router.get('/', response_model=List[{model_name}Response])")
        lines.append(f"def read_{lower_name}s(skip: int = 0, limit: int = 100{get_dep('read')}, db: Session = Depends(get_db)):")
        lines.append(f"    return db.query(Model{model_name}).offset(skip).limit(limit).all()")
        lines.append("")

    # READ ONE
    if api_config.get("read") != "off":
        lines.append(f"@router.get('/{{item_id}}', response_model={model_name}Response)")
        lines.append(f"def read_{lower_name}(item_id: int{get_dep('read')}, db: Session = Depends(get_db)):")
        lines.append(f"    item = db.query(Model{model_name}).filter(Model{model_name}.id == item_id).first()")
        lines.append(f"    if item is None:")
        lines.append(f"        raise HTTPException(status_code=404, detail='{model_name} not found')")
        lines.append(f"    return item")
        lines.append("")

    # UPDATE
    if api_config.get("update") != "off":
        lines.append(f"@router.put('/{{item_id}}', response_model={model_name}Response)")
        lines.append(f"def update_{lower_name}(item_id: int, item_in: {model_name}Update{get_dep('update')}, db: Session = Depends(get_db)):")
        lines.append(f"    db_item = db.query(Model{model_name}).filter(Model{model_name}.id == item_id).first()")
        lines.append(f"    if db_item is None:")
        lines.append(f"        raise HTTPException(status_code=404, detail='{model_name} not found')")
        lines.append(f"    ")
        lines.append(f"    update_data = item_in.dict(exclude_unset=True)")
        lines.append(f"    for key, value in update_data.items():")
        lines.append(f"        setattr(db_item, key, value)")
        lines.append(f"    ")
        lines.append(f"    db.add(db_item)")
        lines.append(f"    db.commit()")
        lines.append(f"    db.refresh(db_item)")
        lines.append(f"    return db_item")
        lines.append("")

    # DELETE
    if api_config.get("delete") != "off":
        lines.append(f"@router.delete('/{{item_id}}')")
        lines.append(f"def delete_{lower_name}(item_id: int{get_dep('delete')}, db: Session = Depends(get_db)):")
        lines.append(f"    db_item = db.query(Model{model_name}).filter(Model{model_name}.id == item_id).first()")
        lines.append(f"    if db_item is None:")
        lines.append(f"        raise HTTPException(status_code=404, detail='{model_name} not found')")
        lines.append(f"    db.delete(db_item)")
        lines.append(f"    db.commit()")
        lines.append(f"    return {{'detail': '{model_name} deleted'}}")
        lines.append("")

    return "\n".join(lines)

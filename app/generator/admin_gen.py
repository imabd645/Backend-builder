from typing import Dict
from ..schemas import ModelDefinition

def generate_admin_file(models: Dict[str, ModelDefinition]) -> str:
    lines = [
        "from sqladmin import ModelView",
        "from . import models",
        ""
    ]
    
    # Generate ModelView for each model
    for model_name, model_def in models.items():
        lines.append(f"class {model_name}Admin(ModelView, model=models.{model_name}):")
        
        # Column List (Display all fields)
        fields = [f'"{f}"' for f in model_def.fields.keys()]
        if model_name == "User":
            fields = ['"id"', '"email"'] # Don't show password hash
        else:
            fields.insert(0, '"id"')
            
        lines.append(f"    column_list = [{', '.join(fields)}]")
        lines.append("")

    # Always generate UserAdmin
    has_user = "User" in models
    if not has_user:
        lines.append("class UserAdmin(ModelView, model=models.User):")
        lines.append("    column_list = ['id', 'email']")
        lines.append("")

    return "\n".join(lines)

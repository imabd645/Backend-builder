from typing import Dict
from ..schemas import ModelDefinition

TYPE_MAPPING = {
    "string": "str",
    "int": "int",
    "boolean": "bool",
    "float": "float",
    "datetime": "datetime",
    "text": "str"
}

def generate_schemas_file(models: Dict[str, ModelDefinition]) -> str:
    lines = [
        "from pydantic import BaseModel",
        "from typing import Optional, List",
        "from datetime import datetime",
        "",
        "class Token(BaseModel):",
        "    access_token: str",
        "    token_type: str",
        "",
        "class TokenData(BaseModel):",
        "    username: Optional[str] = None",
        ""
    ]
    
    # Ensure User schemas are generated even if not in models
    if "User" not in models:
        lines.extend([
            "class UserBase(BaseModel):",
            "    email: str",
            "",
            "class UserCreate(UserBase):",
            "    password: str",
            "",
            "class UserResponse(UserBase):",
            "    id: int",
            "    class Config:",
            "        from_attributes = True",
            "",""
        ])

    for model_name, model_def in models.items():
        # Base API Model (Shared properties)
        lines.append(f"class {model_name}Base(BaseModel):")
        
        if model_name == "User":
             lines.append("    email: str")

        has_fields = False
        for field_name, field_def in model_def.fields.items():
            if field_name == "id": continue
            if model_name == "User" and field_name in ["email", "password"]: continue

            has_fields = True
            py_type = TYPE_MAPPING.get(field_def.type.lower(), "str")
            if not field_def.required:
                lines.append(f"    {field_name}: Optional[{py_type}] = None")
            else:
                lines.append(f"    {field_name}: {py_type}")
        
        # Add relation helper fields (Foreign Keys)
        if model_def.relations:
            for rel_name, rel_def in model_def.relations.items():
                 # Only if one-to-many? For now let's just make sure we don't break
                 # But we need 'int' fields if they are keys?
                 # Actually, schemas usually just carry data.
                 # Let's assume passed in via dictionary.
                 pass

        if not has_fields and model_name != "User":
             lines.append("    pass")

        lines.append("")

        # Create Model
        lines.append(f"class {model_name}Create({model_name}Base):")
        if model_name == "User":
            lines.append("    password: str")
        else:
            lines.append("    pass")
        lines.append("")

        # Update Model (All fields optional)
        # MVP: Just strictly follow base for now, or make all optional
        lines.append(f"class {model_name}Update({model_name}Base):")
        lines.append("    pass")
        lines.append("")

        # Response Model (Includes ID)
        lines.append(f"class {model_name}Response({model_name}Base):")
        lines.append("    id: int")
        lines.append("")
        lines.append("    class Config:")
        lines.append("        from_attributes = True")
        lines.append("")
        
    return "\n".join(lines)

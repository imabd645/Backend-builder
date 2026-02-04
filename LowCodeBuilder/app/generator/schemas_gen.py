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
        ""
    ]

    for model_name, model_def in models.items():
        # Base API Model (Shared properties)
        lines.append(f"class {model_name}Base(BaseModel):")
        for field_name, field_def in model_def.fields.items():
            if field_name == "id": continue
            
            py_type = TYPE_MAPPING.get(field_def.type.lower(), "str")
            if not field_def.required:
                lines.append(f"    {field_name}: Optional[{py_type}] = None")
            else:
                lines.append(f"    {field_name}: {py_type}")
        
        # Add relation helper fields (Foreign Keys) to Base or Create?
        # Ideally to Base so they can be set.
        if model_def.relations:
            for field_name, _ in model_def.relations.items():
                 # user_id: int
                 lines.append(f"    {field_name}: int")

        lines.append("")

        # Create Model (Fields required on creation)
        lines.append(f"class {model_name}Create({model_name}Base):")
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
        lines.append("        orm_mode = True")
        lines.append("")
        
    return "\n".join(lines)

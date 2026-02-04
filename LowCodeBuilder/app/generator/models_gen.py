from typing import Dict
from ..schemas import ModelDefinition

TYPE_MAPPING = {
    "string": "String",
    "int": "Integer",
    "boolean": "Boolean",
    "float": "Float",
    "datetime": "DateTime",
    "text": "Text"
}

def generate_models_file(models: Dict[str, ModelDefinition]) -> str:
    lines = [
        "from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, Text, ForeignKey, create_engine",
        "from sqlalchemy.orm import relationship, declarative_base",
        "from datetime import datetime",
        "",
        "Base = declarative_base()",
        ""
    ]

    for model_name, model_def in models.items():
        lines.append(f"class {model_name}(Base):")
        lines.append(f"    __tablename__ = '{model_name.lower()}s'")
        lines.append(f"    id = Column(Integer, primary_key=True, index=True)")
        
        # Fields
        for field_name, field_def in model_def.fields.items():
            if field_name == "id": continue # Skip ID as it's auto-added
            
            sa_type = TYPE_MAPPING.get(field_def.type.lower(), "String")
            nullable = "True" if not field_def.required else "False"
            lines.append(f"    {field_name} = Column({sa_type}, nullable={nullable})")
            
        # Relations (Simple One-to-Many implementation for MVP)
        # Assuming format: "user_id": "User" means this model belongs to User
        if model_def.relations:
            for field_name, target_model in model_def.relations.items():
                 # Foreign Key Column e.g. user_id = Column(Integer, ForeignKey("users.id"))
                 # We assume the relation field name is the foreign key itself
                lines.append(f"    {field_name} = Column(Integer, ForeignKey('{target_model.lower()}s.id'))")
                
                # Relationship e.g. user = relationship("User", back_populates="posts")
                # We need to guess the back_populates name or just not use it for MVP simplicity if possible
                # But for SQLAlchemy we usually need it.
                # Let's simple it:
                # relation_name: "user" derived from "user_id"
                rel_name = field_name.replace("_id", "")
                lines.append(f"    {rel_name} = relationship('{target_model}')")

        lines.append("")
        
    return "\n".join(lines)

from typing import Dict
from ..schemas import ModelDefinition

def generate_seed_file(models: Dict[str, ModelDefinition]) -> str:
    lines = [
        "from faker import Faker",
        "from sqlalchemy.orm import Session",
        "from . import models, database, auth",
        "",
        "fake = Faker()",
        "",
        "def seed_data():",
        "    db = database.SessionLocal()",
        "    try:",
        "        # Create Admin User",
        "        if not db.query(models.User).filter(models.User.email == 'admin@example.com').first():",
        "            admin_user = models.User(",
        "                email='admin@example.com',",
        "                hashed_password=auth.get_password_hash('admin123')",
        "            )",
        "            db.add(admin_user)",
        "            print('Created admin user: admin@example.com / admin123')",
        "",
        ""
    ]
    
    # Generate seed data for other models
    for model_name, model_def in models.items():
        if model_name == "User": continue # Already handled admin user custom logic
        
        lines.append(f"        # Seed {model_name}")
        lines.append(f"        for _ in range(10):")
        lines.append(f"            item = models.{model_name}(")
        
        for field_name, field_def in model_def.fields.items():
            if field_name == "id": continue
            
            # Generate fake data based on type/name
            fake_val = "fake.word()"
            t = field_def.type.lower()
            if t == "string":
                if "email" in field_name.lower(): fake_val = "fake.email()"
                elif "name" in field_name.lower(): fake_val = "fake.name()"
                elif "url" in field_name.lower(): fake_val = "fake.url()"
                else: fake_val = "fake.text(max_nb_chars=50)"
            elif t == "int":
                fake_val = "fake.random_int(min=1, max=100)"
            elif t == "float":
                fake_val = "fake.pyfloat(positive=True)"
            elif t == "boolean":
                fake_val = "fake.boolean()"
            elif t == "datetime":
                fake_val = "fake.date_time_this_year()"
            
            lines.append(f"                {field_name}={fake_val},")
            
        lines.append(f"            )")
        lines.append(f"            db.add(item)")
        lines.append(f"        print('Seeded 10 {model_name} items')")
        lines.append("")

    lines.append("        db.commit()")
    lines.append("        print('Seeding complete!')")
    lines.append("    finally:")
    lines.append("        db.close()")
    lines.append("")
    lines.append("if __name__ == '__main__':")
    lines.append("    seed_data()")
    
    return "\n".join(lines)

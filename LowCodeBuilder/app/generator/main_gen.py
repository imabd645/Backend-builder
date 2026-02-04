import os
import io
import zipfile
from typing import Dict, Any
from ..schemas import ProjectSchema, ModelDefinition
from .models_gen import generate_models_file
from .schemas_gen import generate_schemas_file
from .router_gen import generate_router_file

# Boilerplate Content
DATABASE_PY = """
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
"""

AUTH_PY = """
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from . import database, models, schemas

# SECURITY CONFIG
SECRET_KEY = "CHANGE_THIS_TO_A_REAL_SECRET_KEY"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(models.User).filter(models.User.email == username).first()
    if user is None:
        raise credentials_exception
    return user
"""

REQUIREMENTS_TXT = """
fastapi
uvicorn
sqlalchemy
pydantic
python-multipart
passlib[bcrypt]
python-jose[cryptography]
sqladmin
"""

DOCKERFILE = """
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""

DOCKER_COMPOSE = """
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    environment:
      - DATABASE_URL=sqlite:///./app.db
"""

def generate_project_zip(project_schema: ProjectSchema) -> bytes:
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # 1. Base files
        zip_file.writestr("app/database.py", DATABASE_PY)
        zip_file.writestr("app/auth.py", AUTH_PY)
        zip_file.writestr("requirements.txt", REQUIREMENTS_TXT)
        zip_file.writestr("Dockerfile", DOCKERFILE)
        zip_file.writestr("docker-compose.yml", DOCKER_COMPOSE)
        zip_file.writestr("app/__init__.py", "")
        
        # 2. Models
        models_code = generate_models_file(project_schema.models)
        zip_file.writestr("app/models.py", models_code)
        
        # 3. Schemas (Pydantic)
        schemas_code = generate_schemas_file(project_schema.models)
        zip_file.writestr("app/schemas.py", schemas_code)
        
        # 4. Routers
        router_imports = []
        router_inclusions = []
        
        # Auth Router
        from .auth_gen import generate_auth_router
        zip_file.writestr("app/routers/auth.py", generate_auth_router())
        router_imports.append("from .routers import auth")
        router_inclusions.append("app.include_router(auth.router)")
        
        # Create routers package
        zip_file.writestr("app/routers/__init__.py", "")
        
        for model_name, model_def in project_schema.models.items():
            # Get API config for this model, default to all public/enabled if missing
            api_config = project_schema.apis.get(model_name, {
                "create": "public", "read": "public", "update": "public", "delete": "public"
            })
            
            router_code = generate_router_file(model_name, model_def, api_config)
            zip_file.writestr(f"app/routers/{model_name.lower()}.py", router_code)
            
            router_imports.append(f"from .routers import {model_name.lower()}")
            router_inclusions.append(f"app.include_router({model_name.lower()}.router)")

        # 5. Admin Panel
        from .admin_gen import generate_admin_file
        zip_file.writestr("app/admin.py", generate_admin_file(project_schema.models))

        # 6. Main App
        main_lines = [
            "from fastapi import FastAPI",
            "from sqladmin import Admin",
            "from . import models, database, admin"
        ]
        
        # Imports from routers
        main_lines.append("from .routers import auth")
        main_lines.extend(router_imports)
        
        main_lines.extend([
            "",
            "models.Base.metadata.create_all(bind=database.engine)",
            "",
            "app = FastAPI(title='Generated App')",
            ""
        ])
        
        # Admin Setup
        main_lines.extend([
            "# Admin Panel",
            "admin_panel = Admin(app, database.engine)",
            ""
        ])
        
        # Register Admin Views
        for model_name in project_schema.models.keys():
            main_lines.append(f"admin_panel.add_view(admin.{model_name}Admin)")
        if "User" not in project_schema.models: # Add UserAdmin if implicitly created
             main_lines.append("admin_panel.add_view(admin.UserAdmin)")
             
        main_lines.append("")
        
        # Include routers
        main_lines.append("app.include_router(auth.router)")
        main_lines.extend(router_inclusions)
        
        main_lines.extend([
            "",
            "@app.get('/')",
            "def read_root():",
            "    return {'message': 'Welcome to your generated API. Go to /docs for API or /admin for Admin Panel'}",
            ""
        ])
        
        zip_file.writestr("app/main.py", "\n".join(main_lines))
        
        # 7. Run script
        zip_file.writestr("run.py", "import uvicorn\n\nif __name__ == '__main__':\n    uvicorn.run('app.main:app', reload=True)")

    return zip_buffer.getvalue()

import requests
import zipfile
import io
import os

BASE_URL = "http://127.0.0.1:8000/api"

def test_builder():
    print("Testing Builder API...")
    
    # 1. Create Project
    res = requests.post(f"{BASE_URL}/projects", json={"name": "Test Project"})
    if res.status_code != 200:
        print("Failed to create project:", res.text)
        return
    
    project = res.json()
    project_id = project["id"]
    print(f"Created project: {project['name']} ({project_id})")
    
    # 2. Update Project (Add a Model)
    # Simulate what frontend sends
    new_schema = project["schema_data"]
    new_schema["models"]["Post"] = {
        "fields": {
            "title": {"type": "string", "required": True},
            "content": {"type": "text", "required": True}
        },
        "relations": {}
    }
    new_schema["apis"] = {
        "Post": {"create": "auth", "read": "public", "update": "auth", "delete": "admin"}
    }
    
    res = requests.put(f"{BASE_URL}/projects/{project_id}", json={
        "schema_data": new_schema
    })
    if res.status_code != 200:
        print("Failed to update project:", res.text)
        return
    print("Updated project schema with 'Post' model.")
    
    # 3. Generate Code
    print("Requesting code generation...")
    res = requests.get(f"{BASE_URL}/projects/{project_id}/generate")
    if res.status_code != 200:
        print("Failed to generate code:", res.text)
        return
    
    # 4. Verify ZIP
    try:
        z = zipfile.ZipFile(io.BytesIO(res.content))
        print("ZIP generated successfully.")
        print("Files in ZIP:", z.namelist())
        
        expected_files = [
            "app/main.py", 
            "app/models.py", 
            "app/schemas.py", 
            "app/routers/post.py",
            "app/routers/auth.py", 
            "app/admin.py",
            "requirements.txt",
            "Dockerfile",
            "docker-compose.yml"
        ]
        
        for f in expected_files:
            if f not in z.namelist():
                print(f"ERROR: Missing expected file {f}")
                return
        
        # Check if auth.py content has SECRET_KEY
        auth_content = z.read("app/auth.py").decode("utf-8")
        if "pwd_context" in auth_content:
             print("Auth content check passed (Bcrypt present).")
             
        # Check requirements
        req_content = z.read("requirements.txt").decode("utf-8")
        if "passlib" in req_content:
             print("Requirements check passed (Passlib present).")
        
        print("SUCCESS: All expected files present.")
        
        # Optional: Check content of routers/post.py
        router_content = z.read("app/routers/post.py").decode("utf-8")
        if "@router.post" in router_content and "admin" in router_content: # admin check logic might be complex but 'admin' string should be there in comment or logic
             print("Router content check passed (basic).")
        
    except Exception as e:
        print("Failed to process ZIP:", e)

if __name__ == "__main__":
    try:
        test_builder()
    except requests.exceptions.ConnectionError:
        print("Could not connect to server. Make sure it is running.")

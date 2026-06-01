from typing import Optional

from fastapi import FastAPI, HTTPException
import logging

from fastapi.params import Depends 
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.openapi.utils import get_openapi

config = {
    "app_name": "Ethical Hacking 2025 CTF",
    "version": "6.7.0",
    "description": "An example FastAPI application with Basic Auth for admin endpoints.",
    "authors": ["Serban Tonie", "Andrew Rutherfoord"],
    "debug": True,
    "admin_user": "admin",
    "admin_password": "jhz-tfv1deg5betMAV"
}

app = FastAPI()
security = HTTPBasic()

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=config["app_name"],
        version=config["version"],
        description=config["description"],
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "basicAuth": {"type": "http", "scheme": "basic"}
    }
    for path in openapi_schema["paths"].values():
        for method in path.values():
            method["security"] = [{"basicAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

class AuthUser:
    def __init__(self, username: str):
        self.username = username
    
    def __str__(self):
        return f"AuthUser(username={self.username})"
    
    def model_dump(self) -> dict:
        """Convert to dictionary (compatible with both Pydantic v1 and v2)."""
        return {"username": self.username}

def get_basic_auth_credentials() -> tuple[str, str]:
    """Get basic auth credentials from environment variables."""
    username = config.get("admin_user", "admin")
    password = config.get("admin_password", "admin")
    return username, password

def validate_basic_auth(credentials: HTTPBasicCredentials) -> Optional[AuthUser]:
    expected_username, expected_password = get_basic_auth_credentials()

    if (
        credentials.username == expected_username
        and credentials.password == expected_password
    ):
        logging.info(f"Basic auth successful for user: {credentials.username}")
        return AuthUser(credentials.username)
    else:
        logging.warning(f"Basic auth failed for user: {credentials.username}")
        return None

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)) -> AuthUser: # type: ignore
    """Dependency that validates Basic Auth and returns the authenticated user."""
    user = validate_basic_auth(credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return user

@app.get("/")
def read_root():
    return {"message": "Welcome to the Ethical Hacking 2025 CTF API!"}

@app.get("/debug/info")
def debug_info():
    if not config.get("debug", False):
        return HTTPException(status_code=403, detail="Debugging endpoint is disabled.")
    """
    Endpoint used only for DEVELOPMENT and DEBUGGING purposes.
    Outputs the settings of the application.
    """
    return config

@app.get("/admin")
def read_admin_data(user :AuthUser = Depends(get_current_user)): # type: ignore
    """
    Example admin endpoint that requires basic authentication.
    """
    with open("/app/flag.txt", "r") as f:
        flag_file_contents = f.read()
    return {"message": f"Welcome, {user.username}!", "admin_data": flag_file_contents}

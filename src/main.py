from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException
from datetime import datetime,timedelta
from src.auth.dependencies import get_current_app, jwt_handler
from passlib.context import CryptContext
from pydantic import BaseModel



ACCESS_TOKEN_EXPIRE_MINUTES = 30

class Login(BaseModel):
    username: str
    password: str

app=FastAPI()

#GET,POST,PUT,DELET
@app.get("/")
def index():
    return {"message":"API is running"}

@app.get("/about")
def about():
    return {"message":"About Page"}

@app.get("/contact")
def contact():
    return {"message":"Contact Page"}

@app.get("/protected")
async def protected_route(current_user = Depends(get_current_app)):
    return {"message": "This is protected"}

@app.post("/token")
def issue_token(login: Login):
    # dev-only check
    if login.username != "test" or login.password != "pass":
        raise HTTPException(status_code=401, detail="Invalid credentials")

    payload = {
        "sub": login.username,
        "role": "admin",
        "app_id": "test_app",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    token = jwt_handler.create_token(payload)
    return {"access_token": token, "token_type": "bearer"}
    
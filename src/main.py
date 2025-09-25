from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException
from datetime import datetime,timedelta
from src.auth.dependencies import get_current_app, get_blob_storage_service, jwt_handler
from src.services.azure_config import AzureKeyVaultConfig
from src.services.blob_storage_service import BlobStorageService
from passlib.context import CryptContext
from pydantic import BaseModel
from src.translation.scriptroutes import router as script_router
import logging


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

ACCESS_TOKEN_EXPIRE_MINUTES = 30

logger = logging.getLogger(__name__)

class Login(BaseModel):
    username: str
    password: str

class DocumentAnalysisRequest(BaseModel):
    container_name: str
    blob_path: str

class ListBlobsRequest(BaseModel):
    container_name: str

app = FastAPI()
app.include_router(script_router)
#GET,POST,PUT,DELET
@app.get("/")
def index():
    try:
        azure_config = AzureKeyVaultConfig("https://aifastapi.vault.azure.net")
        secret = azure_config.get_secret("OPENAI-KEY")
        return {"message":"API is running", "secret": secret}
    except Exception as e:
        logger.error(f"Error getting secret: {str(e)}")
        return {"message":"API is running", "error": str(e)}

    

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

@app.post("/analyze-document")
async def analyze_document(
    request: DocumentAnalysisRequest, 
    current_user = Depends(get_current_app),
    blob_service: BlobStorageService = Depends(get_blob_storage_service)
):
    try:
        analysis_result = blob_service.analyze_text_document(
            request.container_name, 
            request.blob_path
        )
        
        return {
            "status": "success",
            "document_path": f"{request.container_name}/{request.blob_path}",
            "analysis": analysis_result,
            "analyzed_by": current_user.get("sub", "unknown")
        }
        
    except Exception as e:
        logger.error(f"Document analysis failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze document: {str(e)}"
        )

@app.post("/list-blobs")
async def list_blobs(
    request: ListBlobsRequest,
    current_user = Depends(get_current_app),
    blob_service: BlobStorageService = Depends(get_blob_storage_service)
):
    try:
        result = blob_service.list_blobs_in_container(request.container_name)
        
        return {
            "status": "success",
            "container": result,
            "requested_by": current_user.get("sub", "unknown")
        }
        
    except Exception as e:
        logger.error(f"Failed to list blobs: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list blobs in container: {str(e)}"
        )
    
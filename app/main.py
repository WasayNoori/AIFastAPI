from fastapi import FastAPI

api=FastAPI()

#GET,POST,PUT,DELETE
@api.get("/")
def index():
    return {"message":"Hello World"}

@api.get("/about")
def about():
    return {"message":"About Page"}

@api.get("/contact")
def contact():
    return {"message":"Contact Page"}


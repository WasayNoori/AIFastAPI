from fastapi import FastAPI

app=FastAPI()

#GET,POST,PUT,DELETE
@app.get("/")
def index():
    return {"message":"Hello World"}

@app.get("/about")
def about():
    return {"message":"About Page"}

@app.get("/contact")
def contact():
    return {"message":"Contact Page"}


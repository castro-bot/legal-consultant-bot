from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from routers import webhook
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI(title="Ecuadorian Legal Consultant Bot")

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Register the router
app.include_router(webhook.router)

if __name__ == "__main__":
    import uvicorn
    # Run with reload for dev
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
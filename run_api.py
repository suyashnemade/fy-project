import uvicorn
from newuiapi.main import app

if __name__ == "__main__":
    # Start the FastAPI server programmatically. 
    # Must use 127.0.0.1 and port 8000 to match the frontend expectations securely.
    uvicorn.run(app, host="127.0.0.1", port=8000)

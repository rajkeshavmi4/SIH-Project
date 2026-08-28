import uvicorn
import os

if __name__ == "__main__":
    print("==================================================")
    print("  PolarRoute AI — Mission Control Running")
    print("  Dashboard: http://127.0.0.1:8000")
    print("==================================================")
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
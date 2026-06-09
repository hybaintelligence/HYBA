from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Python backend is alive"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

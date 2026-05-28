import uvicorn
import os

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("YOLO_HOST", "0.0.0.0"),
        port=int(os.getenv("YOLO_PORT", "8000")),
        reload=True,
    )

import uvicorn
import os

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("AICHAT_HOST", "0.0.0.0"),
        port=int(os.getenv("AICHAT_PORT", "5000")),
        reload=False,
        timeout_keep_alive=120,
    )

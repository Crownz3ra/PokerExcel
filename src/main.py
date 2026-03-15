import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_PATH = r"C:\Users\fsa12\Desktop\PokerApp\data\processed"


@app.get("/api/strategy/{folder}/{position}")
async def get_strategy(folder: str, position: str):
    path = os.path.join(BASE_PATH, folder, position, "tabela_final.json")
    if not os.path.exists(path):
        raise HTTPException(
            status_code=404, detail=f"Sem dados para {folder}/{position}"
        )
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


app.mount(
    "/",
    StaticFiles(directory=r"C:\Users\fsa12\Desktop\PokerApp\frontend", html=True),
    name="frontend",
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)

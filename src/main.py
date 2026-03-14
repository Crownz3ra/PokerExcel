from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# A MÁGICA ESTÁ AQUI: O caminho (Path) define onde estamos na mão.
# Ex: "UTG" (Início) -> "UTG:Raise 2" (UTG abriu) -> "UTG:Raise 2|HJ:Call" (UTG abriu, HJ pagou)
ARVORE_GTO = {
    "ROOT": {
        "posicao_atual": "UTG",
        "historico": [], # Ninguém agiu ainda
        "acoes_possiveis": ["Fold", "Raise 2", "Allin"],
        "estrategia": {
            "AA": {"Raise 2": 1.0}, "A5s": {"Raise 2": 0.5, "Fold": 0.5}, "72o": {"Fold": 1.0}
        }
    },
    "ROOT|Fold": {
        "posicao_atual": "HJ",
        "historico": [{"pos": "UTG", "acao": "Fold"}],
        "acoes_possiveis": ["Fold", "Raise 2", "Allin"],
        "estrategia": {
            "AA": {"Raise 2": 1.0}, "KQs": {"Raise 2": 0.8, "Fold": 0.2}, "72o": {"Fold": 1.0}
        }
    },
    "ROOT|Raise 2": {
        "posicao_atual": "HJ",
        "historico": [{"pos": "UTG", "acao": "Raise 2"}],
        "acoes_possiveis": ["Fold", "Call", "Raise 7", "Allin"],
        "estrategia": {
            "AA": {"Raise 7": 1.0}, "AQs": {"Call": 0.5, "Raise 7": 0.5}, "55": {"Call": 0.9, "Fold": 0.1}
        }
    },
    "ROOT|Raise 2|Call": {
        "posicao_atual": "CO",
        "historico": [{"pos": "UTG", "acao": "Raise 2"}, {"pos": "HJ", "acao": "Call"}],
        "acoes_possiveis": ["Fold", "Call", "Raise 12", "Allin"],
        "estrategia": {
            "AA": {"Raise 12": 1.0}, "QQ": {"Call": 0.7, "Raise 12": 0.3}, "22": {"Fold": 1.0}
        }
    }
}

@app.get("/api/node/{path:path}")
async def get_node(path: str):
    # Se o caminho não existir no nosso banco de dados, retorna um erro amigável
    if path not in ARVORE_GTO:
        return {"error": "Cenário não mapeado (O Bot precisa extrair esta ramificação)"}
    
    return ARVORE_GTO[path]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
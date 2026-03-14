import json
import os

def classificar_cor_rgb(r, g, b):
    if r > 150 and r > g * 1.5 and r > b * 1.5:
        return "Raise"
    if r > 150 and g > 80 and b < 80:
        return "Raise"
    if g > 100 and g > r * 1.2 and g > b * 1.2:
        return "Call"
    return "Fold"

def traduzir_estilo(dados_celula):
    res = {"Raise": 0.0, "Call": 0.0, "Fold": 0.0}
    acoes = dados_celula.get("acoes", [])

    if not acoes:
        res["Fold"] = 100.0
        return res

    for i, acao in enumerate(acoes):
        cor = acao.get("cor")
        pct = acao.get("pct", 0.0)

        if not cor:
            continue

        nome = classificar_cor_rgb(cor["r"], cor["g"], cor["b"])

        if i == 0:
            res[nome] += pct
        else:
            pct_anterior = acoes[i-1].get("pct", 0.0)
            fatia = pct - pct_anterior
            if fatia > 0:
                res[nome] += fatia

    total = sum(res.values())
    if total < 99.0:
        res["Fold"] += 100.0 - total

    return normalizar(res)

def normalizar(res):
    total = sum(res.values())
    if total > 0:
        return {
            "Raise": round((res["Raise"] / total) * 100, 1),
            "Call":  round((res["Call"]  / total) * 100, 1),
            "Fold":  round((res["Fold"]  / total) * 100, 1)
        }
    return {"Raise": 0.0, "Call": 0.0, "Fold": 100.0}

def processar_tudo():
    base_path = os.path.join(os.getcwd(), "data", "processed")
    if not os.path.exists(base_path):
        print("❌ Pasta data/processed não encontrada.")
        return

    for root, dirs, files in os.walk(base_path):
        if "tabela_bruta.json" in files:
            arquivo_bruto = os.path.join(root, "tabela_bruta.json")
            print(f"⚙️ Processando: {root}")

            with open(arquivo_bruto, "r", encoding="utf-8") as f:
                brutos = json.load(f)

            final = {}
            for mao, dados in brutos.items():
                final[mao] = traduzir_estilo(dados)

            with open(os.path.join(root, "tabela_final.json"), "w", encoding="utf-8") as f:
                json.dump(final, f, indent=4)

    print("\n✨ Processamento concluído!")

if __name__ == "__main__":
    processar_tudo()
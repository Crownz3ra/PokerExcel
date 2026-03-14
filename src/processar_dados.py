import json
import os
import re

def classificar_acao(cor_str):
    cor_str = cor_str.lower()
    if not cor_str or "transparent" in cor_str or "none" in cor_str: 
        return "Fold"

    # Extração de RGB e avaliação lógica de cor
    rgb_match = re.search(r'rgb[a]?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)', cor_str)
    if rgb_match:
        r = int(rgb_match.group(1))
        g = int(rgb_match.group(2))
        b = int(rgb_match.group(3))
        if r > g + 30 and r > b + 30: return "Raise"
        if g > r + 20 and g > b + 20: return "Call"
        return "Fold"
        
    # Extração de HEX e avaliação lógica de cor
    hex_match = re.search(r'#([0-9a-f]{6}|[0-9a-f]{3})', cor_str)
    if hex_match:
        hx = hex_match.group(1)
        if len(hx) == 3: 
            hx = hx[0]*2 + hx[1]*2 + hx[2]*2
        r = int(hx[0:2], 16)
        g = int(hx[2:4], 16)
        b = int(hx[4:6], 16)
        if r > g + 30 and r > b + 30: return "Raise"
        if g > r + 20 and g > b + 20: return "Call"
        return "Fold"
        
    return "Fold"

def traduzir_estilo(dados_celula):
    res = {"Raise": 0.0, "Call": 0.0, "Fold": 0.0}
    
    bg_color = dados_celula.get("bgColor", "")
    bg_img = dados_celula.get("bgImage", "")
    bg_size = dados_celula.get("bgSize", "")

    # 1. Gradiente CSS fatiado do GTO Wizard
    if bg_size and "100%" in bg_size:
        sizes = []
        for p in bg_size.split(","):
            match = re.search(r'([\d\.]+)%', p)
            if match: 
                sizes.append(float(match.group(1)))
        
        layers_colors = []
        gradientes = re.findall(r'linear-gradient\((.*?)\)', bg_img)
        for grad in gradientes:
            color_match = re.search(r'(rgb[a]?\([^)]+\)|#[a-f0-9]{3,6})', grad)
            layers_colors.append(color_match.group(0) if color_match else "")
            
        if sizes and len(sizes) <= len(layers_colors):
            ultimo_w = 0.0
            for i in range(len(sizes)):
                w = sizes[i]
                c = layers_colors[i]
                tamanho = w - ultimo_w
                if tamanho > 0: 
                    acao = classificar_acao(c)
                    res[acao] += tamanho
                ultimo_w = w
                
            if ultimo_w < 99.9: 
                acao = classificar_acao(bg_color)
                res[acao] += (100.0 - ultimo_w)
            
            return normalizar(res)

    # 2. Formato clássico de percentagens contínuas
    partes = re.findall(r'((?:rgb[a]?\([^)]+\)|#[a-f0-9]+))\s+([\d\.]+)%', bg_img)
    if partes:
        ultimo_pct = 0.0
        for cor, pct_str in partes:
            pct = float(pct_str)
            tamanho = pct - ultimo_pct
            if tamanho > 0: 
                acao = classificar_acao(cor)
                res[acao] += tamanho
            ultimo_pct = pct
        if ultimo_pct < 99.9:
            acao = classificar_acao(bg_color)
            res[acao] += (100.0 - ultimo_pct)
        return normalizar(res)

    # 3. Cor sólida (100% Fold/Call/Raise)
    if bg_color and bg_color != "rgba(0, 0, 0, 0)" and bg_color != "transparent":
        acao = classificar_acao(bg_color)
        res[acao] += 100.0
    else:
        acao = classificar_acao(bg_img)
        res[acao] += 100.0

    return normalizar(res)

def normalizar(res):
    total = sum(res.values())
    if total > 0:
        return {"Raise": round((res["Raise"]/total)*100, 1), 
                "Call": round((res["Call"]/total)*100, 1), 
                "Fold": round((res["Fold"]/total)*100, 1)}
    return {"Raise": 0.0, "Call": 0.0, "Fold": 100.0}

def processar_tudo():
    base_path = os.path.join(os.getcwd(), "data", "processed")
    if not os.path.exists(base_path): 
        return

    for root, dirs, files in os.walk(base_path):
        if "tabela_bruta.json" in files:
            arquivo_bruto = os.path.join(root, "tabela_bruta.json")
            print(f"⚙️ Convertendo ficheiro matemático: {root}")
            
            with open(arquivo_bruto, "r", encoding="utf-8") as f:
                brutos = json.load(f)

            final = {}
            for mao, dados in brutos.items():
                final[mao] = traduzir_estilo(dados)
            
            with open(os.path.join(root, "tabela_final.json"), "w", encoding="utf-8") as f:
                json.dump(final, f, indent=4)
                
    print("\n✨ Matrizes processadas com sucesso! Zero erros de sintaxe.")

if __name__ == "__main__":
    processar_tudo()
import pandas as pd

ranks = 'AKQJT98765432'

# Exemplo de Range de RFI (Raise First In) para o BTN (Botão) - Bem agressivo!
range_btn = [
    'AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88', '77', '66', '55', '44', '33', '22',
    'AKs', 'AQs', 'AJs', 'ATs', 'A9s', 'A8s', 'A7s', 'A5s', 'KQs', 'KJs', 'KTs', 'QJs', 'QTs', 'JTs',
    'AKo', 'AQo', 'AJo', 'KQo'
]

def criar_matriz_decisao(posicao_range):
    matriz = []
    for i in range(13):
        linha = []
        for j in range(13):
            r1, r2 = ranks[i], ranks[j]
            if i == j:
                mao = f"{r1}{r2}"
            elif i < j:
                mao = f"{r1}{r2}s"
            else:
                mao = f"{r2}{r1}o"
            
            # Lógica de Decisão: Se a mão está no range, RAISE (R), senão FOLD (.)
            if mao in posicao_range:
                linha.append(" RAISE ")
            else:
                linha.append("   .   ")
        matriz.append(linha)
    
    return pd.DataFrame(matriz, index=list(ranks), columns=list(ranks))

print("\n=== POKER EXCEL: RANGE DE RFI (BTN) ===")
print(criar_matriz_decisao(range_btn))
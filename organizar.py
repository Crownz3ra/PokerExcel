import os
import shutil

def faxina_total():
    # 1. Definição do mapa de pastas
    pastas = {
        'src': ['.py'],
        'data/raw': ['tabela_bruta.json'],
        'data/processed': ['tabela_final.json'],
        'frontend': ['.html', '.css', '.js'],
        'config': ['sessao_gto.json'],
        'logs': ['.png', '.jpg']
    }

    # 2. Criar as pastas se não existirem
    for pasta in pastas.keys():
        os.makedirs(pasta, exist_ok=True)
        print(f"📁 Pasta verificada: {pasta}")

    # 3. Mover os arquivos para seus devidos lugares
    for arquivo in os.listdir('.'):
        # Ignora o próprio script de organização para ele não se mover
        if arquivo == 'organizar.py':
            continue
            
        nome, extensao = os.path.splitext(arquivo)

        # Lógica de movimentação por tipo ou nome exato
        moved = False
        for pasta, regras in pastas.items():
            if arquivo in regras or extensao in regras:
                dest = os.path.join(pasta, arquivo)
                # Se o arquivo já existe no destino, ele substitui (limpeza)
                shutil.move(arquivo, dest)
                print(f"📦 {arquivo} -> {pasta}/")
                moved = True
                break

    print("\n✨ O projeto agora está 100% organizado!")

if __name__ == "__main__":
    faxina_total()
from playwright.sync_api import sync_playwright
# A importação correta para a versão 2.0+ (com 'S' maiúsculo)
from playwright_stealth import Stealth

def fazer_login_camuflado():
    with sync_playwright() as p:
        # Abre o navegador
        navegador = p.chromium.launch(headless=False)
        contexto = navegador.new_context()
        
        # A MÁGICA ATUALIZADA AQUI: Aplica a camuflagem no contexto inteiro
        Stealth().apply_stealth_sync(contexto)
        
        # Cria a aba já camuflada
        pagina = contexto.new_page()
        
        print("🕵️‍♂️ Camuflagem ativada com sucesso! Acessando a página de login...")
        pagina.goto("https://app.gtowizard.com/login")
        
        print("\n" + "="*50)
        print("Tente fazer o seu login com o Google agora.")
        print("O sistema anti-bot deve ignorar você.")
        print("="*50 + "\n")
        
        # Espera você logar
        input("Pressione ENTER aqui no terminal APÓS ver as tabelas do GTO Wizard...")
        
        # Salva a sessão
        contexto.storage_state(path="sessao_gto.json")
        print("✅ Sessão capturada! O arquivo sessao_gto.json foi criado.")
        
        navegador.close()

if __name__ == "__main__":
    fazer_login_camuflado()
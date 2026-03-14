from playwright.sync_api import sync_playwright

def capturar_sessao_real():
    print("🔌 Conectando ao seu Chrome real na porta 9222...")
    
    with sync_playwright() as p:
        try:
            # Conecta ao navegador que você abriu pelo CMD
            navegador = p.chromium.connect_over_cdp("http://localhost:9222")
            
            # Pega o contexto (onde ficam os cookies e a sessão)
            contexto = navegador.contexts[0]
            
            # A MÁGICA: Puxa todos os cookies da sua navegação real e salva no arquivo!
            contexto.storage_state(path="sessao_gto.json")
            
            print("✅ SESSÃO ROUBADA COM SUCESSO! O arquivo 'sessao_gto.json' foi criado.")
            print("Você já pode fechar o Chrome do CMD. O Bot não precisa mais dele!")
            
            navegador.disconnect()
            
        except Exception as e:
            print("\n❌ Erro ao conectar. Certifique-se de que rodou o comando no CMD.")
            print(f"Detalhe: {e}")

if __name__ == "__main__":
    capturar_sessao_real()
import os
import json
from playwright.sync_api import sync_playwright

def salvar_dados(pagina, pasta_cenario, posicao):
    print(f"🔎 Extração em Camadas (Solução Claude): {pasta_cenario} -> {posicao}")
    pagina.wait_for_timeout(2500) 
    
    dados = pagina.evaluate("""() => {
        // Passo 1: Achar os 169 elementos de texto
        const candidatos = [];
        document.querySelectorAll('*').forEach(el => {
            const txt = el.innerText ? el.innerText.trim() : "";
            if (/^[AKQJT98765432]{2}[so]?$/.test(txt) && txt.length <= 3) {
                const rect = el.getBoundingClientRect();
                if (rect.width > 10 && rect.height > 10) {
                    candidatos.push({ el: el, txt: txt, rect: rect });
                }
            }
        });

        const grupos = {};
        candidatos.forEach(c => {
            const chave = Math.round(c.rect.width) + 'x' + Math.round(c.rect.height);
            grupos[chave] = (grupos[chave] || 0) + 1;
        });
        const melhorChave = Object.keys(grupos).reduce((a, b) => grupos[a] > grupos[b] ? a : b);
        const matrizFinal = candidatos.filter(c =>
            (Math.round(c.rect.width) + 'x' + Math.round(c.rect.height)) === melhorChave
        );

        // Função auxiliar: resolve var(--clr-xxx) inspecionando o root
        function resolveVar(value, el) {
            if (!value || !value.includes('var(')) return value;
            return value.replace(/var\((--[\\w-]+)\)/g, (match, varName) => {
                return window.getComputedStyle(document.documentElement).getPropertyValue(varName).trim()
                    || window.getComputedStyle(el).getPropertyValue(varName).trim()
                    || match;
            });
        }

        // Função auxiliar: verifica se uma cor é "real" (não transparente)
        function corReal(c) {
            return c && c !== 'rgba(0, 0, 0, 0)' && c !== 'transparent' && c !== 'none' && c !== '';
        }

        const resultados = {};

        matrizFinal.forEach(c => {
            const x = c.rect.left + c.rect.width / 2;
            const y = c.rect.top  + c.rect.height / 2;

            let bgImg = "", bgColor = "", bgSize = "", fonte = "";

            // Estratégia A: subir o DOM a partir do elemento de texto e procurar irmãos/filhos
            const candidatosLocais = [c.el];

            if (c.el.parentElement) {
                Array.from(c.el.parentElement.children).forEach(irmao => {
                    if (irmao !== c.el) candidatosLocais.push(irmao);
                });
            }

            let cursor = c.el;
            for (let i = 0; i < 4; i++) {
                if (!cursor.parentElement) break;
                cursor = cursor.parentElement;
                candidatosLocais.push(cursor);
                Array.from(cursor.children).forEach(filho => {
                    if (!candidatosLocais.includes(filho)) candidatosLocais.push(filho);
                });
            }

            for (const el of candidatosLocais) {
                const comp = window.getComputedStyle(el);
                const img  = resolveVar(comp.backgroundImage, el);
                const cor  = resolveVar(comp.backgroundColor, el);
                const sz   = comp.backgroundSize;

                if (img && img.includes('gradient')) {
                    bgImg = img; bgSize = sz; bgColor = cor; fonte = "gradient-dom";
                    break;
                }
                if (corReal(cor) && !bgColor) {
                    bgColor = cor; bgImg = img; bgSize = sz; fonte = "color-dom";
                }
            }

            // Estratégia B: elementsFromPoint como fallback (mais abrangente)
            if (!bgImg && !corReal(bgColor)) {
                const pixelEls = document.elementsFromPoint(x, y);
                // Filtra apenas elementos dentro da área da célula
                const dentroRect = pixelEls.filter(el => {
                    const r = el.getBoundingClientRect();
                    return r.left >= c.rect.left - 5
                        && r.top  >= c.rect.top  - 5
                        && r.right  <= c.rect.right  + 5
                        && r.bottom <= c.rect.bottom + 5;
                });

                for (const el of dentroRect) {
                    const comp = window.getComputedStyle(el);
                    const img  = resolveVar(comp.backgroundImage, el);
                    const cor  = resolveVar(comp.backgroundColor, el);

                    if (img && img.includes('gradient')) {
                        bgImg = img; bgSize = comp.backgroundSize; bgColor = cor;
                        fonte = "gradient-point"; break;
                    }
                    if (corReal(cor)) {
                        bgColor = cor; bgImg = img; bgSize = comp.backgroundSize;
                        fonte = "color-point"; break;
                    }
                }
            }

            // Estratégia C: checar atributos data-* e style inline
            if (!bgImg && !corReal(bgColor)) {
                const todosNoPixel = document.elementsFromPoint(x, y);
                for (const el of todosNoPixel) {
                    const inlineStyle = el.getAttribute('style') || "";
                    if (inlineStyle.includes('background')) {
                        bgImg   = el.style.backgroundImage   || "";
                        bgColor = el.style.backgroundColor   || "";
                        bgSize  = el.style.backgroundSize    || "";
                        fonte = "inline-style";
                        if (bgImg || corReal(bgColor)) break;
                    }
                    const dataColor = el.dataset.color || el.dataset.bg
                                   || el.dataset.action || el.dataset.strategy || "";
                    if (dataColor) {
                        bgColor = dataColor; fonte = "data-attr"; break;
                    }
                }
            }

            resultados[c.txt] = { bgImage: bgImg, bgSize: bgSize, bgColor: bgColor, fonte: fonte };
        });

        return resultados;
    }""")
    
    # Salvamento
    if dados:
        dir_path = os.path.join("data", "processed", pasta_cenario, posicao)
        os.makedirs(dir_path, exist_ok=True)
        with open(os.path.join(dir_path, "tabela_bruta.json"), "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=4)
            
        if len(dados) == 169:
            print(f"💎 SUCESSO: 169/169 mãos extraídas com as camadas do Claude.")
        else:
            print(f"⚠️ AVISO: Capturadas {len(dados)} mãos.")
    else:
        print(f"❌ Falha crítica: A extração do Claude retornou vazio.")

def clicar_posicao(pagina, pos):
    # Procura especificamente a caixa da posição (Ex: UTG 100)
    return pagina.evaluate(f"""() => {{
        const caixas = Array.from(document.querySelectorAll('div'));
        for (let n of caixas) {{
            if (n.innerText && n.innerText.startsWith("{pos}\\n")) {{
                n.click(); return true;
            }}
        }}
        return false;
    }}""")

def clicar_acao(pagina, acao):
    # Procura a ação dentro da caixa (Ex: Call ou Raise)
    return pagina.evaluate(f"""() => {{
        const caixas = Array.from(document.querySelectorAll('div'));
        for (let n of caixas) {{
            if (n.innerText && n.innerText.trim().startsWith("{acao}")) {{
                // Clica apenas se o texto for curto (botão de ação) e não a caixa inteira
                if (n.innerText.length < 20 && !n.innerText.includes("Allin")) {{
                    n.click(); return true;
                }}
            }}
        }}
        return false;
    }}""")

def resetar_arvore(pagina):
    # Usa a classe exata do botão que você encontrou na imagem
    try:
        pagina.locator('[data-tst="shrtbtn_reset_history"]').click(timeout=2000)
        pagina.wait_for_timeout(1000)
    except:
        print("⚠️ Botão de reset não encontrado, usando F5...")
        pagina.reload()
        pagina.wait_for_timeout(4000)

def extrair_arvore():
    with sync_playwright() as p:
        print("🚀 Bot V14 - GTO Wizard Clone Edition")
        caminho_perfil = r"C:\ChromeDevSession"
        contexto = p.chromium.launch_persistent_context(user_data_dir=caminho_perfil, channel="chrome", headless=False)
        pagina = contexto.pages[0]
        
        if "gtowizard" not in pagina.url:
            pagina.goto("https://app.gtowizard.com/solutions")

        input("\n1. Deixe a tela visível.\n2. Aperte ENTER para o robô mapear a árvore...\n")

        # --- FASE 1: ABERTURAS (RFI) ---
        print("\n--- FASE 1: ABERTURAS (RFI) ---")
        for pos in ['UTG', 'HJ', 'CO', 'BTN', 'SB', 'BB']:
            resetar_arvore(pagina)
            
            # A Regra de Ouro do BB (SB Limp)
            if pos == 'BB':
                print("▶️ Cenário Especial: BB RFI (SB Call)")
                if clicar_posicao(pagina, 'SB'):
                    pagina.wait_for_timeout(500)
                    if clicar_acao(pagina, 'Call'):
                        pagina.wait_for_timeout(500)
                        if clicar_posicao(pagina, 'BB'):
                            salvar_dados(pagina, "RFI", "BB")
            else:
                if clicar_posicao(pagina, pos):
                    salvar_dados(pagina, "RFI", pos)

        # --- FASE 2: DEFESA VS UTG RAISE ---
        print("\n--- FASE 2: DEFESA VS UTG RAISE ---")
        for pos in ['HJ', 'CO', 'BTN', 'SB', 'BB']:
            resetar_arvore(pagina)
            clicar_posicao(pagina, 'UTG')
            pagina.wait_for_timeout(800)
            
            if clicar_acao(pagina, 'Raise'):
                pagina.wait_for_timeout(800)
                if clicar_posicao(pagina, pos):
                    salvar_dados(pagina, "VS_UTG_RAISE", pos)

        print("\n🏁 EXTRAÇÃO FINALIZADA! Pode rodar o Processador.")
        contexto.close()

if __name__ == "__main__":
    extrair_arvore()
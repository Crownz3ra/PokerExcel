import os
import json
import shutil
from playwright.sync_api import sync_playwright

def limpar_dados():
    base_path = os.path.join("data", "processed")
    if os.path.exists(base_path):
        shutil.rmtree(base_path)
        print("🗑️ Pasta data/processed apagada com sucesso.")
    os.makedirs(base_path, exist_ok=True)

def salvar_dados(pagina, pasta_cenario, posicao):
    print(f"🔎 Extração Cirúrgica: {pasta_cenario} -> {posicao}")
    pagina.wait_for_timeout(2000)  # Alterado para 2000ms

    dados = pagina.evaluate(
        """() => {
        const resultados = {};
        document.querySelectorAll('[id^="0_"][class*="rtc"]').forEach(el => {
            const mao = el.id.replace(/^\\d+_/, '');
            const style = el.getAttribute('style') || '';
            const gradientes = [];
            const gradRegex = /linear-gradient\\([^)]+\\)/g;
            let match;
            while ((match = gradRegex.exec(style)) !== null) {
                gradientes.push(match[0]);
            }
            const tamanhos = [];
            const sizeMatch = style.match(/background-size:\\s*([^;]+)/);
            if (sizeMatch) {
                sizeMatch[1].split(',').forEach(s => tamanhos.push(s.trim()));
            }
            const acoes = gradientes.map((grad, i) => {
                const corMatch = grad.match(/rgb\\(\\s*(\\d+)\\s*,\\s*(\\d+)\\s*,\\s*(\\d+)\\s*\\)/);
                const cor = corMatch
                    ? { r: parseInt(corMatch[1]), g: parseInt(corMatch[2]), b: parseInt(corMatch[3]) }
                    : null;
                const tamanho = tamanhos[i] || '0% 0%';
                const pctMatch = tamanho.match(/([\\d.]+)%/);
                const pct = pctMatch ? parseFloat(pctMatch[1]) : 0;
                return { cor, pct, gradienteRaw: grad, tamanhoRaw: tamanho };
            });
            resultados[mao] = { acoes: acoes, styleRaw: style };
        });
        return resultados;
    }"""
    )

    if dados:
        dir_path = os.path.join("data", "processed", pasta_cenario, posicao)
        os.makedirs(dir_path, exist_ok=True)
        with open(
            os.path.join(dir_path, "tabela_bruta.json"), "w", encoding="utf-8"
        ) as f:
            json.dump(dados, f, indent=4)
        if len(dados) == 169:
            print(f"💎 SUCESSO: 169/169 mãos extraídas com método cirúrgico.")
        else:
            print(f"⚠️ AVISO: Capturadas {len(dados)} mãos (esperado 169).")
    else:
        print(f"❌ Falha: extração retornou vazio.")


def clicar_posicao(pagina, pos):
    return pagina.evaluate(
        f"""() => {{
        const caixas = Array.from(document.querySelectorAll('div'));
        for (let n of caixas) {{
            if (n.innerText && n.innerText.startsWith("{pos}\\n")) {{
                n.click(); return true;
            }}
        }}
        return false;
    }}"""
    )


def clicar_acao(pagina, acao, pos=None):
    if pos:
        return pagina.evaluate(
            f"""() => {{
            const container = document.querySelector('[data-tst*="preflop_{pos}"]');
            if (!container) return false;
            const botoes = Array.from(container.querySelectorAll('.hspotcrd_action_text'));
            for (let n of botoes) {{
                const txt = n.innerText.trim();
                if (txt.startsWith("{acao}") && !txt.includes("Allin")) {{
                    n.click(); return true;
                }}
            }}
            return false;
        }}"""
        )
    else:
        return pagina.evaluate(
            f"""() => {{
            const caixas = Array.from(document.querySelectorAll('.hspotcrd_action_text'));
            for (let n of caixas) {{
                const txt = n.innerText.trim();
                if (txt.startsWith("{acao}") && !txt.includes("Allin")) {{
                    n.click(); return true;
                }}
            }}
            return false;
        }}"""
        )


def resetar_arvore(pagina):
    try:
        pagina.locator('[data-tst="shrtbtn_reset_history"]').click(timeout=2000)
        pagina.wait_for_timeout(2000)  # Alterado para 2000ms
    except:
        print("⚠️ Botão de reset não encontrado, navegando para a página...")
        pagina.goto("https://app.gtowizard.com/solutions")
        pagina.wait_for_timeout(2000)  # Alterado para 2000ms


def extrair_arvore():
    with sync_playwright() as p:
        print("🚀 Bot V20 - Tempos padronizados (2000ms)")
        caminho_perfil = r"C:\ChromeDevSession"
        contexto = p.chromium.launch_persistent_context(
            user_data_dir=caminho_perfil, channel="chrome", headless=False
        )
        pagina = contexto.pages[0]

        if "gtowizard" not in pagina.url:
            pagina.goto("https://app.gtowizard.com/solutions")

        limpar_dados()
        input("\n1. Deixe a tela visível.\n2. Aperte ENTER para começar...\n")

        # --- FASE 1: ABERTURAS (RFI) ---
        print("\n--- FASE 1: ABERTURAS (RFI) ---")
        for pos in ["UTG", "HJ", "CO", "BTN", "SB", "BB"]:
            resetar_arvore(pagina)
            if pos == "BB":
                print("▶️ Cenário Especial: BB RFI (SB Call)")
                if clicar_posicao(pagina, "SB"):
                    pagina.wait_for_timeout(2000)  # Alterado para 2000ms
                    if clicar_acao(pagina, "Call", "SB"):
                        pagina.wait_for_timeout(2000)  # Alterado para 2000ms
                        if clicar_posicao(pagina, "BB"):
                            salvar_dados(pagina, "RFI", "BB")
            else:
                if clicar_posicao(pagina, pos):
                    salvar_dados(pagina, "RFI", pos)

        # --- FASE 2: DEFESA VS UTG RAISE ---
        print("\n--- FASE 2: DEFESA VS UTG RAISE ---")
        for pos in ["HJ", "CO", "BTN", "SB", "BB"]:
            resetar_arvore(pagina)
            clicar_posicao(pagina, "UTG")
            pagina.wait_for_timeout(2000)  # Alterado para 2000ms
            if clicar_acao(pagina, "Raise"):
                pagina.wait_for_timeout(2000)  # Alterado para 2000ms
                if clicar_posicao(pagina, pos):
                    salvar_dados(pagina, "VS_UTG_RAISE", pos)

        # --- FASE 3: DEFESA VS HJ RAISE ---
        print("\n--- FASE 3: DEFESA VS HJ RAISE ---")
        for pos in ["CO", "BTN", "SB", "BB"]:
            resetar_arvore(pagina)
            clicar_posicao(pagina, "HJ")
            pagina.wait_for_timeout(2000)  # Alterado para 2000ms
            if clicar_acao(pagina, "Raise", "HJ"):
                pagina.wait_for_timeout(2000)  # Alterado para 2000ms
                if clicar_posicao(pagina, pos):
                    salvar_dados(pagina, "VS_HJ_RAISE", pos)

        # --- FASE 4: DEFESA VS CO RAISE ---
        print("\n--- FASE 4: DEFESA VS CO RAISE ---")
        for pos in ["BTN", "SB", "BB"]:
            resetar_arvore(pagina)
            clicar_posicao(pagina, "CO")
            pagina.wait_for_timeout(2000)  # Alterado para 2000ms
            if clicar_acao(pagina, "Raise", "CO"):
                pagina.wait_for_timeout(2000)  # Alterado para 2000ms
                if clicar_posicao(pagina, pos):
                    salvar_dados(pagina, "VS_CO_RAISE", pos)

        # --- FASE 5: DEFESA VS BTN RAISE ---
        print("\n--- FASE 5: DEFESA VS BTN RAISE ---")
        for pos in ["SB", "BB"]:
            resetar_arvore(pagina)
            clicar_posicao(pagina, "BTN")
            pagina.wait_for_timeout(2000)  # Alterado para 2000ms
            if clicar_acao(pagina, "Raise", "BTN"):
                pagina.wait_for_timeout(2000)  # Alterado para 2000ms
                if clicar_posicao(pagina, pos):
                    salvar_dados(pagina, "VS_BTN_RAISE", pos)

        # --- FASE 6: DEFESA VS SB RAISE ---
        print("\n--- FASE 6: DEFESA VS SB RAISE ---")
        resetar_arvore(pagina)
        clicar_posicao(pagina, "SB")
        pagina.wait_for_timeout(2000)  # Alterado para 2000ms
        if clicar_acao(pagina, "Raise", "SB"):
            pagina.wait_for_timeout(2000)  # Alterado para 2000ms
            if clicar_posicao(pagina, "BB"):
                salvar_dados(pagina, "VS_SB_RAISE", "BB")

        print("\n🏁 EXTRAÇÃO FINALIZADA! Pode rodar o Processador.")
        contexto.close()

if __name__ == "__main__":
    extrair_arvore()
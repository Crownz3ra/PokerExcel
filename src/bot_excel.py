import os
import json
import shutil
import time
from playwright.sync_api import sync_playwright


def limpar_dados():
    base_path = os.path.join("data", "processed")
    if os.path.exists(base_path):
        shutil.rmtree(base_path)
        print("🗑️ Pasta data/processed apagada com sucesso.")
    os.makedirs(base_path, exist_ok=True)


def salvar_dados(pagina, pasta_cenario, posicao):
    print(f"🔎 Extração Cirúrgica: {pasta_cenario} -> {posicao}")
    pagina.wait_for_timeout(6000)

    dados = pagina.evaluate(
        """() => {
        const resultados = {};
        document.querySelectorAll('[id^="0_"][class*="rtc"]').forEach(el => {
            const mao = el.id.replace(/^\\d+_/, '');
            const style = el.getAttribute('style') || '';

            const gradientes = [];
            const gradRegex = /linear-gradient\\((?:[^()]*|\\([^()]*\\))*\\)/g;
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
        pagina.wait_for_timeout(2000)
    except:
        print("⚠️ Botão de reset não encontrado, navegando para a página...")
        pagina.goto("https://app.gtowizard.com/solutions")
        pagina.wait_for_timeout(2000)


def navegar(pagina, acoes):
    for pos, acao in acoes:
        clicar_posicao(pagina, pos)
        pagina.wait_for_timeout(800)
        clicar_acao(pagina, acao, pos)
        pagina.wait_for_timeout(800)


def extrair_arvore():
    with sync_playwright() as p:
        print("🚀 Bot V24")
        caminho_perfil = r"C:\ChromeDevSession"
        contexto = p.chromium.launch_persistent_context(
            user_data_dir=caminho_perfil, channel="chrome", headless=False
        )
        pagina = contexto.pages[0]

        if "gtowizard" not in pagina.url:
            pagina.goto("https://app.gtowizard.com/solutions")

        limpar_dados()
        print("\n⏳ Iniciando em 6 segundos... Deixe a tela visível.")
        time.sleep(6)

        ordem = ["UTG", "HJ", "CO", "BTN", "SB", "BB"]

        # --- FASE 1: RFI ---
        print("\n--- FASE 1: RFI ---")
        for pos in ordem:
            resetar_arvore(pagina)
            if pos == "BB":
                print("▶️ Cenário Especial: BB RFI (SB Call)")
                if clicar_posicao(pagina, "SB"):
                    pagina.wait_for_timeout(2000)
                    if clicar_acao(pagina, "Call", "SB"):
                        pagina.wait_for_timeout(2000)
                        if clicar_posicao(pagina, "BB"):
                            salvar_dados(pagina, "RFI", "BB")
            else:
                if clicar_posicao(pagina, pos):
                    salvar_dados(pagina, "RFI", pos)

        # --- FASE 2: UTG_R ---
        print("\n--- FASE 2: UTG_R ---")
        for pos in ["HJ", "CO", "BTN", "SB", "BB"]:
            resetar_arvore(pagina)
            clicar_posicao(pagina, "UTG")
            pagina.wait_for_timeout(2000)
            if clicar_acao(pagina, "Raise"):
                pagina.wait_for_timeout(2000)
                if clicar_posicao(pagina, pos):
                    salvar_dados(pagina, "UTG_R", pos)

        # --- FASE 3: HJ_R ---
        print("\n--- FASE 3: HJ_R ---")
        for pos in ["CO", "BTN", "SB", "BB"]:
            resetar_arvore(pagina)
            clicar_posicao(pagina, "HJ")
            pagina.wait_for_timeout(2000)
            if clicar_acao(pagina, "Raise", "HJ"):
                pagina.wait_for_timeout(2000)
                if clicar_posicao(pagina, pos):
                    salvar_dados(pagina, "HJ_R", pos)

        # --- FASE 4: CO_R ---
        print("\n--- FASE 4: CO_R ---")
        for pos in ["BTN", "SB", "BB"]:
            resetar_arvore(pagina)
            clicar_posicao(pagina, "CO")
            pagina.wait_for_timeout(2000)
            if clicar_acao(pagina, "Raise", "CO"):
                pagina.wait_for_timeout(2000)
                if clicar_posicao(pagina, pos):
                    salvar_dados(pagina, "CO_R", pos)

        # --- FASE 5: BTN_R ---
        print("\n--- FASE 5: BTN_R ---")
        for pos in ["SB", "BB"]:
            resetar_arvore(pagina)
            clicar_posicao(pagina, "BTN")
            pagina.wait_for_timeout(2000)
            if clicar_acao(pagina, "Raise", "BTN"):
                pagina.wait_for_timeout(2000)
                if clicar_posicao(pagina, pos):
                    salvar_dados(pagina, "BTN_R", pos)

        # --- FASE 6: SB_R ---
        print("\n--- FASE 6: SB_R ---")
        resetar_arvore(pagina)
        clicar_posicao(pagina, "SB")
        pagina.wait_for_timeout(2000)
        if clicar_acao(pagina, "Raise", "SB"):
            pagina.wait_for_timeout(2000)
            if clicar_posicao(pagina, "BB"):
                salvar_dados(pagina, "SB_R", "BB")

        # --- FASES 7+: RAISE + N CALLERS ---
        print("\n--- FASES 7+: RAISE + N CALLERS ---")

        def gerar_cenarios():
            cenarios = []
            for i, raiser in enumerate(ordem):
                posicoes_depois = ordem[i + 1 :]
                if not posicoes_depois:
                    continue
                possiveis_callers = posicoes_depois[:-1]
                for n_callers in range(1, len(possiveis_callers) + 1):
                    for inicio in range(len(possiveis_callers) - n_callers + 1):
                        callers = possiveis_callers[inicio : inicio + n_callers]
                        folds_antes = posicoes_depois[:inicio]
                        idx_ultimo_caller = ordem.index(callers[-1])
                        posicoes_apos = ordem[idx_ultimo_caller + 1 :]
                        if not posicoes_apos:
                            continue
                        partes = [f"{raiser}_R"]
                        for c in callers:
                            partes.append(f"{c}_C")
                        pasta = "_".join(partes)
                        cenarios.append(
                            (raiser, folds_antes, callers, posicoes_apos, pasta)
                        )
            return cenarios

        cenarios = gerar_cenarios()
        total = sum(len(c[3]) for c in cenarios)
        print(f"  Total de extrações: {total}")

        for raiser, folds_antes_caller, callers, defensores, pasta in cenarios:
            print(f"\n  {pasta}")
            for defensor in defensores:
                resetar_arvore(pagina)

                for p in ordem:
                    if p == raiser:
                        break
                    clicar_posicao(pagina, p)
                    pagina.wait_for_timeout(800)
                    clicar_acao(pagina, "Fold", p)
                    pagina.wait_for_timeout(800)

                clicar_posicao(pagina, raiser)
                pagina.wait_for_timeout(800)
                clicar_acao(pagina, "Raise", raiser)
                pagina.wait_for_timeout(800)

                for p in folds_antes_caller:
                    clicar_posicao(pagina, p)
                    pagina.wait_for_timeout(800)
                    clicar_acao(pagina, "Fold", p)
                    pagina.wait_for_timeout(800)

                for idx_c, caller in enumerate(callers):
                    if idx_c > 0:
                        caller_anterior = callers[idx_c - 1]
                        idx_ant = ordem.index(caller_anterior)
                        idx_cur = ordem.index(caller)
                        for p in ordem[idx_ant + 1 : idx_cur]:
                            clicar_posicao(pagina, p)
                            pagina.wait_for_timeout(800)
                            clicar_acao(pagina, "Fold", p)
                            pagina.wait_for_timeout(800)
                    clicar_posicao(pagina, caller)
                    pagina.wait_for_timeout(800)
                    clicar_acao(pagina, "Call", caller)
                    pagina.wait_for_timeout(800)

                idx_ultimo_caller = ordem.index(callers[-1])
                idx_defensor = ordem.index(defensor)
                for p in ordem[idx_ultimo_caller + 1 : idx_defensor]:
                    clicar_posicao(pagina, p)
                    pagina.wait_for_timeout(800)
                    clicar_acao(pagina, "Fold", p)
                    pagina.wait_for_timeout(800)

                if clicar_posicao(pagina, defensor):
                    salvar_dados(pagina, pasta, defensor)

        # --- FASE 8: 3-BETS ISOLADAS ---
        print("\n--- FASE 8: 3-BETS ISOLADAS ---")

        cenarios_3bet = [
            ("SB", "BB", "SB_R_BB_3B"),
            ("BTN", "SB", "BTN_R_SB_3B"),
            ("BTN", "BB", "BTN_R_BB_3B"),
            ("CO", "BTN", "CO_R_BTN_3B"),
            ("CO", "SB", "CO_R_SB_3B"),
            ("CO", "BB", "CO_R_BB_3B"),
            ("HJ", "SB", "HJ_R_SB_3B"),
            ("UTG", "BB", "UTG_R_BB_3B"),
            ("HJ", "BTN", "HJ_R_BTN_3B"),
            ("UTG", "BTN", "UTG_R_BTN_3B"),
        ]

        for raiser, tresbetor, pasta in cenarios_3bet:
            print(f"\n  {pasta}")
            resetar_arvore(pagina)

            # Fold antes do raiser
            for p in ordem:
                if p == raiser:
                    break
                clicar_posicao(pagina, p)
                pagina.wait_for_timeout(800)
                clicar_acao(pagina, "Fold", p)
                pagina.wait_for_timeout(800)

            # Raiser dá Raise
            clicar_posicao(pagina, raiser)
            pagina.wait_for_timeout(800)
            clicar_acao(pagina, "Raise", raiser)
            pagina.wait_for_timeout(800)

            # Fold entre raiser e 3-bettor
            idx_raiser = ordem.index(raiser)
            idx_3bet = ordem.index(tresbetor)
            for p in ordem[idx_raiser + 1 : idx_3bet]:
                clicar_posicao(pagina, p)
                pagina.wait_for_timeout(800)
                clicar_acao(pagina, "Fold", p)
                pagina.wait_for_timeout(800)

            # 3-bettor dá Raise
            clicar_posicao(pagina, tresbetor)
            pagina.wait_for_timeout(800)
            clicar_acao(pagina, "Raise", tresbetor)
            pagina.wait_for_timeout(800)

            # Fold em todos após o 3-bettor até o fim
            for p in ordem[idx_3bet + 1 :]:
                clicar_posicao(pagina, p)
                pagina.wait_for_timeout(800)
                clicar_acao(pagina, "Fold", p)
                pagina.wait_for_timeout(800)

            # Raiser age após a 3-bet
            salvar_dados(pagina, pasta, raiser)

        print("\n🏁 EXTRAÇÃO FINALIZADA! Pode rodar o Processador.")
        contexto.close()


if __name__ == "__main__":
    extrair_arvore()

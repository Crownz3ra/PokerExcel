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


def clicar_btn_texto(pagina, texto):
    """Clica em um botão pelo texto exato."""
    pagina.evaluate(
        f"""() => {{
        const btns = Array.from(document.querySelectorAll('button, [role="button"]'));
        const btn = btns.find(b => b.innerText.trim() === '{texto}');
        if (btn) btn.click();
    }}"""
    )
    pagina.wait_for_timeout(400)


def configurar_gto(pagina):
    print(
        "⚙️ Configurando GTO Wizard (Cash / 6max / Classic / 100bb / NL50 / General 2x)..."
    )

    # Abre o modal de configuração
    try:
        pagina.locator('[data-tst="shrtbtn_change_solution"]').click(timeout=3000)
    except:
        pagina.evaluate(
            """() => {
            const btns = Array.from(document.querySelectorAll('button'));
            const btn = btns.find(b => b.innerText.trim() === 'Change');
            if (btn) btn.click();
        }"""
        )
    pagina.wait_for_timeout(2000)

    # Seleciona cada opção
    clicar_btn_texto(pagina, "Cash")
    clicar_btn_texto(pagina, "Classic")
    clicar_btn_texto(pagina, "6max")
    clicar_btn_texto(pagina, "Preflop only")
    clicar_btn_texto(pagina, "100")
    clicar_btn_texto(pagina, "NL50")
    clicar_btn_texto(pagina, "General")
    clicar_btn_texto(pagina, "2x")
    pagina.wait_for_timeout(500)

    # Clica na linha General / NL50 / 2x da tabela de resultados
    pagina.evaluate(
        """() => {
        const rows = Array.from(document.querySelectorAll('tr, [role="row"]'));
        for (const row of rows) {
            const txt = row.innerText || '';
            if (txt.includes('General') &&
                txt.includes('NL50') &&
                txt.includes('2x') &&
                !txt.includes('2.25x') &&
                !txt.includes('2.5x') &&
                !txt.includes('3x')) {
                row.click();
                return;
            }
        }
    }"""
    )
    pagina.wait_for_timeout(2000)
    print("✅ Configuração aplicada!")


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


def navegar_ate_squeeze(pagina, raiser, callers, squeezer, ordem):
    """Navega até o estado pós-squeeze."""
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

    ultimo = raiser
    for caller in callers:
        idx_ultimo = ordem.index(ultimo)
        idx_caller = ordem.index(caller)
        for p in ordem[idx_ultimo + 1 : idx_caller]:
            clicar_posicao(pagina, p)
            pagina.wait_for_timeout(800)
            clicar_acao(pagina, "Fold", p)
            pagina.wait_for_timeout(800)
        clicar_posicao(pagina, caller)
        pagina.wait_for_timeout(800)
        clicar_acao(pagina, "Call", caller)
        pagina.wait_for_timeout(800)
        ultimo = caller

    idx_ultimo = ordem.index(ultimo)
    idx_sqz = ordem.index(squeezer)
    for p in ordem[idx_ultimo + 1 : idx_sqz]:
        clicar_posicao(pagina, p)
        pagina.wait_for_timeout(800)
        clicar_acao(pagina, "Fold", p)
        pagina.wait_for_timeout(800)

    clicar_posicao(pagina, squeezer)
    pagina.wait_for_timeout(800)
    clicar_acao(pagina, "Raise", squeezer)
    pagina.wait_for_timeout(800)

    for p in ordem[idx_sqz + 1 :]:
        clicar_posicao(pagina, p)
        pagina.wait_for_timeout(800)
        clicar_acao(pagina, "Fold", p)
        pagina.wait_for_timeout(800)


def extrair_arvore():
    with sync_playwright() as p:
        print("🚀 Bot V26")
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

        # Garante configuração correta antes de extrair
        configurar_gto(pagina)

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

            idx_raiser = ordem.index(raiser)
            idx_3bet = ordem.index(tresbetor)
            for p in ordem[idx_raiser + 1 : idx_3bet]:
                clicar_posicao(pagina, p)
                pagina.wait_for_timeout(800)
                clicar_acao(pagina, "Fold", p)
                pagina.wait_for_timeout(800)

            clicar_posicao(pagina, tresbetor)
            pagina.wait_for_timeout(800)
            clicar_acao(pagina, "Raise", tresbetor)
            pagina.wait_for_timeout(800)

            for p in ordem[idx_3bet + 1 :]:
                clicar_posicao(pagina, p)
                pagina.wait_for_timeout(800)
                clicar_acao(pagina, "Fold", p)
                pagina.wait_for_timeout(800)

            salvar_dados(pagina, pasta, raiser)

        # --- FASE 9: SQUEEZE ---
        print("\n--- FASE 9: SQUEEZE ---")

        cenarios_squeeze = [
            ("CO", ["BTN"], "BB", "CO_R_BTN_C_BB_SQZ"),
            ("HJ", ["CO"], "BTN", "HJ_R_CO_C_BTN_SQZ"),
            ("UTG", ["BTN"], "BB", "UTG_R_BTN_C_BB_SQZ"),
            ("CO", ["BTN"], "SB", "CO_R_BTN_C_SB_SQZ"),
        ]

        for raiser, callers, squeezer, pasta in cenarios_squeeze:
            print(f"\n  {pasta}")

            # 1. Extrai tabela do squeezer
            resetar_arvore(pagina)
            navegar_ate_squeeze(pagina, raiser, callers, squeezer, ordem)
            salvar_dados(pagina, pasta, squeezer)

            # 2. Extrai tabela do raiser respondendo ao squeeze
            resetar_arvore(pagina)
            navegar_ate_squeeze(pagina, raiser, callers, squeezer, ordem)
            salvar_dados(pagina, pasta, raiser)

            # 3. Extrai tabela de cada caller respondendo ao squeeze
            for caller in callers:
                resetar_arvore(pagina)
                navegar_ate_squeeze(pagina, raiser, callers, squeezer, ordem)
                clicar_posicao(pagina, raiser)
                pagina.wait_for_timeout(800)
                clicar_acao(pagina, "Call", raiser)
                pagina.wait_for_timeout(800)
                salvar_dados(pagina, pasta, caller)

        print("\n🏁 EXTRAÇÃO FINALIZADA! Pode rodar o Processador.")
        contexto.close()


if __name__ == "__main__":
    extrair_arvore()

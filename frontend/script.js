"use strict";

const POSITIONS = ["UTG", "HJ", "CO", "BTN", "SB", "BB"];
const STACKS = { UTG: 100, HJ: 100, CO: 100, BTN: 100, SB: 99.5, BB: 99 };
const RANKS = ["A", "K", "Q", "J", "T", "9", "8", "7", "6", "5", "4", "3", "2"];

const RED = "#ef4444";
const GREEN = "#22c55e";
const BLUE = "#3b82f6";

// state[i] = null | "Fold" | "Raise" | "Call" | "3Bet"
let state = Array(6).fill(null);
let activeIdx = 0;

/* ── helpers ── */

function countRaises() {
  return state.filter((s) => s === "Raise").length;
}

function getFirstRaiserIdx() {
  return state.indexOf("Raise");
}

function get3BetIdx() {
  return state.indexOf("3Bet");
}

function getFolder(upTo) {
  // upTo = exclusive index (default: all 6)
  const limit = upTo !== undefined ? upTo : 6;
  let pasta = "";
  for (let i = 0; i < limit; i++) {
    if (state[i] === "Raise") {
      pasta += (pasta ? "_" : "") + POSITIONS[i] + "_R";
    } else if (state[i] === "Call") {
      pasta += (pasta ? "_" : "") + POSITIONS[i] + "_C";
    } else if (state[i] === "3Bet") {
      pasta += (pasta ? "_" : "") + POSITIONS[i] + "_3B";
    }
  }
  return pasta || "RFI";
}

function getActions() {
  const raises = countRaises();
  const has3Bet = get3BetIdx() >= 0;
  const pos = POSITIONS[activeIdx];

  if (has3Bet) return ["Fold", "Call"];
  if (raises === 1) return ["Fold", "Call", "Raise 7", "Allin 100"];

  if (pos === "BB") return ["Check", "Raise 2", "Allin 100"];
  if (pos === "SB") return ["Fold", "Call", "Raise 3", "Allin 100"];
  return ["Fold", "Raise 2", "Allin 100"];
}

function baseOf(label) {
  if (label === "Check") return "Check";
  if (label.startsWith("Raise")) return "Raise";
  if (label.startsWith("Call")) return "Call";
  if (label.startsWith("Allin")) return "Raise";
  return label;
}

function scenarioLabel() {
  const folder = getFolder();
  return folder === "RFI" ? "RFI" : folder;
}

/* ── interactions ── */

function resetGame() {
  state = Array(6).fill(null);
  activeIdx = 0;
  render();
}

function selectAction(label) {
  let base = baseOf(label);
  const raises = countRaises();
  const has3Bet = get3BetIdx() >= 0;

  if (base === "Raise" && raises >= 1 && !has3Bet) {
    base = "3Bet";
  }

  state[activeIdx] = base;

  // Limpa posições futuras
  for (let i = activeIdx + 1; i < 6; i++) state[i] = null;

  // Preenche folds implícitos para posições anteriores
  for (let i = 0; i < activeIdx; i++) {
    if (state[i] === null) state[i] = "Fold";
  }

  const tresBetIdx = get3BetIdx();

  if (tresBetIdx >= 0) {
    // Após 3-bet: próxima posição após o 3-bettor que ainda não agiu
    let proximaAtiva = -1;
    for (let i = tresBetIdx + 1; i < 6; i++) {
      if (state[i] === null) {
        proximaAtiva = i;
        break;
      }
    }

    if (proximaAtiva >= 0) {
      activeIdx = proximaAtiva;
    } else {
      // Todos após o 3-bettor falaram — volta para o raiser
      const raiserIdx = getFirstRaiserIdx();
      const raiserJaRespondeu = state[raiserIdx] !== "Raise";
      if (!raiserJaRespondeu && raiserIdx >= 0) {
        activeIdx = raiserIdx;
      } else {
        activeIdx = Math.min(activeIdx + 1, 5);
      }
    }
  } else {
    activeIdx = Math.min(activeIdx + 1, 5);
  }

  render();
}

function selectPos(idx) {
  // Ao clicar num card, apenas muda o activeIdx
  // Folds implícitos só são adicionados quando uma ação é tomada
  activeIdx = idx;
  render();
}

/* ── render nav ── */

function renderNav() {
  const rail = document.getElementById("pos-rail");
  const drawer = document.getElementById("action-drawer");
  const label = document.getElementById("scenario-label");

  rail.innerHTML = "";
  drawer.innerHTML = "";
  label.textContent = scenarioLabel();

  POSITIONS.forEach((pos, idx) => {
    const isActive = idx === activeIdx;
    const isFolded = state[idx] === "Fold";

    const card = document.createElement("div");
    card.className =
      "pos-card" + (isActive ? " active" : "") + (isFolded ? " folded" : "");
    card.onclick = () => selectPos(idx);

    card.innerHTML = `
      <div class="pos-card-header">
        <span class="pos-name">${pos}</span>
        <span class="pos-stack">${STACKS[pos]}</span>
      </div>
    `;

    if (!isActive && state[idx]) {
      const badge = document.createElement("div");
      badge.className = "pos-badge";
      badge.textContent = state[idx];
      card.appendChild(badge);
    }

    rail.appendChild(card);

    if (isActive) {
      requestAnimationFrame(() =>
        card.scrollIntoView({
          behavior: "smooth",
          block: "nearest",
          inline: "center",
        }),
      );
    }
  });

  // Action buttons
  getActions().forEach((act) => {
    const base = baseOf(act);
    const cur = state[activeIdx];
    const isSelected =
      (base === "Raise" && (cur === "Raise" || cur === "3Bet")) ||
      (base !== "Raise" && cur === base);

    const btn = document.createElement("button");
    btn.className = "action-btn";
    btn.textContent = act;

    if (isSelected) {
      btn.classList.add(
        base === "Raise"
          ? "selected-raise"
          : base === "Call"
            ? "selected-call"
            : "selected-fold",
      );
    }

    btn.onclick = () => selectAction(act);
    drawer.appendChild(btn);
  });

  // Reset button
  const resetBtn = document.createElement("button");
  resetBtn.className = "action-btn";
  resetBtn.textContent = "↺";
  resetBtn.style.marginLeft = "auto";
  resetBtn.onclick = resetGame;
  drawer.appendChild(resetBtn);
}

/* ── render matrix ── */

async function renderMatrix() {
  const pos = POSITIONS[activeIdx];
  const folder = getFolder();
  const url = `/api/strategy/${folder}/${pos}`;
  const matrix = document.getElementById("poker-matrix");

  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error(res.status);
    drawMatrix(await res.json(), matrix);
  } catch {
    matrix.innerHTML = `
      <div class="matrix-error">
        ⚠️ Sem dados<br>${folder} / ${pos}
      </div>`;
  }
}

function drawMatrix(data, matrix) {
  matrix.innerHTML = "";
  let delay = 0;

  const corner = document.createElement("div");
  corner.className = "hdr";
  matrix.appendChild(corner);

  RANKS.forEach((r) => {
    const h = document.createElement("div");
    h.className = "hdr";
    h.textContent = r;
    matrix.appendChild(h);
  });

  RANKS.forEach((row) => {
    const rh = document.createElement("div");
    rh.className = "hdr";
    rh.textContent = row;
    matrix.appendChild(rh);

    RANKS.forEach((col) => {
      const ri = RANKS.indexOf(row);
      const ci = RANKS.indexOf(col);
      const hand =
        ri < ci ? `${row}${col}s` : ri > ci ? `${col}${row}o` : `${row}${col}`;

      const cell = document.createElement("div");
      cell.className = "cell";
      cell.style.animationDelay = `${delay * 2}ms`;
      delay++;

      const d = data[hand] || { Raise: 0, Call: 0, Fold: 100 };
      const r = +d.Raise;
      const rc = r + +d.Call;

      cell.style.background =
        r === 100
          ? RED
          : rc === 0
            ? BLUE
            : `linear-gradient(to right, ${RED} 0% ${r}%, ${GREEN} ${r}% ${rc}%, ${BLUE} ${rc}% 100%)`;

      const lbl = document.createElement("span");
      lbl.className = "cell-label";
      lbl.textContent = hand;
      cell.appendChild(lbl);

      matrix.appendChild(cell);
    });
  });
}

/* ── main ── */

function render() {
  renderNav();
  renderMatrix();
}

document.addEventListener("DOMContentLoaded", render);

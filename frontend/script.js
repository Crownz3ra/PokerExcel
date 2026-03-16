"use strict";

const POSITIONS = ["UTG", "HJ", "CO", "BTN", "SB", "BB"];
const STACKS = { UTG: 100, HJ: 100, CO: 100, BTN: 100, SB: 99.5, BB: 99 };
const RANKS = ["A", "K", "Q", "J", "T", "9", "8", "7", "6", "5", "4", "3", "2"];

const RED = "#ef4444";
const GREEN = "#22c55e";
const BLUE = "#3b82f6";

// state[i] = null | "Fold" | "Raise" | "Call" | "3Bet" | "SQZ"
let state = Array(6).fill(null);
let activeIdx = 0;

// roundTwo: respostas ao squeeze (raiser + callers agem novamente)
let roundTwo = Array(6).fill(null);
let inRoundTwo = false;

/* ── helpers ── */

function countRaises() {
  return state.filter((s) => s === "Raise").length;
}

function getFirstRaiserIdx() {
  return state.indexOf("Raise");
}

function getSQZIdx() {
  const i3 = state.indexOf("3Bet");
  const sq = state.indexOf("SQZ");
  if (i3 >= 0 && sq >= 0) return Math.min(i3, sq);
  if (i3 >= 0) return i3;
  return sq;
}

function hasCaller() {
  return state.some((s) => s === "Call");
}

function getFolder() {
  let pasta = "";
  for (let i = 0; i < 6; i++) {
    if (state[i] === "Raise") pasta += (pasta ? "_" : "") + POSITIONS[i] + "_R";
    else if (state[i] === "Call")
      pasta += (pasta ? "_" : "") + POSITIONS[i] + "_C";
    else if (state[i] === "3Bet")
      pasta += (pasta ? "_" : "") + POSITIONS[i] + "_3B";
    else if (state[i] === "SQZ")
      pasta += (pasta ? "_" : "") + POSITIONS[i] + "_SQZ";
  }
  return pasta || "RFI";
}

// Ordem em que raiser e callers respondem ao squeeze
function getRoundTwoOrder() {
  const participants = [];
  for (let i = 0; i < 6; i++) {
    if (state[i] === "Raise" || state[i] === "Call") participants.push(i);
  }
  return participants.sort((a, b) => a - b);
}

function getActions() {
  const raises = countRaises();
  const sqzIdx = getSQZIdx();
  const has3BetOrSQZ = sqzIdx >= 0;
  const pos = POSITIONS[activeIdx];

  if (inRoundTwo) return ["Fold", "Call"];
  if (has3BetOrSQZ) return ["Fold", "Call"];
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
  if (folder === "RFI") return "RFI";

  return folder
    .replace(/_R(?=_|$)/g, " Raise")
    .replace(/_C(?=_|$)/g, " Call")
    .replace(/_3B(?=_|$)/g, " 3Bet")
    .replace(/_SQZ(?=_|$)/g, " Squeeze")
    .replace(/_/g, " • ")
    .trim();
}

/* ── interactions ── */

function resetGame() {
  state = Array(6).fill(null);
  roundTwo = Array(6).fill(null);
  inRoundTwo = false;
  activeIdx = 0;
  render();
}

function selectAction(label) {
  let base = baseOf(label);

  // ── Round dois (resposta ao squeeze) ──
  if (inRoundTwo) {
    roundTwo[activeIdx] = base;
    const order = getRoundTwoOrder();
    const next = order.find((i) => roundTwo[i] === null);
    if (next !== undefined) {
      activeIdx = next;
    }
    render();
    return;
  }

  // ── Round um ──
  const raises = countRaises();
  const has3BetOrSQZ = getSQZIdx() >= 0;
  const caller = hasCaller();

  // Segundo raise = 3Bet (sem caller) ou SQZ (com caller)
  if (base === "Raise" && raises >= 1 && !has3BetOrSQZ) {
    base = caller ? "SQZ" : "3Bet";
  }

  state[activeIdx] = base;

  // Limpa posições futuras e preenche folds implícitos
  for (let i = activeIdx + 1; i < 6; i++) state[i] = null;
  for (let i = 0; i < activeIdx; i++) if (state[i] === null) state[i] = "Fold";

  const sqzIdx = getSQZIdx();

  if (sqzIdx >= 0) {
    // Procura próxima posição após o agressor que ainda não agiu
    let proximaAtiva = -1;
    for (let i = sqzIdx + 1; i < 6; i++) {
      if (state[i] === null) {
        proximaAtiva = i;
        break;
      }
    }

    if (proximaAtiva >= 0) {
      activeIdx = proximaAtiva;
    } else if (base === "SQZ") {
      // Squeeze completo — inicia round dois
      inRoundTwo = true;
      roundTwo = Array(6).fill(null);
      const order = getRoundTwoOrder();
      activeIdx = order.length > 0 ? order[0] : activeIdx;
    } else {
      // 3-bet isolada — volta para o raiser
      const raiserIdx = getFirstRaiserIdx();
      activeIdx =
        raiserIdx >= 0 && state[raiserIdx] === "Raise"
          ? raiserIdx
          : Math.min(activeIdx + 1, 5);
    }
  } else {
    activeIdx = Math.min(activeIdx + 1, 5);
  }

  render();
}

function selectPos(idx) {
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

    // Badge ação round 1
    if (!isActive && state[idx]) {
      const badge = document.createElement("div");
      badge.className = "pos-badge";
      badge.textContent = state[idx];
      card.appendChild(badge);
    }

    // Badge ação round 2 (resposta ao squeeze)
    if (!isActive && inRoundTwo && roundTwo[idx]) {
      const badge2 = document.createElement("div");
      badge2.className = "pos-badge";
      badge2.textContent = roundTwo[idx];
      card.appendChild(badge2);
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
    const cur = inRoundTwo ? roundTwo[activeIdx] : state[activeIdx];
    const isSelected =
      (base === "Raise" &&
        (cur === "Raise" || cur === "3Bet" || cur === "SQZ")) ||
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
  resetBtn.className = "action-btn reset-btn";
  resetBtn.textContent = "↺ Reset";
  resetBtn.onclick = resetGame;
  drawer.appendChild(resetBtn);
}

/* ── render matrix ── */

async function renderMatrix() {
  const pos = POSITIONS[activeIdx];
  const folder = getFolder();
  const url = `/api/strategy/${folder}/${pos}`;
  const matrix = document.getElementById("poker-matrix");

  // Indicador de carregamento
  matrix.innerHTML = `
    <div class="matrix-loading">
      <div class="spinner"></div>
    </div>`;

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

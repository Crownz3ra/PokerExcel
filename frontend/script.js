const ranks = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2'];
const positions = ['UTG', 'HJ', 'CO', 'BTN', 'SB', 'BB'];

let activePosIndex = 0; 
let treeHistory = { 'UTG': null }; 

function renderTree() {
    const treeContainer = document.getElementById('gto-action-tree');
    treeContainer.innerHTML = '';

    for (let i = 0; i <= activePosIndex; i++) {
        const pos = positions[i];
        const isActive = (i === activePosIndex);
        const actionTaken = treeHistory[pos];

        const block = document.createElement('div');
        block.className = `pos-block ${isActive ? 'active' : ''}`;

        const header = document.createElement('div');
        header.className = 'pos-header';
        header.innerHTML = `<span>${pos}</span> <span>100</span>`;
        block.appendChild(header);

        if (!isActive) {
            const actDiv = document.createElement('div');
            actDiv.className = 'action-item selected';
            actDiv.innerText = actionTaken;
            actDiv.onclick = () => {
                activePosIndex = i;
                treeHistory[pos] = null;
                renderTree();
            };
            block.appendChild(actDiv);
        } else {
            // Se for o BB, a opção padrão preflop muda
            const acoes = pos === 'BB' ? ['Fold', 'Raise 2', 'Call'] : ['Fold', 'Raise 2', 'Allin 100'];
            acoes.forEach(act => {
                const actDiv = document.createElement('div');
                actDiv.className = 'action-item';
                actDiv.innerText = act;
                actDiv.onclick = () => {
                    if (i < positions.length - 1) {
                        treeHistory[pos] = act;
                        activePosIndex = i + 1;
                        treeHistory[positions[activePosIndex]] = null;
                        renderTree();
                    }
                };
                block.appendChild(actDiv);
            });
        }
        treeContainer.appendChild(block);
    }
    loadData();
}

async function loadData() {
    const currentPos = positions[activePosIndex];
    let folder = 'RFI'; 
    
    // Se o UTG deu raise, carrega a pasta correta
    if (activePosIndex > 0 && treeHistory['UTG'] === 'Raise 2') {
        folder = 'VS_UTG_RAISE'; 
    }

    const url = `../data/processed/${folder}/${currentPos}/tabela_final.json`;

    try {
        const response = await fetch(url + "?t=" + new Date().getTime());
        if (!response.ok) throw new Error("Faltam dados");
        const data = await response.json();
        drawMatrix(data);
    } catch (err) {
        document.getElementById('poker-matrix').innerHTML = `
            <div style="grid-column: span 14; padding: 40px; text-align: center; color:#ff6b6b">
                ⚠️ Sem dados para <b>${currentPos}</b> em <b>${folder}</b>.<br>
            </div>`;
    }
}

function drawMatrix(data) {
    const matrix = document.getElementById('poker-matrix');
    matrix.innerHTML = ""; 

    for (let i = 0; i < 14; i++) {
        for (let j = 0; j < 14; j++) {
            const cell = document.createElement('div');
            
            if (i === 0 && j === 0) { cell.className = 'cell header-cell'; } 
            else if (i === 0) { cell.className = 'cell header-cell'; cell.innerText = ranks[j-1]; } 
            else if (j === 0) { cell.className = 'cell header-cell'; cell.innerText = ranks[i-1]; } 
            else {
                const row = i - 1, col = j - 1;
                const hand = (row === col) ? ranks[row] + ranks[col] : 
                             (row < col) ? ranks[row] + ranks[col] + 's' : ranks[col] + ranks[row] + 'o';

                cell.className = 'cell';
                cell.innerText = hand;

                const stats = data[hand] || { Raise: 0, Call: 0, Fold: 100 };
                cell.style.background = `linear-gradient(to right, 
                    #f03c3c ${stats.Raise}%, 
                    #5ab966 ${stats.Raise}% ${stats.Raise + stats.Call}%, 
                    #3d7cb8 ${stats.Raise + stats.Call}% 100%)`;
            }
            matrix.appendChild(cell);
        }
    }
}

renderTree();
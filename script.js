const baseUrl = 'http://127.0.0.1:5000';

// Mostrar todos os nós disponíveis na rede em um combo box
async function getAllNodes() {

    // Fazer uma requisição ao nó de referência para obter todos os nós
    try {
        const response = await fetch(`${baseUrl}/nodes/all`);
        if (!response.ok) {
            throw new Error(`Erro ao buscar nós: ${response.statusText}`);
        }

        const data = await response.json();
        const nodes = data.nodes;

        // Seleciona o combo box no HTML
        const comboBox = document.getElementById('nodeSelect');

        // Remove as opções existentes
        comboBox.innerHTML = '';

        // Adiciona uma opção padrão
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.text = 'Selecione um nó';
        comboBox.appendChild(defaultOption);

        // Adiciona cada nó como uma nova opção no combo box
        nodes.forEach(node => {
            const option = document.createElement('option');
            option.value = node;
            option.text = node;
            comboBox.appendChild(option);
        });
    } catch (error) {
        console.error('Erro ao popular o combo box:', error);
    }
}

async function mineBlock() {
    const response = await fetch(`${baseUrl}/mine`);
    const data = await response.json();
    document.getElementById('output').innerText = JSON.stringify(data, null, 2);
}

async function createTransaction() {
    const sender = document.getElementById('sender').value;
    const recipient = document.getElementById('recipient').value;
    const amount = document.getElementById('amount').value;

    const response = await fetch(`${baseUrl}/transactions/new`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sender, recipient, amount })
    });

    const data = await response.json();
    document.getElementById('output').innerText = JSON.stringify(data, null, 2);
}

async function getBlockchain() {
    const response = await fetch(`${baseUrl}/chain`);
    const data = await response.json();
    document.getElementById('output').innerText = JSON.stringify(data, null, 2);
}

async function registerNodes() {
    const nodes = document.getElementById('nodes').value.split(',').map(node => node.trim());
    const response = await fetch(`${baseUrl}/nodes/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nodes })
    });

    const data = await response.json();
    document.getElementById('output').innerText = JSON.stringify(data, null, 2);
}

async function resolveConflicts() {
    const response = await fetch(`${baseUrl}/nodes/resolve`);
    const data = await response.json();
    document.getElementById('output').innerText = JSON.stringify(data, null, 2);
}
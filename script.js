const referenceUrl = 'http://127.0.0.1:5000';

// Mostrar todos os nós disponíveis na rede em um combo box usando a lista do nós conhecidos do nó de referência
async function getAllNodes() {

    // Fazer uma requisição ao nó de referência para obter todos os nós
    try {
        const response = await fetch(`${referenceUrl}/nodes/all`);
        if (!response.ok) {
            throw new Error(`Erro ao buscar nós: ${response.statusText}`);
        }

        // Nós obtidos na busca
        const data = await response.json();
        const nodes = data.nodes;

        // Pegando o elemento html do combo box
        const comboBox = document.getElementById('nodeSelect');
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

// Buscar nó selecionado no combo box para fazer operações (como transação e mineração)
function getSelectedNode() {
    const selectedNode = document.getElementById('nodeSelect').value;
    if (!selectedNode) {
        alert('Por favor, selecione um nó.');
        throw new Error('Nenhum nó selecionado.');
    }
    return `http://${selectedNode}`;
}

// Iniciar processo de mineraão para criar um bloco com todas as transações feitas e automaticamente resolver conflitos dos nós
async function mineBlock() {
    try {
        const selectedNode = getSelectedNode();
        const response = await fetch(`${selectedNode}/mine`);
        const data = await response.json();
        document.getElementById('output').innerText = ""
        document.getElementById('output').innerText = "Nó: " + selectedNode + "\n" 
        document.getElementById('output').innerText += JSON.stringify(data, null, 2);
    } catch (error) {
        console.error('Erro ao minerar bloco:', error);
    }    

    resolveConflictsMajority()
}

// Criar uma transação
async function createTransaction() {
    try {
        const selectedNode = getSelectedNode();
        const sender = document.getElementById('sender').value;
        const recipient = document.getElementById('recipient').value;
        const amount = document.getElementById('amount').value;

        const response = await fetch(`${selectedNode}/transactions/new`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sender, recipient, amount })
        });

        const data = await response.json();

        document.getElementById('output').innerText = "Nó: " + selectedNode + "\n"
        document.getElementById('output').innerText += JSON.stringify(data, null, 2);
    } catch (error) {
        console.error('Erro ao criar transação:', error);
    }
}

// Obter a blockchain completa de um nó na rede
async function getBlockchain() {
    try {
        const selectedNode = getSelectedNode();
        const response = await fetch(`${selectedNode}/chain`);
        const data = await response.json();
        document.getElementById('output').innerText = "Nó: " + selectedNode + "\n"
        document.getElementById('output').innerText += JSON.stringify(data, null, 2);
    } catch (error) {
        console.error('Erro ao obter a blockchain:', error);
    }
}

// Resolver conflitos usando o algoritmo de consenso de maior cadeia
async function resolveConflicts() {
    const selectedNode = getSelectedNode();
    const response = await fetch(`${selectedNode}/nodes/resolve`);
    const data = await response.json();
    document.getElementById('output').innerText = JSON.stringify(data, null, 2);
}

// Resolver conflitos nos nós da rede pelo algoritmo algoritmo de consenso da maioria (50% + 1)
async function resolveConflictsMajority() {
    try {
        const selectedNode = getSelectedNode();
        const response = await fetch(`${selectedNode}/nodes/all`);
        if (!response.ok) {
            throw new Error(`Erro ao buscar nós: ${response.statusText}`);
        }
        const data = await response.json();
        const nodes = data.nodes;

        let message = ""
        let finalMessage = ""

        for (const node of nodes) {
            const resolveResponse = await fetch(`http://${node}/nodes/resolve/majority`);
            if (!resolveResponse.ok) {
                console.warn(`Falha ao resolver conflitos no nó ${node}`);
                continue;
            }
            const data = await resolveResponse.json();
            
            message = JSON.stringify(data, null, 2)
            if(message.includes('A cadeia de todos os nós foi substituída pela cadeia válida e mais longa')){
                finalMessage = message
            }
            
            //document.getElementById('output-conflict').innerText = "Resultado após resolver conflito:\n" + JSON.stringify(data, null, 2);
        }

        if(finalMessage.length != 0){
            document.getElementById('output-conflict').innerText = "Resultado após resolver conflito:\n" + finalMessage;
        }
        else{
            document.getElementById('output-conflict').innerText = "Resultado após resolver conflito:\n" + message;
        }
    
    }catch (error) {
        console.error(`Erro ao resolver conflitos no nó ${node}:`, error);
    }
}

// Limpar conteúdo dos resoltados na saída 
function cleanOutput(){
    document.getElementById('output').innerText = "Resultado das operações vai aparecer aqui..."
    document.getElementById('output-conflict').innerText = "Resultado de resolvendo conflitos vai aparecer aqui..."
}

    
const baseUrl = 'http://127.0.0.1:5000';

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
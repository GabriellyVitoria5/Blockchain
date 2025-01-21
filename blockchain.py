import hashlib
import json
import time
from urllib.parse import urlparse
from uuid import uuid4
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
from argparse import ArgumentParser
import threading
from collections import Counter

# Classe que implementa a estrutura básica do blockchain
class Blockchain:

    def __init__(self):
        self.current_transactions = [] # Transações pendentes
        self.chain = []
        self.nodes = set()

        # Primeiro bloco da cadeia
        self.new_block(previous_hash='1', proof=100)

    # Adicionar um novo nó na lista 
    def register_node(self, address):
        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            # Aceitar URL do tipo '192.168.0.5:5000'.
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError('Invalid URL')

    # Criar um novo bloco e adicionar na cadeia com base na prova criada pelo algoritmo e o bloco anterior
    def new_block(self, proof, previous_hash):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'transactions': self.current_transactions, # Transações incluídas no bloco
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # Limpa as transações pendentes
        self.current_transactions = []

        self.chain.append(block)
        return block

    # Cria uma nova transação que será incluída no próximo bloco minerado
    def new_transaction(self, sender, recipient, amount):
        self.current_transactions.append({
            'sender': sender, # Quem enviou
            'recipient': recipient, # Quem recebeu
            'amount': amount, # O que é enviado na transação, aqui é a quantidade
        })
        return self.last_block['index'] + 1
    
    # Retorna o hash SHA-256 criado para um bloco
    # OBS: O dicionário precisa estar ordenado para evitar hashs inconsistentes
    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()
    
    # Retorna o último bloco da cadeia
    @property
    def last_block(self):
        return self.chain[-1]
    
    # Implementa o algoritmo de proof of work (PoW) para gerar uma hash com 4 zeros no começo
    def proof_of_work(self, last_block):
        last_proof = last_block['proof']
        last_hash = self.hash(last_block)

        proof = 0
        while self.valid_proof(last_proof, proof, last_hash) is False:
            proof += 1

        return proof

    # Validar a Prova de Trabalho
    @staticmethod
    def valid_proof(last_proof, proof, last_hash):
        guess = f'{last_proof}{proof}{last_hash}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"
    
    # Verifica se o hash de cada bloco da cadeia está correto e de acordo com a proof of work
    def valid_chain(self, chain):
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n-----------\n")
            
            # Verificar se a hash do bloco está correta
            last_block_hash = self.hash(last_block)
            if block['previous_hash'] != last_block_hash:
                return False

            # Verificar se a proof of work está correta
            if not self.valid_proof(last_block['proof'], block['proof'], last_block_hash):
                return False

            last_block = block
            current_index += 1

        return True
    
    # Usar algoritmo de consenso, resolvendo conflitos ao substituir a cadeia pela mais longa e válida na rede
    def resolve_conflicts(self):
        neighbours = self.nodes
        new_chain = None

        # Procurar cadeias maiores do que a atual
        max_length = len(self.chain)

        # Verifica a cadeia de todos os nós na rede
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # Verificar se a nova cadeia é maior e é válida
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Substitui a cadeia se houver uma nova cadeia válida maior que a atual
        if new_chain:
            self.chain = new_chain
            return True

        return False

    # Resolver conflitos nas cadeias dos nós pelo algoritmo de consenso da maioria dos nós (50% + 1)
    # A nova cadeia será a maior mais votada (que mais aparece)
    def resolve_conflicts_majority(self):
        neighbours = self.nodes
        all_chains = []  

        # Buscar as cadeias dos nós disponíveis na rede e armazenar somente as válidas
        for node in neighbours:
            try:
                response = requests.get(f'http://{node}/chain')

                if response.status_code == 200:
                    length = response.json()['length']
                    chain = response.json()['chain']

                    # Armazenar cadeia e seu tamanho 
                    if self.valid_chain(chain):
                        all_chains.append((length, chain))  

            except Exception as e:
                print(f"Erro ao conectar com {node}: {e}")

        # Não há cadeia válida, cadeia dos nós não serão atualizadas
        if not all_chains:
            return False 

        # Lista com todos os tamanhos das cadeias encontradas
        all_chain_lengths = [length for length, chain in all_chains]

        # Contar quantas vezes cada tamanho aparece, simulando um sistema de votação
        length_votes = {}
        for length in all_chain_lengths:
            if length not in length_votes:
                length_votes[length] = 1
            else:
                length_votes[length] += 1

        # Descobrir qual foi o tamanho mais votado (o que mais aparece)
        most_voted_length = max(length_votes, key=length_votes.get)

        # Filtrar as cadeias que têm o tamanho mais votado
        valid_chains = [chain for length, chain in all_chains if length == most_voted_length]

        # Escolher a cadeia mais longa após o filtro de votação. OBS: em caso de empate, a função max retorna a primeira cadeia mais longa
        longest_chain = max(valid_chains, key=len)

        # Substituir a cadeia local pela mais votada e longa
        if len(longest_chain) > len(self.chain):
            self.chain = longest_chain
            return True

        return False

    # Retornar todos os nós da cadeia
    def get_all_nodes(self):
        return self.nodes
    
# Criação de um nó Flask para expor a API
app = Flask(__name__)
CORS(app)

# Criar endereço único para o nó
node_identifier = str(uuid4()).replace('-', '')

# Instanciar a blockchain
blockchain = Blockchain()

# Iniciar o servidor Flask em uma thread separada
def start_flask(port):
    app.run(host='0.0.0.0', port=port)

# Todos os nós criados irão informar o nó de referência sobre sua existência
def connect_nodes_to_reference_node():
    reference_node = "127.0.0.1:5000"  # Nó de referência na porta 5000 por padrão
    try:
        # Solicitar a lista de nós ao nó inicial
        response = requests.get(f'http://{reference_node}/nodes/all')

        # Registrar o novo nó no nó de referência se nó de referência conseguir receber requisições 
        if response.status_code == 200:
            nodes = response.json()['nodes']
            requests.post(f'http://{reference_node}/nodes/register', json={'nodes': [f'http://127.0.0.1:{port}']})

    except requests.exceptions.RequestException as e:
        print(f"Não foi possível conectar ao nó inicial: {e}")

# Atualizar lista de nós conhecidos na rede inteira após a aplicação Flask iniciar
def update_all():
    reference_node = "127.0.0.1:5000" # Nó de referência na porta 5000 por padrão
    try:
        headers = {'Content-Type': 'application/json'}
        data = {'new_node': f'http://127.0.0.1:{port}'} 

        # Enviar a solicitação de atualização ao nó de referência
        response = requests.post(f'http://{reference_node}/nodes/update_all', json=data, headers=headers)
        if response.status_code == 200:
            print("Todos os nós foram atualizados com sucesso.")
        else:
            print(f"Falha ao atualizar os nós: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao tentar atualizar os nós: {e}")

# ---------------- Criação de rotas ----------------

# Rota para minerar um novo bloco
@app.route('/mine', methods=['GET'])
def mine():
    
    # Usar o algoritmo de proof of work no último bloco para pegar a próxima prova
    last_block = blockchain.last_block
    proof = blockchain.proof_of_work(last_block)

    # Recompensa pela mineração
    blockchain.new_transaction(
        sender="0", # 0 significa que minerou 
        recipient=node_identifier,
        amount=1,
    )

    # Adiciona o novo bloco à cadeia
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': "Novo bloco criado",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200

# Rota para criar uma nova transação
@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    # Valida os dados
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Valores estão faltando', 400

    # Criar a transação
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

    response = {'message': f'Transações serão criadas no Bloco {index}'}
    return jsonify(response), 201


# Rota para exibir a cadeia completa
@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

# Rota para registrar novos nós
@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Erro: Favor informar uma lista válida de nós", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'Novos nós foram adicionados',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201

# Rota para aplicar o algoritmo de consenso
@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'A cadeia foi substituída',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'A cadeia está completa',
            'chain': blockchain.chain
        }

    return jsonify(response), 200

# Rota para aplicar o algoritmo de consenso
@app.route('/nodes/resolve/majority', methods=['GET'])
def consensus_majority():
    replaced = blockchain.resolve_conflicts_majority()

    if replaced:
        response = {
            'message': 'A cadeia foi substituída',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'A cadeia atual está completa e não será atualizada',
            'chain': blockchain.chain
        }

    return jsonify(response), 200

# Rota para retornar todos os nós registrados
@app.route('/nodes/all', methods=['GET'])
def get_nodes_blockchain():
    all_nodes = list(blockchain.get_all_nodes())  # Convertendo para lista para facilitar o retorno em JSON
    response = {
        'nodes': all_nodes,
        'total_nodes': len(all_nodes),
    }
    return jsonify(response), 200

# Rota para informar a todos os nós sobre a chegada de um novo nó utilizando a lista do nó de refrerência como base, assim todos os nós irão se conhecer
@app.route('/nodes/update_all', methods=['POST'])
def update_all_nodes():
    reference_node = "http://127.0.0.1:5000"  # Nó de referência na porta 5000 por padrão

    # Nó de referência conhece todos os nós, obter a lista de todos os nós da rede por ele
    try:
        response = requests.get(f'{reference_node}/nodes/all')
        if response.status_code == 200:
            nodes_from_reference = response.json().get('nodes', [])
            print(f"Lista de nós do nó de referência obtida: {nodes_from_reference}")
        else:
            return f"Erro ao obter a lista de nós do nó de referência: {response.text}", 500
    except requests.exceptions.RequestException as e:
        return f"Erro ao conectar ao nó de referência: {e}", 500

    # Atualiza a lista local de nós em todos os nós conhecidos
    for node in nodes_from_reference:
        try:
            # Envia a lista completa de nós para cada nó
            response = requests.post(f'http://{node}/nodes/register', json={'nodes': nodes_from_reference})
            if response.status_code == 201:
                print(f"Lista de nós propagada com sucesso para {node}")
            else:
                print(f"Falha ao propagar a lista de nós para {node}: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Erro ao notificar o nó {node}: {e}")

    return jsonify({'message': 'Todos os nós foram atualizados com sucesso com base no nó de referência'}), 200

# ---------------- Main ----------------
if __name__ == '__main__':

    # Definir um argumento opcional para especificar a porta onde a aplicação será executada
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    # Registrar o próprio nó na lista de nós
    self_node_address = f'http://127.0.0.1:{port}'
    blockchain.register_node(self_node_address)

    # Novo nó criado irá informar o nó de referência sobre sua existência
    connect_nodes_to_reference_node()

    # Inicia o servidor Flask em uma thread separada
    flask_thread = threading.Thread(target=start_flask, args=(port,))
    flask_thread.start()

    # Espera para garantir que o Flask está em execução
    import time
    time.sleep(2)

    # Atualiza a lista local de nós de todos os nós conectados na rede
    update_all()

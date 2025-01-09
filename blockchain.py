import hashlib
import json
from time import time
from uuid import uuid4
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

# Classe que implementa a estrutura básica do blockchain
class Blockchain:

    def __init__(self):
        self.current_transactions = [] # Transações pendentes
        self.chain = []
        self.nodes = set()

        # Primeiro bloco da cadeia
        self.new_block(previous_hash='1', proof=100)

    # Criar um novo bloco e adicionar na cadeia com base na prova criada pelo algoritmo e o bloco anterior
    def new_block(self, proof, previous_hash):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
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
        """
        Creates a new transaction to go into the next mined Block

        :param sender: Address of the Sender
        :param recipient: Address of the Recipient
        :param amount: Amount
        :return: The index of the Block that will hold this transaction
        """

        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
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
    
    # Implementa o algoritmo de Prova de Trabalho (PoW)
    def proof_of_work(self, last_block):
        """
        Simple Proof of Work Algorithm:

         - Find a number p' such that hash(pp') contains leading 4 zeroes
         - Where p is the previous proof, and p' is the new proof
        """

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
            # Check that the hash of the block is correct
            last_block_hash = self.hash(last_block)
            if block['previous_hash'] != last_block_hash:
                return False

            # Check that the Proof of Work is correct
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

                # Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Substitui a cadeia se houver uma nova cadeia válida maior que a atual
        if new_chain:
            self.chain = new_chain
            return True

        return False
    
# Criação de um nó Flask para expor a API
app = Flask(__name__)
CORS(app)

# Criar endereço único para o nó
node_identifier = str(uuid4()).replace('-', '')

# Instanciar do blockchain
blockchain = Blockchain()


# Rota para minerar um novo bloco
@app.route('/mine', methods=['GET'])
def mine():
    # We run the proof of work algorithm to get the next proof...
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
        'message': "New Block Forged",
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
        return 'Missing values', 400

    # Criar a transação
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

    response = {'message': f'Transaction will be added to Block {index}'}
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
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201

# Rota para aplicar o algoritmo de consenso
@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }

    return jsonify(response), 200


app.run(debug=True)
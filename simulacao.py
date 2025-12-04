import math
import os

# CONFIGURAÇÕES
BLOCK_SIZE = 4
NUM_BLOCKS = 100

MAX_PTRS = 12

#  CLASSES

class Bitmap:
    def __init__(self):
        self.mapa = [0] * NUM_BLOCKS  # 0=Livre, 1=Ocupado

    def alloc(self):
        try:
            idx = self.mapa.index(0)
            self.mapa[idx] = 1
            return idx
        except: return -1

class Inode:
    def __init__(self, i_id, i_type='FILE'):
        self.id = i_id
        self.type = i_type
        self.ref_count = 1
        self.size = 0
        
        self.blocks = [-1] * MAX_PTRS #ponteiros

    def __repr__(self):
        return f"< Inode {self.id} > \ntype: {self.type}, \nref_count: {self.ref_count}\nsize: {self.size}, \nblocks: {self.blocks}\n"

class FileSystem:
    def __init__(self):
        self.disk = [None] * NUM_BLOCKS
        self.bitmap = Bitmap()
        self.inodes = {} # Tabela de Inodes
        self.next_id = 1
        
        # BOOT: Cria Inode 0 (Raiz)
        self.inodes[0] = Inode(0, 'DIR')
        self._write_data(self.inodes[0], b".:0|..:0")

    def _write_data(self, inode, data):
        """Pega bytes -> Aloca blocos -> Preenche lista do Inode -> Grava no Disco"""

        qtd = math.ceil(len(data) / BLOCK_SIZE)
        inode.size = len(data)
        
        # Limpa blocos antigos
        for i in range(len(inode.blocks)): 
            if inode.blocks[i] != -1: self.bitmap.mapa[inode.blocks[i]] = 0
            inode.blocks[i] = -1

        cursor = 0
        for i in range(qtd):
            blk = self.bitmap.alloc()
            self.disk[blk] = data[cursor : cursor + BLOCK_SIZE]
            inode.blocks[i] = blk
            cursor += BLOCK_SIZE

    def _read_data(self, inode):
        """Lê os blocos apontados pelo inode e retorna bytes"""
        buf = b""
        for b in inode.blocks:
            if b != -1: buf += self.disk[b]
        return buf

    #Métodos auxiliares
    def add_dir_entry(self, dir_id, name, target_id):
        dir_inode = self.inodes[dir_id]
        content = self._read_data(dir_inode)
        new_entry = f"|{name}:{target_id}".encode()
        self._write_data(dir_inode, content + new_entry)

    def create_file(self, parent_id, name, content_bytes):
        inode = Inode(self.next_id, 'FILE')
        self.inodes[self.next_id] = inode
        self.next_id += 1
        
        self._write_data(inode, content_bytes)
        self.add_dir_entry(parent_id, name, inode.id)
        return inode.id

    def create_dir(self, parent_id, name):
        inode = Inode(self.next_id, 'DIR')
        self.inodes[self.next_id] = inode
        self.next_id += 1
        
        self._write_data(inode, f".:{inode.id}|..:{parent_id}".encode())
        self.add_dir_entry(parent_id, name, inode.id)
        return inode.id
    
    #LINKS
    def hard_link(self, parent_id, name, target_inode_id):
        # Incrementa ref_count e adiciona entrada no dir
        inode = self.inodes[target_inode_id]
        inode.ref_count += 1
        self.add_dir_entry(parent_id, name, target_inode_id)

    def symb_link(self, parent_id, name, target_path_str):
        # Cria inode novo para o o caminho
        inode = Inode(self.next_id, 'LNK')
        self.inodes[self.next_id] = inode
        self.next_id += 1
        
        self._write_data(inode, target_path_str.encode())
        self.add_dir_entry(parent_id, name, inode.id)

# EXECUÇÃO

if __name__ == "__main__":

    # Entrada
    ARQ_ENTRADA = "arq.txt"
    with open(ARQ_ENTRADA, "rb") as f: conteudo = f.read()

    #Inicializa FS
    fs = FileSystem()

    print("\n>>> Iniciando sistema:")
    # Mostra Bitmap inicial)
    print(fs.bitmap.mapa)

    print("\n>>> Tabela de Inodes")
    print(fs.inodes)

    print("\n>>> Inode 0 (Raiz)")
    print(fs.inodes[0])

    print("\n>>> Importar arquivo para a raiz")
    id_arq = fs.create_file(0, ARQ_ENTRADA, conteudo)
    print(f"(Criado com ID {id_arq})")

    print("\n>>> Conteudo do Diretorio 0 ")
    print(fs._read_data(fs.inodes[0]).decode())

    print(f"\n>>> Mostrando node {id_arq}")
    print(fs.inodes[id_arq])
    print("\n>>> Exemplo de Conteudo Físico (primeiro bloco do arquivo original)")
    bloco_dados = fs.inodes[id_arq].blocks[0]
    print(f"Bloco {bloco_dados}: {fs.disk[bloco_dados]}")

    print("\n>>> Criar novo diretorio '/docs' dentro da Raiz")
    id_docs = fs.create_dir(0, "docs")
    print(fs.inodes[id_docs])

    print("\n>>> Criar HARD LINK")
    #dentro de '/docs' apontando para o arquivo original
    fs.hard_link(id_docs, "backup", id_arq)

    print("\n>>> conteudo do Diretorio '/docs'")
    # Aqui vemos que 'hardlink' aponta para 1
    print(fs._read_data(fs.inodes[id_docs]).decode())

    print(f"\n>>> Inode {id_arq} de novo")
    # (Verificar ref_count)
    print(fs.inodes[id_arq]) # ref_count deve ser 2

    print("\n>>> Criar SYMBOLIC LINK dentro de '/docs'")
    fs.symb_link(id_docs, "atalho", "/arq.txt")

    print("\n>>> Mostrar Tabela de Inodes Final")
    for k, v in fs.inodes.items():
        print(f"{k}: {v}")

    print("\n>>> Mostrar Memória (Bitmap) - Primeiros 50 blocos")
    print(fs.bitmap.mapa[:50])


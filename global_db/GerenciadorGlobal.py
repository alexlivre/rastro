import os
import sqlite3
import hashlib
import logging
import shutil
try:
    from util.Utilitarios import eh_diretorio_critico
except ImportError:
    from rastro_app.util.Utilitarios import eh_diretorio_critico

class GerenciadorGlobal:
    def __init__(self):
        self.home = os.path.expanduser('~')
        self.rastro_global_dir = os.path.join(self.home, '.rastro')
        self.db_path = os.path.join(self.rastro_global_dir, 'rastro_global.db')
        self._inicializar_db()

    def _inicializar_db(self):
        if not os.path.exists(self.rastro_global_dir):
            os.makedirs(self.rastro_global_dir, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Projetos (
                id_unico TEXT PRIMARY KEY,
                nome_projeto TEXT,
                caminho_absoluto TEXT,
                data_adicao TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_projetos_caminho
            ON Projetos (caminho_absoluto)
        ''')
        
        conn.commit()
        conn.close()

    def registrar_projeto(self, nome: str, caminho: str, data_inicializacao: str) -> str:
        id_unico = hashlib.sha256(f"{nome}::{data_inicializacao}".encode()).hexdigest()[:16]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO Projetos (id_unico, nome_projeto, caminho_absoluto, data_adicao)
            VALUES (?, ?, ?, datetime('now'))
        ''', (id_unico, nome, caminho))
        
        conn.commit()
        conn.close()
        
        return id_unico

    def obter_projeto_por_id(self, id_unico: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Projetos WHERE id_unico = ?', (id_unico,))
        projeto = cursor.fetchone()
        conn.close()
        return projeto
        
    def obter_projeto_por_nome(self, nome: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Projetos WHERE nome_projeto = ?', (nome,))
        projetos = cursor.fetchall()
        conn.close()
        return projetos

    def listar_projetos_globais(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT id_unico, nome_projeto, caminho_absoluto, data_adicao FROM Projetos')
        projetos = cursor.fetchall()
        conn.close()
        return projetos

    def atualizar_caminho(self, id_unico: str, novo_caminho: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE Projetos SET caminho_absoluto = ? WHERE id_unico = ?', (novo_caminho, id_unico))
            conn.commit()
            return True
        except Exception as e:
            logging.error(f"Erro ao atualizar caminho no DB Global: {e}")
            return False
        finally:
            conn.close()

    def esquecer_projeto(self, identificador: str, dry_run: bool = False):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tentar achar por ID primeiro
        cursor.execute('SELECT * FROM Projetos WHERE id_unico = ?', (identificador,))
        projeto = cursor.fetchone()
        
        if not projeto:
            # Tentando por nome
            cursor.execute('SELECT * FROM Projetos WHERE nome_projeto = ?', (identificador,))
            projetos = cursor.fetchall()
            if len(projetos) > 1:
                print(f"Múltiplos projetos encontrados com o nome '{identificador}'. Use o ID.")
                for p in projetos:
                    print(f"ID: {p[0]} - Caminho: {p[2]}")
                conn.close()
                return
            elif len(projetos) == 1:
                projeto = projetos[0]
        
        if not projeto:
            print(f"Projeto '{identificador}' não encontrado.")
            conn.close()
            return

        id_unico, nome, caminho, _ = projeto
        print(f"Projeto encontrado:")
        print(f"  Nome: {nome}")
        print(f"  ID: {id_unico}")
        print(f"  Caminho: {caminho}")
        
        if dry_run:
            print("[DRY-RUN] O registro seria removido do DB e a pasta .rastro deletada (se segura).")
            conn.close()
            return

        confirm = input("Tem certeza que deseja esquecer este projeto? (y/n): ")
        if confirm.lower() != 'y':
            conn.close()
            return

        cursor.execute('DELETE FROM Projetos WHERE id_unico = ?', (id_unico,))
        conn.commit()
        conn.close()
        print(f"Projeto removido do banco de dados global.")
        
        caminho_rastro = os.path.join(caminho, '.rastro')
        if os.path.exists(caminho_rastro):
            if eh_diretorio_critico(caminho):
                logging.error(f"Caminho do projeto é crítico ({caminho}). Não removendo .rastro por segurança.")
            else:
                try:
                    shutil.rmtree(caminho_rastro)
                    print(f"Pasta .rastro removida de {caminho}")
                except Exception as e:
                    logging.error(f"Erro ao remover .rastro: {e}")

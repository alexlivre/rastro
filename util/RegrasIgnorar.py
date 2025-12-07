import os
import fnmatch

REGRAS_PADRAO_RASTRO = ['.rastro', '.rastro/*', '*.pyc', '__pycache__']

class RegrasIgnorar:
    def __init__(self, regras: list[str]):
        self.regras = regras

    def deve_ignorar(self, caminho_absoluto: str, raiz_projeto: str) -> bool:
        """
        Verifica se o arquivo/diretório deve ser ignorado.
        """
        if not caminho_absoluto.startswith(raiz_projeto):
            return False
            
        caminho_relativo = os.path.relpath(caminho_absoluto, raiz_projeto)
        
        # Normalizar separadores para / para facilitar fnmatch
        caminho_relativo_posix = caminho_relativo.replace(os.path.sep, '/')
        
        # Verifica se o próprio nome do arquivo/dir bate com alguma regra
        nome_arquivo = os.path.basename(caminho_relativo)
        
        for regra in self.regras:
            # Regras podem ser globais (*.pyc) ou de caminho (dir/*)
            if fnmatch.fnmatch(caminho_relativo_posix, regra):
                return True
            if fnmatch.fnmatch(nome_arquivo, regra):
                return True
            # Verifica partes do caminho para diretórios ignorados
            parts = caminho_relativo_posix.split('/')
            for part in parts:
                if fnmatch.fnmatch(part, regra): # Ex: .rastro
                    return True
                    
        return False

def carregar_regras(caminho_raiz: str) -> RegrasIgnorar:
    """
    Carrega regras do .gitignore (se existir) e adiciona as padrões.
    """
    regras = list(REGRAS_PADRAO_RASTRO)
    
    arquivo_gitignore = os.path.join(caminho_raiz, '.gitignore')
    if os.path.isfile(arquivo_gitignore):
        try:
            with open(arquivo_gitignore, 'r', encoding='utf-8') as f:
                for linha in f:
                    linha = linha.strip()
                    if not linha or linha.startswith('#'):
                        continue
                    # Ajustes básicos de .gitignore para fnmatch
                    if linha.endswith('/'):
                        linha = linha[:-1] 
                    regras.append(linha)
        except Exception:
            pass # Falha silenciosa na leitura do gitignore
            
    return RegrasIgnorar(regras)

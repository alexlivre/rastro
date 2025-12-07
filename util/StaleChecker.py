import os
import json
import logging
from .RegrasIgnorar import carregar_regras

CAMINHO_RASTRO = '.rastro'
ARQUIVO_STATE = 'state.json'
ARQUIVO_CONFIG = 'config.json'

class StaleChecker:
    def __init__(self, caminho_raiz: str):
        self.caminho_raiz = caminho_raiz
        self.caminho_state = os.path.join(caminho_raiz, CAMINHO_RASTRO, ARQUIVO_STATE)

    def _gerar_estado_atual(self) -> dict:
        """
        Gera um dicionário representando o estado atual do file system.
        Chave: caminho_relativo, Valor: {mod_time, size}
        """
        estado = {}
        regras = carregar_regras(self.caminho_raiz)
        
        for root, dirs, files in os.walk(self.caminho_raiz):
            # Filtrar diretórios ignorados para não descer neles
            dirs[:] = [d for d in dirs if not regras.deve_ignorar(os.path.join(root, d), self.caminho_raiz)]
            
            for file in files:
                caminho_absoluto = os.path.join(root, file)
                if regras.deve_ignorar(caminho_absoluto, self.caminho_raiz):
                    continue
                
                try:
                    stats = os.stat(caminho_absoluto)
                    caminho_relativo = os.path.relpath(caminho_absoluto, self.caminho_raiz).replace(os.path.sep, '/')
                    estado[caminho_relativo] = {
                        'mod_time': stats.st_mtime,
                        'size': stats.st_size
                    }
                except OSError:
                    continue # Arquivo pode ter sido deletado durante a verificação
                    
        return estado

    def _salvar_state_json(self, base_id: int):
        """
        Salva o estádo atual no arquivo state.json.
        """
        estado_atual = self._gerar_estado_atual()
        dados = {
            "base_id": base_id,
            "arquivos": estado_atual
        }
        
        try:
            with open(self.caminho_state, 'w', encoding='utf-8') as f:
                json.dump(dados, f, indent=2)
        except Exception as e:
            logging.error(f"Erro ao salvar state.json: {e}")

    def obter_delta_modificacao(self):
        """
        Compara o estado salvo em state.json com o sistema de arquivos atual.
        Retorna (modificados, adicionados, removidos) -> listas de caminhos relativos.
        """
        if not os.path.exists(self.caminho_state):
            # Se não existe state, tudo é novo (ou nada, se vazio)
            # Mas sem base de comparação, retornamos tudo como 'adicionado' se quisermos ser rigorosos,
            # ou vazio se assumirmos que é um projeto novo.
            # Logicamente, se não tem state, assumimos que devemos gerar um na próxima.
            # Para fins de 'status', retornamos tudo que existe como adicionado.
            atual = self._gerar_estado_atual()
            return [], list(atual.keys()), []
            
        try:
            with open(self.caminho_state, 'r', encoding='utf-8') as f:
                dados_salvos = json.load(f)
        except Exception:
             return [], [], [] # Erro de leitura, assume sem mudanças ou inconclusivo

        estado_antigo = dados_salvos.get("arquivos", {})
        estado_atual = self._gerar_estado_atual()
        
        modificados = []
        adicionados = []
        removidos = []
        
        # Verificar modificados e removidos
        for caminho, dados_antigos in estado_antigo.items():
            if caminho not in estado_atual:
                removidos.append(caminho)
            else:
                dados_novos = estado_atual[caminho]
                # Comparação simples por mod_time e size
                if (abs(dados_novos['mod_time'] - dados_antigos['mod_time']) > 0.001 or 
                    dados_novos['size'] != dados_antigos['size']):
                    modificados.append(caminho)
        
        # Verificar adicionados
        for caminho in estado_atual:
            if caminho not in estado_antigo:
                adicionados.append(caminho)
                
        return modificados, adicionados, removidos

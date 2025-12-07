import os
import json
import logging
import tarfile
import shutil
import hashlib
from datetime import datetime
from typing import Optional, List
from .Snapshot import Snapshot
try:
    from global_db.GerenciadorGlobal import GerenciadorGlobal
    from util.StaleChecker import StaleChecker
    from util.RegrasIgnorar import carregar_regras
    from util.Utilitarios import eh_diretorio_critico
except ImportError:
    # Fallback se estiver rodando como pacote completo sem path hack
    from rastro_app.global_db.GerenciadorGlobal import GerenciadorGlobal
    from rastro_app.util.StaleChecker import StaleChecker
    from rastro_app.util.RegrasIgnorar import carregar_regras
    from rastro_app.util.Utilitarios import eh_diretorio_critico

class ProjetoNaoInicializado(Exception):
    pass

class GerenciadorRastro:
    def __init__(self, caminho_inicial: Optional[str] = None, comando_atual: str = ""):
        if caminho_inicial:
            if not os.path.exists(caminho_inicial):
                 raise FileNotFoundError(f"Caminho inicial não existe: {caminho_inicial}")
            os.chdir(caminho_inicial)
        
        self.caminho_raiz = self._encontrar_raiz_projeto()
        self.gerenciador_global = GerenciadorGlobal()
        
        if not self.caminho_raiz:
            if comando_atual == 'init':
                self.caminho_raiz = os.getcwd() # Init usa o diretório atual se não achar nada acima
            else:
                raise ProjetoNaoInicializado()
        else:
             # Se for init mas já existe rastro, o _encontrar_raiz_projeto retornou algo.
             # O método inicializar vai lidar com a validação de já existir.
             pass

        self.caminho_rastro = os.path.join(self.caminho_raiz, '.rastro')
        self.caminho_config = os.path.join(self.caminho_rastro, 'config.json')
        self.config = {}

        if os.path.exists(self.caminho_config):
            self._carregar_config()
            self._verificar_registro_global()

    def _encontrar_raiz_projeto(self) -> Optional[str]:
        atual = os.getcwd()
        while True:
            if os.path.isdir(os.path.join(atual, '.rastro')):
                return atual
            pai = os.path.dirname(atual)
            if pai == atual:
                return None
            atual = pai

    def _carregar_config(self):
        with open(self.caminho_config, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

    def _salvar_config(self):
        with open(self.caminho_config, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2)

    def _verificar_registro_global(self):
        nome = self.config['projeto']['nome']
        data_init = self.config['projeto']['data_inicializacao']
        id_unico = hashlib.sha256(f"{nome}::{data_init}".encode()).hexdigest()[:16]
        
        projeto = self.gerenciador_global.obter_projeto_por_id(id_unico)
        
        if projeto:
            caminho_registrado = projeto[2]
            if caminho_registrado != self.caminho_raiz:
                self.gerenciador_global.atualizar_caminho(id_unico, self.caminho_raiz)
                logging.info(f"Caminho do projeto atualizado no registro global: {self.caminho_raiz}")
        else:
            self.gerenciador_global.registrar_projeto(nome, self.caminho_raiz, data_init)

    def inicializar(self, nome: Optional[str], mensagem: Optional[str], descricao: Optional[str] = None):
        if os.path.exists(self.caminho_config):
            logging.warning("Rastro já inicializado neste diretório.")
            print("Rastro já inicializado.")
            return

        os.makedirs(os.path.join(self.caminho_rastro, 'snapshots'), exist_ok=True)
        
        nome_projeto = nome or os.path.basename(self.caminho_raiz)
        desc = descricao or mensagem or f"Projeto {nome_projeto}"
        data_init = datetime.now().isoformat()
        
        self.config = {
            "projeto": {
                "nome": nome_projeto,
                "descricao": desc,
                "data_inicializacao": data_init
            },
            "rastro": {
                "versao": "1.0",
                "proximo_id": 1,
                "ultimo_restaurado_id": 0
            },
            "snapshots": []
        }
        
        self._salvar_config()
        self.gerenciador_global.registrar_projeto(nome_projeto, self.caminho_raiz, data_init)
        logging.info("Projeto Rastro inicializado com sucesso.")
        print(f"Rastro inicializado em: {self.caminho_raiz}")

    def criar_snapshot(self, mensagem: Optional[str] = None):
        stalle_checker = StaleChecker(self.caminho_raiz)
        mods, adds, rems = stalle_checker.obter_delta_modificacao()
        
        # Se for o primeiro snapshot (proximo_id == 1), ignoramos o check de nada modificado
        # pois o state.json ainda não existe ou é base.
        # Mas o stale checker retorna tudo como 'adicionado' se não tiver state.
        if not mods and not adds and not rems and self.config["rastro"]["proximo_id"] > 1:
            logging.info("Nada para salvar, diretório de trabalho limpo.")
            print("Nada para salvar. Diretório limpo.")
            return

        msg = mensagem or "Snapshot sem mensagem"
        id_snap = self.config["rastro"]["proximo_id"]
        filename = f"rastro_{id_snap:04d}.tar.gz"
        caminho_relativo_snap = f"snapshots/{filename}"
        caminho_absoluto_snap = os.path.join(self.caminho_rastro, caminho_relativo_snap)
        
        regras = carregar_regras(self.caminho_raiz)
        
        files_count = 0
        with tarfile.open(caminho_absoluto_snap, mode='w:gz', compresslevel=1) as tar:
            for root, dirs, files in os.walk(self.caminho_raiz):
                # Filtrar diretórios
                dirs[:] = [d for d in dirs if not regras.deve_ignorar(os.path.join(root, d), self.caminho_raiz)]
                
                for file in files:
                    full_path = os.path.join(root, file)
                    if regras.deve_ignorar(full_path, self.caminho_raiz):
                        continue
                        
                    rel_path = os.path.relpath(full_path, self.caminho_raiz)
                    try:
                        tar.add(full_path, arcname=rel_path)
                        files_count += 1
                    except (PermissionError, OSError) as e:
                        logging.warning(f"Arquivo ignorado por erro: {full_path} - {e}")

        size_bytes = os.path.getsize(caminho_absoluto_snap)
        size_str = f"{size_bytes / 1024:.1f} KB" if size_bytes < 1024*1024 else f"{size_bytes / (1024*1024):.1f} MB"
        
        snap = Snapshot(
            id_rastro=id_snap,
            mensagem=msg,
            timestamp=datetime.now().isoformat(),
            caminho_relativo=caminho_relativo_snap,
            tamanho=size_str
        )
        
        self.config["snapshots"].append(snap.para_json())
        self.config["rastro"]["proximo_id"] += 1
        self.config["rastro"]["ultimo_restaurado_id"] = id_snap
        
        self._salvar_config()
        stalle_checker._salvar_state_json(base_id=id_snap)
        
        print(f"Snapshot #{id_snap} criado com sucesso ({size_str}). {files_count} arquivos arquivados.")

    def listar_snapshots(self):
        snaps = self.config.get("snapshots", [])
        print(f"[Rastro: {self.config['projeto']['nome']} - {self.config['projeto']['descricao']}]")
        print(f"{'ID':<4} | {'Ativo':^5} | {'Data/Hora':<19} | {'Tamanho':<8} | {'Mensagem'}")
        print("-" * 80)
        
        ativo_id = self.config["rastro"].get("ultimo_restaurado_id")
        
        for s in snaps:
            data_fmt = datetime.fromisoformat(s["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
            ativo_mark = "*" if s["id_rastro"] == ativo_id else ""
            print(f"{s['id_rastro']:<4} | {ativo_mark:^5} | {data_fmt:<19} | {s['tamanho']:<8} | {s['mensagem']}")

    def restaurar_snapshot(self, alvo: str, dry_run: bool = False, save_before: bool = False):
        snaps = self.config.get("snapshots", [])
        if not snaps:
            print("Nenhum snapshot para restaurar.")
            return

        # Ordenar por id (que é cronológico)
        snaps_sorted = sorted(snaps, key=lambda x: x['id_rastro'])
        
        target_snap = None
        if alvo.lower() == 'last':
            target_snap = snaps_sorted[-1]
        else:
            try:
                # Se id específico (1, 2, 3...)
                alvo_id = int(alvo)
                # Tentar achar pelo ID exato
                for s in snaps_sorted:
                    if s['id_rastro'] == alvo_id:
                        target_snap = s
                        break
                
                # Se não achar por ID, talvez o usuário quis dizer "o 1º mais recente", "o 2º mais recente"
                # A spec diz: "rastro restore 1 -> mais recente", "restore 2 -> penúltimo"
                # Vamos seguir a SPEC, que é baseada em índice reverso (1-based)
                if not target_snap:
                   # SPEC: restore 1 (mais recente/last), restore 2 (penultimo)
                   idx_reverso = int(alvo)
                   if 1 <= idx_reverso <= len(snaps_sorted):
                       target_snap = snaps_sorted[-idx_reverso]
            except ValueError:
                print("Alvo inválido.")
                return

        if not target_snap:
            print(f"Snapshot alvo '{alvo}' não encontrado.")
            return

        print(f"Restaurando snapshot #{target_snap['id_rastro']} - {target_snap['mensagem']}...")

        stale = StaleChecker(self.caminho_raiz)
        mods, adds, rems = stale.obter_delta_modificacao()
        
        if (mods or adds or rems) and not dry_run:
            if save_before:
                self.criar_snapshot(f"Autosave antes de restore para ID {target_snap['id_rastro']}")
            else:
                resp = input("Há alterações não salvas. Continuar perderá essas alterações. Confirmar? (y/n): ")
                if resp.lower() != 'y':
                    print("Operação cancelada.")
                    return

        if dry_run:
            print("[DRY-RUN] O diretório seria limpo (exceto .rastro) e os arquivos do snapshot extraídos.")
            return

        # Segurança crítica
        if eh_diretorio_critico(self.caminho_raiz):
            logging.critical(f"Tentativa de restore em diretório crítico: {self.caminho_raiz}")
            print("ERRO CRÍTICO: Diretório protegido. Operação abortada.")
            return

        # Limpar diretório
        for item in os.listdir(self.caminho_raiz):
            if item == '.rastro': continue
            path = os.path.join(self.caminho_raiz, item)
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
            except Exception as e:
                logging.error(f"Erro ao limpar {path}: {e}")

        # Extrair
        caminho_tar = os.path.join(self.caminho_rastro, target_snap['caminho_relativo'])
        with tarfile.open(caminho_tar, 'r:gz') as tar:
            tar.extractall(self.caminho_raiz)
            
        self.config["rastro"]["ultimo_restaurado_id"] = target_snap['id_rastro']
        self._salvar_config()
        stale._salvar_state_json(base_id=target_snap['id_rastro'])
        print("Restauração concluída com sucesso.")

    def remover_snapshots(self, alvo: str, dry_run: bool = False):
        snaps = self.config.get("snapshots", [])
        if not snaps:
            print("Sem snapshots para remover.")
            return
            
        # Ordenar crescente (mais antigo primeiro)
        snaps_sorted = sorted(snaps, key=lambda x: x['id_rastro'])
        to_remove = []

        if alvo == 'all':
            # Todos exceto o último (mais recente)
            to_remove = snaps_sorted[:-1]
        else:
            try:
                qtd = int(alvo)
                to_remove = snaps_sorted[:qtd]
            except ValueError:
                print("Quantidade inválida.")
                return
        
        ativo_id = self.config["rastro"].get("ultimo_restaurado_id")
        
        final_remove = []
        for s in to_remove:
            if s['id_rastro'] == ativo_id:
                print(f"Ignorando remoção do snapshot #{s['id_rastro']} pois é o ativo.")
            else:
                final_remove.append(s)
        
        if dry_run:
            print("[DRY-RUN] Seriam removidos:")
            for s in final_remove:
                print(f"  - ID {s['id_rastro']}: {s['mensagem']}")
            return

        commits_mantidos = [s for s in snaps if s not in final_remove]
        
        for s in final_remove:
            path_tar = os.path.join(self.caminho_rastro, s['caminho_relativo'])
            try:
                if os.path.exists(path_tar):
                    os.remove(path_tar)
                print(f"Snapshot #{s['id_rastro']} removido.")
            except Exception as e:
                logging.error(f"Erro ao deletar arquivo {path_tar}: {e}")
                # Mantém na lista se falhar? Melhor remover do config para não ficar inconsistente
                
        self.config["snapshots"] = commits_mantidos
        self._salvar_config()

    def exibir_status(self):
        print(f"Projeto: {self.config['projeto']['nome']}")
        ativo = self.config["rastro"].get("ultimo_restaurado_id")
        print(f"Snapshot Ativo ID: {ativo}")
        
        stale = StaleChecker(self.caminho_raiz)
        mods, adds, rems = stale.obter_delta_modificacao()
        
        if not mods and not adds and not rems:
            print("\nDiretório de trabalho limpo. Nada a salvar.")
        else:
            print("\n>>> Modificações detectadas. Trabalho não salvo presente.")
            if mods:
                print("\nArquivos Modificados:")
                for f in mods: print(f"  - {f}")
            if adds:
                print("\nArquivos Novos:")
                for f in adds: print(f"  + {f}")
            if rems:
                print("\nArquivos Deletados:")
                for f in rems: print(f"  - {f}")

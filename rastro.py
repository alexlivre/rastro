import sys
import os
import logging

# Adicionar o diretório atual ao path para garantir que imports funcionem
# mesmo rodando script direto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # Tenta importar como pacote (python -m rastro_app.rastro)
    from rastro_app.util.ArgumentParser import criar_parser
    from rastro_app.core.GerenciadorRastro import GerenciadorRastro, ProjetoNaoInicializado
    from rastro_app.global_db.GerenciadorGlobal import GerenciadorGlobal
except ImportError:
    # Fallback para execução direta (python rastro.py) ou se rastro_app não estiver no path
    try:
        from util.ArgumentParser import criar_parser
        from core.GerenciadorRastro import GerenciadorRastro, ProjetoNaoInicializado
        from global_db.GerenciadorGlobal import GerenciadorGlobal
    except ImportError as e:
        print(f"Erro crítico de importação: {e}")
        sys.exit(1)

def setup_logging(caminho_projeto=None):
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    
    # Logger raiz
    logger = logging.getLogger()
    logger.setLevel(logging.INFO) # Console padrão INFO
    
    # Handler Console
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    logger.addHandler(ch)
    
    # Handler Arquivo (se estiver num projeto)
    log_file = None
    if caminho_projeto:
        rastro_dir = os.path.join(caminho_projeto, '.rastro')
        if os.path.isdir(rastro_dir):
            log_file = os.path.join(rastro_dir, 'rastro.log')
    else:
        # Tenta logar no global se não tiver em projeto
        home = os.path.expanduser('~')
        global_rastro = os.path.join(home, '.rastro')
        if os.path.isdir(global_rastro):
            log_file = os.path.join(global_rastro, 'rastro_global.log')

    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG) # Arquivo com mais detalhes
        fh.setFormatter(logging.Formatter(log_format))
        logger.addHandler(fh)

def main():
    parser = criar_parser()
    args = parser.parse_args()

    # Comandos que não exigem estar num projeto
    if args.comando == 'projects':
        gg = GerenciadorGlobal()
        projs = gg.listar_projetos_globais()
        print(f"{'ID':<16} | {'Nome':<20} | {'Caminho'}")
        print("-" * 80)
        for p in projs:
            print(f"{p[0]:<16} | {p[1]:<20} | {p[2]}")
        return

    if args.comando == 'forget':
        gg = GerenciadorGlobal()
        gg.esquecer_projeto(args.identificador, args.dry_run)
        return

    # Comandos de Projeto
    try:
        # Detectar caminho inicial para setup de logging e manager
        caminho_inicial = os.getcwd()
        if args.comando == 'init' and args.caminho:
             caminho_inicial = args.caminho

        setup_logging(caminho_inicial)
        
        gerenciador = GerenciadorRastro(
            caminho_inicial=caminho_inicial if args.comando == 'init' else None,
            comando_atual=args.comando
        )

        if args.comando == 'init':
            gerenciador.inicializar(args.name, args.message)
        
        elif args.comando == 'save':
            gerenciador.criar_snapshot(args.message)
            
        elif args.comando == 'list':
            gerenciador.listar_snapshots()
            
        elif args.comando == 'status':
            gerenciador.exibir_status()
            
        elif args.comando == 'restore':
            gerenciador.restaurar_snapshot(args.alvo, args.dry_run, args.save_before)
            
        elif args.comando == 'remover':
            gerenciador.remover_snapshots(args.alvo, args.dry_run)

    except ProjetoNaoInicializado:
        print("Este diretório não parece ser um projeto Rastro.")
        # Se não for init, perguntar se quer criar?
        # A spec diz: "Perguntar: 'Rastro não inicializado. Inicializar aqui? (y/n)'"
        # No entanto, init requer argumentos como nome e msg opcionais.
        resp = input("Rastro não inicializado. Inicializar aqui agora? (y/n): ")
        if resp.lower() == 'y':
            try:
                # Inicializa no diretório atual
                g = GerenciadorRastro(comando_atual='init')
                g.inicializar(None, "Inicializado automaticamente")
                print("Agora tente seu comando novamente.")
            except Exception as e:
                print(f"Erro ao tentar inicializar: {e}")
        else:
            print("Operação abortada.")
            
    except Exception as e:
        logging.critical(f"Erro inesperado: {e}", exc_info=True)
        print(f"Erro: {e}")

if __name__ == '__main__':
    main()

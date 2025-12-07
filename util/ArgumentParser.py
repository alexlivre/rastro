import argparse

def criar_parser():
    parser = argparse.ArgumentParser(
        description="Rastro - Sistema de Versionamento Local Simples",
        prog="rastro"
    )
    subparsers = parser.add_subparsers(dest='comando', required=True)

    # Init
    p_init = subparsers.add_parser('init', help='Inicializa um novo projeto Rastro')
    p_init.add_argument('caminho', nargs='?', default='.', help='Caminho do projeto (opcional)')
    p_init.add_argument('--name', help='Nome do projeto')
    p_init.add_argument('-m', '--message', help='Descrição do projeto')

    # Save
    p_save = subparsers.add_parser('save', help='Salva o estado atual (snapshot)')
    p_save.add_argument('-m', '--message', help='Mensagem do snapshot')

    # List
    p_list = subparsers.add_parser('list', help='Lista os snapshots do projeto')

    # Status
    p_status = subparsers.add_parser('status', help='Mostra o status atual')

    # Restore
    p_restore = subparsers.add_parser('restore', help='Restaura um snapshot anterior')
    p_restore.add_argument('alvo', help='ID do snapshot ou "last" ou indice relativo (1=ultimo)')
    p_restore.add_argument('--dry-run', action='store_true', help='Simula a restauração')
    p_restore.add_argument('--save-before', action='store_true', help='Salva snapshot atual antes de restaurar')

    # Remover
    p_remove = subparsers.add_parser('remover', help='Remove snapshots antigos')
    p_remove.add_argument('alvo', help='Quantidade a remover (antigos) ou "all"')
    p_remove.add_argument('--dry-run', action='store_true', help='Simula a remoção')

    # Projects
    p_projects = subparsers.add_parser('projects', help='Lista todos os projetos rastreados globalmente')

    # Forget
    p_forget = subparsers.add_parser('forget', help='Remove um projeto do registro global')
    p_forget.add_argument('identificador', help='ID ou Nome do projeto')
    p_forget.add_argument('--dry-run', action='store_true', help='Simula o esquecimento')

    return parser

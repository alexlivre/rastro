import os

# Constantes de diretórios críticos (segurança para não apagar o sistema)
# Adaptado para Windows e outros sistemas
DIRETORIOS_CRITICOS = [
    'C:\\', 'D:\\', 'E:\\', 'F:\\', 'G:\\',  # Raízes de drives comuns
    '\\', '/', 
    '/home', '/usr', '/bin', '/sbin', '/etc', '/var', '/opt',
    'C:\\Windows', 'C:\\Program Files', 'C:\\Program Files (x86)', 'C:\\Users'
]

def eh_diretorio_critico(caminho: str) -> bool:
    """
    Verifica se o caminho fornecido é um diretório crítico do sistema
    que não deve ser apagado ou alterado drasticamente pelo Rastro.
    """
    if not caminho:
        return False
        
    caminho_abs = os.path.abspath(caminho)
    
    # Verifica correspondência exata
    for critico in DIRETORIOS_CRITICOS:
        if os.name == 'nt': # Windows (case insensitive)
            if caminho_abs.lower() == critico.lower():
                return True
            # Também verificar se é a raiz do drive atual (ex: C:\)
            drive, tail = os.path.splitdrive(caminho_abs)
            if tail in ['\\', '/', ''] and not drive: # Raiz sem drive (Unix)
                 if caminho_abs in ['/', '\\']: return True
            if tail in ['\\', '/', ''] and drive: # Raiz com drive (Windows)
                 return True # C:\ é crítico
        else:
            if caminho_abs == critico:
                return True

    return False

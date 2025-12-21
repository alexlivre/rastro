# Guia do Rastro – Versionamento Local Simples

## 1. Introdução

**Rastro** é uma ferramenta de linha de comando (CLI) simples e segura para:

- Versionar projetos localmente  
- Criar e restaurar snapshots (pontos de restauração)  
- Gerenciar múltiplos projetos de forma leve

Características:

- Escrito em **Python puro**
- Focado em **simplicidade**, sem a complexidade do Git
- Ideal para:
  - Desenvolvedores
  - Escritores
  - Qualquer pessoa que precise de controle de versão local e descomplicado

---

## 2. Instalação

### 2.1. Requisitos

- **Python** 3.14 ou superior  
- Sistema operacional:
  - **Windows**
  - **Linux**
  - **macOS**

---

### 2.2. Instalação no Windows

Você pode instalar o Rastro de duas formas:

---

#### 2.2.1. Instalação (Recomendada) — Instalador para Windows (.exe)

Esta é a forma mais simples: você baixa um `.zip`, **descompacta** e executa o instalador.  
O instalador já está configurado para:

- instalar tudo automaticamente
- criar as pastas necessárias
- configurar o **PATH** do sistema (para o comando `rastro` funcionar no terminal)

**Download (Google Drive):**  
https://drive.google.com/file/d/1uhJW-l1PpboDz6CcKAnLDepeiVIDuD4H/view?usp=sharing

**Passo a passo:**

1. Baixe o arquivo: `RastroSetup_User_v1.0.exe.zip`
2. Clique com o botão direito e **Extraia/Descompacte** o `.zip`
3. Execute o instalador: `RastroSetup_User_v1.0.exe`
4. Conclua a instalação seguindo as etapas do instalador
5. Feche e reabra o terminal (PowerShell ou CMD)
6. Teste:
   ```bash
   rastro --help
   ```

> Observações:
> - Se o Windows SmartScreen exibir aviso, verifique a origem do arquivo antes de prosseguir.
> - Em alguns ambientes, pode ser necessário executar o instalador como **Administrador** para configurar PATH global.

---

#### 2.2.2. Configuração manual (alternativa)

1. **Obtenha o Rastro**  
   Baixe ou clone o repositório em uma pasta, por exemplo:  
   `C:\code\rastro`

2. **Adicione ao PATH** (opção 1 – recomendada se você usa o repositório direto)

   - Abra:  
     `Configurações do Sistema → Variáveis de Ambiente → Path → Editar → Novo`
   - Adicione:  
     `C:\code\rastro`
   - Assim, você poderá usar:
     - Um `rastro.bat` presente nessa pasta, ou  
     - Um executável do Rastro, se existir.

3. **Criar um atalho global via .bat** (opção 2 – alternativa)

   Crie um arquivo `rastro.bat` em **alguma pasta que já esteja no PATH** (ex.: `C:\Windows` ou outra pasta de ferramentas) com o conteúdo:

   ```bat
   @echo off
   python C:\code\rastro\rastro_app\rastro.py %*
   ```

   Assim você poderá chamar `rastro` de qualquer lugar no terminal.

---

### 2.3. Configuração no Linux / macOS

1. **Clone o repositório**, por exemplo:  
   `~/rastro`

2. **Crie um alias no shell** (em `~/.bashrc`, `~/.zshrc` ou equivalente):

   ```bash
   alias rastro='python3 /caminho/para/rastro/rastro_app/rastro.py'
   ```

3. Recarregue o perfil do shell:

   ```bash
   source ~/.bashrc   # ou ~/.zshrc
   ```

Após isso, o comando `rastro` deverá funcionar em qualquer diretório.

---

## 3. Conceitos Fundamentais

- **Projeto**  
  Diretório que contém os arquivos a serem versionados.  
  É inicializado com:

  ```bash
  rastro init
  ```

- **Snapshot (Ponto de Restauração)**  
  - Estado completo do projeto em um momento específico  
  - Armazenado em `.rastro/snapshots`  
  - Cada snapshot tem um **ID numérico sequencial** (0, 1, 2, ...)

- **Snapshot Ativo**  
  - Snapshot cujo estado está refletido no diretório de trabalho atual  
  - Normalmente é o **último snapshot criado**, mas pode mudar com `restore`

- **Trabalho não salvo**  
  - Alterações (criação, modificação, remoção de arquivos) **ainda não registradas** em um snapshot  
  - O comando `rastro status` mostra esse estado

- **Registro Global**  
  - Banco SQLite em `~/.rastro/rastro_global.db`  
  - Mapeia todos os projetos gerenciados pelo Rastro  
  - Permite **listar** e **esquecer** projetos (`projects`, `forget`)

---

## 4. Comandos Básicos

### 4.1. `rastro init`

Inicializa um novo projeto Rastro no diretório atual.

**Sintaxe:**

```bash
rastro init --name "NomeDoProjeto" -m "Descrição inicial"
```

**Opções:**

- `--name` (obrigatório): nome amigável do projeto  
- `-m`, `--mensagem`: mensagem do snapshot inicial  
  - Padrão: `"Snapshot inicial"`

**Exemplo:**

```bash
cd /caminho/do/projeto
rastro init --name "MeuSite" -m "Estrutura básica"
```

**O que acontece:**

- Cria a pasta oculta `.rastro`  
- Cria o snapshot inicial **ID 0** com todos os arquivos atuais  
- Registra o projeto no banco de dados global

---

### 4.2. `rastro save`

Cria um novo snapshot com o estado atual do projeto.

**Sintaxe:**

```bash
rastro save [-m "Mensagem descritiva"]
```

**Opções:**

- `-m`, `--mensagem`: mensagem do snapshot  
  - Se omitida, usa `"Snapshot sem mensagem"`

**Exemplo:**

```bash
rastro save -m "Adicionei a página de contato"
```

**O que acontece:**

- Compara o estado atual com o snapshot ativo
- Se **não houver mudanças**, nenhum snapshot é criado (e o comando avisa)
- Se **houver mudanças**:
  - Compacta todos os arquivos (exceto `.rastro`) em um `.tar.gz`
  - Atribui o próximo **ID sequencial**
  - Define o snapshot recém-criado como **ativo**
  - Atualiza o arquivo de estado (`state.json`)

> Dica: rode `rastro status` antes para ver o que será incluído.

---

### 4.3. `rastro list`

Lista todos os snapshots do projeto atual.

**Sintaxe:**

```bash
rastro list
```

**Saída típica:**

```text
[Rastro: MeuSite - Descrição inicial]
ID   | Ativo | Data/Hora           | Tamanho  | Mensagem
--------------------------------------------------------------------------------
1    |       | 2025-12-07 10:00:00 | 0.5 MB   | Inicialização
2    |   *   | 2025-12-07 10:15:00 | 0.6 MB   | Adicionei a página de contato
```

**Campos:**

- **ID**: número sequencial do snapshot  
- **Ativo**: `*` marca o snapshot ativo  
- **Tamanho**: tamanho aproximado do arquivo de snapshot  
- **Mensagem**: texto passado para `save` ou `init`

---

### 4.4. `rastro status`

Mostra diferenças entre o diretório de trabalho e o snapshot ativo.

**Sintaxe:**

```bash
rastro status
```

**Saída típica:**

```text
Projeto: MeuSite
Snapshot Ativo ID: 2

>>> Modificações detectadas. Trabalho não salvo presente.

Arquivos Modificados:
  - index.html
Arquivos Novos:
  + imagens/logo.png
Arquivos Deletados:
  - script.js
```

**Interpretação:**

- Se não houver alterações:  
  Mensagem do tipo: **Diretório de trabalho limpo. Nada a salvar.**
- Caso contrário:
  - Lista arquivos **modificados**
  - Arquivos **novos**
  - Arquivos **deletados**

> Observação: a comparação é sempre com o **snapshot ativo**.

---

### 4.5. `rastro restore`

Restaura o projeto para o estado de um snapshot específico.

**Sintaxe:**

```bash
rastro restore [ID|last] [--dry-run] [--save-before]
```

**Parâmetros / Opções:**

- `ID`: número do snapshot desejado (veja com `rastro list`)
- `last`: restaura o snapshot mais recente (maior ID)
- `--dry-run`:
  - Apenas **simula** a restauração
  - Mostra o que seria alterado, sem mexer nos arquivos
- `--save-before`:
  - Cria um snapshot com o estado atual **antes de restaurar**
  - Fortemente recomendado se houver trabalho não salvo

**Exemplos:**

```bash
rastro restore 1               # volta para o snapshot ID 1
rastro restore last            # volta para o snapshot mais recente
rastro restore 3 --dry-run     # apenas mostra o que aconteceria
rastro restore 2 --save-before # salva o estado atual, depois restaura o ID 2
```

**Comportamento esperado:**

- Se o diretório estiver **limpo**, a restauração é feita diretamente
- Se houver **trabalho não salvo**:
  - O Rastro **avisa** sobre possível perda de dados  
  - O uso de `--save-before` evita essa perda, criando um snapshot de segurança
- Após a restauração, o snapshot escolhido se torna o **ativo**

**Segurança:**

- O Rastro **bloqueia** restaurações em diretórios críticos do sistema  
  (ex.: `C:\Windows`, `/`, `/etc`)
- `--dry-run` é a forma segura de verificar o que vai mudar
- Boas práticas:
  - Sempre use `--save-before` quando tiver dúvida
  - Entenda que restaurar **pode sobrescrever trabalho não salvo**

---

### 4.6. `rastro remover`

Remove snapshots antigos para liberar espaço.

**Sintaxe:**

```bash
rastro remover [N|all]
```

**Opções:**

- `N` (inteiro): remove os **N snapshots mais antigos** que **não são o ativo**
- `all`: remove **todos** os snapshots, exceto o ativo

**Exemplos:**

```bash
rastro remover 2   # remove os dois snapshots mais antigos não ativos
rastro remover all # mantém apenas o snapshot ativo
```

**Regras de funcionamento:**

- O snapshot **ativo nunca é removido** por esse comando
- Se `N` for maior que o total de snapshots não ativos, remove **todos os não ativos**
- Remove os arquivos `.tar.gz` correspondentes e atualiza `config.json`

> Atenção: a remoção é **definitiva**. Não há como recuperar snapshots apagados.

---

### 4.7. `rastro projects`

Lista todos os projetos registrados no banco global.

**Sintaxe:**

```bash
rastro projects
```

**Saída típica:**

```text
ID               | Nome                 | Caminho
--------------------------------------------------------------------------------
a02dc3e8fdc2f9e4 | MeuSite              | C:\projetos\site
9dc49296a46e179d | Documentos           | C:\Users\Alex\Documents\meu_texto
```

**Utilidade:**

- Ajuda a localizar rapidamente todos os diretórios gerenciados pelo Rastro

---

### 4.8. `rastro forget`

Remove um projeto do registro global e, opcionalmente, apaga a pasta `.rastro` local.

**Sintaxe:**

```bash
rastro forget "NomeDoProjeto"
```

**Exemplo:**

```bash
rastro forget "MeuSite"
```

**O que acontece:**

1. O Rastro pede **confirmação** (`y/n`)
2. Em caso de confirmação:
   - Remove a entrada do projeto no banco global
   - Apaga a pasta `.rastro` no diretório do projeto  
     (ou seja, **todos os snapshots são apagados**)
3. Os **arquivos do projeto** (código, textos etc.) permanecem intactos

> Importante: ação **irreversível**. Só use se tiver certeza de que não precisa mais do histórico.

---

## 5. Exemplos de Fluxo de Trabalho

### 5.1. Iniciar e versionar um projeto

Criando um novo site:

```bash
mkdir meu_site
cd meu_site
echo "<html><body>Olá</body></html>" > index.html

rastro init --name "MeuSite" -m "Primeira versão"
# Cria snapshot ID 0 (inicial)

rastro list
```

Fazendo alterações e salvando:

```bash
echo "<p>Conteúdo novo</p>" >> index.html
mkdir css
echo "body {background: #eee;}" > css/style.css

rastro status               # vê o que mudou
rastro save -m "Adicionados estilo e conteúdo"
```

---

### 5.2. Trabalhando com várias versões

```bash
rastro list
# Suponha que o snapshot ID 2 seja uma versão estável/funcional

echo "console.log('teste');" > script.js
rastro save -m "Adicionei script"

# Algo quebrou, você quer voltar:
rastro restore 2 --save-before
```

Comportamento:

- É criado um snapshot (por exemplo, ID 4) com o **estado atual**, incluindo `script.js`
- Em seguida, o estado do **ID 2** é restaurado
- O snapshot ID 4 permanece no histórico, caso você queira recuperar aquele trabalho

---

### 5.3. Desfazendo alterações não salvas

Você mexeu em arquivos mas decidiu **descartar** tudo:

```bash
rastro status      # confirma que há trabalho não salvo

# Para voltar ao estado do último snapshot salvo:
rastro restore last
```

> Atenção: alterações não salvas serão **perdidas permanentemente**.

---

### 5.4. Limpando o histórico

```bash
# Remove os 5 snapshots mais antigos (exceto o ativo)
rastro remover 5

# Ou deixa apenas o snapshot ativo
rastro remover all
```

---

### 5.5. Gerenciando múltiplos projetos

Listando todos os projetos controlados:

```bash
rastro projects
```

Esquecendo um projeto antigo:

```bash
rastro forget "ProjetoAntigo"
```

---

## 6. Dicas de Segurança e Boas Práticas

- Verifique **sempre** o `rastro status` antes de:
  - `rastro restore`
  - `rastro remover`
- Use `--save-before` em `restore` se houver qualquer dúvida
- Escreva **mensagens descritivas** nos snapshots
- Lembre-se: Rastro **não substitui backup remoto**
  - Considere copiar seus projetos / snapshots para outro disco, nuvem etc.
- Evite versionar arquivos enormes (vídeos, bancos de dados grandes)
  - Podem encher o disco rapidamente
- Não inicialize o Rastro em diretórios de sistema (raiz, `C:\Windows`, `/etc`, etc.)
  - A ferramenta tem proteções, mas é melhor evitar cenários perigosos

---

## 7. Solução de Problemas Comuns

- **`rastro` não é reconhecido como comando**  
  - Verifique se:
    - O diretório do script está no `PATH`, ou  
    - Você está usando o caminho completo do script (ex.: `python /caminho/rastro.py`)

- **`ModuleNotFoundError: No module named 'rastro_app'`**  
  - Execute o comando a partir da raiz do repositório do projeto, ou  
  - Instale em modo desenvolvimento:
    ```bash
    pip install -e .
    ```

- **Erro ao restaurar em diretório crítico**  
  - O Rastro bloqueia para segurança  
  - Mova o projeto para uma pasta de usuário (ex.: `~/projetos`, `C:\Users\SeuUsuario\projetos`)

- **Restauração apagou trabalho não salvo**  
  - Se não foi usado `--save-before` e não há outro backup,  
    **não há como recuperar pelo Rastro**

- **Projeto não aparece em `rastro projects`**  
  - Pode ser:
    - Problema de inicialização (projeto não foi `init` corretamente)
    - Corrupção do banco global  
  - Tente:
    - Rodar `rastro init` novamente no projeto  
    - Verificar permissões de escrita em `~/.rastro`

---

## 8. Considerações Finais

O **Rastro** oferece um controle de versão **local, simples e leve**, ideal para uso diário sem a curva de aprendizado do Git.

Resumo de uso recomendado:

- Use Rastro para:
  - snapshots rápidos
  - experimentação de ideias
  - projetos pessoais e textos
- Combine com Git quando precisar de:
  - colaboração
  - histórico remoto
  - integração com plataformas como GitHub/GitLab
```

# Gmail Manager CLI

Gerenciador de e-mail Gmail via IMAP com interface CLI moderna e intuitiva.

## Requisitos

- Python 3.11+
- Conta Gmail com IMAP habilitado
- Senha de App do Google (não use senha normal)

## Instalação

```bash
# Clone ou copie o projeto
cd gmail-manager

# Instale as dependências
pip install -r requirements.txt
```

## Configuração

### 1. Criar arquivo `.env`

Copie o exemplo e edite com suas credenciais:

```bash
cp .env.example .env
```

Edite `.env`:

```env
GMAIL_EMAIL=seuemail@gmail.com
GMAIL_APP_PASSWORD=sua_senha_de_app_16_caracteres
DOWNLOAD_DIR=downloads
```

### 2. Obter Senha de App do Google

1. Acesse https://myaccount.google.com/apppasswords
2. Faça login na sua conta Google
3. Em "Selecionar app", escolha "Mail"
4. Em "Selecionar dispositivo", escolha seu dispositivo
5. Clique em "Gerar"
6. Copie a senha de 16 caracteres (ex: `abcd efgh ijkl mnop`)
7. Cole no arquivo `.env` como `GMAIL_APP_PASSWORD`

**Importante:** Use a senha sem espaços ou com espaços, ambos funcionam.

### 3. Habilitar IMAP no Gmail

1. Acesse https://mail.google.com
2. Clique em ⚙️ Configurações → Ver todas as configurações
3. Vá na aba "Encaminhamento e POP/IMAP"
4. Em "Acesso IMAP", selecione "Ativar IMAP"
5. Clique em "Salvar alterações"

## Como Executar

```bash
python app.py
```

## Funcionalidades

### Menu Principal

```
╔════════════════════════════════════════════╗
║              GMAIL MANAGER                 ║
╠════════════════════════════════════════════╣
║ Conta: usuario@gmail.com                   ║
║ Status: ● Conectado                        ║
╚════════════════════════════════════════════╝

1. Caixa de entrada      📥
2. Pastas / Marcadores   📁
3. Pesquisar e-mails     🔍
4. Abrir e-mail          📖
5. Selecionar e-mails    ✓
6. Baixar anexos         ⬇️
7. Gerenciar e-mails     ⚙️
8. Atualizar             🔄
0. Sair                  🚪
```

### 1. Caixa de Entrada

Lista os últimos 50 e-mails com:
- ID, Data, Remetente, Assunto
- Status (NOVO/LIDO)
- Contagem de anexos

### 2. Pastas / Marcadores

Lista todas as pastas disponíveis:
- INBOX
- Sent
- Drafts
- Spam
- Trash
- All Mail
- Starred
- E pastas personalizadas

Permite mudar de pasta para visualização.

### 3. Pesquisar E-mails

Formatos de busca suportados:
- `from:email@exemplo.com` - Por remetente
- `subject:assunto` - Por assunto
- `is:unread` - Não lidos
- `is:starred` - Marcados com estrela
- `termo livre` - Busca no assunto

### 4. Abrir E-mail

Visualiza e-mail completo:
- Cabeçalho (De, Para, Data, Assunto)
- Corpo do texto ou HTML
- Lista de anexos
- Opção para baixar anexos
- Marcar como lido/não lido

### 5. Selecionar E-mails

Seleção múltipla por IDs:
- Digite IDs separados por vírgula: `1,3,5`
- Ou `all` para selecionar todos (limite 100)

### 6. Baixar Anexos

Baixa anexos dos e-mails selecionados:
- Organização automática por remetente
- Nomes únicos para evitar sobrescrita
- Progresso em tempo real

### 7. Gerenciar E-mails

Ações disponíveis:
- Marcar como lido
- Marcar como não lido
- Excluir permanentemente (com confirmação)
- Mover para outra pasta
- Limpar seleção

### 8. Atualizar

Recarrega dados da caixa de entrada.

## Estrutura do Projeto

```
gmail-manager/
├── app.py                 # Ponto de entrada
├── .env                   # Credenciais (não commitar)
├── .env.example           # Exemplo de .env
├── .gitignore
├── requirements.txt
├── README.md
├── downloads/             # Anexos baixados
│
└── src/
    ├── __init__.py
    ├── config/
    │   ├── __init__.py
    │   └── settings.py    # Carregamento de configurações
    ├── imap/
    │   ├── __init__.py
    │   ├── client.py      # Cliente IMAP
    │   ├── folders.py     # Gerenciamento de pastas
    │   ├── messages.py    # Gerenciamento de mensagens
    │   └── search.py      # Motor de busca
    ├── email_parser/
    │   ├── __init__.py
    │   └── parser.py      # Parser de e-mails
    ├── attachments/
    │   ├── __init__.py
    │   └── downloader.py  # Download de anexos
    └── cli/
        ├── __init__.py
        └── menu.py        # Interface CLI
```

## Limitações do IMAP/Gmail

1. **Busca por conteúdo**: O IMAP não permite busca full-text eficiente. A busca é feita apenas no assunto.

2. **Mensagens grandes**: E-mails muito grandes podem demorar para carregar.

3. **Rate limiting**: O Gmail pode limitar conexões frequentes.

4. **Anexos grandes**: Downloads de arquivos >25MB podem falhar.

5. **Pasta [Gmail]/All Mail**: Contém todos os e-mails, incluindo cópias de outras pastas.

## Segurança

✅ **Nunca:**
- Salvar senhas no código
- Imprimir senhas no terminal
- Commitar `.env` no Git
- Executar conteúdo HTML recebido
- Executar anexos automaticamente
- Sobrescrever arquivos sem aviso

✅ **Sempre:**
- Usar Senha de App (não senha normal)
- Manter `.env` fora do versionamento
- Confirmar ações destrutivas
- Validar nomes de arquivo

## Troubleshooting

### Erro de autenticação

- Verifique se está usando Senha de App, não senha normal
- Confirme que o IMAP está habilitado no Gmail
- Verifique se há espaços extras no `.env`

### Nenhuma mensagem encontrada

- Verifique se há e-mails na caixa de entrada
- Tente a opção "Atualizar"
- Verifique o log `gmail_manager.log`

### Conexão perdida

- O sistema tenta reconectar automaticamente
- Verifique sua conexão com a internet
- O Gmail pode ter limitado temporariamente

## Licença

MIT License

## Autor

Gmail Manager CLI Team

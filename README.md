# Gmail Manager CLI

Gerenciador de e-mail Gmail via linha de comando (CLI) usando IMAP.

## Requisitos

- Python 3.11+
- Conta Gmail com verificação em duas etapas ativa
- Senha de App do Google

## Instalação

```bash
# Clone ou acesse o diretório do projeto
cd gmail-manager

# Instale as dependências
pip install -r requirements.txt
```

## Configuração

### 1. Criar arquivo `.env`

Copie o exemplo:

```bash
cp .env.example .env
```

### 2. Editar `.env`

```env
GMAIL_EMAIL=seuemail@gmail.com
GMAIL_APP_PASSWORD=sua_senha_de_app_aqui
DOWNLOAD_DIR=downloads
```

### 3. Como obter Senha de App do Google

1. Acesse https://myaccount.google.com/apppasswords
2. Faça login na sua conta Google
3. Ative a **Verificação em Duas Etapas** (se ainda não estiver ativa)
4. Em "Senhas de app":
   - Selecione "Mail" como aplicativo
   - Selecione seu dispositivo (Windows, Mac, etc.)
   - Clique em "Gerar"
5. Copie a senha de 16 caracteres gerada
6. Cole no arquivo `.env` como `GMAIL_APP_PASSWORD`

**Importante:** Use apenas a Senha de App, NÃO use sua senha normal do Gmail.

### 4. Habilitar IMAP no Gmail

1. Acesse https://mail.google.com
2. Clique em ⚙️ Configurações → Ver todas as configurações
3. Vá para a aba "Encaminhamento e POP/IMAP"
4. Em "Acesso IMAP", selecione "Ativar IMAP"
5. Clique em "Salvar alterações"

## Execução

```bash
python app.py
```

## Estrutura do Projeto

```
gmail-manager/
├── app.py                 # Ponto de entrada principal
├── .env                   # Credenciais (não versionar)
├── .env.example           # Exemplo de configuração
├── .gitignore             # Arquivos ignorados pelo Git
├── requirements.txt       # Dependências Python
├── README.md              # Este arquivo
│
├── src/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py    # Carrega configurações do .env
│   ├── imap/
│   │   ├── __init__.py
│   │   ├── client.py      # Cliente IMAP principal
│   │   ├── folders.py     # Gerenciamento de pastas
│   │   ├── messages.py    # Operações com mensagens
│   │   └── search.py      # Buscas IMAP
│   ├── email_parser/
│   │   ├── __init__.py
│   │   └── parser.py      # Parse de e-mails
│   ├── attachments/
│   │   ├── __init__.py
│   │   └── downloader.py  # Download de anexos
│   └── cli/
│       ├── __init__.py
│       └── menu.py        # Interface CLI
│
└── downloads/             # Pasta para anexos baixados
```

## Funcionalidades

### Menu Principal

1. **Caixa de entrada** - Lista e-mails da pasta INBOX
2. **Pastas / Marcadores** - Visualiza e seleciona pastas
3. **Pesquisar e-mails** - Busca por remetente, assunto ou texto
4. **Abrir e-mail** - Lê conteúdo completo de um e-mail
5. **Selecionar e-mails** - Seleciona múltiplos e-mails por ID
6. **Baixar anexos** - Downloads de arquivos anexados
7. **Gerenciar e-mails** - Marcar como lido/não lido, excluir, mover
8. **Atualizar** - Recarrega lista de e-mails
0. **Sair** - Encerra o programa

### Critérios de Pesquisa

- `from:email@dominio.com` - Buscar por remetente
- `subject:palavra` - Buscar por assunto
- `texto livre` - Busca geral no corpo

### Seleção Múltipla

Digite IDs separados por vírgula:
```
1,3,5,7
```

Ou selecione todos:
```
all
```

## Limitações do IMAP/Gmail

- O Gmail usa labels (etiquetas) em vez de pastas tradicionais
- E-mails podem aparecer em múltiplas "pastas" (ex: Inbox e All Mail)
- Exclusão move para Trash, não remove permanentemente
- Algumas operações podem ter limite de taxa do Google
- Anexos muito grandes podem falhar no download

## Segurança

- ✅ Credenciais armazenadas apenas no `.env`
- ✅ Senha nunca é impressa no terminal
- ✅ `.env` ignorado pelo Git
- ✅ Conteúdo HTML convertido para texto seguro
- ✅ Confirmação antes de ações destrutivas

## Solução de Problemas

### "Falha na autenticação"

- Verifique se está usando Senha de App (não senha normal)
- Confirme que a verificação em duas etapas está ativa
- Tente gerar uma nova Senha de App

### "Nenhum e-mail encontrado"

- Verifique se IMAP está habilitado no Gmail
- Aguarde alguns segundos após conectar
- Tente a opção "Atualizar"

### "Erro de conexão"

- Verifique sua conexão com a internet
- Confirme que o firewall não bloqueia a porta 993
- Tente reconectar (opção 8 ou reinicie o programa)

## Licença

MIT License

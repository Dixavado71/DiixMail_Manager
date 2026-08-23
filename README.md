# Gmail Manager CLI

Gerenciador de e-mail Gmail via linha de comando (CLI) usando IMAP. Uma aplicação Python simples, modular e organizada para gerenciar sua conta Gmail, com foco em facilitar a localização, leitura, organização e **download de arquivos/anexos** recebidos por e-mail.

## ⚠️ Importante

Este projeto usa **autenticação por Senha de App do Google** via IMAP. Não use OAuth 2.0, Gmail API, Selenium ou navegador.

## Requisitos

- Python 3.11 ou superior
- Conta Gmail com acesso IMAP habilitado
- Senha de App do Google (não é a senha normal da conta)

## Instalação

1. Clone o repositório ou copie os arquivos para seu projeto:

```bash
cd gmail-manager
```

2. Instale as dependências:

```bash
pip install -r requirements.txt
```

3. Crie o arquivo `.env` baseado no exemplo:

```bash
cp .env.example .env
```

4. Edite o arquivo `.env` com suas credenciais:

```env
GMAIL_EMAIL=seuemail@gmail.com
GMAIL_APP_PASSWORD=sua_senha_de_app_gerada_pelo_google
DOWNLOAD_DIR=downloads
```

## Como Obter a Senha de App do Google

1. Acesse sua Conta Google: https://myaccount.google.com/
2. Vá para **Segurança** no menu lateral
3. Em "Como fazer login no Google", ative a **Verificação em duas etapas** (se ainda não estiver ativa)
4. Após ativar, volte para **Segurança** e procure por **Senhas de app**
5. Ou acesse diretamente: https://myaccount.google.com/apppasswords
6. Selecione:
   - **App**: Mail
   - **Dispositivo**: Other (ou selecione seu dispositivo)
7. Clique em **Generate**
8. Copie a senha de 16 caracteres gerada
9. Cole no arquivo `.env` como `GMAIL_APP_PASSWORD`

**Importante:** 
- Nunca compartilhe sua Senha de App
- Use apenas no arquivo `.env` (que está no `.gitignore`)
- Se suspeitar de comprometimento, revoke a senha e gere uma nova

## Como Executar

```bash
python app.py
```

Após conectar, você verá o dashboard principal:

```
╔════════════════════════════════════════════╗
║              GMAIL MANAGER                 ║
╠════════════════════════════════════════════╣
║ Conta: usuario@gmail.com                   ║
║ Status: ● Conectado                        ║
╚════════════════════════════════════════════╝

1. Caixa de entrada
2. Pastas / Marcadores
3. Pesquisar e-mails
4. Abrir e-mail
5. Selecionar e-mails
6. Baixar anexos
7. Gerenciar e-mails
8. Atualizar
0. Sair
```

## Estrutura do Projeto

```
gmail-manager/
│
├── app.py                 # Ponto de entrada da aplicação
├── .env                   # Credenciais (NÃO commitar!)
├── .env.example           # Exemplo de configuração
├── .gitignore             # Arquivos ignorados pelo Git
├── requirements.txt       # Dependências Python
├── README.md              # Este arquivo
│
├── src/
│   ├── __init__.py
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py    # Carregamento de configurações
│   │
│   ├── imap/
│   │   ├── __init__.py
│   │   ├── client.py      # Cliente IMAP
│   │   ├── folders.py     # Gerenciamento de pastas
│   │   ├── messages.py    # Gerenciamento de mensagens
│   │   └── search.py      # Motor de busca
│   │
│   ├── email/
│   │   ├── __init__.py
│   │   └── parser.py      # Parser de e-mails
│   │
│   ├── attachments/
│   │   ├── __init__.py
│   │   └── downloader.py  # Download de anexos
│   │
│   └── cli/
│       ├── __init__.py
│       └── menu.py        # Interface CLI
│
└── downloads/             # Pasta para anexos baixados
```

## Funcionalidades

### 1. Caixa de Entrada
- Lista e-mails com ID, data, remetente, assunto, status e anexos
- Mostra apenas metadados inicialmente (carregamento rápido)
- Exibe até 50 e-mails mais recentes

### 2. Pastas / Marcadores
- Lista todas as pastas disponíveis no Gmail
- Permite navegar entre pastas (Inbox, Sent, Drafts, etc.)
- Traduz nomes de pastas para português

### 3. Pesquisa de E-mails
Suporta vários formatos de busca:

```
from:email@exemplo.com     # Buscar por remetente
subject:nota fiscal        # Buscar por assunto
to:destinatario@email.com  # Buscar por destinatário
since:2024-01-01          # Desde uma data
last:30                   # Últimos 30 dias
has:attachment            # Com anexos
is:unread                 # Não lidos
texto livre               # Busca em tudo
```

### 4. Abrir E-mail
- Visualiza remetente, destinatário, data e assunto
- Mostra conteúdo em texto plano ou HTML (convertido)
- Identifica e lista anexos disponíveis

### 5. Seleção Múltipla
- Seleciona e-mails individuais: `1,3,5`
- Seleciona intervalo: `1-10`
- Seleciona todos: `all`

### 6. Download de Anexos
- Baixa anexos de e-mail individual
- Baixa anexos de múltiplos e-mails selecionados
- Opções de organização:
  - Por remetente
  - Por assunto
  - Por data (ano/mês)
  - Sem organização (todos na pasta downloads/)
- Evita sobrescrever arquivos existentes

### 7. Gerenciamento de E-mails
- Marcar como lido/não lido
- Excluir e-mails (com confirmação)
- Mover e-mails entre pastas

### 8. Segurança
- Credenciais nunca são impressas no terminal
- Senha armazenada apenas no `.env`
- Conteúdo HTML convertido para texto (sem execução)
- Confirmação antes de ações destrutivas

## Limitações do IMAP/Gmail

1. **Acesso IMAP deve estar habilitado** nas configurações do Gmail
2. **Senha de App obrigatória** - não funciona com senha normal
3. **Pasta [Gmail]/All Mail** contém todos os e-mails (incluindo arquivados)
4. **Exclusão** move para Lixeira primeiro (pode ser necessário esvaziar a lixeira)
5. **Rate limiting** - Google pode limitar conexões muito frequentes
6. **Busca por anexos** usa `has:attachment` (específico do Gmail)

## Troubleshooting

### Erro: "Falha na autenticação"
- Verifique se está usando Senha de App (não a senha normal)
- Confirme que o acesso IMAP está habilitado no Gmail
- Verifique se a Verificação em Duas Etapas está ativa

### Erro: "Acesso bloqueado"
- Acesse https://accounts.google.com/DisplayUnlockCaptcha
- Tente permitir acesso de apps menos seguros (não recomendado)
- Use apenas Senha de App

### Erro: "Connection timeout"
- Verifique sua conexão com a internet
- Firewall pode estar bloqueando a porta 993 (IMAP SSL)

### Nenhum e-mail aparece
- Verifique se há e-mails na conta
- Tente usar a busca `ALL` ou `last:365`
- Algumas pastas podem estar vazias

## Dependências

O projeto usa apenas bibliotecas essenciais:

- `python-dotenv` - Carregamento de variáveis de ambiente
- `rich` - Interface CLI bonita e organizada

A biblioteca padrão Python é usada sempre que possível (`imaplib`, `email`, `pathlib`).

## Licença

Este projeto é fornecido "como está" para fins educacionais e de uso pessoal.

## Aviso de Segurança

- **Nunca** commit o arquivo `.env` no Git
- **Nunca** compartilhe suas credenciais
- **Sempre** use Senha de App em vez da senha principal
- **Revogue** senhas de app quando não forem mais necessárias

---

**Gmail Manager CLI** - Simplificando o gerenciamento de e-mails via terminal.
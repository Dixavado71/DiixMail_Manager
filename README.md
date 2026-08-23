# Gmail Manager TUI - Interface Premium com Textual

Gerenciador de e-mail Gmail com interface **TUI (Text User Interface)** moderna usando o framework **Textual**. Uma aplicação premium, completa e elegante para gerenciar sua conta Gmail, com foco em facilitar a localização, leitura, organização e **download de arquivos/anexos** recebidos por e-mail.

## 🚀 Novidade: Interface TUI Premium!

Agora com interface moderna estilo "app nativo" no terminal:
- ✨ Widgets reais: botões, inputs, scrollbars, abas
- 🎨 Estilo com CSS no terminal
- 🖱️ Suporte completo a mouse
- 📐 Layouts dinâmicos e responsivos
- ⚡ Concorrência nativa com workers assíncronos
- 🌓 Temas dark/light mode
- 🔍 Preview de e-mails em tempo real

## ⚠️ Importante

Este projeto usa **autenticação por Senha de App do Google** via IMAP. Não use OAuth 2.0, Gmail API, Selenium ou navegador.

## Requisitos

- Python 3.11 ou superior
- Conta Gmail com acesso IMAP habilitado
- Senha de App do Google (não é a senha normal da conta)
- Terminal moderno com suporte a Unicode

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

### Interface TUI Premium (Recomendado)

```bash
python app.py
```

Você verá uma interface moderna com:
- Header com relógio e título
- Sidebar com navegação rápida
- Tabela de e-mails interativa
- Preview em tempo real
- Footer com atalhos
- Suporte completo a mouse

### Interface CLI Clássica

```bash
python app.py --cli
```

Para manter a experiência tradicional baseada em menus.

### Ajuda

```bash
python app.py --help
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
│   ├── cli/
│   │   ├── __init__.py
│   │   └── menu.py        # Interface CLI clássica
│   │
│   └── tui/
│       ├── __init__.py
│       └── app.py         # Interface TUI Premium (Textual)
│
└── downloads/             # Pasta para anexos baixados
```

## Funcionalidades da Interface TUI

### 1. Dashboard Principal
- Status de conexão em tempo real
- Contador de e-mails e selecionados
- Navegação rápida por sidebar
- Preview de e-mail selecionado

### 2. Tabela de E-mails Interativa
- Ordenação por colunas
- Seleção múltipla com clique
- Ícones de status (novo/lido/anexos)
- Hover effects e cursor personalizado

### 3. Atalhos de Teclado
- `[q]` - Sair
- `[r]` - Atualizar e-mails
- `[1-3]` - Navegar entre tabs
- `[t]` - Toggle preview
- `[d]` - Excluir selecionados
- `[s]` - Pesquisar
- `[?]` - Ajuda

### 4. Recursos Avançados
- Downloads em background
- Modais de confirmação
- Notificações toast
- Log de atividades
- Estatísticas detalhadas

## Funcionalidades da Interface CLI

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

### 4. Download de Anexos
- Baixa anexos de e-mail individual
- Baixa anexos de múltiplos e-mails selecionados
- Opções de organização:
  - Por remetente
  - Por assunto
  - Por data (ano/mês)
  - Sem organização (todos na pasta downloads/)
- Evita sobrescrever arquivos existentes

## Tecnologias Utilizadas

### Interface TUI
- **Textual** - Framework TUI moderno (mesmo criador do Rich)
- **Rich** - Renderização rica no terminal

### Interface CLI
- **Rich** - Painéis, tabelas e formatação
- **python-dotenv** - Carregamento de variáveis de ambiente

### Backend
- **imaplib** (stdlib) - Cliente IMAP
- **email** (stdlib) - Parser de e-mails
- **pathlib** (stdlib) - Manipulação de paths

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

### Problemas com TUI
- Use terminais modernos (iTerm2, Windows Terminal, Kitty, Alacritty)
- Redimensione a janela se houver problemas de layout
- Use `--cli` como fallback

## Dependências

O projeto usa bibliotecas modernas e essenciais:

- `textual>=0.47.0` - Framework TUI completo
- `rich>=13.0.0` - Renderização rica no terminal
- `python-dotenv>=1.0.0` - Carregamento de variáveis de ambiente

A biblioteca padrão Python é usada sempre que possível (`imaplib`, `email`, `pathlib`).

## Licença

Este projeto é fornecido "como está" para fins educacionais e de uso pessoal.

## Aviso de Segurança

- **Nunca** commit o arquivo `.env` no Git
- **Nunca** compartilhe suas credenciais
- **Sempre** use Senha de App em vez da senha principal
- **Revogue** senhas de app quando não forem mais necessárias

---

**Gmail Manager TUI** - A evolução do gerenciamento de e-mails via terminal com interface premium.

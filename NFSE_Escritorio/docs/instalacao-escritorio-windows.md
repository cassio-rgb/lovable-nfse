# Instalação no escritório (Windows 10/11) — modo LOCAL

> Situação hoje: o programa abre **somente em DEMONSTRAÇÃO, SEM EMISSÃO FISCAL**, com dados fictícios,
> no próprio computador principal. A emissão real ainda está bloqueada (ver "O que falta").

## O que está pronto
- Gerar a versão instalável do site (pasta `.output-local`) e rodá-la com Node no próprio computador.
- Abrir no navegador desse computador em `http://127.0.0.1:4517/` só depois que ele responder.
- Parar somente o programa que o lançador iniciou (nunca outros programas).
- Recusar porta ocupada, acesso pela rede e modo de emissão real enquanto faltarem peças.

## O que NÃO está pronto
- Emissão fiscal real (faltam login real, cofre do certificado, armazenamento durável, contrato oficial).
- Acesso por outros computadores da rede (LAN): **bloqueado** até haver login real e conexão segura (TLS).
- Acesso de clientes pela internet: fase futura, exigirá hospedagem e autenticação.
- Não há instalador `.exe`. Os comandos abaixo foram testados em Linux; **ainda não foram executados em Windows**.

## Computador principal x demais computadores
- **Principal (host):** roda o site e, no futuro, o serviço fiscal Python e guarda o certificado A1.
- **Demais:** hoje não acessam. No futuro, acessarão pela rede com login, depois de liberado.

## Não precisa de hospedagem mensal, mas precisa de
- Windows 10/11 com **Node.js 22.12 ou mais novo (recomendado: 22 LTS ou 24 LTS)**, **Bun 1.x** (só para instalar as dependências a partir do `bun.lock`) e **Python 3.12 ou mais novo**. Instalar manualmente; nada é instalado automaticamente. O lançador recusa construir/iniciar com versões menores.
- Internet no host (para baixar dependências agora e, no futuro, falar com a API nacional da NFS-e).

## Passo a passo (no Prompt de Comando, dentro da pasta do projeto)
1. Instalar dependências do projeto (uma vez), exatamente como no arquivo de travamento do repositório: `bun install --frozen-lockfile`
   (não use `npm ci`: o repositório não tem `package-lock.json`)
2. Conferir: `scripts\escritorio.cmd verificar`
3. Gerar a versão local: `scripts\escritorio.cmd construir`
4. Iniciar e abrir o navegador: `scripts\escritorio.cmd iniciar --abrir`
   - Outra porta: `scripts\escritorio.cmd iniciar --porta 4600 --abrir`
5. Ver se está rodando: `scripts\escritorio.cmd estado`
6. Parar: `scripts\escritorio.cmd parar`
   - Antes de encerrar, o lançador confere (somente leitura, via PowerShell `Get-CimInstance`) se o número do processo ainda é exatamente o mesmo programa, mesma linha de comando e mesmo horário de criação. Se não for, ou se a conferência falhar, **nada é encerrado**.

Sem o `.cmd`, use `py -3 scripts\escritorio.py <comando>`.
Pedir `construir --modo api` hoje é **recusado** com a explicação do que falta — o programa não troca para demonstração escondido.

## Certificado A1
Fica só no computador principal, em local protegido. Nunca no navegador, no repositório ou em e-mail/chat. O programa ainda não o usa para emitir.

## Backup mínimo (quando a emissão real existir)
Copiar diariamente o banco de dados local e guardar uma cópia fora do computador; testar a restauração. Hoje, em demonstração, não há dados reais para guardar.

# Guia de Hospedagem na Nuvem — Além da Meta Concursos

O sistema está pronto para rodar **24h na nuvem** com **multi-usuário**, **escolha de carreira no cadastro** (PM, PRF, PF, PC, Polícia Penal ou Personalizada) e isolamento completo de dados por conta.

---

## Opção A — Render.com (Mais simples, 1 clique via GitHub)

1. Crie uma conta gratuita no **GitHub** e suba esta pasta para um repositório privado.
2. Crie uma conta no **Render.com** e clique em **New → Blueprint** (ou **Web Service**).
3. Conecte o repositório do GitHub. O Render lê automaticamente o arquivo `render.yaml` e o `Dockerfile`:
   - **Disco Persistente (`/data`)**: garante que as contas e estudos dos seus amigos nunca se percam entre atualizações.
   - **Variável `DATA_DIR=/data`**: já aponta o SQLite para o disco persistente.
   - **Variável `COOKIE_SECURE=true`**: protege os cookies de login em `https://`.
4. Ao finalizar o deploy, o Render gera um link `https://alem-da-meta-concursos.onrender.com` (ou você pode conectar um domínio próprio, ex.: `alemdametaconcursos.com.br`).

> [!NOTE]
> No Render, o **Disk** (disco persistente) requer o plano **Starter** (~US$ 7/mês). Se quiser testar antes sem disco ou usar Railway, veja a Opção B.

---

## Opção B — Railway.app

1. Crie uma conta no **Railway.app** e suba pelo GitHub.
2. Adicione um **Volume** montado em `/data`.
3. Em **Variables**, adicione:
   - `DATA_DIR=/data`
   - `COOKIE_SECURE=true`
   - `APP_SECRET_KEY=<uma-frase-longa-aleatoria>`
4. O `Dockerfile` e o `Procfile` iniciam o servidor automaticamente na porta fornecida pelo Railway.

---

## Opção C — VPS Linux (Hostinger / Contabo / Oracle Cloud)

Na sua VPS com Docker instalado:

```bash
docker build -t alem-da-meta .
docker run -d --name alem-da-meta \
  -p 8000:8000 \
  -e DATA_DIR=/data \
  -e APP_SECRET_KEY="troque-por-uma-chave-secreta-forte" \
  -v alem_da_meta_data:/data \
  --restart unless-stopped \
  alem-da-meta
```

Depois aponte seu domínio (Nginx/Caddy com HTTPS automático) para `localhost:8000`.

---

## Como levar seus dados locais para a nuvem

1. No seu sistema local, entre na sua conta (`mikael`) e clique em **BACKUP** no Dashboard (baixa um arquivo `.json`).
2. Crie sua conta no site publicado na nuvem e clique em **RESTAURAR** enviando esse `.json`. Todas as suas horas, matérias da PC-TO e sua aprovação na PMPA são importadas na hora!

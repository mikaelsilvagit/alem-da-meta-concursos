# 🛡️ Além da Meta Concursos v3.0 — Centro de Operações Multi-Carreira

> *"Treinamento difícil, combate fácil. Missão dada é missão cumprida."*

O **Além da Meta Concursos** é uma plataforma web **multi-usuário** e **multi-carreira** para preparação de alto rendimento em concursos públicos (Polícia Militar, Polícia Rodoviária Federal, Polícia Federal, Polícia Civil, Polícia Penal e editais personalizados), construída com **FastAPI + SQLite (modo WAL)** e interface 100% funcional offline.

---

## 🚀 Principais Recursos

- **Multi-Usuário & Isolamento por Conta:** cadastro com senha protegida (`PBKDF2-SHA256` + cookie `HttpOnly`). Cada usuário possui seu próprio histórico, horas, revisões, simulados, caderno de erros e backups.
- **Trilhas Prontas por Carreira:** no cadastro (ou nas Configurações), escolha entre **PM**, **PRF**, **PF**, **PC**, **Polícia Penal** ou **Personalizada** para montar o edital base com pesos calibrados.
- **Ciclo Tático Ponderado + Plano do Dia Automático:** prioriza matérias pelo peso no edital e dias sem estudo, gerando blocos prontos conforme o tempo disponível no dia (`1h`, `2h`, `3h`, `4h` ou livre).
- **Sequência (Streak) & Constância:** contador de dias seguidos e alerta visual de constância.
- **Plantão de Estudos (Cronômetro & Pomodoro):** marcação precisa mesmo com a aba em segundo plano, contador de acertos/erros em tempo real e som ambiente focado.
- **Dossiê de Matérias, Mapa de Fraquezas & Importador de Edital:** controle por tópico (Teoria, Resumo, Questões), alerta vermelho para tópicos abaixo de `60%` de acerto e importador de conteúdo programático que preserva horas já estudadas.
- **Simulados com Nota de Corte & Desempenho por Matéria:** gráfico de evolução contra a nota de corte e ranking acumulado por disciplina.
- **Revisões Espaçadas (24h, 7d, 15d, 30d), Radar de Lei Seca, Blindagem (Caderno de Erros + Redações) e Perfil (Quadro de Honra + TAF).**
- **Painel Admin Integrado:** o primeiro usuário (administrador) pode listar contas cadastradas e redefinir senhas provisórias direto pelas Configurações.

---

## ☁️ Hospedagem na Nuvem (24h)

O projeto já inclui [`Dockerfile`](Dockerfile), [`.dockerignore`](.dockerignore), [`render.yaml`](render.yaml), [`Procfile`](Procfile) e suporte às variáveis:

- `DATA_DIR`: caminho do volume persistente para salvar `concursos.db` e backups (ex.: `/data`).
- `COOKIE_SECURE`: defina como `true` quando publicado em `https://`.
- `APP_SECRET_KEY`: chave secreta para assinatura dos cookies de sessão.
- `PORT`: porta HTTP (padrão `8000`).

Consulte o passo a passo completo em [`DEPLOY_NUVEM.md`](DEPLOY_NUVEM.md).

---

## 💻 Execução Local (Windows / Python)

1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
2. Inicie o servidor:
   - Pelo atalho rápido: `run.bat`
   - Ou via terminal: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
3. Acesse `http://localhost:8000`.

### Backup Local
- `criar_backup.bat` — gera backup completo em `backups/` (`.zip` + pasta).
- `restaurar_backup.bat` — restaura um backup anterior com cópia preventiva automática.
- Além disso, o sistema realiza backup automático do banco a cada inicialização em `backups/auto/` (mantendo os 10 últimos).

---

## 🧱 Estrutura do Projeto

- `app/main.py` — API REST (FastAPI), autenticação, painel admin e inteligência de estudos.
- `app/auth.py` — hash `PBKDF2-SHA256` e assinatura de sessão `HMAC`.
- `app/career_templates.py` — trilhas prontas de matérias e pesos (`PM`, `PRF`, `PF`, `PC`, `PP`, `CUSTOM`).
- `app/database.py` — esquema SQLite multi-tenant, modo WAL e índices.
- `app/news_service.py` — sincronização de notícias policiais.
- `app/templates/index.html`, `app/static/js/app.js`, `app/static/css/custom.css`, `app/static/vendor/` — interface tática com ativos locais offline.

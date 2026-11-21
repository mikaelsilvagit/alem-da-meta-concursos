# 🛡️ QAP CONCURSOS v2.0 - Centro de Operações de Estudos Policiais

> *"Treinamento difícil, combate fácil. Missão dada é missão cumprida!"*

O **QAP Concursos v2.0** é uma plataforma completa e moderna desenvolvida sob medida para a preparação de alto rendimento para concursos da **Área Policial** (Polícia Federal, PRF, Polícia Civil, Polícia Militar, Polícia Penal e Perícia Oficial).

O sistema conta com um layout imersivo **Tático / Policial Operacional** (Dark Mode furtivo, paleta fosca militar preta/cinza/aço, métricas de combate e sons táticos integrados via Web Audio API).

---

## ⚡ Como Iniciar o Sistema (1 Clique)

### Opção 1: Executável Rápido (Local e Rede Wi-Fi)
Basta dar um duplo clique no arquivo:
```cmd
run.bat
```
O script detecta o IP da sua máquina, inicia o servidor e abre o sistema automaticamente em `http://localhost:8000`.

### Opção 2: Modo Rede Local com Porta Personalizada (Celular / Tablet)
Dê um duplo clique no arquivo:
```cmd
iniciar_rede_local.bat
```
- Permite escolher a porta desejada (ou simplesmente dar `Enter` para a porta 8000).
- Exibe o endereço completo para acessar no seu celular (ex: `http://192.168.X.X:8000`).

### Opção 3: Linha de Comando (Terminal)
```bash
# Executar na porta padrão (8000)
python run_lan.py

# Ou especificar uma porta personalizada (ex: 8080)
python run_lan.py 8080
```

> **Dica para Acesso no Celular**: Você também pode clicar no botão **`[ ACESSO WI-FI / CELULAR ]`** dentro do Painel de Comando para ver o link da rede e escanear o **QR Code** diretamente com a câmera do seu celular!

---

## 💾 Segurança Operacional: Backup & Restauração (1 Clique)

O sistema conta com rotinas automatizadas para garantir que seu progresso e banco de dados nunca sejam perdidos:

* **Criar Backup Completo:**
  Dê um duplo clique em:
  ```cmd
  criar_backup.bat
  ```
  Isso gera instantaneamente uma pasta e um arquivo `.zip` compactado dentro do diretório `backups/` com data e hora (ex: `backups/backup_v2.0_20261103_212721.zip`), salvando o banco de dados (`concursos.db`), o código-fonte e as configurações.

* **Restaurar Backup:**
  Caso precise voltar a um ponto anterior ou recuperar dados:
  Dê um duplo clique em:
  ```cmd
  restaurar_backup.bat
  ```
  O assistente listará os backups disponíveis e restaurará seu sistema de forma rápida e segura (gerando um backup preventivo automático antes de sobrescrever).

---

## 🎯 Principais Funcionalidades

### 1. 📊 Painel de Comando (Dashboard Operacional)
- **Horas Líquidas de Estudo**: Acompanhe horas estudadas hoje, na semana e acumulado total.
- **Metas Diárias e Semanais**: Barras de prontidão que calculam a porcentagem cumprida da sua meta.
- **Patente Operacional (Gamificação Policial)**: Conforme você acumula horas de estudo, você é promovido de patente:
  - *Recruta Operacional &rarr; Soldado &rarr; Cabo &rarr; Sargento &rarr; Subtenente &rarr; Tenente &rarr; Capitão &rarr; Major &rarr; Coronel &rarr; Delegado Geral / Lenda Policial*.
- **Gráficos Táticos (Chart.js)**:
  - Gráfico de barras neon com histórico dos últimos 14 dias.
  - Gráfico em Donut com distribuição de tempo por matéria.
- **Linha do Tempo Recente**: Histórico detalhado dos últimos turnos de estudos concluídos.

### 2. ⏱️ Plantão de Estudos (Cronômetro & Pomodoro Tático)
- **Cronômetro Livre**: Contador progressivo para sessões livres.
- **Pomodoro Operacional**: Presets de **50min foco / 10min pausa** ou **25min foco / 5min pausa** com alertas sonoros automáticos.
- **Seleção Dinâmica**: Escolha a disciplina e o tópico do edital verticalizado antes de iniciar.
- **Balística em Combate (Contador de Questões em Tempo Real)**:
  - Botão `[ + Acerto ]` (bipe agudo) e `[ + Erro ]` (bipe grave).
  - Cálculo instantâneo do **Índice de Balística / Taxa de Precisão** (`% de acerto`).
- **Agendamento Automático de Revisão**: Ao salvar uma sessão, o sistema já agenda automaticamente a **Revisão de 24 horas** para o dia seguinte!
- **Registro Manual Retroativo**: Permite registrar horas estudadas fora do computador.

### 3. 📂 Dossiê de Matérias (Edital Esquematizado e Verticalizado)
Disciplinas policiais padrão já pré-carregadas com dezenas de tópicos oficiais:
- 🔴 **Direito Penal** (Teoria do crime, ilicitude, crimes contra pessoa, patrimônio e administração)
- 🟠 **Direito Processual Penal** (Inquérito, ação penal, prisões cautelares, provas, cadeia de custódia)
- 🔵 **Direito Constitucional** (Art. 5º direitos fundamentais, Art. 144 segurança pública, poderes)
- 🌐 **Direito Administrativo** (LIMPE, poder de polícia, atos administrativos, improbidade, licitações)
- 🟣 **Legislação Penal Especial** (Drogas, Desarmamento, Abuso de Autoridade, Hediondos, Organizações Criminosas)
- 🟢 **Língua Portuguesa** (Interpretação, morfossintaxe, concordância, crase, redação oficial)
- 🟡 **Raciocínio Lógico & Matemática** (Proposições, equivalências, combinatória, probabilidade)
- 🟣 **Informática & Cibersegurança** (Segurança da informação, redes, Linux/Windows, Python/SQL)
- 🟢 **Contabilidade Geral** (Específica PF Agente)
- 🔴 **Legislação de Trânsito / CTB** (Específica PRF)
- *Checklist interativo por tópico*: marque **Teoria**, **Resumo** e **Questões**.
- Adicione novas matérias ou tópicos personalizados a qualquer momento!

### 4. 🔄 Protocolo de Retenção Tática (Revisões Espaçadas)
- Baseado na **Curva do Esquecimento de Ebbinghaus**:
  - **R1 (24 Horas)** &rarr; **R2 (7 Dias)** &rarr; **R3 (15 Dias)** &rarr; **R4 (30 Dias)** &rarr; **Concluído**.
- Abas organizadas: *Vencendo Hoje*, *Atrasadas (Alerta Vermelho)*, *Próximos 7 Dias* e *Concluídas*.
- Botão de 1 clique **[ CUMPRIR REVISÃO (QAP!) ]**: O sistema marca a etapa como concluída e calcula e agenda automaticamente a próxima repetição espaçada!

### 5. 📰 Central de Notícias & Inteligência Policial (Estratégia, Gran Cursos & Doutrina)
- **100% Exclusivo da Carreira Policial**: Focado exclusivamente nas forças de segurança (**Polícia Federal, PRF, Polícia Civil, Polícia Militar, Polícia Penal, Perícia Oficial e Guardas Municipais**).
- **Sistema de Priorização Operacional Tática**:
  - 🔴 **Prioridade Maior (Alta)**: *Editais Abertos, Lançados e Prazos de Inscrição* (destaque urgente).
  - ⚡ **Prioridade Média**: *Bancas Definidas (Cebraspe, FGV, Vunesp, etc.), Autorizações Ministeriais e Editais Iminentes*.
  - 📋 **Prioridade Normal**: *Comissões Formadas, Recomposição de Efetivos, Orientações de TAF e Doutrina*.
- **Filtros Táticos Rápidos**: Permite alternar entre *Todas as Notícias*, *Maior (Editais Abertos)*, *Média (Iminentes)* e *Normal (Comissões & TAF)* com um clique.
- **Leitura Direta**: Links rápidos para abrir a matéria completa no portal oficial.

### 6. 🎯 Métricas de Combate & Simulados
- Registro e controle de simulados completos:
  - Total de questões, acertos, erros e **nota líquida**.
  - Comparativo com nota de corte e anotação de pontos fracos para reforço.

### 7. 💻 Arsenal Tático (Bancos de Questões & Videoaulas)
- Área dedicada para centralizar todos os seus sites de estudo:
  - **Bancos de Questões**: Tec Concursos, QConcursos...
  - **Cursos & Videoaulas**: Estratégia Concursos, Gran Cursos, YouTube (Canais Policiais), DSO Concursos...
  - **Jurisprudência & Legislação**: Dizer o Direito, Jusbrasil...
  - **Simulados Inéditos**: Projeto Caveira...
- **Dock de Acesso Rápido Integrado ao Cronômetro**: Durante qualquer turno de estudo ou pomodoro, um dock de links rápidos fica ativo para você abrir seu banco de questões ou aula em 1 clique sem fechar o cronômetro!
- Permite adicionar, editar ou excluir qualquer plataforma ou link com botão `[ + ADICIONAR PLATAFORMA ]`.

### 8. 🏅 Quadro de Honra & Conquistas (Aprovações Anteriores)
- Registre e eternize suas aprovações e fases superadas (concursos municipais, estaduais, TAFs superados, vestibulares).
- Mostra **Ano**, **Cargo**, **Colocação**, **Pontuação/Nota** e insígnias de honra.
- Reforço psicológico e mental para os dias mais difíceis de estudo.

### 9. 🏃‍♂️ Módulo TAF Operacional (Aptidão Física Policial)
- O concurseiro policial precisa treinar o corpo junto com os estudos!
- Registre treinos e simulados de:
  - **Barra Fixa** (repetições ou isometria).
  - **Corrida de 12 Minutos** (distância em metros).
  - **Abdominal Remador** (repetições em 1 min).
  - **Flexão de Braço**.
  - **Natação 50m** (específica para Polícia Federal).
- **Avaliação Automática nos Padrões Cebraspe / PF / PRF**: O sistema calcula se cada índice e o resultado geral estão **APTO** ou **INAPTO**.

### 10. ⏳ Contagem Regressiva do "Dia D" (Operação Prova)
- Relógio tático digital HUD em destaque no Painel de Comando:
  - Contagem regressiva ao vivo em **DIAS, HORAS, MINUTOS e SEGUNDOS** para o dia da prova do seu concurso alvo.
  - Botão de 1 clique para configurar ou alterar a data e o horário da prova.

### 11. ⚖️ Radar de Lei Seca & Artigos Lidos
- 70% a 80% das questões de Direito em provas policiais cobram a **letra da lei**.
- Registro diário de artigos lidos da **CF/88**, **Código Penal**, **CPP** e **Leis Especiais Policiais**.
- Botões de registro rápido (`+10 Artigos CF/88`, `+15 Artigos Código Penal`, etc.) e gráfico de distribuição por código.

### 13. 🔄 Como Zerar o Painel (Reinício Operacional)
- Botão rápido **[ ZERAR PAINEL ]** presente na barra de ações rápidas do Painel de Comando e no menu de Configurações.
- Permite zerar de forma granular com confirmação de segurança:
  - `[x]` Zerar horas estudadas, turnos e contador de questões (retorna a patente para Recruta Operacional Nível 1).
  - `[ ]` Limpar agendamentos de revisões espaçadas.
  - `[ ]` Desmarcar checklists de tópicos (Teoria, Resumo, Questões).
  - `[ ]` Zerar histórico de simulados.

### 14. 🎧 Efeitos Sonoros Táticos (Web Audio API)
- Bipes de rádio operacional discretos ao iniciar o plantão, marcar acertos/erros e cumprir missões.
- Totalmente nativo no navegador (sem necessidade de baixar arquivos de áudio pesados).
- Opção de ativar ou silenciar a qualquer momento nas configurações.

### 15. 📕 Caderno de Erros Operacional (Dossiê de Vulnerabilidades)
- Ferramenta indispensável para concurseiros de alta performance: catalogue cada questão que você errou ou teve dúvida.
- **Marcação por Banca**: Cebraspe, FGV, Vunesp, FCC, IBFC e outras.
- **Classificação da Falha**: *Pegadinha de Banca*, *Falta de Atenção*, *Lacuna Teórica* ou *Interpretação de Texto*.
- **Campo de Bizu Corretivo**: O que a banca tentou fazer e a regra para nunca mais cair na pegadinha.
- **Status "Dominado / Superado"**: Conforme você revisa seus erros, marque como dominado e blinde suas fragilidades.

### 16. 🔄 Ciclo Tático Inteligente (Algoritmo de Próxima Missão)
- Acabe com a dúvida de "o que estudar agora?".
- O algoritmo calcula a pontuação de prioridade com base nos **dias sem estudar a matéria** e no **déficit em relação à meta de horas**.
- Banner em destaque no topo do Painel de Comando: basta clicar em **[ ENTRAR EM MISSÃO ]** para que a matéria e o tópico sejam carregados no cronômetro automaticamente!

### 17. ✍️ Oficina de Discursivas & Redações Policiais
- As provas da PF, PRF, Polícias Civis e Penais exigem discursivas de alto nível (geralmente valendo 20 a 30 pontos cruciais).
- **Banco de Temas Quentes**: 6 temas pré-carregados baseados no histórico recente (ex: *Crime Organizado e Lavagem de Capitais*, *Cadeia de Custódia da Prova*, *Segurança Viária e Sinistros*, *Uso Diferenciado da Força*, etc.).
- **Simulador de 60 Minutos**: Botão que configura o cronômetro para 60 minutos de foco total com folha de rascunho e caneta.
- **Boletim de Redações**: Controle data, órgão, número de linhas, nota obtida e anotações/correções do professor.

### 18. 💾 Backup & Relatório Operacional em PDF / Impressão
- **Exportação JSON em 1 Clique**: Salve todos os seus dados (disciplinas, turnos, revisões, TAF, redações, caderno de erros) em um arquivo `.json` local.
- **Restauração de Backup**: Importe backups anteriores a qualquer momento pelo botão `[ RESTAURAR ]`.
- **Boletim Operacional para Impressão**: Botão `[ IMPRIMIR BOLETIM ]` formatado com regras `@media print` de alta legibilidade para gerar PDF limpo ou imprimir seu relatório de evolução.

### 19. 🌊 Modo Foco Sonoro Tático (Áudio de Hiperfoco Offline)
- Sintetizador direto via **Web Audio API** no navegador, sem carregar arquivos MP3 externos (funciona 100% offline):
  - **Ruído Marrom (Brown Noise)**: Frequências graves contínuas para estudo profundo (Deep Focus).
  - **Ruído Branco (White Noise)**: Bloqueio acústico total de conversas ou barulhos da vizinhança.
  - **Chuva Tática Operacional**: Simulação de ruído relaxante e constante.
  - **Ondas Binaurais Gama (40 Hz)**: Frequência associada a foco cognitivo e retenção de memória.
- Controle de volume deslizante e indicador animado de ondas sonoras no dock do cronômetro.

### 20. ✏️ Edição Completa de Registros Operacionais (CRUD Granular)
- Permite editar qualquer registro sem precisar apagar e recadastrar do zero:
  - **Turnos de Estudo**: Corrija disciplina, tópico, data, minutos estudados e balística de questões certas/erradas.
  - **Caderno de Erros**: Ajuste banca, referências, enunciados e bizus corretivos com facilidade.
  - **Métricas de Simulados**: Atualize nota líquida, total de itens, acertos e observações.
  - **Dossiê de Matérias**: Edite nomes de tópicos e anotações teóricas do edital.

### 21. 🔍 Radar de Busca Global Instantânea (Command Palette `Ctrl + K`)
- Atalho tático universal (`Ctrl + K` no PC ou botão de busca no cabeçalho e mobile):
  - Varredura em tempo real em tópicos do edital, bizus do caderno de erros, notícias, certames do radar e simulados.
  - Filtros rápidos por categoria (*Dossiê, Erros, Editais, Notícias, Simulados*).
  - Salto imediato com destaque visual iluminado no item encontrado.

### 22. 📊 Exportação de Dados para Excel & Planilhas (CSV UTF-8)
- Botões de exportação em 1 clique devidamente configurados com UTF-8 BOM e separador `;` para compatibilidade imediata com o Microsoft Excel e Google Sheets:
  - **Exportar Sessões**: Histórico completo com data, matéria, tempo em minutos/horas e percentual de precisão.
  - **Exportar Caderno de Erros**: Relação de vulnerabilidades, enunciados, bancas e bizus de memorização.
  - **Exportar Simulados**: Relatório de combate com pontuação líquida e taxa de aproveitamento.

---

## 🛠️ Tecnologias Utilizadas

- **Backend**: Python 3.15 + FastAPI + SQLite3 + Uvicorn + Jinja2 + HTTPX.
- **Frontend**: Single-Page Application responsiva com Tailwind CSS, FontAwesome 6, Chart.js e Web Audio API.
- **Banco de Dados**: SQLite local (`concursos.db`), garantindo que seus dados nunca se percam e funcionem 100% offline.

---

*QAP Concursos &bull; Disciplina é Liberdade &bull; Força e Honra.*

import datetime
from app.database import get_db, is_system_seeded

def seed_initial_data():
    if is_system_seeded():
        return
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check if already seeded
        cursor.execute("SELECT COUNT(*) as count FROM subjects")
        if cursor.fetchone()["count"] > 0:
            return

        print("Seeding initial police study data...")
        
        # 1. SUBJECTS AND TOPICS
        subjects_data = [
            {
                "name": "Direito Penal",
                "category": "Jurídica",
                "color": "#ef4444", # Red
                "icon": "fa-handcuffs",
                "target_hours": 60.0,
                "topics": [
                    "Aplicação da Lei Penal (Tempo, Lugar e Territorialidade)",
                    "Teoria do Crime: Fato Típico, Ilicitude e Culpabilidade",
                    "Tentativa, Consumação, Desistência e Arrependimento",
                    "Concurso de Pessoas (Coautoria e Participação)",
                    "Crimes Contra a Pessoa (Homicídio, Lesão Corporal)",
                    "Crimes Contra o Patrimônio (Furto, Roubo, Extorsão, Estelionato)",
                    "Crimes Contra a Dignidade Sexual",
                    "Crimes Contra a Administração Pública (Peculato, Concussão, Corrupção)"
                ]
            },
            {
                "name": "Direito Processual Penal",
                "category": "Jurídica",
                "color": "#f97316", # Orange
                "icon": "fa-scale-balanced",
                "target_hours": 50.0,
                "topics": [
                    "Inquérito Policial (Natureza, Características, Notitia Criminis e Prazos)",
                    "Ação Penal (Pública Incondicionada, Condicionada e Privada)",
                    "Prisão em Flagrante (Espécies, Prazos e Audiência de Custódia)",
                    "Prisão Preventiva e Prisão Temporária (Requisitos e Prazos)",
                    "Medidas Cautelares Diversas da Prisão",
                    "Provas: Exame de Corpo de Delito, Busca e Apreensão, Interceptação Telefônica",
                    "Cadeia de Custódia da Prova (Lei Pacote Anticrime)",
                    "Sujeitos Processuais e Juiz das Garantias"
                ]
            },
            {
                "name": "Direito Constitucional",
                "category": "Jurídica",
                "color": "#3b82f6", # Blue
                "icon": "fa-landmark",
                "target_hours": 50.0,
                "topics": [
                    "Direitos e Garantias Fundamentais (Art. 5º - Vida, Liberdade, Igualdade)",
                    "Remédios Constitucionais (HC, MS, MI, HD, Ação Popular)",
                    "Segurança Pública (Artigo 144 - PF, PRF, PFF, PC, PM, CBM, PP e Guardas)",
                    "Organização Político-Administrativa do Estado e Competências",
                    "Poder Executivo e Atribuições do Presidente da República",
                    "Defesa do Estado e das Instituições Democráticas (Estado de Defesa e Sítio)"
                ]
            },
            {
                "name": "Direito Administrativo",
                "category": "Jurídica",
                "color": "#06b6d4", # Cyan
                "icon": "fa-building-columns",
                "target_hours": 45.0,
                "topics": [
                    "Princípios Expressos e Implícitos (LIMPE e Proporcionalidade)",
                    "Poderes da Administração e Poder de Polícia (Atributos e Fases)",
                    "Atos Administrativos (Elementos, Atributos, Extinção e Revogação)",
                    "Responsabilidade Civil do Estado (Teoria do Risco Administrativo)",
                    "Regime Jurídico dos Servidores Públicos Civis (Lei 8.112/90)",
                    "Improbidade Administrativa (Lei 8.429/92 atualizada)",
                    "Licitações e Contratos (Nova Lei 14.133/21 - Visão Geral)"
                ]
            },
            {
                "name": "Legislação Penal Especial",
                "category": "Jurídica",
                "color": "#8b5cf6", # Purple
                "icon": "fa-gun",
                "target_hours": 55.0,
                "topics": [
                    "Lei de Drogas (Lei nº 11.343/2006 - Posse, Tráfico e Procedimento)",
                    "Estatuto do Desarmamento (Lei nº 10.826/2003 - Posse, Porte e Disparo)",
                    "Abuso de Autoridade (Lei nº 13.869/2019 - Sujeitos e Crimes Típicos)",
                    "Crimes Hediondos (Lei nº 8.072/1990 - Rol e Regime)",
                    "Organizações Criminosas (Lei nº 12.850/2013 - Colaboração Premiada e Infiltração)",
                    "Tortura (Lei nº 9.455/1997)",
                    "Lei Maria da Penha (Lei nº 11.340/2006 - Medidas Protetivas de Urgência)"
                ]
            },
            {
                "name": "Língua Portuguesa",
                "category": "Básica",
                "color": "#10b981", # Green
                "icon": "fa-book-bookmark",
                "target_hours": 60.0,
                "topics": [
                    "Interpretação e Compreensão de Textos (Tipologias e Gêneros)",
                    "Ortografia Oficial e Regras de Acentuação Gráfica",
                    "Classes de Palavras (Verbo, Substantivo, Adjetivo, Pronomes)",
                    "Sintaxe da Oração e do Período (Termos Essenciais e Integrantes)",
                    "Concordância Verbal e Nominal",
                    "Regência Verbal e Emprego do Sinal Indicativo de Crase",
                    "Pontuação (Emprego da Vírgula e Ponto e Vírgula)",
                    "Manual de Redação da Presidência da República"
                ]
            },
            {
                "name": "Raciocínio Lógico & Mat.",
                "category": "Básica",
                "color": "#eab308", # Amber
                "icon": "fa-brain",
                "target_hours": 40.0,
                "topics": [
                    "Lógica Proposicional: Proposições Simples e Compostas, Conectivos",
                    "Tabelas-Verdade, Tautologias, Contradições e Contingências",
                    "Equivalências e Negações Lógicas (Leis de De Morgan)",
                    "Diagramas Lógicos, Conjuntos e Argumentação",
                    "Análise Combinatória (Permutação, Arranjo e Combinação)",
                    "Probabilidade Básica e Condicional"
                ]
            },
            {
                "name": "Informática Policial & Investigação Digital",
                "category": "Específica",
                "color": "#6366f1", # Indigo
                "icon": "fa-network-wired",
                "target_hours": 55.0,
                "topics": [
                    "Sistemas Operacionais (Conceitos Windows 10/11 e Fundamentos do Linux para Servidores)",
                    "Redes de Computadores (Arquitetura TCP/IP, Endereçamento IPv4/IPv6, DNS, DHCP e Roteamento)",
                    "Segurança da Informação (Princípios CID, Criptografia Simétrica e Assimétrica, Assinatura Digital)",
                    "Ameaças Cibernéticas & Malwares (Vírus, Worms, Trojans, Ransomwares, Phishing e Engenharia Social)",
                    "Mecanismos de Defesa (Firewalls, IDS/IPS, Antivírus e Políticas de Backup)",
                    "Computação em Nuvem (Modelos IaaS, PaaS, SaaS e Armazenamento em Nuvem)",
                    "Navegação Segura, Deep Web, Dark Web e Rastreabilidade de Crimes Eletrônicos",
                    "Ferramentas de Produtividade e Manipulação de Dados (Planilhas e Editores de Texto)"
                ]
            },
            {
                "name": "Noções de Direitos Humanos",
                "category": "Específica",
                "color": "#ec4899", # Pink
                "icon": "fa-hand-holding-heart",
                "target_hours": 35.0,
                "topics": [
                    "Conceito, Evolução Histórica e Características dos Direitos Humanos",
                    "Declaração Universal dos Direitos Humanos (DUDH de 1948 - Princípios e Artigos Fundamentais)",
                    "Convenção Americana sobre Direitos Humanos (Pacto de San José da Costa Rica)",
                    "Os Direitos Humanos na Constituição Federal de 1988 e a Segurança Cidadã",
                    "Grupos Vulneráveis, Diversidade, Igualdade Racial e Prevenção à Violência Institucional",
                    "Uso Diferenciado da Força, Princípios da Proporcionalidade e Preservação da Vida nas Ações Policiais"
                ]
            },
            {
                "name": "Legislação do Tocantins & Estatuto da PC-TO",
                "category": "Específica",
                "color": "#f59e0b", # Amber Gold
                "icon": "fa-certificate",
                "target_hours": 45.0,
                "topics": [
                    "Estatuto dos Policiais Civis do Estado do Tocantins (Lei Estadual nº 1.654/2006: Provimento, Deveres e Regime Disciplinar)",
                    "Estatuto dos Servidores Públicos Civis do Tocantins (Lei Estadual nº 1.818/2007: Direitos, Vantagens e Responsabilidades)",
                    "Constituição do Estado do Tocantins (Disposições sobre a Segurança Pública e Polícia Civil)",
                    "Estrutura Orgânica da Secretaria de Segurança Pública do Tocantins (SSP/TO) e Delegacias Regionais",
                    "Formação Histórica e Geográfica do Tocantins (Criação do Estado, Ciclos Econômicos, Demografia e Bacias Hidrográficas)"
                ]
            },
            {
                "name": "Noções de Medicina Legal & Criminalística",
                "category": "Específica",
                "color": "#14b8a6", # Teal
                "icon": "fa-microscope",
                "target_hours": 35.0,
                "topics": [
                    "Introdução à Medicina Legal e Documentos Médico-Legais (Relatório, Laudo, Parecer e Atestado)",
                    "Traumatologia Forense (Lesões por Instrumentos Contundentes, Cortantes, Perfurantes e Perfurocontundentes)",
                    "Tanatologia Forense (Conceito de Morte, Sinais de Morte, Cronotanatognose e Fenômenos Cadavéricos)",
                    "Asfixiologia Forense (Enforcamento, Estrangulamento, Esganadura e Afogamento)",
                    "Criminalística de Campo: Local de Crime (Idoneidade, Preservação, Isolamento e Vestígios Materiais)",
                    "Balística Forense e Identificação de Armas de Fogo e Munições"
                ]
            }
        ]

        for s in subjects_data:
            cursor.execute("""
            INSERT INTO subjects (name, category, color, icon, target_hours)
            VALUES (?, ?, ?, ?, ?)
            """, (s["name"], s["category"], s["color"], s["icon"], s["target_hours"]))
            subject_id = cursor.lastrowid
            
            for t_name in s["topics"]:
                cursor.execute("""
                INSERT INTO topics (subject_id, name)
                VALUES (?, ?)
                """, (subject_id, t_name))

        # 3. POLICE NEWS FEED
        today = datetime.date.today().strftime("%d/%m/%Y")
        yesterday = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%d/%m/%Y")
        news_data = [
            {
                "title": "Concurso Polícia Federal: Minuta do edital avança e previsão é de publicação de cronograma em breve",
                "source": "Boletim Operacional / Notícias Policiais",
                "category": "Federal",
                "link": "https://www.gov.br/pf/pt-br",
                "pub_date": today,
                "summary": "Comissão organizadora acelera tratativas para certame com vagas para Agente, Escrivão e Administrativo. Ênfase em cibersegurança e inteligência policial.",
                "is_pinned": 1
            },
            {
                "title": "PRF confirma necessidade de recomposição do efetivo e planeja novo Curso de Formação Profissional (CFP)",
                "source": "Notícias Táticas",
                "category": "Federal",
                "link": "https://www.gov.br/prf/pt-br",
                "pub_date": today,
                "summary": "Academia Nacional da PRF em Florianópolis já estrutura infraestrutura para receber novas turmas de policiais operacionais.",
                "is_pinned": 1
            },
            {
                "title": "Polícia Civil de SP divulga diretrizes para modernização das provas e inclusão de estudos de caso",
                "source": "Diário Oficial do Estado de SP",
                "category": "Civil",
                "link": "https://www.policiacivil.sp.gov.br",
                "pub_date": yesterday,
                "summary": "A banca examinadora cobrará maior domínio prático da investigação cibernética e legislação penal extravagante.",
                "is_pinned": 0
            },
            {
                "title": "Dicas para o TAF (Teste de Aptidão Física): Barra fixa, corrida de 12 minutos e natação",
                "source": "Manual de Prontidão Tática",
                "category": "Preparação",
                "link": "#",
                "pub_date": yesterday,
                "summary": "Especialistas orientam conciliar a planilha de estudos com o condicionamento aeróbico e força isométrica desde o primeiro dia de preparação.",
                "is_pinned": 0
            },
            {
                "title": "PCDF abre inscrições para certame com remuneração inicial superior a R$ 11 mil reais",
                "source": "Folha dos Concursos",
                "category": "Civil",
                "link": "https://www.pcdf.df.gov.br",
                "pub_date": yesterday,
                "summary": "Candidatos devem conferir cronograma oficial e distribuição de vagas para ampla concorrência e cotas.",
                "is_pinned": 0
            }
        ]

        for n in news_data:
            cursor.execute("""
            INSERT INTO news_feed (title, source, category, link, pub_date, summary, is_pinned)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (n["title"], n["source"], n["category"], n["link"], n["pub_date"], n["summary"], n["is_pinned"]))

        # 4. INITIAL REVISIONS (So the user immediately tests the spaced revision workflow)
        today_iso = datetime.date.today().strftime("%Y-%m-%d")
        tomorrow_iso = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        in_3_days_iso = (datetime.date.today() + datetime.timedelta(days=3)).strftime("%Y-%m-%d")
        
        # Get subject ids
        cursor.execute("SELECT id, name FROM subjects WHERE name LIKE 'Direito Penal%' LIMIT 1")
        penal = cursor.fetchone()
        cursor.execute("SELECT id, name FROM subjects WHERE name LIKE 'Direito Constitucional%' LIMIT 1")
        const = cursor.fetchone()
        cursor.execute("SELECT id, name FROM subjects WHERE name LIKE 'Informática%' LIMIT 1")
        info = cursor.fetchone()

        if penal:
            cursor.execute("""
            INSERT INTO revisions (subject_id, title, scheduled_date, interval_stage, notes)
            VALUES (?, ?, ?, 1, ?)
            """, (penal["id"], "Revisão 24h: Teoria do Crime e Ilicitude", today_iso, "Revisar excludentes de ilicitude (Legítima Defesa, Estado de Necessidade, Estrito Cumprimento do Dever Legal)."))
            
        if const:
            cursor.execute("""
            INSERT INTO revisions (subject_id, title, scheduled_date, interval_stage, notes)
            VALUES (?, ?, ?, 2, ?)
            """, (const["id"], "Revisão 7 Dias: Artigo 144 - Segurança Pública", today_iso, "Revisar órgãos da segurança pública, subordinação das polícias e competências da PF e PRF."))

        if info:
            cursor.execute("""
            INSERT INTO revisions (subject_id, title, scheduled_date, interval_stage, notes)
            VALUES (?, ?, ?, 3, ?)
            """, (info["id"], "Revisão 15 Dias: Segurança da Informação e Criptografia", in_3_days_iso, "Revisar hashes, chaves públicas/privadas e tipos de malware."))

        # 5. INITIAL STUDY SESSIONS (to have live charts on startup)
        yesterday_iso = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        two_days_ago = (datetime.date.today() - datetime.timedelta(days=2)).strftime("%Y-%m-%d")
        
        if penal:
            cursor.execute("""
            INSERT INTO study_sessions (subject_id, date, start_time, duration_seconds, questions_correct, questions_incorrect, notes)
            VALUES (?, ?, '14:00', 5400, 24, 4, 'Resolução de questões Cebraspe sobre Teoria do Crime. Ótimo aproveitamento.')
            """, (penal["id"], yesterday_iso))

        if const:
            cursor.execute("""
            INSERT INTO study_sessions (subject_id, date, start_time, duration_seconds, questions_correct, questions_incorrect, notes)
            VALUES (?, ?, '19:30', 7200, 32, 3, 'Estudo aprofundado do Artigo 5º e 144 da CF/88. Leitura da jurisprudência do STF.')
            """, (const["id"], two_days_ago))

        print("Seeding completed successfully!")

def seed_platforms():
    """Seeds default study platforms if empty."""
    if is_system_seeded():
        return
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM study_platforms")
        if cursor.fetchone()["count"] > 0:
            return

        platforms = [
            {
                "title": "Tec Concursos",
                "url": "https://www.tecconcursos.com.br",
                "category": "Banco de Questões",
                "icon": "fa-list-check",
                "color": "#3b82f6",
                "notes": "Filtros avançados por bancas policiais (Cebraspe, FGV, Vunesp), guias de estudo e comentários de professores.",
                "is_pinned": 1
            },
            {
                "title": "QConcursos",
                "url": "https://www.qconcursos.com",
                "category": "Banco de Questões",
                "icon": "fa-circle-question",
                "color": "#06b6d4",
                "notes": "Milhares de questões comentadas pela comunidade, simulados e estatísticas de resolução.",
                "is_pinned": 1
            },
            {
                "title": "Estratégia Concursos",
                "url": "https://www.estrategiaconcursos.com.br",
                "category": "Videoaulas & Cursos",
                "icon": "fa-graduation-cap",
                "color": "#f59e0b",
                "notes": "PDFs completos, videoaulas direcionadas, Passo Estratégico e Bizus para carreiras policiais.",
                "is_pinned": 1
            },
            {
                "title": "Gran Cursos Online",
                "url": "https://www.grancursosonline.com.br",
                "category": "Videoaulas & Cursos",
                "icon": "fa-video",
                "color": "#ef4444",
                "notes": "Aulas em vídeo, degravações em PDF, mapas mentais e cronogramas de estudo.",
                "is_pinned": 1
            },
            {
                "title": "YouTube (Aulas Policiais)",
                "url": "https://www.youtube.com",
                "category": "Videoaulas & Cursos",
                "icon": "fa-play",
                "color": "#e11d48",
                "notes": "Revisões de véspera gratuitas, maratonas de exercícios ao vivo e preparação para o TAF.",
                "is_pinned": 1
            },
            {
                "title": "Dizer o Direito",
                "url": "https://www.dizerodireito.com.br",
                "category": "Jurisprudência",
                "icon": "fa-gavel",
                "color": "#8b5cf6",
                "notes": "Informativos do STF e STJ esquematizados pelo Juiz Márcio André Lopes Cavalcante. Indispensável para Carreiras Policiais.",
                "is_pinned": 1
            },
            {
                "title": "Jusbrasil (Legislação)",
                "url": "https://www.jusbrasil.com.br/legislacao",
                "category": "Jurisprudência",
                "icon": "fa-scale-balanced",
                "color": "#10b981",
                "notes": "Consulta rápida à Constituição Federal, Código Penal, CPP e Leis Especiais atualizadas.",
                "is_pinned": 0
            },
            {
                "title": "Projeto Caveira",
                "url": "https://projetocaveira.com.br",
                "category": "Simulados",
                "icon": "fa-skull",
                "color": "#64748b",
                "notes": "Simulados inéditos com ranking e notas de corte específicos para PF, PRF e Polícias Civis.",
                "is_pinned": 1
            },
            {
                "title": "DSO Concursos",
                "url": "https://dsoconcursos.com.br",
                "category": "Videoaulas & Cursos",
                "icon": "fa-shield-halved",
                "color": "#d97706",
                "notes": "Aulas de Direito Penal, Processo Penal e Legislação do Prof. Juliano Cesar voltadas para a prática operacional.",
                "is_pinned": 0
            }
        ]

        for p in platforms:
            cursor.execute("""
            INSERT INTO study_platforms (title, url, category, icon, color, notes, is_pinned)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (p["title"], p["url"], p["category"], p["icon"], p["color"], p["notes"], p["is_pinned"]))
            
        print(f"Seeded {len(platforms)} study platforms successfully!")

def seed_tactical_expansions():
    """Seeds sample data for Approvals, TAF, Countdown and Law Reading."""
    if is_system_seeded():
        return
    today = datetime.date.today().strftime("%Y-%m-%d")
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 1. Approvals
        cursor.execute("SELECT COUNT(*) as count FROM approvals")
        if cursor.fetchone()["count"] == 0:
            cursor.execute("""
            INSERT INTO approvals (contest_name, role, year, position, score, status, badge_icon, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "Polícia Militar de São Paulo (PMESP)",
                "Soldado PM de 2ª Classe",
                2024,
                "148º Colocado",
                "76.0 / 100",
                "Classificado & Apto no TAF",
                "fa-trophy",
                "Aprovado na prova objetiva e apto em todas as fases do TAF (barra, corrida e tiro de 50m)."
            ))
            cursor.execute("""
            INSERT INTO approvals (contest_name, role, year, position, score, status, badge_icon, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "Guarda Civil Municipal (GCM)",
                "Guarda Civil 3ª Classe",
                2023,
                "35º Lugar",
                "82.5 pts",
                "Aprovado",
                "fa-medal",
                "Excelente resultado na prova objetiva com 90% de acertos em Legislação e Português."
            ))
            
        # 2. TAF records
        cursor.execute("SELECT COUNT(*) as count FROM taf_records")
        if cursor.fetchone()["count"] == 0:
            cursor.execute("""
            INSERT INTO taf_records (date, pull_ups, run_12min_meters, sit_ups, push_ups, swim_50m_seconds, is_male, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                yesterday,
                6,       # 6 barras (padrão PF/PRF aprovado)
                2450,    # 2.450m corrida (padrão PF/PRF aprovado)
                42,      # 42 abdominais remador
                36,      # 36 flexões
                46.5,    # 46.5s natação 50m (abaixo do teto de 56s da PF)
                1,
                "Simulado de TAF completo na pista de atletismo. Índice excelente para a Polícia Federal e PRF!"
            ))

        # 3. Countdown (Dia D)
        cursor.execute("SELECT COUNT(*) as count FROM exam_countdowns")
        if cursor.fetchone()["count"] == 0:
            # Set countdown 45 days in future
            target_date = (datetime.date.today() + datetime.timedelta(days=45)).strftime("%Y-%m-%d")
            cursor.execute("""
            INSERT INTO exam_countdowns (title, target_date, target_time, is_active)
            VALUES (?, ?, '08:00', 1)
            """, ("Operação Polícia Federal - Dia D", target_date))

        # 4. Law Reading Tracker
        cursor.execute("SELECT COUNT(*) as count FROM law_reading_logs")
        if cursor.fetchone()["count"] == 0:
            cursor.execute("""
            INSERT INTO law_reading_logs (date, code_name, articles_read, notes)
            VALUES (?, ?, ?, ?)
            """, (today, "Constituição Federal (CF/88)", 20, "Artigos 1º ao 17 (Direitos e Deveres Individuais e Coletivos)"))
            cursor.execute("""
            INSERT INTO law_reading_logs (date, code_name, articles_read, notes)
            VALUES (?, ?, ?, ?)
            """, (yesterday, "Código Penal (CP)", 25, "Artigos 1º ao 25 (Aplicação da lei e Teoria do Crime)"))

        # 5. Caderno de Erros
        cursor.execute("SELECT COUNT(*) as count FROM error_notebook")
        if cursor.fetchone()["count"] == 0:
            cursor.execute("SELECT id FROM subjects WHERE name LIKE 'Direito Penal%' LIMIT 1")
            penal_row = cursor.fetchone()
            cursor.execute("SELECT id FROM subjects WHERE name LIKE 'Direito Processual Penal%' LIMIT 1")
            cpp_row = cursor.fetchone()
            cursor.execute("SELECT id FROM subjects WHERE name LIKE 'Direito Constitucional%' LIMIT 1")
            const_row = cursor.fetchone()

            if penal_row:
                cursor.execute("""
                INSERT INTO error_notebook (subject_id, banca, question_ref, error_reason, question_statement, bizu_notes, mastered)
                VALUES (?, 'Cebraspe', 'PF Agente 2021', 'Pegadinha de Banca', 
                        'A tentativa é admissível em crimes culposos quando houver culpa consciente.',
                        'BIZU CEBRASPE: Crimes culposos NÃO admitem tentativa em regra! A única exceção doutrinária é a culpa imprópria (erro de tipo inescusável), mas a banca considerou errada a assertiva genérica.', 0)
                """, (penal_row["id"],))

            if cpp_row:
                cursor.execute("""
                INSERT INTO error_notebook (subject_id, banca, question_ref, error_reason, question_statement, bizu_notes, mastered)
                VALUES (?, 'Cebraspe', 'PRF 2019', 'Falta de Atenção',
                        'O delegado de polícia poderá determinar o arquivamento do inquérito policial se constatar atipicidade manifesta.',
                        'BIZU DE OURO (Art. 17 do CPP): A autoridade policial JAMAIS poderá mandar arquivar autos de inquérito. O arquivamento é ato exclusivo do Judiciário mediante manifestação do MP!', 0)
                """, (cpp_row["id"],))

            if const_row:
                cursor.execute("""
                INSERT INTO error_notebook (subject_id, banca, question_ref, error_reason, question_statement, bizu_notes, mastered)
                VALUES (?, 'FGV', 'PC-SP Escrivão', 'Falta de Lei Seca',
                        'A casa é asilo inviolável, não podendo nela penetrar sem consentimento, salvo durante a noite por determinação judicial.',
                        'BIZU CF/88 (Art. 5º, XI): Durante a NOITE, apenas com flagrante delito, desastre ou socorro. Mandado judicial APENAS DURANTE O DIA!', 1)
                """, (const_row["id"],))

        # 6. Discursive essays & Prompts
        cursor.execute("SELECT COUNT(*) as count FROM discursive_essays")
        if cursor.fetchone()["count"] == 0:
            cursor.execute("""
            INSERT INTO discursive_essays (title, date, agency, lines_count, score, max_score, notes)
            VALUES (?, ?, 'Polícia Federal', 30, 18.2, 20.0, 'Excelente estruturação de parágrafos. Atenção aos conectivos interparágrafos.')
            """, ("O papel da Polícia Federal no combate aos crimes cibernéticos e às organizações criminosas na era digital", yesterday))

        cursor.execute("SELECT COUNT(*) as count FROM essay_prompts")
        if cursor.fetchone()["count"] == 0:
            prompts = [
                {
                    "title": "A atuação das forças policiais no enfrentamento ao crime organizado e o controle das fronteiras nacionais",
                    "agency": "Polícia Federal / PRF",
                    "axis": "Crime Organizado & Fronteiras",
                    "description": "Aborde: 1) A relevância da integração de inteligência entre PF, PRF e Forças Armadas; 2) O impacto do tráfico transnacional de armas e drogas na segurança pública urbana; 3) Propostas para o fortalecimento do Sistema de Fronteiras (Sisfron)."
                },
                {
                    "title": "O avanço dos crimes cibernéticos: desafios para a investigação policial e a preservação da cadeia de custódia digital",
                    "agency": "Polícia Federal / PC",
                    "axis": "Crimes Cibernéticos",
                    "description": "Discorra sobre: 1) As novas modalidades de fraudes eletrônicas e ransomware; 2) Os procedimentos técnicos para apreensão e preservação de evidências digitais (Lei Pacote Anticrime); 3) A cooperação internacional contra crimes na dark web."
                },
                {
                    "title": "A segurança viária e as tecnologias aplicadas à fiscalização do Código de Trânsito Brasileiro",
                    "agency": "PRF",
                    "axis": "Trânsito & Segurança Viária",
                    "description": "Analise: 1) A Década de Ação pela Segurança no Trânsito da ONU e as metas brasileiras; 2) A fiscalização ostensiva com radares, etilômetros e inteligência artificial; 3) O impacto social e econômico dos acidentes de trânsito."
                },
                {
                    "title": "O uso de câmeras corporais operacionais e tecnologia biométrica pelas polícias: eficiência e garantias constitucionais",
                    "agency": "Polícia Militar / Civil",
                    "axis": "Tecnologia & Direitos Fundamentais",
                    "description": "Aborde: 1) A transparência e proteção do próprio agente de segurança; 2) A preservação dos direitos e garantias individuais fundamentais; 3) Diretrizes jurisprudenciais do STF e STJ sobre a matéria."
                },
                {
                    "title": "A crise do sistema prisional brasileiro e a atuação da Polícia Penal Federal na custódia de lideranças criminosas",
                    "agency": "SENAPPEN / Polícia Penal",
                    "axis": "Sistema Prisional & Segurança Máxima",
                    "description": "Discorra sobre: 1) O regime disciplinar diferenciado (RDD) nos presídios federais de segurança máxima; 2) O isolamento de lideranças para desarticular facções; 3) O papel constitucional da Polícia Penal."
                },
                {
                    "title": "A atuação da Polícia Judiciária no acolhimento a grupos vulneráveis e a aplicação da Lei Maria da Penha",
                    "agency": "Polícia Civil",
                    "axis": "Proteção a Vulneráveis",
                    "description": "Aborde: 1) A importância do atendimento especializado nas delegacias da mulher; 2) A concessão de medidas protetivas de urgência no âmbito policial; 3) O feminicídio como crime hediondo e estratégias preventivas."
                }
            ]
            for p in prompts:
                cursor.execute("""
                INSERT INTO essay_prompts (title, agency, axis, description)
                VALUES (?, ?, ?, ?)
                """, (p["title"], p["agency"], p["axis"], p["description"]))

        print("Seeded Tactical Expansions (Approvals, TAF, Countdown, Law, Errors, Essays) successfully!")

"""
Além da Meta Concursos - Templates de Carreiras Policiais e Segurança Pública.
Usado na criação de novas contas para montar o edital verticalizado inicial conforme o alvo do usuário.
"""

CAREER_TEMPLATES = {
    "PM": {
        "label": "Polícia Militar (PM)",
        "default_role": "Polícia Militar - Soldado PM",
        "countdown_title": "Operação Polícia Militar - Dia D",
        "subjects": [
            {
                "name": "Língua Portuguesa",
                "category": "Básica",
                "color": "#10b981",
                "icon": "fa-book-bookmark",
                "target_hours": 55.0,
                "weight": 3.0,
                "topics": [
                    "Interpretação e Compreensão de Textos",
                    "Ortografia Oficial e Acentuação Gráfica",
                    "Classes de Palavras (Verbos, Pronomes e Conjunções)",
                    "Sintaxe da Oração e do Período",
                    "Concordância Verbal e Nominal",
                    "Regência Verbal, Nominal e Crase",
                    "Pontuação e Reescrita de Frases"
                ]
            },
            {
                "name": "Raciocínio Lógico & Matemática",
                "category": "Básica",
                "color": "#eab308",
                "icon": "fa-brain",
                "target_hours": 45.0,
                "weight": 2.5,
                "topics": [
                    "Proposições Lógicas, Conectivos e Tabelas-Verdade",
                    "Equivalências e Negações Lógicas",
                    "Razão, Proporção, Regra de Três e Porcentagem",
                    "Conjuntos Numéricos e Problemas Aritméticos",
                    "Equações de 1º e 2º Grau e Sistemas Lineares",
                    "Noções de Probabilidade e Análise Combinatória"
                ]
            },
            {
                "name": "Direito Constitucional",
                "category": "Jurídica",
                "color": "#3b82f6",
                "icon": "fa-landmark",
                "target_hours": 45.0,
                "weight": 2.5,
                "topics": [
                    "Princípios Fundamentais da CF/88",
                    "Direitos e Garantias Fundamentais (Art. 5º)",
                    "Remédios Constitucionais (HC, MS, HD, MI, Ação Popular)",
                    "Segurança Pública (Art. 144 - PM, CBM, PC, PF, PRF)",
                    "Militares dos Estados e do DF (Art. 42 da CF/88)"
                ]
            },
            {
                "name": "Direito Penal & Penal Militar",
                "category": "Jurídica",
                "color": "#ef4444",
                "icon": "fa-handcuffs",
                "target_hours": 55.0,
                "weight": 3.0,
                "topics": [
                    "Aplicação da Lei Penal e Teoria do Crime",
                    "Excludentes de Ilicitude (Legítima Defesa e Estrito Cumprimento)",
                    "Crimes contra a Pessoa e contra o Patrimônio",
                    "Crimes contra a Administração Pública",
                    "Código Penal Militar: Crime Militar em Tempo de Paz (Art. 9º CPM)",
                    "Crimes Militares contra a Autoridade, Disciplina e Serviço Militar"
                ]
            },
            {
                "name": "Direito Processual Penal & Militar",
                "category": "Jurídica",
                "color": "#f97316",
                "icon": "fa-scale-balanced",
                "target_hours": 45.0,
                "weight": 2.0,
                "topics": [
                    "Inquérito Policial e Inquérito Policial Militar (IPM)",
                    "Prisão em Flagrante, Preventiva e Temporária",
                    "Provas e Busca e Apreensão",
                    "Competência da Justiça Militar Estadual"
                ]
            },
            {
                "name": "Legislação Extravagante & Direitos Humanos",
                "category": "Específica",
                "color": "#8b5cf6",
                "icon": "fa-gun",
                "target_hours": 40.0,
                "weight": 2.0,
                "topics": [
                    "Lei de Drogas (Lei 11.343/06) e Estatuto do Desarmamento (Lei 10.826/03)",
                    "Nova Lei de Abuso de Autoridade (Lei 13.869/19)",
                    "Lei Maria da Penha (Lei 11.340/06) e Lei de Tortura (Lei 9.455/97)",
                    "Declaração Universal dos Direitos Humanos e Uso Progressivo da Força",
                    "Estatuto dos Policiais Militares do Estado (Legislação Local)"
                ]
            },
            {
                "name": "Informática & Atualidades",
                "category": "Básica",
                "color": "#6366f1",
                "icon": "fa-network-wired",
                "target_hours": 30.0,
                "weight": 1.5,
                "topics": [
                    "Windows, Pacote Office / LibreOffice e Navegadores",
                    "Segurança da Informação, Vírus, Golpes e Backup",
                    "Geografia, História e Atualidades de Segurança Pública"
                ]
            }
        ]
    },
    "PRF": {
        "label": "Polícia Rodoviária Federal (PRF)",
        "default_role": "Polícia Rodoviária Federal - PRF",
        "countdown_title": "Operação PRF - Dia D",
        "subjects": [
            {
                "name": "Legislação de Trânsito (CTB + CONTRAN)",
                "category": "Específica",
                "color": "#f43f5e",
                "icon": "fa-car-burst",
                "target_hours": 80.0,
                "weight": 3.5,
                "topics": [
                    "Sistema Nacional de Trânsito (Órgãos e Competências)",
                    "Normas Gerais de Circulação e Conduta (Arts. 26 a 67 CTB)",
                    "Habilitação, Registro e Licenciamento de Veículos",
                    "Infrações, Penalidades e Medidas Administrativas",
                    "Crimes de Trânsito (Arts. 291 a 312 CTB)",
                    "Resoluções do CONTRAN (Pesos, Dimensões, Equipamentos, Etilômetro)"
                ]
            },
            {
                "name": "Língua Portuguesa",
                "category": "Básica",
                "color": "#10b981",
                "icon": "fa-book-bookmark",
                "target_hours": 50.0,
                "weight": 2.5,
                "topics": [
                    "Compreensão e Interpretação de Textos (Padrão Cebraspe)",
                    "Morfossintaxe, Reescrita e Coesão Textual",
                    "Concordância, Regência, Crase e Pontuação",
                    "Redação Oficial (Manual da Presidência)"
                ]
            },
            {
                "name": "Raciocínio Lógico-Matemático",
                "category": "Básica",
                "color": "#eab308",
                "icon": "fa-brain",
                "target_hours": 40.0,
                "weight": 2.0,
                "topics": [
                    "Lógica Proposicional e Argumentação",
                    "Funções, Porcentagem, Análise Combinatória e Probabilidade",
                    "Geometria Básica e Grandezas Proporcionais"
                ]
            },
            {
                "name": "Física Aplicada à Perícia de Acidentes",
                "category": "Específica",
                "color": "#06b6d4",
                "icon": "fa-atom",
                "target_hours": 40.0,
                "weight": 2.0,
                "topics": [
                    "Cinemática Escalar e Vetorial (MRU e MRUV)",
                    "Leis de Newton, Atrito e Dinâmica em Curvas",
                    "Trabalho, Energia Cinética e Conservação de Energia",
                    "Impulso, Quantidade de Movimento e Colisões"
                ]
            },
            {
                "name": "Informática",
                "category": "Básica",
                "color": "#6366f1",
                "icon": "fa-network-wired",
                "target_hours": 35.0,
                "weight": 2.0,
                "topics": [
                    "Redes de Computadores, Internet e Computação em Nuvem",
                    "Segurança da Informação, Malwares e Criptografia",
                    "Sistemas Operacionais e Ferramentas de Escritório"
                ]
            },
            {
                "name": "Direito Penal & Processual Penal",
                "category": "Jurídica",
                "color": "#ef4444",
                "icon": "fa-handcuffs",
                "target_hours": 50.0,
                "weight": 2.5,
                "topics": [
                    "Teoria do Crime e Ilicitude",
                    "Crimes contra a Pessoa, Patrimônio e Administração Pública",
                    "Inquérito Policial, Provas e Cadeia de Custódia",
                    "Prisões em Flagrante, Preventiva e Temporária"
                ]
            },
            {
                "name": "Direito Constitucional & Administrativo",
                "category": "Jurídica",
                "color": "#3b82f6",
                "icon": "fa-landmark",
                "target_hours": 45.0,
                "weight": 2.0,
                "topics": [
                    "Direitos Fundamentais (Art. 5º) e Segurança Pública (Art. 144)",
                    "Poderes Administrativos e Poder de Polícia",
                    "Atos Administrativos, Responsabilidade Civil e Improbidade",
                    "Regime Jurídico (Lei 8.112/90)"
                ]
            },
            {
                "name": "Legislação Especial & Direitos Humanos",
                "category": "Jurídica",
                "color": "#8b5cf6",
                "icon": "fa-gun",
                "target_hours": 40.0,
                "weight": 2.0,
                "topics": [
                    "Lei de Drogas, Desarmamento e Abuso de Autoridade",
                    "Crimes Ambientais e Contrabando/Descaminho",
                    "Direitos Humanos na CF/88 e Pacto de San José da Costa Rica"
                ]
            }
        ]
    },
    "PF": {
        "label": "Polícia Federal (PF - Agente / Escrivão)",
        "default_role": "Polícia Federal - Agente",
        "countdown_title": "Operação Polícia Federal - Dia D",
        "subjects": [
            {
                "name": "Informática & Tecnologia da Informação",
                "category": "Específica",
                "color": "#6366f1",
                "icon": "fa-network-wired",
                "target_hours": 85.0,
                "weight": 3.5,
                "topics": [
                    "Redes de Comunicação, Modelo OSI, TCP/IP, Protocolos e Segurança",
                    "Segurança da Informação, Criptografia, Certificação e Malwares",
                    "Bancos de Dados Relacionais, Modelagem ER e Linguagem SQL",
                    "Programação Python e R aplicada à Ciência de Dados",
                    "Teoria da Informação, Big Data, Mineração de Dados e Aprendizado de Máquina",
                    "Computação em Nuvem e Sistemas Operacionais"
                ]
            },
            {
                "name": "Contabilidade Geral",
                "category": "Específica",
                "color": "#14b8a6",
                "icon": "fa-calculator",
                "target_hours": 65.0,
                "weight": 3.0,
                "topics": [
                    "Conceito, Objeto, Patrimônio e Equação Fundamental",
                    "Fatos Contábeis, Método das Partidas Dobradas e Lançamentos",
                    "Contas Patrimoniais e de Resultado (Plano de Contas)",
                    "Balanço Patrimonial (Ativo, Passivo e PL)",
                    "Demonstração do Resultado do Exercício (DRE) e DFC",
                    "Operações com Mercadorias, Depreciação e Provisões"
                ]
            },
            {
                "name": "Língua Portuguesa",
                "category": "Básica",
                "color": "#10b981",
                "icon": "fa-book-bookmark",
                "target_hours": 55.0,
                "weight": 3.0,
                "topics": [
                    "Compreensão e Interpretação de Textos (Padrão Cebraspe)",
                    "Tipologia Textual, Coesão e Coerência",
                    "Morfossintaxe, Concordância, Regência e Crase",
                    "Reescrita de Frases e Redação Oficial"
                ]
            },
            {
                "name": "Estatística & Raciocínio Lógico",
                "category": "Básica",
                "color": "#eab308",
                "icon": "fa-brain",
                "target_hours": 50.0,
                "weight": 2.5,
                "topics": [
                    "Lógica Proposicional, Equivalências e Argumentação",
                    "Análise Combinatória e Probabilidade Condicional",
                    "Estatística Descritiva (Média, Mediana, Moda, Variância, Desvio Padrão)",
                    "Distribuições de Probabilidade (Binomial, Poisson, Normal)",
                    "Inferência Estatística, Amostragem e Regressão Linear"
                ]
            },
            {
                "name": "Direito Penal & Processual Penal",
                "category": "Jurídica",
                "color": "#ef4444",
                "icon": "fa-handcuffs",
                "target_hours": 50.0,
                "weight": 2.0,
                "topics": [
                    "Teoria do Crime, Concurso de Pessoas e Crimes contra a Adm. Pública",
                    "Inquérito Policial, Provas e Cadeia de Custódia",
                    "Prisão em Flagrante, Preventiva e Temporária"
                ]
            },
            {
                "name": "Direito Constitucional & Administrativo",
                "category": "Jurídica",
                "color": "#3b82f6",
                "icon": "fa-landmark",
                "target_hours": 45.0,
                "weight": 2.0,
                "topics": [
                    "Direitos Fundamentais (Art. 5º) e Segurança Pública (Art. 144)",
                    "Poderes da Administração, Atos Administrativos e Responsabilidade Civil",
                    "Lei 8.112/90 e Improbidade Administrativa"
                ]
            },
            {
                "name": "Legislação Penal Especial",
                "category": "Jurídica",
                "color": "#8b5cf6",
                "icon": "fa-gun",
                "target_hours": 40.0,
                "weight": 2.0,
                "topics": [
                    "Lei de Drogas, Estatuto do Desarmamento e Abuso de Autoridade",
                    "Organizações Criminosas (Lei 12.850/13) e Interceptação Telefônica",
                    "Lavagem de Capitais (Lei 9.613/98)"
                ]
            }
        ]
    },
    "PC": {
        "label": "Polícia Civil (Agente / Investigador / Escrivão)",
        "default_role": "Polícia Civil - Agente / Investigador",
        "countdown_title": "Operação Polícia Civil - Dia D",
        "subjects": [
            {
                "name": "Língua Portuguesa",
                "category": "Básica",
                "color": "#10b981",
                "icon": "fa-book-bookmark",
                "target_hours": 50.0,
                "weight": 3.0,
                "topics": [
                    "Interpretação e Compreensão de Textos",
                    "Ortografia, Acentuação e Classes de Palavras",
                    "Sintaxe, Concordância, Regência e Crase",
                    "Pontuação e Redação Oficial"
                ]
            },
            {
                "name": "Direito Penal",
                "category": "Jurídica",
                "color": "#ef4444",
                "icon": "fa-handcuffs",
                "target_hours": 60.0,
                "weight": 3.0,
                "topics": [
                    "Aplicação da Lei Penal e Teoria do Crime",
                    "Ilicitude, Culpabilidade e Concurso de Pessoas",
                    "Crimes contra a Pessoa e contra o Patrimônio",
                    "Crimes contra a Dignidade Sexual e Administração Pública"
                ]
            },
            {
                "name": "Direito Processual Penal",
                "category": "Jurídica",
                "color": "#f97316",
                "icon": "fa-scale-balanced",
                "target_hours": 60.0,
                "weight": 3.0,
                "topics": [
                    "Inquérito Policial (Instauração, Prazos e Diligências)",
                    "Ação Penal, Provas e Cadeia de Custódia",
                    "Prisão em Flagrante, Preventiva, Temporária e Audiência de Custódia"
                ]
            },
            {
                "name": "Informática Policial & Investigação Digital",
                "category": "Específica",
                "color": "#6366f1",
                "icon": "fa-network-wired",
                "target_hours": 50.0,
                "weight": 2.5,
                "topics": [
                    "Sistemas Operacionais (Windows e Linux)",
                    "Redes TCP/IP, Segurança da Informação e Malwares",
                    "Computação em Nuvem e Rastreabilidade de Crimes Eletrônicos"
                ]
            },
            {
                "name": "Legislação Penal Especial",
                "category": "Jurídica",
                "color": "#8b5cf6",
                "icon": "fa-gun",
                "target_hours": 50.0,
                "weight": 2.5,
                "topics": [
                    "Lei de Drogas (11.343/06) e Estatuto do Desarmamento (10.826/03)",
                    "Abuso de Autoridade (13.869/19) e Organizações Criminosas (12.850/13)",
                    "Crimes Hediondos, Tortura e Lei Maria da Penha"
                ]
            },
            {
                "name": "Direito Constitucional & Administrativo",
                "category": "Jurídica",
                "color": "#3b82f6",
                "icon": "fa-landmark",
                "target_hours": 50.0,
                "weight": 2.0,
                "topics": [
                    "Direitos Fundamentais (Art. 5º) e Segurança Pública (Art. 144)",
                    "Atos Administrativos, Poder de Polícia e Improbidade"
                ]
            },
            {
                "name": "Direitos Humanos, Medicina Legal & RLM",
                "category": "Específica",
                "color": "#ec4899",
                "icon": "fa-microscope",
                "target_hours": 45.0,
                "weight": 1.5,
                "topics": [
                    "DUDH, Pacto de San José da Costa Rica e Uso da Força",
                    "Traumatologia, Tanatologia Forense e Locais de Crime",
                    "Lógica Proposicional, Conjuntos e Estatuto da Polícia Civil Local"
                ]
            }
        ]
    },
    "PP": {
        "label": "Polícia Penal (Estadual / SENAPPEN)",
        "default_role": "Polícia Penal - Policial Penal",
        "countdown_title": "Operação Polícia Penal - Dia D",
        "subjects": [
            {
                "name": "Lei de Execução Penal (LEP - Lei 7.210/84)",
                "category": "Específica",
                "color": "#f59e0b",
                "icon": "fa-lock",
                "target_hours": 70.0,
                "weight": 3.5,
                "topics": [
                    "Objeto, Classificação dos Condenados e Assistência ao Preso",
                    "Trabalho Interno/Externo, Deveres, Direitos e Faltas Disciplinares",
                    "Regimes de Cumprimento, Progressão, Remição e Livramento Condicional",
                    "Órgãos da Execução Penal e Estabelecimentos Penais",
                    "Regras de Mandela e Sistema Penitenciário Federal (RDD)"
                ]
            },
            {
                "name": "Língua Portuguesa",
                "category": "Básica",
                "color": "#10b981",
                "icon": "fa-book-bookmark",
                "target_hours": 50.0,
                "weight": 3.0,
                "topics": [
                    "Interpretação de Textos e Tipologia Textual",
                    "Sintaxe, Concordância, Regência, Crase e Pontuação",
                    "Redação Oficial"
                ]
            },
            {
                "name": "Direito Penal & Processual Penal",
                "category": "Jurídica",
                "color": "#ef4444",
                "icon": "fa-handcuffs",
                "target_hours": 55.0,
                "weight": 2.5,
                "topics": [
                    "Teoria do Crime, Penas e Medidas de Segurança",
                    "Crimes contra a Administração Pública (Facilitação de Fuga, Prevaricação Imprópria)",
                    "Prisões, Medidas Cautelares e Audiência de Custódia"
                ]
            },
            {
                "name": "Direitos Humanos",
                "category": "Específica",
                "color": "#ec4899",
                "icon": "fa-hand-holding-heart",
                "target_hours": 40.0,
                "weight": 2.5,
                "topics": [
                    "Teoria Geral e Declaração Universal dos Direitos Humanos",
                    "Regras Mínimas da ONU para Tratamento de Presos (Regras de Mandela)",
                    "Prevenção à Tortura e Tratamento Degradante"
                ]
            },
            {
                "name": "Direito Constitucional & Administrativo",
                "category": "Jurídica",
                "color": "#3b82f6",
                "icon": "fa-landmark",
                "target_hours": 45.0,
                "weight": 2.0,
                "topics": [
                    "Art. 5º (Direitos do Preso) e Art. 144 (Polícia Penal na CF/88)",
                    "Poder de Polícia, Atos Administrativos e Regime Disciplinar"
                ]
            },
            {
                "name": "Informática & Raciocínio Lógico",
                "category": "Básica",
                "color": "#6366f1",
                "icon": "fa-network-wired",
                "target_hours": 35.0,
                "weight": 1.5,
                "topics": [
                    "Segurança da Informação, Windows, Redes e Pacote Office",
                    "Lógica Proposicional, Conjuntos e Porcentagem"
                ]
            }
        ]
    },
    "CUSTOM": {
        "label": "Personalizada / Outro Concurso",
        "default_role": "Concurso Público - Alvo Personalizado",
        "countdown_title": "Operação Aprovação - Dia D",
        "subjects": [
            {
                "name": "Língua Portuguesa",
                "category": "Básica",
                "color": "#10b981",
                "icon": "fa-book-bookmark",
                "target_hours": 50.0,
                "weight": 3.0,
                "topics": ["Interpretação de Textos", "Gramática Essencial"]
            },
            {
                "name": "Raciocínio Lógico",
                "category": "Básica",
                "color": "#eab308",
                "icon": "fa-brain",
                "target_hours": 35.0,
                "weight": 2.0,
                "topics": ["Estruturas Lógicas e Equivalências"]
            },
            {
                "name": "Direito Constitucional",
                "category": "Jurídica",
                "color": "#3b82f6",
                "icon": "fa-landmark",
                "target_hours": 45.0,
                "weight": 2.5,
                "topics": ["Direitos e Garantias Fundamentais (Art. 5º)"]
            }
        ]
    }
}

DEFAULT_PLATFORMS = [
    ("Tec Concursos", "https://www.tecconcursos.com.br", "Banco de Questões", "fa-crosshairs", "#3b82f6", "Banco de questões avançado com filtros por banca.", 1),
    ("QConcursos", "https://www.qconcursos.com", "Banco de Questões", "fa-check-double", "#10b981", "Questões comentadas pela comunidade e professores.", 1),
    ("Projeto Caveira", "https://projetocaveira.com.br", "Simulados", "fa-skull", "#ef4444", "Simulados inéditos focados nas carreiras policiais.", 1),
    ("Planalto - Legislação Federal", "https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm", "Jurisprudência", "fa-scale-balanced", "#f59e0b", "Texto oficial atualizado da CF/88, CP, CPP e Leis Especiais.", 1),
]

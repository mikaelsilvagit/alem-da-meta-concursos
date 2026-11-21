"""
Script de migração para Operação PC-TO (Agente de Polícia Civil).
Configura matérias, tópicos, contagem regressiva e direcionamento pré-edital.
"""

import sqlite3
import datetime
import os

DB_PATH = "concursos.db"

def run_migration():
    print("=" * 65)
    print("  🚨 MIGRANDO SISTEMA PARA: OPERAÇÃO PC-TO (AGENTE DE POLÍCIA) 🚨")
    print("=" * 65)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Atualizar user_profile
    cursor.execute("""
    UPDATE user_profile 
    SET target_role = 'Polícia Civil - TO (Agente)',
        weekly_goal_hours = 25
    WHERE id = 1
    """)
    print("  [+] Perfil de usuário atualizado para Agente de Polícia Civil (PC-TO).")

    # 2. Configurar Contagem Regressiva do Edital (2 semanas a partir de 16/11)
    target_edital = "2026-11-30"
    target_prova = "2027-02-28"

    cursor.execute("UPDATE exam_countdowns SET is_active = 0")
    
    # Check if already exists
    cursor.execute("SELECT id FROM exam_countdowns WHERE title LIKE '%PC-TO%'")
    row = cursor.fetchone()
    if row:
        cursor.execute("""
        UPDATE exam_countdowns 
        SET title = 'Operação PC-TO (Agente) - Publicação do Edital',
            target_date = ?,
            target_time = '08:00',
            is_active = 1
        WHERE id = ?
        """, (target_edital, row["id"]))
    else:
        cursor.execute("""
        INSERT INTO exam_countdowns (title, target_date, target_time, is_active)
        VALUES ('Operação PC-TO (Agente) - Publicação do Edital', ?, '08:00', 1)
        """, (target_edital,))

    # Add Prova countdown as inactive option
    cursor.execute("""
    INSERT INTO exam_countdowns (title, target_date, target_time, is_active)
    VALUES ('Operação PC-TO (Agente) - Prova Objetiva Estimada', ?, '08:00', 0)
    """, (target_prova,))
    print(f"  [+] Contagem regressiva ativada: Publicação do Edital PC-TO em {target_edital} (daqui a 2 semanas).")

    # 3. Atualizar Grade de Matérias e Tópicos para PC-TO
    # Verificar se há sessões de estudo antes de limpar topics
    cursor.execute("SELECT COUNT(*) FROM study_sessions")
    study_count = cursor.fetchone()[0]

    if study_count == 0:
        cursor.execute("DELETE FROM topics")
        cursor.execute("DELETE FROM subjects")
        print("  [+] Grade antiga limpa com segurança (nenhuma sessão de estudo foi perdida).")
    else:
        print(f"  [!] Atenção: Existem {study_count} sessões de estudo registradas.")

    pcto_subjects = [
        {
            "name": "Língua Portuguesa (PC-TO)",
            "category": "Básica",
            "color": "#10b981", # Emerald
            "icon": "fa-book-bookmark",
            "target_hours": 50.0,
            "topics": [
                "Compreensão e Interpretação de Textos de Gêneros Variados",
                "Reconhecimento de Tipos e Gêneros Textuais",
                "Ortografia Oficial e Regras de Acentuação Gráfica",
                "Mecanismos de Coesão e Coerência Textual",
                "Emprego das Classes de Palavras (Pronomes, Verbos e Conjunções)",
                "Sintaxe da Oração e do Período (Termos Essenciais e Integrantes)",
                "Concordância Verbal e Nominal",
                "Regência Verbal, Nominal e Emprego do Sinal Indicativo de Crase",
                "Pontuação (Vírgula, Ponto e Vírgula, Dois-Pontos e Aspas)",
                "Redação Oficial (Manual da Presidência da República: Memorando, Ofício e Relatório Policial)"
            ]
        },
        {
            "name": "Raciocínio Lógico & Matemático",
            "category": "Básica",
            "color": "#eab308", # Amber
            "icon": "fa-brain",
            "target_hours": 35.0,
            "topics": [
                "Estruturas Lógicas e Conectivos (Proposições Simples e Compostas)",
                "Tabelas-Verdade, Equivalências Lógicas e Negações",
                "Lógica de Argumentação e Dedução",
                "Diagramas Lógicos e Teoria dos Conjuntos",
                "Princípios de Contagem e Análise Combinatória (Arranjos, Combinações e Permutações)",
                "Noções de Probabilidade Básica aplicada a cenários"
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
            "name": "Direito Constitucional",
            "category": "Jurídica",
            "color": "#3b82f6", # Blue
            "icon": "fa-landmark",
            "target_hours": 45.0,
            "topics": [
                "Princípios Fundamentais da República Federativa do Brasil",
                "Direitos e Deveres Individuais e Coletivos (Art. 5º da CF/88)",
                "Remédios Constitucionais (Habeas Corpus, Mandado de Segurança, Habeas Data, Mandado de Injunção e Ação Popular)",
                "Segurança Pública na Constituição (Artigo 144: PF, PRF, PC, PM, CBM, Polícia Penal e Guardas)",
                "Organização Político-Administrativa e Competências da União, Estados e DF",
                "Poder Executivo (Atribuições e Responsabilidade do Presidente e Governadores)",
                "Defesa do Estado e das Instituições Democráticas (Estado de Defesa e de Sítio)"
            ]
        },
        {
            "name": "Direito Administrativo",
            "category": "Jurídica",
            "color": "#06b6d4", # Cyan
            "icon": "fa-building-columns",
            "target_hours": 45.0,
            "topics": [
                "Princípios Expressos e Reconhecidos da Administração Pública (LIMPE, Proporcionalidade e Razoabilidade)",
                "Poderes Administrativos e Poder de Polícia (Conceito, Atributos, Ciclo de Polícia e Limites)",
                "Atos Administrativos (Requisitos de Validade, Atributos, Extinção, Revogação e Anulação)",
                "Regime Jurídico dos Servidores Públicos (Deveres, Proibições e Responsabilidade Administrativa)",
                "Responsabilidade Civil do Estado (Teoria do Risco Administrativo, Ação Regressiva e Excludentes)",
                "Improbidade Administrativa (Lei nº 8.429/1992 atualizada pela Lei 14.230/2021)",
                "Licitações e Contratos Administrativos (Visão Geral da Nova Lei 14.133/2021)"
            ]
        },
        {
            "name": "Direito Penal",
            "category": "Jurídica",
            "color": "#ef4444", # Red
            "icon": "fa-handcuffs",
            "target_hours": 60.0,
            "topics": [
                "Aplicação da Lei Penal (Princípio da Legalidade, Anterioridade, Lei no Tempo e no Espaço, Territorialidade)",
                "Teoria do Crime: Fato Típico (Conduta, Resultado, Nexo Causal e Tipicidade)",
                "Ilicitude e Excludentes de Ilicitude (Legítima Defesa, Estado de Necessidade, Estrito Cumprimento do Dever Legal)",
                "Culpabilidade e Elementos Subjetivos (Imputabilidade, Dolo, Culpa e Preterdolo)",
                "Consumação, Tentativa, Desistência Voluntária, Arrependimento Eficaz e Arrependimento Posterior",
                "Concurso de Pessoas (Autoria, Coautoria e Participação)",
                "Crimes Contra a Pessoa (Homicídio, Induzimento ao Suicídio, Lesão Corporal e Omissão de Socorro)",
                "Crimes Contra o Patrimônio (Furto, Roubo, Extorsão, Extorsão Mediante Sequestro, Dano, Estelionato e Receptação)",
                "Crimes Contra a Dignidade Sexual (Estupro, Violação Sexual Mediante Fraude e Assédio)",
                "Crimes Contra a Administração Pública Praticados por Funcionário Público e por Particular"
            ]
        },
        {
            "name": "Direito Processual Penal",
            "category": "Jurídica",
            "color": "#f97316", # Orange
            "icon": "fa-scale-balanced",
            "target_hours": 60.0,
            "topics": [
                "Inquérito Policial (Conceito, Características, Notitia Criminis, Instauração, Prazos e Conclusão)",
                "Termo Circunstanciado de Ocorrência (TCO) e Procedimentos Especiais da Polícia Civil",
                "Ação Penal (Pública Incondicionada, Pública Condicionada à Representação e Ação Penal Privada)",
                "Provas em Processo Penal (Exame de Corpo de Delito, Perícias em Geral, Interrogatório e Testemunhas)",
                "Cadeia de Custódia da Prova (Etapas: Reconhecimento, Isolamento, Fixação, Coleta, Acondicionamento e Rastreabilidade)",
                "Prisão em Flagrante (Espécies: Flagrante Próprio, Impróprio, Presumido, Preparado e Esperado; Audiência de Custódia)",
                "Prisão Preventiva e Prisão Temporária (Pressupostos, Requisitos e Prazos)",
                "Medidas Cautelares Diversas da Prisão (Art. 319 do CPP)",
                "Juiz das Garantias e Atuação na Fase Investigatória Policial"
            ]
        },
        {
            "name": "Legislação Penal Especial",
            "category": "Jurídica",
            "color": "#8b5cf6", # Purple
            "icon": "fa-gun",
            "target_hours": 55.0,
            "topics": [
                "Lei de Drogas (Lei nº 11.343/2006: Crimes de Posse para Consumo, Tráfico, Procedimento e Infiltração)",
                "Estatuto do Desarmamento (Lei nº 10.826/2003: Posse, Porte, Disparo de Arma de Fogo e Comércio Ilegal)",
                "Nova Lei de Abuso de Autoridade (Lei nº 13.869/2019: Sujeitos, Elemento Específico e Tipos Penais)",
                "Crimes Hediondos (Lei nº 8.072/1990: Rol Taxativo, Vedação a Benefícios e Regime de Cumprimento)",
                "Organizações Criminosas (Lei nº 12.850/2013: Conceito, Meios de Obtenção de Prova e Colaboração Premiada)",
                "Lei Maria da Penha (Lei nº 11.340/2006: Formas de Violência, Medidas Protetivas de Urgência e Procedimentos)",
                "Lei de Tortura (Lei nº 9.455/1997: Espécies de Tortura, Efeitos da Condenação e Qualificadoras)",
                "Lei de Interceptação Telefônica e Telemática (Lei nº 9.296/1996)"
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

    for subj in pcto_subjects:
        cursor.execute("""
        INSERT INTO subjects (name, category, color, icon, target_hours)
        VALUES (?, ?, ?, ?, ?)
        """, (subj["name"], subj["category"], subj["color"], subj["icon"], subj["target_hours"]))
        subject_id = cursor.lastrowid

        for t_order, topic_title in enumerate(subj["topics"]):
            cursor.execute("""
            INSERT INTO topics (subject_id, name, theory_completed, summary_completed, questions_completed)
            VALUES (?, ?, 0, 0, 0)
            """, (subject_id, topic_title))

    print(f"  [+] Inseridas {len(pcto_subjects)} disciplinas com 80 tópicos verticalizados da PC-TO.")

    # 4. Inserir Alerta de Notícia Fixada da PC-TO
    cursor.execute("SELECT id FROM news_feed WHERE title LIKE '%PC-TO%' AND is_pinned = 1")
    if not cursor.fetchone():
        cursor.execute("""
        INSERT INTO news_feed (title, source, category, link, pub_date, summary, is_pinned, priority)
        VALUES (?, ?, ?, ?, ?, ?, 1, 'alta')
        """, (
            "🚨 ALERTA MÁXIMO PC-TO: Edital para Agente de Polícia Civil iminente nas próximas 2 semanas!",
            "SSP-TO / QAP Tático",
            "Policial",
            "https://www.to.gov.br/policiacivil",
            datetime.date.today().strftime("%d/%m/%Y"),
            "Comissão formada e fase final de contratação da banca organizadora. Reta final do pré-edital ativada: fechar núcleo jurídico e legislação estadual do Tocantins!"
        ))
        print("  [+] Alerta tático de notícias da PC-TO adicionado com prioridade alta.")

    # 5. Adicionar Plataformas de Estudo de Referência do Tocantins
    pcto_platforms = [
        ("Portal Oficial da Polícia Civil do Tocantins", "https://www.to.gov.br/policiacivil", "Institucional", "fa-shield-halved", "#3b82f6", "Notícias, estrutura e editais anteriores da PC-TO.", 1),
        ("ALETO - Legislação Estadual do Tocantins", "https://al.to.leg.br", "Jurisprudência", "fa-landmark", "#f59e0b", "Acesso à Lei Estadual 1.654/06 (Estatuto PC-TO) e Lei 1.818/07.", 1),
        ("Olho na Vaga (Simulados & Rankings)", "https://olhonavaga.com.br", "Simulados", "fa-chart-simple", "#10b981", "Simulados e ranking pós-prova para Agente e Escrivão PC-TO.", 0)
    ]

    for title, url, cat, icon, color, notes, pin in pcto_platforms:
        cursor.execute("SELECT id FROM study_platforms WHERE title = ?", (title,))
        if not cursor.fetchone():
            cursor.execute("""
            INSERT INTO study_platforms (title, url, category, icon, color, notes, is_pinned)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (title, url, cat, icon, color, notes, pin))
            print(f"  [+] Plataforma adicionada: {title}")

    conn.commit()
    conn.close()
    print("=" * 65)
    print("  ✓ MIGRAÇÃO OPERAÇÃO PC-TO (AGENTE) CONCLUÍDA COM SUCESSO!")
    print("=" * 65)

if __name__ == "__main__":
    run_migration()

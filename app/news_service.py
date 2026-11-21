import httpx
import re
import datetime
from app.database import get_db

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# Strict indicators for Law Enforcement / Police institutions
POLICE_INDICATORS = [
    'polícia federal', 'policia federal', 'departamento de polícia federal', ' dpf ',
    'polícia rodoviária federal', 'policia rodoviaria federal', ' prf ', '(prf)', 'prf -', 'dprf',
    'polícia civil', 'policia civil', ' pc-', ' pc/', 'pcdf', 'pcsp', 'pcrj', 'pcmg', 'pcba', 'pcpr', 'pcrs', 'pcsc', 'pcgo', 'pcmt', 'pcms', 'pcal', 'pcce', 'pcma', 'pcpb', 'pcpe', 'pcpi', 'pcrn', 'pcse', 'pcto', 'pcan', 'pcap', 'pcpa', 'pcro',
    'polícia militar', 'policia militar', ' pm-', ' pm/', 'pmesp', 'pmmg', 'pmerj', 'pmdf', 'pmba', 'pmpr', 'pmrs', 'pmsc', 'pmgo', 'pmmt', 'pmms', 'pmal', 'pmce', 'pmma', 'pmpb', 'pmpe', 'pmpi', 'pmrn', 'pmse', 'pmto', 'pmap', 'pmpa', 'pmro', 'brigada militar',
    'polícia penal', 'policia penal', 'senappen', 'depen', 'agente penitenciário', 'agente penitenciario', 'policial penal', 'segurança penitenciária',
    'polícia científica', 'policia cientifica', 'perícia oficial', 'pericia oficial', 'perícia forense', 'pericia forense', 'pefoce', 'politec', 'instituto geral de perícias', 'igp', 'polícia técnica', 'policia tecnica', 'instituto de criminalística', 'instituto médico legal', ' iml ',
    'corpo de bombeiros militar', 'bombeiros militar', 'bombeiro militar', ' cbm', 'cbm-', 'cbmerj', 'cbmmg', 'cbmdf',
    'guarda municipal', 'guarda civil municipal', 'guarda civil metropolitana', 'gcm', 'guarda metropolitana'
]

# Strict indicators for Police / Public Security roles
POLICE_ROLES = [
    'delegado', 'investigador', 'escrivão', 'escrivao', 'agente de polícia', 'agente de policia',
    'soldado pm', 'oficial pm', 'aluno-oficial', 'aluno oficial', 'cadete', 'cfo pm', 'soldado combatente',
    'policial penal', 'agente de execução penal', 'agente federal de execução penal', 'agente de segurança penitenciária',
    'perito criminal', 'perito legista', 'perito forense', 'médico legista', 'papiloscopista', 'auxiliar de necropsia', 'técnico pericial',
    'policial rodoviário', 'policial rodoviario', 'guarda civil', 'guarda municipal', 'soldado bombeiro'
]

# Strict non-police exclusions (Courts, Councils, City Councils, Universities, Hospitals, etc.)
EXCLUDE_TERMS = [
    'câmara', 'camara', 'tribunal', 'tjsp', 'trf', 'trt', 'tre', 'stf', 'stj', 'tst', 'tse', 'stm', 'cnj',
    'judiciário', 'judiciario', 'escrevente', 'analista judiciário', 'técnico judiciário', 'oficial de justiça',
    'assembleia legislativa', 'senado', 'câmara dos deputados', 'procurador legislativo', 'consultor legislativo',
    'ministério público', 'ministerio publico', 'promotor', 'defensoria pública', 'defensoria publica',
    'universidade', 'faculdade', 'instituto federal', 'ifsp', 'ufmg', 'ufrj', 'unesp', 'unicamp', 'usp',
    'hospital', 'clínicas', 'clinicas', 'saúde', 'enfermagem', 'médico clinico', 'fisioterapeuta',
    'professor', 'educação básica', 'docente', 'pedagogo',
    'prefeitura municipal', 'prefeitura de', 'prefeitura da'
]

def is_strictly_police(title: str, agency: str, role: str, details: str = "") -> bool:
    """Verifies whether a contest is strictly within the police and security forces domain."""
    full_text = f" {title} {agency} {role} {details} ".lower()
    full_text = re.sub(r'[\s\-_/]+', ' ', full_text)
    
    has_police_indicator = any(term in full_text for term in POLICE_INDICATORS)
    has_police_role = any(role_term in full_text for role_term in POLICE_ROLES)
    
    if not (has_police_indicator or has_police_role):
        return False
        
    for exc in EXCLUDE_TERMS:
        if exc in full_text:
            # Exception: allow Guarda Municipal / GCM even if organized under a Prefeitura / Secretaria
            if 'guarda' in full_text or 'gcm' in full_text:
                if any(k in exc for k in ['prefeitura', 'câmara', 'camara']):
                    continue
            return False
            
    return True

def detect_agency_type(text: str) -> str:
    """Categorizes the police branch."""
    t = text.lower()
    if any(k in t for k in ["federal", "prf", "senappen", "depen", "pf", "dprf", "dpf"]):
        return "Federal"
    if any(k in t for k in ["militar", "pm", "brigada", "bombeiro", "cbm"]):
        return "Militar"
    if any(k in t for k in ["civil", "pc", "investigador", "delegado", "escrivão", "escrivao"]):
        return "Civil"
    if any(k in t for k in ["penal", "presidiário", "polícia penal", "sap"]):
        return "Penal"
    if any(k in t for k in ["perícia", "perito", "científica", "legista", "pefoce", "politec", "igp"]):
        return "Perícia"
    if any(k in t for k in ["guarda", "gcm"]):
        return "Guarda Municipal"
    return "Policial Geral"

def calc_priority(status: str) -> str:
    """Calculates tactical operational priority."""
    s = (status or "").lower()
    if any(k in s for k in ["edital aberto", "aberto", "aberta", "inscrições", "inscricoes", "publicado", "em andamento"]):
        return "alta"
    elif any(k in s for k in ["iminente", "banca", "autorizado", "autorização", "autorizacao", "contratada", "escolha"]):
        return "media"
    else:
        return "normal"

def get_priority_color(priority: str) -> str:
    if priority == "alta":
        return "#ef4444" # Siren Red (Urgent / Edital Aberto)
    elif priority == "media":
        return "#f59e0b" # Tactical Amber (Warning / Edital Iminente)
    else:
        return "#64748b" # Gunmetal Slate (Comissão Formada / Previsto)

# Strict terms for police news
POLICE_NEWS_TERMS = [
    'polícia', 'policia', 'pf', 'prf', 'pm', 'pc', 'policial', 'penal', 'depen', 'senappen',
    'perícia', 'perito', 'forense', 'delegado', 'escrivão', 'escrivao', 'soldado', 'investigador',
    'bombeiro', 'guarda municipal', 'gcm', 'segurança pública', 'seguranca publica', 'taf',
    'porte de arma', 'edital policial', 'carreira policial'
]

EXCLUDE_NEWS = [
    'shopping', 'lojas', 'coca-cola', 'supermercado', 'prefeitura de', 'prefeitura municipal',
    'auxiliar de cobrança', 'engenheiro de projetos', 'assistente de logística', 'professor',
    'médico', 'saúde', 'enfermagem', 'docente', 'crea', 'cro', 'oab', 'universidade', 'ufes',
    'vestibular', 'enem', 'escola', 'creche', 'educação infantil', 'camara', 'câmara'
]

def is_strictly_police_news(title: str, summary: str = "") -> bool:
    """Filters news strictly for police career operations."""
    text = f" {title} {summary} ".lower()
    has_pol = any(p in text for p in POLICE_NEWS_TERMS)
    if not has_pol:
        return False
    for exc in EXCLUDE_NEWS:
        if exc in text:
            if any(p in text for p in ['polícia', 'policia', 'delegado', 'escrivão', 'soldado', 'perito criminal']):
                continue
            return False
    return True

def calc_news_priority(title: str, summary: str = "") -> str:
    """Calculates news operational priority."""
    text = f" {title} {summary} ".lower()
    if any(k in text for k in ["edital publicado", "publicado", "inscrições abertas", "inscricoes abertas", "edital aberto", "abertas"]):
        return "alta"
    elif any(k in text for k in ["iminente", "banca", "autorizado", "autorização", "cebraspe", "fgv", "vunesp"]):
        return "media"
    else:
        return "normal"

def sync_estrategia_news():
    """Fetches real news EXCLUSIVELY about Police Careers from Estratégia Concursos & Gran Cursos."""
    urls = [
        {"url": "https://concursos.estrategia.com/portal/feed/", "source": "Estratégia Concursos"},
        {"url": "https://blog.grancursosonline.com.br/feed/", "source": "Gran Cursos"}
    ]
    
    new_items_count = 0
    import xml.etree.ElementTree as ET
    
    try:
        with httpx.Client(headers=HEADERS, timeout=12.0, follow_redirects=True) as client:
            for src in urls:
                try:
                    resp = client.get(src["url"])
                    if resp.status_code != 200:
                        continue
                    
                    root = ET.fromstring(resp.content)
                    channel = root.find("channel")
                    if channel is None:
                        continue
                    
                    with get_db() as conn:
                        cursor = conn.cursor()
                        for item in channel.findall("item"):
                            title = (item.findtext("title") or "").strip()
                            link = (item.findtext("link") or "").strip()
                            description = (item.findtext("description") or "").strip()
                            
                            if not title:
                                continue
                            
                            clean_desc = re.sub(r'<[^>]+>', '', description).strip()
                            if len(clean_desc) > 320:
                                clean_desc = clean_desc[:317] + "..."
                                
                            # Strict police news filtering
                            if not is_strictly_police_news(title, clean_desc):
                                continue
                                
                            cursor.execute("SELECT id FROM news_feed WHERE link = ? OR title = ?", (link, title))
                            if cursor.fetchone():
                                continue
                                
                            priority = calc_news_priority(title, clean_desc)
                            category = detect_agency_type(f"{title} {clean_desc}")
                            formatted_date = datetime.date.today().strftime("%d/%m/%Y")
                            
                            cursor.execute("""
                            INSERT INTO news_feed (title, source, category, link, pub_date, summary, is_pinned, priority)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """, (title, src["source"], category, link, formatted_date, clean_desc, 1 if priority == "alta" else 0, priority))
                            new_items_count += 1
                except Exception as inner_e:
                    print(f"Erro ao buscar feed {src['source']}: {inner_e}")
                    continue

        return {
            "success": True, 
            "new_items": new_items_count, 
            "message": f"Central de Notícias Policiais atualizada! {new_items_count} novas notícias operacionais catalogadas com prioridade."
        }
    except Exception as e:
        print("Erro geral ao sincronizar notícias policiais:", e)
        return {"success": False, "error": str(e)}

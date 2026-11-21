"""
QAP Concursos v2.0 - Backup & Restore Manager
Utilitario de seguranca operacional para criacao e restauracao de backups.
"""

import sys
import os
import shutil
import zipfile
import datetime
import sqlite3
import stat
import time

def safe_rmtree(path):
    if not os.path.exists(path):
        return
    # Remove readonly flags first
    for root, dirs, files in os.walk(path):
        for f in files:
            try:
                os.chmod(os.path.join(root, f), stat.S_IWRITE)
            except Exception:
                pass
        for d in dirs:
            try:
                os.chmod(os.path.join(root, d), stat.S_IWRITE)
            except Exception:
                pass
    shutil.rmtree(path, ignore_errors=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("DATA_DIR", "").strip()
BACKUPS_DIR = os.path.join(DATA_DIR or BASE_DIR, "backups")
DB_FILE = os.path.join(DATA_DIR or BASE_DIR, "concursos.db")
APP_DIR = os.path.join(BASE_DIR, "app")

FILES_TO_BACKUP = [
    "run.bat",
    "run_lan.py",
    "iniciar_rede_local.bat",
    "liberar_firewall.bat",
    "requirements.txt",
    "README.md",
    "backup_manager.py",
    "criar_backup.bat",
    "restaurar_backup.bat",
]

def ensure_backups_dir():
    if not os.path.exists(BACKUPS_DIR):
        os.makedirs(BACKUPS_DIR, exist_ok=True)

def safe_db_copy(src, dst):
    """Safely copies SQLite database using sqlite3 backup API if possible."""
    try:
        src_conn = sqlite3.connect(src)
        dst_conn = sqlite3.connect(dst)
        with dst_conn:
            src_conn.backup(dst_conn)
        dst_conn.close()
        src_conn.close()
    except Exception:
        shutil.copy2(src, dst)

def create_backup(tag=None):
    ensure_backups_dir()
    now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup_v2.0_{tag or now_str}"
    target_folder = os.path.join(BACKUPS_DIR, backup_name)
    target_zip = os.path.join(BACKUPS_DIR, f"{backup_name}.zip")

    if os.path.exists(target_folder):
        safe_rmtree(target_folder)
    os.makedirs(target_folder, exist_ok=True)

    print("=" * 65)
    print("      🛡️  QAP CONCURSOS v2.0 - CRIANDO BACKUP OPERACIONAL  🛡️")
    print("=" * 65)

    # 1. Backup Database
    if os.path.exists(DB_FILE):
        dst_db = os.path.join(target_folder, "concursos.db")
        safe_db_copy(DB_FILE, dst_db)
        print("  [+] Banco de Dados (concursos.db) copiado com integridade.")

    # 2. Backup app/ directory (backend, static, templates)
    if os.path.exists(APP_DIR):
        dst_app = os.path.join(target_folder, "app")
        shutil.copytree(APP_DIR, dst_app, dirs_exist_ok=True)
        print("  [+] Codigo Fonte & Layout (/app) copiado com sucesso.")

    # 3. Backup root scripts
    for fname in FILES_TO_BACKUP:
        src_f = os.path.join(BASE_DIR, fname)
        if os.path.exists(src_f):
            shutil.copy2(src_f, os.path.join(target_folder, fname))
    print("  [+] Scripts de inicializacao copiados com sucesso.")

    # 4. Generate ZIP archive
    with zipfile.ZipFile(target_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(target_folder):
            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, target_folder)
                zipf.write(abs_path, rel_path)

    print("  [+] Pacote comprimido ZIP gerado com sucesso.")
    print("-----------------------------------------------------------------")
    print(f"  ✓ Pasta do Backup:  {target_folder}")
    print(f"  ✓ Arquivo ZIP:      {target_zip}")
    print("=" * 65)
    return target_folder, target_zip

def auto_backup_db(max_keep=10):
    """Cria backup automático do banco na inicialização, mantendo os últimos `max_keep` arquivos."""
    try:
        if not os.path.exists(DB_FILE):
            return None
        auto_dir = os.path.join(BACKUPS_DIR, "auto")
        os.makedirs(auto_dir, exist_ok=True)
        now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        dst_db = os.path.join(auto_dir, f"auto_concursos_{now_str}.db")
        safe_db_copy(DB_FILE, dst_db)

        # Prune older auto-backups beyond max_keep
        files = [
            os.path.join(auto_dir, f)
            for f in os.listdir(auto_dir)
            if f.startswith("auto_concursos_") and f.endswith(".db")
        ]
        files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
        for old_file in files[max_keep:]:
            try:
                os.remove(old_file)
            except Exception:
                pass
        return dst_db
    except Exception as e:
        print(f"  [!] Aviso no backup automático: {e}")
        return None


def list_backups():
    ensure_backups_dir()
    entries = []
    for item in os.listdir(BACKUPS_DIR):
        if item == "auto":
            continue
        full_path = os.path.join(BACKUPS_DIR, item)
        if os.path.isdir(full_path):
            entries.append((item, full_path, os.path.getmtime(full_path)))
    entries.sort(key=lambda x: x[2], reverse=True)
    return entries

def restore_backup(backup_folder_path=None):
    ensure_backups_dir()
    backups = list_backups()
    if not backups:
        print("[ERRO] Nenhum backup encontrado na pasta 'backups/'!")
        return False

    if not backup_folder_path:
        print("=" * 65)
        print("    🛡️  QAP CONCURSOS v2.0 - RESTAURACAO DE BACKUP TÁTICO  🛡️")
        print("=" * 65)
        print("Backups disponiveis:")
        for idx, (name, path, mtime) in enumerate(backups):
            date_str = datetime.datetime.fromtimestamp(mtime).strftime("%d/%m/%Y %H:%M:%S")
            print(f"  [{idx + 1}] {name}  (Criado em: {date_str})")
        print()
        
        try:
            choice = input(f"Selecione o numero do backup para restaurar [1-{len(backups)}] (ou Enter para o 1): ").strip()
            if not choice:
                selected_idx = 0
            else:
                selected_idx = int(choice) - 1
            if selected_idx < 0 or selected_idx >= len(backups):
                print("[ERRO] Opcao invalida!")
                return False
            backup_folder_path = backups[selected_idx][1]
        except Exception:
            backup_folder_path = backups[0][1]

    print(f"\nRestaurando a partir de: {backup_folder_path} ...")

    # Safety auto-backup of current DB before overwrite
    if os.path.exists(DB_FILE):
        safety_bkp = os.path.join(BACKUPS_DIR, f"pre_restore_safety_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
        safe_db_copy(DB_FILE, safety_bkp)
        print(f"  [+] Backup preventivo do banco atual salvo em: {os.path.basename(safety_bkp)}")

    # 1. Restore Database
    backup_db = os.path.join(backup_folder_path, "concursos.db")
    if os.path.exists(backup_db):
        safe_db_copy(backup_db, DB_FILE)
        print("  ✓ Banco de dados (concursos.db) restaurado com sucesso.")

    # 2. Restore app folder
    backup_app = os.path.join(backup_folder_path, "app")
    if os.path.exists(backup_app):
        shutil.copytree(backup_app, APP_DIR, dirs_exist_ok=True)
        print("  ✓ Codigo-fonte e arquivos (/app) restaurados com sucesso.")

    print("\n[SUCESSO] Restauracao concluida com exito!")
    print("Agora voce pode iniciar o sistema executando run.bat.")
    print("=" * 65)
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].lower() == "restore":
        restore_backup()
    elif len(sys.argv) > 1 and sys.argv[1].lower() == "create":
        tag = sys.argv[2] if len(sys.argv) > 2 else None
        create_backup(tag)
    else:
        # Default action: create backup
        create_backup()

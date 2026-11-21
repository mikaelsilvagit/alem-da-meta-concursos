import sys
import os
import socket
import webbrowser
import subprocess

def get_lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def main():
    default_port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            port = default_port
    else:
        # Check if environment variable set or default
        port_env = os.environ.get("QAP_PORT")
        if port_env:
            try:
                port = int(port_env)
            except ValueError:
                port = default_port
        else:
            port = default_port

    lan_ip = get_lan_ip()
    local_url = f"http://localhost:{port}"
    lan_url = f"http://{lan_ip}:{port}"

    print("=" * 68)
    print("     🛡️  QAP CONCURSOS v2.0 - CENTRO DE OPERAÇÕES POLICIAIS  🛡️")
    print("                 SERVIDOR DE REDE LOCAL (LAN)")
    print("=" * 68)
    print()
    print(f"  [+] Endereço IP da Máquina:  {lan_ip}")
    print(f"  [+] Porta Operacional:       {port}")
    print()
    print("  ------------------------------------------------------------")
    print(f"  💻 ACESSO NESTE COMPUTADOR:")
    print(f"     -> {local_url}")
    print()
    print(f"  📱 ACESSO NO CELULAR / TABLET / OUTROS DISPOSITIVOS NO WI-FI:")
    print(f"     -> {lan_url}")
    print("  ------------------------------------------------------------")
    print()
    print("  Dica: Certifique-se de que o celular está conectado na")
    print("  mesma rede Wi-Fi deste computador.")
    print()
    print("  Pressione Ctrl + C no terminal para encerrar o servidor.")
    print("=" * 68)
    print()

    # Try to open local browser
    try:
        webbrowser.open(local_url)
    except Exception:
        pass

    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)

if __name__ == "__main__":
    main()

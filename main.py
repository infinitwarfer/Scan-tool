
import argparse
import threading
import time
import os
from colorama import init, Fore, Style
from network_utils import detect_local_network, parse_manual_network
from scanner import NetworkScanner


init(autoreset=True)


def banner():

    print(Fore.RED + r"""
           ██▓ ███▄    █   █████▒██▓ ███▄    █  ██▓▄▄▄█████▓▓██   ██▓
          ▓██▒ ██ ▀█   █ ▓██   ▒▓██▒ ██ ▀█   █ ▓██▒▓  ██▒ ▓▒ ▒██  ██▒
          ▒██▒▓██  ▀█ ██▒▒████ ░▒██▒▓██  ▀█ ██▒▒██▒▒ ▓██░ ▒░  ▒██ ██░
          ░██░▓██▒  ▐▌██▒░▓█▒  ░░██░▓██▒  ▐▌██▒░██░░ ▓██▓ ░   ░ ▐██▓░
          ░██░▒██░   ▓██░░▒█░   ░██░▒██░   ▓██░░██░  ▒██▒ ░   ░ ██▒▓░
          ░▓  ░ ▒░   ▒ ▒  ▒ ░   ░▓  ░ ▒░   ▒ ▒ ░▓    ▒ ░░      ██▒▒▒
           ▒ ░░ ░░   ░ ▒░ ░      ▒ ░░ ░░   ░ ▒░ ▒ ░    ░      ▓██ ░▒░
           ▒ ░   ░   ░ ░  ░ ░    ▒ ░   ░   ░ ░  ▒ ░  ░        ▒ ▒ ░░
          ░   ░           ░          ░           ░  ░              ░ ░
""")

    print(
        Fore.LIGHTBLACK_EX +
        "              NETWORK SCANNER -- INFINITY"
    )

    print(
        Fore.LIGHTBLACK_EX +
        "                       uso autorizado"
    )




def limpar_tela():

    os.system(
        "cls" if os.name == "nt" else "clear"
    )


def linha():

    print(
        Fore.RED +
        "═" * 68
    )


def titulo(texto):

    linha()

    print(
        Fore.RED +
        f"                      {texto}"
    )

    linha()


def pausar():

    input(
        Fore.WHITE +
        "\n  Pressione ENTER para continuar..."
    )




def parse_args():

    parser = argparse.ArgumentParser(
        description="Ferramenta de descoberta de dispositivos na rede local."
    )

    parser.add_argument(
        "--network",
        "-n",
        type=str,
        default=None,
        help="Rede em formato CIDR."
    )

    parser.add_argument(
        "--workers",
        "-w",
        type=int,
        default=50,
        help="Número máximo de threads."
    )

    parser.add_argument(
        "--timeout",
        "-t",
        type=int,
        default=800,
        help="Timeout do ping em milissegundos."
    )

    return parser.parse_args()




def mostrar_portas(scanner, ip):

    portas = scanner.get_port_status(ip)

    if not portas:

        print(
            Fore.LIGHTBLACK_EX +
            "       Portas: Nenhuma informação disponível"
        )

        return

    abertas = []
    filtradas = []

    for porta, estado in sorted(portas.items()):

        if estado == "open":

            abertas.append(porta)

        elif estado == "filtered":

            filtradas.append(porta)

    print(
        Fore.WHITE +
        "       Portas:"
    )


    if abertas:

        print(
            Fore.GREEN +
            "         OPEN:     " +
            ", ".join(
                str(porta)
                for porta in abertas
            )
        )

    else:

        print(
            Fore.LIGHTBLACK_EX +
            "         OPEN:     nenhuma"
        )

    

    if filtradas:

        print(
            Fore.YELLOW +
            "         FILTERED: " +
            ", ".join(
                str(porta)
                for porta in filtradas
            )
        )

    else:

        print(
            Fore.LIGHTBLACK_EX +
            "         FILTERED: nenhuma"
        )



def mostrar_dispositivos(devices, scanner):

    if not devices:

        print(
            Fore.YELLOW +
            "\n  [!] Nenhum dispositivo encontrado."
        )

        return

    print()

    linha()

    print(
        Fore.RED +
        "                       DISPOSITIVOS"
    )

    linha()

    for numero, device in enumerate(devices, 1):

        ip = getattr(
            device,
            "ip",
            "Desconhecido"
        )

        mac = getattr(
            device,
            "mac",
            "Desconhecido"
        )

        hostname = getattr(
            device,
            "hostname",
            "Desconhecido"
        )

        fabricante = getattr(
            device,
            "vendor",
            "Desconhecido"
        )

        print()

        print(
            Fore.WHITE +
            f"  [{numero:02}] " +
            Fore.LIGHTRED_EX +
            f"{ip}"
        )

        print(
            Fore.LIGHTBLACK_EX +
            f"       MAC:        {mac}"
        )

        print(
            Fore.WHITE +
            f"       Hostname:   {hostname}"
        )

        print(
            Fore.WHITE +
            f"       Fabricante: {fabricante}"
        )

        mostrar_portas(
            scanner,
            ip
        )

    print()

    linha()

    print(
        Fore.GREEN +
        f"  [+] {len(devices)} dispositivo(s) encontrado(s)"
    )

    linha()


def executar_scan(args):

    limpar_tela()

    banner()

    print()

    titulo("NETWORK SCANNER")

    print()


    print(
        Fore.YELLOW +
        "  [*] Detectando rede..."
    )

    if args.network:

        try:

            network = parse_manual_network(
                args.network
            )

            print(
                Fore.GREEN +
                f"  [+] Rede definida: " +
                Fore.WHITE +
                f"{network}"
            )

        except Exception as exc:

            print(
                Fore.RED +
                f"\n  [!] Erro: {exc}"
            )

            pausar()

            return

    else:

        try:

            info = detect_local_network()

        except RuntimeError as exc:

            print(
                Fore.RED +
                f"\n  [!] Erro: {exc}"
            )

            pausar()

            return

        network = info.network

        print(
            Fore.GREEN +
            f"  [+] IP local: " +
            Fore.WHITE +
            f"{info.local_ip}"
        )

        print(
            Fore.GREEN +
            f"  [+] Máscara: " +
            Fore.WHITE +
            f"{info.netmask}"
        )

        print(
            Fore.GREEN +
            f"  [+] Rede: " +
            Fore.WHITE +
            f"{network}"
        )

    total_hosts = (
        network.num_addresses - 2
        if network.num_addresses > 2
        else network.num_addresses
    )

    checked_count = {
        "value": 0
    }

    devices = []

    state_lock = threading.Lock()

    start_time = time.time()

    def on_device_found(device):

        with state_lock:

            devices.append(device)

    def on_host_checked(ip):

        with state_lock:

            checked_count["value"] += 1

    scanner = NetworkScanner(

        network=network,

        max_workers=args.workers,

        timeout_ms=args.timeout,

        on_device_found=on_device_found,

        on_host_checked=on_host_checked,

        on_status=lambda msg: None
    )

    print()

    linha()

    print(
        Fore.YELLOW +
        "  [*] Iniciando descoberta de dispositivos..."
    )

    print(
        Fore.LIGHTBLACK_EX +
        f"  [*] Hosts para verificar: {total_hosts}"
    )

    print(
        Fore.LIGHTBLACK_EX +
        f"  [*] Workers: {args.workers}"
    )

    print(
        Fore.LIGHTBLACK_EX +
        f"  [*] Timeout ping: {args.timeout} ms"
    )

    print(
        Fore.LIGHTBLACK_EX +
        "  [*] Scan de portas: ATIVADO"
    )

    print(
        Fore.LIGHTBLACK_EX +
        "  [*] Portas: 21, 22, 23, 25, 53, 80, 110, 135,"
    )

    print(
        Fore.LIGHTBLACK_EX +
        "             139, 143, 443, 445, 587, 993, 995,"
    )

    print(
        Fore.LIGHTBLACK_EX +
        "             1723, 3306, 3389, 5900, 8080"
    )

    linha()

    print()

    scan_thread = threading.Thread(
        target=scanner.run,
        daemon=True
    )

    scan_thread.start()

    stopped_by_user = False

    try:

        while scan_thread.is_alive():

            with state_lock:

                checked = checked_count["value"]

                encontrados = len(devices)

            elapsed = time.time() - start_time

            porcentagem = (
                (checked / total_hosts) * 100
                if total_hosts > 0
                else 100
            )

            print(
                Fore.WHITE +
                f"\r  [*] Progresso: "
                f"{checked}/{total_hosts} "
                f"({porcentagem:.1f}%) "
                f"| Encontrados: {encontrados} "
                f"| Tempo: {elapsed:.1f}s",
                end="",
                flush=True
            )

            time.sleep(0.2)

        with state_lock:

            checked = checked_count["value"]

            current_devices = list(
                devices
            )

    except KeyboardInterrupt:

        stopped_by_user = True

        print(
            Fore.RED +
            "\n\n  [!] Interrompendo scan..."
        )

        scanner.stop()

        scan_thread.join(
            timeout=5
        )

        current_devices = list(
            devices
        )

    print("\n")

    if stopped_by_user:

        print(
            Fore.RED +
            "  [!] Scan interrompido pelo usuário."
        )

    else:

        print(
            Fore.GREEN +
            "  [+] Scan concluído."
        )

    elapsed = time.time() - start_time

    print(
        Fore.WHITE +
        f"  [*] Hosts verificados: {checked}"
    )

    print(
        Fore.WHITE +
        f"  [*] Dispositivos encontrados: "
        f"{len(devices)}"
    )

    print(
        Fore.WHITE +
        f"  [*] Tempo total: {elapsed:.2f}s"
    )

    mostrar_dispositivos(
        current_devices,
        scanner
    )

    pausar()



def main():

    args = parse_args()

    executar_scan(args)


if __name__ == "__main__":

    main()
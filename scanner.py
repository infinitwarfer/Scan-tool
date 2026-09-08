
import platform
import re
import socket
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from ipaddress import IPv4Network
from device import Device
from vendor_lookup import VendorLookup
IS_WINDOWS = platform.system().lower() == "windows"
socket.setdefaulttimeout(1.5)


DEFAULT_PORTS = [

    21,      # FTP
    22,      # SSH
    23,      # Telnet
    25,      # SMTP
    53,      # DNS
    80,      # HTTP
    110,     # POP3
    135,     # MS RPC
    139,     # NetBIOS
    143,     # IMAP
    443,     # HTTPS
    445,     # SMB
    554,     #RTSP
    587,     # SMTP
    993,     # IMAPS
    995,     # POP3S
    1723,    # PPTP
    3306,    # MySQL
    3389,    # RDP
    5900,    # VNC
    8080,    # HTTP alternativo

]

def _ping(
    ip: str,
    timeout_ms: int = 800
) -> bool:


    if IS_WINDOWS:

        cmd = [
            "ping",
            "-n",
            "1",
            "-w",
            str(timeout_ms),
            ip
        ]

    else:

        timeout_s = max(
            1,
            timeout_ms // 1000
        )

        cmd = [
            "ping",
            "-c",
            "1",
            "-W",
            str(timeout_s),
            ip
        ]

    try:

        result = subprocess.run(

            cmd,

            stdout=subprocess.DEVNULL,

            stderr=subprocess.DEVNULL,

            timeout=(timeout_ms / 1000) + 1,

        )

        return result.returncode == 0

    except Exception:

        return False

def _get_mac_from_arp_table(
    ip: str
) -> str:

    """
    Consulta a tabela ARP do sistema operacional.
    """

    try:

        if IS_WINDOWS:

            cmd = [
                "arp",
                "-a",
                ip
            ]

        else:

            cmd = [
                "arp",
                "-n",
                ip
            ]

        output = subprocess.run(

            cmd,

            stdout=subprocess.PIPE,

            stderr=subprocess.DEVNULL,

            timeout=2,

            text=True,

        ).stdout

        match = re.search(

            r"([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}",

            output

        )

        if match:

            return (
                match.group(0)
                .replace("-", ":")
                .upper()
            )

    except Exception:

        pass

    return "Desconhecido"

def _get_hostname(
    ip: str
) -> str:

    """
    Tenta resolver o hostname através
    de DNS reverso.
    """

    try:

        return socket.gethostbyaddr(
            ip
        )[0]

    except Exception:

        return "Desconhecido"


def _scan_port(
    ip: str,
    port: int,
    timeout: float = 0.5
) -> str:

    """
    Testa uma porta TCP.

    Retorna:

        open
        closed
        filtered
    """

    sock = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    sock.settimeout(
        timeout
    )

    try:

        resultado = sock.connect_ex(
            (
                ip,
                port
            )
        )


        if resultado == 0:

            return "open"

        if resultado in (
            61,
            111,
            10061
        ):

            return "closed"

        return "filtered"

    except socket.timeout:

        return "filtered"

    except OSError as exc:

        if getattr(
            exc,
            "errno",
            None
        ) in (
            60,
            110,
            10060
        ):

            return "filtered"

        return "closed"

    except Exception:

        return "filtered"

    finally:

        sock.close()

def _scan_ports(
    ip: str,
    ports,
    timeout: float = 0.5
):

    """
    Verifica todas as portas especificadas.

    Retorna:

        {
            22: "open",
            80: "open",
            443: "filtered"
        }
    """

    results = {}

    for port in ports:

        results[port] = _scan_port(

            ip,

            port,

            timeout

        )

    return results


class NetworkScanner:

    """
    Orquestra a descoberta de dispositivos
    e o scan de portas.
    """

    def __init__(

        self,

        network: IPv4Network,

        max_workers: int = 50,

        timeout_ms: int = 800,

        on_device_found=None,

        on_host_checked=None,

        on_status=None,

        scan_ports: bool = True,

        ports=None,

        port_timeout: float = 0.5,

    ):

        self.network = network

        self.max_workers = max_workers

        self.timeout_ms = timeout_ms

        self.on_device_found = (

            on_device_found

            or (
                lambda device: None
            )

        )

        self.on_host_checked = (

            on_host_checked

            or (
                lambda ip: None
            )

        )

        self.on_status = (

            on_status

            or (
                lambda msg: None
            )

        )

        self._stop_event = (
            threading.Event()
        )

        self._vendor_lookup = (
            VendorLookup()
        )

        self.devices_found = []

        self._lock = (
            threading.Lock()
        )

        self.scan_ports = scan_ports

        self.ports = (

            ports

            if ports is not None

            else DEFAULT_PORTS

        )

        self.port_timeout = (
            port_timeout
        )

        self.port_results = {}

    def stop(self):


        self._stop_event.set()


    def _scan_host(
        self,
        ip: str
    ):

        if self._stop_event.is_set():

            return None

        try:

            if not _ping(
                ip,
                self.timeout_ms
            ):

                return None

            mac = _get_mac_from_arp_table(
                ip
            )

            hostname = _get_hostname(
                ip
            )

            vendor = (
                self._vendor_lookup
                .get_vendor(mac)
            )


            device = Device(

                ip=ip,

                mac=mac,

                hostname=hostname,

                vendor=vendor

            )

            if self.scan_ports:

                self.on_status(

                    f"Verificando portas de {ip}..."

                )

                ports = _scan_ports(

                    ip,

                    self.ports,

                    self.port_timeout

                )

                with self._lock:

                    self.port_results[
                        ip
                    ] = ports


            with self._lock:

                self.devices_found.append(
                    device
                )

            self.on_device_found(
                device
            )

            return device

        except Exception:

            return None

        finally:

            self.on_host_checked(
                ip
            )


    def run(self):


        hosts = list(
            self.network.hosts()
        )

        self.on_status(

            f"Escaneando {len(hosts)} "
            f"endereços possíveis..."

        )

        with ThreadPoolExecutor(

            max_workers=self.max_workers

        ) as executor:

            futures = {

                executor.submit(

                    self._scan_host,

                    str(ip)

                ): ip

                for ip in hosts

            }

            for future in as_completed(
                futures
            ):

                if self._stop_event.is_set():

                    for f in futures:

                        f.cancel()

                    self.on_status(
                        "Scan interrompido pelo usuário."
                    )

                    break


        if not self._stop_event.is_set():

            self.on_status(
                "Scan concluído."
            )


        return self.devices_found

    def get_port_status(
        self,
        ip: str
    ):

        with self._lock:

            return dict(

                self.port_results.get(

                    ip,

                    {}

                )

            )
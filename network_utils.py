

import ipaddress
import socket

import psutil


class NetworkInfo:

    def __init__(self, local_ip: str, netmask: str, network: ipaddress.IPv4Network):
        self.local_ip = local_ip
        self.netmask = netmask
        self.network = network

    def __str__(self):
        return f"{self.local_ip}/{self.netmask} -> rede {self.network}"


def _get_default_local_ip() -> str:
   
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()


def detect_local_network() -> NetworkInfo:

    local_ip = _get_default_local_ip()


    for interface_name, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family == socket.AF_INET and addr.address == local_ip:
                netmask = addr.netmask
                if not netmask:
                    continue
                interface = ipaddress.IPv4Interface(f"{local_ip}/{netmask}")
                return NetworkInfo(
                    local_ip=local_ip,
                    netmask=netmask,
                    network=interface.network,
                )

    raise RuntimeError(
        "Não foi possível detectar automaticamente a rede local. "
        "Verifique sua conexão de rede ou informe a rede manualmente "
        "com --network (ex: --network 192.168.1.0/24)."
    )


def parse_manual_network(cidr: str) -> ipaddress.IPv4Network:
    return ipaddress.ip_network(cidr, strict=False)

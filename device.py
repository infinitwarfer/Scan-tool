
from dataclasses import dataclass

@dataclass
class Device:
  
    ip: str
    mac: str = "Desconhecido"
    hostname: str = "Desconhecido"
    vendor: str = "Desconhecido"
    status: str = "ativo" 
                         

    def as_row(self) -> tuple:
        
        return (self.ip, self.mac, self.hostname, self.vendor, self.status)

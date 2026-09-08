
from mac_vendor_lookup import MacLookup

class VendorLookup:


    def __init__(self):
        self._lookup = MacLookup()
        self._ready = False
        self._try_update_database()

    def _try_update_database(self):
     
        try:
            self._lookup.update_vendors()
            self._ready = True
        except Exception:
           
            self._ready = True

    def get_vendor(self, mac: str) -> str:
        
        if not mac or mac == "Desconhecido":
            return "Desconhecido"
        try:
            return self._lookup.lookup(mac)
        except Exception:
            return "Desconhecido"

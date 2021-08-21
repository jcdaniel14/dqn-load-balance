class Port:
    def __init__(self, name, router, snmp_id=0, proveedor="", peer_v4="", capacidad="", threshold=90, optimal_thold=100, optimal_priority=1, os_type=5):
        self.router = router
        self.name = name
        self.gate = f"{router}:{name}"
        self.proveedor = proveedor
        self.peer_v4 = peer_v4
        self.capacidad = capacidad  # Gbps
        self.threshold = threshold
        self.optimal_thold = optimal_thold
        self.optimal_priority = optimal_priority
        self.snmp_id = snmp_id
        self.os_type = os_type

        self.current_gbps = 0  # Gbps
        self.load = 0  # Percentage
        self.available = 0
        self.optimal_available = 0
        self.return_available = 0

    def __str__(self):
        return f"Gate:{self.router}:{self.name} - Provider:{self.proveedor} - Capacidad:{self.capacidad} - CurrentBW:{self.current_gbps} - Avail:{self.available} - Priority:{self.optimal_priority} - OptimalAvail:{self.optimal_available}"

    def calculate_available(self):
        self.available = round((self.capacidad * self.threshold / 100) - self.current_gbps, 2)
        self.return_available = round((self.capacidad * self.threshold*0.9 / 100) - self.current_gbps, 2)
        self.optimal_available = round((self.capacidad * self.optimal_thold / 100) - self.current_gbps, 2)
        self.available = 0 if self.available < 0 else self.available
        self.optimal_available = 0 if self.optimal_available < 0 else self.optimal_available

from typing import Dict, Optional

class TenantResolver:
    @staticmethod
    def resolve_from_header(headers: Dict[str, str], header_name: str = "x-tenant-id") -> Optional[str]:
        for k, v in headers.items():
            if k.lower() == header_name.lower():
                return v
        return None

    @staticmethod
    def resolve_from_host(host: str) -> Optional[str]:
        parts = host.split('.')
        if len(parts) >= 3:
            return parts[0]
        return None

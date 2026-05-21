import subprocess
from src.backend.app.core.config import settings

class VPNService:
    def is_connected(self) -> bool:
        """
        Verifica se a Mullvad VPN está conectada via CLI.
        """
        try:
            result = subprocess.run(["mullvad", "status"], capture_output=True, text=True, timeout=5)
            # O comando retorna algo como "Connected to <location>" ou "Disconnected"
            return "Connected" in result.stdout
        except Exception as e:
            print(f"[VPN SERVICE] Erro ao verificar status da Mullvad: {e}")
            return False

    def ensure_connected(self):
        """
        Lança uma exceção se a VPN for obrigatória e não estiver conectada.
        """
        if settings.MULLVAD_REQUIRED and not self.is_connected():
            raise Exception("Download bloqueado: Mullvad VPN não está conectada e MULLVAD_REQUIRED está ativo.")

vpn_service = VPNService()

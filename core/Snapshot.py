from dataclasses import dataclass
from typing import Optional

@dataclass
class Snapshot:
    id_rastro: int
    mensagem: str
    timestamp: str
    caminho_relativo: str
    tamanho: str

    def para_json(self) -> dict:
        return {
            "id_rastro": self.id_rastro,
            "mensagem": self.mensagem,
            "timestamp": self.timestamp,
            "caminho_relativo": self.caminho_relativo,
            "tamanho": self.tamanho
        }

    @staticmethod
    def de_json(d: dict) -> 'Snapshot':
        return Snapshot(
            id_rastro=d["id_rastro"],
            mensagem=d["mensagem"],
            timestamp=d["timestamp"],
            caminho_relativo=d["caminho_relativo"],
            tamanho=d["tamanho"]
        )

from abc import ABC, abstractmethod
from pathlib import Path


class ContestInitializer(ABC):
    def __init__(self, name: str, root: Path):
        self.name = name
        self.root = root

    @abstractmethod
    def init(self):
        pass

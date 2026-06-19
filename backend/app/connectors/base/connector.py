from abc import ABC, abstractmethod
from backend.app.connectors.base.models import LineageGraph


class BaseConnector(ABC):
    """
    Abstract Base Class for all lineage metadata connectors.
    """

    @abstractmethod
    def ingest(self, *args, **kwargs) -> LineageGraph:
        """
        Runs the extraction and parsing logic, returning a canonical LineageGraph.
        """
        pass

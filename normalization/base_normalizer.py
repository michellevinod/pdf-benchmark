from abc import ABC, abstractmethod


class BaseNormalizer(ABC):
    """
    Base class for converting parser-specific output into
    a common normalized schema.
    """

    @abstractmethod
    def normalize(
        self,
        raw_json: dict,
    ) -> dict:
        """
        Converts a parser-specific JSON into the common schema.
        """
        pass
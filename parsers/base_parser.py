from abc import ABC, abstractmethod


class BaseParser(ABC):
    """
    Abstract base class for all PDF parsers.
    """

    @abstractmethod
    def parse(
        self,
        pdf_path: str,
        markdown_path: str,
        json_path: str,
    ) -> str:
        """
        Parse the PDF and save both Markdown and JSON outputs.

        Args:
            pdf_path: Path to input PDF.
            markdown_path: Path to save Markdown.
            json_path: Path to save JSON.

        Returns:
            Extracted markdown as a string.
        """
        pass
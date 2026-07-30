import fitz


class ReferenceExtractor:
    """
    Extracts reference content directly from the benchmark PDF.

    The extracted content acts as the ground truth for evaluating
    parser outputs.
    """

    @staticmethod
    def extract_text(
        pdf_path: str,
    ) -> list[str]:
        """
        Extracts plain text from every page of the PDF.

        Returns:
            List[str]:
                One text string per page.
        """

        document = fitz.open(pdf_path)

        pages = []

        try:
            for page in document:
                text = page.get_text("text").strip()
                pages.append(text)

        finally:
            document.close()

        return pages

    @staticmethod
    def extract_table_count(
        pdf_path: str,
    ) -> int:
        """
        Extracts the number of tables detected in the PDF.
        """

        document = fitz.open(pdf_path)

        try:
            total_tables = 0

            for page in document:
                total_tables += len(
                    page.find_tables().tables
                )

            return total_tables

        finally:
            document.close()

    @staticmethod
    def extract_image_count(
        pdf_path: str,
    ) -> int:
        """
        Extracts the number of images in the PDF.
        """

        document = fitz.open(pdf_path)

        try:
            total_images = 0

            for page in document:
                total_images += len(
                    page.get_images(
                        full=True,
                    )
                )

            return total_images

        finally:
            document.close()
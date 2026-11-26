import io
from pathlib import Path

import pandas as pd

from pypdf import PdfReader
from docx import Document
from pptx import Presentation


SUPPORTED_FORMATS = {
    ".pdf",
    ".docx",
    ".pptx",
    ".xlsx",
    ".csv",
    ".txt"
}


class DocumentProcessingError(Exception):
    pass


class DocumentLoader:

    def extract_text(self, file_bytes: bytes, filename: str):

        extension = Path(filename).suffix.lower()

        if extension not in SUPPORTED_FORMATS:
            raise DocumentProcessingError(
                f"Unsupported file format: {extension}"
            )

        if not file_bytes:
            raise DocumentProcessingError(
                "The uploaded file is empty."
            )

        try:

            if extension == ".pdf":
                text = self._load_pdf(file_bytes)

            elif extension == ".docx":
                text = self._load_docx(file_bytes)

            elif extension == ".pptx":
                text = self._load_pptx(file_bytes)

            elif extension == ".xlsx":
                text = self._load_xlsx(file_bytes)

            elif extension == ".csv":
                text = self._load_csv(file_bytes)

            elif extension == ".txt":
                text = self._load_txt(file_bytes)

            text = text.strip()

            if not text:
                raise DocumentProcessingError(
                    "No readable text found in the document."
                )

            return {
                "success": True,
                "filename": filename,
                "file_type": extension,
                "character_count": len(text),
                "text": text
            }

        except DocumentProcessingError:
            raise

        except Exception as error:
            raise DocumentProcessingError(
                f"Document extraction failed: {error}"
            ) from error

    def _load_pdf(self, file_bytes):

        reader = PdfReader(io.BytesIO(file_bytes))

        pages = []

        for page_number, page in enumerate(reader.pages, start=1):

            page_text = page.extract_text() or ""

            pages.append(
                f"\n--- PAGE {page_number} ---\n{page_text}"
            )

        return "\n".join(pages)

    def _load_docx(self, file_bytes):

        document = Document(io.BytesIO(file_bytes))

        content = []

        for paragraph in document.paragraphs:

            if paragraph.text.strip():
                content.append(paragraph.text)

        for table in document.tables:

            for row in table.rows:

                row_data = [
                    cell.text.strip()
                    for cell in row.cells
                ]

                content.append(" | ".join(row_data))

        return "\n".join(content)

    def _load_pptx(self, file_bytes):

        presentation = Presentation(io.BytesIO(file_bytes))

        slides_content = []

        for slide_number, slide in enumerate(
            presentation.slides,
            start=1
        ):

            slide_text = []

            for shape in slide.shapes:

                if hasattr(shape, "text") and shape.text.strip():
                    slide_text.append(shape.text)

            slides_content.append(
                f"\n--- SLIDE {slide_number} ---\n"
                + "\n".join(slide_text)
            )

        return "\n".join(slides_content)

    def _load_xlsx(self, file_bytes):

        workbook = pd.ExcelFile(io.BytesIO(file_bytes))

        content = []

        for sheet_name in workbook.sheet_names:

            dataframe = pd.read_excel(
                workbook,
                sheet_name=sheet_name
            )

            content.append(
                f"\n--- SHEET: {sheet_name} ---\n"
            )

            content.append(
                dataframe.to_string(index=False)
            )

        return "\n".join(content)

    def _load_csv(self, file_bytes):

        dataframe = pd.read_csv(
            io.BytesIO(file_bytes)
        )

        return dataframe.to_string(index=False)

    def _load_txt(self, file_bytes):

        return file_bytes.decode(
            "utf-8-sig",
            errors="replace"
        )


document_loader = DocumentLoader()
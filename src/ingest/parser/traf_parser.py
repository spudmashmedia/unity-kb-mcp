from .base import BaseParser
import trafilatura

class TrafilaturaHtmlParser(BaseParser):
    def parse(self, content: str) -> str:
        """Remove noise using Trafilatura."""
        try:
            result = trafilatura.extract(
                content,
                include_tables=True,
                include_formatting=True,
                favor_precision=True,
                output_format="markdown"
            )
            return result if result else ""
        except Exception as e:
            print(f"⚠️ Trafilatura error: {e}")
            return content

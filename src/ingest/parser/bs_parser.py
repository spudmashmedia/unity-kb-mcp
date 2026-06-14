from .base import BaseParser
from bs4 import BeautifulSoup

class BeautifulSoupHTMLParser(BaseParser):
    def parse(self, content: str) -> str:
        """Remove noise using BeautifulSoup."""
        soup = BeautifulSoup(content, "lxml")
    
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
    
        return soup.get_text(separator="\n", strip=True)

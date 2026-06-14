from .base import BaseParser
import re

class MarkdownParser(BaseParser):
    def parse(self, content: str) -> str:
        """Minimal markdown cleanup - preserve structure."""
        content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
    
        lines = []
        for line in content.split('\n'):
            stripped = line.strip()
            if stripped:
                lines.append(line)
    
        return '\n'.join(lines).strip()


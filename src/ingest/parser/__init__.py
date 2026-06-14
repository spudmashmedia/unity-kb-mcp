# package
from .base import BaseParser
from .md_parser import MarkdownParser
from .bs_parser import BeautifulSoupHTMLParser
from .traf_parser import TrafilaturaHtmlParser
from typing import Optional, Any, List, Tuple, Set

def get_parser(format_type: str, algo: str) -> BaseParser:
    if format_type == "html":
        if algo == "bs":
            return BeautifulSoupHTMLParser()
        elif algo == "traf":
            return BeautifulSoupHTMLParser() 
    elif format_type == "markdown":
        return MarkdownParser() 
    else:
        raise ValueError(f"Unknown file format: {format_type}")
         

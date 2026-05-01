import re
import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Default Wikipedia articles (matching the paper, Table 7 / Table 11)
# ---------------------------------------------------------------------------
WIKI_ARTICLES = {
    # Matching (semantically related) articles
    "geography_related": "Capital_city",
    "history_related": "Treaty",
    "biology_related": "Species",
    # Mismatching (semantically unrelated) articles
    "geography_unrelated": "2012_Formula_One_season",
    "history_unrelated": "Rock_music",
    "biology_unrelated": "European_debt_crisis",
}


class WikiScraper:
    """Scraper for fetching Wikipedia articles based on the haystack config."""

    def __init__(self):
        pass

    def get_haystack_text(
        self, question_domain: str, semantic_related: bool, max_words: int = 5000
    ) -> str:
        """
        Fetch the appropriate Wikipedia article based on the haystack config.

        Parameters
        ----------
            None

        Returns
        -------
            str :
                The plain text of the selected Wikipedia article.
        """
        # Determine the article based on domain configurations of haystack
        key = f"{question_domain}_{'related' if semantic_related else 'unrelated'}"

        # Make sure article exists for a given config, then fetch and return text
        if key not in WIKI_ARTICLES:
            available = [k for k in WIKI_ARTICLES if k.startswith(question_domain)]
            raise ValueError(
                f"No article configured for key '{key}'. Available: {available}"
            )

        article_title = WIKI_ARTICLES[key]
        return self.fetch_wikipedia_text(article_title)

    def split_sentences(self, text: str) -> list[str]:
        """Split text into sentences using a regex consistent with the scraper."""
        # Insert a space after punctuation if missing before a capital letter
        text = re.sub(r'(?<=[.!?])(?=[A-Z])', ' ', text)
        # Split on . ! ? followed by whitespace and uppercase, or end of string
        pattern = re.compile(r'(?<=[.!?])\s+(?=[A-Z"])')
        parts = pattern.split(text.strip())
        return [p.strip() for p in parts if p.strip()] 

    def fetch_wikipedia_text(self, title: str, max_words: int = 5000) -> str:
        """
        Fetch plain text of a Wikipedia article via the MediaWiki API.

        Parameters
        ----------
            title : str
                The title of the Wikipedia article to fetch.
            max_words : int
                Maximum number of words to return (truncated at sentence boundary).

        Returns
        -------
            str :
                The plain text of the Wikipedia article.

        """
        # Fetch the article raw html content
        url = f"https://en.wikipedia.org/wiki/{title}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        }
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
        except Exception as e:
            raise ValueError(f"Error fetching Wikipedia article '{title}': {e}")

        # Parse the HTML content
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Remove reference/citation tags before extracting text
        for sup in soup.find_all("sup", class_="reference"):
            sup.decompose()
            
        # Extract text from the main content div if possible
        content_div = soup.find("div", {"id": "mw-content-text"})
        if content_div:
            paragraphs = content_div.find_all("p")
        else:
            paragraphs = soup.find_all("p")
            
        # Get text and filter out empty paragraphs
        # Use a space separator to prevent words in different elements from being squashed
        text_blocks = [p.get_text(separator=" ", strip=True) for p in paragraphs]
        text = " ".join([t for t in text_blocks if t])
        
        # Clean up any multiple spaces created by separator
        text = re.sub(r"\s+", " ", text)
        
        # Make sure sentences aren't squashed together (e.g. "word.Word" -> "word. Word")
        text = re.sub(r'([a-z][.!?])([A-Z])', r'\1 \2', text)
        
        # Truncate to max_words, keeping sentence boundaries if possible
        words = text.split()
        if len(words) > max_words:
            truncated_text = " ".join(words[:max_words])
            last_period = truncated_text.rfind(".")
            if last_period != -1:
                text = truncated_text[:last_period + 1]
            else:
                text = truncated_text
                
        return text

import re
from needle_haystack import NIAHGenerator, HaystackConfig, NeedleConfig
from WikiScraper import WikiScraper

def split_sentences(text: str) -> list[str]:
    """Split text into sentences using a regex consistent with the scraper."""
    # Insert a space after punctuation if missing before a capital letter
    text = re.sub(r'(?<=[.!?])(?=[A-Z])', ' ', text)
    # Split on . ! ? followed by whitespace and uppercase, or end of string
    pattern = re.compile(r'(?<=[.!?])\s+(?=[A-Z"])')
    parts = pattern.split(text.strip())
    return [p.strip() for p in parts if p.strip()] 

def get_wiki_article(haystack_config: HaystackConfig):
    # Init scraper
    scraper = WikiScraper()

    print(f"{'=' * 100}")
    print(f"Fetching Wikipedia article for {haystack_config.question_domain} {haystack_config.semantic_related}...")
    print(f"{'=' * 100}")
    
    # Grab the raw article text and save it to a file
    article = scraper.get_haystack_text(
        question_domain=haystack_config.question_domain, 
        semantic_related=haystack_config.semantic_related
    )

    # Split the raw article into sentences and save them to a file
    sentences = scraper.split_sentences(article)
    # with open(f"{haystack_config.question_domain}_article.txt", "w") as f:
    #     for i, sentence in enumerate(sentences):
    #         f.write(f"{i}: {sentence}\n")

    return article, sentences

def generate_haystacks(haystack_config: HaystackConfig, needle_config: NeedleConfig, article: str, sentences: list[str]):
    # Init generator 
    generator = NIAHGenerator(needle_config, haystack_config)

    print(f"{'=' * 100}")
    print(f"Injecting needles into {haystack_config.question_domain} {haystack_config.semantic_related}...")
    print(f"{'=' * 100}")

    haystack = generator.inject_needles(article, sentences)
    hay_sentences = split_sentences(haystack)

    # with open(f"Output_{haystack_config.question_domain}_sentences.txt", "w") as f:
    #     for i, sentence in enumerate(hay_sentences):
    #         f.write(f"{i}: {sentence}\n")

    with open(f"haystacks/{haystack_config.question_domain}_haystack.txt", "w") as f:
        f.write(haystack)


def main():
    # Geography Related
    geography_related = HaystackConfig(
        needle_set="C1",
        question_domain="geography",
        semantic_related=True,
        position="even",
        grouping="5pct_apart",
        max_words=5000,
    )

    # History Related
    history_related = HaystackConfig(
        needle_set="C1",
        question_domain="history",
        semantic_related=True,
        position="even",
        grouping="5pct_apart",
        max_words=5000,
    )

    # Biology Related 
    biology_related = HaystackConfig(
        needle_set="C1",
        question_domain="biology",
        semantic_related=True,
        position="even",
        grouping="5pct_apart",
        max_words=5000,
    )

    # Needle Configs for all
    needle_config = NeedleConfig(
        repetitions=[5, 5, 5],
        order=[0, 1, 2],
    )   

    # 1. Fetch and parse the original wiki articles
    geography_related_article, geography_related_sentences = get_wiki_article(geography_related)
    history_related_article, history_related_sentences = get_wiki_article(history_related)
    biology_related_article, biology_related_sentences = get_wiki_article(biology_related)

    # 2. Generate the haystacks with needles injected 
    generate_haystacks(geography_related, needle_config, geography_related_article, geography_related_sentences)
    generate_haystacks(history_related, needle_config, history_related_article, history_related_sentences)
    generate_haystacks(biology_related, needle_config, biology_related_article, biology_related_sentences)


if __name__ == "__main__":
    main()

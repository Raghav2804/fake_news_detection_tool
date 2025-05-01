import newspaper
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse

# Try to import newspaper, but provide fallback if it fails
try:
    from newspaper import Article, ArticleException

    NEWSPAPER_AVAILABLE = True
except ImportError:
    print("Warning: newspaper3k module could not be imported. Falling back to BeautifulSoup only.")
    NEWSPAPER_AVAILABLE = False


    # Define ArticleException for compatibility
    class ArticleException(Exception):
        pass


def extract_content_from_url(url):
    """
    Extract article content from a given URL using newspaper3k.
    Falls back to BeautifulSoup if newspaper3k fails.

    Args:
        url (str): URL of the news article

    Returns:
        str: Extracted article text
    """
    # Check if URL is valid
    if not is_valid_url(url):
        raise ValueError("Invalid URL provided")

    # Enhanced headers to mimic a real browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://www.google.com/',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0'
    }

    # Special handling for known sites with restrictions
    domain = urlparse(url).netloc

    # Reuters specific handling
    if 'reuters.com' in domain:
        try:
            print(f"Using special handling for {domain}")
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find article body specifically for Reuters
            article_body = soup.find('div', {'class': 'article-body__content__17Yit'})
            if not article_body:
                article_body = soup.find('div', {'data-testid': 'article-body'})

            if article_body:
                paragraphs = article_body.find_all('p')
                text = '\n'.join(p.get_text().strip() for p in paragraphs)

                # If we found text, return it
                if text.strip():
                    return text

            # If specific Reuters selectors didn't work, fall through to general extraction
        except Exception as e:
            print(f"Reuters-specific extraction failed: {e}, trying general methods")

    # Try with newspaper3k first if available
    if NEWSPAPER_AVAILABLE:
        try:
            # Configure newspaper with browser headers
            config = newspaper.Config()
            config.browser_user_agent = headers['User-Agent']
            config.request_timeout = 15

            article = Article(url, config=config)
            article.download()
            article.parse()

            # If article text is empty, raise exception to try BeautifulSoup
            if not article.text.strip():
                raise ArticleException("No text extracted by newspaper3k")

            # Return article text
            return article.text

        except (ArticleException, Exception) as e:
            print(f"newspaper3k extraction failed: {e}, trying BeautifulSoup")

    # Fall back to BeautifulSoup if newspaper3k fails or is not available
    try:
        # Make the request with our enhanced headers
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses

        soup = BeautifulSoup(response.text, 'html.parser')

        # Remove script and style elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            element.decompose()

        # Try different content selectors
        selectors = [
            'article', 'main',
            '[id*=content]', '[class*=content]',
            '[id*=article]', '[class*=article]',
            '[id*=story]', '[class*=story]',
            '[id*=body]', '[class*=body]'
        ]

        for selector in selectors:
            content_elements = soup.select(selector)
            if content_elements:
                # Extract text from these elements
                text = '\n'.join(element.get_text(strip=True, separator='\n') for element in content_elements)
                if text.strip():
                    return text

        # If no selectors match, extract all paragraphs
        paragraphs = soup.find_all('p')
        text = '\n'.join(p.get_text(strip=True) for p in paragraphs)

        # Clean up the text
        text = re.sub(r'\s+', ' ', text).strip()

        # If still no text, extract all div text
        if not text:
            divs = soup.find_all('div')
            text = '\n'.join(div.get_text(strip=True) for div in divs if len(div.get_text(strip=True)) > 100)
            text = re.sub(r'\s+', ' ', text).strip()

        if not text:
            raise Exception("Could not extract content from the URL")

        return text

    except Exception as e:
        raise Exception(f"Failed to extract content from URL: {str(e)}")


def is_valid_url(url):
    """
    Check if the provided URL is valid.

    Args:
        url (str): URL to validate

    Returns:
        bool: True if URL is valid, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def extract_metadata(url):
    """
    Extract metadata from the article, such as:
    - Title
    - Author
    - Publication date
    - Source domain

    Args:
        url (str): URL of the news article

    Returns:
        dict: Dictionary containing metadata
    """
    metadata = {
        'title': None,
        'authors': [],
        'publish_date': None,
        'source_domain': None,
        'meta_description': None,
        'main_image': None
    }

    try:
        # Extract domain
        parsed_url = urlparse(url)
        metadata['source_domain'] = parsed_url.netloc

        # Use newspaper3k to extract other metadata if available
        if NEWSPAPER_AVAILABLE:
            try:
                article = Article(url)
                article.download()
                article.parse()

                metadata['title'] = article.title
                metadata['authors'] = article.authors
                metadata['publish_date'] = article.publish_date
                metadata['meta_description'] = article.meta_description
                metadata['main_image'] = article.top_image
                return metadata
            except Exception as e:
                print(f"Error extracting metadata with newspaper3k: {e}")

        # Fall back to BeautifulSoup for basic metadata
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract title
        title_tag = soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.text.strip()

        # Extract meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta',
                                                                                  attrs={'property': 'og:description'})
        if meta_desc:
            metadata['meta_description'] = meta_desc.get('content', '')

        # Extract main image
        meta_img = soup.find('meta', attrs={'property': 'og:image'})
        if meta_img:
            metadata['main_image'] = meta_img.get('content', '')

    except Exception as e:
        print(f"Error extracting metadata: {e}")

    return metadata


def analyze_source_credibility(domain):
    """
    Analyze the credibility of the source domain against known reliable/unreliable sources.
    This is a placeholder - in a real application, you would use a proper database of sources.

    Args:
        domain (str): Domain name of the source

    Returns:
        dict: Credibility assessment
    """
    # This is a simplified placeholder function
    # In a real application, you would:
    # 1. Check against a database of known reliable/unreliable sources
    # 2. Look up domain age, popularity, transparency metrics, etc.
    # 3. Check for fact-checking network affiliations

    # Example trusted news sources (for demonstration purposes only)
    trusted_domains = [
        'reuters.com', 'apnews.com', 'bbc.com', 'bbc.co.uk',
        'npr.org', 'nytimes.com', 'wsj.com', 'economist.com',
        'washingtonpost.com', 'theguardian.com', 'cnn.com',
        'nbcnews.com', 'cbsnews.com', 'abcnews.go.com',
    ]

    # Example satirical/fake news sites (for demonstration purposes only)
    unreliable_domains = [
        'theonion.com', 'babylonbee.com',  # Satire
        'worldnewsdailyreport.com', 'nationalreport.net',  # Fake news
    ]

    if domain in trusted_domains:
        return {
            'credibility': 'high',
            'category': 'established news source',
            'notes': 'This is a well-established news source with editorial standards.'
        }
    elif domain in unreliable_domains:
        return {
            'credibility': 'low',
            'category': 'satirical or fake news site',
            'notes': 'This site is known for publishing fictional or satirical content.'
        }
    else:
        return {
            'credibility': 'unknown',
            'category': 'uncategorized',
            'notes': 'This source is not in our database. Exercise caution and verify from multiple sources.'
        }
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
import re
import string

# Download necessary NLTK data
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)


def preprocess_text(text):
    """
    Preprocess text for fake news detection:
    1. Convert to lowercase
    2. Remove special characters, URLs, and numbers
    3. Remove punctuation
    4. Tokenize text
    5. Remove stopwords
    6. Apply stemming
    7. Rejoin tokens into a single string

    Args:
        text (str): Raw text input

    Returns:
        str: Preprocessed text
    """
    if not text:
        return ""

    # Convert to lowercase
    text = text.lower()

    # Remove URLs
    text = re.sub(r'https?://\S+|www\.\S+', '', text)

    # Remove special characters and numbers
    text = re.sub(r'\W', ' ', text)
    text = re.sub(r'\d', ' ', text)

    # Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))

    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    # Tokenize text
    tokens = word_tokenize(text)

    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    tokens = [word for word in tokens if word not in stop_words]

    # Apply stemming
    stemmer = PorterStemmer()
    tokens = [stemmer.stem(word) for word in tokens]

    # Rejoin tokens
    processed_text = ' '.join(tokens)

    return processed_text


def extract_features(text):
    """
    Extract additional NLP features from text that might be useful for fake news detection:
    - Text length
    - Number of sentences
    - Average sentence length
    - Number of capitalized words (might indicate sensationalism)
    - Number of exclamation marks (might indicate sensationalism)
    - Number of question marks (might indicate leading questions)

    Args:
        text (str): Raw text input

    Returns:
        dict: Dictionary of extracted features
    """
    if not text:
        return {
            "text_length": 0,
            "sentence_count": 0,
            "avg_sentence_length": 0,
            "capitalized_word_count": 0,
            "exclamation_count": 0,
            "question_count": 0
        }

    # Text length
    text_length = len(text)

    # Sentence analysis
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    sentence_count = len(sentences)

    # Average sentence length
    if sentence_count > 0:
        avg_sentence_length = sum(len(s.split()) for s in sentences) / sentence_count
    else:
        avg_sentence_length = 0

    # Count capitalized words (excluding first words of sentences)
    words = text.split()
    capitalized_word_count = sum(1 for word in words if word[0].isupper())

    # Count exclamation marks
    exclamation_count = text.count('!')

    # Count question marks
    question_count = text.count('?')

    return {
        "text_length": text_length,
        "sentence_count": sentence_count,
        "avg_sentence_length": avg_sentence_length,
        "capitalized_word_count": capitalized_word_count,
        "exclamation_count": exclamation_count,
        "question_count": question_count
    }


def get_emotional_tone(text):
    """
    Analyze the emotional tone of the text using basic sentiment analysis.
    This is a simplified version; in a production system, you would use a more
    sophisticated sentiment analysis library.

    Args:
        text (str): Raw text input

    Returns:
        dict: Dictionary with sentiment analysis results
    """
    # This is a very basic implementation using simple keyword counting
    # In a real system, you would use a proper sentiment analysis library or model

    # Define emotion/sentiment word lists
    positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'best', 'happy',
                      'positive', 'success', 'successful', 'win', 'winning', 'beneficial']

    negative_words = ['bad', 'terrible', 'awful', 'horrible', 'worst', 'poor', 'negative',
                      'fail', 'failure', 'lose', 'losing', 'detrimental', 'dangerous']

    sensational_words = ['shocking', 'astounding', 'incredible', 'unbelievable', 'amazing',
                         'sensational', 'stunning', 'remarkable', 'spectacular', 'astonishing',
                         'mind-blowing', 'extraordinary', 'jaw-dropping']

    fear_words = ['fear', 'danger', 'threat', 'scary', 'terrifying', 'frightening', 'alarming',
                  'horrifying', 'dire', 'dread', 'panic', 'terror', 'worry', 'concerned']

    # Tokenize and clean text
    text = text.lower()
    words = re.findall(r'\b\w+\b', text)

    # Count occurrences
    positive_count = sum(1 for word in words if word in positive_words)
    negative_count = sum(1 for word in words if word in negative_words)
    sensational_count = sum(1 for word in words if word in sensational_words)
    fear_count = sum(1 for word in words if word in fear_words)

    # Calculate total word count for percentages
    total_words = len(words)
    if total_words == 0:
        total_words = 1  # Avoid division by zero

    return {
        "positive_ratio": positive_count / total_words,
        "negative_ratio": negative_count / total_words,
        "sensational_ratio": sensational_count / total_words,
        "fear_ratio": fear_count / total_words,
        "overall_sentiment": "positive" if positive_count > negative_count else "negative",
        "sensationalism_level": "high" if sensational_count > (total_words * 0.02) else "low"
    }
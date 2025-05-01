import pickle
import os
import numpy as np
import random
import re

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.pipeline import Pipeline
    from sklearn.model_selection import train_test_split
    import pandas as pd

    SKLEARN_AVAILABLE = True
except ImportError:
    print("Warning: scikit-learn modules could not be imported. Using fallback simple model.")
    SKLEARN_AVAILABLE = False

try:
    import nltk
    from nltk.corpus import stopwords

    # Download necessary NLTK data
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    NLTK_AVAILABLE = True
except ImportError:
    print("Warning: NLTK modules could not be imported. Some text processing features will be limited.")
    NLTK_AVAILABLE = False

# Global flag to control prediction behavior
FORCE_REAL_PREDICTIONS = False  # Set to False to use actual classification logic


# Sample fake news dataset (for demonstration)
# In a real application, you would use a proper dataset
def load_sample_data():
    # This is a placeholder function that would typically load a real dataset
    # For the purposes of this demo, we'll create a more comprehensive synthetic dataset

    real_news = [
        "The president announced new economic policies today aimed at reducing inflation.",
        "Scientists discover a new species of frog in the Amazon rainforest.",
        "The Supreme Court ruled 7-2 in favor of the plaintiff in a landmark case.",
        "NASA's new telescope captured stunning images of a distant galaxy.",
        "The Federal Reserve raised interest rates by 0.25% today to combat inflation.",
        "Local officials announced plans to repair the city's aging infrastructure.",
        "Research shows that regular exercise can improve cognitive function in older adults.",
        "The company reported a 10% increase in quarterly earnings, exceeding analyst expectations.",
        "A new study published in the Journal of Medicine suggests a link between diet and heart health.",
        "The city council voted unanimously to approve the new public transportation budget.",
        "Weather forecasters predict above-average rainfall for the upcoming season.",
        "International diplomats reached an agreement after three days of negotiations.",
        "Researchers have developed a new treatment for arthritis that shows promising results in clinical trials.",
        "The stock market closed higher today, with the main index gaining 2% by closing bell.",
        "A survey of consumers indicates growing confidence in the economy despite inflation concerns."
    ]

    fake_news = [
        "Scientists confirm that the earth is actually flat after all.",
        "Man grows third arm after COVID vaccination, doctors baffled.",
        "Government secretly replacing birds with surveillance drones since 1970s.",
        "New study finds chocolate prevents all forms of cancer, doctors hate this trick!",
        "Celebrity found alive in secret bunker years after reported death.",
        "5G towers proven to control human thoughts, whistleblower reveals.",
        "Ancient alien technology discovered beneath the Antarctic ice.",
        "Miracle supplement reverses aging overnight, scientists speechless.",
        "Secret government program allows people to communicate with animals.",
        "Doctors hiding the fact that common fruit cures all diseases.",
        "World leaders are actually reptilian aliens in disguise, insider confirms.",
        "Child prodigy solves complex math problem that baffled scientists for centuries.",
        "Hidden camera reveals that the moon landing was filmed in Hollywood.",
        "Scientists discover that drinking coffee mixed with lemon burns belly fat instantly.",
        "Exclusive: Time traveler returns with shocking predictions for next year."
    ]

    df = pd.DataFrame({
        'text': real_news + fake_news,
        'label': ['real'] * len(real_news) + ['fake'] * len(fake_news)
    })

    return df


# Initialize and train a model
def initialize_model():
    model_path = 'fake_news_model.pkl'

    # If scikit-learn is not available, use a simple rule-based model
    if not SKLEARN_AVAILABLE:
        return SimpleFakeNewsDetector()

    # If model already exists, load it
    if os.path.exists(model_path):
        try:
            with open(model_path, 'rb') as f:
                pipeline = pickle.load(f)
            return pipeline
        except Exception as e:
            print(f"Error loading model: {e}. Creating a new one.")

    # Load data
    df = load_sample_data()

    # Create a pipeline with TF-IDF and Random Forest
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(stop_words='english', max_features=5000)),
        ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
    ])

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        df['text'], df['label'], test_size=0.2, random_state=42
    )

    # Train model
    pipeline.fit(X_train, y_train)

    # Save model
    try:
        with open(model_path, 'wb') as f:
            pickle.dump(pipeline, f)
    except Exception as e:
        print(f"Error saving model: {e}")

    return pipeline


# Simple rule-based model as fallback
class SimpleFakeNewsDetector:
    """A simple rule-based fake news detector for when scikit-learn is not available"""

    def __init__(self):
        # More refined list of fake news indicators
        self.fake_indicators = [
            'conspiracy', 'shocking truth', 'they don\'t want you to know', 'secret cure',
            'miraculous', 'censored', 'what the media isn\'t saying', 'they won\'t tell you',
            'doctors hate', 'one weird trick', 'government is hiding', 'illuminati',
            'mind control', 'chemtrails', 'flat earth', 'hoax', 'scam', 'miracle cure',
            'ancient secret', 'forbidden', 'coverup', 'cover-up', 'what they don\'t want you to know'
        ]

        # Indicators of credible news
        self.credible_indicators = [
            'according to research', 'study shows', 'scientists found', 'researchers at',
            'experts say', 'data indicates', 'evidence suggests', 'analysis shows',
            'survey found', 'officials confirmed', 'report states', 'investigation revealed'
        ]

        self.classes_ = np.array(['real', 'fake'])

    def predict(self, texts):
        if isinstance(texts, str):
            texts = [texts]

        results = []
        for text in texts:
            text = text.lower()

            # Count matches of indicators
            fake_count = sum(1 for indicator in self.fake_indicators if indicator in text)
            real_count = sum(1 for indicator in self.credible_indicators if indicator in text)

            # More sophisticated decision logic
            # If there are more credible indicators than fake ones, classify as real
            if real_count > fake_count:
                results.append('real')
            # If there are more fake indicators than credible ones, classify as fake
            elif fake_count > real_count:
                results.append('fake')
            # If there are equal indicators or none, default to real (reduce false positives)
            else:
                results.append('real')

        return np.array(results)

    def predict_proba(self, texts):
        if isinstance(texts, str):
            texts = [texts]

        probas = []
        for text in texts:
            text = text.lower()

            # Calculate indicator matches
            fake_count = sum(1 for indicator in self.fake_indicators if indicator in text)
            real_count = sum(1 for indicator in self.credible_indicators if indicator in text)

            # Calculate probability based on the balance of indicators
            total_count = fake_count + real_count

            if total_count == 0:
                # If no indicators are found, default to more likely real
                real_prob = 0.7
                fake_prob = 0.3
            else:
                # Calculate weighted probability
                fake_prob = min(0.95, max(0.05, fake_count / (total_count * 1.5)))
                real_prob = 1.0 - fake_prob

                # Adjust for very low counts to prevent overconfidence
                if total_count < 2:
                    # Move probabilities closer to neutral
                    fake_prob = (fake_prob + 0.5) / 2
                    real_prob = 1.0 - fake_prob

            probas.append([real_prob, fake_prob])

        return np.array(probas)


# Global model instance
try:
    # New approach: we'll skip scikit-learn completely and use our rule-based approach
    model = None  # We don't need the model variable anymore, but keeping it for compatibility
except Exception as e:
    print(f"Error initializing model: {e}")


def predict_fake_news(text):
    """
    Predict whether the given text is fake news or not using improved heuristics.

    Returns:
    - prediction: 'real' or 'fake'
    - confidence: confidence score (0-100%)
    """
    # Basic input validation
    if not text or len(text.split()) < 5:
        return 'unknown', 50.0

    # Text preprocessing
    text_lower = text.lower()
    word_count = len(text.split())

    # Use a more sophisticated rule-based approach
    # These are common characteristics of fake news
    fake_indicators = [
        # Clickbait phrases
        r'(you won\'t believe|mind(\s|-)?blown|shocking truth|shocking result|what happens next|doctors hate|one weird trick)',
        # Conspiracy phrases
        r'(conspiracy|illuminati|mind(\s|-)?control|chemtrails?|flat earth|lizard people|deep state|new world order)',
        # Health misinformation
        r'(cure for (cancer|all diseases)|miracle cure|secret cure|big pharma doesn\'t want you to know)',
        # Exaggerated claims
        r'(100% guaranteed|impossible|never seen before|ancient secret|changes everything|revolutionary breakthrough)',
        # Urgency/Fear
        r'(before it\'s too late|catastrophic|devastating|urgent warning|imminent danger)',
        # Sensationalism
        r'(unbelievable|incredible|amazing|mind(\s|-)?blowing)'
    ]

    # Indicators of credible news
    credible_indicators = [
        # Citations
        r'(according to|cited by|quoted|study (by|from)|research (by|from)|analysis (by|from))',
        # Statistics/Data
        r'(percent|percentage|survey found|data (shows|indicates|suggests)|study found|statistics)',
        # Expert references
        r'(experts say|scientist(s)? (say|found|discovered)|researchers|professor|dr\.|officials)',
        # Balanced language
        r'(on the other hand|however|although|while|nevertheless|despite this|in contrast)',
        # Specific attributions
        r'(said in (a|an) (statement|interview|press release)|reported by|confirmed by|verified by)',
        # Precise details
        r'(\d+ percent|\d+%|\d+\.\d+|detailed analysis)'
    ]

    # Count indicator matches
    fake_count = sum(1 for pattern in fake_indicators if re.search(pattern, text_lower))
    credible_count = sum(1 for pattern in credible_indicators if re.search(pattern, text_lower))

    # Evaluate text length (fake news often has shorter paragraphs)
    avg_sentence_length = len(text) / max(1, text.count('.') + text.count('!') + text.count('?'))
    length_score = min(1.0, avg_sentence_length / 100.0)  # Normalize to 0-1

    # Calculate probabilities
    fake_score = fake_count / max(1, fake_count + credible_count)
    credible_score = credible_count / max(1, fake_count + credible_count)

    # Adjust scores based on various factors

    # 1. Length penalty for very short texts (often fake news)
    if word_count < 50:
        fake_score += 0.1

    # 2. Boost credibility for longer, detailed texts
    if word_count > 200 and avg_sentence_length > 15:
        credible_score += 0.15

    # 3. Excessive punctuation is common in fake news
    exclamation_count = text.count('!')
    question_count = text.count('?')
    if exclamation_count > 3 or (exclamation_count + question_count) > 5:
        fake_score += 0.15

    # 4. ALL CAPS or excessive capitalization suggests fake news
    caps_words = sum(1 for word in text.split() if word.isupper() and len(word) > 2)
    if caps_words > 3 or caps_words / max(1, word_count) > 0.1:
        fake_score += 0.2

    # Calculate final probabilities with a bias toward real news to minimize false positives
    # The 0.6 weight for credible_score creates a bias toward "real" classification
    final_real_prob = (0.4 + 0.6 * credible_score) / (0.4 + 0.6 * credible_score + 0.4 * fake_score)
    final_fake_prob = 1.0 - final_real_prob

    # Make the decision
    if final_fake_prob > 0.65:  # High threshold for fake news classification
        return 'fake', round(final_fake_prob * 100, 1)
    else:
        return 'real', round(final_real_prob * 100, 1)


# For future: Implement BERT version
def initialize_bert_model():
    """
    Future implementation: Use BERT for more accurate predictions
    """
    try:
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        import torch

        # Load pre-trained model and tokenizer
        tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
        model = AutoModelForSequenceClassification.from_pretrained("bert-base-uncased", num_labels=2)

        # Here you would fine-tune the model on fake news dataset
        # This is just a placeholder for the actual implementation

        return tokenizer, model
    except ImportError:
        print("Transformers library not installed. Please install with: pip install transformers")
        return None, None


def predict_with_bert(text, tokenizer, model):
    """
    Future implementation: Make predictions using BERT
    """
    if not tokenizer or not model:
        return "real", 50.0

    try:
        import torch

        # Tokenize input
        inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)

        # Make prediction
        with torch.no_grad():
            outputs = model(**inputs)
            predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)

        # Get probabilities
        fake_prob = predictions[0][1].item()
        real_prob = predictions[0][0].item()

        if fake_prob > real_prob:
            return "fake", round(fake_prob * 100, 2)
        else:
            return "real", round(real_prob * 100, 2)
    except Exception as e:
        print(f"Error in BERT prediction: {e}")
        return "real", 50.0
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List
import numpy as np
import jieba
import os

from .models import ThoughtData

# Load Chinese stop words
def load_chinese_stopwords():
    script_dir = os.path.dirname(__file__)
    stopwords_path = os.path.join(script_dir, "stopwords_zh.txt")
    try:
        with open(stopwords_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Warning: Chinese stopwords file not found at {stopwords_path}. Using no stop words for Chinese.")
        return []

CHINESE_STOPWORDS = load_chinese_stopwords()

def chinese_tokenizer(text):
    """
    Jieba tokenizer for Chinese text.
    """
    return list(jieba.cut(text))

class AdvancedAnalyzer:
    """
    Performs advanced analysis on thoughts, such as textual similarity.
    """

    @staticmethod
    def calculate_similarity_matrix(thoughts: List[ThoughtData], lang: str = 'en') -> np.ndarray:
        """
        Calculates the cosine similarity matrix for a list of thoughts.

        Args:
            thoughts: A list of ThoughtData objects.
            lang: Language of the thoughts ('en' for English, 'zh' for Chinese).

        Returns:
            A numpy array representing the similarity matrix.
        """
        if not thoughts or len(thoughts) < 2:
            return np.array([])

        documents = [thought.thought for thought in thoughts]

        if lang == 'zh':
            vectorizer = TfidfVectorizer(tokenizer=chinese_tokenizer, stop_words=CHINESE_STOPWORDS)
        else: # Default to English
            vectorizer = TfidfVectorizer(stop_words='english')

        tfidf_matrix = vectorizer.fit_transform(documents)
        cosine_sim_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)

        return cosine_sim_matrix
import math
import re
from loguru import logger

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
    """
    Slices text into smaller, overlapping character chunks to preserve context at boundaries.
    """
    if not text:
        return []
    
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunk = text[start:end]
        chunks.append(chunk)
        
        # Move start point forward by (chunk_size - overlap)
        if end == text_length:
            break
        start += (chunk_size - overlap)
        
    logger.info(f"Chunked document into {len(chunks)} fragments (size={chunk_size}, overlap={overlap}).")
    return chunks

class SimpleRetrievalEngine:
    """
    A 100% manual TF-IDF search engine.
    Computes text relevance without external vector databases or remote embedding APIs.
    """
    def __init__(self, chunks: list[str]):
        self.chunks = chunks
        self.documents_count = len(chunks)
        self.vocab = set()
        self.chunk_tokens = []
        self.idf = {}
        
        # Build Vocab and Token Lists
        self._initialize_index()

    def _tokenize(self, text: str) -> list[str]:
        """Simple lowercase word tokenization using regex."""
        return re.findall(r'\b\w+\b', text.lower())

    def _initialize_index(self):
        """Builds vocab and calculates Inverse Document Frequency (IDF) scores."""
        # Tokenize all chunks
        for chunk in self.chunks:
            tokens = self._tokenize(chunk)
            self.chunk_tokens.append(tokens)
            self.vocab.update(tokens)

        # Calculate document frequency (DF) for each word in vocab
        # (how many chunks contain this word)
        df = {word: 0 for word in self.vocab}
        for tokens in self.chunk_tokens:
            unique_tokens = set(tokens)
            for token in unique_tokens:
                if token in df:
                    df[token] += 1

        # Calculate Inverse Document Frequency (IDF)
        # Smooth IDF: log( 1 + N / (1 + df) )
        for word, freq in df.items():
            self.idf[word] = math.log(1 + (self.documents_count / (1 + freq)))

    def _get_tf_vector(self, tokens: list[str]) -> dict[str, float]:
        """Calculates Term Frequency (TF) for a tokenized text."""
        tf = {}
        if not tokens:
            return tf
        
        # Word counts
        for token in tokens:
            if token in self.vocab:
                tf[token] = tf.get(token, 0) + 1
                
        # Normalize TF by dividing by document length
        length = len(tokens)
        for token in tf:
            tf[token] = tf[token] / length
            
        return tf

    def _get_tfidf_vector(self, tokens: list[str]) -> dict[str, float]:
        """Calculates TF-IDF vector representing a text segment."""
        tf = self._get_tf_vector(tokens)
        tfidf = {}
        for token, tf_val in tf.items():
            tfidf[token] = tf_val * self.idf.get(token, 0)
        return tfidf

    def _cosine_similarity(self, vec1: dict[str, float], vec2: dict[str, float]) -> float:
        """Calculates Cosine Similarity between two sparse term vectors."""
        # Find intersecting keys to compute dot product
        intersection = set(vec1.keys()) & set(vec2.keys())
        dot_product = sum(vec1[key] * vec2[key] for key in intersection)
        
        # Magnitudes
        sum1 = sum(val ** 2 for val in vec1.values())
        sum2 = sum(val ** 2 for val in vec2.values())
        
        mag1 = math.sqrt(sum1)
        mag2 = math.sqrt(sum2)
        
        if mag1 == 0.0 or mag2 == 0.0:
            return 0.0
            
        return dot_product / (mag1 * mag2)

    def retrieve(self, query: str, top_k: int = 2) -> list[tuple[str, float]]:
        """
        Retrieves the top_k most relevant chunks matching the user's query.
        Returns a list of tuples containing (chunk_content, similarity_score).
        """
        query_tokens = self._tokenize(query)
        if not query_tokens or self.documents_count == 0:
            return []
            
        query_vector = self._get_tfidf_vector(query_tokens)
        
        scores = []
        for idx, chunk in enumerate(self.chunks):
            chunk_tokens = self.chunk_tokens[idx]
            chunk_vector = self._get_tfidf_vector(chunk_tokens)
            
            similarity = self._cosine_similarity(query_vector, chunk_vector)
            scores.append((chunk, similarity))
            
        # Sort chunks by highest similarity score
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

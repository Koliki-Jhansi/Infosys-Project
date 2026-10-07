"""
AeroAssist AI - Ticket Classification Engine
Uses Scikit-Learn (TF-IDF Vectorizer + Multinomial Naive Bayes / Calibrated Classifier)
to predict airport & airways support categories with confidence estimation.
"""
import os
import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

CATEGORIES = [
    "Booking & Confirmation",
    "Check-in & Boarding",
    "Baggage",
    "Delays & Cancellations",
    "Refunds & Payments",
    "Airport Facilities",
    "Shopping & Services",
    "Passenger Assistance",
    "General Support"
]

class TicketClassifier:
    def __init__(self):
        self.model = None
        self.is_trained = False
        self._initialize_and_train()

    def _initialize_and_train(self):
        """Loads training dataset and fits TF-IDF + MultinomialNB pipeline."""
        dataset_path = os.path.join(os.path.dirname(__file__), "data", "training_dataset.json")
        
        if not os.path.exists(dataset_path):
            raise FileNotFoundError(f"Training dataset not found at {dataset_path}")
            
        with open(dataset_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        texts = [item["text"] for item in data]
        labels = [item["category"] for item in data]

        # Pipeline with TF-IDF and Naive Bayes
        self.model = Pipeline([
            ("tfidf", TfidfVectorizer(
                ngram_range=(1, 2),
                stop_words="english",
                sublinear_tf=True,
                min_df=1
            )),
            ("clf", MultinomialNB(alpha=0.5))
        ])

        self.model.fit(texts, labels)
        self.is_trained = True

    def classify(self, title: str, description: str = "") -> dict:
        """
        Classifies support ticket text.
        Returns:
            {
                "predicted_category": str,
                "confidence": float (0.0 - 1.0),
                "all_probabilities": dict
            }
        """
        if not self.is_trained:
            self._initialize_and_train()

        combined_text = f"{title.strip()} {description.strip()}".strip()
        if not combined_text:
            return {
                "predicted_category": "General Support",
                "confidence": 0.50,
                "all_probabilities": {}
            }

        # Predict probability distribution
        probabilities = self.model.predict_proba([combined_text])[0]
        classes = self.model.classes_

        best_idx = np.argmax(probabilities)
        predicted_category = classes[best_idx]
        confidence = float(probabilities[best_idx])

        # Normalize confidence to realistic calibrated display (minimum baseline for known domain)
        all_probs = {cls: round(float(prob), 4) for cls, prob in zip(classes, probabilities)}

        return {
            "predicted_category": predicted_category,
            "confidence": round(confidence, 4),
            "all_probabilities": all_probs
        }

# Global singleton instance
_classifier_instance = None

def get_classifier():
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = TicketClassifier()
    return _classifier_instance

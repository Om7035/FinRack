"""ML-based transaction categorization service"""
from typing import Optional, List
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
import pickle
import os
import logging

logger = logging.getLogger(__name__)


class TransactionCategorizer:
    """ML-based transaction categorization"""
    
    # Standard categories
    CATEGORIES = [
        'Food & Dining',
        'Shopping',
        'Transportation',
        'Bills & Utilities',
        'Entertainment',
        'Healthcare',
        'Travel',
        'Personal Care',
        'Education',
        'Gifts & Donations',
        'Business Services',
        'Financial',
        'Home',
        'Income',
        'Transfer',
        'Other',
    ]
    
    # Category keywords for rule-based fallback
    CATEGORY_KEYWORDS = {
        'Food & Dining': ['restaurant', 'cafe', 'coffee', 'food', 'dining', 'pizza', 'burger', 'starbucks', 'mcdonald'],
        'Shopping': ['amazon', 'walmart', 'target', 'store', 'shop', 'retail', 'mall', 'clothing'],
        'Transportation': ['uber', 'lyft', 'gas', 'fuel', 'parking', 'transit', 'taxi', 'car'],
        'Bills & Utilities': ['electric', 'water', 'internet', 'phone', 'utility', 'bill', 'insurance'],
        'Entertainment': ['netflix', 'spotify', 'movie', 'theater', 'game', 'entertainment', 'subscription'],
        'Healthcare': ['pharmacy', 'doctor', 'hospital', 'medical', 'health', 'dental', 'cvs', 'walgreens'],
        'Travel': ['hotel', 'airbnb', 'airline', 'flight', 'booking', 'travel', 'vacation'],
        'Personal Care': ['salon', 'spa', 'gym', 'fitness', 'beauty', 'barber'],
        'Education': ['school', 'university', 'course', 'tuition', 'book', 'education'],
        'Gifts & Donations': ['gift', 'donation', 'charity', 'contribution'],
        'Business Services': ['office', 'business', 'professional', 'service', 'consulting'],
        'Financial': ['bank', 'atm', 'fee', 'interest', 'investment', 'credit'],
        'Home': ['rent', 'mortgage', 'furniture', 'home', 'apartment', 'lease'],
        'Income': ['salary', 'paycheck', 'deposit', 'income', 'payment received'],
        'Transfer': ['transfer', 'venmo', 'paypal', 'zelle', 'cashapp'],
    }
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize categorizer
        
        Args:
            model_name: Sentence transformer model name
        """
        self.embedding_model = SentenceTransformer(model_name)
        self.classifier: Optional[RandomForestClassifier] = None
        self.label_encoder: Optional[LabelEncoder] = None
        self.model_path = 'models/transaction_classifier.pkl'
        
        # Load pre-trained model if exists
        self._load_model()
    
    def _load_model(self) -> None:
        """Load pre-trained classifier if exists"""
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'rb') as f:
                    data = pickle.load(f)
                    self.classifier = data['classifier']
                    self.label_encoder = data['label_encoder']
                logger.info("Loaded pre-trained transaction classifier")
            except Exception as e:
                logger.warning(f"Failed to load classifier: {e}")
    
    def _save_model(self) -> None:
        """Save trained classifier"""
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump({
                'classifier': self.classifier,
                'label_encoder': self.label_encoder,
            }, f)
        logger.info("Saved transaction classifier")
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        embedding = self.embedding_model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def categorize(
        self,
        description: str,
        merchant: Optional[str] = None,
        amount: Optional[float] = None
    ) -> str:
        """
        Categorize a transaction
        
        Args:
            description: Transaction description
            merchant: Merchant name
            amount: Transaction amount
            
        Returns:
            Category name
        """
        # Combine text for better context
        text = description
        if merchant:
            text = f"{merchant} - {description}"
        
        # Try ML model first
        if self.classifier is not None and self.label_encoder is not None:
            try:
                embedding = self.generate_embedding(text)
                prediction = self.classifier.predict([embedding])[0]
                category = self.label_encoder.inverse_transform([prediction])[0]
                return category
            except Exception as e:
                logger.warning(f"ML categorization failed: {e}")
        
        # Fallback to rule-based
        return self._rule_based_categorize(text, amount)
    
    def _rule_based_categorize(self, text: str, amount: Optional[float] = None) -> str:
        """
        Rule-based categorization fallback
        
        Args:
            text: Transaction text
            amount: Transaction amount
            
        Returns:
            Category name
        """
        text_lower = text.lower()
        
        # Check for income (positive amount)
        if amount and amount < 0:  # Plaid uses negative for income
            return 'Income'
        
        # Check keywords
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        
        return 'Other'
    
    def train(
        self,
        descriptions: List[str],
        categories: List[str],
        merchants: Optional[List[str]] = None
    ) -> None:
        """
        Train the classifier on labeled data
        
        Args:
            descriptions: List of transaction descriptions
            categories: List of corresponding categories
            merchants: Optional list of merchant names
        """
        # Combine descriptions with merchants
        texts = []
        for i, desc in enumerate(descriptions):
            text = desc
            if merchants and i < len(merchants) and merchants[i]:
                text = f"{merchants[i]} - {desc}"
            texts.append(text)
        
        # Generate embeddings
        logger.info(f"Generating embeddings for {len(texts)} transactions...")
        embeddings = [self.generate_embedding(text) for text in texts]
        
        # Encode labels
        self.label_encoder = LabelEncoder()
        encoded_categories = self.label_encoder.fit_transform(categories)
        
        # Train classifier
        logger.info("Training classifier...")
        self.classifier = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        self.classifier.fit(embeddings, encoded_categories)
        
        # Save model
        self._save_model()
        
        logger.info(f"Classifier trained on {len(texts)} samples")
    
    def batch_categorize(
        self,
        transactions: List[dict]
    ) -> List[str]:
        """
        Categorize multiple transactions efficiently
        
        Args:
            transactions: List of transaction dicts with 'name', 'merchant_name', 'amount'
            
        Returns:
            List of categories
        """
        categories = []
        for txn in transactions:
            category = self.categorize(
                description=txn.get('name', ''),
                merchant=txn.get('merchant_name'),
                amount=txn.get('amount')
            )
            categories.append(category)
        
        return categories


# Global instance
categorizer = TransactionCategorizer()

"""ML-based transaction categorization service"""

from typing import Dict, List, Optional, Tuple
import logging
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re

logger = logging.getLogger(__name__)


class CategorizationService:
    """Service for ML-based transaction categorization"""
    
    # Category mappings with keywords
    CATEGORIES = {
        'Food & Dining': {
            'keywords': ['restaurant', 'cafe', 'coffee', 'food', 'dining', 'pizza', 'burger', 'sushi', 'bar', 'pub', 'bakery', 'grocery', 'supermarket', 'market'],
            'subcategories': ['Restaurants', 'Groceries', 'Coffee Shops', 'Fast Food', 'Bars']
        },
        'Shopping': {
            'keywords': ['amazon', 'walmart', 'target', 'store', 'shop', 'retail', 'mall', 'clothing', 'fashion', 'electronics'],
            'subcategories': ['Online Shopping', 'Clothing', 'Electronics', 'General Merchandise']
        },
        'Transportation': {
            'keywords': ['uber', 'lyft', 'taxi', 'gas', 'fuel', 'parking', 'metro', 'train', 'bus', 'transit', 'airline', 'flight'],
            'subcategories': ['Ride Share', 'Gas/Fuel', 'Parking', 'Public Transit', 'Airlines']
        },
        'Bills & Utilities': {
            'keywords': ['electric', 'water', 'gas', 'internet', 'phone', 'mobile', 'utility', 'bill', 'insurance', 'rent', 'mortgage'],
            'subcategories': ['Electric', 'Water', 'Gas', 'Internet', 'Phone', 'Insurance', 'Rent']
        },
        'Entertainment': {
            'keywords': ['netflix', 'spotify', 'hulu', 'disney', 'movie', 'theater', 'cinema', 'concert', 'game', 'gaming', 'entertainment'],
            'subcategories': ['Streaming Services', 'Movies', 'Gaming', 'Concerts', 'Events']
        },
        'Healthcare': {
            'keywords': ['doctor', 'hospital', 'pharmacy', 'medical', 'health', 'clinic', 'dental', 'dentist', 'medicine', 'prescription'],
            'subcategories': ['Doctor', 'Pharmacy', 'Hospital', 'Dental', 'Medical Supplies']
        },
        'Travel': {
            'keywords': ['hotel', 'airbnb', 'booking', 'travel', 'vacation', 'resort', 'airline', 'flight', 'rental car'],
            'subcategories': ['Hotels', 'Flights', 'Car Rental', 'Vacation']
        },
        'Personal Care': {
            'keywords': ['salon', 'spa', 'gym', 'fitness', 'beauty', 'haircut', 'massage', 'cosmetics'],
            'subcategories': ['Salon', 'Gym', 'Spa', 'Beauty Products']
        },
        'Education': {
            'keywords': ['school', 'university', 'college', 'tuition', 'course', 'book', 'education', 'learning'],
            'subcategories': ['Tuition', 'Books', 'Courses', 'Supplies']
        },
        'Income': {
            'keywords': ['salary', 'paycheck', 'deposit', 'income', 'payment', 'refund', 'reimbursement'],
            'subcategories': ['Salary', 'Freelance', 'Refunds', 'Other Income']
        },
        'Transfer': {
            'keywords': ['transfer', 'venmo', 'paypal', 'zelle', 'cashapp', 'payment'],
            'subcategories': ['Peer-to-Peer', 'Account Transfer']
        },
        'Uncategorized': {
            'keywords': [],
            'subcategories': []
        }
    }
    
    def __init__(self):
        """Initialize categorization service"""
        try:
            # Load sentence transformer model for embeddings
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Sentence transformer model loaded successfully")
            
            # Pre-compute category embeddings
            self.category_embeddings = self._compute_category_embeddings()
            
        except Exception as e:
            logger.error(f"Failed to initialize categorization service: {e}")
            self.model = None
            self.category_embeddings = {}
    
    def _compute_category_embeddings(self) -> Dict[str, np.ndarray]:
        """Pre-compute embeddings for all categories"""
        category_embeddings = {}
        
        for category, data in self.CATEGORIES.items():
            # Combine category name and keywords
            text = f"{category} {' '.join(data['keywords'])}"
            embedding = self.model.encode(text, convert_to_numpy=True)
            category_embeddings[category] = embedding
        
        return category_embeddings
    
    def categorize_transaction(
        self,
        description: str,
        merchant_name: Optional[str] = None,
        plaid_category: Optional[str] = None,
        amount: Optional[float] = None
    ) -> Tuple[str, float]:
        """
        Categorize a transaction using ML and rules
        
        Args:
            description: Transaction description
            merchant_name: Merchant name (if available)
            plaid_category: Plaid's category (if available)
            amount: Transaction amount (positive for expenses)
            
        Returns:
            Tuple of (category, confidence_score)
        """
        # Use Plaid category if available and confident
        if plaid_category and plaid_category in self.CATEGORIES:
            return plaid_category, 0.95
        
        # Combine description and merchant name
        text = f"{description} {merchant_name or ''}".lower().strip()
        
        # Rule-based categorization first (fast path)
        rule_category, rule_confidence = self._rule_based_categorization(text, amount)
        if rule_confidence > 0.8:
            return rule_category, rule_confidence
        
        # ML-based categorization (slower but more accurate)
        if self.model:
            ml_category, ml_confidence = self._ml_based_categorization(text)
            
            # Combine rule-based and ML-based results
            if rule_confidence > 0.5 and ml_confidence > 0.5:
                # Average confidence if both methods agree
                if rule_category == ml_category:
                    return rule_category, (rule_confidence + ml_confidence) / 2
                # Use ML result if more confident
                elif ml_confidence > rule_confidence:
                    return ml_category, ml_confidence
                else:
                    return rule_category, rule_confidence
            elif ml_confidence > 0.5:
                return ml_category, ml_confidence
        
        # Fallback to rule-based result
        return rule_category, rule_confidence
    
    def _rule_based_categorization(
        self,
        text: str,
        amount: Optional[float] = None
    ) -> Tuple[str, float]:
        """Rule-based categorization using keywords"""
        text_lower = text.lower()
        
        # Check for income (negative amount in Plaid)
        if amount and amount < 0:
            for keyword in self.CATEGORIES['Income']['keywords']:
                if keyword in text_lower:
                    return 'Income', 0.9
            return 'Income', 0.7
        
        # Check each category's keywords
        best_category = 'Uncategorized'
        best_score = 0.0
        
        for category, data in self.CATEGORIES.items():
            if category == 'Uncategorized':
                continue
            
            # Count keyword matches
            matches = sum(1 for keyword in data['keywords'] if keyword in text_lower)
            
            if matches > 0:
                # Calculate confidence based on matches
                confidence = min(0.9, 0.5 + (matches * 0.1))
                
                if confidence > best_score:
                    best_score = confidence
                    best_category = category
        
        return best_category, best_score
    
    def _ml_based_categorization(self, text: str) -> Tuple[str, float]:
        """ML-based categorization using embeddings"""
        try:
            # Generate embedding for transaction text
            text_embedding = self.model.encode(text, convert_to_numpy=True)
            
            # Calculate similarity with each category
            similarities = {}
            for category, category_embedding in self.category_embeddings.items():
                similarity = cosine_similarity(
                    text_embedding.reshape(1, -1),
                    category_embedding.reshape(1, -1)
                )[0][0]
                similarities[category] = similarity
            
            # Get best match
            best_category = max(similarities, key=similarities.get)
            confidence = float(similarities[best_category])
            
            # Adjust confidence (cosine similarity is 0-1, but we want stricter thresholds)
            confidence = min(0.95, confidence * 1.2)
            
            return best_category, confidence
            
        except Exception as e:
            logger.error(f"ML categorization failed: {e}")
            return 'Uncategorized', 0.0
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding vector for text (for storage in pgvector)
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding, or None if failed
        """
        try:
            if not self.model:
                return None
            
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None
    
    def batch_categorize(
        self,
        transactions: List[Dict[str, any]]
    ) -> List[Tuple[str, float]]:
        """
        Batch categorize multiple transactions
        
        Args:
            transactions: List of transaction dictionaries
            
        Returns:
            List of (category, confidence) tuples
        """
        results = []
        
        for txn in transactions:
            category, confidence = self.categorize_transaction(
                description=txn.get('name', ''),
                merchant_name=txn.get('merchant_name'),
                plaid_category=txn.get('category'),
                amount=txn.get('amount')
            )
            results.append((category, confidence))
        
        return results


# Global categorization service instance
categorization_service = CategorizationService()

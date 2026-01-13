"""
RAG (Retrieval Augmented Generation) System for E-commerce Knowledge Base
Retrieves product information, policies, FAQs, and order data from JSON
"""
import os
import json
from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()


class RAGSystem:
    def __init__(
        self,
        json_path: str = "ecommerce_voicebot_knowledge_base.json",
        persist_directory: str = "./chroma_db"
    ):
        """
        Initialize RAG system with JSON knowledge base.

        Args:
            json_path: Path to the JSON knowledge base file
            persist_directory: Directory to persist ChromaDB
        """
        self.json_path = json_path
        self.persist_directory = persist_directory
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )

        # Get or create collection for e-commerce knowledge base
        self.collection = self.client.get_or_create_collection(
            name="ecommerce_knowledge_base",
            metadata={"hnsw:space": "cosine"}
        )

        # Load or build index
        self._initialize_index()

    def _load_json_data(self) -> Dict[str, Any]:
        """Load and parse JSON knowledge base file."""
        if not os.path.exists(self.json_path):
            print(
                f"Warning: Knowledge base file {self.json_path} not found. "
                "RAG will work but without knowledge base context."
            )
            return {}

        try:
            with open(self.json_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            return data
        except Exception as e:
            print(f"Error loading JSON knowledge base: {e}")
            return {}

    def _extract_chunks_from_json(self) -> List[str]:
        """Extract text chunks from JSON knowledge base."""
        chunks = []
        data = self._load_json_data()

        if not data:
            return chunks

        # Extract product information
        if 'products' in data:
            for product in data['products']:
                name = product.get('name', 'Unknown')
                prod_id = product.get('product_id', 'N/A')
                category = product.get('category', 'N/A')
                subcat = product.get('subcategory', 'N/A')
                brand = product.get('brand', 'N/A')
                price = product.get('price', 0)
                stock = product.get('stock_status', 'N/A')
                desc = product.get('description', 'N/A')

                product_text = (
                    f"Product: {name} (ID: {prod_id}). "
                    f"Category: {category} - {subcat}. "
                    f"Brand: {brand}. Price: ${price:.2f}. "
                    f"Stock Status: {stock}. Description: {desc}. "
                )

                # Add specifications
                if 'specifications' in product:
                    specs = product['specifications']
                    spec_text = "Specifications: "
                    for key, value in specs.items():
                        if isinstance(value, list):
                            val_str = ', '.join(map(str, value))
                            spec_text += f"{key}: {val_str}; "
                        else:
                            spec_text += f"{key}: {value}; "
                    product_text += spec_text

                # Add ratings and reviews
                if 'rating' in product:
                    rating = product.get('rating', 0)
                    reviews = product.get('review_count', 0)
                    product_text += (
                        f"Rating: {rating}/5.0 ({reviews} reviews). "
                    )

                # Add keywords
                if 'keywords' in product:
                    keywords_str = ', '.join(product['keywords'])
                    product_text += f"Keywords: {keywords_str}."

                chunks.append(product_text.strip())

        # Extract order information
        if 'orders' in data:
            for order in data['orders']:
                order_text = (
                    f"Order ID: {order.get('order_id', 'N/A')}. "
                    f"Status: {order.get('order_status', 'N/A')}. "
                    f"Order Date: {order.get('order_date', 'N/A')}. "
                )

                if 'tracking_number' in order and order['tracking_number']:
                    order_text += (
                        f"Tracking: {order.get('tracking_number', 'N/A')} "
                        f"via {order.get('carrier', 'N/A')}. "
                    )

                if 'estimated_delivery' in order:
                    order_text += (
                        f"Estimated Delivery: "
                        f"{order.get('estimated_delivery', 'N/A')}. "
                    )

                if 'items' in order:
                    items_text = "Items: "
                    for item in order['items']:
                        items_text += (
                            f"{item.get('product_name', 'N/A')} "
                            f"(Qty: {item.get('quantity', 0)}, "
                            f"Price: ${item.get('price', 0):.2f}); "
                        )
                    order_text += items_text

                if 'total' in order:
                    order_text += (
                        f"Total: ${order.get('total', 0):.2f} "
                        f"(Shipping: ${order.get('shipping_cost', 0):.2f}, "
                        f"Tax: ${order.get('tax', 0):.2f}). "
                    )

                chunks.append(order_text.strip())

        # Extract policies
        if 'policies' in data:
            policies = data['policies']
            for policy_name, policy_data in policies.items():
                if isinstance(policy_data, dict):
                    title = policy_data.get('title', policy_name)
                    updated = policy_data.get('last_updated', 'N/A')
                    policy_text = (
                        f"Policy: {title}. Last Updated: {updated}. "
                    )

                    if 'content' in policy_data:
                        policy_text += f"{policy_data['content']} "

                    # Extract policy details
                    for key, value in policy_data.items():
                        if key not in ['title', 'last_updated', 'content']:
                            if isinstance(value, list):
                                if value and isinstance(value[0], dict):
                                    # Handle list of objects
                                    # (e.g., shipping methods)
                                    for item in value:
                                        if isinstance(item, dict):
                                            item_text = ""
                                            for k, v in item.items():
                                                item_text += f"{k}: {v}; "
                                            item_stripped = item_text.strip()
                                            policy_text += f"{item_stripped}. "
                                else:
                                    # Handle simple lists
                                    val_str = ', '.join(map(str, value))
                                    policy_text += (
                                        f"{key}: {val_str}. "
                                    )
                            elif isinstance(value, str):
                                policy_text += f"{key}: {value}. "

                    chunks.append(policy_text.strip())

        # Extract FAQs
        if 'faqs' in data:
            for faq_category in data['faqs']:
                category_name = faq_category.get('category', 'General')
                if 'questions' in faq_category:
                    for faq in faq_category['questions']:
                        faq_text = (
                            f"FAQ Category: {category_name}. "
                            f"Question: {faq.get('question', 'N/A')} "
                            f"Answer: {faq.get('answer', 'N/A')}"
                        )
                        chunks.append(faq_text.strip())

        # Extract voice query scenarios
        if 'voice_query_scenarios' in data:
            for scenario in data['voice_query_scenarios']:
                scenario_text = (
                    f"Voice Scenario: {scenario.get('category', 'N/A')}. "
                    f"Intent: {scenario.get('user_intent', 'N/A')}. "
                )

                if 'sample_queries' in scenario:
                    scenario_text += (
                        f"Sample queries: "
                        f"{', '.join(scenario['sample_queries'][:3])}. "
                    )

                if 'sample_bot_response' in scenario:
                    scenario_text += (
                        f"Bot response: "
                        f"{scenario.get('sample_bot_response', 'N/A')}. "
                    )

                chunks.append(scenario_text.strip())

        chunk_count = len(chunks)
        print(f"Extracted {chunk_count} knowledge base chunks from JSON")
        return chunks

    def _initialize_index(self):
        """Initialize or load the vector index."""
        # Check if collection already has documents
        if self.collection.count() > 0:
            count = self.collection.count()
            print(f"RAG index already exists with {count} chunks")
            return

        # Extract and index JSON knowledge base
        chunks = self._extract_chunks_from_json()

        if not chunks:
            print(
                "No knowledge base information to index. RAG will work but "
                "without knowledge base context."
            )
            return

        # Generate embeddings and add to collection
        ids = [f"chunk_{i}" for i in range(len(chunks))]
        embeddings = self.embedding_model.encode(
            chunks, show_progress_bar=True
        ).tolist()

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=[{"chunk_id": i} for i in range(len(chunks))]
        )

        print(f"Indexed {len(chunks)} knowledge base chunks into RAG")

    def retrieve(self, query: str, top_k: int = 3) -> List[str]:
        """
        Retrieve relevant knowledge base chunks for a query.

        Args:
            query: User query
            top_k: Number of chunks to retrieve

        Returns:
            List of relevant knowledge base chunks
        """
        if self.collection.count() == 0:
            return []

        # Generate query embedding
        query_embedding = self.embedding_model.encode([query]).tolist()[0]

        # Search in ChromaDB
        max_results = min(top_k, self.collection.count())
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=max_results
        )

        # Extract documents
        if results['documents'] and len(results['documents']) > 0:
            return results['documents'][0]

        return []

    def is_relevant_query(self, query: str) -> bool:
        """
        Determine if query is relevant to e-commerce knowledge base.
        Uses similarity threshold and e-commerce keywords to decide.

        Args:
            query: User query

        Returns:
            True if query is relevant to knowledge base
        """
        if self.collection.count() == 0:
            return False

        # E-commerce related keywords
        ecommerce_keywords = [
            'product', 'item', 'buy', 'purchase', 'price', 'cost',
            'feature', 'specification', 'spec', 'available', 'stock',
            'catalog', 'shopping', 'shop', 'store', 'brand', 'model',
            'review', 'rating', 'compare', 'similar', 'alternative',
            'discount', 'sale', 'offer', 'deal', 'shipping', 'delivery',
            'warranty', 'return', 'refund', 'order', 'cart', 'checkout',
            'track', 'status', 'policy', 'faq', 'question', 'help',
            'support', 'customer service', 'payment', 'billing'
        ]

        query_lower = query.lower()

        # Check if query contains e-commerce keywords
        has_ecommerce_keywords = any(
            keyword in query_lower for keyword in ecommerce_keywords
        )

        # Retrieve results to check similarity
        results = self.retrieve(query, top_k=1)

        if not results:
            return False

        # Consider relevant if:
        # 1. Has e-commerce keywords, OR
        # 2. Retrieved results exist (semantic similarity)
        return has_ecommerce_keywords or len(results) > 0


# Global RAG instance
_rag_instance = None


def get_rag_system() -> RAGSystem:
    """Get or create the global RAG system instance."""
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = RAGSystem()
    return _rag_instance

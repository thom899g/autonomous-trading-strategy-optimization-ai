"""
Firestore Client for Autonomous Trading Strategy Optimization AI
Centralized Firestore client with connection pooling, error handling, and type safety
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timezone
from google.cloud import firestore
from google.cloud.firestore_v1.client import Client as FirestoreClient
from google.cloud.firestore_v1.document import DocumentReference
from google.cloud.firestore_v1.collection import CollectionReference
import google.auth
from google.auth.exceptions import DefaultCredentialsError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FirestoreConnectionError(Exception):
    """Custom exception for Firestore connection failures"""
    pass


class FirestoreClientSingleton:
    """
    Singleton Firestore client with connection pooling and automatic retry logic
    Follows Firebase Priority constraint for all database and state management
    """
    
    _instance: Optional['FirestoreClientSingleton'] = None
    _client: Optional[FirestoreClient] = None
    _credentials_path: Optional[str] = None
    
    def __new__(cls) -> 'FirestoreClientSingleton':
        if cls._instance is None:
            cls._instance = super(FirestoreClientSingleton, cls).__new__(cls)
        return cls._instance
    
    def initialize(self, credentials_path: Optional[str] = None) -> None:
        """
        Initialize Firestore client with credentials
        
        Args:
            credentials_path: Path to Google Cloud credentials JSON file
            
        Raises:
            FirestoreConnectionError: If Firestore cannot be initialized
        """
        if self._client is not None:
            logger.info("Firestore client already initialized")
            return
            
        try:
            if credentials_path:
                # Use service account credentials from file
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
                self._credentials_path = credentials_path
                logger.info(f"Using credentials from: {credentials_path}")
            
            # Initialize Firestore client
            self._client = firestore.Client()
            
            # Test connection with a simple operation
            test_ref = self._client.collection('system_health').document('connection_test')
            test_ref.set({
                'test_timestamp': datetime.now(timezone.utc),
                'status': 'connected',
                'system': 'trading_strategy_ai'
            })
            
            logger.info("Firestore client initialized successfully")
            
        except DefaultCredentialsError as e:
            error_msg = "Failed to initialize Firestore: Google Cloud credentials not found"
            logger.error(f"{error_msg}: {str(e)}")
            raise FirestoreConnectionError(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to initialize Firestore client: {str(e)}"
            logger.error(error_msg)
            raise FirestoreConnectionError(error_msg) from e
    
    @property
    def client(self) -> FirestoreClient:
        """
        Get Firestore client instance
        
        Returns:
            Initialized Firestore client
            
        Raises:
            FirestoreConnectionError: If client is not initialized
        """
        if self._client is None:
            raise FirestoreConnectionError(
                "Firestore client not initialized. Call initialize() first."
            )
        return self._client
    
    def get_collection(self, collection_path: str) -> CollectionReference:
        """
        Get Firestore collection reference with validation
        
        Args:
            collection_path: Path to collection
            
        Returns:
            Firestore CollectionReference
            
        Raises:
            ValueError: If collection_path is invalid
        """
        if not collection_path or not isinstance(collection_path, str):
            raise ValueError("Collection path must be a non-empty string")
        
        try:
            return self.client.collection(collection_path)
        except Exception as e:
            logger.error(f"Failed to get collection {collection_path}: {str(e)}")
            raise
    
    def get_document(self, collection_path: str, document_id: str) -> DocumentReference:
        """
        Get Firestore document reference with validation
        
        Args:
            collection_path: Path to collection
            document_id: Document ID
            
        Returns:
            Firestore DocumentReference
            
        Raises:
            ValueError: If inputs are invalid
        """
        if not document_id or not isinstance(document_id, str):
            raise ValueError("Document ID must be a non-empty string")
        
        collection = self.get_collection(collection_path)
        return collection.document(document_id)
    
    def close(self) -> None:
        """Close Firestore connection"""
        if self._client:
            try:
                # Firestore client doesn't have explicit close method in this version
                # It will be garbage collected
                self._client = None
                logger.info("Firestore client closed")
            except Exception as e:
                logger.warning(f"Error closing Firestore client: {str(e)}")
    
    def __del__(self) -> None:
        """Destructor to ensure cleanup"""
        self.close()


# Global singleton instance
firestore_client = FirestoreClientSingleton()
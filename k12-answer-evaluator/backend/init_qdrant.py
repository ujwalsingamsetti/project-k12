#!/usr/bin/env python3
"""Initialize Qdrant collection for textbooks"""

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

# Connect to Qdrant
client = QdrantClient(url="http://localhost:6333")

# Create collection
collection_name = "k12_textbooks"

try:
    # Check if collection exists
    collections = client.get_collections().collections
    exists = any(c.name == collection_name for c in collections)
    
    if exists:
        print(f"✅ Collection '{collection_name}' already exists")
    else:
        # Create collection
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )
        print(f"✅ Created collection '{collection_name}'")
        print("Note: Collection is empty. Run textbook ingestion to add data.")
        
except Exception as e:
    print(f"❌ Error: {e}")

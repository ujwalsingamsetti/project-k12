#!/usr/bin/env python3
"""Quick textbook ingestion to Qdrant"""

import os
import PyPDF2
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
import uuid

print("Loading embedding model...")
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

print("Connecting to Qdrant...")
client = QdrantClient(url="http://localhost:6333")

def ingest_pdf(pdf_path, subject):
    print(f"\nProcessing: {os.path.basename(pdf_path)}")
    
    with open(pdf_path, 'rb') as file:
        pdf = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf.pages:
            text += page.extract_text()
    
    # Split into chunks
    chunks = []
    chunk_size = 1000
    overlap = 200
    
    for i in range(0, len(text), chunk_size - overlap):
        chunk = text[i:i + chunk_size]
        if len(chunk.strip()) > 50:
            chunks.append(chunk)
    
    print(f"  Created {len(chunks)} chunks")
    
    # Generate embeddings and upload
    points = []
    for idx, chunk in enumerate(chunks):
        embedding = model.encode(chunk).tolist()
        points.append(PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={
                "text": chunk,
                "subject": subject,
                "source": os.path.basename(pdf_path),
                "chunk_index": idx
            }
        ))
    
    client.upsert(collection_name="k12_textbooks", points=points)
    print(f"  ✅ Uploaded {len(points)} chunks")
    return len(points)

# Ingest all textbooks
total = 0

print("\n" + "="*60)
print("INGESTING SCIENCE TEXTBOOKS")
print("="*60)
for file in os.listdir("data/textbooks/science"):
    if file.endswith(".pdf"):
        total += ingest_pdf(f"data/textbooks/science/{file}", "science")

print("\n" + "="*60)
print("INGESTING MATHEMATICS TEXTBOOKS")
print("="*60)
for file in os.listdir("data/textbooks/mathematics"):
    if file.endswith(".pdf"):
        total += ingest_pdf(f"data/textbooks/mathematics/{file}", "mathematics")

print("\n" + "="*60)
print(f"✅ COMPLETE! Ingested {total} total chunks")
print("="*60)

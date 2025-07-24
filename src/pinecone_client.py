import os
from dotenv import load_dotenv

import pinecone
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
load_dotenv()

# Initialize Pinecone
pc = Pinecone(api_key="pcsk_3knenT_LgZnRKu4i9bNAfa4KQAQRkymRh1RCsXFctnVx6pGGjTbVP4HB919t6VB36e4uQB")

index_name = "chat-bot-hackathon"
dimension = 384

# ✅ Use free-tier supported region
if index_name not in pc.list_indexes():
    pc.create_index(
        name=index_name,
        dimension=dimension,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )

index = pc.Index(index_name)

model = SentenceTransformer('all-MiniLM-L6-v2')

chunks = [
    "HR Policy: New joiners are eligible for 20 days of paid leave annually. Leave requests must be submitted via the HR portal.",
    "Onboarding: Employees must complete onboarding training within the first week, including security and compliance modules.",
    "Project Alpha Overview: This project uses microservices architecture built with Spring Boot and deployed on GCP."
]

embeddings = model.encode(chunks)

for i, emb in enumerate(embeddings):
    index.upsert([
        {
            "id": str(i),
            "values": emb.tolist(),
            "metadata": {"text": chunks[i]}
        }
    ])

query = "How many paid leaves do new joiners get?"
query_emb = model.encode([query])[0]

results = index.query(
    vector=query_emb.tolist(),
    top_k=1,
    include_metadata=True
)
print("results:\n", results)
context = "\n".join([match['metadata']['text'] for match in results['matches']])
print("Retrieved Context:\n", context)
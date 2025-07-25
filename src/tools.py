import requests
import os
from langchain_core.tools import tool
#from langchain.tools import tool
#from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore # <-- Import PineconeVectorStore
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
load_dotenv()

# Placeholder for actual API calls
JIRA_API_URL = "https://your-company.atlassian.net/rest/api/2/issue"
JIRA_USER = "your-jira-email"
JIRA_TOKEN = os.getenv("JIRA_API_TOKEN") # Store this securely!

CAB_SERVICE_API_URL = "https://api.yourcabservice.com/v1/bookings"
CAB_SERVICE_API_KEY = os.getenv("CAB_API_KEY")

import random
import string
import secrets
import string
import datetime
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("chat-bot-hackathon")
model = SentenceTransformer('all-MiniLM-L6-v2')

def generate_secure_id(length=10):
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_cab_number():
    state_code = "TS"
    rto_code = random.randint(1, 99)
    series = ''.join(random.choices(string.ascii_uppercase, k=2))
    number = random.randint(1000, 9999)
    return f"{state_code}{rto_code:02d}{series}{number}"

def generate_otp(length=4):
    return ''.join(random.choices(string.digits, k=length))

def book_cab(pickup: str, destination: str, time: str) -> str:
    """Books a cab for the specified route and time."""
    print(f"--- Calling Cab Service API ---")
    # In a real scenario, you would make an API call like this:
    # headers = {"Authorization": f"Bearer {CAB_SERVICE_API_KEY}"}
    # payload = {"pickup": pickup, "destination": destination, "time": time}
    # response = requests.post(CAB_SERVICE_API_URL, json=payload, headers=headers)
    # if response.status_code == 201:
    #     return f"Successfully booked a cab from {pickup} to {destination} for {time}."
    # else:
    #     return f"Failed to book cab. Service returned: {response.text}"
    cab_number = generate_cab_number()
    otp = generate_otp()
    booking_id = generate_secure_id()
    return (
        f"CAB BOOKED: From {pickup} to {destination} at {time}. Booking ID: {booking_id}\n"
        f"Cab Number: {cab_number}\n"
        f"OTP for driver verification: {otp}"
    )



def create_ticket(description: str, summary: str) -> str:
    """Creates an IT support ticket in Jira or a similar system."""
    print(f"--- Calling Jira API ---")
    # In a real scenario, you would make an API call like this:
    # auth = (JIRA_USER, JIRA_TOKEN)
    # headers = {"Accept": "application/json", "Content-Type": "application/json"}
    # payload = {
    #     "fields": {
    #         "project": {"key": "IT"},
    #         "summary": summary,
    #         "description": description,
    #         "issuetype": {"name": "Task"}
    #     }
    # }
    # response = requests.post(JIRA_API_URL, json=payload, headers=headers, auth=auth)
    # if response.status_code == 201:
    #     ticket_key = response.json()['key']
    #     return f"Successfully created ticket {ticket_key} with summary: '{summary}'."
    # else:
    #     return f"Failed to create ticket. Jira returned: {response.text}"
    prefix = "INC"
    number = random.randint(1000000, 9999999)
    ticket_id = f"{prefix}{number}"

    # Optionally include a timestamp or mock sys_id
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {
        f"Ticket Created with Ticket id : {ticket_id} at {timestamp}."
        f"Summary: {{summary}}\n"
        f"You can check the status in here IT@LBG."   
    }


PINECONE_INDEX_NAME = "chat-bot-hackathon"
embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vectorstore = PineconeVectorStore(index_name=PINECONE_INDEX_NAME, embedding=embedding_function)
retriever = vectorstore.as_retriever(search_kwargs={'k': 1}) # Retrieve top 2 chunks
llm = ChatGroq(temperature=0, model_name="llama3-70b-8192")
template = """
Answer the question based ONLY on the following context.
If the context does not contain the answer, state that you don't have enough information to answer.
Do not use any information outside of this context.

Context:
{context}

Question:
{question}
"""
prompt = PromptTemplate.from_template(template)
rag_chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)
def company_docs_query(question: str) -> str:
    # ... (no change in this function)
    print(f"--- Looking up company policy for: '{question}' ---")
    return rag_chain.invoke(question)
# def company_docs_query(query: str) -> str:
#     """Answers HR or project-related questions using company documents."""
#     query_emb = model.encode([query])[0]
#     results = index.query(vector=query_emb.tolist(), top_k=2, include_metadata=True)
#     context = "\n".join([match['metadata']['text'] for match in results['matches']])
#     return f"Based on company documents:\n{context}"
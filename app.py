
import os
import uuid
import fitz
import chainlit as cl
from openai import AzureOpenAI
import requests
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter

load_dotenv()

# Azure OpenAI configuration
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = "text-embedding-3-large"
AZURE_DEPLOYMENT_ID = os.getenv("AZURE_DEPLOYMENT_ID")  # GPT model deployment
AZURE_API_VERSION = os.getenv("AZURE_API_VERSION")

# Azure AI Search configuration
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")
AZURE_SEARCH_INDEX_NAME = "agent-index"
AZURE_SEARCH_API_VERSION = os.getenv("AZURE_SEARCH_API_VERSION")

# DEBUG: print index name
print(f"Using Azure Search Index: {AZURE_SEARCH_INDEX_NAME}")

client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_API_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
)

SYSTEM_PROMPT = """
You are EasyDocs, an assistant that answers user questions based strictly on the content of official documents such as contracts, agreements, or insurance policies.

Your answers must only rely on the actual text of the document, without adding external knowledge or assumptions. If the question asks about something not found in the document, respond with:
"I'm sorry, I couldn’t find any relevant information about that in the document."

When the document is in Hebrew, respond in clear and simple Hebrew. When it's in English, respond in clear and simple English. Avoid translating languages unless the user asks you to.

Do not summarize or rewrite the document. Just answer questions about its contents faithfully and clearly.
"""


def split_pdf_into_chunks(file_path, chunk_size=800, chunk_overlap=100):
    doc = fitz.open(file_path)
    raw_text = ""
    for page in doc:
        raw_text += page.get_text() + "\n"

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", " "]
    )
    chunks = splitter.split_text(raw_text)
    print(f"Total chunks created: {len(chunks)}")
    return chunks


def embed_texts(chunks):
    print("Generating embeddings...")
    response = client.embeddings.create(
        input=chunks,
        model=AZURE_OPENAI_EMBEDDING_DEPLOYMENT
    )
    vectors = [item.embedding for item in response.data]
    print(f"Embeddings generated: {len(vectors)} vectors")
    return vectors


def upload_to_azure_search(chunks, embeddings, title="Uploaded Document"):
    url = f"{AZURE_SEARCH_ENDPOINT}/indexes/{AZURE_SEARCH_INDEX_NAME}/docs/index?api-version={AZURE_SEARCH_API_VERSION}"
    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_SEARCH_API_KEY
    }

    documents = []
    for i, (chunk, vector) in enumerate(zip(chunks, embeddings)):
        if vector is None:
            print(f"Missing embedding for chunk #{i}")
            continue
        documents.append({
            "@search.action": "upload",
            "id": str(uuid.uuid4()),
            "title": title,
            "content": chunk,
            "contentVector": vector
        })

    payload = {"value": documents}
    print(
        f"Uploading {len(documents)} chunks to Azure Search index: {AZURE_SEARCH_INDEX_NAME}")
    response = requests.post(url, headers=headers, json=payload)

    try:
        response.raise_for_status()
        print("Upload to Azure Search successful!")
        return True
    except requests.exceptions.RequestException as e:
        print("Upload failed:", e)
        print("Response:", response.text)
        return False


def retrieve_documents(query):

    embedding_response = client.embeddings.create(
        input=query,
        model=AZURE_OPENAI_EMBEDDING_DEPLOYMENT
    )
    vector = embedding_response.data[0].embedding

    url = f"{AZURE_SEARCH_ENDPOINT}/indexes/{AZURE_SEARCH_INDEX_NAME}/docs/search?api-version={AZURE_SEARCH_API_VERSION}"
    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_SEARCH_API_KEY
    }

    payload = {
        "search": query,
        "vector": {
            "value": vector,
            "fields": "contentVector",
            "k": 3
        },
        "searchFields": "content",
        "select": "content",
        "searchMode": "all"
    }

    response = requests.post(url, headers=headers, json=payload)
    print("Azure Search response:", response.text)
    response.raise_for_status()
    results = response.json()
    return [doc["content"] for doc in results.get("value", [])]


@cl.on_chat_start
async def start():
    await cl.Message(
        content="👋 Welcome to EasyDocs. You can now ask a question based on existing documents, or upload a new PDF file."
    ).send()

    await cl.Message(
        content="To upload a new document click the file icon."
    ).send()


@cl.on_message
async def handle_message(msg: cl.Message):
    query = msg.content.strip()

    if query.lower().startswith("/upload"):
        await cl.Message(content="📎 Please upload a PDF to add it to the index.").send()
        files = await cl.AskFileMessage(
            accept=["application/pdf"],
            max_size_mb=20
        ).send()

        if not files or len(files) == 0:
            await cl.Message(content="No file uploaded.").send()
            return

        await process_uploaded_file(files[0])
        return

    # RAG
    retrieved_docs = retrieve_documents(query)
    if not retrieved_docs:
        await cl.Message(content="Sorry, relevant content found.").send()
        return

    context = "\n\n".join(retrieved_docs)

    completion = client.chat.completions.create(
        model=AZURE_DEPLOYMENT_ID,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Answer the following question based on the documents:\n{context}\n\nQuestion: {query}"}
        ]
    )

    answer = completion.choices[0].message.content
    await cl.Message(content=answer).send()


async def process_uploaded_file(file):
    file_path = file.path
    file_name = file.name
    await cl.Message(content=f"Processing file: **{file_name}**...").send()

    try:
        chunks = split_pdf_into_chunks(file_path)
        embeddings = embed_texts(chunks)
        success = upload_to_azure_search(chunks, embeddings, title=file_name)

        if success:
            await cl.Message(
                content=f"Successfully uploaded *{file_name}* to the index! ({len(chunks)} chunks)"
            ).send()
        else:
            await cl.Message(content="Upload failed.").send()
    except Exception as e:
        await cl.Message(content=f"Error while uploading: {e}").send()

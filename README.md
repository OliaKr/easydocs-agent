## 🧾 EasyDocs

AI-powered tool designed to help **olim hadashim (new immigrants)** who have difficulty understanding official documents in Hebrew or English — such as rental agreements, contracts, or government forms.

Upload a document, ask your question in simple language, and receive a clear answer — based only on what's written in the document.

## 🧠 Key Features

- Upload and process any official document in PDF format
- Automatic text chunking and embedding generation
- Hybrid search using both text and semantic vectors
- Reliable answers generated **only** from the document itself
- Answers in **clear Hebrew or English**, depending on the document
- No external assumptions or interpretations

## 🛠️ Technologies Used

EasyDocs is built using modern tools that combine semantic search and generative AI:

- **Python** for backend logic and processing
- **Chainlit** to create an interactive chatbot-like interface
- **PyMuPDF** (`fitz`) to extract and read text from PDF files
- **LangChain** for smart text chunking
- **Azure OpenAI** to generate embeddings and answer questions using GPT-4
- **Azure Cognitive Search** for fast, vector-based retrieval from indexed documents
- **.env configuration** for managing secure API keys

## 🔄 How It Works

1. User uploads a PDF document (e.g. a lease or official form)
2. The document is split into small overlapping chunks
3. Each chunk is converted into a semantic embedding using Azure OpenAI
4. The chunks and embeddings are stored in an Azure AI Search index
5. When the user asks a question, an embedding is generated for the query
6. The system performs a hybrid semantic + text search in the index
7. Relevant document parts are retrieved and passed to the GPT model
8. A clear answer is generated based on those exact text segments only

## 💬 Example Questions

- What is the duration of the agreement?
- Are payments made monthly or upfront?
- What guarantees are required from the tenant?
- What happens if the contract is terminated early?

If the answer is not found in the document, the assistant will politely say so — without guessing.

---

## 🚀 Local Installation

1. Clone the repo  
   `git clone https://github.com/yourusername/easydocs && cd easydocs`

2. Install dependencies  
   `pip install -r requirements.txt`

3. Create a `.env` file with your credentials:

```bash
   AZURE_RESOURCE_NAME=...
   AZURE_OPENAI_ENDPOINT=...
   AZURE_OPENAI_API_KEY=...
   AZURE_DEPLOYMENT_ID=...
   AZURE_API_VERSION=...

   AZURE_SEARCH_ENDPOINT=...
   AZURE_SEARCH_API_KEY=...
   AZURE_SEARCH_INDEX_NAME=...
   AZURE_SEARCH_API_VERSION=...
```

4. Run the app

```bash
chainlit run app.py

```

![תמונה](https://github.com/OliaKr/easydocs-agent/blob/main/.public/easy1.JPG)
![תמונה](https://github.com/OliaKr/easydocs-agent/blob/main/.public/easy2.JPG)

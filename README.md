# LightRAG Ask AI

A local Retrieval-Augmented Generation (RAG) conversational agent built on top of [LightRAG](https://github.com/HKUDS/LightRAG). This project allows you to seamlessly chat with and extract insights from your documents using state-of-the-art embedding, reranking, and Large Language Models (LLMs).

## 🚀 What This Project Is
This application ingests text documents (like the provided `sample.md` story) into a knowledge graph and vector database. It then provides an interactive command-line interface to ask questions about the documents. 
By utilizing hybrid search modes, semantic embeddings, and an advanced reranker, the agent can fetch highly context-relevant information to generate accurate and comprehensive answers powered by OpenAI models (e.g., `gpt-4o`).

## 🛠️ Tech Stack Used
* **Python**: Core programming language.
* **LightRAG**: The underlying framework for blazing-fast knowledge graph-based RAG.
* **Sentence-Transformers (PyTorch)**: 
  * Embedding Model: `BAAI/bge-m3`
  * Reranker Model: `BAAI/bge-reranker-v2-m3`
* **OpenAI API**: For target LLM generation.
* **Asyncio**: For non-blocking, asynchronous execution of embeddings and queries.
* **Numpy**: Handling embedding arrays.

## ✨ Advantages
1. **High Retrieval Accuracy**: Combines LightRAG's graph-based retrieval with the powerful BGE-M3 embedding model and cross-encoder reranking.
2. **Dynamic Query Modes**: Switch between multiple RAG query modes in real-time (`mix`, `hybrid`, `local`, `global`, `naive`).
3. **Hardware Acceleration**: Automatically detects and utilizes NVIDIA GPUs (CUDA) via PyTorch if available, falling back gracefully to CPU.
4. **Interactive CLI**: Simple and engaging chat loop to query your documents right from the terminal.

## 📦 How to Install and Run

### Prerequisites
* Python 3.10+
* An OpenAI API Key

### Step-by-Step Installation
1. **Clone the Repository** (or navigate to your project directory):
   ```bash
   cd LightRAG-askAI
   ```

2. **Create a Virtual Environment** (Recommended):
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Setup**:
   Copy the example environment file and add your OpenAI API Key.
   ```bash
   cp env.example .env
   ```
   Open `.env` and configure your credentials:
   ```env
   OPENAI_API_KEY=your-actual-api-key-here
   OPENAI_MODEL=gpt-4o
   RAG_STORAGE_DIR=./rag_storage
   ```

5. **Run the Application**:
   ```bash
   python app.py
   ```
   The application will initialize, embed the `sample.md` file, and drop you into an interactive chat prompt where you can start asking questions!

## 💡 Usage Commands
Inside the chat interface, you can type the following commands:
* **Ask a question**: Normally type your query and hit Enter.
* **Change Mode**: Type `mode <mix|hybrid|local|global|naive>` to switch the search strategy.
* **Exit**: Type `quit` or `exit` to close the application.

import os
import asyncio
import numpy as np
import torch
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer, CrossEncoder
from lightrag import LightRAG, QueryParam
from lightrag.utils import EmbeddingFunc, setup_logger
from openai import OpenAI

setup_logger("lightrag", level="INFO")

load_dotenv()

WORKING_DIR = os.getenv("RAG_STORAGE_DIR", "./rag_storage")
if not os.path.exists(WORKING_DIR):
    os.mkdir(WORKING_DIR)

OPENAI_API_KEY    = os.getenv("OPENAI_API_KEY")
OPENAI_CHAT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

client = OpenAI(api_key=OPENAI_API_KEY)

_device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"[Device] Using: {_device.upper()}")

embed_model = SentenceTransformer(
    "BAAI/bge-m3",
    device=_device,
    model_kwargs={"torch_dtype": torch.float16} if _device == "cuda" else {},
)
print("[Embed] bge-m3 loaded.")

EMBED_DIM   = 1024
MAX_TOKENS  = 8192
_BATCH_SIZE = 2 if _device == "cpu" else 12


async def huggingface_embed(texts: list[str]) -> np.ndarray:
    loop = asyncio.get_event_loop()
    embeddings = await loop.run_in_executor(
        None,
        lambda: embed_model.encode(
            texts,
            batch_size=_BATCH_SIZE,
            normalize_embeddings=True,
            show_progress_bar=False,
        ),
    )
    return np.array(embeddings, dtype=np.float32)


embedding_func = EmbeddingFunc(
    embedding_dim=EMBED_DIM,
    max_token_size=MAX_TOKENS,
    func=huggingface_embed,
)

# bge-reranker-v2-m3
reranker = CrossEncoder(
    "BAAI/bge-reranker-v2-m3",
    device=_device,
    automodel_args={
        "torch_dtype": torch.float16 if _device == "cuda" else torch.float32
    },
)
print("[Rerank] bge-reranker-v2-m3 loaded.")


async def rerank_func(query: str, documents: list[str], top_n: int) -> list[dict]:
    loop = asyncio.get_event_loop()
    pairs  = [(query, doc) for doc in documents]
    scores = await loop.run_in_executor(
        None,
        lambda: reranker.predict(pairs, show_progress_bar=False),
    )
    ranked = sorted(
        [{"index": i, "relevance_score": float(s)} for i, s in enumerate(scores)],
        key=lambda x: x["relevance_score"],
        reverse=True,
    )
    return ranked[:top_n]


async def openai_llm_func(
    prompt: str,
    system_prompt: str | None = None,
    history_messages: list | None = None,
    **kwargs,
) -> str:
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    if history_messages:
        messages.extend(history_messages)
    messages.append({"role": "user", "content": prompt})

    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        lambda: client.chat.completions.create(
            model=OPENAI_CHAT_MODEL,
            messages=messages,
            **{k: v for k, v in kwargs.items() if k in ("temperature", "max_tokens")},
        ),
    )
    return response.choices[0].message.content


async def initialize_rag() -> LightRAG:
    rag = LightRAG(
        working_dir=WORKING_DIR,
        embedding_func=embedding_func,
        llm_model_func=openai_llm_func,
        embedding_func_max_async=1,
        rerank_model_func=rerank_func,
    )
    await rag.initialize_storages()
    return rag


async def insert_documents(rag: LightRAG, files: list[str]) -> None:
    for file_path in files:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            await rag.ainsert(text)
            print(f"✓ Inserted '{file_path}' into RAG / knowledge graph.")
        else:
            print(f"✗ File not found: {file_path}")


# Chat
async def chat_loop(rag: LightRAG) -> None:
    mode = "mix"
    print("\n" + "═" * 60)
    print("  Document Q&A ready  —  ask anything about your docs")
    print(f"  Current query mode : {mode}  (reranker active)")
    print("  Commands : mode <mix|hybrid|local|global|naive> | quit")
    print("═" * 60 + "\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting chat.")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit"):
            print("Goodbye!")
            break

        if user_input.lower().startswith("mode "):
            new_mode = user_input.split(maxsplit=1)[1].strip().lower()
            if new_mode in ("mix", "hybrid", "local", "global", "naive"):
                mode = new_mode
                print(f"  ✓ Query mode switched to: {mode}\n")
            else:
                print("  ✗ Unknown mode. Choose: mix | hybrid | local | global | naive\n")
            continue

        try:
            print("AI: ", end="", flush=True)
            answer = await rag.aquery(
                user_input,
                param=QueryParam(mode=mode, enable_rerank=True),
            )
            print(answer)
            print()
        except Exception as e:
            print(f"[Error during query: {e}]\n")


async def main() -> None:
    rag = None
    try:
        rag = await initialize_rag()
        await insert_documents(rag, ["sample.md"])
        await chat_loop(rag)
    except Exception as e:
        print(f"An error occurred: {e}")
        raise
    finally:
        if rag:
            await rag.finalize_storages()


if __name__ == "__main__":
    asyncio.run(main())
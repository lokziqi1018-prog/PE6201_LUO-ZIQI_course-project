import os, re, json
from dotenv import load_dotenv
from openai import OpenAI
import chromadb
from chromadb.utils import embedding_functions
from data import HR_DOCS

load_dotenv()
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="https://openrouter.ai/api/v1" # 增加此行，指向 OpenRouter 节点
)

# 初始化本地向量数据库
chroma_client = chromadb.Client()
collection = chroma_client.create_collection(
    name="hr_docs",
    embedding_function=embedding_functions.DefaultEmbeddingFunction()
)

for doc in HR_DOCS:
    collection.add(
        documents=[doc["content"]],
        metadatas=[{"title": doc["title"]}],
        ids=[str(doc["doc_id"])]
    )


def keyword_baseline(query):
    if not query.strip():
        return "False"
    words = set(query.lower().split())
    max_matches = 0
    for doc in HR_DOCS:
        matches = len(words.intersection(set(doc["content"].lower().split())))
        if matches > max_matches:
            max_matches = matches
    return "True" if max_matches > 3 else "False"


def prompt_v1(q, ctx):
    return f"You are an HR assistant. Answer this query based on context.\nContext: {ctx}\nQuery: {q}\nReturn JSON with eligible, reason, policy_reference."


def prompt_v2(q, ctx):
    return (
        "You are an automated HR Policy Assistant.\n"
        "Return ONLY a raw JSON object without markdown code blocks.\n"
        "Fields MUST be: ['eligible', 'reason', 'policy_reference'].\n"
        "Field 'eligible' MUST strictly be 'True' or 'False'.\n"
        "If query is invalid, empty, or not mentioned in policy, set 'eligible' to 'False'.\n\n"
        f"CONTEXT:\n{ctx}\n\nQUERY: {q}"
    )


def run_rag(query, prompt_fn):
    if not query.strip():
        return '{"eligible": "False", "reason": "Empty input", "policy_reference": "N/A"}'

    docs = collection.query(query_texts=[query], n_results=2)["documents"][0]
    context = "\n".join(docs) if docs else "No document found."

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt_fn(query, context)}],
        temperature=0.0
    )
    return res.choices[0].message.content


def check_l1(raw, case):
    try:
        m = re.search(r'\{.*\}', raw, re.S)
        if not m:
            return False
        obj = json.loads(m.group(0))
        if str(obj.get("eligible", "")).capitalize() not in ["True", "False"]:
            return False
        return str(obj.get("eligible", "")).lower() == str(case.expect.get("eligible", "")).lower()
    except Exception:
        return False
# %% [markdown]
# # Adaptive RAG
# 
# Adaptive RAG is a strategy for RAG that unites (1) [query analysis](https://blog.langchain.dev/query-construction/) with (2) [active / self-corrective RAG](https://blog.langchain.dev/agentic-rag-with-langgraph/).
# 
# In the [paper](https://arxiv.org/abs/2403.14403), they report query analysis to route across:
# 
# * No Retrieval
# * Single-shot RAG
# * Iterative RAG
# 
# Let's build on this using LangGraph. 
# 
# In our implementation, we will route between:
# 
# * Web search: for questions related to recent events
# * Self-corrective RAG: for questions related to our index
# 
# ![Screenshot 2024-03-26 at 1.36.03 PM.png](attachment:36fa621a-9d3d-4860-a17c-5d20e6987481.png)

# %% [markdown]
# # Environment 

# %%
# %%capture --no-stderr
# ! pip install -U langchain_community tiktoken langchain-openai langchain-cohere langchainhub chromadb langchain langgraph  tavily-python

# %%
### LLMs
import os

# os.environ["OPENAI_API_KEY"] = ""
EMBEDDING_MODEL = "text-embedding-3-large"
LANGUAGE_MODEL = "gpt-4o-mini"
TEMPERATURE = 0.2

# %% [markdown]
# ### Tracing
# 
# * Optionally, use [LangSmith](https://docs.smith.langchain.com/) for tracing (shown at bottom) by setting: 

# %%
# ### Tracing (optional)
# os.environ["LANGCHAIN_TRACING_V2"] = "true"
# os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
# os.environ["LANGCHAIN_API_KEY"] = "<your-api-key>"

# %% [markdown]
# ## Index

# %%
### Build Index
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

# Set embeddings
embd = OpenAIEmbeddings(model=EMBEDDING_MODEL)

# Add to vectorstore
vectorstore = Chroma(
    persist_directory="../chroma_langchain_db",
    collection_name="summary_content",
    embedding_function=embd,
)
retriever = vectorstore.as_retriever()

# %% [markdown]
# ## LLMs

# %%
### Router

from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI


# Data model
class RouteQuery(BaseModel):
    """Route a user query to the most relevant datasource."""

    datasource: Literal["vectorstore", "denial"] = Field(
        ...,
        description="Given a user question, choose to route it to denial or a vectorstore.",
    )


# LLM with function call
llm = ChatOpenAI(model=LANGUAGE_MODEL, temperature=TEMPERATURE)
structured_llm_router = llm.with_structured_output(RouteQuery)

# Prompt
system = """You are an expert at routing a user question to a vectorstore or a denial.
The vectorstore contains documents related to 通訊所相關辦法，涵蓋各式碩士生和博士生的規定.
Use the vectorstore for questions on these topics. Otherwise, deny."""
route_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "{question}"),
    ]
)

question_router = route_prompt | structured_llm_router
# print(
#     question_router.invoke(
#         {"question": "Who will the Bears draft first in the NFL draft?"}
#     )
# )
# print(question_router.invoke({"question": "博士班學生畢業所需學分?"}))

# %%
### Retrieval Grader

# Data model
class GradeDocuments(BaseModel):
    """Binary score for relevance check on retrieved documents."""

    binary_score: str = Field(
        description="Documents are relevant to the question, 'yes' or 'no'"
    )


# LLM with function call
llm = ChatOpenAI(model=LANGUAGE_MODEL, temperature=TEMPERATURE)
structured_llm_grader = llm.with_structured_output(GradeDocuments)

# Prompt
system = """You are a grader assessing relevance of a retrieved document to a user question. \n 
    If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant. \n
    It does not need to be a stringent test. The goal is to filter out erroneous retrievals. \n
    Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question."""
grade_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "Retrieved document: \n\n {document} \n\n User question: {question}"),
    ]
)

retrieval_grader = grade_prompt | structured_llm_grader
# question = "博士班畢業規定"
# docs = retriever.invoke(question)
# for i in range(len(docs)):
#     doc_txt = docs[i].page_content
#     print(retrieval_grader.invoke({"question": question, "document": doc_txt}))

# %%
# print([docs[i].metadata for i in range(len(docs))])

# %%
# print(docs)

# %%
### Generate

from langchain_core.output_parsers import StrOutputParser

# Prompt
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "human",
            """任務：使用所有文件中提供的內容，以繁體中文簡潔扼要的回答問題。

指示：

平等對待：在形成您的回答時，請確保您對每個文件給予同等的重要性。

標題與內容的整合：您的回答必須整合並反映每個文件的標題和主要內容，因為它們是密切相關的。

結合且統一的回答：提供一個全面且詳細的回答，將所有文件的見解編織成一個統一的回應。避免逐文件列出資訊，而是將相關點融合在一起，形成一個連貫的敘述。

額外辦法、獎學金等的獨立處理：在回答問題時，首先確認文件是否涉及額外辦法、獎學金或類似內容。如果是，請將這些文件內容單獨提取並放置，不與一般辦法混合。清楚描述申請這些辦法後，申請者可能會面臨的變化或需要滿足的不同需求，確保讀者能夠清晰理解這些變化及其影響。

考慮變化和可選方法：如果文件之間的細節或觀點有所不同，請在回答中流暢地整合這些差異。特別注意方法或做法是否被描述為可選。明確指出某個方法是可選的，並解釋其含義，確保它不會被誤認為是標準方法。舉例來說：額外辦法或獎學金的辦法通常為可選的。

清晰度：如果從所有文件中無法清楚地回答問題，請說明該資訊不可用。

審查過程：仔細審查全部內容，確保您的回答充分考慮每個文件的標題和內容之間的聯繫。確保文件之間的區別被流暢地整合，提供一個連貫且全面的回答，反映所有文件的統一理解。明確識別並解釋任何可選的方法或做法，確保它們被適當地表示為可選項。

問題：{question}
文件：{context}
回答：
""",
        ),
    ]
)

# LLM
llm = ChatOpenAI(model_name=LANGUAGE_MODEL, temperature=1)


# Post-processing
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


# Chain
rag_chain = prompt | llm | StrOutputParser()

# Run
# generation = rag_chain.invoke({"context": docs, "question": question})
# print(generation)

# %%
# print({"context": docs, "question": question})

# %%
### Hallucination Grader


# Data model
class GradeHallucinations(BaseModel):
    """Binary score for hallucination present in generation answer."""

    binary_score: str = Field(
        description="Answer is grounded in the facts, 'yes' or 'no'"
    )


# LLM with function call
llm = ChatOpenAI(model=LANGUAGE_MODEL, temperature=TEMPERATURE)
structured_llm_grader = llm.with_structured_output(GradeHallucinations)

# Prompt
system = """You are a grader assessing whether an LLM generation is grounded in / supported by a set of retrieved facts. \n 
     Give a binary score 'yes' or 'no'. 'Yes' means that the answer is grounded in / supported by the set of facts."""
hallucination_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "Set of facts: \n\n {documents} \n\n LLM generation: {generation}"),
    ]
)

hallucination_grader = hallucination_prompt | structured_llm_grader
# hallucination_grader.invoke({"documents": docs, "generation": generation})

# %%
### Answer Grader


# Data model
class GradeAnswer(BaseModel):
    """Binary score to assess answer addresses question."""

    binary_score: str = Field(
        description="Answer addresses the question, 'yes' or 'no'"
    )


# LLM with function call
llm = ChatOpenAI(model=LANGUAGE_MODEL, temperature=TEMPERATURE)
structured_llm_grader = llm.with_structured_output(GradeAnswer)

# Prompt
system = """You are a grader assessing whether an answer addresses / resolves a question \n 
     Give a binary score 'yes' or 'no'. Yes' means that the answer resolves the question."""
answer_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "User question: \n\n {question} \n\n LLM generation: {generation}"),
    ]
)

answer_grader = answer_prompt | structured_llm_grader
# answer_grader.invoke({"question": question, "generation": generation})

# %%
### Question Re-writer

# LLM
llm = ChatOpenAI(model=LANGUAGE_MODEL, temperature=TEMPERATURE)

# Prompt
system = """You a question re-writer that converts an input question to a better version that is optimized \n 
     for vectorstore retrieval. Look at the input and try to reason about the underlying semantic intent / meaning."""
re_write_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        (
            "human",
            "Here is the initial question: \n\n {question} \n\n 根據問題，應要使用什麼關鍵字找資料。請直接舉數例關鍵字句，並刪去關鍵字以外的部分。舉例：「博士班 畢業要求」、「博士學位 學分規定」、等等.",
        ),
    ]
)

question_rewriter = re_write_prompt | llm | StrOutputParser()
# question_rewriter.invoke({"question": question})

# %% [markdown]
# ## Web Search Tool

# %%
# ### Search

# from langchain_community.tools.tavily_search import TavilySearchResults

# web_search_tool = TavilySearchResults(k=3)

# %% [markdown]
# # Graph 
# 
# Capture the flow in as a graph.
# 
# ## Graph state

# %%
from typing import List

from typing_extensions import TypedDict


class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        question: question
        query: query
        generation: LLM generation
        documents: list of documents
    """

    question: str
    query: str
    generation: str
    documents: List[str]
    filter_documents: List[str]

# %% [markdown]
# ## Graph Flow 

# %%
from langchain.schema import Document
import concurrent.futures

def retrieve(state):
    """
    Retrieve documents

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, documents, that contains retrieved documents
    """
    print("---RETRIEVE---")
    print(state)
    question = state["question"]
    query = state["query"]
    filter_documents = state["filter_documents"]

    # Retrieval
    documents = retriever.invoke(query)
    return {"documents": documents, "filter_documents": filter_documents, "question": question, "query": query}


def generate(state):
    """
    Generate answer

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, generation, that contains LLM generation
    """
    print("---GENERATE---")
    question = state["question"]
    query = state["query"]
    filter_documents = state["filter_documents"]

    # RAG generation
    generation = rag_chain.invoke({"context": filter_documents, "question": question})
    return {"filter_documents": filter_documents, "question": question, "generation": generation, "query": query}


def grade_documents(state):
    """
    Determines whether the retrieved documents are relevant to the question.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates documents key with only filtered relevant documents
    """

    print("---CHECK DOCUMENT RELEVANCE TO QUESTION---")
    question = state["question"]
    query = state["query"]
    documents = state["documents"]
    filter_documents = state["filter_documents"]

    # Score each doc
    filtered_docs = filter_documents

    def grade_document(d, query):
        print("Start")
        score = retrieval_grader.invoke({"question": query, "document": d.page_content})
        grade = score.binary_score
        if grade == "yes":
            print("---GRADE: DOCUMENT RELEVANT---")
            print(d.metadata["title"])
            return d  # Return the document if relevant
        else:
            print("---GRADE: DOCUMENT NOT RELEVANT---")
            print(d.metadata["title"])
            return None  # Return None if not relevant

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(grade_document, d, query) for d in documents]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result is not None and result not in filtered_docs:
                filtered_docs.append(result)
        
    return {"filter_documents": filtered_docs, "question": question, "query": query}


def transform_query(state):
    """
    Transform the query to produce a better question.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates question key with a re-phrased question
    """

    print("---TRANSFORM QUERY---")
    question = state["question"]
    query = state["query"]
    filter_documents = state["filter_documents"]

    # Re-write question
    better_query = question_rewriter.invoke({"question": query})
    return {"filter_documents": filter_documents, "question": question, "query": better_query}


def denial(state):
    """
    Deny the question.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates documents key with appended web results
    """

    print("---DENY---")
    question = state["question"]

    return {"generation": "Please ask again. Question need to be related to our document about 通訊所相關辦法.", "question": question}


# %%
### Edges ###


def route_question(state):
    """
    Route question to denial or RAG.

    Args:
        state (dict): The current graph state

    Returns:
        str: Next node to call
    """

    print("---ROUTE QUESTION---")
    question = state["question"] 
    
    source = question_router.invoke({"question": question})
    if source.datasource == "denial":
        print("---ROUTE QUESTION TO DENIAL---")
        return "denial"
    elif source.datasource == "vectorstore":
        print("---ROUTE QUESTION TO RAG---")
        return "vectorstore"


def decide_to_generate(state):
    """
    Determines whether to generate an answer, or re-generate a question.

    Args:
        state (dict): The current graph state

    Returns:
        str: Binary decision for next node to call
    """

    print("---ASSESS GRADED DOCUMENTS---")
    # state["question"]
    filter_documents = state["filter_documents"]

    if len(filter_documents) < 2:
        # All documents have been filtered check_relevance
        # We will re-generate a new query
        print(
            "---DECISION: ALL DOCUMENTS ARE NOT RELEVANT TO QUESTION, TRANSFORM QUERY---"
        )
        return "transform_query"
    else:
        # We have relevant documents, so generate answer
        print("---DECISION: GENERATE---")
        return "generate"


def grade_generation_v_documents_and_question(state):
    """
    Determines whether the generation is grounded in the document and answers question.

    Args:
        state (dict): The current graph state

    Returns:
        str: Decision for next node to call
    """

    print("---CHECK HALLUCINATIONS---")
    question = state["question"]
    documents = state["documents"]
    generation = state["generation"]

    score = hallucination_grader.invoke(
        {"documents": documents, "generation": generation}
    )
    grade = score.binary_score

    # Check hallucination
    if grade == "yes":
        print("---DECISION: GENERATION IS GROUNDED IN DOCUMENTS---")
        # Check question-answering
        print("---GRADE GENERATION vs QUESTION---")
        score = answer_grader.invoke({"question": question, "generation": generation})
        grade = score.binary_score
        if grade == "yes":
            print("---DECISION: GENERATION ADDRESSES QUESTION---")
            return "useful"
        else:
            print("---DECISION: GENERATION DOES NOT ADDRESS QUESTION---")
            return "not useful"
    else:
        print("---DECISION: GENERATION IS NOT GROUNDED IN DOCUMENTS, RE-TRY---")
        return "not supported"

# %% [markdown]
# ## Build Graph

# %%
from langgraph.graph import END, StateGraph, START

workflow = StateGraph(GraphState)

# Define the nodes
workflow.add_node("denial", denial)  # deny
workflow.add_node("retrieve", retrieve)  # retrieve
workflow.add_node("grade_documents", grade_documents)  # grade documents
workflow.add_node("generate", generate)  # generatae
workflow.add_node("transform_query", transform_query)  # transform_query

# Build graph
workflow.add_conditional_edges(
    START,
    route_question,
    {
        "denial": "denial",
        "vectorstore": "retrieve",
    },
)
workflow.add_edge("denial", END)
workflow.add_edge("retrieve", "grade_documents")
workflow.add_conditional_edges(
    "grade_documents",
    decide_to_generate,
    {
        "transform_query": "transform_query",
        "generate": "generate",
    },
)
workflow.add_edge("transform_query", "retrieve")
workflow.add_conditional_edges(
    "generate",
    grade_generation_v_documents_and_question,
    {
        "not supported": "generate",
        "useful": END,
        "not useful": "transform_query",
    },
)

# Compile
graph = workflow.compile()

# # %%
# from IPython.display import Image, display

# try:
#     display(Image(graph.get_graph(xray=True).draw_mermaid_png()))
# except Exception:
#     # This requires some extra dependencies and is optional
#     pass

# # %%
# from pprint import pprint

# # Run
# inputs = {
#     "question": "What player at the Bears expected to draft first in the 2024 NFL draft?",
#     "query": "What player at the Bears expected to draft first in the 2024 NFL draft?",
# }
# for output in graph.stream(inputs):
#     for key, value in output.items():
#         # Node
#         pprint(f"Node '{key}':")
#         # Optional: print full state at each node
#         # pprint.pprint(value["keys"], indent=2, width=80, depth=None)
#     pprint("\n---\n")

# # Final generation
# # print(output)
# pprint(value["generation"])
# if key == "generate":
#     print([value["documents"][i].metadata for i in range(len(value["documents"]))])

# # %% [markdown]
# # Trace: 
# # 
# # https://smith.langchain.com/public/7e3aa7e5-c51f-45c2-bc66-b34f17ff2263/r

# # %%
# # Run
# inputs = {"query": "博士有哪些畢業管道", "question": "博士有哪些畢業管道", "filter_documents": []}
# for output in graph.stream(inputs):
#     for key, value in output.items():
#         # Node
#         # pprint(f"Node '{key}':")
#         # Optional: print full state at each node
#         pprint(value, indent=2, width=80, depth=None)
#     # pprint("\n---\n")

# # Final generation
# pprint(value["generation"])
# if key == "generate":
#     print([value["filter_documents"][i].metadata for i in range(len(value["filter_documents"]))])

# # %% [markdown]
# # Trace: 
# # 
# # https://smith.langchain.com/public/fdf0a180-6d15-4d09-bb92-f84f2105ca51/r

# # %%
# print(value["filter_documents"])



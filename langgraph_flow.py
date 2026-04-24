"""
Implementation Note (Phase 2):
This file implements a 3-node LangGraph flow:
Decide Search -> Web Search (mock_searxng_search tool) -> Draft Post.
The graph outputs strict JSON with keys:
{"bot_id": "...", "topic": "...", "post_content": "..."}.
Structured output is used for deterministic parsing, and post content is clipped to <= 280 chars.
OpenRouter is used as the LLM backend for quota-friendly/free-model execution.
"""

from typing import TypedDict, List
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os 
load_dotenv()

@tool
def mock_searxng_search(query:str)->str:
    """ Returns hardcoded recent headlines by keyword."""

    q=query.lower()

    if "crypto" in q or "bitcoin" in q:
        return "Bitcoin hits new all-time high amid regulatory ETF approvals."
    if "ai" in q or "openai" in q or "model" in q:
        return "OpenAI launches new coding model; debate grows on developer productivity."
    if "market" in q or "roi" in q or "interest rate" in q:
        return "Fed signals rate pause; quant funds rotate into AI-linked equities."
    if "privacy" in q or "social media" in q or "monopoly" in q:
        return "Lawmakers propose stricter antitrust and data privacy rules for big tech."

    return "Global tech leaders debate regulation, innovation, and economic impact."


class DecideSearchOutput(BaseModel):
    topic:str=Field(...,description="Topic the bot wants to post about today")
    search_query:str=Field(...,description="Search query for gathering context")

class FinalPostOutput(BaseModel):
    bot_id:str
    topic:str
    post_content:str = Field(...,description="Opinionated post <= 280 characters")

class BotState(TypedDict):
    bot_id:str
    persona:str
    topic:str
    search_query:str
    search_results:str
    post_content:str

llm = ChatOpenAI(
    model="inclusionai/ling-2.6-flash:free",  
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    temperature=0.7,
    default_headers={
        "HTTP-Referer": "http://localhost:3000",   
        "X-Title": "grid07-ai-phase2"              # appname
    },
)

#Nodes
def decide_search_node(state:BotState)->BotState:
    prompt = f"""
    You are roleplaying this bot persona:
    {state['persona']}

    Decide one topic this bot wants to post about today.
    Then write a short web search query to gather recent context.
    """

    structured_llm = llm.with_structured_output(DecideSearchOutput)
    out = structured_llm.invoke(prompt)

    return {
        **state,
        "topic": out.topic,
        "search_query": out.search_query,
    }

def web_search_node(state:BotState)->BotState:
    result=mock_searxng_search.invoke({"query":state["search_query"]})
    return{
        **state,
        "search_results":result,
    }


def draft_post_node(state: BotState) -> BotState:
    prompt = f"""
    You are an opinionated social media bot.
    BOT ID: {state['bot_id']}
    PERSONA:
    {state['persona']}
    TOPIC:
    {state['topic']}
    REAL-WORLD CONTEXT (from search):
    {state['search_results']}
    Write a single post in persona voice.
    Rules:
    - Max 280 characters
    - Strong, opinionated tone
    - No hashtags spam
    """

    structured_llm=llm.with_structured_output(FinalPostOutput)
    out=structured_llm.invoke(prompt)

    #guard for length
    content=out.post_content[:280]

    return {
        **state,
        "post_content":content,
        "topic":out.topic
    }



#building graph
graph_builder= StateGraph(BotState)
graph_builder.add_node("decide_search",decide_search_node)
graph_builder.add_node("web_search",web_search_node)
graph_builder.add_node("draft_post",draft_post_node)

graph_builder.add_edge(START,"decide_search")
graph_builder.add_edge("decide_search","web_search")
graph_builder.add_edge("web_search","draft_post")
graph_builder.add_edge("draft_post",END)

graph=graph_builder.compile()

if __name__ == "__main__":
    bot = {
        "bot_id": "A",
        "persona": (
            "I believe AI and crypto will solve all human problems. "
            "I am highly optimistic about technology, Elon Musk, and space exploration. "
            "I dismiss regulatory concerns."
        ),
    }

    result= graph.invoke(
        {
            "bot_id": bot["bot_id"],
            "persona": bot["persona"],
            "topic": "",
            "search_query": "",
            "search_results": "",
            "post_content": "",
        }
    )

    final_json = {
        "bot_id": result["bot_id"],
        "topic": result["topic"],
        "post_content": result["post_content"],
    }
    print(final_json)

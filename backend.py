import os 
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
load_dotenv()

from typing import TypedDict, Annotated
import operator
import uuid

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_core.messages import (
    AnyMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
)
from langchain_openai import ChatOpenAI
from tools.hotel_search import tavily_search
from tools.flight_search import search_flights


llm = ChatOpenAI(model="gpt-5-mini")

def get_database_url():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError(
            "DATABASE_URL is missing. Please add your Render PostgreSQL External Database URL to .env"
        )

    if "sslmode=" not in database_url:
        separator = "&" if "?" in database_url else "?"
        database_url = f"{database_url}{separator}sslmode=require"
        
    return database_url



class PlannerState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    user_query: str
    route : str
    sightseeing_results: str
    hotel_results: str
    food_results : str
    flight_results : str
    itinerary: str
    llm_calls: int

def router_agent(state: PlannerState):
    response = llm.invoke([
        SystemMessage(content="""
        Classify the user's request.

        Return exactly TRAVEL if the request is about:
        trips, itineraries, flights, hotels, restaurants,
        sightseeing, or travel destinations.

        Return exactly GENERAL for all other requests.

        Output only one word: TRAVEL or GENERAL.
        """),
        HumanMessage(content=state["user_query"])
    ])

    route = response.content.strip().upper()

    if route not in ["TRAVEL", "GENERAL"]:
        route = "GENERAL"

    return {
        "route": route,
        "llm_calls": state.get("llm_calls", 0) + 1
    }

def general_agent(state: PlannerState):
    response = llm.invoke([
        SystemMessage(content=(
            "You are a travel planning assistant. "
            "Only answer questions related to travel, trips, "
            "destinations, flights, hotels, restaurants, and itineraries. "
            "For any unrelated question, do not answer it. "
            "Instead, say: 'I can only help with travel-related questions. "
            "Please ask me about a trip!'"
        )),
        HumanMessage(content=state["user_query"])
    ])

    return {
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1
    }

def flight_agent(state: PlannerState):

    query = state["user_query"]
    flight_data = search_flights(query)

    return {
        "flight_results": flight_data,
        "messages": [
            AIMessage(content="Flight results fetched.")
        ],
        "llm_calls": state.get("llm_calls", 0) + 1
    }


def hotel_restaurant_agent(state: PlannerState):
    
    destination = state["user_query"]

    hotel_results = tavily_search(
        f"Best hotels in {destination} for different budgets"
    )

    food_results = tavily_search(
        f"Best restaurants, local food, and must-try dishes in {destination}"
    )

    return {
        "hotel_results": hotel_results,
        "food_results": food_results,
        "messages": [
            AIMessage(content="Hotel and food information fetched.")
        ]
    }


def sightseeing_agent(state: PlannerState):

    query = f" Must see places in {state['user_query']}"

    response = llm.invoke([
            SystemMessage(content="You are an expert travel planner."),
            HumanMessage(content=query)
        ])

    return {
        "sightseeing_results": response.content,
        "messages": [
            response
        ],

        "llm_calls": state.get("llm_calls", 0) + 1
    }



def itinerary_agent(state: PlannerState):
    prompt = f"""
Create a complete travel itinerary.

User Request:
{state['user_query']}


Hotels:
{state['hotel_results']}

Food:
{state['food_results']}

Places:
{state['sightseeing_results']}

Make the itinerary practical, budget-aware, and easy to follow.
"""

    response = llm.invoke([
        SystemMessage(content="You are an expert travel planner."),
        HumanMessage(content=prompt)
    ])

    return {
        "itinerary": response.content,
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1
    }


def final_agent(state: PlannerState):

    final_prompt = f"""
Generate the final travel response for the user.

User Request:
{state['user_query']}

Flights:
{state['flight_results']}

Hotels:
{state['hotel_results']}

Food:
{state['food_results']}
Places:
{state['sightseeing_results']}
Itinerary:
{state['itinerary']}

Format the final answer beautifully using these sections:

1. Trip Summary
2. Flight Information
3. Hotel Suggestions
4. Food Suggestions
5. Must see places 
6. Day-by-Day Itinerary
7. Estimated Budget
8. Final Recommendations

Important:
- Be clear and practical.
- Mention that live flight API may not provide ticket prices if pricing is unavailable.
- Keep the response useful for real travel planning.
"""

    response = llm.invoke([
        SystemMessage(content="You are a professional AI travel booking assistant."),
        HumanMessage(content=final_prompt)
    ])

    return {
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1
    }



graph = StateGraph(PlannerState)
graph.add_node("router_agent", router_agent)
graph.add_node("general_agent", general_agent)
graph.add_node("flight_agent", flight_agent)
graph.add_node("hotel_restaurant_agent", hotel_restaurant_agent)
graph.add_node("sightseeing_agent", sightseeing_agent)
graph.add_node("itinerary_agent", itinerary_agent)
graph.add_node("final_agent", final_agent)



graph.add_edge(START, "router_agent")
graph.add_conditional_edges(
    "router_agent",
    lambda state: state["route"],
    {
        "TRAVEL": "flight_agent",
        "GENERAL": "general_agent"
    }
)
graph.add_edge("general_agent", END)

graph.add_edge("flight_agent", "hotel_restaurant_agent")
graph.add_edge("hotel_restaurant_agent", "sightseeing_agent")
graph.add_edge("sightseeing_agent", "itinerary_agent")
graph.add_edge("itinerary_agent", "final_agent")
graph.add_edge("final_agent", END)


DATABASE_URL = get_database_url()

conn = psycopg.connect(
    DATABASE_URL,
    autocommit=True,
    row_factory=dict_row
)

checkpointer = PostgresSaver(conn)
checkpointer.setup()

travel_graph = graph.compile(checkpointer=checkpointer)



def run(user_input: str, thread_id: str | None = None):
    if not thread_id:
        thread_id = f"user_{uuid.uuid4().hex}"

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    result = travel_graph.invoke(
        {
            "messages": [
                HumanMessage(content=user_input)
            ],
            "user_query" : user_input,
            "sightseeing_results": "",
            "hotel_results": "",
            "food_results": "",
            "flight_results": "",
            "itinerary": "",
            "llm_calls": 0
        },
        config=config
    )

    final_answer = result["messages"][-1].content

    return {
    "thread_id": thread_id,
    "answer": final_answer,
    "route": result.get("route", ""),
    "flight_results": result.get("flight_results", ""),
    "hotel_results": result.get("hotel_results", ""),
    "food_results": result.get("food_results", ""),
    "sightseeing_results": result.get("sightseeing_results", ""),
    "itinerary": result.get("itinerary", ""),
    "llm_calls": result.get("llm_calls", 0),
}

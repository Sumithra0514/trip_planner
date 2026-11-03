# ✈️ AI Trip Planner

An AI-powered travel planning application built with **FastAPI, LangGraph, OpenAI, Tavily, AviationStack, and PostgreSQL**.

The application takes a user's travel request and uses an agentic LangGraph workflow to gather flight information, hotel recommendations, food suggestions, sightseeing recommendations, and generate a structured travel itinerary.

## Features

- **AI Trip Planning:** Generate travel plans from natural-language requests.
- **Travel Intent Routing:** Classifies requests as `TRAVEL` or `GENERAL`.
- **Flight Search:** Retrieves flight information using a AviationStack API
- **Hotel Search:** Uses Tavily to search for hotel recommendations across different budgets.
- **Food & Restaurant Search:** Uses Tavily to find restaurants, local food, and must-try dishes.
- **Sightseeing Recommendations:** Generates recommendations for must-see places.
- **Automated Itinerary Generation:** Combines information from multiple sources into a structured travel plan.
- **Agentic Workflow:** Uses LangGraph to orchestrate multiple specialized agents.
- **Conversation Persistence:** Uses LangGraph's PostgreSQL checkpointer to save workflow state and maintain execution history using thread IDs.

## Deployment

The application is deployed using **Render**.

- Frontend: HTML, CSS, JavaScript
- Backend: FastAPI
- Hosting platform: Render

**Demo URL:** https://trip-planner-1rxr.onrender.com

*Note: The application is currently suspended to manage hosting resources. It can be reactivated for a demonstration upon request.*

## 🛠️ Tech Stack

- **Frontend:** HTML, CSS, JavaScript
- **Backend:** FastAPI
- **AI Workflow:** LangGraph
- **LLM:** OpenAI
- **LLM Framework:** LangChain
- **Flight Search:** AviationStack API
- **Web Search:** Tavily API
- **Database:** PostgreSQL
- **Workflow Persistence:** LangGraph PostgreSQL Checkpointer
- **Language:** Python
- **Deployment:** Render
- **LLM Observability**: LangSmith (Tracing and Monitoring)

## How It Works

### 1. User Request

The user enters a travel request, for example:

"Plan a 5-day trip to Japan for two people."
The request is passed to the LangGraph workflow.

### 2. Router Agent

The router checks whether the request is travel-related.
- TRAVEL: Sends it to the travel planning workflow.
- GENERAL: Sends it to the general agent, which handles unrelated questions with a travel-only response.

### 3. Flight Agent

Searches for flight information using the flight search tool and saves the results.
The workflow then passes this information to the next agent.

### 4. Hotel & Restaurant Agent

This agent uses **Tavily** to search for:

- Hotel recommendations for different budgets.
- Restaurants.
- Local food.
- Must-try dishes.

### 5. Sightseeing Agent

The sightseeing agent uses the LLM to generate recommendations for must-see places based on the user's destination and travel request.

### 6. Itinerary Agent

Combines all the collected information and generates the final travel plan, including flights, hotels, food, sightseeing, daily itinerary, and estimated budget.

## Project Structure

```text
trip_planner/
│
├── tools/
│   ├── hotel_search.py
│   └── flight_search.py
│
├── index.html
│── backend.py
│── server.py
├── .gitignore
├── requirements.txt
└── README.md
```

## Disclaimer

Travel information such as flight schedules, prices, hotel availability, and restaurant information may change over time.
Users should verify important travel information directly with airlines, hotels, restaurants, and other service providers before making bookings.

# 🌍 Tourism Chatbot – Multi-Agent Travel Assistant

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-Web%20Framework-green?logo=flask)](https://flask.palletsprojects.com/)
[![Status](https://img.shields.io/badge/Status-Active-success)]()
[![GitHub stars](https://img.shields.io/github/stars/Ishashetty07/tourism-chatbot?style=social)](https://github.com/Ishashetty07/tourism-chatbot)

A tourism chatbot website built using *Python, Flask and a multi-agent architecture*.  
It helps users plan trips by providing:

- *Live weather* (temperature + rain probability)  
- *Top nearby tourist spots* (temples, beaches, waterfalls, parks, historic places, etc.)  
- Natural-language chat interface in the browser  

---

## 🧠 Architecture – Multi-Agent System

This project is designed as a simple multi-agent system:

| Agent           | Responsibility                                                                 |
|-----------------|---------------------------------------------------------------------------------|
| *Parent Agent* (Tourism Agent) | Reads user message, extracts the place, detects intent (weather / places / both), and orchestrates child agents. |
| *Child Agent 0 – Geocoding Agent* | Uses *Nominatim* (OpenStreetMap) to convert place name → latitude & longitude. |
| *Child Agent 1 – Weather Agent* | Uses *Open-Meteo API* to fetch current temperature and precipitation probability. |
| *Child Agent 2 – Places Agent* | Uses *Overpass API* to fetch up to 5 nearby tourism spots (temples, beaches, waterfalls, parks, viewpoints, historic places). |

All agents are implemented in app.py and coordinated by the parent tourism agent.

---

## 💬 Example Queries

You can chat with the bot using natural sentences, for example:

- I'm going to go to Bangalore, what is the temperature there?
- I'm going to go to Udupi, let's plan my trip.
- I'm going to go to Goa, what is the temperature there and what places can I visit?
- I'm going to go to Jog Falls, let's plan my trip.

The bot will:

- Detect whether you want *weather, **tourist places, or **both*  
- Call the appropriate agents  
- Reply in a friendly, readable format

---

## 🖥 Web UI

The frontend is a minimal but modern chat interface:

- Built with *HTML + CSS + Vanilla JavaScript*
- Dark theme, rounded chat bubbles, “typing…” indicator
- Messages displayed as User (🧑) and Bot (🤖)

Structure:

```text
tourism-chatbot/
│ app.py
├─ templates/
│   └─ index.html      # Chat UI
└─ static/
    └─ style.css       # Styling for the chat UI

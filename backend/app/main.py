from datetime import datetime, timedelta
from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import heapq
import itertools

app = FastAPI(title="RouteWise API", version="1.0.0",
              description="Journey planning demo using simulated transport data.")

# Demo-only CORS. Restrict this to your frontend URL before production use.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

STOPS = [
    {"id": "central", "name": "Central Station", "lat": 22.5726, "lon": 88.3639},
    {"id": "museum", "name": "Museum", "lat": 22.5702, "lon": 88.3510},
    {"id": "market", "name": "City Market", "lat": 22.5680, "lon": 88.3705},
    {"id": "river", "name": "Riverside", "lat": 22.5615, "lon": 88.3540},
    {"id": "university", "name": "University", "lat": 22.5760, "lon": 88.4170},
    {"id": "techpark", "name": "Tech Park", "lat": 22.5850, "lon": 88.4300},
    {"id": "airport", "name": "Airport", "lat": 22.6547, "lon": 88.4467},
    {"id": "hospital", "name": "City Hospital", "lat": 22.5790, "lon": 88.3900},
]

# Times are illustrative scheduled minutes from midnight. All data is simulated.
EDGES = [
    {"id":"e1","from":"central","to":"museum","mode":"Metro","minutes":8,"fare":12,"walk":0,"departures":[0,10,20,30,40,50]},
    {"id":"e2","from":"museum","to":"river","mode":"Bus","minutes":12,"fare":10,"walk":0,"departures":[0,15,30,45]},
    {"id":"e3","from":"central","to":"market","mode":"Bus","minutes":10,"fare":8,"walk":0,"departures":[0,12,24,36,48]},
    {"id":"e4","from":"market","to":"river","mode":"Metro","minutes":9,"fare":12,"walk":0,"departures":[0,10,20,30,40,50]},
    {"id":"e5","from":"river","to":"university","mode":"Bus","minutes":16,"fare":12,"walk":0,"departures":[0,20,40]},
    {"id":"e6","from":"market","to":"university","mode":"Metro","minutes":14,"fare":15,"walk":0,"departures":[0,15,30,45]},
    {"id":"e7","from":"university","to":"techpark","mode":"Bus","minutes":12,"fare":10,"walk":0,"departures":[0,15,30,45]},
    {"id":"e8","from":"central","to":"hospital","mode":"Bus","minutes":15,"fare":10,"walk":0,"departures":[0,15,30,45]},
    {"id":"e9","from":"hospital","to":"university","mode":"Metro","minutes":11,"fare":12,"walk":0,"departures":[0,10,20,30,40,50]},
    {"id":"e10","from":"techpark","to":"airport","mode":"Bus","minutes":25,"fare":20,"walk":0,"departures":[0,30]},
    {"id":"e11","from":"river","to":"market","mode":"Walk","minutes":13,"fare":0,"walk":900,"departures":list(range(0,60,5))},
    {"id":"e12","from":"museum","to":"central","mode":"Metro","minutes":8,"fare":12,"walk":0,"departures":[0,10,20,30,40,50]},
    {"id":"e13","from":"market","to":"central","mode":"Bus","minutes":10,"fare":8,"walk":0,"departures":[0,12,24,36,48]},
    {"id":"e14","from":"river","to":"museum","mode":"Bus","minutes":12,"fare":10,"walk":0,"departures":[0,15,30,45]},
    {"id":"e15","from":"university","to":"market","mode":"Metro","minutes":14,"fare":15,"walk":0,"departures":[0,15,30,45]},
    {"id":"e16","from":"university","to":"hospital","mode":"Metro","minutes":11,"fare":12,"walk":0,"departures":[0,10,20,30,40,50]},
    {"id":"e17","from":"techpark","to":"university","mode":"Bus","minutes":12,"fare":10,"walk":0,"departures":[0,15,30,45]},
    {"id":"e18","from":"airport","to":"techpark","mode":"Bus","minutes":25,"fare":20,"walk":0,"departures":[0,30]},
    {"id":"e19","from":"market","to":"techpark","mode":"Bus","minutes":25,"fare":18,"walk":0,"departures":[0,15,30,45]},
]

class PlanRequest(BaseModel):
    origin: str
    destination: str
    departure_time: str = "09:00"
    arrival_deadline: Optional[str] = None
    budget: float = Field(default=100, ge=0, le=10000)
    max_walking_m: int = Field(default=1500, ge=0, le=50000)
    preference: str = "balanced"
    disruptions: list[dict] = Field(default_factory=list)

class DisruptionRequest(BaseModel):
    kind: str = "cancel"
    edge_id: Optional[str] = None

def parse_time(value: str) -> int:
    try:
        h, m = map(int, value.split(":"))
        if not (0 <= h <= 23 and 0 <= m <= 59):
            raise ValueError()
        return h * 60 + m
    except Exception:
        raise ValueError("Time must use HH:MM, for example 09:00.")

def fmt_time(minutes: int) -> str:
    minutes = minutes % (24 * 60)
    return f"{minutes // 60:02d}:{minutes % 60:02d}"

def next_departure(edge, current_minute):
    departures = edge.get("departures", list(range(0,60,10)))
    base_hour = (current_minute // 60) * 60
    candidates = [base_hour + d for d in departures if base_hour + d >= current_minute]
    if candidates:
        return min(candidates)
    return base_hour + 60 + min(departures)

def get_edges(disruptions):
    by_id = {d.get("edge_id"): d for d in disruptions if d.get("edge_id")}
    result = []
    for original in EDGES:
        edge = dict(original)
        d = by_id.get(edge["id"])
        if d and d.get("kind") == "cancel":
            continue
        if d and d.get("kind") == "delay":
            edge["minutes"] += int(d.get("delay_minutes", 15))
        result.append(edge)
    return result

def find_paths(origin, destination, departure, disruptions, max_walking, max_budget, deadline):
    edges = get_edges(disruptions)
    graph = {}
    for e in edges:
        graph.setdefault(e["from"], []).append(e)
    # Dijkstra-like search over arrival time, keeping several simple alternatives.
    queue = []
    counter = itertools.count()
    heapq.heappush(queue, (departure, next(counter), origin, [], 0.0, 0, [], None))
    results = []
    expansions = 0
    while queue and len(results) < 12 and expansions < 12000:
        now, _, node, path, fare, walking, legs, previous_mode = heapq.heappop(queue)
        expansions += 1
        if node == destination and path:
            results.append({
                "id": "-".join(path),
                "arrival_minutes": now,
                "arrival_time": fmt_time(now),
                "duration_minutes": now - departure,
                "fare": round(fare, 2),
                "walking_m": walking,
                "transfers": max(0, sum(1 for i in range(1, len(legs)) if legs[i]["mode"] != legs[i-1]["mode"]) - 0),
                "stops": [STOPS_BY_ID[origin]["name"]] + [STOPS_BY_ID[leg["to"]]["name"] for leg in legs],
                "legs": legs,
            })
            continue
        if len(path) >= 6:
            continue
        for edge in graph.get(node, []):
            if edge["id"] in path or edge["to"] in [origin] + [x["to"] for x in legs]:
                continue
            new_fare = fare + edge["fare"]
            new_walk = walking + edge["walk"]
            if new_fare > max_budget or new_walk > max_walking:
                continue
            depart = next_departure(edge, now + (4 if previous_mode and previous_mode != edge["mode"] else 0))
            arrive = depart + edge["minutes"]
            if deadline is not None and arrive > deadline:
                continue
            leg = {
                "edge_id": edge["id"], "from": edge["from"], "to": edge["to"],
                "from_name": STOPS_BY_ID[edge["from"]]["name"],
                "to_name": STOPS_BY_ID[edge["to"]]["name"],
                "mode": edge["mode"], "depart_time": fmt_time(depart),
                "arrival_time": fmt_time(arrive), "minutes": edge["minutes"],
                "fare": edge["fare"], "walking_m": edge["walk"],
                "wait_minutes": max(0, depart - now)
            }
            heapq.heappush(queue, (arrive, next(counter), edge["to"], path + [edge["id"]],
                                   new_fare, new_walk, legs + [leg], edge["mode"]))
    # Remove duplicate stop sequences and sort stable
    unique = {}
    for r in results:
        key = tuple(r["stops"])
        if key not in unique or r["duration_minutes"] < unique[key]["duration_minutes"]:
            unique[key] = r
    return list(unique.values())

STOPS_BY_ID = {s["id"]: s for s in STOPS}

def score_route(route, preference):
    if preference == "fastest":
        return (route["duration_minutes"], route["fare"])
    if preference == "cheapest":
        return (route["fare"], route["duration_minutes"])
    return (route["duration_minutes"] + route["fare"] * 0.7 + route["transfers"] * 4, route["duration_minutes"])

@app.get("/")
def root():
    return {"name":"RouteWise API","status":"ok","data_mode":"simulated"}

@app.get("/api/stops")
def stops():
    return {"data_mode":"simulated","stops":STOPS}

@app.get("/api/disruptions")
def disruption_options():
    return {"options":[
        {"edge_id":"e7","kind":"cancel","label":"Cancel University → Tech Park bus"},
        {"edge_id":"e7","kind":"delay","delay_minutes":20,"label":"Delay University → Tech Park bus by 20 min"},
        {"edge_id":"e6","kind":"cancel","label":"Cancel Market → University metro"},
        {"edge_id":"e1","kind":"delay","delay_minutes":15,"label":"Delay Central → Museum metro by 15 min"},
    ]}

@app.post("/api/disruptions/random")
def random_disruption():
    # deterministic rotating demo choice, no external/live data
    return {"disruption":{"edge_id":"e7","kind":"cancel","label":"University → Tech Park bus cancelled (simulated)"}}

@app.post("/api/plan")
def plan(req: PlanRequest):
    if req.origin not in STOPS_BY_ID or req.destination not in STOPS_BY_ID:
        return {"routes":[],"message":"Choose a valid origin and destination."}
    if req.origin == req.destination:
        return {"routes":[],"message":"Origin and destination must be different."}
    try:
        departure = parse_time(req.departure_time)
        deadline = parse_time(req.arrival_deadline) if req.arrival_deadline else None
    except ValueError as e:
        return {"routes":[],"message":str(e)}
    routes = find_paths(req.origin, req.destination, departure, req.disruptions,
                        req.max_walking_m, req.budget, deadline)
    routes.sort(key=lambda r: score_route(r, req.preference))
    # Keep alternatives with differing tradeoffs where possible
    routes = routes[:5]
    for i, r in enumerate(routes):
        r["rank"] = i + 1
        r["recommendation"] = "Recommended" if i == 0 else "Alternative"
        r["explanation"] = (
            f"{r['duration_minutes']} minutes total, fare {r['fare']:.0f}, "
            f"{r['transfers']} mode changes and {r['walking_m']} m walking. "
            f"Ranked for your {req.preference} preference."
        )
    return {
        "data_mode":"simulated",
        "routes":routes,
        "message": "" if routes else "No route satisfies the current budget, walking limit, and arrival deadline. Try relaxing one constraint.",
        "summary":{"origin":STOPS_BY_ID[req.origin]["name"],"destination":STOPS_BY_ID[req.destination]["name"],
                   "departure_time":req.departure_time,"routes_found":len(routes)}
    }

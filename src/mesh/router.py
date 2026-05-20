import re
from typing import Any, NamedTuple

SERVICE_ENDPOINTS = {
    "mmdb": [
        ("store", "POST", "/store"),
        ("get_crystal", "GET", "/crystal/{crystal_id}"),
        ("search", "POST", "/search"),
        ("stats", "GET", "/stats"),
    ],
    "mdhg": [
        ("create_session", "POST", "/session"),
        ("add_node", "POST", "/add_node"),
        ("get_graph", "GET", "/graph/{session_id}"),
        ("traverse", "POST", "/traverse"),
    ],
    "snap": [
        ("gate369", "POST", "/gate369"),
        ("triad", "POST", "/triad"),
        ("stratify", "POST", "/stratify"),
        ("evaluate_lenses", "POST", "/evaluate_lenses"),
        ("taxonomy", "GET", "/taxonomy"),
    ],
    "tarpit": [
        ("create_atom", "POST", "/tarpit/create_atom"),
        ("bond", "POST", "/tarpit/bond"),
        ("atoms", "GET", "/tarpit/atoms"),
    ],
    "speedlight": [
        ("get", "GET", "/v1/cache/{key}"),
        ("put", "POST", "/v1/cache"),
    ],
    "manny": [
        ("run", "POST", "/run"),
        ("probe", "POST", "/probe"),
        ("verbalize", "GET", "/verbalize"),
    ],
}


class RoutingDecision(NamedTuple):
    service: str
    endpoint: str
    method: str
    path: str
    confidence: float
    explanation: str


INTENT_MAP = [
    (["store", "crystal", "save", "memory", "persist"], "mmdb", "store"),
    (["crystal", "retrieve", "get", "fetch", "load"], "mmdb", "get_crystal"),
    (["search", "find", "query", "proximity", "similar", "lookup"], "mmdb", "search"),
    (["stats", "statistics", "count", "summary"], "mmdb", "stats"),
    (["session", "explore", "traverse", "hierarchy", "graph", "hash"], "mdhg", "create_session"),
    (["node", "add", "insert", "append"], "mdhg", "add_node"),
    (["traverse", "navigate", "up", "down", "sibling"], "mdhg", "traverse"),
    (["gate369", "triad", "hexad", "ennead", "select", "choose", "pick"], "snap", "gate369"),
    (["stratify", "expand", "explode", "concept", "deepen"], "snap", "stratify"),
    (["lens", "evaluate", "polarity", "perspective"], "snap", "evaluate_lenses"),
    (["taxonomy", "family", "type", "registry", "classification"], "snap", "taxonomy"),
    (["atom", "create", "element", "charge"], "tarpit", "create_atom"),
    (["bond", "connect", "link", "join", "attach", "chemistry"], "tarpit", "bond"),
    (["cache", "speed", "receipt", "merkle", "content"], "speedlight", "put"),
    (["get", "retrieve", "fetch", "read"], "speedlight", "get"),
    (["brain", "run", "think", "reason", "process", "execute"], "manny", "run"),
    (["probe", "query", "ask", "question", "inspect"], "manny", "probe"),
    (["verbalize", "speak", "explain", "describe", "summarize"], "manny", "verbalize"),
]


class IntentRouter:
    def __init__(self):
        self._custom_routes: list[tuple[re.Pattern, str, str]] = []

    def add_route(self, pattern: str, service: str, endpoint: str):
        self._custom_routes.append((re.compile(pattern, re.I), service, endpoint))

    def route(self, intent: str) -> RoutingDecision | None:
        intent_lower = intent.lower()

        for pattern, svc, ep in self._custom_routes:
            if pattern.search(intent_lower):
                return RoutingDecision(svc, ep, *self._endpoint_info(svc, ep), 1.0, "custom route")

        for keywords, svc, ep in INTENT_MAP:
            matches = sum(1 for kw in keywords if kw in intent_lower)
            if matches:
                confidence = min(matches / max(len(keywords), 1) * 2, 1.0)
                return RoutingDecision(svc, ep, *self._endpoint_info(svc, ep), confidence, f"matched {matches} keyword(s)")

        return None

    def route_or_fallback(self, intent: str, default_service: str = "manny",
                          default_endpoint: str = "run") -> RoutingDecision:
        result = self.route(intent)
        if result is None:
            return RoutingDecision(default_service, default_endpoint, *self._endpoint_info(default_service, default_endpoint), 0.0, "fallback")
        return result

    def list_routes(self, service: str | None = None) -> list[dict[str, Any]]:
        routes = []
        for keywords, svc, ep in INTENT_MAP:
            if service and svc != service:
                continue
            routes.append({
                "service": svc,
                "endpoint": ep,
                "keywords": keywords,
            })
        return routes

    @staticmethod
    def _endpoint_info(service: str, endpoint: str) -> tuple[str, str]:
        for ep_name, method, path in SERVICE_ENDPOINTS.get(service, []):
            if ep_name == endpoint:
                return method, path
        return "POST", f"/{endpoint}"

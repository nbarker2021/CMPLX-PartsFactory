from typing import Any


class ServiceDependencyGraph:
    def __init__(self):
        self._nodes: dict[str, dict[str, Any]] = {}
        self._edges: dict[str, set[str]] = {}
        self._reverse: dict[str, set[str]] = {}

    def add_service(self, name: str, metadata: dict | None = None):
        if name not in self._nodes:
            self._nodes[name] = metadata or {}
            self._edges.setdefault(name, set())
            self._reverse.setdefault(name, set())

    def add_dependency(self, service: str, depends_on: str):
        self.add_service(service)
        self.add_service(depends_on)
        self._edges[service].add(depends_on)
        self._reverse[depends_on].add(service)

    def remove_service(self, name: str):
        self._nodes.pop(name, None)
        self._edges.pop(name, None)
        self._reverse.pop(name, None)
        for deps in self._edges.values():
            deps.discard(name)
        for deps in self._reverse.values():
            deps.discard(name)

    def dependencies(self, service: str) -> set[str]:
        return set(self._edges.get(service, set()))

    def dependents(self, service: str) -> set[str]:
        return set(self._reverse.get(service, set()))

    def has_cycle(self) -> bool:
        visited = set()
        recursion = set()

        def dfs(node: str) -> bool:
            visited.add(node)
            recursion.add(node)
            for dep in self._edges.get(node, set()):
                if dep not in visited:
                    if dfs(dep):
                        return True
                elif dep in recursion:
                    return True
            recursion.discard(node)
            return False

        for node in self._nodes:
            if node not in visited:
                if dfs(node):
                    return True
        return False

    def find_cycle(self) -> list[str] | None:
        visited = set()
        recursion = set()
        path: list[str] = []

        def dfs(node: str) -> bool:
            visited.add(node)
            recursion.add(node)
            path.append(node)
            for dep in self._edges.get(node, set()):
                if dep not in visited:
                    if dfs(dep):
                        return True
                elif dep in recursion:
                    cycle_start = path.index(dep)
                    cycle_path = path[cycle_start:] + [dep]
                    path.clear()
                    path.extend(cycle_path)
                    return True
            recursion.discard(node)
            path.pop()
            return False

        for node in self._nodes:
            if node not in visited:
                if dfs(node):
                    return list(path)
        return None

    def topological_sort(self) -> list[str]:
        visited = set()
        result: list[str] = []

        def dfs(node: str):
            visited.add(node)
            for dep in self._edges.get(node, set()):
                if dep not in visited:
                    dfs(dep)
            result.append(node)

        for node in self._nodes:
            if node not in visited:
                dfs(node)

        return result

    def execution_order(self, target: str) -> list[str]:
        visited = set()
        order: list[str] = []

        def dfs(node: str):
            if node in visited:
                return
            visited.add(node)
            for dep in self._edges.get(node, set()):
                dfs(dep)
            order.append(node)

        dfs(target)
        return order

    def impact_analysis(self, service: str) -> dict[str, Any]:
        affected = set()
        queue = [service]
        while queue:
            node = queue.pop(0)
            for dep in self._reverse.get(node, set()):
                if dep not in affected:
                    affected.add(dep)
                    queue.append(dep)

        return {
            "service": service,
            "dependencies": list(self.dependencies(service)),
            "dependents": list(self.dependents(service)),
            "all_affected_upstream": list(affected),
            "has_cycle": self.has_cycle(),
        }

    def to_dict(self) -> dict:
        return {
            "services": {k: v for k, v in self._nodes.items()},
            "dependencies": {k: sorted(v) for k, v in self._edges.items()},
            "dependents": {k: sorted(v) for k, v in self._reverse.items()},
        }

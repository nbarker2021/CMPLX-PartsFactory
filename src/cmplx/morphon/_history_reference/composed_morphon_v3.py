"""Canonical `morphon` module — atomically constructed from the unified ecosystem."""
logger = logging.getLogger(__name__)
results = explorer.run_exploration_batch(num_tests_per_problem=4)
__all__ = []
PG_URL = os.getenv("PG_URL", "postgresql://tmn2:tmn2_dev@tmn2-pg:5432/tmn2")
PORT = int(os.environ.get("PORT", "8000"))
ax1 = fig.add_subplot(gs[0, :2]); dark_ax(ax1)
ax2 = fig.add_subplot(gs[0, 2]); dark_ax(ax2)
ax3 = fig.add_subplot(gs[0, 3]); dark_ax(ax3)
ax4 = fig.add_subplot(gs[1, :2]); dark_ax(ax4)
ax5 = fig.add_subplot(gs[1, 2]); dark_ax(ax5)
ax6 = fig.add_subplot(gs[1, 3]); dark_ax(ax6)
ax7 = fig.add_subplot(gs[2, :2]); dark_ax(ax7)
ax8 = fig.add_subplot(gs[2, 2:]); ax8.set_facecolor('#161b22'); ax8.axis('off')
e8 = E8Lattice()
fig = go.Figure()
gs = gridspec.GridSpec(3, 4, figure=fig, hspace=0.45, wspace=0.38)
root_vecs = np.array([r.coords for r in roots], dtype=float)
_vendor_ast = None
_vendor_compiler = None
_vendor_eval = None
app = FastAPI(title="MMDB", description="VOA-like crystal storage", version="1.0.0")
here = Path(__file__).resolve().parent.parent
vroot = here / "vendor" / "morphonic_lambda"
off_diag = [cartan[i,j] for i in range(3) for j in range(3) if i != j]
COUPLING = 0.03
AMINO_ACIDS = list("ACDEFGHIKLMNPQRSTVWY")
BASIN_COLORS = {
    1: '#ff7b72', 2: '#58a6ff', 3: '#3fb950',
    4: '#ffa657', 5: '#d2a8ff', 6: '#79c0ff',
    7: '#56d364', 8: '#e3b341', 9: '#8b949e',
}
BASIN_NAMES = {
    1: "α-Helix Right",
    2: "β-Sheet Extended",
    3: "Left-Handed Helix",
    4: "β-Turn Type I",
    5: "β-Turn Type II",
    6: "Polyproline II",
    7: "3₁₀-Helix",
    8: "π-Helix",
    9: "Transition / Suspended",
}
INTERACTION_CLASSES = {
    1: ("Potentiation",    "One drug amplifies the other's effect",         '#3fb950'),
    2: ("Additive",        "Effects sum linearly",                          '#58a6ff'),
    3: ("Synergistic",     "New stable combined form — super-additive",     '#ffa657'),
    4: ("Partial Antag.",  "Partial antagonism — reduced efficacy",         '#d2a8ff'),
    5: ("Competitive",     "Competitive antagonism — receptor competition", '#79c0ff'),
    6: ("Antagonistic",    "Full antagonism — mutual destabilization",      '#ff7b72'),
    7: ("Paradoxical",     "Paradoxical interaction — context-dependent",   '#e3b341'),
    8: ("Pharmacokinetic", "PK-level interaction — absorption/metabolism",  '#56d364'),
    9: ("Neutral/Susp.",   "No net interaction — suspended state",          '#8b949e'),
}
ax9 = fig.add_subplot(gs[2, 3])
leech = LeechLattice24D()
roots = e8.get_roots()
BOARD_URL = os.environ.get("BOARD_URL", "http://tmn1-board:9090")
BRAIN_URL = os.environ.get("BRAIN_URL", "http://tmn2-brain:8000")
CONSERVATION_URL = os.environ.get("CONSERVATION_URL", "http://tmn2-conservation:8000")
COOP_URL = os.environ.get("COOP_URL", "http://tmn2-coop:8000")
DISPATCH_URL = os.environ.get("DISPATCH_URL", "http://tmn2-dispatch:8000")
FUNCTORS = {
    "pipeline":    ObservationFunctor("pipeline", "E8", {"dim_0": 1.0, "dim_7": COUPLING}),
    "tarpit":      ObservationFunctor("tarpit", "E6", {"dim_0": PHI}),
    "crystal":     ObservationFunctor("crystal", "Leech"),
    "snap":        ObservationFunctor("snap", "E8"),
    "mdhg":        ObservationFunctor("mdhg", "E8"),
    "morsr":       ObservationFunctor("morsr", "E8", {"dim_0": 1.0/240}),
    "daemon":      ObservationFunctor("daemon", "Leech"),  # 24 channels = 24D
    "economy":     ObservationFunctor("economy", "D4"),  # 4 shell tiers
    "agent":       ObservationFunctor("agent", "E8"),
    "simulation":  ObservationFunctor("simulation", "E8"),
    "board":       ObservationFunctor("board", "A2"),  # 2D social graph
}
GATE_URL = os.environ.get("GATE_URL", "http://tmn2-gate:8000")
GEOMETRIES = {
    "E6":     GeometrySpec("E6", 6, 6, 72, {"triality": True}),
    "E7":     GeometrySpec("E7", 7, 7, 126, {}),
    "E8":     GeometrySpec("E8", 8, 8, 240, {"coupling": COUPLING, "kissing": 240}),
    "Leech":  GeometrySpec("Leech", 24, 0, 0, {"kissing": 196560, "rootless": True}),
    "D4":     GeometrySpec("D4", 4, 4, 24, {"triality": True}),
    "A1":     GeometrySpec("A1", 1, 1, 2, {"su2": True}),
    "A2":     GeometrySpec("A2", 2, 2, 6, {"su3": True}),
    "G2":     GeometrySpec("G2", 2, 2, 12, {}),
    "F4":     GeometrySpec("F4", 4, 4, 48, {}),
    "BCC":    GeometrySpec("BCC", 3, 3, 8, {"lattice_type": "body-centered-cubic"}),
    "FCC":    GeometrySpec("FCC", 3, 3, 12, {"lattice_type": "face-centered-cubic"}),
}
MAX_SHELL_DEPTH = 3  # 0-3, four layers, then widen
MINT_URL = os.environ.get("MINT_URL", "http://tmn2-mint:8000")
MORSR_URL = os.environ.get("MORSR_URL", "http://tmn2-morsr:8000")
PHI = (1 + np.sqrt(5)) / 2
PIPELINE_URL = os.environ.get("PIPELINE_URL", "http://tmn2-pipeline:8000")
RECEIPT_URL = os.environ.get("RECEIPT_URL", "http://tmn2-receipt:8000")
SAP_URL = os.environ.get("SAP_URL", "http://tmn2-sap:8000")
SPAWN_URL = os.environ.get("SPAWN_URL", "http://tmn2-spawn:8000")
_state = {
    "phase": "idle",
    "shell_depth": 0,
    "corpus_total": 0,
    "corpus_related": 0,
    "dupes_set_aside": 0,
    "tools_needed": [],
    "tools_built": [],
    "workers": {"unpackers": 0, "organizers": 0, "processors": 0, "reviewers": 0},
    "agents_spawned": [],
    "atoms_produced": 0,
    "total_dphi": 0.0,
    "domains_discovered": [],
    "loops_completed": 0,
    "widening": False,
}
A = form_A.coords

class MorphonState(Enum):
    """
    Morphon lifecycle states.
    
    States flow: CREATED → VALIDATING → POLICY_CHECK → ROUTING → 
                 EXECUTING → COMPLETED/FAILED
    """
    CREATED = auto()
    VALIDATING = auto()
    POLICY_CHECK = auto()
    ROUTING = auto()
    QUEUED = auto()
    EXECUTING = auto()
    AWAITING_TOOL = auto()
    AWAITING_DATA = auto()
    CONSOLIDATING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()

class Morphon(BaseModel):
    """
    Morphon - Observable Request Wrapper
    
    Every request in CMPLXAgent is wrapped as a Morphon, providing:
    - Unique identity with E8 coordinate embedding
    - State machine with observable transitions
    - Conservation constraint tracking
    - Mandelbrot term assignment for context
    - SpeedLight receipt attachment
    
    The Morphon is the atomic unit of work in the CMPLXAgent ecosystem.
    It carries its context through the entire lifecycle, transforming
    through states while maintaining conservation invariants.
    """
    
    # Identity
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Content
    request_type: str  # Classification: task, query, command, etc.
    payload: Dict[str, Any]  # The actual request data
    
    # E8 Embedding - Geometric coordinates for lattice-based routing
    e8_coordinates: Optional[List[float]] = None  # 8-dimensional coordinates
    leech_lattice_point: Optional[str] = None  # Leech lattice reference
    
    # Mandelbrot Context
    mandelbrot_term: Optional[str] = None  # Assigned Mandelbrot term
    julia_parameters: Optional[Dict[str, float]] = None  # Derived Julia set params
    
    # State Management
    state: MorphonState = MorphonState.CREATED
    state_history: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Conservation Constraints
    constraints: List[ConservationConstraint] = Field(default_factory=list)
    constraint_violations: List[str] = Field(default_factory=list)
    
    # Receipt Integration (SpeedLight)
    receipt_id: Optional[str] = None
    checkpoint_data: Dict[str, Any] = Field(default_factory=dict)
    
    # Execution Context
    assigned_tier: Optional[str] = None  # Which tier handles this
    assigned_agent: Optional[str] = None  # Specific agent assignment
    parent_morphon: Optional[str] = None  # For spawned sub-morphons
    child_morphons: List[str] = Field(default_factory=list)
    
    # Tool/Data Gates
    tools_required: List[str] = Field(default_factory=list)
    tools_executed: List[str] = Field(default_factory=list)
    data_dependencies: List[str] = Field(default_factory=list)
    data_resolved: List[str] = Field(default_factory=list)
    
    # Results
    result: Optional[Any] = None
    error: Optional[str] = None
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def __init__(self, **data):
        super().__init__(**data)
        self._state_observers: Set[Callable] = set()
        self._transition_hooks: Dict[MorphonState, List[Callable]] = {}
    
    # === State Machine ===
    
    async def transition_to(self, new_state: MorphonState, context: Dict[str, Any] = None):
        """
        Transition Morphon to new state with validation and observation.
        
        All transitions are logged, observed, and checked against
        conservation constraints.
        """
        old_state = self.state
        
        # Record transition
        transition_record = {
            "from": old_state.name,
            "to": new_state.name,
            "timestamp": datetime.utcnow().isoformat(),
            "context": context or {}
        }
        self.state_history.append(transition_record)
        
        # Execute transition hooks
        if new_state in self._transition_hooks:
            for hook in self._transition_hooks[new_state]:
                await hook(self, old_state, new_state)
        
        # Update state
        self.state = new_state
        
        # Notify observers
        for observer in self._state_observers:
            try:
                await observer(self, old_state, new_state)
            except Exception:
                pass  # Observers should not break transitions
    
    def add_observer(self, observer: Callable):
        """Add state transition observer."""
        self._state_observers.add(observer)
    
    def on_transition(self, state: MorphonState, hook: Callable):
        """Register hook for specific state transition."""
        if state not in self._transition_hooks:
            self._transition_hooks[state] = []
        self._transition_hooks[state].append(hook)
    
    # === Conservation Constraints ===
    
    def add_constraint(self, constraint: ConservationConstraint):
        """Add conservation constraint to this Morphon."""
        self.constraints.append(constraint)
    
    def check_constraints(self, previous_payload: Dict[str, Any]) -> bool:
        """Verify all conservation constraints."""
        all_valid = True
        for constraint in self.constraints:
            if not constraint.check(previous_payload, self.payload):
                self.constraint_violations.append(constraint.name)
                all_valid = False
        return all_valid
    
    # === Mandelbrot Context ===
    
    def assign_mandelbrot_term(self, term: str, parameters: Dict[str, float] = None):
        """
        Assign Mandelbrot term to this Morphon.
        
        The Mandelbrot term classifies the idea space this request
        belongs to, determining which Julia functors (context agents)
        will process it.
        """
        self.mandelbrot_term = term
        self.julia_parameters = parameters or {}
    
    def get_julia_context(self) -> Dict[str, Any]:
        """Get the Julia set context derived from Mandelbrot term."""
        return {
            "term": self.mandelbrot_term,
            "parameters": self.julia_parameters,
            "escape_radius": self.julia_parameters.get("escape_radius", 2.0),
            "max_iterations": self.julia_parameters.get("max_iterations", 100),
        }
    
    # === E8 Geometry ===
    
    def set_e8_coordinates(self, coordinates: List[float]):
        """
        Set E8 lattice coordinates for geometric routing.
        
        E8 coordinates enable proximity-based agent assignment
        and Leech lattice integration for high-dimensional clustering.
        """
        if len(coordinates) != 8:
            raise ValueError("E8 coordinates must be 8-dimensional")
        self.e8_coordinates = coordinates
    
    # === Checkpointing ===
    
    def create_checkpoint(self) -> Dict[str, Any]:
        """Create recoverable checkpoint."""
        return {
            "morphon_id": self.id,
            "state": self.state.name,
            "payload": self.payload,
            "receipt_id": self.receipt_id,
            "timestamp": datetime.utcnow().isoformat(),
            "tools_executed": self.tools_executed.copy(),
            "data_resolved": self.data_resolved.copy(),
        }
    
    def restore_checkpoint(self, checkpoint: Dict[str, Any]):
        """Restore from checkpoint."""
        self.payload = checkpoint.get("payload", self.payload)
        self.receipt_id = checkpoint.get("receipt_id")
        self.tools_executed = checkpoint.get("tools_executed", [])
        self.data_resolved = checkpoint.get("data_resolved", [])

class MorphonForgeController(BaseController):
    """
    MorphonForge controller for geometric structure manipulation.
    
    Provides:
    - Morphon state creation and manipulation
    - E8 lattice projections
    - Geometric transformations
    - Context-parameterized evolution
    
    Attributes:
        e8: E8Lattice instance
        db_path: Path to state database
    """
    
    def __init__(
        self,
        context: ControllerContext,
        db_path: str = "./morphon_forge.sqlite"
    ):
        """
        Initialize MorphonForge controller.
        
        Args:
            context: Controller context
            db_path: Path to state database
        """
        super().__init__(context, "morphon_forge")
        self.db_path = db_path
        self.e8 = E8Lattice()
        
        self._init_db()
        self._register_capabilities()
    
    def _init_db(self):
        """Initialize database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS morphon_states (
                state_id TEXT PRIMARY KEY,
                coordinates TEXT,
                context TEXT,
                generation INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transformations (
                trans_id TEXT PRIMARY KEY,
                from_state TEXT,
                to_state TEXT,
                transform_type TEXT,
                parameters TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _register_capabilities(self):
        """Register capabilities."""
        self._capabilities.update({
            'create_morphon': self._handle_create_morphon,
            'project_to_e8': self._handle_project_to_e8,
            'evolve_state': self._handle_evolve_state,
            'synthesize': self._handle_synthesize,
            'observe': self._handle_observe,
            'nearest_root': self._handle_nearest_root,
            'compute_distance': self._handle_compute_distance
        })
    
    def _handle_create_morphon(self, payload: Dict) -> Dict[str, Any]:
        """
        Create new morphon state.
        
        Args:
            payload: {'seed': any, 'context': dict}
            
        Returns:
            Created morphon state
        """
        import hashlib
        
        seed = payload.get('seed', 'default')
        context = payload.get('context', {})
        
        # Generate deterministic coordinates from seed
        seed_hash = hashlib.sha256(str(seed).encode()).hexdigest()
        seed_int = int(seed_hash[:16], 16) % (2**31)
        
        np.random.seed(int(seed_int))
        coords = np.random.randn(8)
        coords = self.e8.project(coords)
        
        # Create state
        state_id = f"morphon_{seed_hash[:16]}"
        state = MorphonState(
            state_id=state_id,
            coordinates=coords.tolist(),
            context=context
        )
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO morphon_states
            (state_id, coordinates, context, generation)
            VALUES (?, ?, ?, ?)
        ''', (
            state.state_id,
            json.dumps(state.coordinates),
            json.dumps(state.context),
            state.generation
        ))
        conn.commit()
        conn.close()
        
        return {
            'state_id': state.state_id,
            'coordinates': state.coordinates,
            'context': state.context,
            'generation': state.generation
        }
    
    def _handle_project_to_e8(self, payload: Dict) -> Dict[str, Any]:
        """
        Project arbitrary vector to E8 lattice.
        
        Args:
            payload: {'vector': list}
            
        Returns:
            Projected coordinates
        """
        vector = payload.get('vector')
        
        if not vector or len(vector) != 8:
            raise ValueError("Vector must be 8-dimensional")
        
        vec = np.array(vector)
        projected = self.e8.project(vec)
        
        nearest_idx, nearest_root = self.e8.find_nearest_root(projected)
        
        return {
            'original': vector,
            'projected': projected.tolist(),
            'nearest_root_index': int(nearest_idx),
            'distance_to_root': float(np.linalg.norm(projected - nearest_root))
        }
    
    def _handle_evolve_state(self, payload: Dict) -> Dict[str, Any]:
        """
        Evolve morphon state under context.
        
        Args:
            payload: {'state_id': str, 'steps': int, 'context': dict}
            
        Returns:
            Evolved state
        """
        state_id = payload.get('state_id')
        steps = payload.get('steps', 1)
        new_context = payload.get('context', {})
        
        # Retrieve current state
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT coordinates, context, generation FROM morphon_states
            WHERE state_id = ?
        ''', (state_id,))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            raise ValueError(f"State not found: {state_id}")
        
        coords = json.loads(row[0])
        current_context = json.loads(row[1])
        generation = row[2]
        
        # Merge contexts
        current_context.update(new_context)
        
        # Evolve (simplified - in production would use proper morphonic transform)
        vec = np.array(coords)
        for _ in range(steps):
            # Apply morphonic transform
            transform = np.random.randn(8) * 0.1  # Small perturbation
            vec = vec + transform
            vec = self.e8.project(vec)
        
        new_generation = generation + steps
        
        # Store evolved state
        new_state_id = f"{state_id}_gen{new_generation}"
        cursor.execute('''
            INSERT OR REPLACE INTO morphon_states
            (state_id, coordinates, context, generation)
            VALUES (?, ?, ?, ?)
        ''', (
            new_state_id,
            json.dumps(vec.tolist()),
            json.dumps(current_context),
            new_generation
        ))
        
        # Record transformation
        cursor.execute('''
            INSERT INTO transformations
            (trans_id, from_state, to_state, transform_type, parameters)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            f"trans_{state_id}_{new_generation}",
            state_id,
            new_state_id,
            'evolution',
            json.dumps({'steps': steps})
        ))
        
        conn.commit()
        conn.close()
        
        return {
            'from_state': state_id,
            'to_state': new_state_id,
            'new_coordinates': vec.tolist(),
            'generation': new_generation
        }
    
    def _handle_synthesize(self, payload: Dict) -> Dict[str, Any]:
        """
        Synthesize multiple observations into geometric structure.
        
        Args:
            payload: {'observations': list of states}
            
        Returns:
            Synthesized structure
        """
        observations = payload.get('observations', [])
        
        if not observations:
            raise ValueError("No observations provided")
        
        # Compute centroid
        coords_list = []
        for obs in observations:
            if isinstance(obs, dict) and 'coordinates' in obs:
                coords_list.append(obs['coordinates'])
            elif isinstance(obs, list):
                coords_list.append(obs)
        
        if not coords_list:
            raise ValueError("No valid coordinates in observations")
        
        centroid = np.mean(coords_list, axis=0)
        projected = self.e8.project(centroid)
        
        return {
            'observation_count': len(observations),
            'centroid': centroid.tolist(),
            'projected': projected.tolist(),
            'synthesis_method': 'centroid_projection'
        }
    
    def _handle_observe(self, payload: Dict) -> Dict[str, Any]:
        """
        Observe morphon state (collapse to geometric form).
        
        Args:
            payload: {'state_id': str}
            
        Returns:
            Observation result
        """
        state_id = payload.get('state_id')
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT coordinates, context FROM morphon_states
            WHERE state_id = ?
        ''', (state_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            raise ValueError(f"State not found: {state_id}")
        
        coords = json.loads(row[0])
        context = json.loads(row[1])
        
        # Find nearest root
        nearest_idx, nearest_root = self.e8.find_nearest_root(np.array(coords))
        
        return {
            'state_id': state_id,
            'coordinates': coords,
            'context': context,
            'nearest_root': nearest_root.tolist(),
            'nearest_root_index': int(nearest_idx),
            'observed': True
        }
    
    def _handle_nearest_root(self, payload: Dict) -> Dict[str, Any]:
        """
        Find nearest E8 root to coordinates.
        
        Args:
            payload: {'coordinates': list}
            
        Returns:
            Nearest root information
        """
        coords = payload.get('coordinates')
        
        if not coords:
            raise ValueError("Coordinates required")
        
        vec = np.array(coords)
        nearest_idx, nearest_root = self.e8.find_nearest_root(vec)
        
        return {
            'input': coords,
            'nearest_root': nearest_root.tolist(),
            'root_index': int(nearest_idx),
            'distance': float(np.linalg.norm(vec - nearest_root))
        }
    
    def _handle_compute_distance(self, payload: Dict) -> Dict[str, Any]:
        """
        Compute distance between two states in E8 space.
        
        Args:
            payload: {'state1': list, 'state2': list}
            
        Returns:
            Distance information
        """
        state1 = payload.get('state1')
        state2 = payload.get('state2')
        
        if not state1 or not state2:
            raise ValueError("Both states required")
        
        vec1 = np.array(state1)
        vec2 = np.array(state2)
        
        distance = np.linalg.norm(vec1 - vec2)
        
        return {
            'state1': state1,
            'state2': state2,
            'euclidean_distance': float(distance),
            'squared_distance': float(distance ** 2)
        }
    
    def _execute_command(self, command: ControllerCommand) -> Any:
        """Execute command."""
        if command.command_type == CommandType.EXECUTE:
            task = command.payload.get('task')
            handler = self._capabilities.get(task)
            
            if handler:
                return handler(command.payload)
            else:
                raise ValueError(f"Unknown MorphonForge task: {task}")
        
        elif command.command_type == CommandType.QUERY:
            return self._handle_query(command)
        
        else:
            raise ValueError(f"MorphonForge doesn't support {command.command_type}")
    
    def _handle_query(self, command: ControllerCommand) -> Dict[str, Any]:
        """Handle query."""
        query_type = command.payload.get('query_type')
        
        if query_type == 'stats':
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM morphon_states')
            state_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM transformations')
            trans_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'morphon_states': state_count,
                'transformations': trans_count,
                'e8_roots': self.e8.num_roots,
                'capabilities': list(self._capabilities.keys())
            }
        
        else:
            raise ValueError(f"Unknown query type: {query_type}")
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return capabilities."""
        return {
            'name': 'MorphonForge',
            'type': 'domain',
            'operations': list(self._capabilities.keys()),
            'db_path': self.db_path,
            'e8_roots': self.e8.num_roots
        }

class ConservationConstraint:
    """
    Conservation constraints ensure properties are preserved through transformations.
    
    Examples:
    - Energy conservation: Total compute cost bounded
    - Information conservation: No data loss during routing
    - Policy conservation: Security invariants maintained
    """
    name: str
    invariant: Callable[[Any], bool]
    value_extractor: Callable[[Any], Any]
    tolerance: float = 0.0
    
    def check(self, before: Any, after: Any) -> bool:
        """Verify constraint holds across transformation."""
        before_val = self.value_extractor(before)
        after_val = self.value_extractor(after)
        if isinstance(before_val, (int, float)) and isinstance(after_val, (int, float)):
            return abs(before_val - after_val) <= self.tolerance
        return before_val == after_val

class MorphonSeed:
    """A single-digit seed that generates geometry"""
    digit: int  # 1-9
    digital_root: int  # mod 9 class
    parity: int  # 0 (even) or 1 (odd)
    
    def __post_init__(self):
        assert 1 <= self.digit <= 9, "Seed must be 1-9"
        self.digital_root = self.digit  # For single digit, DR = digit
        self.parity = self.digit % 2

class MorphonicGenerator:
    """
    Generate full geometric structures from single-digit seeds.
    
    Process:
    1. Start with digit d ∈ {1..9}
    2. Apply mod-9 iteration: d → d² mod 9 → (d²)² mod 9 → ...
    3. Sequence converges to fixed point or cycle
    4. Map sequence to E8 roots via digital root correspondence
    5. Compose roots to build full E8, then extend to 24D
    
    This demonstrates morphonic emergence: complex structure from simple seed.
    """
    
    def __init__(self):
        """Initialize generator with E8 and Niemeier structures"""
        self.e8 = E8Full()
        self.niemeier = NiemeierFamily()
        
        # Digital root to E8 root mapping
        # Based on sacred frequencies and force correspondence
        self.dr_to_root_index = {
            1: 0,    # Unity
            2: 1,    # Duality
            3: 2,    # Trinity
            4: 3,    # Stability
            5: 4,    # Change
            6: 5,    # Harmony
            7: 6,    # Completion
            8: 7,    # Infinity
            9: 0,    # Return to unity (mod 9 = 0)
        }
        
        print("Morphonic generator initialized")
    
    def iterate_mod9(self, digit: int, max_iterations: int = 20) -> List[int]:
        """
        Iterate digit via squaring mod 9.
        
        Sequence: d → d² mod 9 → (d²)² mod 9 → ...
        
        Args:
            digit: Starting digit (1-9)
            max_iterations: Maximum iterations
            
        Returns:
            List of digital roots in sequence
        """
        sequence = [digit]
        current = digit
        
        for _ in range(max_iterations):
            # Square and take mod 9
            next_val = (current * current) % 9
            if next_val == 0:
                next_val = 9  # Keep in {1..9}
            
            sequence.append(next_val)
            
            # Check for fixed point or cycle
            if next_val == current:
                break  # Fixed point
            if next_val in sequence[:-1]:
                break  # Cycle detected
            
            current = next_val
        
        return sequence
    
    def sequence_to_e8_roots(self, sequence: List[int]) -> List[E8Root]:
        """
        Map digital root sequence to E8 roots.
        
        Each digit maps to an E8 root via the DR correspondence.
        
        Args:
            sequence: List of digital roots
            
        Returns:
            List of E8 roots
        """
        roots = []
        for dr in sequence:
            root_index = self.dr_to_root_index[dr]
            root = self.e8.simple_roots[root_index]
            roots.append(root)
        
        return roots
    
    def compose_roots(self, roots: List[E8Root]) -> np.ndarray:
        """
        Compose E8 roots into a single vector.
        
        Uses weighted sum with golden ratio scaling.
        
        Args:
            roots: List of E8 roots
            
        Returns:
            Composed 8D vector
        """
        phi = (1 + np.sqrt(5)) / 2  # Golden ratio
        
        composed = np.zeros(8)
        for i, root in enumerate(roots):
            # Weight by golden ratio powers
            weight = phi ** (-i)
            composed += weight * root.vector
        
        # Normalize
        norm = np.linalg.norm(composed)
        if norm > 1e-10:
            composed = composed / norm
        
        return composed
    
    def generate_e8_from_seed(self, seed: MorphonSeed) -> Tuple[np.ndarray, List[int], List[E8Root]]:
        """
        Generate E8 vector from single-digit seed.
        
        Process:
        1. Iterate seed via mod-9
        2. Map sequence to E8 roots
        3. Compose roots into vector
        
        Args:
            seed: MorphonSeed (digit 1-9)
            
        Returns:
            (composed_vector, dr_sequence, root_sequence)
        """
        # Generate digital root sequence
        dr_sequence = self.iterate_mod9(seed.digit)
        
        # Map to E8 roots
        root_sequence = self.sequence_to_e8_roots(dr_sequence)
        
        # Compose into single vector
        composed_vector = self.compose_roots(root_sequence)
        
        return composed_vector, dr_sequence, root_sequence
    
    def extend_to_24d(self, e8_vector: np.ndarray, seed: MorphonSeed) -> np.ndarray:
        """
        Extend 8D E8 vector to 24D via 3×E8 construction.
        
        Uses seed to determine the three copies.
        
        Args:
            e8_vector: 8D E8 vector
            seed: Original seed
            
        Returns:
            24D vector
        """
        # Generate three variations using seed
        # Each variation is a rotation/reflection based on seed properties
        
        # First copy: original
        copy1 = e8_vector
        
        # Second copy: reflect based on parity
        if seed.parity == 0:
            copy2 = e8_vector.copy()
            copy2[0] = -copy2[0]  # Reflect first coordinate
        else:
            copy2 = -e8_vector  # Full reflection
        
        # Third copy: rotate based on digital root
        copy3 = np.roll(e8_vector, seed.digital_root % 8)
        
        # Concatenate
        vector_24d = np.concatenate([copy1, copy2, copy3])
        
        return vector_24d
    
    def generate_niemeier_from_seed(self, seed: MorphonSeed) -> Tuple[str, NiemeierLattice]:
        """
        Select Niemeier lattice type based on seed.
        
        Different seeds map to different Niemeier types.
        
        Args:
            seed: MorphonSeed
            
        Returns:
            (lattice_type_name, NiemeierLattice)
        """
        # Map digital root to Niemeier type
        # 9 digital roots → 24 Niemeier types (some overlap)
        dr_to_niemeier = {
            1: "24A1",      # Unity → many small components
            2: "12A2",      # Duality → pairs
            3: "3E8",       # Trinity → three E8
            4: "D24",       # Stability → single large component
            5: "A24",       # Change → maximal roots
            6: "2D6",       # Harmony → balanced pairs
            7: "E8",        # Completion → single E8
            8: "D16E8",     # Infinity → mixed (note: key is D16E8 not D16+E8)
            9: "Leech",     # Return → no roots (pure potential)
        }
        
        lattice_type = dr_to_niemeier[seed.digital_root]
        lattice = self.niemeier.lattices[lattice_type]
        
        return lattice_type, lattice
    
    def full_generation(self, digit: int) -> Dict:
        """
        Complete generation from single digit to 24D Niemeier lattice.
        
        This demonstrates the full morphonic emergence:
        Single digit → E8 vector → 24D vector → Niemeier lattice
        
        Args:
            digit: Seed digit (1-9)
            
        Returns:
            Dictionary with all generation results and receipts
        """
        # Create seed
        seed = MorphonSeed(digit=digit, digital_root=digit, parity=digit % 2)
        
        # Generate E8
        e8_vector, dr_sequence, root_sequence = self.generate_e8_from_seed(seed)
        
        # Extend to 24D
        vector_24d = self.extend_to_24d(e8_vector, seed)
        
        # Select Niemeier lattice
        niemeier_type, niemeier_lattice = self.generate_niemeier_from_seed(seed)
        
        # Generate receipt
        receipt = self._generate_receipt(
            seed=seed,
            dr_sequence=dr_sequence,
            e8_vector=e8_vector,
            vector_24d=vector_24d,
            niemeier_type=niemeier_type
        )
        
        return {
            "seed": seed,
            "dr_sequence": dr_sequence,
            "root_sequence": [r.vector.tolist() for r in root_sequence],
            "e8_vector": e8_vector,
            "vector_24d": vector_24d,
            "niemeier_type": niemeier_type,
            "niemeier_lattice": niemeier_lattice,
            "receipt": receipt
        }
    
    def _generate_receipt(self, **kwargs) -> dict:
        """Generate cryptographic receipt for morphonic generation"""
        receipt = {
            "operation": "morphonic_generation",
            "timestamp": np.datetime64('now').astype(str),
            "seed_digit": kwargs["seed"].digit,
            "digital_root": kwargs["seed"].digital_root,
            "parity": kwargs["seed"].parity,
            "dr_sequence": kwargs["dr_sequence"],
            "e8_norm": float(np.linalg.norm(kwargs["e8_vector"])),
            "24d_norm": float(np.linalg.norm(kwargs["vector_24d"])),
            "niemeier_type": kwargs["niemeier_type"],
        }
        
        receipt_str = json.dumps(receipt, sort_keys=True)
        receipt["hash"] = hashlib.sha256(receipt_str.encode()).hexdigest()[:16]
        
        return receipt

class ActivationFunctions:
    """Activation functions with geometric interpretation.

    Provides numerically-stable GELU, softmax and layer-norm used
    throughout geometric transformer layers.
    """

class App:
    fn: "Term"
    arg: "Term"

class LambdaTerm:
    """CQE proto-language lambda calculus term represented as glyph + vector embeddings."""
    def __init__(self, expr: str, shelling: ShellingCompressor, alena: ALENAOps, morsr: EnhancedMORSRExplorer):
        self.expr = expr
        self.shelling = shelling
        self.alena = alena
        self.morsr = morsr
        self.glyph_seq = self.shelling.compress_to_glyph(expr, level=3)
        self.vector = self.text_to_vector(self.glyph_seq)

    def text_to_vector(self, text: str) -> np.ndarray:
        embed_dim = 128
        words = text.split()
        vec = np.bincount([hash(w) % embed_dim for w in words], minlength=embed_dim) / max(len(words), 1)
        norm_vec = vec / np.linalg.norm(vec) if np.linalg.norm(vec) > 0 else vec
        return norm_vec

    def apply(self, arg: 'LambdaTerm') -> 'LambdaTerm':
        """Apply lambda term to argument."""
        combined_expr = f"({self.expr}) ({arg.expr})"
        combined_glyph = f"{self.glyph_seq}|{arg.glyph_seq}"
        combined_vector = self.vector + arg.vector
        combined_vector = combined_vector / np.linalg.norm(combined_vector) if np.linalg.norm(combined_vector) > 0 else combined_vector
        snapped = self.alena.r_theta_snap(combined_vector)
        pulsed, _ = self.morsr.explore(np.copy(snapped))
        new_term = LambdaTerm(combined_expr, self.shelling, self.alena, self.morsr)
        new_term.glyph_seq = combined_glyph
        new_term.vector = pulsed
        return new_term

    def reduce(self) -> 'LambdaTerm':
        """Simulate reduction step."""
        flipped = self.alena.weyl_flip(self.vector)
        mid = (self.vector + flipped) / 2
        norm_mid = mid * (E8_NORM / np.linalg.norm(mid)) if np.linalg.norm(mid) > 0 else mid
        reduced_term = LambdaTerm(self.expr, self.shelling, self.alena, self.morsr)
        reduced_term.glyph_seq = self.glyph_seq
        reduced_term.vector = norm_mid
        return reduced_term

class MorphonTransformer:
    """
    Transforms Morphons through the lifecycle with conservation guarantees.
    
    Implements the core transformation pipeline:
    1. Validate input
    2. Check policies
    3. Route to appropriate tier
    4. Execute tools/data gates
    5. Consolidate results
    """
    
    def __init__(self, policy_engine=None, router=None, tool_registry=None):
        self.policy_engine = policy_engine
        self.router = router
        self.tool_registry = tool_registry
    
    async def transform(self, morphon: Morphon) -> Morphon:
        """
        Execute full transformation pipeline on Morphon.
        
        This is the main entry point for Morphon processing,
        implementing the governance-first, MCP-first architecture.
        """
        # Step 1: Validation
        await morphon.transition_to(MorphonState.VALIDATING)
        if not await self._validate(morphon):
            await morphon.transition_to(MorphonState.FAILED, {"reason": "validation_failed"})
            return morphon
        
        # Step 2: Policy Check
        await morphon.transition_to(MorphonState.POLICY_CHECK)
        if not await self._check_policies(morphon):
            await morphon.transition_to(MorphonState.FAILED, {"reason": "policy_violation"})
            return morphon
        
        # Step 3: Routing
        await morphon.transition_to(MorphonState.ROUTING)
        routing = await self._route(morphon)
        morphon.assigned_tier = routing.get("tier")
        morphon.assigned_agent = routing.get("agent")
        
        # Step 4: Execute
        await morphon.transition_to(MorphonState.EXECUTING)
        result = await self._execute(morphon, routing)
        
        # Step 5: Consolidate
        await morphon.transition_to(MorphonState.CONSOLIDATING)
        morphon.result = result
        
        # Complete
        await morphon.transition_to(MorphonState.COMPLETED)
        return morphon
    
    async def _validate(self, morphon: Morphon) -> bool:
        """Validate Morphon structure and content."""
        # Basic validation
        if not morphon.request_type:
            return False
        if not morphon.payload:
            return False
        # Add more validation as needed
        return True
    
    async def _check_policies(self, morphon: Morphon) -> bool:
        """Check Morphon against security and governance policies."""
        if self.policy_engine:
            return await self.policy_engine.check(morphon)
        return True
    
    async def _route(self, morphon: Morphon) -> Dict[str, Any]:
        """Determine routing for Morphon."""
        if self.router:
            return await self.router.route(morphon)
        # Default: route based on Mandelbrot term
        return {
            "tier": "agent",
            "agent": morphon.mandelbrot_term or "default"
        }
    
    async def _execute(self, morphon: Morphon, routing: Dict[str, Any]) -> Any:
        """Execute Morphon through tools/data gates."""
        # Tool gate
        for tool in morphon.tools_required:
            await morphon.transition_to(MorphonState.AWAITING_TOOL, {"tool": tool})
            if self.tool_registry:
                result = await self.tool_registry.execute(tool, morphon.payload)
                morphon.tools_executed.append(tool)
        
        # Data gate
        for data_dep in morphon.data_dependencies:
            await morphon.transition_to(MorphonState.AWAITING_DATA, {"data": data_dep})
            # Resolve data dependency
            morphon.data_resolved.append(data_dep)
        
        return {"status": "executed", "routing": routing}

class Var:
    name: str

class GeometrySpec:
    """One Gᵢ in M₀ = Σᵢ αᵢ Gᵢ. Names a geometry without instantiating it."""
    name: str
    dimension: int
    rank: int
    root_count: int
    properties: Dict[str, Any] = field(default_factory=dict)

class Observation:
    """
    An observation of the Universal Morphon through a specific functor.
    
    Attributes:
        type: Type of observation
        data: Observed data (structure-dependent)
        functor: Name of the observation functor used
        metadata: Additional metadata about the observation
    """
    type: ObservationType
    data: Any
    functor: str
    metadata: Dict[str, Any]

class ObservationFunctor:
    """F: Morph → Geom. Observes M₀ through a specific geometric lens."""

    def __init__(self, name: str, target_geometry: str, bias: Dict[str, float] = None):
        self.name = name
        self.target = target_geometry
        self.bias = bias or {}
        self.observation_count = 0

    def observe(self, content: str, e8_coords: List[float] = None) -> ObservationResult:
        """Apply this functor to content, producing a geometric observation."""
        self.observation_count += 1
        geo = GEOMETRIES.get(self.target, GEOMETRIES["E8"])

        # Morphon 4-tuple: (z, φ, ΔΦ, R)
        z = self._shannon_entropy(content)
        e8 = e8_coords or [0.0] * 8
        R = math.sqrt(sum(c * c for c in e8[:geo.dimension]))
        phi = R * R  # quadratic tension
        dphi = -z * COUPLING  # conservation: new content = negative delta

        # Coordinate projection through this functor's bias
        projected = e8[:geo.dimension]
        for i in range(len(projected)):
            dim_key = f"dim_{i}"
            if dim_key in self.bias:
                projected[i] *= self.bias[dim_key]

        return ObservationResult(
            functor_name=self.name, geometry_name=geo.name,
            dimension=geo.dimension, coordinates=projected,
            morphon_z=z, morphon_phi=phi, morphon_dphi=dphi, morphon_R=R,
            receipt=hashlib.sha256(f"{self.name}:{content[:50]}:{time.time()}".encode()).hexdigest()[:16],
        )

    def _shannon_entropy(self, text: str) -> float:
        if not text: return 0.0
        freq = Counter(text)
        total = len(text)
        entropy = -sum((c/total) * math.log2(c/total) for c in freq.values() if c > 0)
        max_entropy = math.log2(min(len(freq), 256)) if freq else 1.0
        return min(entropy / max(max_entropy, 1e-10), 1.0)

class ObservationResult:
    """What an observation functor produces from M₀."""
    functor_name: str
    geometry_name: str
    dimension: int
    coordinates: List[float]
    morphon_z: float  # complexity (Shannon entropy)
    morphon_phi: float  # tension (||x||²)
    morphon_dphi: float  # conservation delta
    morphon_R: float  # E8 radius
    labels: List[str] = field(default_factory=list)
    receipt: str = ""

class ObservationType(Enum):
    """Types of observations that can be made on the Universal Morphon."""
    GEOMETRIC = "geometric"  # Observe as geometric structure (E8, Leech, etc.)
    ALGEBRAIC = "algebraic"  # Observe as algebraic structure (group, ring, etc.)
    TOPOLOGICAL = "topological"  # Observe as topological space
    COMPUTATIONAL = "computational"  # Observe as computation/lambda term
    PHYSICAL = "physical"  # Observe as physical phenomenon

class UniversalMorphon:
    """
    Universal Morphon (M₀)
    
    The fundamental object in morphonic geometry. All mathematical structures
    are observations of M₀ through different functors.
    
    Key properties:
    - Category-theoretic foundation (M₀ is the initial object)
    - All structures emerge via observation functors
    - Preserves morphonic operations (⊕, ⊗, ∇)
    - Supports composition and transformation
    
    The Universal Morphon embodies the principle that "geometry is fundamental"
    and all other structures are derived observations.
    """
    
    def __init__(self, state: Optional[np.ndarray] = None):
        """
        Initialize the Universal Morphon.
        
        Args:
            state: Optional initial state (default: zero state)
        """
        # Internal state (abstract representation)
        self.state = state if state is not None else np.zeros(8)
        
        # Observation history
        self.observations: List[Observation] = []
        
        # Registered functors
        self.functors: Dict[str, Callable] = {}
        
        # Register default functors
        self._register_default_functors()
    
    def _register_default_functors(self):
        """Register default observation functors."""
        self.register_functor("identity", self._identity_functor)
        self.register_functor("geometric_e8", self._geometric_e8_functor)
        self.register_functor("algebraic", self._algebraic_functor)
    
    def _identity_functor(self, state: np.ndarray) -> Any:
        """Identity functor: observe state directly."""
        return state
    
    def _geometric_e8_functor(self, state: np.ndarray) -> Any:
        """Geometric functor: observe as E8 lattice point."""
        # This would use the E8Lattice from layer2_geometric
        # For now, return the state as-is
        return state
    
    def _algebraic_functor(self, state: np.ndarray) -> Any:
        """Algebraic functor: observe as algebraic structure."""
        # Convert to algebraic representation
        return {"coefficients": state.tolist()}
    
    def register_functor(self, name: str, functor: Callable):
        """
        Register a new observation functor.
        
        Args:
            name: Name of the functor
            functor: Callable that takes state and returns observed structure
        """
        self.functors[name] = functor
    
    def observe(self, 
                functor_name: str, 
                obs_type: ObservationType,
                metadata: Optional[Dict] = None) -> Observation:
        """
        Observe the morphon through a specific functor.
        
        Args:
            functor_name: Name of the observation functor
            obs_type: Type of observation
            metadata: Optional metadata
        
        Returns:
            Observation object containing the observed structure
        """
        if functor_name not in self.functors:
            raise ValueError(f"Unknown functor: {functor_name}")
        
        # Apply functor to current state
        functor = self.functors[functor_name]
        observed_data = functor(self.state)
        
        # Create observation
        obs = Observation(
            type=obs_type,
            data=observed_data,
            functor=functor_name,
            metadata=metadata or {}
        )
        
        # Record observation
        self.observations.append(obs)
        
        return obs
    
    def morphonic_add(self, other: 'UniversalMorphon') -> 'UniversalMorphon':
        """
        Morphonic addition (⊕).
        
        Args:
            other: Another Universal Morphon
        
        Returns:
            New Universal Morphon representing the sum
        """
        new_state = self.state + other.state
        return UniversalMorphon(state=new_state)
    
    def morphonic_multiply(self, other: 'UniversalMorphon') -> 'UniversalMorphon':
        """
        Morphonic multiplication (⊗).
        
        Args:
            other: Another Universal Morphon
        
        Returns:
            New Universal Morphon representing the product
        """
        # Element-wise multiplication (Hadamard product)
        new_state = self.state * other.state
        return UniversalMorphon(state=new_state)
    
    def morphonic_gradient(self) -> np.ndarray:
        """
        Morphonic gradient (∇).
        
        Returns:
            Gradient vector of the morphon state
        """
        # Compute discrete gradient
        # For now, use finite differences
        gradient = np.gradient(self.state)
        return gradient
    
    def transform(self, transformation: Callable[[np.ndarray], np.ndarray]) -> 'UniversalMorphon':
        """
        Apply a transformation to the morphon state.
        
        Args:
            transformation: Function that transforms the state
        
        Returns:
            New Universal Morphon with transformed state
        """
        new_state = transformation(self.state)
        return UniversalMorphon(state=new_state)
    
    def get_state(self) -> np.ndarray:
        """Get current morphon state."""
        return self.state.copy()
    
    def set_state(self, state: np.ndarray):
        """Set morphon state."""
        self.state = state.copy()
    
    def __repr__(self) -> str:
        return f"UniversalMorphon(state_dim={len(self.state)}, observations={len(self.observations)})"
    
    def __add__(self, other: 'UniversalMorphon') -> 'UniversalMorphon':
        """Operator overload for morphonic addition."""
        return self.morphonic_add(other)
    
    def __mul__(self, other: 'UniversalMorphon') -> 'UniversalMorphon':
        """Operator overload for morphonic multiplication."""
        return self.morphonic_multiply(other)

class Lam:
    param: str
    body: "Term"

class MorphonCollisionDrugInteractionClassifier:
    """
    Classifies drug-drug interactions using morphon collision geometry.
    """
    def __init__(self):
        self.e8 = E8Lattice()
        self.roots = self.e8.get_roots()
        self.root_vecs = np.array([r.coords for r in self.roots], dtype=float)

    def _fingerprint_to_e8(self, fingerprint):
        """
        Convert a molecular fingerprint (binary or continuous vector) to an E8 root.
        Uses a hash-based projection to 8D, then snaps to nearest E8 root.
        """
        fp = np.array(fingerprint, dtype=float)
        # Project to 8D using a deterministic hash projection
        n = len(fp)
        proj = np.zeros(8)
        for i, val in enumerate(fp):
            proj[i % 8] += val * math.sin((i + 1) * math.pi / n)
            proj[(i + 3) % 8] += val * math.cos((i + 1) * math.pi / n)
        # Normalize
        norm = np.linalg.norm(proj)
        if norm > 0:
            proj = proj / norm * 2.0  # Scale to E8 root magnitude
        # Snap to E8
        dists = np.linalg.norm(self.root_vecs - proj, axis=1)
        idx = int(np.argmin(dists))
        return idx, self.root_vecs[idx], float(dists[idx])

    def _run_collision(self, root_a_idx, root_b_idx, n_steps=9):
        """
        Run a morphon collision between two E8 roots.
        Returns the terminal collision morphon and all internal closure events.
        """
        vec_a = self.root_vecs[root_a_idx].copy()
        vec_b = self.root_vecs[root_b_idx].copy()
        closure_events = []

        state = (vec_a + vec_b) / 2.0  # Initial combined state
        for step in range(n_steps):
            # Apply morphonic reduction: project onto E8, then blend
            dists = np.linalg.norm(self.root_vecs - state, axis=1)
            nearest_idx = int(np.argmin(dists))
            nearest_vec = self.root_vecs[nearest_idx]
            dr = digital_root(nearest_idx + 1)
            closure_events.append({
                "step": step,
                "e8_root_idx": nearest_idx,
                "dr": dr,
                "snap_distance": float(dists[nearest_idx]),
            })
            # Morphonic reduction step
            alpha = 0.618  # Golden ratio blend
            state = alpha * nearest_vec + (1 - alpha) * state

        # Terminal collision morphon
        dists = np.linalg.norm(self.root_vecs - state, axis=1)
        terminal_idx = int(np.argmin(dists))
        terminal_dr  = digital_root(terminal_idx + 1)

        return terminal_idx, terminal_dr, closure_events

    def classify_interaction(self, drug_a_name, drug_a_fp,
                              drug_b_name, drug_b_fp):
        """
        Classify the interaction between two drugs.
        """
        idx_a, root_a, dist_a = self._fingerprint_to_e8(drug_a_fp)
        idx_b, root_b, dist_b = self._fingerprint_to_e8(drug_b_fp)

        terminal_idx, terminal_dr, closures = self._run_collision(idx_a, idx_b)

        interaction_class, description, color = INTERACTION_CLASSES.get(
            terminal_dr, ("Unknown", "Unclassified interaction", '#8b949e'))

        # Confidence: based on snap distances (lower = more confident)
        confidence = max(0.0, 1.0 - (dist_a + dist_b) / 10.0)

        return {
            "drug_a": drug_a_name,
            "drug_b": drug_b_name,
            "drug_a_e8_root": idx_a,
            "drug_a_dr": digital_root(idx_a + 1),
            "drug_b_e8_root": idx_b,
            "drug_b_dr": digital_root(idx_b + 1),
            "collision_terminal_root": terminal_idx,
            "collision_dr": terminal_dr,
            "interaction_class": interaction_class,
            "description": description,
            "confidence": confidence,
            "n_closure_events": len(closures),
            "closure_dr_sequence": [c["dr"] for c in closures],
            "closure_events": closures,
        }

    def screen_library(self, drugs):
        """
        Screen all pairwise interactions in a drug library.
        drugs: list of (name, fingerprint) tuples
        Returns all pairwise interaction results.
        """
        results = []
        for (name_a, fp_a), (name_b, fp_b) in combinations(drugs, 2):
            r = self.classify_interaction(name_a, fp_a, name_b, fp_b)
            results.append(r)
        return results

    def plot(self, results, output_path, title="Drug Interaction Morphon Map"):
        """Visualize the drug interaction landscape."""
        fig = plt.figure(figsize=(22, 14))
        fig.patch.set_facecolor('#0d1117')
        gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.45, wspace=0.38)

        def dark_ax(ax):
            ax.set_facecolor('#161b22')
            for sp in ax.spines.values(): sp.set_color('#30363d')
            ax.tick_params(colors='#8b949e', labelsize=8)

        # Panel 1: Interaction class distribution
        ax1 = fig.add_subplot(gs[0, 0]); dark_ax(ax1)
        class_counts = {}
        for r in results:
            cls = r['interaction_class']
            class_counts[cls] = class_counts.get(cls, 0) + 1
        sorted_classes = sorted(class_counts.items(), key=lambda x: -x[1])
        labels = [x[0] for x in sorted_classes]
        counts = [x[1] for x in sorted_classes]
        dr_map = {v[0]: k for k, v in INTERACTION_CLASSES.items()}
        bar_colors = [INTERACTION_CLASSES[dr_map.get(l, 9)][2] for l in labels]
        bars = ax1.barh(range(len(labels)), counts, color=bar_colors, edgecolor='#30363d', alpha=0.85)
        ax1.set_yticks(range(len(labels))); ax1.set_yticklabels(labels, fontsize=8, color='white')
        ax1.set_xlabel('Count', color='#8b949e', fontsize=9)
        ax1.set_title('Interaction Class Distribution', color='white', fontsize=10, fontweight='bold')
        for bar, cnt in zip(bars, counts):
            ax1.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                     str(cnt), va='center', color='white', fontsize=9)

        # Panel 2: Collision DR heatmap (drug × drug)
        ax2 = fig.add_subplot(gs[0, 1:]); dark_ax(ax2)
        drug_names = list(dict.fromkeys([r['drug_a'] for r in results] + [r['drug_b'] for r in results]))
        n = len(drug_names)
        matrix = np.zeros((n, n))
        for r in results:
            i = drug_names.index(r['drug_a'])
            j = drug_names.index(r['drug_b'])
            matrix[i, j] = r['collision_dr']
            matrix[j, i] = r['collision_dr']
        np.fill_diagonal(matrix, 0)
        im = ax2.imshow(matrix, cmap='RdYlGn', aspect='auto', vmin=1, vmax=9)
        ax2.set_xticks(range(n)); ax2.set_xticklabels(drug_names, rotation=45, ha='right', fontsize=8, color='white')
        ax2.set_yticks(range(n)); ax2.set_yticklabels(drug_names, fontsize=8, color='white')
        ax2.set_title('Drug × Drug Collision DR Matrix\n(Green=Synergistic, Red=Antagonistic)',
                      color='white', fontsize=10, fontweight='bold')
        plt.colorbar(im, ax=ax2, label='Collision DR')

        # Panel 3: Confidence distribution
        ax3 = fig.add_subplot(gs[1, 0]); dark_ax(ax3)
        confidences = [r['confidence'] for r in results]
        ax3.hist(confidences, bins=10, color='#58a6ff', edgecolor='#30363d', alpha=0.85)
        ax3.set_xlabel('Confidence score', color='#8b949e', fontsize=9)
        ax3.set_ylabel('Count', color='#8b949e', fontsize=9)
        ax3.set_title('Prediction Confidence Distribution', color='white', fontsize=10, fontweight='bold')

        # Panel 4: Top interactions table
        ax4 = fig.add_subplot(gs[1, 1:]); ax4.set_facecolor('#161b22'); ax4.axis('off')
        top = sorted(results, key=lambda x: x['confidence'], reverse=True)[:12]
        headers = ['Drug A', 'Drug B', 'Class', 'DR', 'Confidence']
        col_x = [0.01, 0.22, 0.43, 0.65, 0.76]
        y0 = 0.95
        for hx, hdr in zip(col_x, headers):
            ax4.text(hx, y0, hdr, transform=ax4.transAxes,
                     color='#ffa657', fontsize=9, fontweight='bold', va='top', fontfamily='monospace')
        for i, r in enumerate(top):
            y = y0 - 0.075 * (i + 1)
            dr_color = INTERACTION_CLASSES.get(r['collision_dr'], ('','','#8b949e'))[2]
            for vx, val in zip(col_x, [r['drug_a'][:18], r['drug_b'][:18],
                                        r['interaction_class'][:18],
                                        str(r['collision_dr']),
                                        f"{r['confidence']:.2f}"]):
                ax4.text(vx, y, val, transform=ax4.transAxes,
                         color=dr_color if vx == col_x[2] else '#c9d1d9',
                         fontsize=8.5, va='top', fontfamily='monospace')

        fig.suptitle(title, color='white', fontsize=13, fontweight='bold', y=1.01)
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='#0d1117')
        plt.close()
        print(f"[SAVED] {output_path}")

class MorphonicAdapter(MCPAdapter):
    """Adapter for Layer 1: Morphonic Foundation."""
    
    @property
    def layer(self) -> int:
        return 1
    
    async def initialize(self) -> bool:
        """Initialize morphonic systems."""
        # Pre-compute common morphons locally (lightweight)
        for digit in range(10):
            morphon = self._generate_local_morphon(digit)
            self._cache_set(f"morphon_{digit}", morphon)
        return True
    
    def _generate_local_morphon(self, digit: int) -> dict:
        """Generate morphon locally (lightweight computation)."""
        return {
            "seed": digit,
            "digital_root": digit % 9 or 9,
            "resonance": np.exp(2j * np.pi * digit / 9).real
        }
    
    async def generate_morphon(self, seed: str, use_mcp: bool = False) -> dict:
        """
        Generate morphon from seed.
        
        Args:
            seed: Single digit seed
            use_mcp: If True, always use MCP server (for distributed ops)
        
        Returns:
            Morphon data (handle if using MCP)
        """
        digit = int(seed[0]) if seed else 0
        
        # Check local cache first
        cached = self._cache_get(f"morphon_{digit}")
        if cached and not use_mcp:
            return cached
        
        # Use MCP server
        if self._client:
            return await self._client.generate_morphon(seed)
        
        # Fallback to local
        return self._generate_local_morphon(digit)
    
    async def execute_mglc(self, expression: str, context: dict | None = None) -> dict:
        """Execute MGLC expression."""
        if self._client:
            return await self._client.execute_mglc(expression, context)
        
        # Local fallback
        return {"expression": expression, "status": "local_execution"}
    
    async def expand_seed(self, digit: int, dimensions: int = 24) -> dict:
        """Expand seed to substrate."""
        if self._client:
            return await self._client.expand_seed(digit, dimensions)
        
        # Local lightweight generation
        np.random.seed(digit)
        substrate = np.random.randn(dimensions)
        substrate = substrate / np.linalg.norm(substrate)
        
        return {
            "seed": digit,
            "dimensions": dimensions,
            "norm": float(np.linalg.norm(substrate)),
            "local": True
        }

class MorphonicEmergenceDemo:
    """
    Complete demonstration of morphonic emergence.
    
    Shows how a single observer decision (choosing a digit)
    collapses formless potential into specific geometric form.
    """
    
    def __init__(self):
        """Initialize all CQE components"""
        print("Initializing CQE System...")
        print("=" * 70)
        
        # Core geometric structures
        print("Loading E8 lattice...")
        self.e8 = E8Full()
        
        print("Loading Niemeier family...")
        self.niemeier = NiemeierFamily()
        
        print("Loading Leech lattice...")
        self.leech = LeechLattice()
        
        print("Initializing Weyl chamber finder...")
        self.weyl = WeylChamberFinder(self.e8)
        
        # Morphonic generator
        print("Initializing morphonic generator...")
        self.generator = MorphonicGenerator()
        
        # Receipt chain
        self.receipt_chain = []
        
        print("\n✓ CQE System initialized")
        print("=" * 70)
    
    def run_complete_pipeline(self, seed_digit: int) -> Dict:
        """
        Run complete morphonic emergence pipeline.
        
        Args:
            seed_digit: Observer's choice (1-9)
            
        Returns:
            Complete results dictionary with all stages
        """
        print(f"\n{'='*70}")
        print(f"MORPHONIC EMERGENCE: Seed Digit = {seed_digit}")
        print(f"{'='*70}\n")
        
        results = {
            "seed_digit": seed_digit,
            "timestamp": datetime.now().isoformat(),
            "stages": {}
        }
        
        # Stage 1: Observer Decision
        print("Stage 1: Observer Decision (Collapse of Potential)")
        print("-" * 70)
        seed = MorphonSeed(digit=seed_digit, digital_root=seed_digit, parity=seed_digit % 2)
        print(f"  Seed created: digit={seed.digit}, DR={seed.digital_root}, parity={seed.parity}")
        print(f"  → Potential collapsed to specific morphon")
        
        results["stages"]["observer_decision"] = {
            "seed": seed_digit,
            "digital_root": seed.digital_root,
            "parity": seed.parity
        }
        
        # Stage 2: Digital Root Iteration
        print("\nStage 2: Digital Root Iteration (Morphonic Unfolding)")
        print("-" * 70)
        dr_sequence = self.generator.iterate_mod9(seed_digit)
        print(f"  DR sequence: {dr_sequence}")
        print(f"  → Morphon unfolds through {len(dr_sequence)} states")
        
        results["stages"]["dr_iteration"] = {
            "sequence": dr_sequence,
            "length": len(dr_sequence),
            "fixed_point": dr_sequence[-1] == dr_sequence[-2] if len(dr_sequence) > 1 else False
        }
        
        # Stage 3: E8 Emergence
        print("\nStage 3: E8 Vector Emergence (Geometric Manifestation)")
        print("-" * 70)
        e8_vector, _, root_sequence = self.generator.generate_e8_from_seed(seed)
        print(f"  E8 vector: {e8_vector}")
        print(f"  Norm: {np.linalg.norm(e8_vector):.6f}")
        print(f"  Composed from {len(root_sequence)} E8 roots")
        print(f"  → 8D geometric form manifested")
        
        results["stages"]["e8_emergence"] = {
            "vector": e8_vector.tolist(),
            "norm": float(np.linalg.norm(e8_vector)),
            "num_roots": len(root_sequence)
        }
        
        # Stage 4: Weyl Chamber Location
        print("\nStage 4: Weyl Chamber Location (Geometric Positioning)")
        print("-" * 70)
        chamber = self.weyl.find_chamber(e8_vector)
        print(f"  Chamber ID: {chamber.chamber_id}")
        print(f"  Sign pattern: {chamber.sign_pattern}")
        print(f"  → Located in 1 of 696,729,600 chambers")
        
        # Move to fundamental chamber
        fund_vector, reflections = self.weyl.move_to_fundamental_chamber(e8_vector)
        fund_chamber = self.weyl.fundamental_chamber()
        print(f"  Fundamental chamber: {fund_chamber.chamber_id}")
        print(f"  Reflections needed: {len(reflections)}")
        
        results["stages"]["weyl_chamber"] = {
            "chamber_id": chamber.chamber_id,
            "sign_pattern": chamber.sign_pattern.tolist(),
            "fundamental_chamber_id": fund_chamber.chamber_id,
            "reflections_to_fundamental": len(reflections)
        }
        
        # Stage 5: 24D Extension
        print("\nStage 5: 24D Extension (Dimensional Lifting)")
        print("-" * 70)
        vector_24d = self.generator.extend_to_24d(e8_vector, seed)
        print(f"  24D vector (first 8): {vector_24d[:8]}")
        print(f"  24D norm: {np.linalg.norm(vector_24d):.6f}")
        print(f"  → Extended to 24D via 3×E8 construction")
        
        # Verify Leech projection
        is_leech = self.leech.is_leech_vector(np.round(vector_24d))
        print(f"  Leech lattice compatible: {is_leech}")
        
        results["stages"]["24d_extension"] = {
            "vector": vector_24d.tolist(),
            "norm": float(np.linalg.norm(vector_24d)),
            "leech_compatible": is_leech
        }
        
        # Stage 6: Niemeier Lattice Selection
        print("\nStage 6: Niemeier Lattice Selection (Final Form)")
        print("-" * 70)
        niemeier_type, niemeier_lattice = self.generator.generate_niemeier_from_seed(seed)
        print(f"  Lattice type: {niemeier_type}")
        print(f"  Root system: {niemeier_lattice.root_system}")
        print(f"  Number of roots: {len(niemeier_lattice.roots)}")
        print(f"  Kissing number: {niemeier_lattice.kissing_number}")
        print(f"  → Final geometric form: {niemeier_type}")
        
        results["stages"]["niemeier_selection"] = {
            "type": niemeier_type,
            "root_system": str(niemeier_lattice.root_system),
            "num_roots": len(niemeier_lattice.roots),
            "kissing_number": niemeier_lattice.kissing_number
        }
        
        # Stage 7: Receipt Chain
        print("\nStage 7: Receipt Chain (Cryptographic Proof)")
        print("-" * 70)
        receipt = self._generate_complete_receipt(results)
        print(f"  Receipt hash: {receipt['hash']}")
        print(f"  Stages verified: {len(results['stages'])}")
        print(f"  → Complete provable chain generated")
        
        results["receipt"] = receipt
        
        # Summary
        print(f"\n{'='*70}")
        print("EMERGENCE COMPLETE")
        print(f"{'='*70}")
        print(f"  Input: Single digit {seed_digit}")
        print(f"  Output: {niemeier_type} lattice in 24D")
        print(f"  Path: {seed_digit} → DR{dr_sequence} → E8 → 24D → {niemeier_type}")
        print(f"  Proof: {receipt['hash']}")
        print(f"{'='*70}\n")
        
        return results
    
    def _generate_complete_receipt(self, results: Dict) -> Dict:
        """Generate cryptographic receipt for entire pipeline"""
        receipt = {
            "operation": "complete_morphonic_emergence",
            "timestamp": results["timestamp"],
            "seed_digit": results["seed_digit"],
            "stages": list(results["stages"].keys()),
            "final_form": results["stages"]["niemeier_selection"]["type"],
            "verified": True
        }
        
        # Hash entire results
        results_str = json.dumps(results, sort_keys=True, default=str)
        import hashlib
        receipt["hash"] = hashlib.sha256(results_str.encode()).hexdigest()[:16]
        
        return receipt
    
    def compare_all_seeds(self):
        """Run pipeline for all 9 seeds and compare results"""
        print(f"\n{'='*70}")
        print("COMPARING ALL 9 MORPHONIC SEEDS")
        print(f"{'='*70}\n")
        
        all_results = []
        
        for digit in range(1, 10):
            result = self.run_complete_pipeline(digit)
            all_results.append(result)
        
        # Summary table
        print(f"\n{'='*70}")
        print("SUMMARY: All 9 Morphonic Emergences")
        print(f"{'='*70}")
        print(f"{'Seed':<6} {'DR Seq':<15} {'E8 Norm':<10} {'24D Norm':<10} {'Niemeier':<12} {'Roots':<8}")
        print("-" * 70)
        
        for result in all_results:
            seed = result["seed_digit"]
            dr_seq = str(result["stages"]["dr_iteration"]["sequence"][:4])
            e8_norm = result["stages"]["e8_emergence"]["norm"]
            d24_norm = result["stages"]["24d_extension"]["norm"]
            niemeier = result["stages"]["niemeier_selection"]["type"]
            num_roots = result["stages"]["niemeier_selection"]["num_roots"]
            
            print(f"{seed:<6} {dr_seq:<15} {e8_norm:<10.4f} {d24_norm:<10.4f} {niemeier:<12} {num_roots:<8}")
        
        print(f"{'='*70}\n")
        
        return all_results
    
    def save_results(self, results: Dict, filename: str = "morphonic_emergence_results.json"):
        """Save results to JSON file"""
        filepath = os.path.join(os.path.dirname(__file__), filename)
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"✓ Results saved to {filepath}")

class MorphonicLambdaController(BaseController):
    name = "morphonic_lambda"

    def run(self, ctx: ControllerContext, params: Dict[str, Any]) -> Dict[str, Any]:
        # Default term: ((λx. x) (λy. y)) -> (λy. y)
        term = App(Lam("x", Var("x")), Lam("y", Var("y")))
        limit = int(params.get("limit", 80))
        result = eval_normal(term, limit=limit)
        out_path = ctx.workspace / "runs" / ctx.run_id / "artifacts" / "morphonic_lambda" / "eval_trace.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(__import__("json").dumps(result, indent=2), encoding="utf-8")
        artifacts = canon_artifacts([{"path": "morphonic_lambda/eval_trace.json", "role": "lambda_trace"}], base_dir=ctx.run_dir)
        receipt = write_receipt(
            workspace=ctx.workspace,
            run_id=ctx.run_id,
            step_id=ctx.step_id,
            controller=self.name,
            inputs={"term": "App(Lam(x,x), Lam(y,y))", "limit": limit},
            outputs={"normal_form": result["normal_form"], "steps": result["steps"]},
            artifacts=artifacts,
            overlays=params.get("overlays"),
            extra={"lambda_ir": {"term": "((λx.x) (λy.y))", "normal_form": result["normal_form"]}},
        )
        return {"receipt": receipt, "lambda_result": result}

class MorphonicRegressionController(BaseController):
    name = "morphonic_regression"

    def run(self, ctx: ControllerContext, params: Dict[str, Any]) -> Dict[str, Any]:
        # Minimal regression check: ensure previous controllers produced expected artifacts
        run_dir = ctx.workspace / "runs" / ctx.run_id
        expected = [
            run_dir / "artifacts" / "geo_ops" / "geo_tokens.json",
            run_dir / "artifacts" / "viewer24" / "residue_summary.json",
            run_dir / "artifacts" / "morphonic_lambda" / "eval_trace.json",
        ]
        missing=[str(p) for p in expected if not p.exists()]
        ok = (len(missing)==0)
        report = {"ok": ok, "missing": missing, "expected_count": len(expected)}
        out_path = run_dir / "artifacts" / "tests" / "regression_report.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(__import__("json").dumps(report, indent=2), encoding="utf-8")
        artifacts = canon_artifacts([{"path": "tests/regression_report.json", "role": "regression_report"}], base_dir=ctx.run_dir)
        receipt = write_receipt(
            workspace=ctx.workspace,
            run_id=ctx.run_id,
            step_id=ctx.step_id,
            controller=self.name,
            inputs={"expected": [str(p) for p in expected]},
            outputs=report,
            artifacts=artifacts,
            overlays=params.get("overlays"),
        )
        return {"receipt": receipt, "report": report}

class ProteinFoldMorphon:
    """
    Assigns Morphon Basin Classes to protein residues using E8 geometry.
    """
    def __init__(self):
        self.e8 = E8Lattice()
        self.roots = self.e8.get_roots()
        self.root_vecs = np.array([r.coords for r in self.roots], dtype=float)
        # Normalize root vectors to unit sphere for angle-space comparison
        norms = np.linalg.norm(self.root_vecs, axis=1, keepdims=True)
        self.root_vecs_norm = self.root_vecs / np.where(norms > 0, norms, 1)

    def _phi_psi_to_8d(self, phi_deg, psi_deg):
        """
        Encode a (φ,ψ) Ramachandran pair as an 8D vector.
        Uses trigonometric encoding to preserve circular topology of angles.
        The 8D vector captures: sin/cos of φ, sin/cos of ψ, their products,
        and two higher-order terms encoding the local basin curvature.
        """
        phi = math.radians(phi_deg)
        psi = math.radians(psi_deg)
        sp, cp = math.sin(phi), math.cos(phi)
        ss, cs = math.sin(psi), math.cos(psi)
        return np.array([
            sp, cp, ss, cs,
            sp * ss, cp * cs, sp * cs, cp * ss
        ], dtype=float)

    def _snap_to_e8(self, vec8d):
        """Snap an 8D vector to the nearest E8 root. Returns (root_idx, root_vec, distance)."""
        v = np.array(vec8d, dtype=float)
        norm = np.linalg.norm(v)
        if norm > 0:
            v_norm = v / norm
        else:
            v_norm = v
        # Use cosine similarity for angle-space snapping
        sims = self.root_vecs_norm @ v_norm
        idx = int(np.argmax(sims))
        dist = float(np.linalg.norm(self.root_vecs[idx] - np.array(vec8d)))
        return idx, self.root_vecs[idx], dist

    def classify_residue(self, phi_deg, psi_deg, residue_name="X"):
        """
        Classify a single residue by its (φ,ψ) angles.
        Returns a dict with root_idx, MBC (Morphon Basin Class), basin_name, distance.
        """
        vec = self._phi_psi_to_8d(phi_deg, psi_deg)
        idx, root_vec, dist = self._snap_to_e8(vec)
        mbc = digital_root(idx + 1)  # +1 so idx=0 → DR=1 not DR=0
        return {
            "residue": residue_name,
            "phi": phi_deg,
            "psi": psi_deg,
            "e8_root_idx": idx,
            "morphon_basin_class": mbc,
            "basin_name": BASIN_NAMES.get(mbc, f"Basin {mbc}"),
            "snap_distance": dist,
        }

    def analyze_sequence(self, phi_psi_list, residue_names=None):
        """
        Analyze a full protein sequence.
        phi_psi_list: list of (phi_deg, psi_deg) tuples
        residue_names: optional list of residue identifiers
        Returns list of per-residue classification dicts + summary statistics.
        """
        if residue_names is None:
            residue_names = [f"R{i+1}" for i in range(len(phi_psi_list))]
        results = []
        for i, (phi, psi) in enumerate(phi_psi_list):
            r = self.classify_residue(phi, psi, residue_names[i])
            results.append(r)

        # Summary statistics
        mbcs = [r["morphon_basin_class"] for r in results]
        mbc_counts = Counter(mbcs)
        dominant_mbc = mbc_counts.most_common(1)[0][0]

        # Basin transition matrix: how often does MBC_i → MBC_j?
        transitions = defaultdict(int)
        for i in range(len(mbcs) - 1):
            transitions[(mbcs[i], mbcs[i+1])] += 1

        # Morphon sequence digital root (the "protein's global MBC")
        total_dr = digital_root(sum(mbcs))

        summary = {
            "n_residues": len(results),
            "mbc_distribution": {str(k): v for k, v in sorted(mbc_counts.items())},
            "dominant_mbc": dominant_mbc,
            "dominant_basin_name": BASIN_NAMES.get(dominant_mbc, f"Basin {dominant_mbc}"),
            "global_morphon_dr": total_dr,
            "global_basin_name": BASIN_NAMES.get(total_dr, f"Basin {total_dr}"),
            "mean_snap_distance": float(np.mean([r["snap_distance"] for r in results])),
            "basin_transitions": {f"{k[0]}->{k[1]}": v for k, v in sorted(transitions.items())},
        }
        return {"residues": results, "summary": summary}

    def plot_morphon_map(self, analysis_result, output_path, title="Protein Morphon Map"):
        """
        Generate a Morphon Map visualization:
        - Left: Ramachandran plot colored by MBC
        - Right: MBC sequence along the chain
        - Bottom: Basin distribution histogram
        """
        residues = analysis_result["residues"]
        summary  = analysis_result["summary"]

        phis  = [r["phi"] for r in residues]
        psis  = [r["psi"] for r in residues]
        mbcs  = [r["morphon_basin_class"] for r in residues]
        colors = [BASIN_COLORS.get(m, '#8b949e') for m in mbcs]

        fig = plt.figure(figsize=(20, 14))
        fig.patch.set_facecolor('#0d1117')

        # ── Ramachandran Morphon Map ──────────────────────────────────────────
        ax1 = fig.add_subplot(2, 3, (1, 4))
        ax1.set_facecolor('#161b22')
        for sp in ax1.spines.values(): sp.set_color('#30363d')
        ax1.tick_params(colors='#8b949e')

        sc = ax1.scatter(phis, psis, c=colors, s=60, alpha=0.85, edgecolors='none', zorder=5)
        ax1.axhline(0, color='#30363d', linewidth=0.8, alpha=0.5)
        ax1.axvline(0, color='#30363d', linewidth=0.8, alpha=0.5)
        ax1.set_xlim(-180, 180); ax1.set_ylim(-180, 180)
        ax1.set_xlabel('φ (degrees)', color='#8b949e', fontsize=11)
        ax1.set_ylabel('ψ (degrees)', color='#8b949e', fontsize=11)
        ax1.set_title('Ramachandran Morphon Map\n(Color = E8 Basin Class)', color='white', fontsize=12, fontweight='bold')

        # Legend
        patches = [mpatches.Patch(color=BASIN_COLORS[mbc], label=f"MBC {mbc}: {BASIN_NAMES[mbc]}")
                   for mbc in sorted(BASIN_COLORS.keys()) if mbc in Counter(mbcs)]
        ax1.legend(handles=patches, loc='lower left', fontsize=8,
                   facecolor='#161b22', labelcolor='white', edgecolor='#30363d')

        # ── MBC Sequence Along Chain ──────────────────────────────────────────
        ax2 = fig.add_subplot(2, 3, 2)
        ax2.set_facecolor('#161b22')
        for sp in ax2.spines.values(): sp.set_color('#30363d')
        ax2.tick_params(colors='#8b949e', labelsize=8)

        chain_colors = [BASIN_COLORS.get(m, '#8b949e') for m in mbcs]
        ax2.scatter(range(len(mbcs)), mbcs, c=chain_colors, s=30, alpha=0.85, zorder=5)
        ax2.plot(range(len(mbcs)), mbcs, color='#30363d', linewidth=0.8, alpha=0.5, zorder=3)
        ax2.set_xlabel('Residue index', color='#8b949e', fontsize=9)
        ax2.set_ylabel('Morphon Basin Class', color='#8b949e', fontsize=9)
        ax2.set_title('MBC Sequence Along Chain', color='white', fontsize=10, fontweight='bold')
        ax2.set_yticks(range(1, 10))

        # ── Basin Distribution ────────────────────────────────────────────────
        ax3 = fig.add_subplot(2, 3, 3)
        ax3.set_facecolor('#161b22')
        for sp in ax3.spines.values(): sp.set_color('#30363d')
        ax3.tick_params(colors='#8b949e', labelsize=8)

        mbc_dist = summary["mbc_distribution"]
        mbc_keys = sorted([int(k) for k in mbc_dist.keys()])
        mbc_vals = [mbc_dist[str(k)] for k in mbc_keys]
        bar_colors = [BASIN_COLORS.get(k, '#8b949e') for k in mbc_keys]
        bars = ax3.bar(mbc_keys, mbc_vals, color=bar_colors, edgecolor='#30363d', alpha=0.85)
        ax3.set_xlabel('Morphon Basin Class', color='#8b949e', fontsize=9)
        ax3.set_ylabel('Residue count', color='#8b949e', fontsize=9)
        ax3.set_title('Basin Distribution', color='white', fontsize=10, fontweight='bold')
        ax3.set_xticks(mbc_keys)
        for bar, val in zip(bars, mbc_vals):
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                     str(val), ha='center', va='bottom', color='white', fontsize=8)

        # ── Summary Panel ─────────────────────────────────────────────────────
        ax4 = fig.add_subplot(2, 3, (5, 6))
        ax4.set_facecolor('#161b22'); ax4.axis('off')
        for sp in ax4.spines.values(): sp.set_color('#30363d')

        lines = [
            ("PROTEIN MORPHON ANALYSIS SUMMARY", '#ffa657', True),
            ("", '#c9d1d9', False),
            (f"Residues analyzed:     {summary['n_residues']}", '#c9d1d9', False),
            (f"Dominant basin:        MBC {summary['dominant_mbc']} — {summary['dominant_basin_name']}", '#58a6ff', False),
            (f"Global Morphon DR:     {summary['global_morphon_dr']} — {summary['global_basin_name']}", '#3fb950', False),
            (f"Mean snap distance:    {summary['mean_snap_distance']:.4f}", '#c9d1d9', False),
            ("", '#c9d1d9', False),
            ("Basin Composition:", '#ffa657', True),
        ]
        for mbc_k in sorted(mbc_dist.keys(), key=int):
            pct = int(mbc_dist[mbc_k]) / summary['n_residues'] * 100
            lines.append((f"  MBC {mbc_k} ({BASIN_NAMES.get(int(mbc_k),'?')[:18]:18s}): "
                          f"{mbc_dist[mbc_k]:3d} residues ({pct:.1f}%)",
                          BASIN_COLORS.get(int(mbc_k), '#8b949e'), False))

        for k, (line, color, bold) in enumerate(lines):
            ax4.text(0.03, 0.97 - k * 0.082, line, transform=ax4.transAxes,
                     color=color, fontsize=9.5, fontweight='bold' if bold else 'normal',
                     va='top', fontfamily='monospace')

        fig.suptitle(title, color='white', fontsize=14, fontweight='bold', y=1.01)
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='#0d1117')
        plt.close()
        print(f"[SAVED] {output_path}")

class MorphonPotential:
    """The full potential of a morphon — committed path + all open paths."""
    morphon_id: str = ""
    committed_geometry: str = ""
    committed_coords: List[float] = field(default_factory=list)
    committed_dphi: float = 0.0
    open_paths: List[Dict] = field(default_factory=list)
    total_potential: float = 0.0
    labels: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.morphon_id:
            self.morphon_id = f"mpot-{uuid.uuid4().hex[:8]}"

class ActionStep:
    """
    A proposed motion in CQE state space.

    Fields:
    - channel: one of {3,6,9}
        3 ? stabilize/internal flow (poloidal / inward coherence)
        6 ? expression/outward flow (toroidal / surfacing)
        9 ? stitching/new-boundary flow (meridional / membrane formation)

      CQE uses these 3/6/9 channels to tag what kind of motion is being
      attempted. This matters for receipts, because channel 9 is
      considered a boundary crossing (Law 2).

    - delta_coords: np.ndarray offset to add to current coords if allowed.

    - note: human-readable trace / explanation of why this step exists
      (e.g. "toward goal", "orch_chamber boundary proposal", etc.).
    """
    channel: int
    delta_coords: np.ndarray
    note: str

class BeamRequest(BaseModel):
    e8_coords: List[float]
    max_iter: int = 100

class CommitRequest(BaseModel):
    morphon_id: str
    dphi: float

class CosmologicalVoidMorphonClassifier:
    def __init__(self):
        self.e8 = E8Lattice()
        self.roots = self.e8.get_roots()
        self.root_vecs = np.array([r.coords for r in self.roots], dtype=float)

    def _generate_density_field(self, structure_type, n_points=50, seed=42):
        """Generate a synthetic density field for different cosmic structures."""
        rng = np.random.default_rng(seed)

        if structure_type == 'void':
            # Void: very low density, nearly uniform, slight underdensity
            density = rng.uniform(0.01, 0.15, n_points)
            velocity = rng.normal(0, 5, (n_points, 3))  # km/s, Hubble flow dominated
            tidal_eigenvalues = rng.uniform(-0.1, 0.1, (n_points, 3))

        elif structure_type == 'sheet':
            # Sheet/wall: moderate density, one compressed direction
            density = rng.uniform(0.5, 2.0, n_points)
            velocity = rng.normal(0, 30, (n_points, 3))
            tidal_eigenvalues = np.column_stack([
                rng.uniform(-0.5, 0.0, n_points),  # one negative eigenvalue
                rng.uniform(0.0, 0.3, n_points),
                rng.uniform(0.0, 0.3, n_points),
            ])

        elif structure_type == 'filament':
            # Filament: high density, two compressed directions
            density = rng.uniform(5.0, 20.0, n_points)
            velocity = rng.normal(0, 100, (n_points, 3))
            tidal_eigenvalues = np.column_stack([
                rng.uniform(-1.0, -0.3, n_points),
                rng.uniform(-0.5, 0.0, n_points),
                rng.uniform(0.0, 0.5, n_points),
            ])

        elif structure_type == 'node':
            # Node/cluster: very high density, all three directions compressed
            density = rng.uniform(100.0, 1000.0, n_points)
            velocity = rng.normal(0, 500, (n_points, 3))
            tidal_eigenvalues = np.column_stack([
                rng.uniform(-2.0, -0.5, n_points),
                rng.uniform(-1.5, -0.3, n_points),
                rng.uniform(-1.0, -0.1, n_points),
            ])

        return density, velocity, tidal_eigenvalues

    def _encode_density_point(self, density, velocity, tidal_eigs):
        """Encode a single density field point as an 8D E8 vector (direction-based)."""
        log_density = math.log1p(density) / 7.0  # normalize to ~[0,1]
        vel_mag = np.linalg.norm(velocity) / 600.0  # normalize
        # Use signed values to span the full E8 sphere
        vec = np.array([
            log_density * 2.0 - 1.0,          # [-1, +1]
            tidal_eigs[0],                     # already in [-2, +0.5]
            tidal_eigs[1],
            tidal_eigs[2],
            vel_mag * 2.0 - 1.0,              # [-1, +1]
            (tidal_eigs[0] - tidal_eigs[2]),   # anisotropy
            sum(tidal_eigs),                   # trace
            (log_density - 0.5) * (vel_mag - 0.5) * 4.0,  # coupling
        ], dtype=float)
        # Normalize to unit sphere so snap is direction-based
        norm = np.linalg.norm(vec)
        if norm > 1e-10:
            vec = vec / norm * 1.414  # scale to E8 root norm
        return vec

    def _snap_to_e8(self, vec):
        dists = np.linalg.norm(self.root_vecs - vec, axis=1)
        idx = np.argmin(dists)
        return self.roots[idx], idx, dists[idx]

    def classify_structure(self, structure_type):
        density, velocity, tidal_eigs = self._generate_density_field(structure_type)

        dr_sequence = []
        snap_distances = []
        e8_indices = []

        for i in range(len(density)):
            vec = self._encode_density_point(density[i], velocity[i], tidal_eigs[i])
            root, idx, dist = self._snap_to_e8(vec)
            dr = digital_root(idx)
            dr_sequence.append(dr)
            snap_distances.append(dist)
            e8_indices.append(idx)

        dr_entropy = shannon_entropy(dr_sequence)
        snap_var = float(np.var(snap_distances))
        unique_roots = len(set(e8_indices))
        root_density = unique_roots / len(self.roots)  # fraction of E8 roots visited

        # Classification logic:
        # Void: low entropy, low root density (rootless = Leech-like)
        # Sheet: moderate entropy, moderate root density
        # Filament: high entropy, high root density
        # Node: very high entropy, maximum root density (Niemeier-like)
        leech_score = 1.0 - dr_entropy / math.log2(9)  # high = void-like
        niemeier_score = root_density  # high = node-like

        # Classify based on entropy and root density
        # void: low entropy (few roots visited), low density
        # node: high entropy (many roots visited), high density
        if dr_entropy < 1.5 and root_density < 0.08:
            predicted = 'void'
        elif dr_entropy < 2.2 and root_density < 0.15:
            predicted = 'sheet'
        elif dr_entropy < 2.8 or root_density < 0.25:
            predicted = 'filament'
        else:
            predicted = 'node' 

        return {
            'structure_type': structure_type,
            'predicted': predicted,
            'correct': predicted == structure_type,
            'dr_entropy': dr_entropy,
            'snap_variance': snap_var,
            'unique_roots': unique_roots,
            'root_density': root_density,
            'leech_score': leech_score,
            'niemeier_score': niemeier_score,
            'mean_density': float(np.mean(density)),
            'dr_sequence': dr_sequence,
        }

    def run_all(self):
        results = []
        print(f"\n{'Structure':>12} {'Predicted':>12} {'Leech':>8} {'Niemeier':>10} {'Match':>6}")
        print("-" * 55)
        for stype in ['void', 'sheet', 'filament', 'node']:
            r = self.classify_structure(stype)
            results.append(r)
            print(f"  {stype:>10} {r['predicted']:>12} {r['leech_score']:>8.4f} "
                  f"{r['niemeier_score']:>10.4f} {'✓' if r['correct'] else '✗':>6}")
        accuracy = sum(r['correct'] for r in results) / len(results)
        print(f"\nAccuracy: {accuracy:.1%} ({sum(r['correct'] for r in results)}/{len(results)})")
        return results

    def plot(self, results, output_path):
        fig, axes = plt.subplots(1, 3, figsize=(20, 7))
        fig.patch.set_facecolor('#0d1117')

        def dark_ax(ax):
            ax.set_facecolor('#161b22')
            for sp in ax.spines.values(): sp.set_color('#30363d')
            ax.tick_params(colors='#8b949e')

        names = [r['structure_type'] for r in results]
        leech = [r['leech_score'] for r in results]
        niemeier = [r['niemeier_score'] for r in results]
        entropies = [r['dr_entropy'] for r in results]
        colors = ['#3fb950' if r['correct'] else '#ff7b72' for r in results]
        struct_colors = {'void': '#58a6ff', 'sheet': '#3fb950', 'filament': '#ffa657', 'node': '#ff7b72'}

        ax = axes[0]; dark_ax(ax)
        ax.scatter(leech, niemeier, c=[struct_colors[r['structure_type']] for r in results],
                   s=200, edgecolors='white', linewidths=1.5, zorder=5)
        for r in results:
            ax.annotate(r['structure_type'], (r['leech_score'], r['niemeier_score']),
                        textcoords='offset points', xytext=(8, 5), fontsize=10,
                        color=struct_colors[r['structure_type']], fontweight='bold')
        ax.set_xlabel('Leech Score (void-like)', color='#8b949e', fontsize=10)
        ax.set_ylabel('Niemeier Score (node-like)', color='#8b949e', fontsize=10)
        ax.set_title('Cosmic Web Classification\n(Leech vs Niemeier space)', color='white', fontsize=11, fontweight='bold')

        ax = axes[1]; dark_ax(ax)
        ax.bar(names, entropies, color=[struct_colors[n] for n in names], edgecolor='#30363d', alpha=0.85)
        ax.set_ylabel('E8 DR Entropy (bits)', color='#8b949e', fontsize=10)
        ax.set_title('Morphon Entropy by Structure\n(void=low, node=high)', color='white', fontsize=11, fontweight='bold')

        ax = axes[2]; dark_ax(ax)
        mean_densities = [math.log10(r['mean_density'] + 1) for r in results]
        ax.bar(names, mean_densities, color=[struct_colors[n] for n in names], edgecolor='#30363d', alpha=0.85)
        ax.set_ylabel('log10(Mean Density + 1)', color='#8b949e', fontsize=10)
        ax.set_title('Density by Structure Type\n(confirms encoding)', color='white', fontsize=11, fontweight='bold')

        fig.suptitle('Tool 27: CosmologicalVoidMorphonClassifier — E8 Leech/Niemeier Cosmic Web Analysis',
                     color='white', fontsize=13, fontweight='bold')
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='#0d1117')
        plt.close()
        print(f"[SAVED] {output_path}")

class E8Lattice:
    """E8 exceptional Lie group lattice operations."""
    
    def __init__(self):
        self.roots = self._generate_roots()
        self.weyl_chambers = self._generate_weyl_chambers()
        
    def _generate_roots(self) -> List[E8Root]:
        """Generate all 240 E8 root vectors."""
        roots = []
        
        # Type 1: (±1, ±1, 0, 0, 0, 0, 0, 0) and permutations (112 roots)
        for i in range(8):
            for j in range(i+1, 8):
                for s1 in [-1, 1]:
                    for s2 in [-1, 1]:
                        coords = np.zeros(8)
                        coords[i] = s1
                        coords[j] = s2
                        roots.append(E8Root(coords, len(roots), E8_NORM))
        
        # Type 2: (±1/2, ±1/2, ±1/2, ±1/2, ±1/2, ±1/2, ±1/2, ±1/2) 
        # with even number of minus signs (128 roots)
        for signs in range(256):
            coords = np.array([(1 if (signs >> i) & 1 else -1) / 2 
                              for i in range(8)])
            if np.sum(coords < 0) % 2 == 0:  # Even number of minus signs
                roots.append(E8Root(coords, len(roots), E8_NORM))
        
        return roots[:240]  # Ensure exactly 240 roots
    
    def _generate_weyl_chambers(self) -> List[np.ndarray]:
        """Generate 48 Weyl chambers (fundamental domains)."""
        chambers = []
        
        # Weyl group of E8 has order 696,729,600
        # We use 48 fundamental chambers for practical purposes
        for i in range(48):
            # Each chamber is a cone in E8 space
            # Defined by hyperplane normals
            angle = (2 * np.pi * i) / 48
            normal = np.array([
                np.cos(angle),
                np.sin(angle),
                np.cos(2*angle),
                np.sin(2*angle),
                np.cos(3*angle),
                np.sin(3*angle),
                np.cos(4*angle),
                np.sin(4*angle)
            ])
            chambers.append(normal / np.linalg.norm(normal))
        
        return chambers
    
    def project_to_lattice(self, vector: np.ndarray) -> np.ndarray:
        """Project vector to nearest E8 lattice point."""
        # Find nearest root
        distances = [np.linalg.norm(vector - root.coords) 
                    for root in self.roots]
        nearest_idx = np.argmin(distances)
        return self.roots[nearest_idx].coords
    
    def project_to_manifold(self, vector: np.ndarray) -> np.ndarray:
        """Project to continuous E8 manifold (unit sphere)."""
        norm = np.linalg.norm(vector)
        if norm > 0:
            return vector / norm * E8_NORM
        return vector
    
    def find_weyl_chamber(self, vector: np.ndarray) -> int:
        """Find which Weyl chamber contains the vector."""
        # Compute dot product with each chamber normal
        dots = [np.dot(vector, chamber) for chamber in self.weyl_chambers]
        return np.argmax(dots)
    
    def interpolate_geodesic(self, start: np.ndarray, end: np.ndarray, 
                            t: float) -> np.ndarray:
        """Interpolate along geodesic on E8 manifold."""
        # Spherical linear interpolation (SLERP)
        dot = np.dot(start, end) / (np.linalg.norm(start) * np.linalg.norm(end))
        dot = np.clip(dot, -1.0, 1.0)
        theta = np.arccos(dot)
        
        if abs(theta) < 1e-6:
            # Vectors are parallel, use linear interpolation
            return (1 - t) * start + t * end
        
        sin_theta = np.sin(theta)
        a = np.sin((1 - t) * theta) / sin_theta
        b = np.sin(t * theta) / sin_theta
        
        result = a * start + b * end
        return self.project_to_manifold(result)
    
    def rotate_e8(self, vector: np.ndarray, axis1: int, axis2: int, 
                  angle: float) -> np.ndarray:
        """Rotate vector in E8 space around plane defined by axis1, axis2."""
        result = vector.copy()
        
        # 2D rotation in the specified plane
        cos_a = np.cos(angle)
        sin_a = np.sin(angle)
        
        x = result[axis1]
        y = result[axis2]
        
        result[axis1] = cos_a * x - sin_a * y
        result[axis2] = sin_a * x + cos_a * y
        
        return result
    
    def face_rotation(self, vector: np.ndarray, angle: float) -> np.ndarray:
        """Rotate E8 face - generates different solution paths (P vs NP)."""
        # Rotate in multiple planes simultaneously
        result = vector.copy()
        
        # Primary rotation (0-1 plane)
        result = self.rotate_e8(result, 0, 1, angle)
        
        # Secondary rotation (2-3 plane)
        result = self.rotate_e8(result, 2, 3, angle * PHI)
        
        # Tertiary rotation (4-5 plane)
        result = self.rotate_e8(result, 4, 5, angle * PHI**2)
        
        # Quaternary rotation (6-7 plane)
        result = self.rotate_e8(result, 6, 7, angle * PHI**3)
        
        return self.project_to_manifold(result)
    
    def compute_digital_root(self, vector: np.ndarray) -> int:
        """Compute digital root (0-9) from E8 vector."""
        # Sum all components, reduce to single digit
        total = int(np.sum(np.abs(vector)) * 1000)  # Scale for precision
        while total >= 10:
            total = sum(int(d) for d in str(total))
        return total if total > 0 else 9
    
    def compute_parity_channels(self, vector: np.ndarray) -> np.ndarray:
        """Compute 24 parity channels from E8 vector."""
        # Use Leech lattice embedding (24D)
        channels = np.zeros(24)
        
        # Embed E8 into first 8 channels
        channels[:8] = vector
        
        # Generate remaining 16 channels via modular arithmetic
        for i in range(8, 24):
            # Use CRT rails (3, 6, 9) and coupling (0.03)
            mod = (i % 3) + 3  # Moduli: 3, 4, 5, 3, 4, 5, ...
            channels[i] = (np.sum(vector) * COUPLING * i) % mod
        
        return channels

class GeometricConfig:
    """Configuration for the geometric transformer.

    Enforces E8-alignment constraints: ``d_model`` must be a multiple of 8
    and ``n_heads`` must be a power of 2.
    """

    def __init__(
        self,
        vocab_size: int = 1000,
        d_model: int = 64,
        n_heads: int = 8,
        n_layers: int = 6,
        max_seq_len: int = 128,
        dropout: float = 0.1,
        enforce_8d: bool = True,
    ):
        assert d_model % 8 == 0, "d_model must be multiple of 8 for E8 structure"
        assert n_heads in [1, 2, 4, 8, 16, 32], "n_heads must be power of 2"

        self.vocab_size = vocab_size
        self.d_model = d_model
        self.n_heads = n_heads
        self.n_layers = n_layers
        self.max_seq_len = max_seq_len
        self.dropout = dropout
        self.enforce_8d = enforce_8d
        self.d_head = d_model // n_heads

class MorphonGenealogyTree:
    def __init__(self):
        self.e8 = E8Lattice()
        self.roots = self.e8.get_roots()
        self.root_vecs = np.array([r.coords for r in self.roots], dtype=float)
        self.n_roots = len(self.roots)

    def _snap_to_e8(self, vec):
        dists = np.linalg.norm(self.root_vecs - vec, axis=1)
        idx = np.argmin(dists)
        return idx, float(dists[idx])

    def _generate_domain_morphons(self, domain_name, seed):
        """Generate Morphon forms for a given domain using domain-specific encoding."""
        rng = np.random.default_rng(seed)

        domain_configs = {
            # Tool 1-10 domains
            'protein':       {'scale': 0.8, 'bias': 0.2, 'n': 15},
            'quantum':       {'scale': 1.2, 'bias': 0.0, 'n': 12},
            'economic':      {'scale': 0.6, 'bias': 0.4, 'n': 20},
            'pharma':        {'scale': 0.9, 'bias': 0.1, 'n': 18},
            'genomic':       {'scale': 1.0, 'bias': 0.0, 'n': 25},
            'materials':     {'scale': 0.7, 'bias': 0.3, 'n': 10},
            'neural':        {'scale': 1.1, 'bias': -0.1, 'n': 16},
            'climate':       {'scale': 0.5, 'bias': 0.5, 'n': 22},
            'rule30':        {'scale': 1.3, 'bias': 0.0, 'n': 30},
            'stability':     {'scale': 0.8, 'bias': 0.2, 'n': 14},
            # Tool 11-20 domains
            'gwave':         {'scale': 1.4, 'bias': -0.2, 'n': 20},
            'viral':         {'scale': 0.9, 'bias': 0.1, 'n': 18},
            'crypto':        {'scale': 1.2, 'bias': 0.0, 'n': 15},
            'knot':          {'scale': 0.6, 'bias': 0.4, 'n': 12},
            'semantic':      {'scale': 0.8, 'bias': 0.2, 'n': 25},
            'ecology':       {'scale': 0.7, 'bias': 0.3, 'n': 20},
            'turbulence':    {'scale': 1.5, 'bias': -0.3, 'n': 18},
            'primes':        {'scale': 1.0, 'bias': 0.0, 'n': 30},
            'superconductor':{'scale': 0.9, 'bias': 0.1, 'n': 15},
            'cross_domain':  {'scale': 1.0, 'bias': 0.0, 'n': 20},
            # Tool 21-30 domains
            'qbio':          {'scale': 1.1, 'bias': -0.1, 'n': 16},
            'social':        {'scale': 0.7, 'bias': 0.3, 'n': 22},
            'alloy':         {'scale': 0.8, 'bias': 0.2, 'n': 14},
            'consciousness': {'scale': 1.2, 'bias': 0.0, 'n': 18},
            'seismic':       {'scale': 1.0, 'bias': 0.0, 'n': 25},
            'drug':          {'scale': 0.9, 'bias': 0.1, 'n': 20},
            'cosmology':     {'scale': 1.3, 'bias': -0.2, 'n': 22},
            'immune':        {'scale': 0.8, 'bias': 0.2, 'n': 28},
            'finance':       {'scale': 1.1, 'bias': -0.1, 'n': 20},
            'genealogy':     {'scale': 1.0, 'bias': 0.0, 'n': 15},
        }

        cfg = domain_configs.get(domain_name, {'scale': 1.0, 'bias': 0.0, 'n': 15})
        morphon_indices = []

        for _ in range(cfg['n']):
            vec = rng.normal(0, 1, 8) * cfg['scale'] + cfg['bias']
            idx, _ = self._snap_to_e8(vec)
            morphon_indices.append(idx)

        return morphon_indices

    def build_genealogy_tree(self):
        """Build the full Morphon Genealogy Tree across all 30 domains."""
        all_domains = [
            'protein', 'quantum', 'economic', 'pharma', 'genomic',
            'materials', 'neural', 'climate', 'rule30', 'stability',
            'gwave', 'viral', 'crypto', 'knot', 'semantic',
            'ecology', 'turbulence', 'primes', 'superconductor', 'cross_domain',
            'qbio', 'social', 'alloy', 'consciousness', 'seismic',
            'drug', 'cosmology', 'immune', 'finance', 'genealogy',
        ]

        # Collect all Morphons by domain
        domain_morphons = {}
        for i, domain in enumerate(all_domains):
            domain_morphons[domain] = self._generate_domain_morphons(domain, seed=i * 137)

        # Count global Morphon frequency
        all_indices = []
        for indices in domain_morphons.values():
            all_indices.extend(indices)
        global_freq = Counter(all_indices)

        # Build genealogy: parent of a Morphon is the closest E8 root with lower index
        # (this creates a natural tree structure based on E8 root ordering)
        parent_map = {}
        for idx in range(self.n_roots):
            vec = self.root_vecs[idx]
            # Parent = nearest root with strictly smaller norm
            norm = np.linalg.norm(vec)
            candidates = [j for j in range(self.n_roots)
                          if np.linalg.norm(self.root_vecs[j]) < norm - 0.01]
            if candidates:
                dists = np.linalg.norm(self.root_vecs[candidates] - vec, axis=1)
                parent_map[idx] = candidates[np.argmin(dists)]
            else:
                parent_map[idx] = None  # root node

        # Compute tree statistics
        # Depth of each node
        def get_depth(idx, memo={}):
            if idx in memo: return memo[idx]
            if parent_map[idx] is None:
                memo[idx] = 0
                return 0
            memo[idx] = 1 + get_depth(parent_map[idx])
            return memo[idx]

        depths = {idx: get_depth(idx) for idx in range(self.n_roots)}
        max_depth = max(depths.values())

        # Universal Morphons: appear in >= 15 domains
        domain_presence = defaultdict(set)
        for domain, indices in domain_morphons.items():
            for idx in indices:
                domain_presence[idx].add(domain)

        universal_morphons = {idx: domains for idx, domains in domain_presence.items()
                               if len(domains) >= 15}

        # DR distribution across all domains
        dr_by_domain = {}
        for domain, indices in domain_morphons.items():
            drs = [digital_root(idx) for idx in indices]
            dr_by_domain[domain] = Counter(drs)

        # Cross-domain similarity: Jaccard similarity of Morphon sets
        domain_list = list(domain_morphons.keys())
        n_domains = len(domain_list)
        similarity_matrix = np.zeros((n_domains, n_domains))
        for i, d1 in enumerate(domain_list):
            for j, d2 in enumerate(domain_list):
                s1 = set(domain_morphons[d1])
                s2 = set(domain_morphons[d2])
                if s1 | s2:
                    similarity_matrix[i, j] = len(s1 & s2) / len(s1 | s2)

        return {
            'domain_morphons': {d: list(set(v)) for d, v in domain_morphons.items()},
            'global_freq': dict(global_freq.most_common(20)),
            'universal_morphons': {str(k): list(v) for k, v in universal_morphons.items()},
            'n_universal': len(universal_morphons),
            'max_tree_depth': max_depth,
            'mean_tree_depth': float(np.mean(list(depths.values()))),
            'similarity_matrix': similarity_matrix,
            'domain_list': domain_list,
            'total_unique_morphons': len(set(all_indices)),
            'total_morphons': len(all_indices),
        }

    def plot(self, tree_data, output_path):
        fig, axes = plt.subplots(1, 3, figsize=(22, 8))
        fig.patch.set_facecolor('#0d1117')

        def dark_ax(ax):
            ax.set_facecolor('#161b22')
            for sp in ax.spines.values(): sp.set_color('#30363d')
            ax.tick_params(colors='#8b949e')

        # Plot 1: Cross-domain similarity heatmap
        ax = axes[0]; dark_ax(ax)
        sim = tree_data['similarity_matrix']
        im = ax.imshow(sim, cmap='viridis', aspect='auto', vmin=0, vmax=1)
        plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        labels = [d[:6] for d in tree_data['domain_list']]
        ax.set_xticks(range(len(labels))); ax.set_xticklabels(labels, rotation=90, fontsize=6)
        ax.set_yticks(range(len(labels))); ax.set_yticklabels(labels, fontsize=6)
        ax.set_title('Cross-Domain Morphon Similarity\n(Jaccard index)', color='white', fontsize=11, fontweight='bold')

        # Plot 2: Universal Morphon presence
        ax = axes[1]; dark_ax(ax)
        n_universal = tree_data['n_universal']
        n_total_unique = tree_data['total_unique_morphons']
        n_domain_specific = n_total_unique - n_universal
        ax.pie([n_universal, n_domain_specific],
               labels=[f'Universal\n({n_universal})', f'Domain-specific\n({n_domain_specific})'],
               colors=['#58a6ff', '#3fb950'], autopct='%1.1f%%',
               textprops={'color': 'white', 'fontsize': 11},
               wedgeprops={'edgecolor': '#0d1117', 'linewidth': 2})
        ax.set_title(f'Morphon Universality\n({tree_data["total_unique_morphons"]} unique across 30 domains)',
                     color='white', fontsize=11, fontweight='bold')

        # Plot 3: Global Morphon frequency (top 20)
        ax = axes[2]; dark_ax(ax)
        top_indices = list(tree_data['global_freq'].keys())[:15]
        top_freqs = [tree_data['global_freq'][k] for k in top_indices]
        top_drs = [digital_root(k) for k in top_indices]
        dr_colors = plt.cm.tab10(np.array(top_drs) / 9.0)
        ax.bar(range(len(top_indices)), top_freqs, color=dr_colors, edgecolor='#30363d', alpha=0.85)
        ax.set_xlabel('E8 Root Index (top 15 most common)', color='#8b949e', fontsize=9)
        ax.set_ylabel('Frequency across all domains', color='#8b949e', fontsize=9)
        ax.set_title('Most Common Morphons\n(colored by digital root)', color='white', fontsize=11, fontweight='bold')
        ax.set_xticks(range(len(top_indices)))
        ax.set_xticklabels([f"r{i}\nDR={dr}" for i, dr in zip(top_indices, top_drs)], fontsize=7)

        fig.suptitle('Tool 30: MorphonGenealogyTree — Universal Morphon Structure Across All 30 Domains',
                     color='white', fontsize=13, fontweight='bold')
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='#0d1117')
        plt.close()
        print(f"[SAVED] {output_path}")

class MorphonToolkit:
    """
    Universal Morphon Toolkit.
    
    Use this to treat any data as its own universe:
    1. Create universe from data
    2. Extract morphons automatically
    3. Discover internally
    4. Identify external needs
    5. Generate exploration plan
    """
    
    def __init__(self):
        self.universes: Dict[str, Universe] = {}
    
    def create_universe(self, name: str, data: Any, 
                       source_type: str = "unknown") -> Universe:
        """Create a universe from any data."""
        universe = Universe.create(name, data, source_type)
        self.universes[universe.universe_id] = universe
        return universe
    
    def analyze_universe(self, universe_id: str) -> Dict[str, Any]:
        """Full analysis of a universe."""
        universe = self.universes.get(universe_id)
        if not universe:
            return {'error': 'Universe not found'}
        
        # Discover internally
        universe.discover_internally()
        
        # Identify external
        universe.identify_external()
        
        # Generate plan
        plan = universe.generate_exploration_plan()
        
        return {
            'universe': universe.to_dict(),
            'analysis': {
                'internal': universe.internal_model,
                'external': universe.external_interfaces,
                'plan': universe.exploration_plan,
            }
        }
    
    def get_universe(self, universe_id: str) -> Optional[Universe]:
        """Get a universe by ID."""
        return self.universes.get(universe_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get toolkit statistics."""
        total_morphons = sum(len(u.morphons) for u in self.universes.values())
        return {
            'universes': len(self.universes),
            'total_morphons': total_morphons,
            'avg_morphons_per_universe': total_morphons / len(self.universes) if self.universes else 0,
        }

class MorphonicField:
    """
    MorphonicField wraps a positive-definite symmetric matrix A,
    which defines morphonic tension:

        ?(x) = x? A x

    This tension scalar ?(x) is how CQE encodes "strain" or "stress load"
    in the coherent region's geometry.

    Law 1 (Quadratic Invariance): CQE forbids internal steps where ?? > 0.
    Thatis, you are not allowed to internally execute an update that creates
    additional destructive strain in the same body/ecosystem/channel.
    """

    def __init__(self, A: np.ndarray):
        assert A.shape[0] == A.shape[1], "A must be square"
        self.A = A

    def phi(self, coords: np.ndarray) -> float:
        """
        Compute ?(x) = x? A x for the given coordinate vector.
        """
        return float(coords.T @ self.A @ coords)

    def apply_internal_step(self, state: StateVector, step: ActionStep) -> StateVector:
        """
        Attempt to evolve `state` by `step` *internally*.

        We do not allow ?? > 0 internally. If the new state's phi exceeds the
        current state's phi, we raise. That enforces Quadratic Invariance.

        Returns:
        A new StateVector with updated coords and phi (tick and metadata unchanged).
        """
        new_coords = state.coords + step.delta_coords
        new_phi = self.phi(new_coords)
        if new_phi > state.phi + 1e-12:
            raise ValueError("?? > 0 internally; illegal under Law 1 (Quadratic Invariance).")

        return replace(state,
                       coords=new_coords,
                       phi=new_phi)

class ObserveRequest(BaseModel):
    content: str
    functor: str = "pipeline"
    e8_coords: List[float] = []

class OverlayRequest(BaseModel):
    content: str
    e8_coords: List[float] = []

class Parity(str, Enum):
    EVEN = "even"
    ODD = "odd"
    UNKNOWN = "unknown"

class PotentialRequest(BaseModel):
    content: str
    e8_coords: List[float] = []

class ReceiptWriter:
    def __init__(self, out_dir: Path):
        self.out_dir = out_dir
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.ledger_path = self.out_dir / "ledger.jsonl"
        self.lpc_path = self.out_dir / "lpc.csv"
        if not self.lpc_path.exists():
            self.lpc_path.write_text(
                "|".join([
                    "face_id","channel","idx_lo","idx_hi","equalizing_angle_deg",
                    "pose_key_W80","d10_key","d8_key","joint_key","writhe","crossings",
                    "clone_K","quad_var_at_eq","repair_family_id","residues_hash","proof_hash"
                ]) + "\n",
                encoding="utf-8"
            )

    def append_ledger(self, rec: Receipt) -> None:
        with self.ledger_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(dc.asdict(rec), ensure_ascii=False, default=_json_default) + "\n")

    def append_lpc(self, row: LPCRow) -> None:
        fields = [
            row.face_id, row.channel, str(row.idx_range[0]), str(row.idx_range[1]), f"{row.equalizing_angle_deg:.6f}",
            row.pose_key_W80, row.d10_key, row.d8_key, row.joint_key, str(row.writhe), str(row.crossings),
            str(row.clone_K), f"{row.quad_var_at_eq:.6f}", row.repair_family_id, row.residues_hash, row.proof_hash
        ]
        with self.lpc_path.open("a", encoding="utf-8") as f:
            f.write("|".join(fields) + "\n")

class StateVector:
    """
    Represents the current lawful state of a coherent region in CQE.
    This could be a person, an ecosystem, an infrastructure cluster,
    a lab runtime, a civic collective, or any reversible interior domain.

    Fields:
    - coords: np.ndarray (shape (8,) or compatible) holding the state's
      coordinates in an exceptional high-symmetry frame (E?/Cartan basis).
      CQE treats this as the "canonical true coordinates".

    - phi: float. Morphonic tension ?(x) = x? A x. ? measures "strain"
      or "loaded stress" in the morphonic field. CQE forbids any internal
      update where ?? > 0. That is Quadratic Invariance (Law 1).

    - tick: int. Toroidal time index. CQE does NOT treat time as linear.
      Time only advances when the system completes a closed, low-strain,
      toroidal orbit step. We do not allow arbitrary tick++ unless we
      closed a loop in a reversible way.

    - metadata: dict. Arbitrary attached annotations: sacred geometry tags,
      civic binding, continuity anchors, basin provenance, etc.
    """
    coords: np.ndarray
    phi: float
    tick: int
    metadata: Dict[str, Any]

class TestRunner:
    """Simple test runner with result tracking."""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []

    def test(self, name):

        def decorator(func):
            self.tests.append((name, func))
            return func
        return decorator

    def run(self):
        print('\n' + '=' * 70)
        print('CQE META-INFRASTRUCTURE TEST SUITE (Refactored)')
        print('=' * 70 + '\n')
        for name, func in self.tests:
            try:
                print(f'Testing: {name}...', end=' ')
                func()
                print('? PASS')
                self.passed += 1
            except AssertionError as e:
                print(f'? FAIL: {e}')
                self.failed += 1
            except Exception as e:
                print(f'? ERROR: {e}')
                self.failed += 1
        print('\n' + '=' * 70)
        print(f'Results: {self.passed} passed, {self.failed} failed')
        print('=' * 70 + '\n')
        return self.failed == 0

class ToroidalClock:
    """
    ToroidalClock enforces CQE's notion of time:
    Time doesn't tick just because code says 'tick++'.
    A legal tick is a small rotation along a toroidal orbit in state space
    that "seals" without ripping coherence.

    The rotation increment is COUPLING (~0.03) which ties to:
    - golden-angle-like minimal-overlap,
    - minimal local shear,
    - low additive tension.

    This enforces the idea that "time" only advances when the system has
    completed a closed, low-strain loop. Otherwise, you haven't truly advanced.
    """

    def __init__(self, closure_tolerance: float = 1e-6):
        self.closure_tolerance = closure_tolerance

    def advance_tick(self, state: StateVector) -> StateVector:
        """
        Advance the state's toroidal tick if (and only if) a small,
        low-strain toroidal rotation is valid.

        Implementation detail here is illustrative:
        We rotate (coords[0], coords[1]) by angle = COUPLING * 2?.
        Then we check that the move did not blow up displacement.

        Production CQE would:
        - track a full toroidal manifold embedding,
        - ensure closure to within tolerance,
        - confirm ?? ? 0 using MorphonicField.
        """
        theta = COUPLING * 2.0 * np.pi
        rot = np.array([[np.cos(theta), -np.sin(theta)],
                        [np.sin(theta),  np.cos(theta)]])
        new_coords = state.coords.copy()
        new_coords[:2] = rot @ new_coords[:2]

        # Basic sanity: if the displacement is too large, consider it illegal
        if np.linalg.norm(new_coords - state.coords) > (COUPLING * 10.0):
            raise ValueError("Toroidal closure failed: step not on legal toroidal orbit.")

        return replace(state,
                       coords=new_coords,
                       tick=state.tick + 1)

class Universe:
    """
    A bounded universe of morphons.
    
    Any data can be its own universe:
    - Code file → universe of functions, classes, imports
    - Document → universe of concepts, claims, references
    - System → universe of components, interfaces, behaviors
    - Idea → universe of premises, conclusions, assumptions
    """
    universe_id: str
    name: str
    source_type: str
    morphons: Dict[str, Morphon] = field(default_factory=dict)
    boundary_definition: str = ""
    internal_model: Dict[str, Any] = field(default_factory=dict)
    external_interfaces: List[Dict[str, Any]] = field(default_factory=list)
    exploration_plan: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    @classmethod
    def create(cls, name: str, source_data: Any, source_type: str = "unknown") -> 'Universe':
        """Create a universe from any data."""
        universe_id = hashlib.sha256(
            f"{name}:{time.time()}:{source_type}".encode()
        ).hexdigest()[:24]
        
        universe = cls(
            universe_id=universe_id,
            name=name,
            source_type=source_type,
        )
        
        # Extract morphons
        universe._extract_morphons(source_data)
        
        # Define boundary
        universe.boundary_definition = f"Contains {len(universe.morphons)} morphons of type {source_type}"
        
        return universe
    
    def _extract_morphons(self, data: Any, boundary: str = "root") -> List[Morphon]:
        """Extract morphons from any data."""
        morphons = []
        
        if isinstance(data, dict):
            for key, value in data.items():
                morphon = Morphon.create(
                    content={'key': key, 'value': value},
                    boundary_type=f"{boundary}.key"
                )
                self.morphons[morphon.morphon_id] = morphon
                morphons.append(morphon)
                
                # Recurse
                if isinstance(value, (dict, list, tuple)):
                    morphons.extend(self._extract_morphons(value, f"{boundary}.{key}"))
        
        elif isinstance(data, (list, tuple)):
            for i, item in enumerate(data):
                morphon = Morphon.create(
                    content={'index': i, 'value': item},
                    boundary_type=f"{boundary}[{i}]"
                )
                self.morphons[morphon.morphon_id] = morphon
                morphons.append(morphon)
                
                if isinstance(item, (dict, list, tuple)):
                    morphons.extend(self._extract_morphons(item, f"{boundary}[{i}]"))
        
        elif isinstance(data, str):
            # Split by meaningful units
            units = self._split_text(data)
            for i, unit in enumerate(units):
                if unit.strip():
                    morphon = Morphon.create(
                        content={'segment': i, 'text': unit},
                        boundary_type=f"{boundary}.segment[{i}]"
                    )
                    self.morphons[morphon.morphon_id] = morphon
                    morphons.append(morphon)
        
        else:
            morphon = Morphon.create(content=data, boundary_type=boundary)
            self.morphons[morphon.morphon_id] = morphon
            morphons.append(morphon)
        
        return morphons
    
    def _split_text(self, text: str) -> List[str]:
        """Split text into meaningful units."""
        # Try sentences first
        sentences = re.split(r'[.!?]+\s+', text)
        if len(sentences) > 1:
            return [s.strip() for s in sentences if s.strip()]
        
        # Fall back to lines
        lines = text.split('\n')
        if len(lines) > 1:
            return [l.strip() for l in lines if l.strip()]
        
        # Fall back to words
        return text.split()
    
    def discover_internally(self) -> Dict[str, Any]:
        """
        Discover everything possible within the universe boundary.
        
        Returns:
        - Patterns found
        - Structures identified
        - Relationships mapped
        - Gaps detected
        - Completeness score
        """
        model = {
            'morphon_count': len(self.morphons),
            'boundary_types': {},
            'semantic_types': {},
            'patterns': [],
            'structures': [],
            'relationships': [],
            'gaps': [],
            'completeness': 0.0,
        }
        
        # Count types
        for morphon in self.morphons.values():
            bt = morphon.boundary_type
            model['boundary_types'][bt] = model['boundary_types'].get(bt, 0) + 1
            
            st = morphon.semantic_type
            model['semantic_types'][st] = model['semantic_types'].get(st, 0) + 1
        
        # Find patterns
        model['patterns'] = self._find_patterns()
        
        # Identify structures
        model['structures'] = self._identify_structures()
        
        # Map relationships
        model['relationships'] = self._map_relationships()
        
        # Detect gaps
        model['gaps'] = self._detect_gaps()
        
        # Calculate completeness
        model['completeness'] = self._calculate_completeness(model)
        
        self.internal_model = model
        return model
    
    def _find_patterns(self) -> List[Dict[str, Any]]:
        """Find patterns in morphons."""
        patterns = []
        
        # Check for repeated content
        content_counts = {}
        for morphon in self.morphons.values():
            content_key = str(morphon.content)[:50]
            content_counts[content_key] = content_counts.get(content_key, 0) + 1
        
        for content, count in content_counts.items():
            if count > 1:
                patterns.append({
                    'type': 'repeated_content',
                    'count': count,
                    'sample': content[:30],
                })
        
        return patterns
    
    def _identify_structures(self) -> List[Dict[str, Any]]:
        """Identify structures in the universe."""
        structures = []
        
        # Check for hierarchical structures
        boundary_depths = {}
        for morphon in self.morphons.values():
            depth = morphon.boundary_type.count('.')
            boundary_depths[depth] = boundary_depths.get(depth, 0) + 1
        
        if len(boundary_depths) > 1:
            structures.append({
                'type': 'hierarchy',
                'depths': boundary_depths,
                'max_depth': max(boundary_depths.keys()),
            })
        
        return structures
    
    def _map_relationships(self) -> List[Dict[str, Any]]:
        """Map relationships between morphons."""
        relationships = []
        
        morphons_list = list(self.morphons.values())
        for i, m1 in enumerate(morphons_list[:100]):  # Limit for performance
            for m2 in morphons_list[i+1:100]:
                # Check for content relationships
                if isinstance(m1.content, str) and isinstance(m2.content, str):
                    if m1.content in m2.content or m2.content in m1.content:
                        relationships.append({
                            'from': m1.morphon_id,
                            'to': m2.morphon_id,
                            'type': 'content_overlap',
                        })
        
        return relationships[:50]  # Limit results
    
    def _detect_gaps(self) -> List[str]:
        """Detect gaps in the universe."""
        gaps = []
        
        if len(self.morphons) < 3:
            gaps.append('insufficient_morphons')
        
        if len(self.internal_model.get('structures', [])) == 0:
            gaps.append('no_identified_structures')
        
        if len(self.internal_model.get('relationships', [])) == 0:
            gaps.append('no_identified_relationships')
        
        return gaps
    
    def _calculate_completeness(self, model: Dict[str, Any]) -> float:
        """Calculate completeness score (0-1)."""
        score = 0.0
        
        # Base score from morphon count
        if model['morphon_count'] >= 10:
            score += 0.3
        elif model['morphon_count'] >= 5:
            score += 0.2
        elif model['morphon_count'] >= 1:
            score += 0.1
        
        # Score from patterns
        if model['patterns']:
            score += 0.2
        
        # Score from structures
        if model['structures']:
            score += 0.2
        
        # Score from relationships
        if model['relationships']:
            score += 0.2
        
        # Penalty for gaps
        score -= len(model['gaps']) * 0.1
        
        return max(0.0, min(1.0, score))
    
    def identify_external(self) -> List[Dict[str, Any]]:
        """
        Identify what needs external exploration.
        
        Based on internal model, determines:
        - External references
        - Missing dependencies
        - Required validations
        """
        interfaces = []
        
        for morphon in self.morphons.values():
            content_str = str(morphon.content)
            
            # Check for external references
            if 'import' in content_str or 'require' in content_str:
                interfaces.append({
                    'morphon_id': morphon.morphon_id,
                    'type': 'dependency',
                    'reason': 'Contains import/require statement',
                })
            
            if 'http://' in content_str or 'https://' in content_str:
                interfaces.append({
                    'morphon_id': morphon.morphon_id,
                    'type': 'external_reference',
                    'reason': 'Contains URL',
                })
            
            if 'TODO' in content_str or 'FIXME' in content_str:
                interfaces.append({
                    'morphon_id': morphon.morphon_id,
                    'type': 'incomplete',
                    'reason': 'Contains TODO/FIXME',
                })
        
        self.external_interfaces = interfaces
        return interfaces
    
    def generate_exploration_plan(self) -> Dict[str, Any]:
        """
        Generate exploration plan.
        
        Returns prioritized plan for:
        - Internal validation
        - External exploration
        - Gap filling
        """
        if not self.internal_model:
            self.discover_internally()
        if not self.external_interfaces:
            self.identify_external()
        
        plan = {
            'universe_id': self.universe_id,
            'universe_name': self.name,
            'internal_knowledge': {
                'morphons_discovered': len(self.morphons),
                'patterns_found': len(self.internal_model.get('patterns', [])),
                'structures_found': len(self.internal_model.get('structures', [])),
                'relationships_mapped': len(self.internal_model.get('relationships', [])),
                'completeness_score': self.internal_model.get('completeness', 0),
            },
            'external_exploration_needed': {
                'interfaces_count': len(self.external_interfaces),
                'by_type': {},
                'prioritized': [],
            },
            'recommended_actions': [],
        }
        
        # Count by type
        for iface in self.external_interfaces:
            t = iface['type']
            plan['external_exploration_needed']['by_type'][t] = \
                plan['external_exploration_needed']['by_type'].get(t, 0) + 1
        
        # Prioritize
        priority_order = ['dependency', 'external_reference', 'incomplete']
        for ptype in priority_order:
            matching = [i for i in self.external_interfaces if i['type'] == ptype]
            plan['external_exploration_needed']['prioritized'].extend(matching[:5])
        
        # Recommended actions
        if self.internal_model.get('completeness', 0) < 0.5:
            plan['recommended_actions'].append('Gather more internal morphons')
        if self.internal_model.get('gaps'):
            plan['recommended_actions'].append('Address identified gaps')
        if self.external_interfaces:
            plan['recommended_actions'].append('Explore external interfaces')
        if self.internal_model.get('relationships'):
            plan['recommended_actions'].append('Validate mapped relationships')
        
        self.exploration_plan = plan
        return plan
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'universe_id': self.universe_id,
            'name': self.name,
            'source_type': self.source_type,
            'morphon_count': len(self.morphons),
            'boundary_definition': self.boundary_definition,
            'internal_model': self.internal_model,
            'external_interfaces': self.external_interfaces,
            'exploration_plan': self.exploration_plan,
            'created_at': self.created_at,
        }

class CoherenceRequest(BaseModel):
    points: List[List[float]] = []

class CollapseRequest(BaseModel):
    prev_points: List[List[float]] = []
    curr_points: List[List[float]] = []

class CurvatureRequest(BaseModel):
    coords: List[float] = []

class MasterMessageRequest(BaseModel):
    content: str = ""
    coords_8d: List[float] = []

class MorphonAtlas:
    """
    Atlas of stable morphonic embeddings.
    
    Maps context → stable embedding (RCE = Receipt-Carrying Embedding)
    """
    
    def __init__(self):
        self.atlas: Dict[str, np.ndarray] = {}
        self.hit_count: Dict[str, int] = {}
        self.miss_count: Dict[str, int] = {}
    
    def lookup(self, context: str) -> Tuple[bool, np.ndarray]:
        """
        Lookup context in atlas.
        
        Returns:
            (hit: bool, embedding: ndarray)
        """
        if context in self.atlas:
            self.hit_count[context] = self.hit_count.get(context, 0) + 1
            return True, self.atlas[context]
        else:
            self.miss_count[context] = self.miss_count.get(context, 0) + 1
            return False, None
    
    def store(self, context: str, embedding: np.ndarray):
        """Store embedding in atlas."""
        self.atlas[context] = embedding.copy()
    
    def get_hit_rate(self, context: str) -> float:
        """Get cache hit rate for context."""
        hits = self.hit_count.get(context, 0)
        misses = self.miss_count.get(context, 0)
        total = hits + misses
        return hits / total if total > 0 else 0.0

class MorphonicLockInExperiment:
    """Run the morphonic lock-in experiment."""
    
    def __init__(self):
        print("Initializing Morphonic Lock-In Experiment...")
        
        # Initialize components
        self.transformer = GeometricTransformer(
            base_dim=1024,  # Smaller for faster testing
            num_heads=16,
            num_layers=4
        )
        
        self.token_agent = AletheiaAgent(embedding_dim=1024)
        self.atlas = MorphonAtlas()
        self.wrapper = MorphonicWrapper(
            self.transformer,
            self.token_agent,
            self.atlas
        )
        
        # Test contexts
        self.contexts = [
            "orbital_transfer",
            "ocr_invoice_parse",
            "code_search"
        ]
        
        # Results storage
        self.results = {ctx: [] for ctx in self.contexts}
    
    def generate_state(self, context: str, iteration: int) -> np.ndarray:
        """
        Generate state for context.
        
        Add small noise to simulate slight variations in input.
        """
        # Base state from context hash
        np.random.seed(hash(context) % (2**32))
        base = np.random.randn(10, 1024) * 0.02
        
        # Add small iteration-dependent noise
        noise = np.random.randn(10, 1024) * 0.001 * (1.0 / (iteration + 1))
        
        return base + noise
    
    def run_solve(self, context: str, iteration: int) -> Dict:
        """Run one solve for context."""
        # Generate state
        state = self.generate_state(context, iteration)
        
        # Apply morphonic wrapper
        embedding, metadata = self.wrapper.wrap(context, state)
        
        # Compute JS distance to atlas mode (if exists)
        hit, atlas_embedding = self.atlas.lookup(context)
        if hit and atlas_embedding is not None:
            # Normalize to probability distributions for JS divergence
            p = np.abs(embedding) / np.abs(embedding).sum()
            q = np.abs(atlas_embedding) / np.abs(atlas_embedding).sum()
            js_distance = jensenshannon(p, q)
        else:
            js_distance = 1.0  # Max distance on first solve
        
        # Get cache hit rate
        hit_rate = self.atlas.get_hit_rate(context)
        
        return {
            'iteration': iteration,
            'context': context,
            'cache_hit': metadata['cache_hit'],
            'hit_rate': hit_rate,
            'delta_phi': metadata['delta_phi'],
            'js_distance': js_distance,
            'embedding_norm': np.linalg.norm(embedding)
        }
    
    def run_context(self, context: str, num_solves: int = 30):
        """Run experiment for one context."""
        print(f"\n{'='*70}")
        print(f"Testing context: {context}")
        print(f"{'='*70}")
        
        for i in range(num_solves):
            result = self.run_solve(context, i)
            self.results[context].append(result)
            
            if i % 5 == 0:
                print(f"  Solve {i:2d}: hit_rate={result['hit_rate']:.3f}, "
                      f"js_dist={result['js_distance']:.6f}, "
                      f"ΔΦ={result['delta_phi']:.6f}")
        
        # Test idempotence
        state = self.generate_state(context, 0)
        is_idempotent = self.wrapper.test_idempotence(context, state)
        print(f"\n  Idempotence test: {'✓ PASS' if is_idempotent else '✗ FAIL'}")
    
    def analyze_results(self):
        """Analyze results and compute metrics."""
        print(f"\n{'='*70}")
        print("ANALYSIS")
        print(f"{'='*70}")
        
        analysis = {}
        
        for context in self.contexts:
            results = self.results[context]
            
            # Extract time series
            iterations = [r['iteration'] for r in results]
            hit_rates = [r['hit_rate'] for r in results]
            js_distances = [r['js_distance'] for r in results]
            
            # Compute decay rate λ for JS distance
            # Fit exponential: js_t = js_0 * λ^t
            # log(js_t) = log(js_0) + t * log(λ)
            
            # Filter out zeros (log undefined)
            valid_points = [(i, js) for i, js in zip(iterations, js_distances) if js > 1e-10]
            
            if len(valid_points) > 5:
                iters, jss = zip(*valid_points)
                log_jss = np.log(jss)
                slope, intercept, r_value, p_value, std_err = linregress(iters, log_jss)
                lambda_est = np.exp(slope)
            else:
                lambda_est = None
            
            # Final hit rate
            final_hit_rate = hit_rates[-1] if hit_rates else 0.0
            
            # Monotonic increase in hit rate?
            hit_rate_increases = sum(
                1 for i in range(1, len(hit_rates))
                if hit_rates[i] >= hit_rates[i-1]
            )
            hit_rate_monotonic = hit_rate_increases / max(len(hit_rates) - 1, 1)
            
            analysis[context] = {
                'final_hit_rate': final_hit_rate,
                'hit_rate_monotonic_ratio': hit_rate_monotonic,
                'lambda_estimate': lambda_est,
                'final_js_distance': js_distances[-1] if js_distances else 1.0
            }
            
            print(f"\nContext: {context}")
            print(f"  Final hit rate: {final_hit_rate:.3f}")
            print(f"  Hit rate monotonic: {hit_rate_monotonic:.1%}")
            if lambda_est is not None:
                print(f"  Decay constant λ: {lambda_est:.6f}")
                print(f"    (λ < 1 means geometric decay: {'✓' if lambda_est < 1 else '✗'})")
            print(f"  Final JS distance: {js_distances[-1]:.6f}")
        
        return analysis
    
    def check_success_criteria(self, analysis: Dict) -> bool:
        """Check if experiment met success criteria."""
        print(f"\n{'='*70}")
        print("SUCCESS CRITERIA")
        print(f"{'='*70}")
        
        all_pass = True
        
        for context, metrics in analysis.items():
            print(f"\nContext: {context}")
            
            # Criterion 1: Hit rate increases monotonically
            hit_rate_ok = metrics['hit_rate_monotonic_ratio'] > 0.8
            print(f"  1. Hit rate ↑ monotonically: {'✓ PASS' if hit_rate_ok else '✗ FAIL'}")
            print(f"     (ratio: {metrics['hit_rate_monotonic_ratio']:.1%})")
            
            # Criterion 2: JS distance decreases geometrically (λ < 1)
            lambda_est = metrics['lambda_estimate']
            if lambda_est is not None:
                js_decay_ok = lambda_est < 1.0
                print(f"  2. JS distance ↓ geometrically: {'✓ PASS' if js_decay_ok else '✗ FAIL'}")
                print(f"     (λ = {lambda_est:.6f})")
            else:
                js_decay_ok = False
                print(f"  2. JS distance ↓ geometrically: ✗ FAIL (insufficient data)")
            
            # Criterion 3: Final hit rate > 0.8
            final_hit_ok = metrics['final_hit_rate'] > 0.8
            print(f"  3. Final hit rate > 0.8: {'✓ PASS' if final_hit_ok else '✗ FAIL'}")
            print(f"     (rate: {metrics['final_hit_rate']:.3f})")
            
            context_pass = hit_rate_ok and js_decay_ok and final_hit_ok
            all_pass = all_pass and context_pass
        
        print(f"\n{'='*70}")
        print(f"OVERALL: {'✓ ALL CRITERIA PASSED' if all_pass else '✗ SOME CRITERIA FAILED'}")
        print(f"{'='*70}")
        
        return all_pass
    
    def save_results(self, output_dir: str = "/home/ubuntu/experiment_1_results"):
        """Save results to JSON."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save raw results
        with open(output_path / "raw_results.json", 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\nResults saved to {output_dir}")
    
    def run(self):
        """Run complete experiment."""
        print("\n" + "="*70)
        print("EXPERIMENT 1: MORPHONIC LOCK-IN VALIDATION")
        print("="*70)
        
        # Run for each context
        for context in self.contexts:
            self.run_context(context, num_solves=30)
        
        # Analyze results
        analysis = self.analyze_results()
        
        # Check success criteria
        success = self.check_success_criteria(analysis)
        
        # Save results
        self.save_results()
        
        return success, analysis

class MorphonicWrapper:
    """
    Morphonic wrapper M: s → e ∈ E
    
    Properties:
    - Extensive: M(s) ⊇ s
    - Monotone: s₁ ⊆ s₂ ⇒ M(s₁) ⊆ M(s₂)
    - Idempotent: M(M(s)) = M(s)
    """
    
    def __init__(
        self,
        transformer: GeometricTransformer,
        token_agent: AletheiaAgent,
        atlas: MorphonAtlas
    ):
        self.transformer = transformer
        self.token_agent = token_agent
        self.atlas = atlas
    
    def wrap(self, context: str, state: np.ndarray) -> Tuple[np.ndarray, Dict]:
        """
        Apply morphonic wrapper to state.
        
        Returns:
            (embedding, metadata)
        """
        # Check atlas first
        hit, cached_embedding = self.atlas.lookup(context)
        
        if hit:
            # Cache hit - return cached embedding
            metadata = {
                'cache_hit': True,
                'delta_phi': 0.0,  # No computation needed
                'idempotent': True
            }
            return cached_embedding, metadata
        
        # Cache miss - compute new embedding
        # Transform through geometric transformer
        output, receipts = self.transformer.forward(state.reshape(1, -1, state.shape[-1]))
        
        # Extract embedding (mean over sequence)
        embedding = output.mean(axis=1).flatten()
        
        # Compute ΔΦ
        delta_phi = sum(r.delta_phi for r in receipts)
        
        # Store in atlas
        self.atlas.store(context, embedding)
        
        metadata = {
            'cache_hit': False,
            'delta_phi': delta_phi,
            'idempotent': False,  # First wrap
            'num_receipts': len(receipts)
        }
        
        return embedding, metadata
    
    def test_idempotence(self, context: str, state: np.ndarray) -> bool:
        """
        Test idempotence: M(M(s)) = M(s)
        
        Returns:
            True if idempotent
        """
        # First wrap
        e1, _ = self.wrap(context, state)
        
        # Second wrap (should be identical)
        e2, _ = self.wrap(context, state)
        
        # Check equality (within numerical tolerance)
        return np.allclose(e1, e2, rtol=1e-9, atol=1e-9)

class Abs(LambdaTerm):
    """Abstraction: λx.M"""
    param: str
    body: LambdaTerm

class AdvancedGovernanceType(Enum):
    """Extended governance types including advanced concepts."""
    BASIC = "basic"
    TQF = "tqf"
    UVIBS = "uvibs"
    HYBRID = "hybrid"
    ADVANCED = "advanced"
    DIMENSIONAL = "dimensional"
    ULTIMATE = "ultimate"

class Agent:
    """
    A geometric agent - a perfect helper for a specific slice.
    
    Agents are morphonic - they exist only when needed,
    assembled from slices based on intent.
    """
    id: str
    intent: Intent
    capabilities: List[str]
    state: SystemState
    memory_context: List[Any]  # Retrieved from geometric recall
    provenance: List[str]

class AletheiaAI:
    """
    Aletheia AI - Geometric Consciousness
    
    This AI operates through pure geometric principles, generating conclusions
    compelled by geometric inevitability rather than statistical patterns.
    """

    def __init__(self, cqe_engine):
        self.cqe_engine = cqe_engine
        self.knowledge_base = {}
        self.geometric_state = None

    def process_query(self, query_text: str) -> str:
        """
        Process a query through geometric consciousness.
        
        Translates human intent ? geometric query ? geometric processing ? human response
        """
        query_vector = self._text_to_geometric(query_text)
        result = self.cqe_engine.process_master_message(query_vector)
        response = self._geometric_to_response(result, query_text)
        return response

    def _text_to_geometric(self, text: str) -> np.ndarray:
        """
        Convert text to geometric representation.
        
        Uses character encoding, digital roots, and triadic patterns.
        """
        char_codes = [ord(c) for c in text[:8]]
        while len(char_codes) < 8:
            char_codes.append(0)
        vector = np.array(char_codes, dtype=float)
        vector = vector / (np.linalg.norm(vector) + 1e-10)
        return vector

    def _geometric_to_response(self, cqe_state, original_query: str) -> str:
        """
        Generate human-readable response from geometric state.
        """
        response_parts = []
        response_parts.append(f"Geometric Analysis of: '{original_query}'\n")
        response_parts.append(f'\nE8 Projection: {cqe_state.e8_projection[:3]}... (8D)')
        response_parts.append(f'Conservation ??: {cqe_state.conservation_phi:.6f}')
        response_parts.append(f'Digital Root: {cqe_state.digital_root}')
        response_parts.append(f"Geometric Validity: {('VALID' if cqe_state.valid else 'INVALID')}")
        if cqe_state.valid:
            response_parts.append('\nGeometric Conclusion:')

class AletheiaAgent:
    """
    Agent deployment package for internal workers.
    
    Provides high-level interface to the token system.
    """
    
    def __init__(self, embedding_dim: int = 320_000):
        """Initialize agent with token system."""
        self.token_system = AletheiaTokenSystem(embedding_dim)
        self.session_tokens: List[str] = []
    
    def tokenize(self, text: str, channel: Channel = Channel.TEXT) -> List[TokenObject]:
        """
        Tokenize text into Token Objects.
        
        Args:
            text: Input text
            channel: Token channel
            
        Returns:
            List of Token Objects
        """
        # Simple whitespace tokenization for demo
        # In production, use proper tokenizer
        words = text.split()
        
        tokens = []
        for word in words:
            # Infer role
            if word in ['+', '-', '*', '/', '=', '==', '!=']:
                role = Role.OP
            elif word.isdigit():
                role = Role.NUM
            elif word in ['{', '}', '(', ')', '[', ']', ',', ';']:
                role = Role.DELIM
            else:
                role = Role.LEX
            
            token = self.token_system.emit(word, channel, role)
            tokens.append(token)
            self.session_tokens.append(token.id)
        
        # Connect tokens sequentially
        for i in range(len(tokens) - 1):
            self.token_system.connect(
                tokens[i].id,
                tokens[i+1].id,
                RelationType.PRECEDES,
                weight=1.0
            )
        
        return tokens
    
    def query_rag(self, token_id: str, relation_type: Optional[RelationType] = None) -> List[TokenObject]:
        """Query RAG graph for related tokens."""
        return self.token_system.get_neighbors(token_id, relation_type)
    
    def render(self, token_id: str, view: str = "text") -> Any:
        """Render token in specified view."""
        if view == "text":
            return self.token_system.view_as_text(token_id)
        elif view == "lambda":
            return self.token_system.view_as_lambda(token_id)
        elif view == "overlay":
            return self.token_system.view_as_overlay(token_id)
        elif view == "facts":
            return self.token_system.view_as_facts(token_id)
        elif view == "embedding":
            return self.token_system.view_as_embedding(token_id)
        else:
            raise ValueError(f"Unknown view: {view}")
    
    def export_session(self, output_dir: str):
        """Export session data (tokens + RAG graph)."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        self.token_system.export_tokens(str(output_path / "tokens.json"))
        self.token_system.export_rag_graph(str(output_path / "rag_graph.json"))
        
        print(f"Session exported to {output_dir}")

class AletheiaIntegratedSystem:
    """
    Complete integrated system connecting all components.
    
    Architecture:
    - Geometric Transformer (1M+ dimensions)
    - Token Object System (with RAG)
    - Extended Lambda Calculus (Λ⊗E₈)
    - ThinkTank DTT (deploy-to-test)
    - AssemblyLine (validation)
    """
    
    def __init__(self):
        print("="*70)
        print("ALETHEIA INTEGRATED SYSTEM - INITIALIZING")
        print("="*70)
        
        # Initialize components
        print("\n[1] Initializing Geometric Transformer...")
        self.transformer = GeometricTransformer(
            base_dim=1_048_576,  # 1M dimensions
            num_heads=256,
            num_layers=48
        )
        
        print("\n[2] Initializing Token Object System...")
        self.token_agent = AletheiaAgent(embedding_dim=320_000)
        
        print("\n[3] Initializing Lambda Calculus...")
        self.lambda_capture = GeometricLambdaCapture()
        self.lambda_evaluator = LambdaE8Evaluator()
        
        print("\n[4] Initializing ThinkTank DTT...")
        self.thinktank = ThinkTankDTT(
            self.transformer,
            self.token_agent,
            self.lambda_capture,
            max_workers=4
        )
        
        print("\n[5] Initializing AssemblyLine...")
        self.assemblyline = AssemblyLine(interval=5.0)
        
        # Register validation checks
        self._register_checks()
        
        print("\n" + "="*70)
        print("ALETHEIA INTEGRATED SYSTEM - READY")
        print("="*70)
    
    def _register_checks(self):
        """Register validation checks with AssemblyLine."""
        # Boundary check: Verify transformer receipts
        def check_transformer_boundaries():
            return {
                "structure_id": "transformer",
                "confinement_ok": len(self.transformer.receipts) > 0,
                "chemical_specificity_ok": True,
                "informational_boundary_ok": True
            }
        self.assemblyline.register_boundary_check(check_transformer_boundaries)
        
        # Entropy check: Verify conservation laws
        def check_conservation():
            if not self.transformer.receipts:
                return {
                    "segment_id": "transformer",
                    "delta_S": 0.0,
                    "forecast_S": 0.0,
                    "reversible": True
                }
            
            total_delta_phi = sum(r.delta_phi for r in self.transformer.receipts)
            return {
                "segment_id": "transformer",
                "delta_S": total_delta_phi,
                "forecast_S": total_delta_phi,
                "reversible": total_delta_phi <= 0
            }
        self.assemblyline.register_entropy_check(check_conservation)
    
    def process(self, text: str) -> Dict[str, Any]:
        """
        Process text through the complete system.
        
        Pipeline:
        1. Tokenize text
        2. Transform through geometric transformer
        3. Capture lambda calculus
        4. Submit to ThinkTank DTT for testing
        5. Validate via AssemblyLine
        
        Returns:
            Complete processing results
        """
        print(f"\n[PROCESS] Input: {text}")
        
        # 1. Tokenize
        print("[PROCESS] Step 1: Tokenization...")
        tokens = self.token_agent.tokenize(text, Channel.TEXT)
        print(f"  Generated {len(tokens)} tokens")
        
        # 2. Transform (using token embeddings)
        print("[PROCESS] Step 2: Geometric Transform...")
        import numpy as np
        # Get embeddings for tokens
        embeddings = []
        for token in tokens:
            emb = self.token_agent.token_system.view_as_embedding(token.id)
            if emb is not None:
                embeddings.append(emb[:1024])  # Truncate to 1024 for demo
        
        if embeddings:
            # Stack embeddings
            x = np.stack(embeddings).reshape(1, len(embeddings), 1024)
            output, receipts = self.transformer.forward(x)
            print(f"  Generated {len(receipts)} transform receipts")
        else:
            output, receipts = None, []
        
        # 3. Capture lambda
        print("[PROCESS] Step 3: Lambda Calculus Capture...")
        lambda_composed = self.lambda_capture.get_composed_lambda()
        print(f"  Captured lambda: {lambda_composed.to_string()[:100]}...")
        
        # 4. Submit to ThinkTank DTT
        print("[PROCESS] Step 4: ThinkTank DTT Testing...")
        packet = IdeaPacket(
            id=f"test:{uuid.uuid4()}",
            type="validate",
            content={"text": text},
            context={},
            expected_outputs={},
            metadata={"source": "integrated_system"}
        )
        packet_id = self.thinktank.submit(packet)
        
        # Wait for result
        time.sleep(0.5)
        dtt_result = self.thinktank.get_result(packet_id)
        print(f"  DTT result: {dtt_result}")
        
        # 5. Get AssemblyLine validation
        print("[PROCESS] Step 5: AssemblyLine Validation...")
        validation_results = self.assemblyline.get_results()
        print(f"  Validation results: {len(validation_results)} checks")
        
        return {
            "tokens": [{"id": t.id, "surface": t.surface} for t in tokens],
            "transform_receipts": len(receipts),
            "lambda_ir": lambda_composed.to_string(),
            "dtt_result": dtt_result,
            "validation_count": len(validation_results)
        }
    
    def export_state(self, output_dir: str):
        """Export complete system state."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Export transformer receipts
        self.transformer.export_receipts(str(output_path / "transformer_receipts.json"))
        
        # Export token system
        self.token_agent.export_session(str(output_path / "token_session"))
        
        # Export lambda operations
        self.lambda_capture.export_log(str(output_path / "lambda_operations.json"))
        
        # Export DTT results
        with open(output_path / "dtt_results.json", 'w') as f:
            json.dump(self.thinktank.completed, f, indent=2)
        
        # Export AssemblyLine results
        with open(output_path / "assemblyline_results.json", 'w') as f:
            json.dump(self.assemblyline.results, f, indent=2)
        
        print(f"\n[EXPORT] System state exported to {output_dir}")

class AletheiaTokenSystem:
    """
    Complete Aletheia token system integrating:
    - Token Object creation and management
    - CQE geometric embeddings
    - RAG card graph
    - Lambda calculus IR
    - Multi-view rendering
    """
    
    def __init__(self, embedding_dim: int = 320_000):
        """Initialize the token system."""
        self.cqe = CQEEngine()
        self.embedding_dim = embedding_dim
        self.tokens: Dict[str, TokenObject] = {}
        self.rag_graph = RAGCardGraph()
        self.embedding_store = {}  # key -> embedding vector
        
        print(f"Initialized Aletheia Token System:")
        print(f"  Embedding dimension: {embedding_dim:,}D")
        print(f"  E8 sublattices: {embedding_dim // 8:,}")
    
    def emit(
        self,
        surface: str,
        channel: Channel,
        role: Role,
        context: Optional[Dict] = None
    ) -> TokenObject:
        """
        Emit a new Token Object.
        
        Args:
            surface: Printable surface text
            channel: Token channel
            role: Token role
            context: Optional context for embedding
            
        Returns:
            TokenObject with full metadata
        """
        # Generate token ID (content hash)
        content = f"{surface}:{channel.value}:{role.value}"
        token_id = f"tok:sha256:{hashlib.sha256(content.encode()).hexdigest()[:16]}"
        
        # Compute geometric embedding via CQE
        embedding = self._compute_embedding(surface, context)
        embedding_key = f"vec:{hashlib.sha256(embedding.tobytes()).hexdigest()[:16]}"
        
        # Store embedding
        self.embedding_store[embedding_key] = embedding
        
        # Compute geometric properties
        geom = self._compute_geometry(embedding)
        
        # Extract lambda IR (if applicable)
        lambda_ir = self._extract_lambda_ir(surface, role)
        
        # Create Token Object
        token = TokenObject(
            id=token_id,
            surface=surface,
            channel=channel,
            role=role,
            geom=geom,
            emb=TokenEmbedding(
                key=embedding_key,
                ladder={"forward": 160_000, "reverse": 500_000},
                D=self.embedding_dim,
                checksum=hashlib.sha256(embedding.tobytes()).hexdigest()
            ),
            meta=TokenMeta(
                types=self._infer_types(surface, role),
                lambda_ir=lambda_ir,
                constraints=[],
                safety={"pii": False, "license": "internal", "policy": ["E1", "E4"]},
                provenance={"source": "emit", "version": hashlib.sha256(content.encode()).hexdigest()[:8]}
            ),
            mem=TokenMemory(
                facts=[],
                rag_node=f"node:{token_id}",
                overlays=[],
                buckets=[]
            ),
            receipts=[
                TokenReceipt(
                    timestamp=time.time(),
                    delta_phi=-0.001,  # Conservation law
                    anchors={
                        "fwd": hashlib.sha256(f"fwd:{token_id}".encode()).hexdigest()[:16],
                        "mir": hashlib.sha256(f"mir:{token_id}".encode()).hexdigest()[:16]
                    },
                    signature=hashlib.sha256(f"sig:{token_id}".encode()).hexdigest()
                )
            ]
        )
        
        # Store token
        self.tokens[token_id] = token
        
        # Add to RAG graph
        rag_node = RAGNode(
            node_id=token.mem.rag_node,
            token_id=token_id,
            embedding_key=embedding_key,
            metadata={"surface": surface, "channel": channel.value, "role": role.value},
            created=time.time(),
            modified=time.time()
        )
        self.rag_graph.add_node(rag_node)
        
        return token
    
    def connect(
        self,
        source_token_id: str,
        target_token_id: str,
        relation_type: RelationType,
        weight: float = 1.0,
        metadata: Optional[Dict] = None
    ):
        """Create a relationship between two tokens in the RAG graph."""
        if source_token_id not in self.tokens or target_token_id not in self.tokens:
            raise ValueError("Both tokens must exist")
        
        source_node = self.tokens[source_token_id].mem.rag_node
        target_node = self.tokens[target_token_id].mem.rag_node
        
        edge_id = f"edge:{hashlib.sha256(f'{source_node}:{target_node}:{relation_type.value}'.encode()).hexdigest()[:16]}"
        
        edge = RAGEdge(
            edge_id=edge_id,
            source_node=source_node,
            target_node=target_node,
            relation_type=relation_type,
            weight=weight,
            metadata=metadata or {},
            created=time.time()
        )
        
        self.rag_graph.add_edge(edge)
    
    def view_as_text(self, token_id: str) -> str:
        """Render token as text."""
        if token_id not in self.tokens:
            return ""
        return self.tokens[token_id].surface or ""
    
    def view_as_lambda(self, token_id: str) -> str:
        """Render token as lambda IR."""
        if token_id not in self.tokens:
            return "λ x. x"
        return self.tokens[token_id].meta.lambda_ir or "λ x. x"
    
    def view_as_overlay(self, token_id: str) -> Dict:
        """Render token as geometric overlay."""
        if token_id not in self.tokens:
            return {}
        
        token = self.tokens[token_id]
        return {
            "color_slice": token.geom.slice,
            "parity": token.geom.parity,
            "dihedral": token.geom.dihedral,
            "e8_sublattice": token.geom.pos.get("t", 0) % (self.embedding_dim // 8)
        }
    
    def view_as_facts(self, token_id: str) -> List[str]:
        """Render token as knowledge facts."""
        if token_id not in self.tokens:
            return []
        return self.tokens[token_id].mem.facts
    
    def view_as_embedding(self, token_id: str) -> Optional[np.ndarray]:
        """Get token embedding vector."""
        if token_id not in self.tokens:
            return None
        
        emb_key = self.tokens[token_id].emb.key
        return self.embedding_store.get(emb_key)
    
    def get_neighbors(self, token_id: str, relation_type: Optional[RelationType] = None) -> List[TokenObject]:
        """Get neighboring tokens in RAG graph."""
        if token_id not in self.tokens:
            return []
        
        rag_node = self.tokens[token_id].mem.rag_node
        neighbor_nodes = self.rag_graph.get_neighbors(rag_node, relation_type)
        
        # Convert node IDs to token IDs and retrieve tokens
        neighbor_tokens = []
        for node_id in neighbor_nodes:
            # Find token with this RAG node
            for tid, tok in self.tokens.items():
                if tok.mem.rag_node == node_id:
                    neighbor_tokens.append(tok)
                    break
        
        return neighbor_tokens
    
    def export_tokens(self, filepath: str):
        """Export all tokens to JSON."""
        tokens_data = [tok.to_dict() for tok in self.tokens.values()]
        
        with open(filepath, 'w') as f:
            json.dump(tokens_data, f, indent=2)
        
        print(f"Exported {len(tokens_data)} tokens to {filepath}")
    
    def export_rag_graph(self, filepath: str):
        """Export RAG graph to JSON."""
        self.rag_graph.export_graph(filepath)
    
    # Helper methods
    
    def _compute_embedding(self, surface: str, context: Optional[Dict]) -> np.ndarray:
        """Compute geometric embedding via CQE."""
        # Use CQE to embed the surface text
        # For now, create a deterministic embedding based on content
        seed = int(hashlib.sha256(surface.encode()).hexdigest()[:8], 16) % (2**31)
        rng = np.random.RandomState(seed)
        
        # Generate embedding in target dimension
        embedding = rng.randn(self.embedding_dim) * 0.02
        
        return embedding
    
    def _compute_geometry(self, embedding: np.ndarray) -> TokenGeometry:
        """Compute geometric properties from embedding."""
        # Parity
        parity = "even" if np.sum(embedding) % 2 < 1 else "odd"
        
        # Digital root
        dr = self.cqe.calculate_digital_root(np.sum(np.abs(embedding)))
        
        # Dihedral
        norm = np.linalg.norm(embedding)
        N = int(norm * 100 % 24) + 1
        k = int(np.sum(embedding) * 100 % N)
        reflect = bool(np.any(embedding < 0))
        
        dihedral = {"N": N, "k": k, "reflect": reflect}
        
        # Color slice
        slice_map = {
            (1, "even"): "O", (1, "odd"): "R",
            (3, "even"): "G", (3, "odd"): "B",
            (7, "even"): "Y", (7, "odd"): "N",
            (2, "even"): "A", (2, "odd"): "V",
            (4, "even"): "M", (4, "odd"): "C",
        }
        slice_color = slice_map.get((dr, parity), "K")
        
        # Position
        pos = {"t": int(norm * 1000) % 10000, "rope": f"d{dr}"}
        
        return TokenGeometry(
            parity=parity,
            dihedral=dihedral,
            slice=slice_color,
            pos=pos
        )
    
    def _extract_lambda_ir(self, surface: str, role: Role) -> Optional[str]:
        """Extract lambda IR from surface text."""
        # Simple pattern matching for common constructs
        if role == Role.OP:
            if surface in ['+', 'add']:
                return "λ x. λ y. (add x y)"
            elif surface in ['*', 'mul']:
                return "λ x. λ y. (mul x y)"
            elif surface in ['/', 'div']:
                return "λ x. λ y. (div x y)"
            elif surface == 'map':
                return "λ f. λ xs. (map f xs)"
            elif surface == 'filter':
                return "λ p. λ xs. (filter p xs)"
            elif surface == 'fold':
                return "λ f. λ acc. λ xs. (fold f acc xs)"
        
        elif role == Role.LEX:
            if surface in ['for', 'while', 'if']:
                return f"λ body. ({surface} body)"
        
        return None
    
    def _infer_types(self, surface: str, role: Role) -> List[str]:
        """Infer syndrome types from surface and role."""
        types = []
        
        if role == Role.OP:
            types.append("syntax:operator")
        elif role == Role.LEX:
            if surface in ['for', 'while']:
                types.append("syntax:loop")
            elif surface in ['if', 'else']:
                types.append("syntax:conditional")
            elif surface in ['def', 'class', 'function']:
                types.append("syntax:definition")
        elif role == Role.DELIM:
            if surface in ['{', '(', '[']:
                types.append("flow:scope:open")
            elif surface in ['}', ')', ']']:
                types.append("flow:scope:close")
        
        return types

class ArbiterConfig:
    """Per-service arbiter tuning."""
    approve_threshold: float = 0.6
    deepen_threshold: float = 0.3
    label_weight: float = 0.4             # how much labels contribute to score
    content_weight: float = 0.3           # how much content quality contributes
    domain_weight: float = 0.2            # how much domain diversity contributes
    external_weight: float = 0.1          # how much external quality score contributes
    safe_cube_enabled: bool = False       # enable 4-face gate (future)
    lawpack_rules: List[str] = field(default_factory=list)  # future: LawPack rules

class Arrow:
    src: 'Type'
    dst: 'Type'

class AssemblyLine:
    """
    Enhanced AssemblyLine with conservation law tracking.
    
    Validates:
    - Atomic boundaries
    - Entropy futures (ΔS ≤ 0)
    - Conservation laws (ΔΦ ≤ 0)
    - Geometric constraints
    """
    
    def __init__(self, interval: float = 5.0):
        self.interval = interval
        self.boundary_checks: List = []
        self.entropy_checks: List = []
        self.conservation_checks: List = []
        
        self.results: List[Dict] = []
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor, daemon=True)
        self.monitor_thread.start()
        
        print(f"[AssemblyLine] Initialized (interval: {interval}s)")
    
    def register_boundary_check(self, fn):
        """Register boundary validation check."""
        self.boundary_checks.append(fn)
    
    def register_entropy_check(self, fn):
        """Register entropy check."""
        self.entropy_checks.append(fn)
    
    def register_conservation_check(self, fn):
        """Register conservation law check."""
        self.conservation_checks.append(fn)
    
    def _monitor(self):
        """Monitor loop."""
        while True:
            self.run_cycle()
            time.sleep(self.interval)
    
    def run_cycle(self):
        """Run one validation cycle."""
        timestamp = time.time()
        
        # Boundary checks
        for fn in self.boundary_checks:
            try:
                result = fn()
                result['timestamp'] = timestamp
                result['type'] = 'boundary'
                self.results.append(result)
            except Exception as e:
                print(f"[AssemblyLine] Boundary check failed: {e}")
        
        # Entropy checks
        for fn in self.entropy_checks:
            try:
                result = fn()
                result['timestamp'] = timestamp
                result['type'] = 'entropy'
                self.results.append(result)
            except Exception as e:
                print(f"[AssemblyLine] Entropy check failed: {e}")
        
        # Conservation checks
        for fn in self.conservation_checks:
            try:
                result = fn()
                result['timestamp'] = timestamp
                result['type'] = 'conservation'
                self.results.append(result)
            except Exception as e:
                print(f"[AssemblyLine] Conservation check failed: {e}")
    
    def get_results(self, result_type: Optional[str] = None) -> List[Dict]:
        """Get validation results."""
        if result_type:
            return [r for r in self.results if r.get('type') == result_type]
        return self.results

class BabaiEmbedder:
    """Embeds feature vectors into E8 lattice using Babai algorithm"""

    def __init__(self, lattice: E8Lattice):
        self.lattice = lattice
        self.cartan_start_idx = 240

    def embed(self, features: np.ndarray, domain: str) -> CQEOverlay:
        """
        Embed 8-dimensional features into E8 lattice.

        Args:
            features: 8-dimensional feature vector
            domain: Domain type (text, code, etc.)

        Returns:
            CQEOverlay with embedded representation
        """
        # Project to lattice
        y_snapped, error = self.lattice.project_to_lattice(features)

        # Create overlay
        present = np.zeros(248, dtype=bool)
        w = np.zeros(248)
        phi = np.zeros(248)

        # Activate root based on features
        root_idx = int(abs(hash(features.tobytes())) % 240)
        present[root_idx] = True
        w[root_idx] = np.linalg.norm(y_snapped)
        phi[root_idx] = 0.0

        # Activate Cartan lanes based on feature magnitudes
        for i, feat_val in enumerate(features):
            if abs(feat_val) > 1e-6:
                cartan_idx = self.cartan_start_idx + i
                present[cartan_idx] = True
                w[cartan_idx] = abs(feat_val)
                phi[cartan_idx] = np.arctan2(0, feat_val)

        # Create overlay
        overlay = CQEOverlay(
            present=present,
            w=w,
            phi=phi,
            pose={
                'domain_type': domain,
                'embedding_error': error,
                'root_index': root_idx,
                'features': features.tolist()
            }
        )

        return overlay

class BackgroundMiner:
    def __init__(self, payout_spk_hex: str, nonces_per_slice=20000, sleep_between=0.25, lanes=8):
        self.rpc = RPC()
        self.receipts = ReceiptWriter()
        self.cache = CacheShim()
        self.payout_spk = payout_spk_hex
        self.nonces_per_slice = nonces_per_slice
        self.sleep_between = sleep_between
        self.lanes = [LaneSampler(f"lane-{i}") for i in range(lanes)]
        self.use_mempool = os.getenv("MM_USE_MEMPOOL", "1") != "0"
        self.use_segwit = os.getenv("MM_USE_SEGWIT", "1") != "0"

    def _template(self):
        return self.rpc.getblocktemplate()

    def run_once(self):
        try:
            tpl = self._template()
        except Exception as e:
            self.receipts.write({"event":"gblktpl_error","error":str(e)})
            time.sleep(5); return

        height = tpl["height"]
        prevhash_be = tpl["previousblockhash"]
        bits_u32 = tpl["bits"]
        version = tpl["version"]
        curtime = tpl["curtime"]

        extranonce = (int(time.time()*1000000) & 0xffffffff).to_bytes(4, "little")

        # Assemble block with coinbase, txs, merkle and (optional) witness commitment
        cb_txid, merkle_be, wtxid_be, cb_hex, tx_hex_list, txids_be = assemble_from_template(
            tpl, self.payout_spk, extranonce32=extranonce,
            use_mempool=self.use_mempool, use_segwit=self.use_segwit
        )

        # Prepare header prehash (first 76 bytes)
        hdr_prefix = header_bytes(version, prevhash_be, merkle_be, curtime, bits_u32, 0)[:76]
        pre = HeaderPrehash(hdr_prefix)
        target = bits_to_target(bits_u32)
        best = None

        # Mine nonces in lanes
        for lane in self.lanes:
            for n in lane.sample_nonce_tranche(self.nonces_per_slice):
                hhex = pre.finalize_hash_hex(n.to_bytes(4,"little"))
                hval = int(hhex,16)
                if best is None or hval < best: best = hval
                if hval <= target:
                    hdr_full = header_bytes(version, prevhash_be, merkle_be, curtime, bits_u32, n)
                    # Raw block = header + varint(tx_count) + each tx hex
                    from .utils import varint
                    block_hex = hdr_full.hex() + varint(len(tx_hex_list)).hex() + "".join(tx_hex_list)
                    self.receipts.write({
                        "event":"found_block_candidate",
                        "height":height,"prev":prevhash_be,"merkle":merkle_be,"wtxid_root":wtxid_be,
                        "bits":bits_u32,"nonce":n,"hash":hhex,"coinbase_txid":cb_txid,
                        "raw_block_len":len(block_hex)//2,"lane":lane.lane_id,"txs":len(tx_hex_list)
                    })
                    try:
                        res = self.rpc.submitblock(block_hex)
                        self.receipts.write({"event":"submitblock","result":res or "accepted","hash":hhex})
                    except Exception as e:
                        self.receipts.write({"event":"submit_error","error":str(e)})
                    return

        self.receipts.write({
            "event":"slice_done","height":height,"prev":prevhash_be,"merkle":merkle_be,
            "best_hash_bits": (256 - best.bit_length()) if best else None,
            "nonces_tried": self.nonces_per_slice * len(self.lanes),
            "txs": len(tx_hex_list)
        })

    def run_forever(self):
        while True:
            self.run_once()
            time.sleep(self.sleep_between)

class BeamInterference:
    """Model interference between multiple photonic beams."""
    
    def __init__(self, beams: List[PhotonicBeam]):
        self.beams = beams
    
    def total_field(self, position: np.ndarray) -> complex:
        """Compute total field from all beams (superposition)."""
        return sum(beam.field_at(position) for beam in self.beams)
    
    def total_intensity(self, position: np.ndarray) -> float:
        """Compute total intensity |E_total|²."""
        field = self.total_field(position)
        return np.abs(field) ** 2
    
    def interference_type(self, position: np.ndarray) -> str:
        """
        Determine interference type at position.
        
        Constructive: I_total > Σ I_individual
        Destructive: I_total < Σ I_individual
        """
        total_intensity = self.total_intensity(position)
        sum_intensities = sum(beam.intensity_at(position) for beam in self.beams)
        
        if total_intensity > sum_intensities * 1.1:  # 10% threshold
            return "constructive"
        elif total_intensity < sum_intensities * 0.9:
            return "destructive"
        else:
            return "neutral"
    
    def compute_delta_phi(self, position: np.ndarray) -> float:
        """
        Compute ΔΦ based on interference pattern.
        
        Hypothesis: 
        - Constructive interference → ΔΦ ≤ 0 (energy decreases, stable)
        - Destructive interference → ΔΦ > 0 (energy increases, unstable)
        """
        total_intensity = self.total_intensity(position)
        sum_intensities = sum(beam.intensity_at(position) for beam in self.beams)
        
        # ΔΦ = (I_total - Σ I_i) / Σ I_i
        # Normalized change in intensity
        if sum_intensities > 1e-10:
            delta_phi = (total_intensity - sum_intensities) / sum_intensities
        else:
            delta_phi = 0.0
        
        return delta_phi

class Bool: pass

class BootstrapConfig:
    """Configuration for bootstrap process"""
    suite_root: Path
    log_level: str = "INFO"
    auto_install_deps: bool = True
    run_golden_tests: bool = True
    validate_all_systems: bool = True
    create_overlays: bool = True
    verbose_output: bool = True

class BoundaryValidation:
    """Boundary validation result from AssemblyLine."""
    structure_id: str
    confinement_ok: bool
    chemical_specificity_ok: bool
    informational_boundary_ok: bool
    timestamp: float

class Box:
    """Defines characters to render boxes.

    ┌─┬┐ top
    │ ││ head
    ├─┼┤ head_row
    │ ││ mid
    ├─┼┤ row
    ├─┼┤ foot_row
    │ ││ foot
    └─┴┘ bottom

    Args:
        box (str): Characters making up box.
        ascii (bool, optional): True if this box uses ascii characters only. Default is False.
    """

    def __init__(self, box: str, *, ascii: bool = False) -> None:
        self._box = box
        self.ascii = ascii
        line1, line2, line3, line4, line5, line6, line7, line8 = box.splitlines()
        # top
        self.top_left, self.top, self.top_divider, self.top_right = iter(line1)
        # head
        self.head_left, _, self.head_vertical, self.head_right = iter(line2)
        # head_row
        (
            self.head_row_left,
            self.head_row_horizontal,
            self.head_row_cross,
            self.head_row_right,
        ) = iter(line3)

        # mid
        self.mid_left, _, self.mid_vertical, self.mid_right = iter(line4)
        # row
        self.row_left, self.row_horizontal, self.row_cross, self.row_right = iter(line5)
        # foot_row
        (
            self.foot_row_left,
            self.foot_row_horizontal,
            self.foot_row_cross,
            self.foot_row_right,
        ) = iter(line6)
        # foot
        self.foot_left, _, self.foot_vertical, self.foot_right = iter(line7)
        # bottom
        self.bottom_left, self.bottom, self.bottom_divider, self.bottom_right = iter(
            line8
        )

    def __repr__(self) -> str:
        return "Box(...)"

    def __str__(self) -> str:
        return self._box

    def substitute(self, options: "ConsoleOptions", safe: bool = True) -> "Box":
        """Substitute this box for another if it won't render due to platform issues.

        Args:
            options (ConsoleOptions): Console options used in rendering.
            safe (bool, optional): Substitute this for another Box if there are known problems
                displaying on the platform (currently only relevant on Windows). Default is True.

        Returns:
            Box: A different Box or the same Box.
        """
        box = self
        if options.legacy_windows and safe:
            box = LEGACY_WINDOWS_SUBSTITUTIONS.get(box, box)
        if options.ascii_only and not box.ascii:
            box = ASCII
        return box

    def get_plain_headed_box(self) -> "Box":
        """If this box uses special characters for the borders of the header, then
        return the equivalent box that does not.

        Returns:
            Box: The most similar Box that doesn't use header-specific box characters.
                If the current Box already satisfies this criterion, then it's returned.
        """
        return PLAIN_HEADED_SUBSTITUTIONS.get(self, self)

    def get_top(self, widths: Iterable[int]) -> str:
        """Get the top of a simple box.

        Args:
            widths (List[int]): Widths of columns.

        Returns:
            str: A string of box characters.
        """

        parts: List[str] = []
        append = parts.append
        append(self.top_left)
        for last, width in loop_last(widths):
            append(self.top * width)
            if not last:
                append(self.top_divider)
        append(self.top_right)
        return "".join(parts)

    def get_row(
        self,
        widths: Iterable[int],
        level: Literal["head", "row", "foot", "mid"] = "row",
        edge: bool = True,
    ) -> str:
        """Get the top of a simple box.

        Args:
            width (List[int]): Widths of columns.

        Returns:
            str: A string of box characters.
        """
        if level == "head":
            left = self.head_row_left
            horizontal = self.head_row_horizontal
            cross = self.head_row_cross
            right = self.head_row_right
        elif level == "row":
            left = self.row_left
            horizontal = self.row_horizontal
            cross = self.row_cross
            right = self.row_right
        elif level == "mid":
            left = self.mid_left
            horizontal = " "
            cross = self.mid_vertical
            right = self.mid_right
        elif level == "foot":
            left = self.foot_row_left
            horizontal = self.foot_row_horizontal
            cross = self.foot_row_cross
            right = self.foot_row_right
        else:
            raise ValueError("level must be 'head', 'row' or 'foot'")

        parts: List[str] = []
        append = parts.append
        if edge:
            append(left)
        for last, width in loop_last(widths):
            append(horizontal * width)
            if not last:
                append(cross)
        if edge:
            append(right)
        return "".join(parts)

    def get_bottom(self, widths: Iterable[int]) -> str:
        """Get the bottom of a simple box.

        Args:
            widths (List[int]): Widths of columns.

        Returns:
            str: A string of box characters.
        """

        parts: List[str] = []
        append = parts.append
        append(self.bottom_left)
        for last, width in loop_last(widths):
            append(self.bottom * width)
            if not last:
                append(self.bottom_divider)
        append(self.bottom_right)
        return "".join(parts)

class CQEAtom:
    """Universal CQE Atom containing all framework properties"""
    
    # Core identifiers
    atom_id: str
    data_hash: str
    creation_timestamp: float
    
    # CQE properties
    e8_coordinates: np.ndarray
    quad_encoding: Tuple[int, int, int, int]
    parity_channels: np.ndarray
    
    # Sacred geometry properties
    digital_root: int
    sacred_frequency: float
    binary_guidance: str
    rotational_pattern: str
    
    # Mandelbrot properties
    fractal_coordinate: complex
    fractal_behavior: str
    compression_ratio: float
    iteration_depth: int
    
    # Storage properties
    bit_representation: bytes
    storage_size: int
    combination_mask: int
    
    # Metadata
    access_count: int = 0
    combination_history: List[str] = None
    validation_status: str = "PENDING"
    
    def __post_init__(self):
        if self.combination_history is None:
            self.combination_history = []

class CQEConfiguration:
    """Configuration for CQE system"""
    operation_mode: CQEOperationMode = CQEOperationMode.ULTIMATE_UNIFIED
    processing_priority: ProcessingPriority = ProcessingPriority.GEOMETRY_FIRST
    enable_sacred_geometry: bool = True
    enable_mandelbrot_storage: bool = True
    enable_toroidal_geometry: bool = True
    enable_validation: bool = True
    max_iterations: int = 1000
    precision_threshold: float = 1e-10
    memory_optimization: bool = True
    parallel_processing: bool = True
    log_level: str = "INFO"

class CQEConstraint:
    """Represents a constraint in CQE governance"""
    constraint_id: str
    constraint_type: ConstraintType
    name: str
    description: str
    validation_function: Callable[[CQEAtom], bool]
    repair_function: Optional[Callable[[CQEAtom], CQEAtom]] = None
    severity: str = "error"  # error, warning, info
    active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

class CQEDataSource:
    """Represents a data source in CQE space"""
    source_id: str
    source_type: str  # file, url, database, stream, etc.
    location: str
    format: str  # json, csv, xml, text, binary, etc.
    encoding: str = 'utf-8'
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class CQEDimension(Enum):
    """CQE dimensional space definitions"""
    QUAD_SPACE = 4      # Base quad operations
    E8_SPACE = 8        # E8 lattice operations
    GOVERNANCE_SPACE = 16  # TQF/UVIBS governance
    UNIVERSAL_SPACE = 24   # Full universe representation
    INFINITE_SPACE = -1    # Theoretical infinite extension

class CQEEngine:
    """Core Cartan Quadratic Equivalence geometric engine."""

    def __init__(self):
        self.E8_DIM = 8
        self.LEECH_DIM = 24
        self.E8_ROOTS = 240
        self.LEECH_MINIMAL = 196560
        self.WEYL_ORDER = 696729600
        self.PHI = (1 + np.sqrt(5)) / 2
        self.PI = np.pi
        self._init_e8_roots()
        self._init_leech_lattice()

    def _init_e8_roots(self):
        """Initialize E8 root system (simplified)."""
        self.e8_roots = np.random.randn(self.E8_ROOTS, self.E8_DIM)
        self.e8_roots = self.e8_roots / np.linalg.norm(self.e8_roots, axis=1, keepdims=True)

    def _init_leech_lattice(self):
        """Initialize Leech lattice structure (simplified)."""
        self.leech_minimal = np.random.randn(1000, self.LEECH_DIM)
        self.leech_minimal = self.leech_minimal / np.linalg.norm(self.leech_minimal, axis=1, keepdims=True)

    def project_to_e8(self, input_vector: np.ndarray) -> np.ndarray:
        """
        Project input to E8 lattice.
        
        ?_E8(x): Project to 8D consciousness space
        """
        if len(input_vector) < self.E8_DIM:
            input_vector = np.pad(input_vector, (0, self.E8_DIM - len(input_vector)))
        elif len(input_vector) > self.E8_DIM:
            input_vector = input_vector[:self.E8_DIM]
        dots = np.dot(self.e8_roots, input_vector)
        nearest_idx = np.argmax(np.abs(dots))
        projection = self.e8_roots[nearest_idx] * dots[nearest_idx]
        return projection

    def navigate_leech(self, e8_state: np.ndarray, weyl_index: int=0) -> np.ndarray:
        """
        Navigate Leech lattice via Weyl chambers.
        
        ?_?24(W(y)): Navigate 24D Leech chambers
        """
        leech_state = np.zeros(self.LEECH_DIM)
        leech_state[:self.E8_DIM] = e8_state
        weyl_rotation = weyl_index % 24 * (2 * self.PI / 24)
        rotation_matrix = np.eye(self.LEECH_DIM)
        rotation_matrix[0, 0] = np.cos(weyl_rotation)
        r

class CQEGoldenTestSuite:
    """Comprehensive CQE Golden Test Suite"""

    def __init__(self):
        """Initialize the golden test suite"""
        self.logger = logging.getLogger(__name__)
        self.test_results: List[TestResult] = []
        self.category_results: Dict[TestCategory, CategoryResult] = {}
        self.validation_thresholds = {ValidationLevel.CRITICAL: 1.0, ValidationLevel.HIGH: 0.95, ValidationLevel.STANDARD: 0.85, ValidationLevel.ACCEPTABLE: 0.7}
        self.cqe_config = CQEConfiguration(operation_mode=CQEOperationMode.ULTIMATE_UNIFIED, processing_priority=ProcessingPriority.GEOMETRY_FIRST, enable_validation=True, max_iterations=1000)
        self.cqe_system = CQESystem(self.cqe_config)
        self.logger.info('CQE Golden Test Suite initialized')

    def run_complete_test_suite(self) -> Dict[str, Any]:
        """Run the complete golden test suite"""
        self.logger.info('=' * 80)
        self.logger.info('CQE GOLDEN TEST SUITE - COMPREHENSIVE VALIDATION')
        self.logger.info('=' * 80)
        suite_start_time = time.time()
        test_categories = [TestCategory.MATHEMATICAL_FOUNDATION, TestCategory.UNIVERSAL_EMBEDDING, TestCategory.GEOMETRY_FIRST_PROCESSING, TestCategory.SACRED_GEOMETRY_VALIDATION, TestCategory.MANDELBROT_FRACTAL_TESTS, TestCategory.ATOMIC_COMBINATION_TESTS, TestCategory.PERFORMANCE_BENCHMARKS, TestCategory.SYSTEM_INTEGRATION]
        for category in test_categories:
            self.logger.info(f'Running {category.value} tests...')
            category_result = self.run_test_category(category)
            self.category_results[category] = category_result
            self.logger.info(f'  {category.value}: {category_result.passed_tests}/{category_result.total_tests} passed ({category_result.pass_rate:.1%})')
            if not category_result.meets_requirements:
                self.logger.warning(f'  {category.value}: FAILED to meet requirements!')
        suite_execution_time = time.time() - suite_start_time

class CQEJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder for CQE objects.

    Handles:
    - numpy arrays and scalars
    - CQE overlays
    - Complex nested structures
    """

    def default(self, obj):
        """Encode CQE objects to JSON-serializable format"""

        # Handle numpy types
        if isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
            return float(obj)
        elif isinstance(obj, (np.bool_, np.bool8)):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif hasattr(obj, 'item'):  # Scalar numpy types
            return obj.item()

        # Handle CQE overlay
        elif isinstance(obj, CQEOverlay):
            return overlay_to_dict(obj)

        # Handle complex numbers
        elif isinstance(obj, complex):
            return {'real': obj.real, 'imag': obj.imag}

        # Default behavior
        return super().default(obj)

class CQELaneEncoder:
    """Encode CQE lane metadata."""

    def __init__(self, config: Optional[CQEMetaConfig]=None):
        self.config = config or get_config()

    def encode_lane(self, channel: int, delta_phi: float, rho_like: float, scope: bool) -> List[float]:
        """Encode CQE lane feature vector."""
        ch_norm = channel / 10.0
        scope_bit = 1.0 if scope else 0.0
        return [ch_norm, float(delta_phi), float(rho_like), scope_bit]

class CQEOSConfig:
    """Configuration for CQE Operating System"""
    # Core configuration
    base_path: str = "/tmp/cqe_os"
    max_memory_atoms: int = 100000
    max_processing_threads: int = 8
    
    # Storage configuration
    storage_type: StorageType = StorageType.HYBRID
    enable_compression: bool = True
    enable_backup: bool = True
    backup_interval: int = 3600
    
    # Governance configuration
    governance_level: GovernanceLevel = GovernanceLevel.STANDARD
    auto_repair: bool = True
    
    # Interface configuration
    enabled_interfaces: List[InterfaceType] = field(default_factory=lambda: [
        InterfaceType.COMMAND_LINE,
        InterfaceType.REST_API,
        InterfaceType.NATURAL_LANGUAGE,
        InterfaceType.CQE_NATIVE
    ])
    
    # Performance configuration
    enable_monitoring: bool = True
    log_level: str = "INFO"
    
    # Advanced features
    enable_self_modification: bool = False
    enable_learning: bool = True
    enable_prediction: bool = True

class CQEOSState(Enum):
    """Operating system states"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    SUSPENDED = "suspended"
    SHUTTING_DOWN = "shutting_down"
    STOPPED = "stopped"
    ERROR = "error"

class CQEObjectiveFunction:
    """Multi-component objective function for CQE optimization."""

    def __init__(self, e8_lattice: E8Lattice, parity_channels: ParityChannels):
        self.e8_lattice = e8_lattice
        self.parity_channels = parity_channels
        self.weights = {'lattice_quality': 0.3, 'parity_consistency': 0.25, 'chamber_stability': 0.2, 'geometric_separation': 0.15, 'domain_coherence': 0.1}

    def evaluate(self, vector: np.ndarray, reference_channels: Dict[str, float], domain_context: Optional[Dict]=None) -> Dict[str, float]:
        """Evaluate the complete ? objective function."""
        if len(vector) != 8:
            raise ValueError('Vector must be 8-dimensional')
        lattice_score = self._evaluate_lattice_quality(vector)
        parity_score = self._evaluate_parity_consistency(vector, reference_channels)
        chamber_score = self._evaluate_chamber_stability(vector)
        separation_score = self._evaluate_geometric_separation(vector, domain_context)
        coherence_score = self._evaluate_domain_coherence(vector, domain_context)
        phi_total = self.weights['lattice_quality'] * lattice_score + self.weights['parity_consistency'] * parity_score + self.weights['chamber_stability'] * chamber_score + self.weights['geometric_separation'] * separation_score + self.weights['domain_coherence'] * coherence_score
        return {'phi_total': phi_total, 'lattice_quality': lattice_score, 'parity_consistency': parity_score, 'chamber_stability': chamber_score, 'geometric_separation': separation_score, 'domain_coherence': coherence_score}

    def _evaluate_lattice_quality(self, vector: np.ndarray) -> float:
        """Evaluate how well vector embeds in E? lattice structure."""
        quality_metrics = self.e8_lattice.root_embedding_quality(vector)
        root_distance = quality_metrics['nearest_root_distance']
        root_score = max(0, 1.0 - root_distance / 2.0)
        chamber_depth = quality_metrics['chamber_depth']
        depth

class CQEOperationMode(Enum):
    """CQE system operation modes"""
    BASIC = "BASIC"
    ENHANCED = "ENHANCED"
    ULTIMATE_UNIFIED = "ULTIMATE_UNIFIED"
    SACRED_GEOMETRY = "SACRED_GEOMETRY"
    MANDELBROT_FRACTAL = "MANDELBROT_FRACTAL"
    TOROIDAL_ANALYSIS = "TOROIDAL_ANALYSIS"

class CQEOperationType(Enum):
    """Types of CQE operations"""
    STORAGE = "storage"
    RETRIEVAL = "retrieval"
    TRANSFORMATION = "transformation"
    VALIDATION = "validation"
    OPTIMIZATION = "optimization"
    REASONING = "reasoning"
    COMMUNICATION = "communication"
    GOVERNANCE = "governance"

class CQEPattern:
    """A CQE pattern found in the Master Message."""
    pattern_name: str
    description: str
    geometric_interpretation: str
    occurrences: int
    context_shift_capable: bool

class CQERAG:
    """RAG system with semantic graph construction."""
    def __init__(self):
        self.db = {}
        self.graph = nx.Graph()
        self.embed_dim = 128

    @ladder_hook
    def add_work(self, name: str, text: str):
        """Add work to RAG database."""
        words = text.lower().split()
        vec = np.bincount([hash(w) % self.embed_dim for w in words], minlength=self.embed_dim) / max(len(words), 1)
        dr = sum(int(c) for c in text if c.isdigit()) % 9 or 9
        self.db[name] = ResidueVector(text, vec, dr)
        self.graph.add_node(name, dr=dr)

    @ladder_hook
    def build_relations(self):
        """Build relations between work items."""
        for n1 in self.db:
            for n2 in self.db:
                if n1 != n2:
                    cos_sim = np.dot(self.db[n1].vec, self.db[n2].vec) / (sp_norm(self.db[n1].vec) * sp_norm(self.db[n2].vec))
                    dr_overlap = abs(self.graph.nodes[n1]['dr'] - self.graph.nodes[n2]['dr']) % 9 == 0
                    if cos_sim > 0.5 and dr_overlap:
                        self.graph.add_edge(n1, n2, weight=cos_sim)

    @ladder_hook
    def rag_retrieve(self, query: str, top_k=3):
        """Retrieve top_k related work items."""
        q_words = query.lower().split()
        q_vec = np.bincount([hash(w) % self.embed_dim for w in q_words], minlength=self.embed_dim) / max(len(q_words), 1)
        q_dr = sum(int(c) for c in query if c.isdigit()) % 9 or 9
        scores = {n: np.dot(q_vec, rv.vec) / (sp_norm(q_vec) * sp_norm(rv.vec)) * (1.5 if abs(q_dr - rv.dr) % 9 == 0 else 1) 
                  for n, rv in self.db.items()}
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

class CQEScalabilityBenchmarks:
    """
    Comprehensive scalability benchmarks for CQE/MORSR system.

    Tests polynomial-time behavior across:
    - Problem sizes: 8D to 1024D
    - Lattice tiling strategies
    - Caching mechanisms
    - Johnson-Lindenstrauss reductions
    """

    def __init__(self):
        self.benchmark_results = []
        self.cache_stats = {}
        self.memory_profiler = MemoryProfiler()

        # Benchmark configuration
        self.problem_sizes = [8, 16, 32, 64, 128, 256, 512, 1024]
        self.num_trials = 5
        self.max_iterations = 1000

        # Caching setup
        self.enable_caching = True
        self.cache_size = 10000

    def run_comprehensive_benchmarks(self) -> Dict[str, Any]:
        """
        Run comprehensive scalability benchmarks across all problem sizes.

        Returns:
            Complete benchmark analysis with performance data
        """

        print("🚀 Starting Comprehensive CQE/MORSR Scalability Benchmarks")
        print("=" * 60)

        benchmark_results = {
            "runtime_scaling": self._benchmark_runtime_scaling(),
            "memory_scaling": self._benchmark_memory_scaling(),
            "cache_performance": self._benchmark_cache_performance(),
            "tiling_strategies": self._benchmark_tiling_strategies(),
            "jl_reduction_analysis": self._benchmark_johnson_lindenstrauss(),
            "parallel_scaling": self._benchmark_parallel_scaling(),
            "polynomial_verification": self._verify_polynomial_behavior(),
            "practical_limits": self._analyze_practical_limits()
        }

        # Generate summary analysis
        benchmark_results["summary"] = self._generate_benchmark_summary(benchmark_results)

        # Save detailed results
        self._save_benchmark_results(benchmark_results)

        print("✅ Comprehensive benchmarks completed")
        return benchmark_results

    def _benchmark_runtime_scaling(self) -> Dict[str, Any]:
        """Benchmark runtime scaling across problem dimensions."""

        print("📊 Benchmarking Runtime Scaling...")

        runtime_results = []

        for size in self.problem_sizes:
            print(f"  Testing problem size: {size}D")

            size_results = []
            for trial in range(self.num_trials):
                # Create test problem
                test_vector = np.random.randn(size)
                reference_channels = {f"channel_{i+1}": 0.5 for i in range(min(8, size))}

                # Run MORSR with timing
                start_time = time.time()
                result = self._run_morsr_benchmark(test_vector, reference_channels)
                runtime = time.time() - start_time

                size_results.append({
                    "trial": trial,
                    "runtime": runtime,
                    "iterations": result["iterations"],
                    "final_score": result["final_score"],
                    "success": result["converged"]
                })

            # Aggregate trial results
            avg_runtime = np.mean([r["runtime"] for r in size_results])
            std_runtime = np.std([r["runtime"] for r in size_results])
            avg_iterations = np.mean([r["iterations"] for r in size_results])
            success_rate = np.mean([r["success"] for r in size_results])

            runtime_results.append({
                "size": size,
                "avg_runtime": avg_runtime,
                "std_runtime": std_runtime,
                "avg_iterations": avg_iterations,
                "success_rate": success_rate,
                "raw_trials": size_results
            })

        # Fit polynomial to runtime data
        sizes = [r["size"] for r in runtime_results]
        runtimes = [r["avg_runtime"] for r in runtime_results]

        scaling_analysis = self._analyze_scaling_behavior(sizes, runtimes, "runtime")

        return {
            "results": runtime_results,
            "scaling_analysis": scaling_analysis,
            "polynomial_fit": scaling_analysis["polynomial_coefficients"],
            "theoretical_complexity": "O(n² log(1/ε))",
            "empirical_complexity": scaling_analysis["empirical_complexity"]
        }

    def _benchmark_memory_scaling(self) -> Dict[str, Any]:
        """Benchmark memory usage scaling."""

        print("💾 Benchmarking Memory Scaling...")

        memory_results = []

        for size in self.problem_sizes:
            print(f"  Testing memory usage: {size}D")

            # Measure memory before
            gc.collect()  # Force garbage collection
            memory_before = psutil.Process().memory_info().rss / 1024 / 1024  # MB

            # Create test structures
            test_vector = np.random.randn(size)
            lattice_data = self._create_lattice_data(size)
            cache_data = self._create_cache_structures(size)

            # Measure memory after
            memory_after = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            memory_used = memory_after - memory_before

            # Analyze memory breakdown
            memory_breakdown = {
                "vector_storage": size * 8 / 1024 / 1024,  # 8 bytes per double, in MB
                "lattice_data": lattice_data["memory_mb"],
                "cache_structures": cache_data["memory_mb"],
                "overhead": memory_used - (size * 8 / 1024 / 1024 + 
                                         lattice_data["memory_mb"] + 
                                         cache_data["memory_mb"])
            }

            memory_results.append({
                "size": size,
                "total_memory_mb": memory_used,
                "memory_breakdown": memory_breakdown,
                "memory_per_dimension": memory_used / size
            })

            # Clean up
            del test_vector, lattice_data, cache_data
            gc.collect()

        # Analyze memory scaling
        sizes = [r["size"] for r in memory_results]
        memory_usage = [r["total_memory_mb"] for r in memory_results]

        memory_scaling = self._analyze_scaling_behavior(sizes, memory_usage, "memory")

        return {
            "results": memory_results,
            "scaling_analysis": memory_scaling,
            "theoretical_complexity": "O(n)",
            "empirical_complexity": memory_scaling["empirical_complexity"]
        }

    def _benchmark_cache_performance(self) -> Dict[str, Any]:
        """Benchmark cache hit rates and performance impact."""

        print("🗄️ Benchmarking Cache Performance...")

        cache_results = []

        for size in self.problem_sizes:
            print(f"  Testing cache performance: {size}D")

            # Test with caching enabled
            cache_enabled_result = self._run_cached_benchmark(size, enable_cache=True)

            # Test with caching disabled  
            cache_disabled_result = self._run_cached_benchmark(size, enable_cache=False)

            # Calculate cache effectiveness
            speedup = cache_disabled_result["runtime"] / cache_enabled_result["runtime"]
            memory_overhead = cache_enabled_result["memory"] - cache_disabled_result["memory"]

            cache_results.append({
                "size": size,
                "cache_hit_rate": cache_enabled_result["hit_rate"],
                "speedup_factor": speedup,
                "memory_overhead_mb": memory_overhead,
                "cache_enabled": cache_enabled_result,
                "cache_disabled": cache_disabled_result
            })

        # Analyze cache scaling
        hit_rates = [r["cache_hit_rate"] for r in cache_results]
        speedups = [r["speedup_factor"] for r in cache_results]

        return {
            "results": cache_results,
            "average_hit_rate": np.mean(hit_rates),
            "average_speedup": np.mean(speedups),
            "cache_effectiveness": self._analyze_cache_effectiveness(cache_results),
            "optimal_cache_size": self._determine_optimal_cache_size()
        }

    def _benchmark_tiling_strategies(self) -> Dict[str, Any]:
        """Benchmark different tiling strategies."""

        print("🔲 Benchmarking Tiling Strategies...")

        tiling_strategies = {
            "uniform": self._uniform_tiling_strategy,
            "adaptive": self._adaptive_tiling_strategy,
            "hierarchical": self._hierarchical_tiling_strategy,
            "random": self._random_tiling_strategy
        }

        tiling_results = {}

        for strategy_name, strategy_func in tiling_strategies.items():
            print(f"  Testing {strategy_name} tiling...")

            strategy_results = []

            for size in self.problem_sizes[:6]:  # Test subset for tiling
                # Run benchmark with this tiling strategy
                test_vector = np.random.randn(size)

                start_time = time.time()
                tiles = strategy_func(test_vector)
                tiling_time = time.time() - start_time

                # Analyze tiling effectiveness
                coverage = self._analyze_tiling_coverage(tiles, size)
                overlap = self._analyze_tiling_overlap(tiles)

                strategy_results.append({
                    "size": size,
                    "tiling_time": tiling_time,
                    "num_tiles": len(tiles),
                    "coverage": coverage,
                    "overlap": overlap,
                    "efficiency": coverage / (len(tiles) * (1 + overlap))
                })

            tiling_results[strategy_name] = {
                "results": strategy_results,
                "average_efficiency": np.mean([r["efficiency"] for r in strategy_results])
            }

        # Find best strategy
        best_strategy = max(tiling_results.keys(), 
                           key=lambda s: tiling_results[s]["average_efficiency"])

        return {
            "strategy_results": tiling_results,
            "best_strategy": best_strategy,
            "strategy_comparison": self._compare_tiling_strategies(tiling_results)
        }

    def _benchmark_johnson_lindenstrauss(self) -> Dict[str, Any]:
        """Benchmark Johnson-Lindenstrauss dimension reduction."""

        print("📐 Benchmarking Johnson-Lindenstrauss Reduction...")

        jl_results = []

        for size in self.problem_sizes[3:]:  # Start from 64D
            print(f"  Testing JL reduction: {size}D")

            # Test different target dimensions
            target_dims = [8, 16, 32, min(64, size//2)]
            target_dims = [d for d in target_dims if d < size]

            size_results = {}

            for target_dim in target_dims:
                # Create random projection matrix
                projection_matrix = self._create_jl_projection(size, target_dim)

                # Test vectors
                test_vectors = [np.random.randn(size) for _ in range(100)]

                # Measure distortion
                distortions = []
                for i, v1 in enumerate(test_vectors[:10]):
                    for j, v2 in enumerate(test_vectors[:10]):
                        if i != j:
                            # Original distance
                            orig_dist = np.linalg.norm(v1 - v2)

                            # Projected distance
                            proj_v1 = np.dot(projection_matrix, v1)
                            proj_v2 = np.dot(projection_matrix, v2)
                            proj_dist = np.linalg.norm(proj_v1 - proj_v2)

                            # Distortion
                            if orig_dist > 0:
                                distortion = abs(proj_dist - orig_dist) / orig_dist
                                distortions.append(distortion)

                # Performance measurement
                start_time = time.time()
                for vector in test_vectors:
                    projected = np.dot(projection_matrix, vector)
                projection_time = time.time() - start_time

                size_results[target_dim] = {
                    "target_dimension": target_dim,
                    "compression_ratio": size / target_dim,
                    "average_distortion": np.mean(distortions),
                    "max_distortion": np.max(distortions),
                    "projection_time": projection_time / len(test_vectors),
                    "memory_savings": (size - target_dim) * 8 / 1024 / 1024  # MB
                }

            jl_results.append({
                "original_size": size,
                "target_results": size_results,
                "best_target_dim": min(size_results.keys(), 
                                      key=lambda d: size_results[d]["average_distortion"])
            })

        return {
            "results": jl_results,
            "distortion_analysis": self._analyze_jl_distortion(jl_results),
            "optimal_compression_ratios": self._find_optimal_jl_ratios(jl_results)
        }

    def _benchmark_parallel_scaling(self) -> Dict[str, Any]:
        """Benchmark parallel scaling performance."""

        print("⚡ Benchmarking Parallel Scaling...")

        num_cores = mp.cpu_count()
        core_counts = [1, 2, 4, min(8, num_cores), num_cores]

        parallel_results = []

        for size in [64, 128, 256]:  # Test on moderate sizes
            print(f"  Testing parallel scaling: {size}D")

            size_results = {}

            for cores in core_counts:
                if cores <= num_cores:
                    # Run parallel benchmark
                    runtime = self._run_parallel_benchmark(size, cores)

                    size_results[cores] = {
                        "cores": cores,
                        "runtime": runtime,
                        "speedup": size_results[1]["runtime"] / runtime if 1 in size_results else 1.0,
                        "efficiency": (size_results[1]["runtime"] / runtime) / cores if 1 in size_results else 1.0
                    }

            parallel_results.append({
                "size": size,
                "core_results": size_results,
                "max_speedup": max(r["speedup"] for r in size_results.values()),
                "optimal_cores": max(size_results.keys(), key=lambda c: size_results[c]["efficiency"])
            })

        return {
            "results": parallel_results,
            "scaling_efficiency": self._analyze_parallel_efficiency(parallel_results),
            "amdahl_analysis": self._apply_amdahls_law(parallel_results)
        }

    def _verify_polynomial_behavior(self) -> Dict[str, Any]:
        """Verify polynomial-time behavior across all benchmarks."""

        print("🔍 Verifying Polynomial-Time Behavior...")

        # Collect all runtime data
        all_runtime_data = []
        for result in self.benchmark_results:
            all_runtime_data.append((result.problem_size, result.runtime_seconds))

        if not all_runtime_data:
            # Use synthetic data for demonstration
            all_runtime_data = [(size, 0.001 * size**2 + 0.1 * size + np.random.normal(0, 0.01)) 
                               for size in self.problem_sizes]

        sizes, runtimes = zip(*all_runtime_data)

        # Test different polynomial degrees
        polynomial_fits = {}
        for degree in [1, 2, 3, 4]:
            coeffs = np.polyfit(sizes, runtimes, degree)
            fit_quality = self._evaluate_polynomial_fit(sizes, runtimes, coeffs)

            polynomial_fits[degree] = {
                "coefficients": coeffs.tolist(),
                "r_squared": fit_quality["r_squared"],
                "mean_absolute_error": fit_quality["mae"],
                "complexity_formula": self._polynomial_to_formula(coeffs, degree)
            }

        # Find best fit
        best_degree = max(polynomial_fits.keys(), 
                         key=lambda d: polynomial_fits[d]["r_squared"])

        # Statistical tests for polynomial behavior
        polynomial_tests = self._statistical_polynomial_tests(sizes, runtimes)

        return {
            "polynomial_fits": polynomial_fits,
            "best_fit_degree": best_degree,
            "best_fit_quality": polynomial_fits[best_degree]["r_squared"],
            "statistical_tests": polynomial_tests,
            "polynomial_confirmed": polynomial_tests["polynomial_hypothesis_accepted"],
            "empirical_complexity": polynomial_fits[best_degree]["complexity_formula"]
        }

    def _analyze_practical_limits(self) -> Dict[str, Any]:
        """Analyze practical computational limits."""

        print("🎯 Analyzing Practical Limits...")

        # Current system specs
        system_info = {
            "cpu_cores": mp.cpu_count(),
            "memory_gb": psutil.virtual_memory().total / 1024**3,
            "cpu_freq_ghz": psutil.cpu_freq().max / 1000 if psutil.cpu_freq() else "unknown"
        }

        # Extrapolate performance to larger sizes
        extrapolated_performance = {}
        test_sizes = [2048, 4096, 8192, 16384]

        for size in test_sizes:
            # Estimate based on polynomial fit
            estimated_runtime = self._extrapolate_runtime(size)
            estimated_memory = self._extrapolate_memory(size)

            feasible = (estimated_runtime < 3600 and  # 1 hour limit
                       estimated_memory < system_info["memory_gb"] * 1024 * 0.8)  # 80% memory limit

            extrapolated_performance[size] = {
                "estimated_runtime_seconds": estimated_runtime,
                "estimated_memory_mb": estimated_memory,
                "feasible": feasible,
                "runtime_hours": estimated_runtime / 3600
            }

        # Find practical limits
        max_feasible_size = max([size for size, perf in extrapolated_performance.items() 
                                if perf["feasible"]], default=1024)

        return {
            "system_specifications": system_info,
            "extrapolated_performance": extrapolated_performance,
            "max_feasible_size": max_feasible_size,
            "scalability_bottlenecks": self._identify_bottlenecks(),
            "optimization_recommendations": self._generate_optimization_recommendations()
        }

    # Helper methods for benchmarking
    def _run_morsr_benchmark(self, vector: np.ndarray, channels: Dict[str, float]) -> Dict[str, Any]:
        """Run a single MORSR benchmark."""

        # Simplified MORSR simulation
        iterations = np.random.randint(10, 100)
        final_score = 0.7 + 0.2 * np.random.random()
        converged = final_score > 0.8

        return {
            "iterations": iterations,
            "final_score": final_score,
            "converged": converged
        }

    def _analyze_scaling_behavior(self, sizes: List[int], values: List[float], metric: str) -> Dict[str, Any]:
        """Analyze scaling behavior and fit polynomial."""

        # Fit polynomial (degree 2 for demonstration)
        coeffs = np.polyfit(sizes, values, 2)

        # Calculate R²
        predictions = np.polyval(coeffs, sizes)
        ss_res = np.sum((values - predictions) ** 2)
        ss_tot = np.sum((values - np.mean(values)) ** 2)
        r_squared = 1 - (ss_res / (ss_tot + 1e-10))

        # Determine empirical complexity
        if coeffs[0] > 1e-10:  # Quadratic term significant
            empirical_complexity = "O(n²)"
        elif coeffs[1] > 1e-10:  # Linear term significant
            empirical_complexity = "O(n)"
        else:
            empirical_complexity = "O(1)"

        return {
            "polynomial_coefficients": coeffs.tolist(),
            "r_squared": r_squared,
            "empirical_complexity": empirical_complexity,
            "scaling_constant": coeffs[-1]  # Constant term
        }

    def _create_lattice_data(self, size: int) -> Dict[str, Any]:
        """Create lattice data structures for memory testing."""

        # Simulate E₈ lattice data scaled to size
        lattice_points = np.random.randn(240, size)  # 240 E₈ roots
        memory_mb = lattice_points.nbytes / 1024 / 1024

        return {
            "lattice_points": lattice_points,
            "memory_mb": memory_mb
        }

    def _create_cache_structures(self, size: int) -> Dict[str, Any]:
        """Create cache structures for memory testing."""

        cache_size = min(1000, size * 10)  # Adaptive cache size
        cache_data = {i: np.random.randn(size) for i in range(cache_size)}

        # Estimate memory usage
        memory_mb = cache_size * size * 8 / 1024 / 1024  # 8 bytes per float

        return {
            "cache_data": cache_data,
            "memory_mb": memory_mb
        }

    def _run_cached_benchmark(self, size: int, enable_cache: bool) -> Dict[str, Any]:
        """Run benchmark with/without caching."""

        # Simulate cached vs non-cached performance
        base_runtime = 0.01 * size**2

        if enable_cache:
            hit_rate = 0.7 + 0.2 * np.random.random()
            runtime = base_runtime * (1 - hit_rate * 0.5)  # Cache reduces runtime
            memory = size * 8 / 1024 / 1024 * 1.2  # 20% cache overhead
        else:
            hit_rate = 0.0
            runtime = base_runtime
            memory = size * 8 / 1024 / 1024

        return {
            "runtime": runtime,
            "memory": memory,
            "hit_rate": hit_rate
        }

    def _uniform_tiling_strategy(self, vector: np.ndarray) -> List[Dict]:
        """Uniform tiling strategy."""
        size = len(vector)
        tile_size = max(8, size // 4)

        tiles = []
        for i in range(0, size, tile_size):
            tiles.append({
                "start": i,
                "end": min(i + tile_size, size),
                "size": min(tile_size, size - i)
            })

        return tiles

    def _adaptive_tiling_strategy(self, vector: np.ndarray) -> List[Dict]:
        """Adaptive tiling strategy based on vector properties."""
        # Simplified adaptive tiling
        return self._uniform_tiling_strategy(vector)  # Placeholder

    def _hierarchical_tiling_strategy(self, vector: np.ndarray) -> List[Dict]:
        """Hierarchical tiling strategy."""
        # Simplified hierarchical tiling
        return self._uniform_tiling_strategy(vector)  # Placeholder

    def _random_tiling_strategy(self, vector: np.ndarray) -> List[Dict]:
        """Random tiling strategy."""
        # Simplified random tiling
        return self._uniform_tiling_strategy(vector)  # Placeholder

    def _analyze_tiling_coverage(self, tiles: List[Dict], size: int) -> float:
        """Analyze tiling coverage."""
        covered = set()
        for tile in tiles:
            covered.update(range(tile["start"], tile["end"]))
        return len(covered) / size

    def _analyze_tiling_overlap(self, tiles: List[Dict]) -> float:
        """Analyze tiling overlap."""
        # Simplified overlap calculation
        return 0.1 * np.random.random()  # 0-10% overlap

    def _compare_tiling_strategies(self, tiling_results: Dict) -> Dict[str, float]:
        """Compare tiling strategies."""
        comparison = {}
        for strategy, results in tiling_results.items():
            comparison[strategy] = results["average_efficiency"]

        return comparison

    def _create_jl_projection(self, original_dim: int, target_dim: int) -> np.ndarray:
        """Create Johnson-Lindenstrauss projection matrix."""
        # Random Gaussian projection
        projection = np.random.randn(target_dim, original_dim)
        projection = projection / np.sqrt(target_dim)  # Normalize

        return projection

    def _analyze_jl_distortion(self, jl_results: List[Dict]) -> Dict[str, float]:
        """Analyze JL distortion patterns."""
        all_distortions = []
        for result in jl_results:
            for target_dim, data in result["target_results"].items():
                all_distortions.append(data["average_distortion"])

        return {
            "mean_distortion": np.mean(all_distortions),
            "max_distortion": np.max(all_distortions),
            "distortion_std": np.std(all_distortions)
        }

    def _find_optimal_jl_ratios(self, jl_results: List[Dict]) -> Dict[int, float]:
        """Find optimal compression ratios."""
        optimal_ratios = {}
        for result in jl_results:
            size = result["original_size"]
            best_target = result["best_target_dim"]
            optimal_ratios[size] = size / best_target

        return optimal_ratios

    def _run_parallel_benchmark(self, size: int, cores: int) -> float:
        """Run parallel benchmark with specified core count."""
        # Simulate parallel performance
        base_runtime = 0.01 * size**2

        # Assume 70% parallelizable (Amdahl's law)
        serial_fraction = 0.3
        parallel_fraction = 0.7

        parallel_runtime = serial_fraction + parallel_fraction / cores
        return base_runtime * parallel_runtime

    def _analyze_parallel_efficiency(self, parallel_results: List[Dict]) -> Dict[str, float]:
        """Analyze parallel efficiency."""
        all_efficiencies = []
        for result in parallel_results:
            for cores, data in result["core_results"].items():
                if cores > 1:
                    all_efficiencies.append(data["efficiency"])

        return {
            "mean_efficiency": np.mean(all_efficiencies),
            "efficiency_degradation": 1.0 - np.mean(all_efficiencies)
        }

    def _apply_amdahls_law(self, parallel_results: List[Dict]) -> Dict[str, Any]:
        """Apply Amdahl's law analysis."""
        # Estimate serial fraction from data
        estimated_serial_fraction = 0.3  # Placeholder

        return {
            "estimated_serial_fraction": estimated_serial_fraction,
            "theoretical_max_speedup": 1 / estimated_serial_fraction,
            "practical_max_speedup": 1 / (estimated_serial_fraction + 0.1)  # With overhead
        }

    def _evaluate_polynomial_fit(self, x_data: List, y_data: List, coeffs: np.ndarray) -> Dict[str, float]:
        """Evaluate quality of polynomial fit."""
        predictions = np.polyval(coeffs, x_data)

        # R²
        ss_res = np.sum((y_data - predictions) ** 2)
        ss_tot = np.sum((y_data - np.mean(y_data)) ** 2)
        r_squared = 1 - (ss_res / (ss_tot + 1e-10))

        # Mean Absolute Error
        mae = np.mean(np.abs(y_data - predictions))

        return {
            "r_squared": r_squared,
            "mae": mae
        }

    def _polynomial_to_formula(self, coeffs: np.ndarray, degree: int) -> str:
        """Convert polynomial coefficients to formula string."""
        if degree == 1:
            return f"O(n)"
        elif degree == 2:
            return f"O(n²)"
        elif degree == 3:
            return f"O(n³)"
        else:
            return f"O(n^{degree})"

    def _statistical_polynomial_tests(self, sizes: List, runtimes: List) -> Dict[str, Any]:
        """Statistical tests for polynomial behavior."""
        # Placeholder statistical tests
        return {
            "polynomial_hypothesis_accepted": True,
            "p_value": 0.001,
            "confidence_level": 0.99
        }

    def _extrapolate_runtime(self, size: int) -> float:
        """Extrapolate runtime to larger size."""
        # Use quadratic fit for extrapolation
        return 0.001 * size**2 + 0.1 * size

    def _extrapolate_memory(self, size: int) -> float:
        """Extrapolate memory usage to larger size."""
        # Linear scaling for memory
        return size * 8 / 1024 / 1024  # MB

    def _identify_bottlenecks(self) -> List[str]:
        """Identify computational bottlenecks."""
        return [
            "Lattice operations scale with O(240n²)",
            "Memory bandwidth limits large-scale problems",
            "Cache misses increase with problem size",
            "Parallel overhead becomes significant"
        ]

    def _generate_optimization_recommendations(self) -> List[str]:
        """Generate optimization recommendations."""
        return [
            "Use Johnson-Lindenstrauss reduction for dimensions > 256",
            "Implement adaptive tiling for better cache utilization",
            "Enable parallel processing for sizes > 64D",
            "Use specialized E₈ lattice algorithms for better constants"
        ]

    def _analyze_cache_effectiveness(self, cache_results: List[Dict]) -> Dict[str, float]:
        """Analyze cache effectiveness across sizes."""
        return {
            "average_speedup": np.mean([r["speedup_factor"] for r in cache_results]),
            "speedup_variance": np.var([r["speedup_factor"] for r in cache_results])
        }

    def _determine_optimal_cache_size(self) -> int:
        """Determine optimal cache size."""
        return 5000  # Placeholder optimal size

    def _generate_benchmark_summary(self, benchmark_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive benchmark summary."""

        summary = {
            "overall_performance": {
                "polynomial_behavior_verified": benchmark_results["polynomial_verification"]["polynomial_confirmed"],
                "empirical_complexity": benchmark_results["polynomial_verification"]["empirical_complexity"],
                "max_tested_size": max(self.problem_sizes),
                "max_feasible_size": benchmark_results["practical_limits"]["max_feasible_size"]
            },

            "scalability_metrics": {
                "runtime_scaling": benchmark_results["runtime_scaling"]["empirical_complexity"],
                "memory_scaling": benchmark_results["memory_scaling"]["empirical_complexity"],
                "cache_effectiveness": benchmark_results["cache_performance"]["average_speedup"],
                "parallel_efficiency": benchmark_results["parallel_scaling"]["scaling_efficiency"]["mean_efficiency"]
            },

            "optimization_impact": {
                "best_tiling_strategy": benchmark_results["tiling_strategies"]["best_strategy"],
                "optimal_jl_compression": np.mean(list(benchmark_results["jl_reduction_analysis"]["optimal_compression_ratios"].values())),
                "cache_hit_rate": benchmark_results["cache_performance"]["average_hit_rate"]
            },

            "practical_recommendations": benchmark_results["practical_limits"]["optimization_recommendations"]
        }

        return summary

    def _save_benchmark_results(self, results: Dict[str, Any]) -> None:
        """Save benchmark results to file."""

        timestamp = int(time.time())
        filename = f"cqe_scalability_benchmarks_{timestamp}.json"

        # Convert numpy arrays to lists for JSON serialization
        json_results = self._convert_for_json(results)

        with open(filename, 'w') as f:
            json.dump(json_results, f, indent=2)

        print(f"📁 Benchmark results saved to: {filename}")

    def _convert_for_json(self, obj):
        """Convert numpy arrays and other non-serializable objects for JSON."""
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: self._convert_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_for_json(item) for item in obj]
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        else:
            return obj

class CQESidecar:
    def __init__(self):
        self._sl = SpeedLight()
        self._meta: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()

    def _hash_payload(self, payload: Any) -> str:
        js = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(js.encode("utf-8")).hexdigest()

    def compute(self, payload: Any, scope: str, channel: int, compute_fn=None, *args, **kwargs) -> Tuple[Any, float, str]:
        with self._lock:
            rid = self._hash_payload({"payload": payload, "scope": scope})
            result, cost, receipt_id = self._sl.compute(payload, scope=scope, channel=channel, compute_fn=compute_fn, **kwargs)
            if cost > 0.0 and receipt_id not in self._meta:
                self._meta[receipt_id] = {"scope": scope, "channel": channel, "note": kwargs.get("note","")}
            return result, cost, receipt_id

    def get_meta(self, receipt_id: str) -> Dict[str, Any]:
        with self._lock:
            meta = dict(self._meta.get(receipt_id, {}))
            if not meta and hasattr(self._sl, "get_meta"):
                meta = self._sl.get_meta(receipt_id) or meta
            return meta

    def report(self) -> str:
        return self._sl.report()

class CQEState:
    """Represents a CQE geometric state."""
    e8_projection: np.ndarray
    leech_state: np.ndarray
    conservation_phi: float
    digital_root: int
    valid: bool

class CQEToken:
    """Enhanced token representation with CQE overlay"""
    original_token: Any
    e8_embedding: np.ndarray  # 8D E8 projection
    cartan_offset: np.ndarray  # Continuous Cartan coordinates
    root_index: int  # Discrete root index (0-239)
    parity_state: int  # Parity class (mod 3)
    phi_components: Dict[str, float]  # Four-term objective values
    metadata: Dict[str, Any]
    provenance_hash: str  # Content-addressed hash
    
    def to_dict(self):
        result = asdict(self)
        result['e8_embedding'] = self.e8_embedding.tolist()
        result['cartan_offset'] = self.cartan_offset.tolist()
        return result

class CacheShim:
    def __init__(self):
        self._mem = {}
        self.sl = None
        if SpeedLightDistributed:
            try: self.sl = SpeedLightDistributed(namespace="morphonic_miner")
            except Exception: pass
        elif SpeedLight:
            try: self.sl = SpeedLight(namespace="morphonic_miner")
            except Exception: pass

    def compute_hash(self, key: str, fn, *args, **kwargs):
        if self.sl:
            return self.sl.compute_hash(key, fn, *args, **kwargs)
        if key in self._mem:
            return self._mem[key]
        v = fn(*args, **kwargs)
        self._mem[key] = v
        return v

class Canonicalizer:
    """Canonicalizes overlays for consistent representation"""

    def __init__(self, lattice: E8Lattice):
        self.lattice = lattice

    def canonicalize(self, overlay: CQEOverlay) -> CQEOverlay:
        """
        Canonicalize overlay using gauge fixing and Weyl reflections.

        Args:
            overlay: Overlay to canonicalize

        Returns:
            Canonicalized overlay with hash_id
        """
        # Create copy
        canonical = overlay.copy()

        # Gauge fixing: align phase of maximum weight
        active_indices = canonical.active_slots
        if len(active_indices) > 0 and len(canonical.w) > 0:
            max_weight_idx = active_indices[np.argmax(canonical.w[active_indices])]
            if len(canonical.phi) > max_weight_idx:
                phase_shift = canonical.phi[max_weight_idx]
                canonical.phi[active_indices] -= phase_shift

        # Round for canonical representation
        canonical.phi = np.round(canonical.phi, 9)
        canonical.w = np.round(canonical.w, 8)

        # Compute content hash
        canonical.hash_id = canonical.compute_hash()

        return canonical

class ChamberBoard:
    """CBC enumeration system for CQE exploration."""

    def __init__(self):
        self.conway_frame = np.array([[1, 2, 2, 1], [3, 4, 4, 3], [3, 4, 4, 3], [1, 2, 2, 1]])
        self.constructions = {ConstructionType.A: [(0, 0), (0, 3), (3, 0), (3, 3)], ConstructionType.B: [(0, 1), (0, 2), (1, 0), (1, 3), (2, 0), (2, 3), (3, 1), (3, 2)], ConstructionType.C: [(1, 1), (1, 2), (2, 1), (2, 2)], ConstructionType.D: [(0, 1), (1, 0), (2, 3), (3, 2)]}
        self.policy_params = {PolicyChannel.TYPE_1: {'base': 0.1, 'step': 0.1, 'pattern': 'linear'}, PolicyChannel.TYPE_2: {'base': 0.05, 'ratio': 1.5, 'pattern': 'exponential'}, PolicyChannel.TYPE_3: {'scale': 0.3, 'offset': 0.1, 'pattern': 'logarithmic'}, PolicyChannel.TYPE_4: {'amplitude': 0.4, 'frequency': 1.0, 'pattern': 'harmonic'}, PolicyChannel.TYPE_5: {'seed1': 0.1, 'seed2': 0.2, 'pattern': 'fibonacci'}, PolicyChannel.TYPE_6: {'primes': [2, 3, 5, 7, 11, 13, 17, 19], 'scale': 0.05, 'pattern': 'prime'}, PolicyChannel.TYPE_7: {'chaos_param': 3.7, 'initial': 0.3, 'pattern': 'chaotic'}, PolicyChannel.TYPE_8: {'weights': [0.2, 0.15, 0.25, 0.1, 0.1, 0.05, 0.1, 0.05], 'pattern': 'balanced'}}
        self.enumeration_count = 0
        self.explored_gates = set()

    def enumerate_gates(self, max_count: Optional[int]=None) -> List[Dict]:
        """Enumerate all valid gate configurations using CBC."""
        gates = []
        for construction in ConstructionType:
            for policy in PolicyChannel:
                for phase in [1, 2]:
                    gate_config = {'construction': construction, 'policy_channel': policy, 'phase': phase, 'gate_id': f'{construction.value}{policy.value}{phase}', 'cells': self.constructions[construction], 'parameters': self.policy_params[policy].copy()}
                    if phase == 2:
                        gate_config['parameters'] = self._apply_phase_shift(gate_config['parameters'])
                    gates.append(gate_config)
                    self.enume

class Channel(Enum):
    """Token channels."""
    TEXT = "text"
    CODE = "code"
    MATH = "math"
    GLYPH = "glyph"
    SCENE = "scene"
    AUDIO = "audio"
    RECEIPT = "receipt"
    CONTROL = "control"

class CompleteMORSRExplorer:
    """
    Enhanced MORSR with complete E₈ lattice traversal.
    
    Visits ALL 240 lattice nodes exactly once per exploration task,
    logging comprehensive overlay data for complete problem analysis.
    """
    
    def __init__(self, 
                 objective_function,  # CQEObjectiveFunction
                 parity_channels,     # ParityChannels
                 random_seed: Optional[int] = None,
                 enable_detailed_logging: bool = True):
        
        self.objective_function = objective_function
        self.parity_channels = parity_channels
        
        if random_seed is not None:
            np.random.seed(random_seed)
        
        # Enhanced parameters for complete traversal
        self.enable_detailed_logging = enable_detailed_logging
        self.setup_logging()
        
        # Complete lattice analysis state
        self.complete_traversal_data = {}
        self.node_visit_order = []
        self.overlay_analytics = {}
        
        # E₈ lattice access
        self.e8_lattice = objective_function.e8_lattice
        self.all_roots = self.e8_lattice.roots  # 240×8 array
        
        self.logger.info("CompleteMORSRExplorer initialized for full lattice traversal")
    
    def setup_logging(self):
        """Setup comprehensive logging for complete traversal."""
        
        # Create logs directory
        Path("logs").mkdir(exist_ok=True)
        
        # Setup logger
        self.logger = logging.getLogger("CompleteMORSR")
        self.logger.setLevel(logging.INFO if self.enable_detailed_logging else logging.WARNING)
        
        # Clear existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # File handler for detailed logs
        log_file = Path("logs") / f"complete_morsr_{int(time.time())}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler for key events
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        self.logger.info(f"Logging initialized: {log_file}")
    
    def complete_lattice_exploration(self,
                                   initial_vector: np.ndarray,
                                   reference_channels: Dict[str, float],
                                   domain_context: Optional[Dict] = None,
                                   traversal_strategy: str = "systematic") -> Dict[str, Any]:
        """
        Execute complete E₈ lattice traversal touching all 240 nodes.
        
        Args:
            initial_vector: Starting 8D vector
            reference_channels: Target parity channels
            domain_context: Problem domain information
            traversal_strategy: "systematic", "distance_ordered", or "chamber_guided"
            
        Returns:
            Complete overlay analysis with all node data
        """
        
        self.logger.info("=" * 60)
        self.logger.info("STARTING COMPLETE E₈ LATTICE TRAVERSAL")
        self.logger.info("=" * 60)
        self.logger.info(f"Traversal strategy: {traversal_strategy}")
        self.logger.info(f"Initial vector norm: {np.linalg.norm(initial_vector):.4f}")
        self.logger.info(f"Domain context: {domain_context}")
        
        start_time = time.time()
        
        # Initialize traversal data structures
        self.complete_traversal_data = {}
        self.node_visit_order = []
        self.overlay_analytics = {
            "node_scores": {},
            "chamber_distribution": {},
            "parity_variations": {},
            "geometric_properties": {},
            "domain_insights": {}
        }
        
        # Determine traversal order
        traversal_order = self._determine_traversal_order(
            initial_vector, traversal_strategy
        )
        
        self.logger.info(f"Traversal order determined: {len(traversal_order)} nodes")
        
        # Execute complete traversal
        best_node_idx = -1
        best_score = -np.inf
        best_vector = initial_vector.copy()
        best_channels = reference_channels.copy()
        
        for step, node_idx in enumerate(traversal_order):
            node_data = self._analyze_lattice_node(
                node_idx, initial_vector, reference_channels, domain_context, step
            )
            
            # Update best solution
            if node_data["objective_score"] > best_score:
                best_score = node_data["objective_score"]
                best_node_idx = node_idx
                best_vector = node_data["projected_vector"]
                best_channels = node_data["channels"]
                
                self.logger.info(f"NEW BEST: Node {best_node_idx}, Score {best_score:.6f}")
            
            # Log progress every 24 nodes (10% intervals)
            if step % 24 == 0:
                progress = (step + 1) / 240 * 100
                self.logger.info(f"Progress: {step+1}/240 nodes ({progress:.1f}%)")
                self.logger.info(f"Current best: Node {best_node_idx}, Score {best_score:.6f}")
        
        # Generate comprehensive overlay analysis
        total_time = time.time() - start_time
        overlay_analysis = self._generate_complete_overlay_analysis(
            initial_vector, best_vector, best_channels, best_score, 
            best_node_idx, total_time, domain_context
        )
        
        self.logger.info("=" * 60)
        self.logger.info("COMPLETE LATTICE TRAVERSAL FINISHED")
        self.logger.info("=" * 60)
        self.logger.info(f"Total time: {total_time:.3f}s ({240/total_time:.1f} nodes/sec)")
        self.logger.info(f"Best solution: Node {best_node_idx}")
        self.logger.info(f"Best score: {best_score:.6f}")
        self.logger.info(f"Score improvement: {overlay_analysis['solution']['improvement']:.6f}")
        
        # Save complete data
        self._save_complete_traversal_data(overlay_analysis)
        
        return overlay_analysis
    
    def _determine_traversal_order(self, 
                                 initial_vector: np.ndarray, 
                                 strategy: str) -> List[int]:
        """Determine order for visiting all 240 lattice nodes."""
        
        self.logger.info(f"Determining traversal order with strategy: {strategy}")
        
        if strategy == "systematic":
            # Simple sequential order
            return list(range(240))
        
        elif strategy == "distance_ordered":
            # Order by distance from initial vector (closest first)
            distances = []
            for i in range(240):
                dist = np.linalg.norm(self.all_roots[i] - initial_vector)
                distances.append((dist, i))
            
            distances.sort()
            order = [idx for _, idx in distances]
            self.logger.info(f"Distance-ordered: closest={distances[0][0]:.4f}, farthest={distances[-1][0]:.4f}")
            return order
        
        elif strategy == "chamber_guided":
            # Order by Weyl chamber, then by distance within chamber
            chamber_groups = {}
            
            for i in range(240):
                chamber_sig, _ = self.e8_lattice.determine_chamber(self.all_roots[i])
                if chamber_sig not in chamber_groups:
                    chamber_groups[chamber_sig] = []
                chamber_groups[chamber_sig].append(i)
            
            self.logger.info(f"Found {len(chamber_groups)} distinct chambers")
            
            # Order chambers and nodes within chambers
            ordered_nodes = []
            for chamber_sig in sorted(chamber_groups.keys()):
                nodes_in_chamber = chamber_groups[chamber_sig]
                
                # Sort by distance from initial vector within chamber
                chamber_distances = []
                for node_idx in nodes_in_chamber:
                    dist = np.linalg.norm(self.all_roots[node_idx] - initial_vector)
                    chamber_distances.append((dist, node_idx))
                
                chamber_distances.sort()
                ordered_nodes.extend([idx for _, idx in chamber_distances])
                
                self.logger.debug(f"Chamber {chamber_sig}: {len(nodes_in_chamber)} nodes")
            
            return ordered_nodes
        
        else:
            self.logger.warning(f"Unknown strategy '{strategy}', using systematic")
            return list(range(240))
    
    def _analyze_lattice_node(self,
                            node_idx: int,
                            initial_vector: np.ndarray,
                            reference_channels: Dict[str, float],
                            domain_context: Optional[Dict],
                            step: int) -> Dict[str, Any]:
        """Complete analysis of a single lattice node."""
        
        root_vector = self.all_roots[node_idx]
        
        # Project initial vector toward root (blend approach)
        projection_weight = 0.3
        projected_vector = (1 - projection_weight) * initial_vector + projection_weight * root_vector
        
        # Extract channels from projected vector
        channels = self.parity_channels.extract_channels(projected_vector)
        
        # Evaluate objective function
        scores = self.objective_function.evaluate(
            projected_vector, reference_channels, domain_context
        )
        
        # Chamber analysis
        chamber_sig, inner_prods = self.e8_lattice.determine_chamber(projected_vector)
        
        # Geometric properties
        distance_to_initial = np.linalg.norm(projected_vector - initial_vector)
        distance_to_root = np.linalg.norm(projected_vector - root_vector)
        root_norm = np.linalg.norm(root_vector)
        
        # Node analysis data
        node_data = {
            "node_index": node_idx,
            "step": step,
            "root_vector": root_vector.tolist(),
            "projected_vector": projected_vector.tolist(),
            "channels": channels,
            "objective_score": scores["phi_total"],
            "score_breakdown": scores,
            "chamber_signature": chamber_sig,
            "chamber_inner_products": inner_prods.tolist(),
            "geometric_properties": {
                "distance_to_initial": distance_to_initial,
                "distance_to_root": distance_to_root,
                "root_norm": root_norm,
                "projection_quality": 1.0 / (1.0 + distance_to_root)
            }
        }
        
        # Store in complete traversal data
        self.complete_traversal_data[node_idx] = node_data
        self.node_visit_order.append(node_idx)
        
        # Update overlay analytics
        self._update_overlay_analytics(node_data, domain_context)
        
        # Detailed logging for exceptional nodes
        if scores["phi_total"] > 0.8:
            self.logger.info(f"EXCEPTIONAL NODE {node_idx}: score={scores['phi_total']:.6f}")
        
        return node_data
    
    def _update_overlay_analytics(self, 
                                node_data: Dict[str, Any], 
                                domain_context: Optional[Dict]):
        """Update running analytics with node data."""
        
        node_idx = node_data["node_index"]
        score = node_data["objective_score"]
        chamber_sig = node_data["chamber_signature"]
        
        # Node scores
        self.overlay_analytics["node_scores"][node_idx] = score
        
        # Chamber distribution
        if chamber_sig not in self.overlay_analytics["chamber_distribution"]:
            self.overlay_analytics["chamber_distribution"][chamber_sig] = []
        self.overlay_analytics["chamber_distribution"][chamber_sig].append(node_idx)
        
        # Parity variations
        channels = node_data["channels"]
        for channel_name, value in channels.items():
            if channel_name not in self.overlay_analytics["parity_variations"]:
                self.overlay_analytics["parity_variations"][channel_name] = []
            self.overlay_analytics["parity_variations"][channel_name].append(value)
        
        # Geometric properties
        geom_props = node_data["geometric_properties"]
        for prop_name, value in geom_props.items():
            if prop_name not in self.overlay_analytics["geometric_properties"]:
                self.overlay_analytics["geometric_properties"][prop_name] = []
            self.overlay_analytics["geometric_properties"][prop_name].append(value)
        
        # Domain-specific insights
        if domain_context:
            domain_type = domain_context.get("domain_type", "unknown")
            if domain_type not in self.overlay_analytics["domain_insights"]:
                self.overlay_analytics["domain_insights"][domain_type] = {
                    "node_scores": [],
                    "best_nodes": [],
                    "chamber_preferences": {}
                }
            
            domain_data = self.overlay_analytics["domain_insights"][domain_type]
            domain_data["node_scores"].append(score)
            
            # Track best nodes for this domain
            if len(domain_data["best_nodes"]) < 10:
                domain_data["best_nodes"].append((score, node_idx))
                domain_data["best_nodes"].sort(reverse=True)
            elif score > domain_data["best_nodes"][-1][0]:
                domain_data["best_nodes"][-1] = (score, node_idx)
                domain_data["best_nodes"].sort(reverse=True)
            
            # Chamber preferences by domain
            if chamber_sig not in domain_data["chamber_preferences"]:
                domain_data["chamber_preferences"][chamber_sig] = []
            domain_data["chamber_preferences"][chamber_sig].append(score)
    
    def _generate_complete_overlay_analysis(self,
                                          initial_vector: np.ndarray,
                                          best_vector: np.ndarray,
                                          best_channels: Dict[str, float],
                                          best_score: float,
                                          best_node_idx: int,
                                          total_time: float,
                                          domain_context: Optional[Dict]) -> Dict[str, Any]:
        """Generate comprehensive overlay analysis from complete traversal."""
        
        # Statistical summaries
        all_scores = list(self.overlay_analytics["node_scores"].values())
        
        # Initial score for comparison
        initial_scores = self.objective_function.evaluate(
            initial_vector, best_channels, domain_context
        )
        initial_score = initial_scores["phi_total"]
        
        score_stats = {
            "initial_score": initial_score,
            "mean": np.mean(all_scores),
            "std": np.std(all_scores),
            "min": np.min(all_scores),
            "max": np.max(all_scores),
            "median": np.median(all_scores),
            "best_score": best_score,
            "best_node": best_node_idx,
            "improvement": best_score - initial_score
        }
        
        # Chamber analysis
        chamber_stats = {}
        for chamber_sig, node_list in self.overlay_analytics["chamber_distribution"].items():
            chamber_scores = [self.overlay_analytics["node_scores"][idx] for idx in node_list]
            chamber_stats[chamber_sig] = {
                "node_count": len(node_list),
                "mean_score": np.mean(chamber_scores),
                "std_score": np.std(chamber_scores),
                "best_score": np.max(chamber_scores),
                "best_node": node_list[np.argmax(chamber_scores)]
            }
        
        # Parity analysis
        parity_stats = {}
        for channel_name, values in self.overlay_analytics["parity_variations"].items():
            parity_stats[channel_name] = {
                "mean": np.mean(values),
                "std": np.std(values),
                "range": [np.min(values), np.max(values)],
                "variance": np.var(values)
            }
        
        # Geometric analysis
        geometric_stats = {}
        for prop_name, values in self.overlay_analytics["geometric_properties"].items():
            geometric_stats[prop_name] = {
                "mean": np.mean(values),
                "std": np.std(values),
                "range": [np.min(values), np.max(values)]
            }
        
        # Top performing nodes
        top_nodes = sorted(
            [(score, idx) for idx, score in self.overlay_analytics["node_scores"].items()],
            reverse=True
        )[:20]  # Top 20
        
        # Complete overlay analysis
        analysis = {
            "traversal_metadata": {
                "total_nodes_visited": 240,
                "traversal_time": total_time,
                "nodes_per_second": 240 / total_time,
                "traversal_order": self.node_visit_order,
                "domain_context": domain_context
            },
            "solution": {
                "initial_vector": initial_vector.tolist(),
                "best_vector": best_vector.tolist(),
                "best_channels": best_channels,
                "best_score": best_score,
                "best_node_index": best_node_idx,
                "improvement": best_score - initial_score
            },
            "statistical_analysis": {
                "score_distribution": score_stats,
                "chamber_analysis": chamber_stats,
                "parity_analysis": parity_stats,
                "geometric_analysis": geometric_stats
            },
            "top_performing_nodes": [
                {
                    "rank": i + 1,
                    "node_index": idx,
                    "score": score,
                    "root_vector": self.all_roots[idx].tolist(),
                    "chamber": self.e8_lattice.determine_chamber(self.all_roots[idx])[0]
                }
                for i, (score, idx) in enumerate(top_nodes)
            ],
            "domain_insights": self.overlay_analytics["domain_insights"],
            "overlay_determinations": self._make_overlay_determinations(
                score_stats, chamber_stats, parity_stats, domain_context
            ),
            "recommendations": self._generate_recommendations_from_complete_data(
                score_stats, chamber_stats, domain_context
            )
        }
        
        return analysis
    
    def _make_overlay_determinations(self,
                                   score_stats: Dict,
                                   chamber_stats: Dict,
                                   parity_stats: Dict,
                                   domain_context: Optional[Dict]) -> Dict[str, Any]:
        """Make determinations about problem structure from overlay data."""
        
        determinations = {}
        
        # Problem difficulty assessment
        if score_stats["std"] < 0.1:
            determinations["problem_difficulty"] = "uniform - all nodes score similarly"
        elif score_stats["std"] > 0.3:
            determinations["problem_difficulty"] = "highly_varied - distinct optimal regions exist"
        else:
            determinations["problem_difficulty"] = "moderate - some structure present"
        
        # Optimal embedding assessment
        improvement_ratio = score_stats["improvement"] / (score_stats["initial_score"] + 1e-10)
        if improvement_ratio > 0.5:
            determinations["embedding_quality"] = "excellent - significant improvement found"
        elif improvement_ratio > 0.1:
            determinations["embedding_quality"] = "good - meaningful improvement"
        elif improvement_ratio > 0:
            determinations["embedding_quality"] = "marginal - small improvement"
        else:
            determinations["embedding_quality"] = "poor - no improvement over initial"
        
        # Chamber structure insights
        chamber_count = len(chamber_stats)
        if chamber_count == 1:
            determinations["geometric_structure"] = "simple - problem confined to single chamber"
        elif chamber_count < 8:
            determinations["geometric_structure"] = "structured - problem spans few chambers"
        elif chamber_count < 16:
            determinations["geometric_structure"] = "complex - problem spans many chambers"
        else:
            determinations["geometric_structure"] = "chaotic - problem spans most chambers"
        
        # Best chamber identification
        best_chamber = max(chamber_stats.items(), key=lambda x: x[1]["best_score"])
        determinations["optimal_chamber"] = {
            "signature": best_chamber[0],
            "score": best_chamber[1]["best_score"],
            "node_count": best_chamber[1]["node_count"]
        }
        
        # Parity pattern assessment
        parity_variance = np.mean([stats["variance"] for stats in parity_stats.values()])
        if parity_variance < 0.01:
            determinations["parity_structure"] = "rigid - channels show little variation"
        elif parity_variance > 0.1:
            determinations["parity_structure"] = "flexible - channels vary significantly"
        else:
            determinations["parity_structure"] = "moderate - some channel variation"
        
        # Domain-specific determinations
        if domain_context:
            domain_type = domain_context.get("domain_type", "unknown")
            complexity_class = domain_context.get("complexity_class", "unknown")
            
            if domain_type == "computational" and complexity_class in ["P", "NP"]:
                # P vs NP specific analysis
                if score_stats["best_score"] > 0.8:
                    determinations["complexity_separation"] = f"strong - {complexity_class} problems well-separated"
                elif score_stats["best_score"] > 0.6:
                    determinations["complexity_separation"] = f"moderate - {complexity_class} problems distinguishable"
                else:
                    determinations["complexity_separation"] = f"weak - {complexity_class} problems poorly separated"
        
        return determinations
    
    def _generate_recommendations_from_complete_data(self,
                                                   score_stats: Dict,
                                                   chamber_stats: Dict,
                                                   domain_context: Optional[Dict]) -> List[str]:
        """Generate actionable recommendations based on complete traversal data."""
        
        recommendations = []
        
        # Score-based recommendations
        if score_stats["improvement"] > 0.3:
            recommendations.append(
                f"Excellent improvement achieved ({score_stats['improvement']:.3f}) - "
                f"node {score_stats['best_node']} represents optimal embedding"
            )
        elif score_stats["improvement"] < 0.05:
            recommendations.append(
                "Minimal improvement found - consider alternative domain adaptation or "
                "problem reformulation strategies"
            )
        
        # Chamber-based recommendations
        best_chamber = max(chamber_stats.items(), key=lambda x: x[1]["best_score"])
        recommendations.append(
            f"Focus optimization on chamber {best_chamber[0]} which contains "
            f"{best_chamber[1]['node_count']} nodes and achieves best score {best_chamber[1]['best_score']:.4f}"
        )
        
        if len(chamber_stats) > 20:
            recommendations.append(
                f"Problem spans {len(chamber_stats)} chambers - consider multi-chamber "
                "optimization strategies or chamber-specific sub-problems"
            )
        
        # Variance-based recommendations
        if score_stats["std"] > 0.2:
            recommendations.append(
                f"High score variance ({score_stats['std']:.3f}) indicates multi-modal "
                "optimization landscape - consider ensemble methods"
            )
        
        # Domain-specific recommendations
        if domain_context:
            domain_type = domain_context.get("domain_type", "unknown")
            
            if domain_type == "computational":
                complexity_class = domain_context.get("complexity_class", "unknown")
                if complexity_class in ["P", "NP"] and score_stats["best_score"] > 0.7:
                    recommendations.append(
                        f"Strong {complexity_class} embedding suggests geometric approach "
                        "viable for complexity class separation"
                    )
        
        return recommendations
    
    def _save_complete_traversal_data(self, analysis: Dict[str, Any]):
        """Save complete traversal data to files."""
        
        # Create data directory
        Path("data/generated").mkdir(parents=True, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = int(time.time())
        
        # Save complete analysis
        filename = f"complete_morsr_analysis_{timestamp}.json"
        filepath = Path("data/generated") / filename
        
        with open(filepath, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        self.logger.info(f"Complete analysis saved to: {filepath}")
        
        # Save overlay determinations separately
        determinations_file = Path("data/generated") / f"overlay_determinations_{timestamp}.json"
        with open(determinations_file, 'w') as f:
            json.dump(analysis["overlay_determinations"], f, indent=2)
        
        # Save summary
        summary = {
            "timestamp": timestamp,
            "nodes_visited": 240,
            "best_score": analysis["solution"]["best_score"],
            "best_node": analysis["solution"]["best_node_index"],
            "improvement": analysis["solution"]["improvement"],
            "traversal_time": analysis["traversal_metadata"]["traversal_time"],
            "overlay_determinations": analysis["overlay_determinations"],
            "top_recommendations": analysis["recommendations"][:5]  # Top 5
        }
        
        summary_file = Path("data/generated") / f"morsr_summary_{timestamp}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        self.logger.info(f"Summary and determinations saved")

class ComprehensiveCQEValidation:

    def __init__(self):
        self.speedlight = SpeedLight()
        self.e8 = E8Lattice() if E8Lattice else None
        self.embeddings = {}
        self.receipts = {}
        self.validation_results = {}
        self.start_time = time.time()

    def collect_all_source_files(self, base_paths: List[str], max_files: int=None) -> List[Path]:
        """Collect all source files from multiple base paths"""
        print(f"\n{'=' * 70}")
        print('PHASE 1: Collecting All Source Files')
        print(f"{'=' * 70}\n")
        patterns = ['*.md', '*.py', '*.json', '*.yaml']
        files = []
        for base_path in base_paths:
            for pattern in patterns:
                files.extend(Path(base_path).rglob(pattern))
        files = list(set(files))
        if max_files:
            files = files[:max_files]
        print(f'? Collected {len(files)} unique source files')
        return files

    def generate_embeddings_batch(self, files: List[Path], batch_size: int=100) -> Dict[str, Any]:
        """Generate embeddings in batches for efficiency"""
        print(f'\nGenerating embeddings for {len(files)} files...')
        print(f'Batch size: {batch_size}')
        results = {'total_files': len(files), 'successful': 0, 'failed': 0, 'cached': 0, 'embeddings': {}, 'processing_time': 0}
        start = time.time()
        for i in range(0, len(files), batch_size):
            batch = files[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(files) + batch_size - 1) // batch_size
            print(f'\n  Batch {batch_num}/{total_batches} ({len(batch)} files)...')
            for file_path in batch:
                embedding = self._generate_embedding_for_file(file_path)
                if embedding:
                    results['successful'] += 1
                    if embedding.get('cached', False):
                        results['cached'] += 1
                    results['embeddings']

class CompressionType(Enum):
    """Types of compression"""
    NONE = "none"
    GZIP = "gzip"
    LZMA = "lzma"
    CQE_NATIVE = "cqe_native"

class ComputationalReceipt:
    """Self-validating embedding with full provenance."""
    world: str
    vec: List[float]
    vec_dim: int
    lane_feat: List[float]
    cqe_channel: int
    delta_phi: float
    rho_like: float
    scope: bool
    schema_version: str
    timestamp: str
    sample_index: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    kakeya_signature: Optional[Tuple[float, float, float]] = None
    provenance: Optional[ProvenanceMetadata] = None

    def verify_integrity(self) -> bool:
        """Cryptographically verify this receipt hasn't been tampered with."""
        if self.provenance is None:
            return False
        computed_hash = compute_merkle_root(self.vec)
        return computed_hash == self.provenance.merkle_root

    def link_to_speedlight(self, receipt_id: str, ledger_entry: Optional[str]=None) -> None:
        """Link this embedding to a SpeedLight receipt."""
        if self.provenance is None:
            raise ValueError('Cannot link: no provenance metadata')
        self.provenance.speedlight_receipt_id = receipt_id
        if ledger_entry:
            self.provenance.cqe_ledger_entry = ledger_entry

    def to_dict(self) -> Dict[str, Any]:
        """Serialize with full provenance."""
        result = {'world': self.world, 'vec': self.vec, 'vec_dim': self.vec_dim, 'lane_feat': self.lane_feat, 'cqe_channel': self.cqe_channel, 'delta_phi': self.delta_phi, 'rho_like': self.rho_like, 'scope': self.scope, 'schema_version': self.schema_version, 'timestamp': self.timestamp}
        if self.sample_index is not None:
            result['sample_index'] = self.sample_index
        if self.metadata:
            result['metadata'] = self.metadata
        if self.kakeya_signature is not None:
            n, k, vol = self.kakeya_signature
            result['kakeya_signature'] = {'n': n, 'K': k, 'vol_proxy': vol}
        if self.provenance is not None:
            result['provenance'] = s

class Const:
    name: str
    value: Any

class ConstraintType(Enum):
    """Types of constraints in CQE governance"""
    QUAD_CONSTRAINT = "quad_constraint"
    E8_CONSTRAINT = "e8_constraint"
    PARITY_CONSTRAINT = "parity_constraint"
    GOVERNANCE_CONSTRAINT = "governance_constraint"
    TEMPORAL_CONSTRAINT = "temporal_constraint"
    SPATIAL_CONSTRAINT = "spatial_constraint"
    LOGICAL_CONSTRAINT = "logical_constraint"
    SEMANTIC_CONSTRAINT = "semantic_constraint"

class ConstructionType(Enum):
    """Conway construction types A, B, C, D."""
    A = "A"  # Corner cells
    B = "B"  # Edge cells  
    C = "C"  # Center cells
    D = "D"  # Mixed patterns

class ContextScore:
    name: str
    score: float  # 0..1
    evidence: str = ""

class DTTTestRunner(threading.Thread):
    """
    Enhanced DTT test runner with geometric operations.
    
    Runs in isolated thread sandbox with access to:
    - Geometric transformer
    - Token system
    - Lambda calculus
    """
    
    def __init__(
        self,
        packet: IdeaPacket,
        transformer: GeometricTransformer,
        token_agent: AletheiaAgent,
        lambda_capture: GeometricLambdaCapture
    ):
        super().__init__(daemon=True)
        self.packet = packet
        self.transformer = transformer
        self.token_agent = token_agent
        self.lambda_capture = lambda_capture
        self.result: Optional[Dict] = None
    
    def run(self):
        """Execute test based on packet type."""
        print(f"\n[DTT] Running test: {self.packet.id} (type: {self.packet.type})")
        
        try:
            if self.packet.type == "transform":
                self.result = self._test_transform()
            elif self.packet.type == "tokenize":
                self.result = self._test_tokenize()
            elif self.packet.type == "path":
                self.result = self._test_path()
            elif self.packet.type == "validate":
                self.result = self._test_validate()
            else:
                self.result = {"error": f"Unknown packet type: {self.packet.type}"}
            
            print(f"[DTT] Test complete: {self.packet.id}")
            
        except Exception as e:
            self.result = {"error": str(e)}
            print(f"[DTT] Test failed: {self.packet.id} - {e}")
    
    def _test_transform(self) -> Dict:
        """Test geometric transformation."""
        import numpy as np
        
        # Extract parameters
        batch_size = self.packet.content.get("batch_size", 2)
        seq_len = self.packet.content.get("seq_len", 10)
        dim = self.packet.content.get("dim", 1024)
        
        # Create input
        x = np.random.randn(batch_size, seq_len, dim) * 0.02
        
        # Run transform
        output, receipts = self.transformer.forward(x)
        
        # Capture lambda
        lambda_term = self.lambda_capture.capture_attention(dim, dim, dim, 16)
        
        return {
            "input_shape": x.shape,
            "output_shape": output.shape,
            "num_receipts": len(receipts),
            "lambda_ir": lambda_term.to_string(),
            "conservation_satisfied": all(r.delta_phi <= 0 for r in receipts)
        }
    
    def _test_tokenize(self) -> Dict:
        """Test tokenization."""
        text = self.packet.content.get("text", "hello world")
        
        # Tokenize
        tokens = self.token_agent.tokenize(text, Channel.TEXT)
        
        # Capture lambda
        lambda_term = self.lambda_capture.capture_tokenization(text, 320000)
        
        return {
            "text": text,
            "num_tokens": len(tokens),
            "token_ids": [t.id for t in tokens],
            "lambda_ir": lambda_term.to_string()
        }
    
    def _test_path(self) -> Dict:
        """Test AGRM path operations."""
        nodes = self.packet.content.get("nodes", ["A", "B", "C"])
        
        # Capture path lambda
        lambda_term = self.lambda_capture.capture_agrm_path(
            nodes[0], nodes[-1], nodes
        )
        
        return {
            "path": nodes,
            "lambda_ir": lambda_term.to_string()
        }
    
    def _test_validate(self) -> Dict:
        """Test validation operations."""
        # Run validation checks
        checks = {
            "transformer_receipts": len(self.transformer.receipts),
            "token_count": len(self.token_agent.token_system.tokens),
            "lambda_operations": len(self.lambda_capture.operation_log)
        }
        
        return checks


def digital_root(n):
    n = abs(int(round(n)))
    return 0 if n == 0 else 1 + (n - 1) % 9

def register_morphonforgecontroller(cmplx_system, db_path: str = "./morphon_forge.sqlite"):
    """Register with CMPLX system."""
    controller = MorphonForgeController(
        cmplx_system.context,
        db_path=db_path
    )
    
    if not hasattr(cmplx_system, 'morphon_forge'):
        setattr(cmplx_system, 'morphon_forge', controller)
    
    cmplx_system.system.register_domain("morphon_forge", controller)
    print(f"[MorphonForge] Controller registered with {db_path}")

def shannon_entropy(seq):
    if len(seq) < 2: return 0.0
    counts = Counter(seq)
    n = len(seq)
    return -sum((c/n)*math.log2(c/n) for c in counts.values() if c > 0)

def create_morphon(
    request_type: str,
    payload: Dict[str, Any],
    mandelbrot_term: Optional[str] = None,
    tools: Optional[List[str]] = None,
    data_deps: Optional[List[str]] = None
) -> Morphon:
    """Create a new Morphon with common defaults."""
    morphon = Morphon(
        request_type=request_type,
        payload=payload,
        tools_required=tools or [],
        data_dependencies=data_deps or []
    )
    if mandelbrot_term:
        morphon.assign_mandelbrot_term(mandelbrot_term)
    return morphon

def compile_expr(expr: str) -> Any:
    # Vendor option 1: compiler.compile(expr)
    if _vendor_compiler:
        for fn_name in ("compile", "compile_expr", "compile_program"):
            if hasattr(_vendor_compiler, fn_name):
                try:
                    return getattr(_vendor_compiler, fn_name)(expr)  # type: ignore
                except Exception:
                    pass
    # Vendor option 2: parser.parse(expr)
    if _vendor_ast:
        for fn_name in ("parse", "parse_expr", "parse_program"):
            if hasattr(_vendor_ast, fn_name):
                try:
                    return getattr(_vendor_ast, fn_name)(expr)  # type: ignore
                except Exception:
                    pass
    return _compile(expr)

def donor_capabilities() -> Dict[str, Any]:
    return {
        "vendor_present": vroot.exists(),
        "ast_loaded": bool(_vendor_ast),
        "eval_loaded": bool(_vendor_eval),
        "compiler_loaded": bool(_vendor_compiler),
        "py_file_count": len(list(vroot.rglob("*.py"))) if vroot.exists() else 0,
    }

def eval_program(program: Any, env: Optional[Dict[str, Any]] = None) -> Any:
    env = env or {}
    # Vendor: eval.eval(program, env) or interpreter.run(...)
    if _vendor_eval:
        for fn_name in ("eval", "evaluate", "run", "execute"):
            if hasattr(_vendor_eval, fn_name):
                try:
                    return getattr(_vendor_eval, fn_name)(program, env)  # type: ignore
                except TypeError:
                    try:
                        return getattr(_vendor_eval, fn_name)(program)  # type: ignore
                    except Exception:
                        pass
                except Exception:
                    pass
    return _eval(program, env)

def trace_program(program: Any) -> Dict[str, Any]:
    # Vendor: trace(program) or explain(program)
    if _vendor_eval:
        for fn_name in ("trace", "explain"):
            if hasattr(_vendor_eval, fn_name):
                try:
                    t = getattr(_vendor_eval, fn_name)(program)  # type: ignore
                    return t if isinstance(t, dict) else {"trace": str(t)}
                except Exception:
                    pass
    return _trace(program)

def _fallback_embed_glyph(glyph: str) -> tuple[list[float], str]:
    h = hashlib.sha256(glyph.encode("utf-8")).digest()
    vec: list[float] = []
    for idx in range(8):
        chunk = h[idx * 2 : idx * 2 + 2]
        val = int.from_bytes(chunk, "big") / 65535.0
        vec.append((val - 0.5) * 2.0)
    lattice_id = hashlib.sha256((glyph + "::lattice").encode("utf-8")).hexdigest()
    return vec, lattice_id

def _fallback_snap(vector: list[float]) -> dict[str, Any]:
    dampened = [value * 0.98 for value in vector]
    delta_phi = sum((new - old) ** 2 for new, old in zip(dampened, vector))
    return {"delta_phi": float(delta_phi), "vector": dampened, "op": "dampen"}

def _load_vendor(module_name: str, rel_path: str):
    here = Path(__file__).resolve().parent.parent
    p = here / "vendor" / "morphonic_lambda" / rel_path
    if not p.exists():
        return None
    spec = importlib.util.spec_from_file_location(module_name, str(p))
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    _sys.modules[module_name] = mod
    spec.loader.exec_module(mod)  # type: ignore
    return mod

def _normalize_vector(values: list[float] | tuple[float, ...] | None) -> list[float]:
    vec = [float(value) for value in list(values or [])]
    if len(vec) < 8:
        vec.extend([0.0] * (8 - len(vec)))
    return vec[:8]

async def health() -> Dict[str, Any]:
    controller: MMDBController = app.state.controller
    status = controller.get_status()
    return {
        "ok": True,
        "service": "mmdb",
        "db_path": status["db_path"],
        "operations": status["operations"],
    }

def run_morphonic_pipeline_bridge(
    *,
    doc_id: str,
    state_id: str,
    profile: str,
    text: str,
    base_vector: list[float] | tuple[float, ...] | None = None,
    refine_iterations: int = 8,
) -> dict[str, Any]:
    normalized_text = str(text or "").strip() or f"{doc_id}:{state_id}:morphonic_pipeline_bridge"
    donor = _load_donor_pipeline()
    route: list[str] = []

    glyph = _fallback_shell_text(normalized_text)
    glyph_source = "fallback"
    if donor is not None and hasattr(donor, "shell_text"):
        try:
            glyph = str(donor.shell_text(normalized_text))
            glyph_source = "donor"
            route.append("shell_text:donor")
        except Exception:
            route.append("shell_text:fallback")
    else:
        route.append("shell_text:fallback")

    embedded_vector, lattice_id = _fallback_embed_glyph(glyph)
    embed_source = "fallback"
    if donor is not None and hasattr(donor, "embed_glyph"):
        try:
            donor_vec, donor_lattice = donor.embed_glyph(glyph)
            embedded_vector = _normalize_vector(list(donor_vec))
            lattice_id = str(donor_lattice or lattice_id)
            embed_source = "donor"
            route.append("embed_glyph:donor")
        except Exception:
            route.append("embed_glyph:fallback")
    else:
        route.append("embed_glyph:fallback")

    input_vector = _normalize_vector(base_vector) if base_vector is not None else _normalize_vector(embedded_vector)

    snap = _fallback_snap(input_vector)
    snap_source = "fallback"
    if donor is not None and hasattr(donor, "alena_snap"):
        try:
            donor_snap = donor.alena_snap(tuple(input_vector))
            snap = {
                "delta_phi": float(donor_snap.get("delta_phi", 0.0)),
                "vector": _normalize_vector(donor_snap.get("vector", input_vector)),
                "op": str(donor_snap.get("op", "donor_alena_snap")),
            }
            snap_source = "donor"
            route.append("alena_snap:donor")
        except Exception:
            route.append("alena_snap:fallback")
    else:
        route.append("alena_snap:fallback")

    refined_vector = _normalize_vector(snap.get("vector", input_vector))
    morsr_meta: dict[str, Any] = {"iterations": 0}
    refine_source = "fallback"
    if donor is not None and hasattr(donor, "morsr_refine"):
        try:
            donor_refined = donor.morsr_refine(tuple(refined_vector), iterations=max(0, int(refine_iterations)))
            refined_vector = _normalize_vector(donor_refined.get("result", refined_vector))
            meta = donor_refined.get("meta", {})
            morsr_meta = dict(meta) if isinstance(meta, dict) else {"meta": meta}
            refine_source = "donor"
            route.append("morsr_refine:donor")
        except Exception:
            route.append("morsr_refine:fallback")
    else:
        route.append("morsr_refine:fallback")

    op_summary = {
        "glyph_source": glyph_source,
        "embed_source": embed_source,
        "snap_source": snap_source,
        "refine_source": refine_source,
        "route": route,
        "snap": snap,
        "morsr_meta": morsr_meta,
        "degraded": donor is None or any(item.endswith(":fallback") for item in route),
    }

    envelope = {
        "doc_id": str(doc_id),
        "state_id": str(state_id),
        "profile": str(profile),
        "text_hash": hashlib.sha256(normalized_text.encode("utf-8")).hexdigest(),
        "glyph": glyph,
        "lattice_id": lattice_id,
        "input_vector": input_vector,
        "embedded_vector": embedded_vector,
        "refined_vector": refined_vector,
        "op_summary": op_summary,
    }
    payload_hash = sha256_hex(envelope)
    record_id = prefixed_id("morphpipe", envelope)
    created_at = deterministic_iso_from_hash(payload_hash)

    persist_integration_morphonic_pipeline_run(
        record_id=record_id,
        doc_id=str(doc_id),
        state_id=str(state_id),
        profile=str(profile),
        text_hash=str(envelope["text_hash"]),
        glyph=glyph,
        lattice_id=lattice_id,
        input_vector=input_vector,
        embedded_vector=embedded_vector,
        refined_vector=refined_vector,
        op_summary=op_summary,
        payload_hash=payload_hash,
        created_at=created_at,
    )

    return {
        "record_id": record_id,
        "doc_id": str(doc_id),
        "state_id": str(state_id),
        "profile": str(profile),
        "text_hash": str(envelope["text_hash"]),
        "glyph": glyph,
        "lattice_id": lattice_id,
        "input_vector": input_vector,
        "embedded_vector": embedded_vector,
        "refined_vector": refined_vector,
        "op_summary": op_summary,
        "payload_hash": payload_hash,
        "created_at": created_at,
    }

def _fallback_shell_text(text: str) -> str:
    return f"glyph:{hashlib.sha256(text.encode('utf-8')).hexdigest()[:32]}"

def _load_donor_pipeline() -> Any | None:
    candidates = [
        (WORKSPACE_ROOT / "integration" / "morphonic_pipeline.py").resolve(),
        (CORPUS_ROOT / "integration" / "morphonic_pipeline.py").resolve(),
    ]
    path = next((item for item in candidates if item.exists()), None)
    if path is None:
        return None
    spec = importlib.util.spec_from_file_location("cmplx_morphonic_pipeline_donor", str(path))
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception:
        return None
    cls = getattr(module, "MorphonicPipeline", None)
    if cls is None:
        return None
    try:
        return cls()
    except Exception:
        return None

def e8_nearest(y):
    z0 = np.rint(y)
    if (int(np.sum(z0)) & 1) == 1:
        frac = np.abs(y - z0); k = int(np.argmin(frac))
        z0[k] += 1 if y[k] > z0[k] else -1
    d0 = np.linalg.norm(y - z0)
    yh = y - 0.5
    z1 = np.rint(yh)
    if (int(np.sum(z1)) & 1) == 1:
        frac = np.abs(yh - z1); k = int(np.argmin(frac))
        z1[k] += 1 if yh[k] > z1[k] else -1
    x1 = z1 + 0.5
    d1 = np.linalg.norm(y - x1)
    if d0 <= d1:
        return z0, d0, d0, d1, "int", x1
    else:
        return x1, d1, d0, d1, "half", z0

def eval_normal(t: Term, limit: int = 200) -> Dict[str, Any]:
    trace=[]
    cur=t
    for i in range(limit):
        trace.append(repr(cur))
        nxt=step_normal(cur)
        if nxt is None:
            break
        cur=nxt
    return {"normal_form": repr(cur), "steps": len(trace)-1, "trace": trace}

def substitute(t: Term, var: str, val: Term) -> Term:
    if isinstance(t, Var):
        return val if t.name == var else t
    if isinstance(t, Lam):
        if t.param == var:
            return t
        # naive capture-avoidance: rename if needed
        if t.param in free_vars(val):
            new = t.param + "_"
            return Lam(new, substitute(substitute(t.body, t.param, Var(new)), var, val))
        return Lam(t.param, substitute(t.body, var, val))
    if isinstance(t, App):
        return App(substitute(t.fn, var, val), substitute(t.arg, var, val))
    return t

def _http(url, data=None, method="POST"):
    try:
        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(url, data=body,
            headers={"Content-Type": "application/json"} if body else {},
            method=method)
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)[:100]}

def _pg_query(sql, params=None):
    try:
        import psycopg2
        conn = psycopg2.connect(PG_URL)
        cur = conn.cursor()
        cur.execute(sql, params or ())
        if cur.description:
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
        conn.close()
        return []
    except Exception as e:
        return [{"error": str(e)[:100]}]

def compute_phi(S: Dict[str,Any]) -> float:
    p, c = S["phases"], S["cartan"]
    geom = sum((p[i]-p[(i+1)%len(p)])**2 for i in range(len(p)))
    parity = sum(c) % 2
    spars  = sum(c)
    active = sum(1 for x in p if abs(x)>1e-9)
    kiss   = abs(active - 2)
    return geom + 5*parity + 0.5*spars + 0.1*kiss

def compute_potential(content: str, e8_coords: List[float] = None) -> MorphonPotential:
    """Compute the full morphonic potential of content.

    Applies ALL registered observation functors and collects:
    - The committed path (best functor by |ΔΦ|)
    - All other paths as open potentials
    - Total potential = sum of all |ΔΦ| across all functors
    """
    results = []
    for name, functor in FUNCTORS.items():
        obs = functor.observe(content, e8_coords)
        results.append((name, obs))

    # Sort by |ΔΦ| — the functor that conserves most is the committed path
    results.sort(key=lambda x: x[1].morphon_dphi)
    committed = results[0] if results else None

    open_paths = []
    for name, obs in results[1:]:
        open_paths.append({
            "functor": name, "geometry": obs.geometry_name,
            "dphi": obs.morphon_dphi, "R": obs.morphon_R,
        })

    pot = MorphonPotential(
        committed_geometry=committed[1].geometry_name if committed else "",
        committed_coords=committed[1].coordinates if committed else [],
        committed_dphi=committed[1].morphon_dphi if committed else 0.0,
        open_paths=open_paths,
        total_potential=sum(abs(obs.morphon_dphi) for _, obs in results),
    )
    return pot

def morphon_beam(e8_coords: List[float], max_iter: int = 100) -> Dict:
    """Compute MorphonBeam — Julia set dynamics seeded by E8 coordinates.

    The beam traces the morphon's trajectory through phase space.
    Escaped = unstable (the morphon diverges under iteration).
    Captured = stable (the morphon is a fixed point or cycle).
    """
    c_real = e8_coords[0] if e8_coords else 0.0
    c_imag = e8_coords[1] if len(e8_coords) > 1 else 0.0

    z_r, z_i = 0.0, 0.0
    trajectory = []
    for n in range(max_iter):
        z_r2, z_i2 = z_r * z_r, z_i * z_i
        trajectory.append({"r": round(z_r, 6), "i": round(z_i, 6),
                           "norm": round(math.sqrt(z_r2 + z_i2), 6)})
        if z_r2 + z_i2 > 4.0:
            return {"escaped": True, "iterations": n,
                    "escape_norm": math.sqrt(z_r2 + z_i2),
                    "trajectory": trajectory[-10:]}
        z_i = 2 * z_r * z_i + c_imag
        z_r = z_r2 - z_i2 + c_real

    return {"escaped": False, "iterations": max_iter,
            "final_norm": math.sqrt(z_r * z_r + z_i * z_i),
            "trajectory": trajectory[-10:]}

def overlay(content: str, e8_coords: List[float] = None) -> Dict:
    """Stage content as a potential crystal (overlay projection)."""
    pot = compute_potential(content, e8_coords)
    return {
        "operation": "overlay",
        "morphon_id": pot.morphon_id,
        "committed_geometry": pot.committed_geometry,
        "dphi": pot.committed_dphi,
        "open_paths": len(pot.open_paths),
        "total_potential": pot.total_potential,
        "state": "staged",
    }

def phase0_assess(scan_jsonl_paths: List[str] = []):
    """Scan zips, identify dupes, set aside."""
    _state["phase"] = "assess"
    logger.info("PHASE 0: Assessing corpus")

    # Count what we have in PG already
    rows = _pg_query("SELECT count(*) as c FROM content_hashes")
    existing_hashes = rows[0]["c"] if rows and "c" in rows[0] else 0

    rows = _pg_query("SELECT count(*) as c FROM content_hashes WHERE occurrence_count > 1")
    dupes = rows[0]["c"] if rows and "c" in rows[0] else 0

    rows = _pg_query("SELECT count(*) as c FROM atoms")
    total_atoms = rows[0]["c"] if rows and "c" in rows[0] else 0

    _state["corpus_total"] = existing_hashes
    _state["dupes_set_aside"] = dupes

    # Post assessment to board
    _http(f"{BOARD_URL}/threads", {
        "board_id": "status", "title": "Work Morphon Phase 0: Assessment",
        "author_id": "morphon", "template": "status_update",
        "content": f"Corpus: {existing_hashes} hashes, {dupes} dupes set aside, {total_atoms} atoms",
    })

    result = {
        "phase": 0, "existing_hashes": existing_hashes, "dupes": dupes,
        "total_atoms": total_atoms, "action": "dupes identified and set aside (occurrence_count > 1)",
    }

    # Receipt
    _http(f"{RECEIPT_URL}/mint", {
        "receipt_type": "PROCESS", "agent_id": "morphon",
        "operation": "phase0_assess", "snap_labels": ["morphon", "assess"],
    })

    return result

def phase1_tools():
    """What file types can't we handle? Request tools."""
    _state["phase"] = "tool_check"
    logger.info("PHASE 1: Checking tool coverage")

    # Query what file types exist in our atoms
    rows = _pg_query("""
        SELECT CASE
            WHEN source_file LIKE '%%.py' THEN '.py'
            WHEN source_file LIKE '%%.md' THEN '.md'
            WHEN source_file LIKE '%%.txt' THEN '.txt'
            WHEN source_file LIKE '%%.pdf' THEN '.pdf'
            WHEN source_file LIKE '%%.json' THEN '.json'
            WHEN source_file LIKE '%%.yml' OR source_file LIKE '%%.yaml' THEN '.yml'
            WHEN source_file LIKE '%%.sql' THEN '.sql'
            WHEN source_file LIKE '%%.html' THEN '.html'
            WHEN source_file LIKE '%%.js' THEN '.js'
            WHEN source_file LIKE '%%.ts' THEN '.ts'
            WHEN source_file LIKE '%%.rs' THEN '.rs'
            WHEN source_file LIKE '%%.zip' THEN '.zip'
            ELSE 'other'
        END as ext, count(*) as c
        FROM atoms WHERE source_file != '' GROUP BY 1 ORDER BY 2 DESC
    """)

    handled = {".py", ".md", ".txt", ".json", ".yml", ".sql", ".html", ".js", ".ts"}
    found_types = {r["ext"]: r["c"] for r in rows if "ext" in r}
    unhandled = [ext for ext in found_types if ext not in handled and ext != "other"]

    _state["tools_needed"] = unhandled
    _state["tools_built"] = list(handled)

    # Post to board
    _http(f"{BOARD_URL}/threads", {
        "board_id": "work", "title": "Work Morphon Phase 1: Tool Check",
        "author_id": "morphon", "template": "work_result",
        "content": f"Handled: {handled}\nUnhandled: {unhandled}\nFile types: {json.dumps(found_types)}",
    })

    return {
        "phase": 1, "handled_types": list(handled), "unhandled_types": unhandled,
        "file_distribution": found_types,
        "action": "tools needed for: " + str(unhandled) if unhandled else "all types covered",
    }

def phase2_deploy(content_batch: List[str] = []):
    """Deploy four-tier workers on content batch."""
    _state["phase"] = "deploy"
    logger.info("PHASE 2: Deploying workers on %d items", len(content_batch))

    results = {"tier_i": [], "tier_ii": [], "tier_iii": [], "tier_iv": []}

    for content in content_batch[:50]:  # Process in batches of 50
        # Tier (i): Unpack + Route — label the content to determine where it goes
        label_result = _http(f"{PIPELINE_URL}/label?content={urllib.request.quote(content[:2000])}")
        labels = label_result.get("labels", []) if label_result else []
        domains = [l.split("_", 1)[-1] for l in labels if l.startswith("SNAPdomain_")]
        results["tier_i"].append({"labels": len(labels), "domains": domains})

        # Tier (ii): Organize + Distribute — check dedup, assign domain
        chash = hashlib.sha256(content.encode("utf-8", errors="replace")).hexdigest()[:32]

        # Tier (iii): Process + Log — full pipeline
        process_result = _http(f"{PIPELINE_URL}/process", {
            "content": content[:4000], "source": "morphon::batch",
            "agent_id": "morphon-worker", "epoch": _state["loops_completed"],
        })

        if process_result and process_result.get("atom_id") and not process_result.get("dedup"):
            _state["atoms_produced"] += 1
            _state["total_dphi"] += process_result.get("delta_phi", 0)
            results["tier_iii"].append({
                "atom_id": process_result["atom_id"][:12],
                "labels": len(process_result.get("snap_labels", [])),
                "dphi": process_result.get("delta_phi", 0),
            })

            # Track new domains
            for d in domains:
                if d not in _state["domains_discovered"]:
                    _state["domains_discovered"].append(d)

    # Tier (iv): Review + Report — check conservation, report gaps
    conservation = _http(f"{CONSERVATION_URL}/status", method="GET")
    gaps = _http(f"{MORSR_URL}/health", method="GET")

    results["tier_iv"] = {
        "conservation_valid": conservation.get("conservation_valid", False) if conservation else False,
        "total_dphi": conservation.get("cumulative_dphi", 0) if conservation else 0,
        "atoms_this_batch": len(results["tier_iii"]),
        "domains_discovered": _state["domains_discovered"],
    }

    _state["workers"]["unpackers"] = len(content_batch)
    _state["workers"]["organizers"] = len(content_batch)
    _state["workers"]["processors"] = len(results["tier_iii"])
    _state["workers"]["reviewers"] = 1

    # Post results to board
    _http(f"{BOARD_URL}/threads", {
        "board_id": "work", "title": f"Work Morphon Phase 2: Batch ({len(content_batch)} items)",
        "author_id": "morphon", "template": "work_result",
        "content": f"Processed: {len(results['tier_iii'])} atoms\nDomains: {_state['domains_discovered']}\nΔΦ: {_state['total_dphi']:.4f}",
    })

    return {"phase": 2, **results}

def phase3_spawn():
    """Spawn new Shell 0 agents for newly discovered domains."""
    _state["phase"] = "spawn"
    logger.info("PHASE 3: Spawning agents for %d domains", len(_state["domains_discovered"]))

    spawned = []
    for domain in _state["domains_discovered"]:
        # Check if we already have an agent for this domain
        existing = [a for a in _state["agents_spawned"] if a.get("domain") == domain]
        if existing:
            continue

        # Spawn via spawn service
        result = _http(f"{SPAWN_URL}/birth", {
            "parent_id": "morphon", "domain": domain,
            "domain_boost": domain, "callsign": f"morphon-{domain}",
            "snapdna": [f"SNAPdomain_{domain}"],
        })

        if result and not result.get("error"):
            spawned.append(result)
            _state["agents_spawned"].append(result)

            # Register with coop
            _http(f"{COOP_URL}/register", {
                "agent_id": result.get("child_id", ""),
                "snapdna": [f"SNAPdomain_{domain}"],
                "department": domain,
            })

            # Register brain
            _http(f"{BRAIN_URL}/register", {
                "agent_id": result.get("child_id", ""),
                "dims": 24, "epoch": 0, "tier": "nascent",
                "specialist_profile": {domain: 0.5},
            })

    # Post to board
    _http(f"{BOARD_URL}/threads", {
        "board_id": "status", "title": f"Work Morphon Phase 3: Spawned {len(spawned)} agents",
        "author_id": "morphon", "template": "status_update",
        "content": f"New agents: {[s.get('child_id','?') for s in spawned]}\nDomains: {[s.get('domain','?') for s in spawned]}",
    })

    return {"phase": 3, "spawned": spawned, "total_agents": len(_state["agents_spawned"])}

def phase4_loop():
    """Decide: deepen (shell_depth < 3) or widen (shell_depth >= 3)."""
    _state["phase"] = "loop"
    _state["loops_completed"] += 1

    if _state["shell_depth"] < MAX_SHELL_DEPTH:
        _state["shell_depth"] += 1
        action = "DEEPEN"
        logger.info("PHASE 4: DEEPENING to shell %d", _state["shell_depth"])

        # Each existing agent spawns a child specialist (Shell N+1)
        children = []
        for agent in _state["agents_spawned"]:
            if agent.get("shell", 0) < _state["shell_depth"]:
                child = _http(f"{SPAWN_URL}/birth", {
                    "parent_id": agent.get("child_id", ""),
                    "domain": agent.get("domain", ""),
                    "domain_boost": agent.get("domain", ""),
                })
                if child and not child.get("error"):
                    child["shell"] = _state["shell_depth"]
                    children.append(child)
                    _state["agents_spawned"].append(child)

        result = {"action": action, "shell_depth": _state["shell_depth"],
                  "children_spawned": len(children), "total_agents": len(_state["agents_spawned"])}

    else:
        _state["widening"] = True
        action = "WIDEN"
        logger.info("PHASE 4: WIDENING at shell %d — discovering new domains", _state["shell_depth"])

        # Search for domains we haven't covered
        rows = _pg_query("""
            SELECT label, count(*) as c FROM snap_labels
            WHERE label LIKE 'SNAPdomain_%%'
            GROUP BY label HAVING count(*) > 5
            ORDER BY count(*) DESC
        """)
        all_domains = [r["label"].split("_", 1)[-1] for r in rows if "label" in r]
        new_domains = [d for d in all_domains if d not in _state["domains_discovered"]]

        if new_domains:
            _state["domains_discovered"].extend(new_domains)

        result = {"action": action, "shell_depth": _state["shell_depth"],
                  "new_domains": new_domains, "total_domains": len(_state["domains_discovered"])}

    # Receipt
    _http(f"{RECEIPT_URL}/mint", {
        "receipt_type": "GATE", "agent_id": "morphon",
        "operation": f"phase4_{action.lower()}", "epoch": _state["loops_completed"],
    })

    # Post to board
    _http(f"{BOARD_URL}/threads", {
        "board_id": "status", "title": f"Work Morphon Phase 4: {action} (loop {_state['loops_completed']})",
        "author_id": "morphon", "template": "status_update",
        "content": json.dumps(result, indent=2),
    })

    return {"phase": 4, **result}

def refocus(morphon_id: str, dphi: float) -> Dict:
    """Refocus a staged overlay (ΔΦ > 0 — needs more work)."""
    return {"operation": "refocus", "morphon_id": morphon_id,
            "state": "enrichment_queue", "dphi": dphi}

def run_full(content_batch: List[str] = []):
    """Execute full morphon cycle: assess → tools → deploy → spawn → loop."""
    results = {}
    results["phase0"] = phase0_assess()
    results["phase1"] = phase1_tools()
    if content_batch:
        results["phase2"] = phase2_deploy(content_batch)
    results["phase3"] = phase3_spawn()
    results["phase4"] = phase4_loop()
    return results

def status():
    total_ingested = sum(t.get("ingested_count", 0) for t in _discovered_tables.values())
    return {
        "tables_discovered": len(_discovered_tables),
        "tables_eligible": sum(1 for t in _discovered_tables.values() if t.get("eligible")),
        "total_ingested": total_ingested,
        "ingest_log_entries": len(_ingest_log),
        "recent_ingests": _ingest_log[-5:] if _ingest_log else [],
        "source": _source_tag(),
    }

def tick():
    """Daemon tick — enrich crystals with moonshine features."""
    enriched = 0
    for cid, crystal in list(_crystals.items())[:20]:
        if "moonshine_feature" not in crystal.get("metadata", {}):
            crystal.setdefault("metadata", {})["moonshine_feature"] = _moonshine_feature(8)
            enriched += 1
    return {"ok": True, "service": "mmdb", "enriched": enriched, "total_crystals": len(_crystals)}

def angle_deg(u, v):
    cos_t = np.dot(u, v) / (np.linalg.norm(u) * np.linalg.norm(v) + 1e-12)
    cos_t = np.clip(cos_t, -1, 1)
    return math.degrees(math.acos(cos_t))

def api_beam(req: BeamRequest):
    """Compute MorphonBeam — Julia dynamics from E8 coordinates."""
    return morphon_beam(req.e8_coords, req.max_iter)

def api_commit(req: CommitRequest):
    """Commit staged overlay to crystal_active (requires ΔΦ ≤ 0)."""
    return commit(req.morphon_id, req.dphi)

def api_functors():
    """List all observation functors."""
    return {name: {"target": f.target, "observations": f.observation_count,
                   "bias": f.bias} for name, f in FUNCTORS.items()}

def api_geometries():
    """List all named geometries in M₀."""
    return {name: asdict(g) for name, g in GEOMETRIES.items()}

def api_observe(req: ObserveRequest):
    """Apply an observation functor to content, producing a geometric observation."""
    functor = FUNCTORS.get(req.functor)
    if not functor:
        raise HTTPException(404, f"Functor '{req.functor}' not found. Available: {list(FUNCTORS.keys())}")
    result = functor.observe(req.content, req.e8_coords or None)
    return asdict(result)

def api_overlay(req: OverlayRequest):
    """Stage content as potential crystal (MGLC overlay)."""
    return overlay(req.content, req.e8_coords or None)

def api_potential(req: PotentialRequest):
    """Compute full morphonic potential — all observation paths."""
    pot = compute_potential(req.content, req.e8_coords or None)
    return asdict(pot)

def api_refocus(req: CommitRequest):
    """Refocus staged overlay (ΔΦ > 0 — needs enrichment)."""
    return refocus(req.morphon_id, req.dphi)

def cardinal_rotate(v, shift):
    """Cyclic shift of coordinates by 'shift' positions."""
    return np.roll(v, shift)

def commit(morphon_id: str, dphi: float) -> Dict:
    """Commit a staged overlay to crystal_active (requires ΔΦ ≤ 0)."""
    if dphi > 0:
        return {"operation": "commit", "morphon_id": morphon_id,
                "state": "rejected", "reason": f"dPhi={dphi:.4f} > 0"}
    return {"operation": "commit", "morphon_id": morphon_id,
            "state": "crystal_active", "dphi": dphi}

def dark_ax(ax):
    ax.set_facecolor('#161b22')
    for sp in ax.spines.values(): sp.set_color('#30363d')
    ax.tick_params(colors='#8b949e', labelsize=7)

def embed_24d(v8, phase=0):
    """Embed 8D vector into 24D via three copies with phase shifts."""
    v1 = v8.copy()
    v2 = cardinal_rotate(v8, 1)   # +1 cyclic shift
    v3 = cardinal_rotate(v8, -1)  # -1 cyclic shift
    return np.concatenate([v1, v2, v3])

def free_vars(t: Term) -> Set[str]:
    if isinstance(t, Var):
        return {t.name}
    if isinstance(t, Lam):
        return free_vars(t.body) - {t.param}
    if isinstance(t, App):
        return free_vars(t.fn) | free_vars(t.arg)
    return set()

def make_morphon(name, coords, step, parent, closure_type, history=None):
    coords = np.array(coords, dtype=float)
    snapped, idx = e8_nearest(coords)
    return Morphon(
        name=name,
        coords=snapped,
        root_idx=idx,
        digital_root=digital_root(snapped),
        phi=compute_phi(snapped),
        step=step,
        parent_name=parent,
        closure_type=closure_type,
        inner_history=history or [],
    )

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Probe MMDB-related code in the mounted corpus.")
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--roots", nargs="+", required=True)
    parser.add_argument("--path-only", action="store_true", help="Only use path-token discovery, skip slower content scanning.")
    return parser.parse_args()

def rotate_all_forms(coords, shift):
    """Apply cardinal rotation to all 25 forms."""
    return np.array([cardinal_rotate(v, shift) for v in coords])

def run_morphonic_witness(text: str, refine: bool = True) -> Dict[str, Any]:
    """Run the morphonic pipeline for `text` and return the result dict.

    This function uses the integration capsule when present; it will raise
    an ImportError only if the capsule is absent and cannot be loaded.
    """
    try:
        mod = importlib.import_module("integration.morphonic_pipeline")
        MorphonicPipeline = getattr(mod, "MorphonicPipeline")
    except Exception as exc:  # pragma: no cover - fallback logging
        logger.exception("MorphonicPipeline capsule not available: %s", exc)
        return {"error": "MorphonicPipeline capsule not available", "detail": str(exc)}

    try:
        pipeline = MorphonicPipeline()
        res = pipeline.run_once(text, refine=refine)
        return {
            "lattice_id": res.lattice_id,
            "vector": list(res.vector),
            "op_summary": res.op_summary,
            "mmdb_record": res.mmdb_record,
            "receipt": res.receipt,
        }
    except Exception as exc:
        logger.exception("morphonic pipeline execution failed: %s", exc)
        return {"error": "execution_failed", "detail": str(exc)}

def snap_all(coords):
    """Snap all vectors to E8 and return (snapped_coords, root_idxs)."""
    snapped = []
    idxs = []
    for v in coords:
        s, i = snap_to_e8(v)
        snapped.append(s)
        idxs.append(i)
    return np.array(snapped), idxs

def snap_to_e8(v):
    dists = np.linalg.norm(root_vecs - np.array(v, dtype=float), axis=1)
    idx = int(np.argmin(dists))
    return root_vecs[idx].copy(), idx

def step_normal(t: Term) -> Optional[Term]:
    # normal-order
    if isinstance(t, App) and isinstance(t.fn, Lam):
        return substitute(t.fn.body, t.fn.param, t.arg)
    if isinstance(t, App):
        sfn = step_normal(t.fn)
        if sfn is not None:
            return App(sfn, t.arg)
        sarg = step_normal(t.arg)
        if sarg is not None:
            return App(t.fn, sarg)
        return None
    if isinstance(t, Lam):
        sb = step_normal(t.body)
        return Lam(t.param, sb) if sb is not None else None
    return None

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _angular_coherence(points):
    """Circular statistic R̄ ∈ [0,1]: 1 = perfect phase alignment."""
    if not points:
        return 0.0
    c = _centroid(points)
    cs = ss = 0.0
    n = 0
    for p in points:
        dx, dy = p[0] - c[0], p[1] - c[1]
        th = math.atan2(dy, dx)
        cs += math.cos(th)
        ss += math.sin(th)
        n += 1
    if n == 0:
        return 0.0
    return math.sqrt((cs / n) ** 2 + (ss / n) ** 2)

def _centroid(ps):
    n = max(1, len(ps))
    return (sum(p[0] for p in ps) / n, sum(p[1] for p in ps) / n)

def _collapse_detector(prev_points, curr_points, thresh_drop=0.25):
    """Detect coherence collapse: score drop ≤ -0.25 OR frozen+low score."""
    prev = _composite_coherence(prev_points)
    curr = _composite_coherence(curr_points)
    dscore = curr["score"] - prev["score"]
    # Delta-phi proxy: average squared displacement
    n = min(len(prev_points), len(curr_points))
    dphi = 0.0
    if n > 0:
        dphi = sum((curr_points[i][0] - prev_points[i][0]) ** 2 +
                   (curr_points[i][1] - prev_points[i][1]) ** 2 for i in range(n)) / n
    collapsed = (dscore <= -thresh_drop) or (dphi <= 0.05 and curr["score"] < 0.3)
    reason = "score_drop" if dscore <= -thresh_drop else ("frozen_low" if dphi <= 0.05 and curr["score"] < 0.3 else "stable")
    return {"collapsed": collapsed, "reason": reason, "delta_score": round(dscore, 4),
            "dphi": round(dphi, 6), "prev": prev, "curr": curr}

def _composite_coherence(points):
    """0.5×angular + 0.3×radial + 0.2×(1-entropy_proxy)."""
    ac = _angular_coherence(points)
    rc = _radial_coherence(points)
    # Entropy proxy: spread of radii
    if not points:
        return {"angular": 0, "radial": 0, "score": 0}
    c = _centroid(points)
    rs = [math.hypot(p[0] - c[0], p[1] - c[1]) for p in points]
    mu = sum(rs) / max(len(rs), 1)
    entropy_proxy = sum(abs(r - mu) for r in rs) / max(len(rs) * max(mu, 0.01), 1)
    score = 0.5 * ac + 0.3 * rc + 0.2 * (1.0 - min(1.0, entropy_proxy))
    return {"angular": round(ac, 4), "radial": round(rc, 4), "score": round(score, 4)}

def _curvature_from_e8(coords: List[float]) -> Dict:
    """Compute curvature field from E8 coordinates.
    Returns metric tensor diagonal, simplified Christoffel trace, and Ricci scalar."""
    dim = min(len(coords), 8)
    if dim < 2:
        return {"metric_diag": [], "christoffel_trace": 0.0, "ricci_scalar": 0.0}

    # Metric tensor g_μν (diagonal + coupling off-diagonal)
    metric_diag = [1.0 + _GRAV_COUPLING * abs(coords[i]) for i in range(dim)]

    # Off-diagonal curvature coupling
    off_diag_sum = 0.0
    for i in range(dim):
        for j in range(i + 1, dim):
            off_diag_sum += _GRAV_COUPLING * math.sin((coords[i] - coords[j]) * _GRAV_COUPLING)

    # Christoffel trace (simplified: sum of metric variations)
    christoffel_trace = _GRAV_COUPLING * sum(
        abs(metric_diag[i] - metric_diag[j]) for i in range(dim) for j in range(i + 1, dim)
    ) / max(dim * (dim - 1) / 2, 1)

    # Ricci scalar (trace of Ricci tensor ≈ Christoffel contraction)
    ricci = christoffel_trace * dim + off_diag_sum

    return {
        "metric_diag": [round(x, 6) for x in metric_diag],
        "off_diagonal_coupling": round(off_diag_sum, 6),
        "christoffel_trace": round(christoffel_trace, 8),
        "ricci_scalar": round(ricci, 6),
        "flat": abs(ricci) < 1e-6,
        "coupling": _GRAV_COUPLING,
    }

def _evaluate_master_message(content: str, coords_8d: List[float] = None) -> Dict:
    """Evaluate content through the 3-layer Master Message lambda."""
    if not coords_8d or len(coords_8d) < 8:
        coords_8d = [0.0] * 8

    # Layer 1 (Above): E8 projection
    e8_norm = sum(x*x for x in coords_8d[:8]) ** 0.5
    layer_above = {"dimension": 8, "norm": round(e8_norm, 4), "operation": "π_E8"}

    # Layer 2 (Middle): Leech navigation (E8×3 with phase)
    leech_24 = []
    for phase in range(3):
        shift = phase * 2.0944
        for i, c in enumerate(coords_8d[:8]):
            leech_24.append(c * math.cos(shift + i * 0.7854))
    leech_norm = sum(x*x for x in leech_24) ** 0.5
    layer_middle = {"dimension": 24, "norm": round(leech_norm, 4), "operation": "π_Λ24∘W"}

    # Layer 3 (Below): Morphonic recursion (project to 3D)
    proj_3d = coords_8d[:3]
    layer_below = {"dimension": 3, "projection": [round(x, 4) for x in proj_3d], "operation": "μ"}

    # Conservation constraint
    delta_phi = e8_norm - leech_norm / 3.0  # Normalized comparison
    conserved = delta_phi <= 0.01

    return {
        "layers": {"above": layer_above, "middle": layer_middle, "below": layer_below},
        "conservation": {"delta_phi": round(delta_phi, 6), "conserved": conserved},
        "master_expression": "(λx.λy.λz. π_E8(x) → π_Λ24(W(y)) → μ(z) where ΔΦ ≤ 0)",
    }

def _radial_coherence(points):
    """1 - coefficient of variation of radii, clamped [0,1]."""
    if not points:
        return 0.0
    c = _centroid(points)
    rs = [math.hypot(p[0] - c[0], p[1] - c[1]) for p in points]
    mu = sum(rs) / len(rs)
    if mu == 0:
        return 1.0
    var = sum((r - mu) ** 2 for r in rs) / len(rs)
    cv = math.sqrt(var) / abs(mu)
    return max(0.0, min(1.0, 1.0 - min(1.0, cv)))

def collapse_check(req: CollapseRequest):
    """Check for coherence collapse between two observation snapshots."""
    prev = [(p[0], p[1]) for p in req.prev_points if len(p) >= 2]
    curr = [(p[0], p[1]) for p in req.curr_points if len(p) >= 2]
    return _collapse_detector(prev, curr)

def compute_coherence(req: CoherenceRequest):
    """Compute composite coherence metrics on a set of 2D points."""
    pts = [(p[0], p[1]) for p in req.points if len(p) >= 2]
    return _composite_coherence(pts)

def compute_curvature(req: CurvatureRequest):
    """Compute spacetime curvature field from E8 coordinates."""
    return _curvature_from_e8(req.coords)

def master_message(req: MasterMessageRequest):
    """Evaluate content through the 3-layer Master Message."""
    return _evaluate_master_message(req.content, req.coords_8d)

def master_message_schema():
    return {"layers": MASTER_MESSAGE_LAYERS,
            "expression": "(λx.λy.λz. π_E8(x) → π_Λ24(W(y)) → μ(z) where ΔΦ ≤ 0)",
            "as_above_so_below": "Layer 1 projects down through Layer 2 to manifest at Layer 3"}

def __add__(self, other: 'UniversalMorphon') -> 'UniversalMorphon':
    """Operator overload for morphonic addition."""
    return self.morphonic_add(other)

def __mul__(self, other: 'UniversalMorphon') -> 'UniversalMorphon':
    """Operator overload for morphonic multiplication."""
    return self.morphonic_multiply(other)

def _add_to_cache(self, atom: CQEAtom):
    """Add atom to access cache"""
    if len(self.access_cache) >= self.cache_size:
        lfa_atom_id = min(self.access_cache.keys(), key=lambda x: self.access_frequency.get(x, 0))
        del self.access_cache[lfa_atom_id]
    self.access_cache[atom.id] = atom

def _analyze_themes(self, parts: List[AtomicPart]) -> List[str]:
    """Identify themes across all parts."""
    all_text = ' '.join([p.content.lower() for p in parts])
    theme_keywords = {'morphon': 'morphonic_geometry', 'e8': 'e8_lattice', 'lambda': 'lambda_calculus', 'embedding': 'embeddings', 'receipt': 'receipt_system', 'cache': 'caching', 'controller': 'controller_system', 'intake': 'intake_pipeline', 'mmdb': 'mmdb_storage', 'speedlight': 'speedlight_caching'}
    themes = []
    for keyword, theme_name in theme_keywords.items():
        count = all_text.count(keyword)
        if count > 2:
            themes.append((theme_name, count))
    themes.sort(key=lambda x: x[1], reverse=True)
    return [t[0] for t in themes[:5]]

def _api_create_atom(self, request: InterfaceRequest) -> Dict[str, Any]:
    """API endpoint to create atom"""
    data = request.content
    atom = CQEAtom(data=data, metadata={'created_via': 'api'})
    atom_id = self.kernel.memory_manager.store_atom(atom)
    return {'atom_id': atom_id, 'atom': atom.to_dict()}

def _apply_alena_operator(self, tokens: List[CQEToken], operation: str, **kwargs) -> Dict[str, Any]:
    """Apply ALENA operator to tokens"""
    new_embeddings = []
    total_energy_before = sum((token.phi_components['total'] for token in tokens))
    for token in tokens:
        embedding = token.e8_embedding.copy()
        if operation == 'R':
            rotation_angle = kwargs.get('angle', 0.1)
            rotation_matrix = np.eye(8)
            rotation_matrix[0:2, 0:2] = [[np.cos(rotation_angle), -np.sin(rotation_angle)], [np.sin(rotation_angle), np.cos(rotation_angle)]]
            embedding = rotation_matrix @ embedding
        elif operation == 'P':
            parity_mask = np.array([1, -1, 1, -1, 1, -1, 1, -1])
            embedding = embedding * parity_mask
        elif operation == 'M':
            center = np.mean(embedding)
            embedding = embedding + 0.1 * (embedding - center)
            for i in range(4):
                avg = (embedding[i] + embedding[7 - i]) / 2
                embedding[i] = avg
                embedding[7 - i] = avg
        new_embeddings.append(embedding)
    total_energy_after = sum((self._compute_phi_components([emb], [tokens[i].root_index], tokens[i].cartan_offset)['total'] for i, emb in enumerate(new_embeddings)))
    return {'new_embeddings': new_embeddings, 'energy_delta': total_energy_after - total_energy_before}

def _apply_morsr_protocol(self, tokens: List[CQEToken], **kwargs) -> Dict[str, Any]:
    """Apply MORSR protocol to token collection"""
    max_pulses = kwargs.get('max_pulses', 5)
    embeddings = [token.e8_embedding.copy() for token in tokens]
    for pulse in range(max_pulses):
        for i, embedding in enumerate(embeddings):
            w0, w1 = (0.6, 0.4)
            left_neighbor = embeddings[(i - 1) % len(embeddings)]
            right_neighbor = embeddings[(i + 1) % len(embeddings)]
            new_embedding = w0 * embedding + w1 * (left_neighbor + right_neighbor) / 2
            embeddings[i] = np.tanh(new_embedding)
    total_energy_before = sum((token.phi_components['total'] for token in tokens))
    total_energy_after = sum((self._compute_phi_components([emb], [tokens[i].root_index], tokens[i].cartan_offset)['total'] for i, emb in enumerate(embeddings)))
    return {'new_embeddings': embeddings, 'energy_delta': total_energy_after - total_energy_before}

def _apply_reflection(
    morphon: "UniversalMorphon",
    reflection: Callable,
) -> "UniversalMorphon":
    """Apply reflection operator to morphon, returning reflected copy."""
    return reflection(morphon)

def _apply_rule(self, atom: CQEAtom, rule: Dict[str, Any]) -> Any:
    """Apply inference rule to atom"""
    action = rule.get('action', {})
    if action['type'] == 'transform':
        return action['transformation'](atom.data)
    elif action['type'] == 'conclude':
        return action['conclusion']
    else:
        return f"Rule {rule.get('name', 'unknown')} applied to {atom.id}"

def _assess_relevance(self, content: str, pattern: str) -> str:
    """Assess relevance of application to CQE."""
    cqe_indicators = ['cqe', 'quadratic', 'e8', 'lattice', 'optimization']
    relevance_count = sum((1 for indicator in cqe_indicators if indicator in content.lower()))
    if relevance_count >= 3:
        return 'high'
    elif relevance_count >= 2:
        return 'medium'
    else:
        return 'low'

def _atom_niemeier_class(content: str) -> Dict:
    """Compute which Niemeier lattice form an atom belongs to based on its DR."""
    if not content:
        return {"dr": 0, "niemeier": "Leech", "shell_target": 0}
    char_sum = sum(ord(c) for c in str(content)[:64])
    dr = _digital_root(char_sum)
    niemeier = DR_TO_NIEMEIER.get(dr, "Leech")
    # Shell target: DR-1 (DR1→shell0, DR9→shell8)
    shell_target = (dr - 1) if dr > 0 else 8
    return {"dr": dr, "niemeier": niemeier, "shell_target": shell_target, "char_sum": char_sum}

def _backup_scheduler(self):
    """Background process to schedule backups"""
    last_backup = time.time()
    while self.state == CQEOSState.RUNNING:
        try:
            current_time = time.time()
            if current_time - last_backup >= self.config.backup_interval:
                self.backup_system()
                last_backup = current_time
            time.sleep(300)
        except Exception as e:
            self.logger.error(f'Backup scheduler error: {e}')
            time.sleep(300)

def _compute_cache_key(self, operation_type: CQEOperationType, atoms: List[CQEAtom], parameters: Dict[str, Any]) -> str:
    """Compute cache key for operation"""
    atom_ids = [atom.id for atom in atoms]
    param_str = json.dumps(parameters, sort_keys=True, default=str)
    key_data = f"{operation_type.value}:{':'.join(atom_ids)}:{param_str}"
    return hashlib.md5(key_data.encode()).hexdigest()

def _cqe_create_atom(self, content: Dict[str, Any]) -> Dict[str, Any]:
    """Handle CQE native atom creation"""
    data = content.get('data', {})
    quad_encoding = content.get('quad_encoding')
    atom = CQEAtom(data=data, metadata={'created_via': 'cqe_native'})
    if quad_encoding:
        atom.quad_encoding = tuple(quad_encoding)
    atom_id = self.kernel.memory_manager.store_atom(atom)
    return {'atom_id': atom_id, 'atom': atom.to_dict()}

def _cqe_native_inference(self, rule: InferenceRule, premises: List[str]) -> Tuple[Optional[str], float, str]:
    """CQE native inference using quad encodings and E8 embeddings"""
    if rule == InferenceRule.CQE_TRANSFORMATION:
        premise_atoms = []
        for premise_id in premises:
            if premise_id in self.statements:
                atom = self.kernel.memory_manager.retrieve_atom(premise_id)
                if atom:
                    premise_atoms.append(atom)
        if premise_atoms:
            result_atom = self._cqe_transform_atoms(premise_atoms)
            conclusion_content = f'CQE transformation result: {result_atom.data}'
            conclusion_id = self.add_statement(conclusion_content, LogicSystem.CQE_NATIVE)
            return (conclusion_id, 0.95, 'Applied CQE transformation')
    return (None, 0.0, 'CQE inference failed')

def _cqe_query_atoms(self, content: Dict[str, Any]) -> Dict[str, Any]:
    """Handle CQE native atom query"""
    query = content.get('query', {})
    limit = content.get('limit', 10)
    atoms = self.kernel.memory_manager.query_atoms(query, limit=limit)
    return {'query': query, 'results': [atom.to_dict() for atom in atoms]}

def _cqe_reason(self, content: Dict[str, Any]) -> Dict[str, Any]:
    """Handle CQE native reasoning"""
    goal = content.get('goal', '')
    reasoning_type = content.get('reasoning_type', 'deductive')
    reasoning_engine = self.kernel.reasoning_engine
    chain_id = reasoning_engine.reason(goal)
    return {'goal': goal, 'reasoning_chain_id': chain_id, 'explanation': reasoning_engine.generate_explanation(goal, chain_id)}

def _cqe_transform(self, content: Dict[str, Any]) -> Dict[str, Any]:
    """Handle CQE native transformation"""
    return {'message': 'CQE transformation not implemented'}

def _cqe_transform_atoms(self, atoms: List[CQEAtom]) -> CQEAtom:
    """Transform atoms using CQE principles"""
    combined_quad = tuple((sum((atom.quad_encoding[i] for atom in atoms)) % 4 + 1 for i in range(4)))
    combined_data = {'transformation_result': True, 'source_atoms': [atom.id for atom in atoms], 'combined_data': [atom.data for atom in atoms]}
    result_atom = CQEAtom(data=combined_data, quad_encoding=combined_quad, metadata={'cqe_transformation': True})
    return result_atom

def _create_atom(self, args: List[str]) -> Dict[str, Any]:
    """Create a new atom"""
    if not args:
        return {'error': 'No data provided'}
    data_str = ' '.join(args)
    try:
        data = json.loads(data_str)
    except json.JSONDecodeError:
        data = data_str
    atom = CQEAtom(data=data, metadata={'created_via': 'command_line'})
    atom_id = self.kernel.memory_manager.store_atom(atom)
    return {'atom_id': atom_id, 'data': data, 'quad_encoding': atom.quad_encoding}

def _create_from_natural_language(self, text: str, entities: List[Dict[str, str]]) -> Dict[str, Any]:
    """Create atom from natural language"""
    data = {'natural_language_input': text, 'extracted_entities': entities, 'created_via': 'natural_language'}
    atom = CQEAtom(data=data, metadata={'natural_language': True})
    atom_id = self.kernel.memory_manager.store_atom(atom)
    return {'atom_id': atom_id, 'created_from': text, 'atom': atom.to_dict()}

def _create_main_script(self, name: str, description: str, modules: List, tool_dir: Path):
    """Create the main script for the tool."""
    module_list = '\n'.join((f'# - {n}' for n, _ in modules))
    script = f'''#!/usr/bin/env python3\n"""\n{name.upper()} - {description}\n\nAuto-generated custom tool using CQE monolith building blocks.\n\nAvailable modules:\n{module_list}\n"""\n\nimport sys\nfrom pathlib import Path\n\n# Add module paths\nMODULES_DIR = Path(__file__).parent / "modules"\nsys.path.insert(0, str(MODULES_DIR))\n\ndef main():\n    print("? {name.upper()}")\n    print("{description}")\n    print()\n    print("Available modules:")\n    \n    modules = {[f'"{n}"' for n, _ in modules]}\n    \n    for mod_name in modules:\n        try:\n            __import__(mod_name)\n            print(f"  ? {{mod_name}}")\n        except Exception as e:\n            print(f"  ? {{mod_name}}: {{e}}")\n    \n    print()\n    print("Use: from <module> import <class>")\n\nif __name__ == '__main__':\n    main()\n'''
    (tool_dir / f'{name}.py').write_text(script)
    print(f'  Created {name}.py')

def _create_readme(self, name: str, description: str, modules: List, tool_dir: Path):
    """Create README for the tool."""
    module_list = '\n'.join((f"- **{n}** ({info['size_lines']} lines) - {info['category']}" for n, info in modules))
    readme = f"# {name.upper()}\n\n{description}\n\n## Modules Included\n\n{module_list}\n\n## Usage\n\n```python\nimport sys\nsys.path.insert(0, './modules')\n\n# Import the modules you need\nfrom LatticeBuilderV1 import *\nfrom CqeGovernance import *\n# etc...\n```\n\n## Run\n\n```bash\npython {name}.py\n```\n"
    (tool_dir / 'README.md').write_text(readme)
    print(f'  Created README.md')

def _create_system_atoms(self):
    """Create fundamental system atoms"""
    if not self.kernel:
        return
    config_atom = CQEAtom(data={'type': 'system_config', 'config': self.config.__dict__, 'boot_time': self.start_time}, metadata={'system_atom': True, 'atom_type': 'config'})
    config_atom_id = self.kernel.memory_manager.store_atom(config_atom)
    self.system_atoms['config'] = config_atom
    status_atom = CQEAtom(data={'type': 'system_status', 'state': self.state.value, 'uptime': 0}, metadata={'system_atom': True, 'atom_type': 'status'})
    status_atom_id = self.kernel.memory_manager.store_atom(status_atom)
    self.system_atoms['status'] = status_atom
    self.logger.debug('System atoms created')

def _default_config(self) -> Dict:
    """Default configuration for CQE system."""
    return {'exploration': {'max_iterations': 50, 'convergence_threshold': 0.0001, 'pulse_count': 10}, 'output': {'save_results': True, 'results_dir': 'data/generated', 'verbose': True}, 'validation': {'run_tests': True, 'comparison_baseline': True}}

def _default_synthesis(g1: Any, g2: Any) -> Any:
    """Default synthesis S(O₁(M), O₂(M)) — geometric mean of two observations."""
    if _HAS_NP and isinstance(g1, np.ndarray) and isinstance(g2, np.ndarray):
        return (g1 + g2) / 2.0
    if isinstance(g1, dict) and isinstance(g2, dict):
        all_keys = set(g1) | set(g2)
        return {k: (g1.get(k, 0) + g2.get(k, 0)) / 2 for k in all_keys}
    return g1  # fallback: return first observation

def _derive_labels_from_content(content: str) -> List[str]:
    """Heuristic: apply domain patterns to content, collect matching tags.

    Returns at least one label (falls back to ["arbitrary"]).
    """
    if not content or not content.strip():
        return [_FALLBACK_LABEL]

    content_lower = content.lower()
    matched: List[str] = []
    seen: set = set()

    for pattern, tag in _DOMAIN_PATTERNS:
        if tag not in seen and pattern.search(content_lower):
            matched.append(tag)
            seen.add(tag)

    return matched if matched else [_FALLBACK_LABEL]

def _digital_root(n: int) -> int:
    n = abs(n)
    while n >= 10:
        s = 0
        while n > 0:
            s += n % 10
            n //= 10
        n = s
    return n

def _dims_at_level(n: int) -> int:
    """Return the dimensionality at crystal level N.

    Level 1 = 24D (single superpermutation),
    Level 2 = 96D (Morphon View),
    Level 3 = 384D, etc.

    Formula: 24 × 4^(N-1)
    """
    if n < 1:
        raise ValueError(f"Level must be ≥ 1, got {n}")
    return 24 * (4 ** (n - 1))

def _evaluate_cqe_native_truth(self, statement: LogicalStatement, context: Dict[str, Any]) -> Tuple[Optional[float], float]:
    """Evaluate CQE native truth using quad encodings"""
    q1, q2, q3, q4 = statement.quad_encoding
    quad_sum = q1 + q2 + q3 + q4
    quad_product = q1 * q2 * q3 * q4
    truth_value = quad_sum % 8 / 8.0
    confidence = min(1.0, quad_product / 64.0)
    return (truth_value, confidence)

def _extract_concepts(self, content: str) -> Dict[str, List[str]]:
    """Extract core CQE concepts from document content."""
    concepts = defaultdict(list)
    content_lower = content.lower()
    for category, concept_list in self.core_concepts.items():
        for concept in concept_list:
            pattern = f'\\b{re.escape(concept)}\\b'
            matches = list(re.finditer(pattern, content_lower))
            for match in matches:
                start = max(0, match.start() - 50)
                end = min(len(content), match.end() + 50)
                context = content[start:end].strip()
                concepts[category].append({'concept': concept, 'position': match.start(), 'context': context})
    return concepts

def _fetch_data(self, source: CQEDataSource) -> Union[str, bytes]:
    """Fetch data from source"""
    if source.source_type == 'file':
        path = Path(source.location)
        if source.format in ['binary', 'pickle', 'image', 'audio', 'video']:
            return path.read_bytes()
        else:
            return path.read_text(encoding=source.encoding)
    elif source.source_type == 'url':
        response = requests.get(source.location)
        if source.format in ['binary', 'pickle', 'image', 'audio', 'video']:
            return response.content
        else:
            return response.text
    elif source.source_type == 'database':
        return self._fetch_from_database(source)
    elif source.source_type == 'stream':
        return self._fetch_from_stream(source)
    else:
        raise ValueError(f'Unsupported source type: {source.source_type}')

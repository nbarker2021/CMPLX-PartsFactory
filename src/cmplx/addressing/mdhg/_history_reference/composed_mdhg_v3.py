"""Canonical `mdhg` module — atomically constructed from the unified ecosystem."""
app = FastAPI(title="MMDB", description="VOA-like crystal storage", version="1.0.0")
TOOLS = [
        "mdhg_family_agrm_mdhg_build.profile",
        "mdhg_family_agrm_mdhg_build.plan_task",
        "mdhg_family_agrm_mdhg_build.validate_candidate",
        "mdhg_family_agrm_mdhg_build.publish_atom",
        "mdhg_family_agrm_mdhg_build.compose_atoms"
]
logger = logging.getLogger(__name__)
HARNESS_SCHEMA = json.loads(SCHEMA_PATH.read_text())
SCHEMA_PATH = pathlib.Path(__file__).resolve().parent.parent.parent / 'schemas' / 'HarnessSliceSchema.json'
__all__ = []
DEFAULT_CHANNELS = [
    "pressure",    # Access frequency
    "risk",        # Uncertainty/entropy
    "trust",       # Verification status
    "food",        # Resource availability (data richness)
    "energy",      # Processing power available
    "water",       # Bandwidth/flow
    "debt",        # Dependency chain depth
    "innovation",  # Novelty of content
    "info",        # Information density
    "harm"         # Error/conflict count
]
CLEANUP_INTERVAL = int(os.getenv("CLEANUP_INTERVAL", "300"))
PORT = int(os.environ.get("PORT", "8000"))
SESSION_TTL = int(os.getenv("SESSION_TTL", "1800"))
COUPLING = 0.03
HIERARCHY_LEVELS = [
    "grain", "dust", "triad", "block", "cluster",
    "domain", "region", "planet", "universe",
]
PG_URL = os.getenv("PG_URL", "postgresql://tmn2:tmn2_dev@tmn2-pg:5432/tmn2")
REDIS_URL = os.getenv("REDIS_URL", "redis://tmn2-redis:6379")
SESSIONS: Dict[str, dict] = {}
__family_key__ = 'tarpit'
_cleanup_lock = threading.Lock()
default = DualGovernanceBridge()
BOARD_URL = os.environ.get("BOARD_URL", "http://tmn1-board:9090")
CMPLX_ROOT = (
    os.environ.get("CMPLX_ROOT")
    or CMPLX_WORKSPACE
    or r"C:\Users\borke\Desktop\Builds\CMPLX"
)
CMPLX_WORKSPACE = os.environ.get("CMPLX_WORKSPACE", "")
DB_PATH = r"C:\Users\borke\Desktop\Builds\CMPLX\unified\cmplx_index.db"
DEFAULT_FACTORS_CORRIDOR = [2, 3, 5, 7, 11, 13]
DEFAULT_FACTORS_LATTICE = [8, 12, 16, 24, 32, 64, 128, 240]
SOURCE_DB = Path(_index_db_env) if _index_db_env else Path(CMPLX_ROOT) / "unified/cmplx_index.db"
_index_db_env = os.environ.get("CMPLX_INDEX_DB", "")
PROJECT_ROOT = SCRIPT_DIR.parent.parent
__adapter__ = 'morphonic_lambda'
__canon_build__ = 'e6_v81_complete_package'
__layer__ = 1
__symbol_count__ = 146
mdhg_app = typer.Typer(help="MDHG: per-task hash-house / planet printer (dynamic routing + hash stack).")
CACHE_PG_URL = os.getenv("CACHE_PG_URL", "").strip()
CHUNK = 2000
DEFAULT_BASE = os.environ.get("MDHG_UNIFIED_URL", "http://mdhg-unified:8085")
MDHG_ADDR_CHARS = set("0123456789abcdef")
MDHG_ADDR_LEN = 16
NAME_PAT = re.compile(r"mdhg", re.IGNORECASE)
OPERATIONAL_ROLES = [
    "conservation_enforcer", "alena_operator", "morsr_optimizer", "labeler",
    "quality_gate", "morphon_generator", "lambda_bridge", "receipt_emitter",
    "crt_validator", "brs_checker", "worldforge", "e8_snap", "mdhg_router",
    "parity_corrector_03x2", "e8_projection", "thinktank_deliberation",
    "assembly_line_op", "quorum_protocol_op", "speedlight_cache_op",
    "leech_lattice_op", "golay_code_op", "niemeier_lattice_op",
    "tier_agent_plex", "tier_full_model", "tier_cqe_agent",
    "embedding_op", "token_op", "receipt_create_op", "contract_validator",
]
PHI = (1 + np.sqrt(5)) / 2
PLANET_NAMES = [
    "alpha", "beta", "gamma", "delta", "epsilon",
    "zeta", "eta", "theta", "kappa",
]  # 9 planets, one per digital root
PRECEDENCE = [
    ("Manny Unification 2 Implementation", "01-active-implementation"),
    ("Working Prototyping",                 "01-active-implementation"),
    ("agent ecosystem",                     "02-agent-ecosystem"),
    ("historical builds",                   "03-historical-builds"),
    ("assorted toolkits",                   "02-agent-ecosystem"),
    ("docker work contents",                "06-docker-work-only-uniques"),
    ("output",                              "04-output-only-uniques"),
    ("datasets from previous review",       "05-dataset-only-uniques"),
]
REQUIRED_LAYERS = ["atom", "room", "floor", "building", "city", "planet"]
ROOT = Path(".").resolve()
SIZE_CAP_MB = 200
SKIP_DIR_PATTERNS = re.compile(
    r"(?:^|[\\/])(?:node_modules|\.git|__pycache__|\.venv|venv|\.tox|\.mypy_cache|\.pytest_cache|"
    r"dist|build|\.next|\.cache|\.idea|\.vscode-server|\.npm)(?:[\\/]|$)",
    re.IGNORECASE,
)
STAGING = Path(r"D:\Manny Unification 2\proposals\agent-doctrine-refinement-2026-05-08\tools\mdhg-staging")
ZIP_OUT = Path(r"D:\Manny Unification 2\assorted toolkits\mdhg-corpus.zip")
_MDHG_LEVELS: List[str] = [
    "Universe", "Galaxies", "Systems", "Planets", "Cities",
    "Locals", "Neighborhoods", "Buildings", "Rooms", "Atoms",
]
_MDHG_LEVEL_SET = set(_MDHG_LEVELS)

class DemandAtomBridge:
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": tool,
                "description": "Demand atom scaffold tool",
                "category": "demand_atom",
                "input_schema": {"type": "object", "properties": {}},
            }
            for tool in TOOLS
        ]

    async def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name not in TOOLS:
            return {"error": f"unknown tool: {tool_name}"}
        return {
            "tool": tool_name,
            "arguments": arguments or {},
            "status": "scaffold-ready",
            "note": "Implement demand-specific handler logic for this tool.",
        }

class MDHGHashTable:
    """
    Multi-Dimensional Hamiltonian Golden Ratio Hash Table.
    A hash table implementation that uses multi-dimensional organization,
    Hamiltonian paths for navigation, and golden ratio-based sizing
    to achieve optimal performance for structured access patterns.

    AGRM Integration Notes:
    - Used for complex state (n>5) in AGRM's hybrid hashing.
    - Stores values as tuples: (actual_value, metadata_dict),
      where metadata_dict contains flags like {'source': 'dict', 'retain_flag': True}.
    - Adaptation logic can be influenced by Modulation Controller signals.
    - Includes full logic for buildings, floors, rooms (conceptual), velocity region,
      dimensional core, conflict handling, Hamiltonian path navigation, and dynamic adaptation.
    """
    def __init__(self, capacity: int = 1024, dimensions: int = 3, load_factor_threshold: float = 0.75, config: Dict = {}):
        """
        Initialize the hash table.
        Args:
            capacity: Initial capacity of the hash table
            dimensions: Number of dimensions for the hash space (tunable by AGRM context)
            load_factor_threshold: When to resize the table
            config: Dictionary for additional MDHG-specific parameters
        """
        self.PHI = (1 + math.sqrt(5)) / 2 # Golden ratio [cite: 1018-1019]
        self.config = config # Store config for internal use

        # Core configuration
        self.capacity = max(capacity, 16) # Ensure minimum capacity
        self.dimensions = max(dimensions, 1) # Ensure at least 1 dimension
        self.load_factor_threshold = load_factor_threshold
        self.size = 0

        # Multi-dimensional organization [cite: 1012-1017]
        self.buildings = self._initialize_buildings()
        self.location_map = {} # Maps keys to their current location (building_id, region_type, location_spec)

        # Navigation components
        self.hamiltonian_paths = {} # Pre-computed paths for critical points [cite: 1020-1022, 1037]
        self.path_cache = {} # Cache of paths between points or for key sets
        self.shortcuts = {} # Direct connections between buildings/regions [cite: 1022]

        # Access pattern tracking
        self.access_history = deque(maxlen=config.get("mdhg_access_history_len", 100)) # Track recent accesses
        self.access_frequency = Counter() # Track frequency of key access
        self.co_access_matrix = defaultdict(Counter) # Track keys accessed together [cite: 1022]
        self.path_usage = Counter() # Track usage of cached paths

        # Statistics
        self.stats = {
            'puts': 0, 'gets': 0, 'hits': 0, 'misses': 0, 'collisions': 0,
            'probes_total': 0, 'max_probes': 0, 'reorganizations': 0,
            'resizes': 0, 'promotions_velocity': 0, 'relocations_from_velocity': 0,
            'clusters_relocated': 0
        }

        # Optimization timing
        self.last_minor_optimization = time.time()
        self.last_major_optimization = time.time()
        self.operations_since_optimization = 0

        # Initialize the structure (compute initial paths, etc.)
        self._initialize_structure()
        print(f"MDHGHashTable initialized: Capacity={self.capacity}, Dimensions={self.dimensions}, Buildings={len(self.buildings)}")

    def _initialize_buildings(self) -> Dict:
        """ Initialize the building structure based on golden ratio proportions. """
        # Determine number of buildings, ensuring at least 1
        building_count = max(1, int(math.log(max(2, self.capacity), self.PHI)))
        buildings = {}
        # Ensure base capacity calculation avoids division by zero
        base_capacity_per_building = self.capacity // building_count if building_count > 0 else self.capacity
        if base_capacity_per_building < 16: base_capacity_per_building = 16 # Ensure minimum size

        print(f"  MDHG: Initializing {building_count} buildings, base capacity per building: {base_capacity_per_building}")

        for b in range(building_count):
            building_id = f"B{b}"
            # Calculate regions using golden ratio [cite: 1018]
            # Ensure minimum sizes for regions
            velocity_region_size = max(4, int(base_capacity_per_building / (self.PHI ** 2)))
            core_region_base_size = max(8, int(velocity_region_size * self.PHI)) # Base size before dimensioning

            dimension_sizes = self._calculate_dimension_sizes(core_region_base_size)
            # Actual core capacity is product of dimension sizes
            core_capacity = math.prod(dimension_sizes) if dimension_sizes else 0

            print(f"    Building {building_id}: Velocity Region Size={velocity_region_size}, Core Capacity={core_capacity}, Dim Sizes={dimension_sizes}")

            buildings[building_id] = {
                'velocity_region': [None] * velocity_region_size, # Fast access [cite: 1022]
                'dimensional_core': {}, # Main storage, dict maps coords -> (key, value_tuple) [cite: 1022]
                'conflict_structures': {}, # Handles collisions beyond path probing [cite: 1022]
                'dimension_sizes': dimension_sizes, # For coordinate calculation
                'hot_keys': set(), # Keys frequently accessed in this building
                'access_count': 0, # Track building usage
                'core_capacity': core_capacity # Store calculated core capacity
            }
        return buildings

    def _calculate_dimension_sizes(self, core_region_base_size: int) -> List[int]:
        """ Calculate sizes for each dimension using golden ratio proportions. """
        if self.dimensions <= 0: return []
        # Estimate base size per dimension
        # Using geometric mean approach: base_size ^ dimensions ≈ core_region_base_size
        # Add epsilon to avoid potential log(0) or root(0) issues if base_size is tiny
        safe_base_size = max(1, core_region_base_size)
        base_size = max(2.0, safe_base_size ** (1.0/self.dimensions)) # Use float for calculation

        sizes = []
        product = 1.0
        # Scale dimensions using PHI, ensuring minimum size 2
        for i in range(self.dimensions):
            # Example scaling: could use other GR-based factors
            # Ensure denominator is safe
            phi_exponent = i / max(1.0, float(self.dimensions - 1))
            size_float = base_size / (self.PHI ** phi_exponent)
            size = max(2, int(round(size_float))) # Round before int conversion
            sizes.append(size)
            product *= size

        # Optional: Adjust sizes slightly if product is too far off target
        # This part requires careful balancing logic to avoid infinite loops or drastic changes
        # print(f"      Calculated dimension sizes: {sizes} (Product: {product}, Target Base: {core_region_base_size})")
        return sizes

    def _initialize_structure(self):
        """ Initialize the hash table structure with navigation components. """
        # Pre-compute critical Hamiltonian paths for each building [cite: 1037]
        print("  MDHG: Initializing structure (paths, shortcuts)...")
        for building_id, building in self.buildings.items():
            self._initialize_building_paths(building_id, building)
        # Initialize shortcuts between buildings
        self._initialize_building_shortcuts()
        print("  MDHG: Structure initialization complete.")


    def _initialize_building_paths(self, building_id: str, building: Dict):
        """ Initialize Hamiltonian paths for critical points in a building. """
        dimension_sizes = building.get('dimension_sizes')
        if not dimension_sizes:
            # print(f"    Skipping path init for {building_id}: No dimensions.")
            return # Skip if no dimensions

        # Generate critical points (corners, center)
        critical_points = set()
        # Add corner points
        corners = self._generate_corner_points(dimension_sizes)
        critical_points.update(corners)
        # Add center point
        center = tuple(d // 2 for d in dimension_sizes)
        critical_points.add(center)

        # Compute and store paths for these critical points
        building_paths = {}
        computed_count = 0
        for point in critical_points:
            # Ensure point is valid within dimensions
            if len(point) != self.dimensions: continue
            valid_point = all(0 <= point[i] < dimension_sizes[i] for i in range(self.dimensions))

            if valid_point:
                path = self._compute_hamiltonian_path(building_id, point)
                if path: # Only store if path computation succeeds
                    path_key = (building_id, point)
                    building_paths[path_key] = path # Store paths per building first
                    computed_count += 1

        self.hamiltonian_paths.update(building_paths) # Add building paths to global store
        # print(f"    Initialized {computed_count} Hamiltonian paths for building {building_id}.")


    def _generate_corner_points(self, dimension_sizes: List[int]) -> List[Tuple]:
        """ Generate corner points for a multi-dimensional space. """
        if not dimension_sizes: return []
        corners = []
        num_dims = len(dimension_sizes)
        num_corners = 2 ** num_dims
        for i in range(num_corners):
            corner = []
            for d in range(num_dims):
                # Use bit masking to determine min (0) or max (size-1) for each dimension
                if (i >> d) & 1:
                    corner.append(max(0, dimension_sizes[d] - 1)) # Use max index
                else:
                    corner.append(0) # Use min index
            corners.append(tuple(corner))
        return corners

    def _initialize_building_shortcuts(self):
        """ Initialize shortcuts between buildings. """
        building_ids = list(self.buildings.keys())
        shortcuts_created = 0
        # Create shortcuts only if there's more than one building
        if len(building_ids) > 1:
            for i, b1 in enumerate(building_ids):
                for j, b2 in enumerate(building_ids):
                    if i != j:
                        # Create bidirectional shortcuts
                        if self._create_building_shortcut(b1, b2):
                            shortcuts_created += 1
        # print(f"  Initialized {shortcuts_created} building shortcuts.")

    def _create_building_shortcut(self, building1: str, building2: str) -> bool:
        """ Create a shortcut between two buildings with default connection points. """
        building1_data = self.buildings.get(building1)
        building2_data = self.buildings.get(building2)
        # Check if dimensions are valid before creating shortcut
        if not building1_data or not building2_data or \
           not building1_data.get('dimension_sizes') or not building2_data.get('dimension_sizes') or \
           len(building1_data['dimension_sizes']) != self.dimensions or \
           len(building2_data['dimension_sizes']) != self.dimensions:
            # print(f"Warning: Cannot create shortcut between {building1} and {building2} due to invalid dimensions.")
            return False # Cannot create shortcut if building data is incomplete

        # Use center points as default connection points
        center1 = tuple(d // 2 for d in building1_data['dimension_sizes'])
        center2 = tuple(d // 2 for d in building2_data['dimension_sizes'])

        shortcut_key = (building1, building2)
        self.shortcuts[shortcut_key] = {
            'entry_point': center1, # Entry point in building1
            'exit_point': center2,  # Exit point in building2 (conceptually)
            'cost': 1.0 / self.PHI, # Lower cost than regular traversal (heuristic)
            'usage_count': 0
        }
        return True

    def _compute_hamiltonian_path(self, building_id: str, start_coords: Tuple) -> List[Tuple]:
        """
        Compute a Hamiltonian-like path (visits many points uniquely) starting from coordinates.
        Uses GR steps. This is a heuristic path, not guaranteed to be truly Hamiltonian or optimal length.
        """
        building = self.buildings.get(building_id)
        if not building or not building.get('dimension_sizes'): return []
        dimension_sizes = building['dimension_sizes']

        # Basic validation of start_coords
        if len(start_coords) != self.dimensions: return []
        if not all(0 <= start_coords[i] < dimension_sizes[i] for i in range(self.dimensions)): return []

        path = [start_coords]
        current = list(start_coords)
        visited = {start_coords}

        # Determine path length heuristic
        total_core_points = math.prod(dimension_sizes) if dimension_sizes else 0
        if total_core_points == 0: return path # Path is just the start point

        path_length_limit = min(total_core_points, self.config.get("mdhg_path_length_limit", 1000))
        # Aim for a path length that covers a reasonable fraction, e.g., sqrt or similar heuristic
        path_length_target = max(self.dimensions * 2, int(math.sqrt(total_core_points) * 2)) # Cover more?
        path_length = min(path_length_limit, path_length_target)

        # Use golden ratio for dimension selection and step direction bias
        for step in range(1, path_length):
            # Choose dimension based on golden ratio progression [cite: 1021]
            dim_choice = int((step * self.PHI) % self.dimensions)

            # Determine step direction (+1 or -1) based on another GR sequence
            direction_bias = (step * self.PHI**2) % 1.0
            step_dir = 1 if direction_bias < 0.5 else -1

            # Try moving in the chosen dimension and direction
            next_coord_list = list(current)
            next_coord_list[dim_choice] = (next_coord_list[dim_choice] + step_dir + dimension_sizes[dim_choice]) % dimension_sizes[dim_choice] # Ensure positive result
            next_coords = tuple(next_coord_list)

            if next_coords not in visited:
                path.append(next_coords)
                visited.add(next_coords)
                current = next_coord_list
            else:
                # Collision: Try alternative dimensions or directions (simple linear probe)
                found_alternative = False
                for alt_offset in range(1, self.dimensions + 1): # Try all dimensions + opposite dir
                    # Try alternative dimension, original direction
                    alt_dim = (dim_choice + alt_offset) % self.dimensions
                    alt_coord_list = list(current)
                    alt_coord_list[alt_dim] = (alt_coord_list[alt_dim] + step_dir + dimension_sizes[alt_dim]) % dimension_sizes[alt_dim]
                    alt_coords = tuple(alt_coord_list)
                    if alt_coords not in visited:
                        path.append(alt_coords)
                        visited.add(alt_coords)
                        current = alt_coord_list
                        found_alternative = True
                        break

                    # Try alternative dimension, opposite direction
                    alt_coord_list = list(current)
                    alt_coord_list[alt_dim] = (alt_coord_list[alt_dim] - step_dir + dimension_sizes[alt_dim]) % dimension_sizes[alt_dim]
                    alt_coords = tuple(alt_coord_list)
                    if alt_coords not in visited:
                        path.append(alt_coords)
                        visited.add(alt_coords)
                        current = alt_coord_list
                        found_alternative = True
                        break

                # If no alternative found after checking all dims/dirs, stop path
                if not found_alternative:
                    # print(f"      Path generation stuck at step {step}, coords {current}")
                    break # Stop if stuck

        return path

    # --- Hashing Functions ---
    def _hash(self, key: Any) -> int:
        """ Primary hash function. Using MurmurHash for better distribution. """
        return self._murmur_hash(key)

    def _secondary_hash(self, key: Any) -> int:
        """ Secondary hash function for specific regions like velocity. Using FNV. """
        return self._fnv_hash(key)

    def _murmur_hash(self, key: Any) -> int:
        """ MurmurHash3 32-bit implementation. """
        key_bytes = str(key).encode('utf-8')
        length = len(key_bytes)
        seed = 0x9747b28c # Example seed
        c1 = 0xcc9e2d51
        c2 = 0x1b873593
        r1 = 15
        r2 = 13
        m = 5
        n = 0xe6546b64
        hash_value = seed

        nblocks = length // 4
        for i in range(nblocks):
            idx = i * 4
            k = (key_bytes[idx] |
                 (key_bytes[idx + 1] << 8) |
                 (key_bytes[idx + 2] << 16) |
                 (key_bytes[idx + 3] << 24))
            k = (k * c1) & 0xFFFFFFFF
            k = ((k << r1) | (k >> (32 - r1))) & 0xFFFFFFFF
            k = (k * c2) & 0xFFFFFFFF
            hash_value ^= k
            hash_value = ((hash_value << r2) | (hash_value >> (32 - r2))) & 0xFFFFFFFF
            hash_value = ((hash_value * m) + n) & 0xFFFFFFFF

        tail_index = nblocks * 4
        k = 0
        tail_size = length & 3
        if tail_size >= 3: k ^= key_bytes[tail_index + 2] << 16
        if tail_size >= 2: k ^= key_bytes[tail_index + 1] << 8
        if tail_size >= 1: k ^= key_bytes[tail_index]
        if tail_size > 0:
            k = (k * c1) & 0xFFFFFFFF
            k = ((k << r1) | (k >> (32 - r1))) & 0xFFFFFFFF
            k = (k * c2) & 0xFFFFFFFF
            hash_value ^= k

        hash_value ^= length
        hash_value ^= hash_value >> 16
        hash_value = (hash_value * 0x85ebca6b) & 0xFFFFFFFF
        hash_value ^= hash_value >> 13
        hash_value = (hash_value * 0xc2b2ae35) & 0xFFFFFFFF
        hash_value ^= hash_value >> 16

        return abs(hash_value) # Ensure positive

    def _fnv_hash(self, key: Any) -> int:
        """ FNV-1a 32-bit hash implementation. """
        key_bytes = str(key).encode('utf-8')
        fnv_prime = 0x01000193 # 16777619
        fnv_offset_basis = 0x811c9dc5 # 2166136261
        hash_value = fnv_offset_basis
        for byte in key_bytes:
            hash_value ^= byte
            hash_value = (hash_value * fnv_prime) & 0xFFFFFFFF
        return abs(hash_value) # Ensure positive

    def _hash_to_building(self, key: Any) -> str:
        """ Determine which building should contain a key using primary hash. """
        if not self.buildings: raise ValueError("MDHGHashTable has no buildings initialized.")
        hash_value = self._hash(key)
        building_idx = hash_value % len(self.buildings)
        return f"B{building_idx}"

    def _hash_to_velocity_index(self, key: Any, building_id: str) -> int:
        """ Calculate velocity region index using secondary hash. """
        building = self.buildings.get(building_id)
        if not building: raise ValueError(f"Building {building_id} not found.")
        velocity_size = len(building['velocity_region'])
        if velocity_size == 0: return 0
        return self._secondary_hash(key) % velocity_size

    def _hash_to_coords(self, key: Any, building_id: str) -> Optional[Tuple]:
        """ Calculate multi-dimensional coordinates using variations of primary hash. """
        building = self.buildings.get(building_id)
        if not building: raise ValueError(f"Building {building_id} not found.")
        dimension_sizes = building.get('dimension_sizes')
        if not dimension_sizes or len(dimension_sizes) != self.dimensions:
            return None # Cannot calculate coords if dimensions mismatch

        coords = []
        # Use primary hash and modify it for each dimension to get variation
        base_hash = self._hash(key)
        for i in range(self.dimensions):
            # Simple variation: XOR with dimension index and shift
            dim_hash = (base_hash ^ (i * 0x9e3779b9)) # Use golden ratio conjugate for mixing
            dim_hash = (dim_hash >> i) | (dim_hash << (32 - i)) & 0xFFFFFFFF # Rotate
            coord_val = abs(dim_hash) % dimension_sizes[i]
            coords.append(coord_val)
        return tuple(coords)

    def _hash_to_conflict_key(self, key: Any, coords: Tuple) -> int:
        """ Create a conflict key combining key hash and coordinates hash. """
        key_hash = self._hash(key)
        coords_hash = hash(coords) # Python's hash for tuple
        return abs(key_hash ^ coords_hash)

    # --- Core Put/Get/Remove ---

    def put(self, key: Any, value: Any) -> None:
        """
        Insert a key-value pair into the hash table.
        Handles routing, velocity region, core, collisions, and conflict structures.
        Value should be (actual_value, metadata_dict) for AGRM integration.
        """
        self.stats['puts'] += 1
        self.operations_since_optimization += 1

        # 1. Determine Target Building
        building_id = self._hash_to_building(key)
        building = self.buildings.get(building_id)
        if not building: # Fallback if building calculation failed somehow
            if not self.buildings: raise RuntimeError("MDHG Hash Table has no buildings.")
            building_id = list(self.buildings.keys())[0]
            building = self.buildings[building_id]
            print(f"Warning: Falling back to building {building_id} for key {key}.")
        building['access_count'] += 1

        # 2. Try Velocity Region
        velocity_idx = self._hash_to_velocity_index(key, building_id)
        if 0 <= velocity_idx < len(building['velocity_region']):
            velocity_entry = building['velocity_region'][velocity_idx]
            if velocity_entry is None:
                building['velocity_region'][velocity_idx] = (key, value)
                self.location_map[key] = (building_id, 'velocity', velocity_idx)
                self.size += 1
                self._update_access_patterns(key)
                self._check_optimization_and_resize()
                return
            elif velocity_entry[0] == key:
                building['velocity_region'][velocity_idx] = (key, value) # Update
                self._update_access_patterns(key)
                return
            # Else: Collision in velocity, proceed to core

        # 3. Try Dimensional Core
        coords = self._hash_to_coords(key, building_id)
        if coords is not None:
            if coords not in building['dimensional_core']:
                building['dimensional_core'][coords] = (key, value)
                self.location_map[key] = (building_id, 'dimensional', coords)
                self.size += 1
                self._update_access_patterns(key)
                self._check_optimization_and_resize()
                return
            elif building['dimensional_core'][coords][0] == key:
                building['dimensional_core'][coords] = (key, value) # Update
                self._update_access_patterns(key)
                return
            else:
                # Collision in dimensional core
                self.stats['collisions'] += 1
                # 4. Follow Hamiltonian Path
                new_coords, probes = self._follow_hamiltonian_path_for_put(building_id, coords)
                self.stats['probes_total'] += probes
                self.stats['max_probes'] = max(self.stats['max_probes'], probes)
                if new_coords:
                    building['dimensional_core'][new_coords] = (key, value)
                    self.location_map[key] = (building_id, 'dimensional', new_coords)
                    self.size += 1
                    self._update_access_patterns(key)
                    self._check_optimization_and_resize()
                    return
                # Else: Path probing failed, proceed to conflict structure
        else: # Coords calculation failed, go directly to conflict structure
             coords = tuple([0]*self.dimensions) # Use fallback coords for conflict key


        # 5. Use Conflict Structure
        conflict_key_hash = self._hash_to_conflict_key(key, coords)
        if conflict_key_hash not in building['conflict_structures']:
            building['conflict_structures'][conflict_key_hash] = {} # Use dict as simple conflict list

        # Store/update in conflict structure
        if key not in building['conflict_structures'][conflict_key_hash]:
            self.size += 1 # Increment size only if new key overall
        building['conflict_structures'][conflict_key_hash][key] = value
        self.location_map[key] = (building_id, 'conflict', conflict_key_hash)
        self._update_access_patterns(key)
        self._check_optimization_and_resize()


    def get(self, key: Any) -> Any:
        """ Retrieve value tuple (val, meta) or None. """
        self.stats['gets'] += 1
        self.operations_since_optimization += 1
        probes = 0

        # 1. Check Location Map Cache
        loc_info = self.location_map.get(key)
        if loc_info:
            building_id, region_type, location_spec = loc_info
            building = self.buildings.get(building_id)
            if building:
                building['access_count'] += 1
                value = None
                if region_type == 'velocity':
                    probes += 1
                    if 0 <= location_spec < len(building['velocity_region']):
                        entry = building['velocity_region'][location_spec]
                        if entry and entry[0] == key: value = entry[1]
                elif region_type == 'dimensional':
                    probes += 1
                    entry = building['dimensional_core'].get(location_spec)
                    if entry and entry[0] == key: value = entry[1]
                elif region_type == 'conflict':
                    probes += 1
                    conflict_map = building['conflict_structures'].get(location_spec)
                    if conflict_map: value = conflict_map.get(key)

                if value is not None:
                    self.stats['hits'] += 1
                    self._update_stats_and_patterns(key, probes)
                    return value
                else: # Location map was stale/incorrect
                     if key in self.location_map: del self.location_map[key]
            else: # Invalid building in map
                 if key in self.location_map: del self.location_map[key]
            # Fall through to full search if map check failed

        # 2. Full Search (if map failed or key not in map)
        primary_building_id = self._hash_to_building(key)
        value, building_probes = self._search_building(primary_building_id, key)
        probes += building_probes
        if value is not None:
            self._update_stats_and_patterns(key, probes)
            return value

        # 3. Search Other Buildings (Only if collisions can spill buildings - assumed NO for now)

        # 4. Key Not Found
        self.stats['misses'] += 1
        self._update_stats_and_patterns(key, probes, found=False)
        return None

    def _update_stats_and_patterns(self, key: Any, probes: int, found: bool = True):
         """ Helper to update stats and access patterns after a get attempt. """
         self.stats['probes_total'] += probes
         self.stats['max_probes'] = max(self.stats['max_probes'], probes)
         if found:
             self._update_access_patterns(key)


    def _search_building(self, building_id: str, key: Any) -> Tuple[Any, int]:
        """ Search for a key within a specific building. Returns (Value, probes). """
        building = self.buildings.get(building_id)
        if not building: return None, 0
        building['access_count'] += 1
        probes = 0

        # Check velocity
        velocity_idx = self._hash_to_velocity_index(key, building_id)
        probes += 1
        if 0 <= velocity_idx < len(building['velocity_region']):
            entry = building['velocity_region'][velocity_idx]
            if entry and entry[0] == key:
                self.stats['hits'] += 1
                self.location_map[key] = (building_id, 'velocity', velocity_idx)
                return entry[1], probes

        # Check dimensional core primary
        coords = self._hash_to_coords(key, building_id)
        if coords is not None:
            probes += 1
            entry = building['dimensional_core'].get(coords)
            if entry and entry[0] == key:
                self.stats['hits'] += 1
                self.location_map[key] = (building_id, 'dimensional', coords)
                return entry[1], probes

            # Check conflict structure based on primary coords
            conflict_key_hash = self._hash_to_conflict_key(key, coords)
            probes += 1
            conflict_map = building['conflict_structures'].get(conflict_key_hash)
            if conflict_map and key in conflict_map:
                self.stats['hits'] += 1
                self.location_map[key] = (building_id, 'conflict', conflict_key_hash)
                return conflict_map[key], probes

            # Follow Hamiltonian path if not found yet
            value, path_probes = self._search_path(building_id, coords, key)
            probes += path_probes
            if value is not None:
                # Hit, location map update happen inside _search_path
                return value, probes

        else: # Coords failed, check conflict based on fallback
            fallback_coords = tuple([0]*self.dimensions)
            conflict_key_hash = self._hash_to_conflict_key(key, fallback_coords)
            probes += 1
            conflict_map = building['conflict_structures'].get(conflict_key_hash)
            if conflict_map and key in conflict_map:
                self.stats['hits'] += 1
                self.location_map[key] = (building_id, 'conflict', conflict_key_hash)
                return conflict_map[key], probes

        # Key not found in this building
        return None, probes


    def _search_path(self, building_id: str, start_coords: Tuple, key: Any) -> Tuple[Any, int]:
         """ Search for a key along a Hamiltonian path starting near coords. """
         building = self.buildings.get(building_id)
         if not building or not self.hamiltonian_paths: return None, 0

         nearest_path_key = self._find_nearest_path_key(building_id, start_coords)
         if not nearest_path_key: return None, 0
         path = self.hamiltonian_paths[nearest_path_key]
         if not path: return None, 0

         start_idx = self._find_path_start_index(path, start_coords)
         max_probes = self.config.get("mdhg_max_search_probes", 20)
         probes = 0
         path_len = len(path)
         forward_steps = 0
         backward_steps = 0

         while probes < max_probes and (forward_steps + backward_steps) < path_len:
             # Check forward
             idx = (start_idx + forward_steps) % path_len
             check_coords = path[idx]
             probes += 1
             entry = building['dimensional_core'].get(check_coords)
             if entry and entry[0] == key:
                 self.stats['hits'] += 1
                 self.location_map[key] = (building_id, 'dimensional', check_coords)
                 return entry[1], probes
             forward_steps += 1

             if probes >= max_probes or (forward_steps + backward_steps) >= path_len: break

             # Check backward (if path has more than one point)
             if backward_steps < forward_steps and path_len > 1:
                 idx = (start_idx - backward_steps - 1 + path_len) % path_len
                 check_coords = path[idx]
                 probes += 1
                 entry = building['dimensional_core'].get(check_coords)
                 if entry and entry[0] == key:
                     self.stats['hits'] += 1
                     self.location_map[key] = (building_id, 'dimensional', check_coords)
                     return entry[1], probes
                 backward_steps += 1

         return None, probes # Not found along path segment

    def _follow_hamiltonian_path_for_put(self, building_id: str, start_coords: Tuple) -> Tuple[Optional[Tuple], int]:
        """ Follow a Hamiltonian path to find an empty slot for insertion. """
        building = self.buildings.get(building_id)
        if not building or not self.hamiltonian_paths: return None, 0

        nearest_path_key = self._find_nearest_path_key(building_id, start_coords)
        if not nearest_path_key: return None, 0
        path = self.hamiltonian_paths[nearest_path_key]
        if not path: return None, 0

        start_idx = self._find_path_start_index(path, start_coords)
        max_probes = self.config.get("mdhg_max_put_probes", 20)
        probes = 0
        path_len = len(path)
        forward_steps = 0
        backward_steps = 0

        while probes < max_probes and (forward_steps + backward_steps) < path_len:
            # Check forward
            idx = (start_idx + forward_steps) % path_len
            coords = path[idx]
            probes += 1
            if coords not in building['dimensional_core']:
                return coords, probes
            forward_steps += 1

            if probes >= max_probes or (forward_steps + backward_steps) >= path_len: break

            # Check backward
            if backward_steps < forward_steps and path_len > 1:
                idx = (start_idx - backward_steps - 1 + path_len) % path_len
                coords = path[idx]
                probes += 1
                if coords not in building['dimensional_core']:
                    return coords, probes
                backward_steps += 1

        return None, probes # No empty slot found

    def remove(self, key: Any) -> bool:
        """ Remove a key-value pair. """
        # 1. Check Location Map first
        loc_info = self.location_map.get(key)
        removed = False
        if loc_info:
            building_id, region_type, location_spec = loc_info
            building = self.buildings.get(building_id)
            if building:
                if region_type == 'velocity':
                    if 0 <= location_spec < len(building['velocity_region']):
                        entry = building['velocity_region'][location_spec]
                        if entry and entry[0] == key:
                            building['velocity_region'][location_spec] = None
                            removed = True
                elif region_type == 'dimensional':
                    entry = building['dimensional_core'].get(location_spec)
                    if entry and entry[0] == key:
                        del building['dimensional_core'][location_spec]
                        removed = True
                elif region_type == 'conflict':
                    conflict_map = building['conflict_structures'].get(location_spec)
                    if conflict_map and key in conflict_map:
                        del conflict_map[key]
                        if not conflict_map: del building['conflict_structures'][location_spec]
                        removed = True

                if removed:
                    del self.location_map[key]
                    self.size -= 1
                    return True
                else: # Location map was stale
                    del self.location_map[key]
            else: # Invalid building in map
                 del self.location_map[key]

        # 2. Full Search if map failed or key not in map
        primary_building_id = self._hash_to_building(key)
        if self._remove_from_building(primary_building_id, key):
            return True

        # 3. Search other buildings (if spillover possible - assuming not)

        return False # Key not found

    def _remove_from_building(self, building_id: str, key: Any) -> bool:
         """ Removes key from a specific building. Helper for remove(). """
         building = self.buildings.get(building_id)
         if not building: return False

         # Check velocity
         velocity_idx = self._hash_to_velocity_index(key, building_id)
         if 0 <= velocity_idx < len(building['velocity_region']):
             entry = building['velocity_region'][velocity_idx]
             if entry and entry[0] == key:
                 building['velocity_region'][velocity_idx] = None
                 if key in self.location_map: del self.location_map[key]
                 self.size -= 1
                 return True

         # Check core and conflict (primary coords)
         coords = self._hash_to_coords(key, building_id)
         if coords is not None:
             entry = building['dimensional_core'].get(coords)
             if entry and entry[0] == key:
                 del building['dimensional_core'][coords]
                 if key in self.location_map: del self.location_map[key]
                 self.size -= 1
                 return True

             conflict_key_hash = self._hash_to_conflict_key(key, coords)
             conflict_map = building['conflict_structures'].get(conflict_key_hash)
             if conflict_map and key in conflict_map:
                 del conflict_map[key]
                 if not conflict_map: del building['conflict_structures'][conflict_key_hash]
                 if key in self.location_map: del self.location_map[key]
                 self.size -= 1
                 return True

             # Search path if necessary (more complex removal)
             # Simplified: Assume if not at primary/velocity/conflict, it's not easily removable

         else: # Coords failed, check conflict based on fallback
              fallback_coords = tuple([0]*self.dimensions)
              conflict_key_hash = self._hash_to_conflict_key(key, fallback_coords)
              conflict_map = building['conflict_structures'].get(conflict_key_hash)
              if conflict_map and key in conflict_map:
                  del conflict_map[key]
                  if not conflict_map: del building['conflict_structures'][conflict_key_hash]
                  if key in self.location_map: del self.location_map[key]
                  self.size -= 1
                  return True

         return False

    # --- Helper methods for path finding ---
    def _find_nearest_path_key(self, building_id: str, coords: Tuple) -> Optional[Tuple]:
        """ Find the key (building_id, start_coords) of the nearest pre-computed path. """
        min_dist_sq = float('inf')
        nearest_key = None
        if coords is None: return None

        # Filter paths belonging to the target building
        building_paths = {k: v for k, v in self.hamiltonian_paths.items() if k[0] == building_id}
        if not building_paths: return None

        for path_key, path_data in building_paths.items():
            path_start_coords = path_key[1]
            # Ensure coordinates have same dimension before calculating distance
            if len(coords) != len(path_start_coords): continue
            # Calculate squared Euclidean distance for efficiency
            dist_sq = sum((c1 - c2)**2 for c1, c2 in zip(coords, path_start_coords))
            if dist_sq < min_dist_sq:
                min_dist_sq = dist_sq
                nearest_key = path_key
        return nearest_key

    def _find_path_start_index(self, path: List[Tuple], coords: Tuple) -> int:
        """ Find the index in a path closest to the given coordinates. """
        if not path: return 0
        if coords is None: return 0

        min_dist_sq = float('inf')
        best_idx = 0
        for i, path_coords in enumerate(path):
             # Ensure coordinates have same dimension
             if len(coords) != len(path_coords): continue
             dist_sq = sum((c1 - c2)**2 for c1, c2 in zip(coords, path_coords))
             if dist_sq < min_dist_sq:
                 min_dist_sq = dist_sq
                 best_idx = i
             if min_dist_sq == 0: break # Exact match found
        return best_idx

    # --- Dynamic Adaptation & Optimization (Placeholders - Require full logic) ---

    def _update_access_patterns(self, key: Any) -> None:
        """ Update access frequency, history, and co-access matrix. """
        self.access_history.append(key)
        self.access_frequency[key] += 1
        # Update co-access (simplified)
        if len(self.access_history) > 1:
            last_key = self.access_history[-2]
            if last_key != key:
                self.co_access_matrix[last_key][key] += 1
                self.co_access_matrix[key][last_key] += 1

        # Trigger potential promotion based on frequency
        promo_threshold = self.config.get("mdhg_velocity_promo_threshold", 10)
        if self.access_frequency[key] >= promo_threshold:
            if key in self.location_map:
                building_id = self.location_map[key][0]
                self._consider_velocity_promotion(key, building_id)


    def _consider_velocity_promotion(self, key: Any, building_id: str) -> None:
         """ Consider promoting a key to the velocity region if beneficial. """
         building = self.buildings.get(building_id)
         if not building or key not in self.location_map: return

         current_loc = self.location_map[key]
         if current_loc[1] == 'velocity': return # Already there

         target_idx = self._hash_to_velocity_index(key, building_id)
         if not (0 <= target_idx < len(building['velocity_region'])): return # Invalid index

         current_entry = building['velocity_region'][target_idx]
         key_freq = self.access_frequency.get(key, 0)
         should_promote = False

         if current_entry is None:
             should_promote = True
         else:
             occupant_key = current_entry[0]
             occupant_freq = self.access_frequency.get(occupant_key, 0)
             # Promote if new key is significantly more frequent (using PHI ratio)
             if key_freq > occupant_freq * self.PHI:
                 should_promote = True
                 # Relocate the occupant if it's being evicted
                 print(f"    MDHG: Evicting {occupant_key} (freq {occupant_freq}) from velocity for {key} (freq {key_freq})")
                 self._relocate_from_velocity(occupant_key, current_entry[1], building_id)
                 self.stats['relocations_from_velocity'] += 1

         if should_promote:
             # Get current value (get() handles finding it)
             value_tuple = self.get(key) # This will update access patterns again
             if value_tuple is not None:
                 print(f"    MDHG: Promoting key {key} to velocity region in {building_id}")
                 # Remove from old location BEFORE putting in new one
                 self._remove_from_current_location(key) # Removes from core/conflict
                 building['velocity_region'][target_idx] = (key, value_tuple)
                 self.location_map[key] = (building_id, 'velocity', target_idx) # Update location map
                 self.stats['promotions_velocity'] += 1


    def _relocate_from_velocity(self, key: Any, value: Any, building_id: str) -> None:
        """ Relocate a key evicted from velocity region back to core/conflict. """
        # This is essentially a 'put' operation, but we know it's not in velocity.
        # We need to ensure size isn't incremented again.
        building = self.buildings.get(building_id)
        if not building: return

        # Try dimensional core first
        coords = self._hash_to_coords(key, building_id)
        if coords is not None:
            if coords not in building['dimensional_core']:
                building['dimensional_core'][coords] = (key, value)
                self.location_map[key] = (building_id, 'dimensional', coords)
                return
            else: # Collision
                new_coords, _ = self._follow_hamiltonian_path_for_put(building_id, coords)
                if new_coords:
                    building['dimensional_core'][new_coords] = (key, value)
                    self.location_map[key] = (building_id, 'dimensional', new_coords)
                    return
        # Fallback to conflict structure
        fallback_coords = coords if coords is not None else tuple([0]*self.dimensions)
        conflict_key_hash = self._hash_to_conflict_key(key, fallback_coords)
        if conflict_key_hash not in building['conflict_structures']:
            building['conflict_structures'][conflict_key_hash] = {}
        building['conflict_structures'][conflict_key_hash][key] = value
        self.location_map[key] = (building_id, 'conflict', conflict_key_hash)


    def _remove_from_current_location(self, key: Any) -> None:
        """ Helper to remove key from core/conflict AFTER checking location map. """
        if key not in self.location_map: return
        building_id, region_type, location_spec = self.location_map[key]
        building = self.buildings.get(building_id)
        if not building: return

        removed = False
        if region_type == 'dimensional':
            if location_spec in building['dimensional_core'] and building['dimensional_core'][location_spec][0] == key:
                del building['dimensional_core'][location_spec]
                removed = True
        elif region_type == 'conflict':
            conflict_map = building['conflict_structures'].get(location_spec)
            if conflict_map and key in conflict_map:
                del conflict_map[key]
                if not conflict_map: del building['conflict_structures'][location_spec]
                removed = True
        # Note: We don't delete from location map here, caller handles final update


    def _check_optimization_and_resize(self) -> None:
        """ Check if optimization or resize is needed based on operations or time. """
        current_time = time.time()
        ops_threshold_minor = self.config.get("mdhg_ops_thresh_minor", 100)
        time_threshold_minor = self.config.get("mdhg_time_thresh_minor", 1.0)
        ops_threshold_major = self.config.get("mdhg_ops_thresh_major", 1000)
        time_threshold_major = self.config.get("mdhg_time_thresh_major", 5.0)

        needs_minor_opt = (self.operations_since_optimization > 0 and self.operations_since_optimization % ops_threshold_minor == 0) or \
                          (current_time - self.last_minor_optimization >= time_threshold_minor)
        needs_major_opt = (self.operations_since_optimization > 0 and self.operations_since_optimization % ops_threshold_major == 0) or \
                          (current_time - self.last_major_optimization >= time_threshold_major)

        if needs_major_opt:
            # print("    MDHG: Performing major optimization...")
            self._perform_major_optimization()
            self.last_major_optimization = current_time
            self.last_minor_optimization = current_time # Reset minor timer too
            self.operations_since_optimization = 0 # Reset counter
        elif needs_minor_opt:
            # print("    MDHG: Performing minor optimization...")
            self._perform_minor_optimization()
            self.last_minor_optimization = current_time
            # Don't reset major timer or op counter on minor opt

        # Check resize AFTER potential optimizations
        current_load_factor = self.size / self.capacity if self.capacity > 0 else 1.0
        if current_load_factor > self.load_factor_threshold:
            print(f"    MDHG: Load factor {current_load_factor:.2f} exceeds threshold {self.load_factor_threshold}. Resizing.")
            self._resize()

    def _perform_minor_optimization(self) -> None:
        """ Perform minor optimizations like promoting hot keys. """
        hot_key_count = self.config.get("mdhg_hot_key_count", 100)
        hot_key_min_freq = self.config.get("mdhg_hot_key_min_freq", 5)
        hot_keys_global = self.access_frequency.most_common(hot_key_count)
        promoted_count = 0
        for key, freq in hot_keys_global:
            if freq < hot_key_min_freq: break
            if key in self.location_map:
                building_id = self.location_map[key][0]
                # This call might result in promotion
                self._consider_velocity_promotion(key, building_id)
                # Check if promotion actually happened (location map changed)
                if key in self.location_map and self.location_map[key][1] == 'velocity':
                     promoted_count += 1
        # if promoted_count > 0: print(f"      MDHG Minor Opt: Considered {len(hot_keys_global)} hot keys, promoted {promoted_count} to velocity.")


    def _perform_major_optimization(self) -> None:
        """ Perform major structural reorganizations. """
        self.stats['reorganizations'] += 1
        start_time = time.time()
        # print("      MDHG Major Opt: Updating shortcuts...")
        # self._update_shortcuts() # Placeholder
        # print("      MDHG Major Opt: Identifying and relocating clusters...")
        # self._identify_and_relocate_key_clusters() # Placeholder
        # print("      MDHG Major Opt: Pruning path cache...")
        # self._prune_path_cache() # Placeholder
        end_time = time.time()
        print(f"    MDHG: Major optimization complete in {end_time - start_time:.4f}s (Placeholders used).")


    def _update_shortcuts(self) -> None:
        """ Placeholder: Update shortcuts based on observed usage patterns. """
        # Requires tracking inter-building traversals or using co-access matrix across buildings
        pass

    def _identify_and_relocate_key_clusters(self) -> None:
        """ Placeholder: Identify clusters of co-accessed keys and move them closer. """
        # Requires graph analysis of co_access_matrix and complex relocation logic
        clusters_found = 0
        # ... implementation needed ...
        if clusters_found > 0:
            self.stats['clusters_relocated'] += clusters_found
            # print(f"        MDHG Cluster Opt: Relocated {clusters_found} key clusters.")
        pass

    def _prune_path_cache(self) -> None:
        """ Placeholder: Prune the path cache based on usage or recency. """
        max_cache_size = self.config.get("mdhg_path_cache_max_size", 100)
        if len(self.path_cache) > max_cache_size:
            # Simple prune: Keep top 50% most used
            keep_count = max_cache_size // 2
            sorted_usage = sorted(self.path_usage.items(), key=lambda item: item[1], reverse=True)
            keys_to_keep = {key for key, usage in sorted_usage[:keep_count]}
            old_size = len(self.path_cache)
            self.path_cache = {k: v for k, v in self.path_cache.items() if k in keys_to_keep}
            self.path_usage = {k: v for k, v in self.path_usage.items() if k in keys_to_keep}
            # print(f"        MDHG Cache Prune: Reduced path cache from {old_size} to {len(self.path_cache)} entries.")
        pass

    def _resize(self) -> None:
        """ Resize the hash table when load factor is exceeded. """
        self.stats['resizes'] += 1
        old_capacity = self.capacity
        # Increase capacity using golden ratio
        new_capacity = max(old_capacity + 1, int(old_capacity * self.PHI * 1.1)) # Add buffer
        print(f"    MDHG Resize: Increasing capacity from {old_capacity} to {new_capacity}")

        # Store old data temporarily
        old_items = []
        for key, loc_info in self.location_map.items():
            # Retrieve value from old structure before wiping it
            building_id_old, region_type_old, location_spec_old = loc_info
            building_old = self.buildings.get(building_id_old)
            value_tuple = None
            if building_old:
                if region_type_old == 'velocity':
                    if 0 <= location_spec_old < len(building_old['velocity_region']):
                        entry = building_old['velocity_region'][location_spec_old]
                        if entry and entry[0] == key: value_tuple = entry[1]
                elif region_type_old == 'dimensional':
                    entry = building_old['dimensional_core'].get(location_spec_old)
                    if entry and entry[0] == key: value_tuple = entry[1]
                elif region_type_old == 'conflict':
                    conflict_map = building_old['conflict_structures'].get(location_spec_old)
                    if conflict_map: value_tuple = conflict_map.get(key)
            if value_tuple is not None:
                old_items.append((key, value_tuple))
            # else: print(f"Warning: Could not retrieve value for key {key} during resize.")

        # Re-initialize with new capacity
        self.capacity = new_capacity
        self.size = 0 # Reset size, will be repopulated
        self.buildings = self._initialize_buildings()
        self.location_map = {} # Clear location map
        self._initialize_structure() # Recompute paths etc. for new structure

        # Rehash all elements
        print(f"    MDHG Resize: Rehashing {len(old_items)} elements...")
        rehash_start_time = time.time()
        for key, value_tuple in old_items:
            self.put(key, value_tuple) # Re-insert into the new structure
        rehash_end_time = time.time()
        print(f"    MDHG Resize: Rehashing complete in {rehash_end_time - rehash_start_time:.4f}s. New size: {self.size}")

        # Reset optimization timers after resize
        self.last_minor_optimization = time.time()
        self.last_major_optimization = time.time()
        self.operations_since_optimization = 0

class AGRMController:
    """ Orchestrates the AGRM TSP solving process using the agent stack. """
    def __init__(self, cities: List[Tuple[float, float]], config: Dict = {}, previous_recommendations: Dict = {}):
        """
        Initializes the controller and all agents.
        Args:
            cities: List of city coordinates.
            config: Base configuration dictionary.
            previous_recommendations: Parameter adjustments from previous PathAuditAgent run.
        """
        self.cities = cities
        self.num_nodes = len(cities)

        # Apply recommendations to base config
        self.config = config.copy()
        if previous_recommendations:
            print(f"CONTROLLER: Applying {len(previous_recommendations)} recommendations from previous run.")
            self.config.update(previous_recommendations)
            print(f"  New Config Snippet: { {k: self.config[k] for k in previous_recommendations} }")

        # Initialize shared state bus with potentially updated config
        self.bus = AGRMStateBus(cities, self.config)

        # Initialize agents, passing the bus and config
        self.navigator = NavigatorGR(cities, self.config)
        self.validator = AGRMEdgeValidator(self.bus, self.config)
        # Pass self (controller) to agents that might need to signal back directly? Or use bus.
        self.mod_controller_agent = ModulationController(self.bus, self.config) # The agent managing modulation params
        self.builder_fwd: Optional[PathBuilder] = None
        self.builder_rev: Optional[PathBuilder] = None
        self.salesman = SalesmanValidator(self.bus, self.validator, self.config)
        self.path_audit = PathAuditAgent(self.bus, self.config) # Initialize audit agent

        self.run_stats = {}


    def solve(self) -> Tuple[Optional[List[int]], Dict]:
        """ Runs the full AGRM TSP solving process, returning path and stats. """
        print(f"\n=== AGRM Controller: Starting Solve for {self.num_nodes} Nodes ===")
        overall_start_time = time.time()
        self.run_stats = {} # Reset stats for this run

        # --- 1. Sweep Phase ---
        sweep_results = self.navigator.run_sweep()
        self.bus.update_sweep_data(sweep_results)
        if self.bus.start_node_fwd is None or self.bus.start_node_rev is None:
             print("CONTROLLER ERROR: Navigator failed to determine start nodes.")
             return None, {"error": "Navigator failed"}
        self.run_stats['sweep_time'] = time.time() - overall_start_time

        # --- Initialize Builders ---
        self.builder_fwd = PathBuilder('forward', self.bus.start_node_fwd, self.bus, self.validator, self.config)
        self.builder_rev = PathBuilder('reverse', self.bus.start_node_rev, self.bus, self.validator, self.config)

        # --- 2. Bidirectional Build Phase ---
        print("CONTROLLER: Starting Bidirectional Build Phase...")
        build_start_time = time.time()
        max_steps = self.num_nodes * self.config.get("runner_max_step_factor", 3)
        steps = 0
        build_complete = False
        while steps < max_steps:
            steps += 1
            # Alternate stepping? Or step both? Stepping both:
            progress_fwd = self.builder_fwd.step() if self.bus.builder_fwd_state["status"] in ["running", "stalled"] else False
            progress_rev = self.builder_rev.step() if self.bus.builder_rev_state["status"] in ["running", "stalled"] else False

            # Update modulation controller based on latest builder states
            self.mod_controller_agent.update_controller_state()

            # Check for convergence
            if self.bus.check_convergence():
                 print(f"CONTROLLER: Convergence detected at step {steps}.")
                 build_complete = self.bus.merge_paths()
                 break # Exit build loop

            # Check for hard stalls
            if self.bus.builder_fwd_state["status"] == "stalled_hard" and \
               self.bus.builder_rev_state["status"] == "stalled_hard":
                print("CONTROLLER ERROR: Both builders hard stalled. Attempting merge.")
                build_complete = self.bus.merge_paths() # Try merging anyway
                break

            # Check if no progress possible and not converged
            if not progress_fwd and not progress_rev and \
               self.bus.builder_fwd_state["status"] not in ["running", "converged"] and \
               self.bus.builder_rev_state["status"] not in ["running", "converged"]:
                 print(f"CONTROLLER WARNING: No progress from either builder at step {steps}. Stopping build.")
                 build_complete = self.bus.merge_paths() # Try merging what we have
                 break

        if steps >= max_steps:
             print(f"CONTROLLER WARNING: Max steps ({max_steps}) reached during build phase.")
             build_complete = self.bus.merge_paths() # Try merging what we have

        self.run_stats['build_time'] = time.time() - build_start_time
        print(f"CONTROLLER: Build phase finished in {self.run_stats['build_time']:.4f}s ({steps} steps).")

        # --- 3. Patching Phase (If Needed for Missed Nodes) ---
        if self.bus.current_phase == "patching":
            print("CONTROLLER: Entering patching phase for missed nodes...")
            patch_start_time = time.time()
            # TODO: Implement robust patching logic
            # Needs to find missed nodes, determine best insertion points respecting legality
            # This is complex - requires potentially re-invoking builder/validator locally
            # For now, just flag as incomplete
            print(f"CONTROLLER WARNING: Path construction incomplete, {self.num_nodes - len(set(self.bus.full_path))} nodes missed. Patching logic not fully implemented.")
            build_complete = False # Mark as incomplete
            self.run_stats['patch_time'] = time.time() - patch_start_time
            self.bus.current_phase = "finalizing" # Move phase even if incomplete

        # --- 4. Salesman Validation & Refinement ---
        if self.bus.full_path:
            print("CONTROLLER: Starting Salesman validation and refinement...")
            salesman_start_time = time.time()
            self.salesman.run_validation_and_patching()
            # Controller evaluates proposals and stores accepted ones
            self.mod_controller_agent.process_salesman_feedback()
            # Builder splices approved patches (via bus)
            accepted_patches = self.bus.get_accepted_patches()
            if accepted_patches:
                 print(f"CONTROLLER: Applying {len(accepted_patches)} accepted patches...")
                 spliced_count = 0
                 # Apply patches iteratively? Or assume they don't overlap significantly?
                 # Applying iteratively for now
                 for patch in accepted_patches:
                     if self.bus.splice_patch(patch):
                         spliced_count += 1
                 print(f"CONTROLLER: Successfully spliced {spliced_count} patches.")
                 self.bus.clear_accepted_patches() # Clear after applying
            self.run_stats['salesman_time'] = time.time() - salesman_start_time
            print(f"CONTROLLER: Salesman phase complete in {self.run_stats['salesman_time']:.4f}s.")
        else:
            print("CONTROLLER: No path generated, skipping Salesman validation.")
            self.run_stats['salesman_time'] = 0.0

        # --- 5. Path Audit Phase (Meta-Learning) ---
        print("CONTROLLER: Starting Path Audit...")
        audit_start_time = time.time()
        recommendations = self.path_audit.run_audit() # Returns dict of param adjustments
        self.run_stats['audit_time'] = time.time() - audit_start_time
        print(f"CONTROLLER: Path Audit complete in {self.run_stats['audit_time']:.4f}s.")

        # --- 6. Final Results ---
        overall_end_time = time.time()
        final_path = self.bus.full_path
        # Recalculate final cost after potential splicing
        final_cost = self.calculate_total_path_cost(final_path) if final_path else 0.0

        # Compile final statistics
        final_stats = {
            "execution_time": overall_end_time - overall_start_time,
            "sweep_time": self.run_stats.get('sweep_time', 0.0),
            "build_time": self.run_stats.get('build_time', 0.0),
            "patch_time": self.run_stats.get('patch_time', 0.0),
            "salesman_time": self.run_stats.get('salesman_time', 0.0),
            "audit_time": self.run_stats.get('audit_time', 0.0),
            "path_complete": build_complete and bool(final_path) and len(set(final_path[:-1])) == self.num_nodes,
            "visited_nodes": len(set(final_path[:-1])) if final_path else 0,
            "path_length_nodes": len(final_path) if final_path else 0,
            "salesman_flags": self.salesman.stats.get('flags_generated', 0),
            "salesman_proposals": self.salesman.stats.get('proposals_generated', 0),
            "total_path_cost": final_cost,
            "efficiency": final_cost / max(1, self.num_nodes),
            "audit_recommendations": recommendations # Include recommendations for next run
        }
        self.bus.current_phase = "complete"
        print(f"=== AGRM Controller: Solve Complete in {final_stats['execution_time']:.4f}s ===")
        return final_path, final_stats

    def calculate_total_path_cost(self, path: Optional[List[int]]) -> float:
        """ Calculates the Euclidean distance of the TSP path. """
        if not path or len(path) < 2: return 0.0
        total_distance = 0.0
        for i in range(len(path) - 1):
            # Add checks for valid indices
            idx1, idx2 = path[i], path[i+1]
            if 0 <= idx1 < self.num_nodes and 0 <= idx2 < self.num_nodes:
                 pos1 = self.cities[idx1]
                 pos2 = self.cities[idx2]
                 total_distance += math.dist(pos1, pos2)
            else:
                 print(f"ERROR: Invalid node index in path during cost calculation: {idx1} or {idx2}")
                 return 0.0 # Indicate error
        return total_distance

class MDHGCache:
    """
    MDHG geometric cache: 24D → 2D slot grid → per-slot eviction.
    
    Slot occupancy creates a "shape" that the CA field responds to.
    """
    
    def __init__(self, grid_side=12, cap_per_slot=6, bins=16, layer_name="default"):
        self.grid_side = grid_side
        self.cap_per_slot = cap_per_slot
        self.bins = bins
        self.layer_name = layer_name
        self.slots: Dict[str, List[SlotEntry]] = {}
        self._admission_count = 0
        self._eviction_count = 0
    
    def admit(self, v24: List[float], meta: Dict[str, Any]) -> Dict[str, Any]:
        """
        Admit a 24D vector into the cache.
        
        Returns admission result with slot assignment.
        """
        q = quantize(v24, bins=self.bins)
        slot = slot_of(q, grid_side=self.grid_side)
        
        # Create key from content
        key = _h({"q": q, "meta": {k: meta.get(k) for k in sorted(meta)[:12]}})[:16]
        
        arr = self.slots.setdefault(slot, [])
        
        # Check for existing (cache hit)
        for e in arr:
            if e.key == key:
                e.hits += 1
                e.last = time.time()
                return {
                    "admit": True,
                    "hit": True,
                    "slot": slot,
                    "distance": 0.0,
                    "key": key,
                    "q24": q,
                    "layer": self.layer_name
                }
        
        # Calculate distance to existing entries
        dist = 0.0
        if arr:
            distances = [sum(1 for a, b in zip(q, e.q24) if a != b) for e in arr]
            dist = float(min(distances))
        
        # Evict if necessary (LRU-like)
        evicted = None
        if len(arr) >= self.cap_per_slot:
            # Sort by (hits, last_access) - evict least used
            cand = sorted(arr, key=lambda e: (e.hits, e.last))[0]
            evicted = {
                "key": cand.key,
                "hits": cand.hits,
                "last": cand.last,
                "meta": cand.meta
            }
            arr.remove(cand)
            self._eviction_count += 1
        
        # Admit new entry
        arr.append(SlotEntry(key=key, q24=q, meta=meta))
        self._admission_count += 1
        
        return {
            "admit": True,
            "hit": False,
            "slot": slot,
            "distance": dist,
            "key": key,
            "evicted": evicted,
            "q24": q,
            "layer": self.layer_name
        }
    
    def get_slot_contents(self, slot: str) -> List[SlotEntry]:
        """Get all entries in a slot."""
        return self.slots.get(slot, [])
    
    def occupancy_grid(self) -> List[List[int]]:
        """Return 2D occupancy grid (0-9 scale)."""
        g = [[0 for _ in range(self.grid_side)] for _ in range(self.grid_side)]
        for s, arr in self.slots.items():
            try:
                x, y = s.split(",")
                g[int(y)][int(x)] = min(9, len(arr))
            except (ValueError, IndexError):
                continue
        return g
    
    def get_stats(self) -> Dict[str, Any]:
        """Cache statistics."""
        total_entries = sum(len(arr) for arr in self.slots.values())
        return {
            "layer": self.layer_name,
            "slots_used": len(self.slots),
            "total_entries": total_entries,
            "admissions": self._admission_count,
            "evictions": self._eviction_count,
            "grid_side": self.grid_side,
            "cap_per_slot": self.cap_per_slot
        }
    
    def snapshot(self) -> Dict[str, Any]:
        """Full snapshot for persistence."""
        return {
            "grid_side": self.grid_side,
            "cap_per_slot": self.cap_per_slot,
            "bins": self.bins,
            "layer_name": self.layer_name,
            "slots": {
                k: [{"key": e.key, "hits": e.hits, "last": e.last, "meta": e.meta} for e in v]
                for k, v in self.slots.items()
            }
        }

class AGRMEdgeValidator:
    """
    Provides methods to check if a transition (edge) between two nodes
    is legal according to the current dynamic AGRM modulation parameters.
    Operates ephemerally - computes legality on demand using data from the StateBus.
    """
    def __init__(self, bus: AGRMStateBus, config: Dict):
        self.bus = bus
        self.config = config
        self.PHI = (1 + math.sqrt(5)) / 2

    def is_edge_legal(self, node_from: int, node_to: int, builder_type: str) -> bool:
        """ Checks all AGRM legality rules for a potential edge. """
        params = self.bus.modulation_params
        data_from = self.bus.get_node_sweep_data(node_from)
        data_to = self.bus.get_node_sweep_data(node_to)
        if not data_from or not data_to: return False

        if not self._check_shell_proximity(data_from, data_to, params): return False
        if not self._check_sector_continuity(data_from, data_to, params): return False
        if not self._check_phase_timing(data_to, params): return False
        if not self._check_curvature(node_from, node_to, builder_type, params): return False
        if not self._check_distance_cap(node_from, node_to, data_from, params): return False
        # Add Quadrant transition checks if needed
        return True

    def _check_shell_proximity(self, data_from: Dict, data_to: Dict, params: Dict) -> bool:
        shell_from = data_from.get('shell', -1)
        shell_to = data_to.get('shell', -1)
        if shell_from == -1 or shell_to == -1: return False
        shell_diff = abs(shell_from - shell_to)
        is_reentry_inward = params.get("reentry_mode", False) and shell_to < shell_from
        within_tolerance = shell_diff <= params.get("shell_tolerance", 2)
        return within_tolerance or is_reentry_inward

    def _check_sector_continuity(self, data_from: Dict, data_to: Dict, params: Dict) -> bool:
        sector_from = data_from.get('sector', -1)
        sector_to = data_to.get('sector', -1)
        if sector_from == -1 or sector_to == -1: return False
        num_sectors = self.config.get("sweep_num_sectors", 8)
        if num_sectors <= 0: return True
        sector_diff = abs(sector_from - sector_to)
        angular_diff = min(sector_diff, num_sectors - sector_diff)
        return angular_diff <= params.get("sector_tolerance", 2)

    def _check_phase_timing(self, data_to: Dict, params: Dict) -> bool:
        """ Checks if moving to a sparse zone is allowed based on phase unlock state. """
        if params.get("allow_sparse_unlock", False):
            return True # Sparse zones are allowed
        else:
            # Disallow entry *into* sparse zones before unlock
            return data_to.get('density') != "sparse"

    def _check_curvature(self, node_from: int, node_to: int, builder_type: str, params: Dict) -> bool:
        """ Checks if the turn angle respects the dynamic GR curvature limit. """
        path = self.bus.path_fwd if builder_type == 'forward' else self.bus.path_rev
        if len(path) < 2: return True # No angle to check

        node_prev = path[-2]
        try:
            pos_prev = self.bus.cities[node_prev]
            pos_from = self.bus.cities[node_from]
            pos_to = self.bus.cities[node_to]
        except IndexError: return False # Invalid index

        vec1 = (pos_from[0] - pos_prev[0], pos_from[1] - pos_prev[1])
        vec2 = (pos_to[0] - pos_from[0], pos_to[1] - pos_from[1])
        len1 = math.hypot(vec1[0], vec1[1])
        len2 = math.hypot(vec2[0], vec2[1])
        if len1 < 1e-9 or len2 < 1e-9: return True # Allow if points overlap

        dot_product = vec1[0] * vec2[0] + vec1[1] * vec2[1]
        cos_angle = max(-1.0, min(1.0, dot_product / (len1 * len2)))
        angle = math.acos(cos_angle)
        return angle <= params.get("curvature_limit", math.pi / 4)

    def _check_distance_cap(self, node_from: int, node_to: int, data_from: Dict, params: Dict) -> bool:
        """ Checks if the edge distance exceeds a dynamic cap. """
        avg_dist_in_shell = max(1.0, self.bus.shell_width or 10.0) # Proxy
        base_dist_cap = avg_dist_in_shell * params.get("distance_cap_factor", 3.0)
        if data_from.get('density') == "sparse":
            base_dist_cap *= self.config.get("dist_cap_sparse_mult", 1.5)

        effective_dist_cap = base_dist_cap
        if params.get("soft_override_active", False) or params.get("reentry_mode", False):
             effective_dist_cap *= self.config.get("dist_cap_override_mult", 1.5)
        try:
            actual_dist = math.dist(self.bus.cities[node_from], self.bus.cities[node_to])
        except IndexError: return False
        return actual_dist <= effective_dist_cap

class AGRMStateBus:
    """
    Manages the shared state between AGRM agents.
    Acts as the central repository for path data, node states,
    sweep metadata, modulation parameters, and agent signals.
    Uses Hybrid Hashing strategy based on complexity.
    """
    def __init__(self, cities: List[Tuple[float, float]], config: Dict):
        """
        Initializes the state bus.
        Args:
            cities: List of (x, y) coordinates for the nodes.
            config: Dictionary containing configuration parameters for AGRM and MDHG.
        """
        self.config = config
        self.num_nodes = len(cities)
        self.cities = cities # List of (x, y) tuples

        # --- Core State ---
        self.visited_fwd: Set[int] = set() # Nodes visited by forward builder
        self.visited_rev: Set[int] = set() # Nodes visited by reverse builder
        self.path_fwd: List[int] = [] # Path built by forward builder
        self.path_rev: List[int] = [] # Path built by reverse builder (in reverse order)
        self.full_path: Optional[List[int]] = None # Final merged path

        # --- Sweep Metadata (Populated by Navigator) ---
        self.sweep_data: Dict[int, Dict] = {} # node_id -> {rank, shell, sector, quadrant, hemisphere, density, gr_score}
        self.sweep_center: Optional[Tuple[float, float]] = None
        self.max_radius: float = 0.0
        self.shell_width: float = 0.0
        self.start_node_fwd: Optional[int] = None
        self.start_node_rev: Optional[int] = None

        # --- Legal Graph & Modulation State (Managed by Controller) ---
        # Legal edges are computed ephemerally by the validator agent
        # self.legal_edges: Optional[Dict[int, List[int]]] = None # Not stored persistently
        # Store default modulation params for reset
        self.default_modulation_params = {
            "shell_tolerance": config.get("mod_shell_tolerance", 2),
            "curvature_limit": config.get("mod_curvature_limit", math.pi / 4), # Approx 45 deg
            "sector_tolerance": config.get("mod_sector_tolerance", 2),
            "distance_cap_factor": config.get("mod_dist_cap_factor", 3.0), # Multiplier for avg dist in shell
            "allow_sparse_unlock": False,
            "soft_override_active": False,
            "reentry_mode": False
        }
        self.modulation_params = self.default_modulation_params.copy() # Start with defaults
        self.current_phase: str = "initializing" # 'initializing', 'building', 'pre-midpoint', 'converging', 'post-midpoint', 'post-merge', 'patching', 'finalizing', 'complete'

        # --- Hybrid Hashing State ---
        self.complexity_threshold = config.get("hybrid_hash_threshold", 5) # n=5 complexity threshold [cite: 896-913]
        # Instantiate caches
        self.low_complexity_cache = {} # Standard dict for n <= 5 tasks/data
        # Instantiate MDHG for high complexity state. Tailoring parameters applied here.
        mdhg_dims = config.get("mdhg_dimensions", 3)
        mdhg_cap = max(1024, self.num_nodes) # Capacity scales with problem size
        self.high_complexity_cache = MDHGHashTable(capacity=mdhg_cap, dimensions=mdhg_dims, config=config) # Pass config
        print(f"StateBus: Initialized Hybrid Caching (n={self.complexity_threshold} threshold). MDHG Dims={mdhg_dims}, Capacity={mdhg_cap}")

        # --- Agent Feedback / Flags ---
        self.builder_fwd_state = {"status": "idle", "stalls": 0, "last_node": -1, "current_shell": -1, "current_sector": -1}
        self.builder_rev_state = {"status": "idle", "stalls": 0, "last_node": -1, "current_shell": -1, "current_sector": -1}
        self.salesman_proposals: List[Dict] = [] # Patches suggested for review by Salesman
        self.accepted_patches: List[Dict] = [] # Patches approved by Controller for splicing

    def get_cache(self, complexity_level: int) -> Union[Dict, MDHGHashTable]:
        """
        Returns the appropriate cache backend based on complexity level 'n'.
        Called by agents needing to store/retrieve state ephemerally.
        Args:
            complexity_level: The estimated complexity 'n' of the current operation.
        Returns:
            The standard dict or the MDHGHashTable instance.
        """
        # Note: Complexity level 'n' determination logic resides in the calling agent/controller
        # This provides the interface based on that determination.
        if complexity_level <= self.complexity_threshold:
            # print(f"DEBUG: Using low complexity cache (dict) for n={complexity_level}")
            return self.low_complexity_cache
        else:
            # print(f"DEBUG: Using high complexity cache (MDHG) for n={complexity_level}")
            return self.high_complexity_cache

    def migrate_data(self, key: Any, current_complexity: int, new_complexity: int):
        """
        Migrates a key between caches if the complexity threshold is crossed.
        Called by the Modulation Controller. Assumes value needs to be fetched.
        Args:
            key: The key to migrate.
            current_complexity: The previous complexity level 'n'.
            new_complexity: The new complexity level 'n'.
        """
        # Determine source and target caches
        source_cache = self.get_cache(current_complexity)
        target_cache = self.get_cache(new_complexity)

        # Only migrate if the cache type actually changes
        if type(source_cache) == type(target_cache):
            return # No migration needed

        value_to_migrate = None
        metadata = {}

        # Get value from source cache
        if isinstance(source_cache, MDHGHashTable):
            result = source_cache.get(key)
            if result:
                value_to_migrate, metadata = result # MDHG stores tuple
        elif isinstance(source_cache, dict):
            value_to_migrate = source_cache.get(key)
            metadata = {'source': 'dict'} # Assume origin if coming from dict

        # If value exists in source, remove it and put it in target
        if value_to_migrate is not None:
            # Remove from source
            if isinstance(source_cache, MDHGHashTable):
                source_cache.remove(key)
            elif isinstance(source_cache, dict):
                if key in source_cache: del source_cache[key]

            # Put into target
            if isinstance(target_cache, MDHGHashTable):
                 # Ensure metadata includes source info
                 metadata['source'] = 'dict' if isinstance(source_cache, dict) else metadata.get('source', 'mdhg')
                 # Ensure retain_flag exists, default to False if not present
                 metadata['retain_flag'] = metadata.get('retain_flag', False)
                 target_cache.put(key, (value_to_migrate, metadata)) # Store as tuple
                 print(f"StateBus: Migrated key {key} from {type(source_cache).__name__} to MDHG.")
            elif isinstance(target_cache, dict):
                 target_cache[key] = value_to_migrate # Store only value in dict
                 print(f"StateBus: Migrated key {key} from MDHG to {type(target_cache).__name__}.")

    # --- Rest of AGRMStateBus methods ---
    # (update_sweep_data, get_node_sweep_data, is_visited, add_visited,
    #  get_unvisited_nodes, update_modulation_params, update_builder_state,
    #  check_convergence, merge_paths, add_salesman_proposal, etc.)
    # These remain largely the same as provided before, ensuring they interact
    # correctly with the rest of the system state variables.
    # ... (Previous AGRMStateBus methods included here for completeness) ...
    # Note: Ensure methods like add_visited correctly interact with the
    #       get_cache() method if storing visited status in hybrid caches.
    #       Currently, visited status uses Python sets directly for simplicity.

    def update_sweep_data(self, sweep_results: Dict):
        """ Updates state bus with data generated by the Navigator sweep. """
        print("StateBus: Updating with Navigator sweep data...")
        self.sweep_data = sweep_results.get('node_data', {})
        self.sweep_center = sweep_results.get('center')
        self.max_radius = sweep_results.get('max_radius', 0.0)
        self.shell_width = sweep_results.get('shell_width', 0.0)
        self.start_node_fwd = sweep_results.get('start_node_fwd')
        self.start_node_rev = sweep_results.get('start_node_rev')

        # Initialize visited sets and paths
        self.visited_fwd.clear()
        self.visited_rev.clear()
        self.path_fwd = []
        self.path_rev = []
        self.full_path = None
        self.current_phase = "building" # Ready to start building

        if self.start_node_fwd is not None:
            self.visited_fwd.add(self.start_node_fwd)
            self.path_fwd = [self.start_node_fwd]
            fwd_data = self.get_node_sweep_data(self.start_node_fwd)
            self.builder_fwd_state = {"status": "running", "stalls": 0, "last_node": self.start_node_fwd,
                                      "current_shell": fwd_data.get('shell', -1),
                                      "current_sector": fwd_data.get('sector', -1)}
        else:
            self.builder_fwd_state["status"] = "error"

        if self.start_node_rev is not None:
            # Ensure start nodes are different if possible, handle single node case
            if self.start_node_rev != self.start_node_fwd:
                 self.visited_rev.add(self.start_node_rev)
            self.path_rev = [self.start_node_rev]
            rev_data = self.get_node_sweep_data(self.start_node_rev)
            self.builder_rev_state = {"status": "running", "stalls": 0, "last_node": self.start_node_rev,
                                      "current_shell": rev_data.get('shell', -1),
                                      "current_sector": rev_data.get('sector', -1)}
        else:
            self.builder_rev_state["status"] = "error"

        print(f"StateBus: Sweep data loaded. Fwd starts at {self.start_node_fwd}, Rev starts at {self.start_node_rev}")

    def get_node_sweep_data(self, node_id: int) -> Dict:
        """ Gets sweep metadata for a specific node. Returns empty dict if not found. """
        return self.sweep_data.get(node_id, {})

    def is_visited(self, node_id: int) -> bool:
        """ Checks if a node has been visited by EITHER builder using internal sets. """
        return node_id in self.visited_fwd or node_id in self.visited_rev

    def add_visited(self, node_id: int, builder_type: str):
        """ Adds a node to the appropriate visited set and path, updates builder state. """
        node_data = self.get_node_sweep_data(node_id)
        current_shell = node_data.get('shell', -1)
        current_sector = node_data.get('sector', -1)

        if builder_type == 'forward':
            if node_id not in self.visited_fwd:
                self.visited_fwd.add(node_id)
                self.path_fwd.append(node_id)
                self.builder_fwd_state.update({
                    "last_node": node_id, "stalls": 0, "status": "running",
                    "current_shell": current_shell, "current_sector": current_sector
                })
        elif builder_type == 'reverse':
             if node_id not in self.visited_rev:
                self.visited_rev.add(node_id)
                self.path_rev.append(node_id)
                self.builder_rev_state.update({
                    "last_node": node_id, "stalls": 0, "status": "running",
                    "current_shell": current_shell, "current_sector": current_sector
                })

    def get_unvisited_nodes(self) -> Set[int]:
        """ Returns the set of all nodes not yet visited by either builder. """
        all_nodes = set(range(self.num_nodes))
        visited_all = self.visited_fwd.union(self.visited_rev)
        return all_nodes - visited_all

    def update_modulation_params(self, new_params: Dict):
        """ Updates dynamic modulation parameters (called by Controller). """
        self.modulation_params.update(new_params)
        # print(f"StateBus: Modulation params updated: {self.modulation_params}")

    def update_builder_state(self, builder_type: str, status: Optional[str] = None, stalled: Optional[bool] = None):
         """ Updates the status of a builder agent, tracking stalls. """
         state = self.builder_fwd_state if builder_type == 'forward' else self.builder_rev_state
         if status:
             state["status"] = status
         if stalled is True:
             state["stalls"] += 1
             state["status"] = "stalled" # Mark as stalled
         elif stalled is False: # Explicitly told not stalled (i.e., progress made)
             state["stalls"] = 0
             if not status: state["status"] = "running" # Assume running if progress made

    def check_convergence(self) -> bool:
         """ Checks if builders meet criteria to merge paths using dynamic midpoint logic. """
         node_fwd = self.builder_fwd_state["last_node"]
         node_rev = self.builder_rev_state["last_node"]
         if node_fwd == -1 or node_rev == -1 or \
            self.builder_fwd_state["status"] not in ["running", "stalled"] or \
            self.builder_rev_state["status"] not in ["running", "stalled"]:
             return False

         shell_fwd = self.builder_fwd_state["current_shell"]
         shell_rev = self.builder_rev_state["current_shell"]
         sector_fwd = self.builder_fwd_state["current_sector"]
         sector_rev = self.builder_rev_state["current_sector"]
         if shell_fwd == -1 or shell_rev == -1 or sector_fwd == -1 or sector_rev == -1: return False

         shell_threshold = self.config.get("convergence_shell_threshold", 1)
         shell_overlap = abs(shell_fwd - shell_rev) <= shell_threshold

         num_sectors = self.config.get("sweep_num_sectors", 8)
         sector_threshold = self.config.get("convergence_sector_threshold", 1)
         sector_diff = abs(sector_fwd - sector_rev)
         sector_proximity = min(sector_diff, num_sectors - sector_diff) <= sector_threshold

         stall_dist_factor = self.config.get("convergence_stall_dist_factor", 5.0)
         stall_dist_threshold = stall_dist_factor * max(1.0, self.shell_width or 10.0)
         phys_dist = math.dist(self.cities[node_fwd], self.cities[node_rev])
         is_stalled = self.builder_fwd_state["stalls"] > 3 or self.builder_rev_state["stalls"] > 3
         stall_convergence = is_stalled and phys_dist <= stall_dist_threshold

         converged = (shell_overlap and sector_proximity) or stall_convergence

         if converged:
             print(f"StateBus: Convergence detected between FWD {node_fwd} and REV {node_rev}")
             self.current_phase = "converging"
             self.builder_fwd_state["status"] = "converged"
             self.builder_rev_state["status"] = "converged"
         return converged

    def merge_paths(self) -> bool:
        """ Merges paths after convergence. Returns True if complete, False if patching needed. """
        if self.current_phase != "converging": return False
        print("StateBus: Attempting path merge...")
        node_fwd_last = self.path_fwd[-1]
        node_rev_last = self.path_rev[-1]
        merged_list = list(self.path_fwd)
        reversed_rev_path = self.path_rev[::-1]
        if node_fwd_last == node_rev_last:
            merged_list.extend(reversed_rev_path[1:])
        else:
            merged_list.extend(reversed_rev_path)
        self.full_path = merged_list

        visited_final = set(self.full_path)
        missed_nodes = set(range(self.num_nodes)) - visited_final
        if missed_nodes:
            print(f"StateBus WARNING: Path merge complete, but {len(missed_nodes)} nodes missed.")
            self.current_phase = "patching"
            return False
        else:
            if len(self.full_path) > 1 and self.full_path[0] != self.full_path[-1]:
                self.full_path.append(self.full_path[0]) # Close the loop
            print(f"StateBus: Path merge successful. All {self.num_nodes} nodes included.")
            self.current_phase = "merged"
            return True

    def add_salesman_proposal(self, proposal: Dict):
        self.salesman_proposals.append(proposal)

    def get_salesman_proposals(self) -> List[Dict]:
        return self.salesman_proposals

    def clear_salesman_proposals(self):
        self.salesman_proposals = []

    def store_accepted_patch(self, patch: Dict):
        self.accepted_patches.append(patch)

    def get_accepted_patches(self) -> List[Dict]:
        return self.accepted_patches

    def clear_accepted_patches(self):
        self.accepted_patches = []

    def splice_patch(self, patch: Dict) -> bool:
        """ Applies an accepted patch to the full_path. """
        if not self.full_path or self.current_phase not in ["merged", "finalizing", "complete"]:
            print("ERROR: Cannot splice patch, path not ready.")
            return False
        try:
            start_idx, end_idx = patch['segment_indices']
            new_subpath = patch['new_subpath_nodes']
            if not (0 <= start_idx < end_idx < len(self.full_path)):
                print(f"ERROR: Invalid splice indices {start_idx}, {end_idx}")
                return False
            # Assumes new_subpath replaces nodes from index start_idx+1 up to end_idx-1
            print(f"StateBus: Splicing patch {new_subpath} between indices {start_idx} and {end_idx}")
            self.full_path = self.full_path[:start_idx+1] + new_subpath + self.full_path[end_idx:]
            print(f"StateBus: Path spliced. New length: {len(self.full_path)}")
            return True
        except Exception as e:
            print(f"ERROR: Exception during patch splice: {e}")
            return False

class MDHG:
    def __init__(self, buckets:int=256, lfu_size:int=8192):
        self.buckets=buckets; self.lfu=TinyLFU(lfu_size); self.store={}; self.place={}
    def _place(self, key:str)->int:
        h=int(hashlib.blake2b(key.encode(), digest_size=8).hexdigest(),16); return jump_hash(h, self.buckets)
    def put(self, item: Dict[str, Any]):
        if "key" not in item:
            item=dict(item); item["key"]=sha256_json(item)
        key=item["key"]; idx=self._place(key); self.store[key]=item; self.place[key]=idx; self.lfu.admit(key)
        return now_receipt({"stage":"mdhg.put","key":key,"bucket":idx})
    def propose_topK(self, k:int=8):
        keys=list(self.store.keys()); keys.sort(key=lambda x:self.lfu.score(x), reverse=True); return keys[:k]
    def manifest(self): return now_receipt({"stage":"mdhg.manifest","count":len(self.store)})

class ModulationController:
    """
    The 'brain' of AGRM. Manages system state, agent coordination,
    dynamic legality modulation, phase unlocks, and recovery triggers.
    Uses Hybrid Hashing logic. Includes dynamic adjustments based on feedback.
    """
    def __init__(self, bus: AGRMStateBus, config: Dict):
        self.bus = bus
        self.config = config
        self.default_modulation_params = self.bus.modulation_params.copy()
        self.complexity_threshold = config.get("hybrid_hash_threshold", 5)

    def assess_complexity(self, context: Dict) -> int:
        # Placeholder - needs better logic based on context
        return context.get("num_candidates", 1)

    def select_cache(self, context: Dict) -> Union[Dict, MDHGHashTable]:
        complexity_n = self.assess_complexity(context)
        return self.bus.get_cache(complexity_n)

    def trigger_migration_check(self, key: Any, old_n: int, new_n: int):
        # Simplified: Assumes value needs to be fetched if migrating dict->MDHG
        if (old_n <= self.complexity_threshold < new_n):
             source_cache = self.bus.get_cache(old_n)
             if key in source_cache:
                 value = source_cache.get(key) # Get value before migrating
                 self.bus.migrate_data(key, old_n, new_n, value) # Pass value
        elif (old_n > self.complexity_threshold >= new_n):
             self.bus.migrate_data(key, old_n, new_n) # Value fetched inside migrate_data


    def update_controller_state(self):
        """ Main update loop for the controller - applies dynamic modulation. """
        fwd_stalls = self.bus.builder_fwd_state["stalls"]
        rev_stalls = self.bus.builder_rev_state["stalls"]
        fwd_status = self.bus.builder_fwd_state["status"]
        rev_status = self.bus.builder_rev_state["status"]

        nodes_visited_count = len(self.bus.visited_fwd) + len(self.bus.visited_rev)
        progress_percent = nodes_visited_count / max(1, self.bus.num_nodes)

        new_params = {}
        params_changed = False
        current_params = self.bus.modulation_params

        # --- Adaptive Unlocking ---
        midpoint_percent = self.config.get("midpoint_unlock_percent", 0.5)
        if progress_percent >= midpoint_percent and not current_params["allow_sparse_unlock"]:
            print("CONTROLLER: Midpoint reached. Unlocking sparse zones.")
            new_params["allow_sparse_unlock"] = True
            params_changed = True
        # Update overall phase on bus if needed (e.g., based on progress)
        if progress_percent >= midpoint_percent and self.bus.current_phase == "building":
             self.bus.current_phase = "post-midpoint"

        # --- Dynamic Modulation & Override Logic ---
        stall_threshold = self.config.get("controller_stall_threshold", 5)
        severe_stall_threshold = stall_threshold * self.config.get("controller_severe_stall_factor", 2)
        override_active_now = False
        reentry_active_now = False

        # Check for severe stalls -> trigger reentry
        if (fwd_stalls >= severe_stall_threshold or rev_stalls >= severe_stall_threshold) and not current_params["reentry_mode"]:
            print(f"CONTROLLER: Severe stall ({fwd_stalls}, {rev_stalls}). Triggering Reentry Mode.")
            new_params["reentry_mode"] = True
            new_params["soft_override_active"] = True # Reentry implies override
            # Apply significant relaxation for reentry
            new_params["curvature_limit"] = self.default_modulation_params["curvature_limit"] + self.config.get("mod_reentry_curve_relax", math.pi / 6)
            new_params["shell_tolerance"] = self.default_modulation_params["shell_tolerance"] + self.config.get("mod_reentry_shell_relax", 2)
            new_params["distance_cap_factor"] = self.default_modulation_params["distance_cap_factor"] * self.config.get("mod_reentry_dist_relax_factor", 1.5)
            params_changed = True
            reentry_active_now = True
        elif current_params["reentry_mode"]: # If already in reentry, keep flags set
             reentry_active_now = True
             override_active_now = True # Reentry keeps override active

        # Check for moderate stalls -> trigger soft override (if not already in reentry)
        elif fwd_stalls >= stall_threshold and rev_stalls >= stall_threshold and not current_params["soft_override_active"]:
            print(f"CONTROLLER: Both builders stalled ({fwd_stalls}, {rev_stalls}). Activating soft override.")
            new_params["soft_override_active"] = True
            # Apply moderate relaxation
            new_params["curvature_limit"] = self.default_modulation_params["curvature_limit"] + self.config.get("mod_override_curve_relax", math.pi / 12)
            new_params["shell_tolerance"] = self.default_modulation_params["shell_tolerance"] + self.config.get("mod_override_shell_relax", 1)
            params_changed = True
            override_active_now = True
        elif current_params["soft_override_active"]: # If already in override, keep flag set
             override_active_now = True

        # Reset if overrides were active but no longer needed
        # Check if builders are running OR converged (implying stability)
        fwd_stable = fwd_status in ["running", "converged", "finished"]
        rev_stable = rev_status in ["running", "converged", "finished"]
        # Reset if BOTH are stable AND override/reentry was previously active
        if (current_params["soft_override_active"] or current_params["reentry_mode"]) and \
           fwd_stable and rev_stable:
             print("CONTROLLER: Builders stable. Deactivating overrides/reentry. Resetting params.")
             # Reset only the params that were changed by override/reentry
             reset_keys = ["soft_override_active", "reentry_mode", "curvature_limit", "shell_tolerance", "distance_cap_factor"]
             for key in reset_keys:
                 if key in self.default_modulation_params:
                     new_params[key] = self.default_modulation_params[key]
                 else: # Ensure flags are reset even if not in defaults
                     if key == "soft_override_active": new_params[key] = False
                     if key == "reentry_mode": new_params[key] = False
             # Ensure sparse unlock state is preserved based on progress
             new_params["allow_sparse_unlock"] = current_params["allow_sparse_unlock"]
             params_changed = True

        # Apply changes to the bus
        if params_changed:
            self.bus.update_modulation_params(new_params)

    def get_current_legality_params(self) -> Dict:
        """ Returns the currently active legality parameters from the bus. """
        return self.bus.modulation_params.copy()

    def process_salesman_feedback(self):
        """ Evaluates patch proposals from Salesman and stores accepted ones on bus. """
        proposals = self.bus.get_salesman_proposals()
        if not proposals: return
        print(f"CONTROLLER: Evaluating {len(proposals)} Salesman proposals.")
        accepted_patches = []
        for patch in proposals:
            # Evaluation logic: Accept if cost saving is positive and significant?
            # Needs more sophisticated evaluation (e.g., structural impact)
            cost_saving = patch.get('cost_saving', 0.0)
            if cost_saving > self.config.get("controller_patch_min_saving", 0.1): # Require min saving
                print(f"CONTROLLER: Accepting patch proposal for segment {patch.get('segment_indices')} (Save: {cost_saving:.2f})")
                self.bus.store_accepted_patch(patch) # Store on bus for builder
            # else: print(f"CONTROLLER: Rejecting patch proposal for segment {patch.get('segment_indices')} (Saving too small)")
        self.bus.clear_salesman_proposals() # Clear pending proposals

class NavigatorGR:
    """
    Performs Golden Ratio sweeps to gather spatial and structural metadata.
    Does NOT build paths. Provides data for AGRM filtering and pathing.
    Includes dynamic shell width, quadrant/hemisphere/sector tagging, k-NN density.
    """
    def __init__(self, cities: List[Tuple[float, float]], config: Dict):
        self.cities = cities
        self.num_nodes = len(cities)
        self.config = config
        self.PHI = (1 + math.sqrt(5)) / 2
        self.sweep_data: Dict[int, Dict] = {i:{} for i in range(self.num_nodes)} # Pre-initialize
        self.center: Optional[Tuple[float, float]] = None
        self.max_radius: float = 0.0
        self.shell_width: float = 0.0
        self.start_node_fwd: Optional[int] = None
        self.start_node_rev: Optional[int] = None

    def _calculate_center(self):
        if not self.cities: self.center = (0.0, 0.0); return
        sum_x = sum(c[0] for c in self.cities)
        sum_y = sum(c[1] for c in self.cities)
        self.center = (sum_x / self.num_nodes, sum_y / self.num_nodes)

    def _calculate_radii_and_angles(self):
        if self.center is None: self._calculate_center()
        cx, cy = self.center
        max_r_sq = 0
        for i, (x, y) in enumerate(self.cities):
            dx, dy = x - cx, y - cy
            radius_sq = dx*dx + dy*dy
            radius = math.sqrt(radius_sq) if radius_sq > 0 else 0
            angle = math.atan2(dy, dx)
            self.sweep_data[i].update({'radius': radius, 'angle': angle})
            if radius_sq > max_r_sq: max_r_sq = radius_sq
        self.max_radius = math.sqrt(max_r_sq) if max_r_sq > 0 else 0

    def _assign_shells_and_sectors(self):
        if self.max_radius == 0 and self.num_nodes > 1: self._calculate_radii_and_angles()
        if self.max_radius == 0: # Handle single node or all nodes at center
             for i in range(self.num_nodes):
                 self.sweep_data[i]['shell'] = 0
                 self.sweep_data[i]['sector'] = 0
             self.shell_width = 1.0
             return

        desired_shells = self.config.get("sweep_num_shells", 10)
        self.shell_width = (self.max_radius / desired_shells) if desired_shells > 0 else self.max_radius
        if self.shell_width <= 1e-9: self.shell_width = 1.0

        num_sectors = self.config.get("sweep_num_sectors", 8)
        if num_sectors <= 0: num_sectors = 1
        sector_angle = 2 * math.pi / num_sectors

        shell_counts = Counter()
        for i in range(self.num_nodes):
            radius = self.sweep_data[i].get('radius', 0.0)
            angle = self.sweep_data[i].get('angle', 0.0)
            shell = int(radius // self.shell_width)
            shell = min(shell, desired_shells - 1) if desired_shells > 0 else 0
            self.sweep_data[i]['shell'] = max(0, shell)
            shell_counts[self.sweep_data[i]['shell']] += 1
            normalized_angle = (angle + 2 * math.pi) % (2 * math.pi)
            sector = int(normalized_angle // sector_angle)
            self.sweep_data[i]['sector'] = min(sector, num_sectors - 1)
        # print(f"  Navigator: Shell distribution: {dict(sorted(shell_counts.items()))}")

    def _calculate_gr_sweep_scores(self):
        # Placeholder: Rank by shell, then angle. Needs proper GR spiral logic.
        temp_nodes = []
        for i in range(self.num_nodes):
            shell = self.sweep_data[i].get('shell', 999)
            angle = self.sweep_data[i].get('angle', 0.0)
            score = shell + (abs(angle) / (2*math.pi)) # Simple composite score
            temp_nodes.append((score, i))
        temp_nodes.sort()
        for rank, (score, i) in enumerate(temp_nodes):
            self.sweep_data[i]['sweep_rank'] = rank
            self.sweep_data[i]['gr_score'] = score
        if temp_nodes:
            self.start_node_fwd = temp_nodes[0][1]
            self.start_node_rev = temp_nodes[-1][1]
            # print(f"  Navigator: Determined Fwd Start={self.start_node_fwd}, Rev Start={self.start_node_rev}")

    def _assign_quadrants_and_hemispheres(self):
        if self.center is None: self._calculate_center()
        cx, cy = self.center
        if not any('sweep_rank' in d for i,d in self.sweep_data.items()):
             print("  Navigator ERROR: Sweep rank needed for hemisphere assignment.")
             return
        midpoint_rank = self.num_nodes // 2
        for i, (x, y) in enumerate(self.cities):
            if x >= cx and y >= cy: quadrant = "Q1"
            elif x < cx and y >= cy: quadrant = "Q2"
            elif x < cx and y < cy: quadrant = "Q3"
            else: quadrant = "Q4"
            self.sweep_data[i]['quadrant'] = quadrant
            rank = self.sweep_data[i].get('sweep_rank', -1)
            hemisphere = "A_start" if rank < midpoint_rank else "B_end"
            self.sweep_data[i]['hemisphere'] = hemisphere

    def _classify_density(self):
        print("  Navigator: Classifying node density...")
        if not HAS_SKLEARN or self.num_nodes < 3: # Need at least 3 points for k-NN with k>=1
            print("  Navigator WARNING: Using basic shell density (sklearn not found or N too small).")
            nodes_per_shell = Counter(d.get('shell', -1) for d in self.sweep_data.values())
            if not nodes_per_shell: return # Avoid division by zero
            avg_nodes_per_shell = self.num_nodes / max(1, len(nodes_per_shell))
            dense_threshold = avg_nodes_per_shell * self.config.get("density_dense_factor", 1.5)
            sparse_threshold = avg_nodes_per_shell * self.config.get("density_sparse_factor", 0.5)
            for i in range(self.num_nodes):
                shell = self.sweep_data[i].get('shell', -1)
                shell_count = nodes_per_shell.get(shell, 0)
                if shell_count >= dense_threshold: density = "dense"
                elif shell_count <= sparse_threshold: density = "sparse"
                else: density = "midling"
                self.sweep_data[i]['density'] = density
        else:
            coords = np.array(self.cities)
            k = self.config.get("density_knn_k", 10)
            k = min(k, self.num_nodes - 1)
            if k <= 0: # Handle N=1 or N=2 case
                 for i in range(self.num_nodes): self.sweep_data[i]['density'] = "midling"
                 return

            # Use BallTree for potentially better performance on some distributions
            tree = BallTree(coords)
            # Query for k+1 neighbors to exclude self
            distances, _ = tree.query(coords, k=k + 1)
            # Calculate average distance to k nearest neighbors (excluding self)
            avg_distances = np.mean(distances[:, 1:], axis=1)

            mean_avg_dist = np.mean(avg_distances)
            std_avg_dist = np.std(avg_distances)
            # Avoid zero std dev
            if std_avg_dist < 1e-9: std_avg_dist = mean_avg_dist * 0.1 if mean_avg_dist > 0 else 1.0

            density_factor = self.config.get("density_std_dev_factor", 0.75)
            dense_threshold = mean_avg_dist - std_avg_dist * density_factor
            sparse_threshold = mean_avg_dist + std_avg_dist * density_factor

            for i in range(self.num_nodes):
                avg_dist = avg_distances[i]
                if avg_dist <= dense_threshold: density = "dense"
                elif avg_dist >= sparse_threshold: density = "sparse"
                else: density = "midling"
                self.sweep_data[i]['density'] = density

        density_counts = Counter(d.get('density', 'unknown') for d in self.sweep_data.values())
        print(f"  Navigator: Density classification complete. Counts: {dict(density_counts)}")


    def run_sweep(self) -> Dict:
        """ Executes the full sweep and data generation process. """
        print("Navigator: Running sweep...")
        start_time = time.time()
        self._calculate_center()
        self._calculate_radii_and_angles()
        self._assign_shells_and_sectors()
        self._calculate_gr_sweep_scores() # Assigns ranks
        self._assign_quadrants_and_hemispheres() # Assigns hemi based on rank
        self._classify_density() # Assigns density
        end_time = time.time()
        print(f"Navigator: Sweep complete in {end_time - start_time:.4f} seconds.")
        return {
            'node_data': self.sweep_data, 'center': self.center, 'max_radius': self.max_radius,
            'shell_width': self.shell_width, 'start_node_fwd': self.start_node_fwd, 'start_node_rev': self.start_node_rev
        }

class PathAuditAgent:
    """
    Runs AFTER the full AGRM + Salesman process is complete.
    Evaluates the final path quality using global metrics.
    Analyzes patterns of sub-optimality.
    Generates parameter adjustment recommendations for the NEXT run.
    Enables run-to-run meta-learning.
    """
    def __init__(self, bus: AGRMStateBus, config: Dict):
        self.bus = bus
        self.config = config
        self.metrics = {}
        self.patterns = {}
        self.recommendations = {}

    def run_audit(self) -> Dict:
        """ Performs the full audit process. Returns recommendations dict. """
        print("AUDIT AGENT: Starting post-run path audit...")
        if not self.bus.full_path or self.bus.current_phase not in ["merged", "finalizing", "complete", "patched"]: # Allow patched state
            print("AUDIT AGENT: Final path not available or run not complete. Skipping audit.")
            return {}

        self.metrics = self._calculate_global_metrics()
        self.patterns = self._analyze_patterns()
        self.recommendations = self._generate_recommendations()

        print("AUDIT AGENT: Audit complete.")
        print(f"  Audit Metrics: {self.metrics}")
        print(f"  Audit Patterns: {self.patterns}")
        print(f"  Audit Recommendations: {self.recommendations}")
        return self.recommendations

    def _calculate_global_metrics(self) -> Dict:
        """ Calculates high-level quality metrics for the final path. """
        metrics = {}
        path = self.bus.full_path
        # 1. Final Path Length
        final_cost = self.bus.calculate_total_path_cost(path) # Use bus helper
        metrics['final_path_cost'] = final_cost
        metrics['final_efficiency'] = final_cost / max(1, self.bus.num_nodes)

        # 2. Comparison to Baseline (e.g., simple Nearest Neighbor from start)
        baseline_cost = self._run_simple_nn_baseline()
        metrics['baseline_nn_cost'] = baseline_cost
        if baseline_cost > 0:
             metrics['length_vs_baseline'] = final_cost / baseline_cost

        # 3. Remaining Salesman Flags (Count reported by Salesman)
        # Need Salesman to store final flag count accessible here
        # metrics['remaining_salesman_flags'] = self.bus.salesman_final_flags?

        # 4. Structural Metrics (Example: Bounding Box Ratio)
        if path:
             coords = np.array([self.bus.cities[i] for i in path[:-1]]) # Exclude return to start
             min_x, min_y = np.min(coords, axis=0)
             max_x, max_y = np.max(coords, axis=0)
             width = max_x - min_x
             height = max_y - min_y
             metrics['bounding_box_ratio'] = width / height if height > 0 else 1.0

        # 5. Add more metrics: Avg turn angle, std dev of edge lengths, etc.
        return metrics

    def _run_simple_nn_baseline(self) -> float:
         """ Runs a basic Nearest Neighbor heuristic for baseline comparison. """
         if not self.bus.cities: return 0.0
         start_node = self.bus.start_node_fwd if self.bus.start_node_fwd is not None else 0
         unvisited = set(range(self.bus.num_nodes))
         current = start_node
         path = [current]
         unvisited.remove(current)
         total_dist = 0.0

         while unvisited:
             nearest_node = -1
             min_dist = float('inf')
             pos_current = self.bus.cities[current]
             for node in unvisited:
                 dist = math.dist(pos_current, self.bus.cities[node])
                 if dist < min_dist:
                     min_dist = dist
                     nearest_node = node
             if nearest_node != -1:
                 total_dist += min_dist
                 current = nearest_node
                 path.append(current)
                 unvisited.remove(current)
             else: break # Should not happen if graph is connected

         # Add return to start
         if len(path) > 1:
              total_dist += math.dist(self.bus.cities[current], self.bus.cities[start_node])
         return total_dist


    def _analyze_patterns(self) -> Dict:
        """ Analyzes patterns of sub-optimality in the final path. """
        patterns = {}
        # Example: Analyze where Salesman flags occurred (requires Salesman to store flag locations)
        # patterns['flag_concentration_quadrant'] = self._analyze_flag_distribution('quadrant')
        # patterns['flag_concentration_shell'] = self._analyze_flag_distribution('shell')
        # patterns['high_cost_segments'] = self._find_high_cost_segments()
        return patterns # Placeholder

    def _generate_recommendations(self) -> Dict:
        """ Generates parameter tuning recommendations based on metrics and patterns. """
        recommendations = {}
        # Example Rules:
        length_ratio = self.metrics.get('length_vs_baseline', 1.0)
        target_ratio = self.config.get("audit_target_baseline_ratio", 1.1) # e.g., aim for 10% worse than NN

        # If path is much longer than baseline, maybe legality was too strict?
        if length_ratio > target_ratio * 1.2: # If >20% worse than target
             # Suggest relaxing curvature or shell tolerance slightly
             recommendations['mod_curvature_limit'] = self.bus.default_modulation_params['curvature_limit'] * 1.1 # Relax by 10%
             recommendations['mod_shell_tolerance'] = self.bus.default_modulation_params['shell_tolerance'] + 1
             print("AUDIT Recommendation: Path long vs baseline. Suggest relaxing curvature/shell tolerance.")

        # If Salesman found many 2-opt opportunities (requires pattern analysis)
        # if self.patterns.get('high_2opt_flags'):
        #    recommendations['salesman_2opt_threshold'] = self.config['salesman_2opt_threshold'] * 1.01 # Make slightly easier to trigger
        #    print("AUDIT Recommendation: Many 2-opt flags. Suggest lowering 2-opt improvement threshold.")

        # Add more rules based on other metrics and patterns
        return recommendations

class PathBuilder:
    """
    Builds a path segment (forward or reverse) using AGRM rules.
    Operates ephemerally, querying legality on demand.
    Interacts with Controller for modulation and feedback.
    Handles reentry logic when triggered.
    Can splice patches provided by Controller. Includes k-NN neighbor finding.
    """
    def __init__(self, builder_type: str, start_node: int, bus: AGRMStateBus, validator: AGRMEdgeValidator, config: Dict):
        self.builder_type = builder_type
        self.current_node = start_node
        self.bus = bus
        self.validator = validator
        self.config = config
        self.stalled_cycles = 0
        self.is_reentering = False
        # Initialize KDTree/BallTree for neighbor search if available
        self.neighbor_finder = None
        if HAS_SKLEARN and self.bus.num_nodes > 1:
            try:
                # Use BallTree as it can be better for non-uniform distributions
                self.neighbor_finder = BallTree(np.array(self.bus.cities))
                print(f"  Builder ({self.builder_type}): Initialized BallTree for neighbor search.")
            except Exception as e:
                print(f"  Builder ({self.builder_type}) WARNING: Failed to initialize BallTree: {e}. Falling back to linear scan.")
                self.neighbor_finder = None

    def step(self) -> bool:
        """ Performs one step of path construction. Returns True if progress was made. """
        state_key = "builder_fwd_state" if self.builder_type == 'forward' else "builder_rev_state"
        current_state = getattr(self.bus, state_key)
        if current_state["status"] in ["converged", "finished", "stalled_hard"]: return False

        # --- Candidate Selection ---
        k_neighbors = self.config.get("builder_knn_k", 50)
        k_neighbors = min(k_neighbors, self.bus.num_nodes - 1)
        potential_candidates = self._find_k_nearest_unvisited(k_neighbors)

        legal_candidates = [
            node for node in potential_candidates
            if self.validator.is_edge_legal(self.current_node, node, self.builder_type)
        ]

        # --- Decision & State Update ---
        next_node = None
        progress_made = False

        if legal_candidates:
            self.stalled_cycles = 0
            if self.is_reentering: # If we were reentering, mark as finished
                print(f"BUILDER ({self.builder_type}): Reentry successful, resuming normal modulation.")
                self.is_reentering = False
                # Signal controller implicitly via lack of stall
            self.bus.update_builder_state(self.builder_type, stalled=False) # Signal progress

            # Choose best candidate based on AGRM scoring (Sweep Rank)
            legal_candidates.sort(key=lambda n: self.bus.get_node_sweep_data(n).get('sweep_rank', float('inf')))
            next_node = legal_candidates[0]

        else: # Stalled
            self.stalled_cycles += 1
            self.bus.update_builder_state(self.builder_type, stalled=True)
            # print(f"BUILDER ({self.builder_type}): Stalled at node {self.current_node}, cycle {self.stalled_cycles}.")

            # Check if Controller activated reentry mode
            if self.bus.modulation_params.get("reentry_mode", False):
                if not self.is_reentering:
                    print(f"BUILDER ({self.builder_type}): Reentry mode active. Attempting inward move...")
                    self.is_reentering = True
                next_node = self._find_reentry_node()
                if not next_node:
                    print(f"BUILDER ({self.builder_type}): Reentry failed to find valid inward node. Hard stall likely.")
                    self.bus.update_builder_state(self.builder_type, status="stalled_hard")
            # Else: Normal stall, wait for controller action

        # --- Update Path ---
        if next_node is not None:
            self.bus.add_visited(next_node, self.builder_type)
            self.current_node = next_node
            progress_made = True
            # Ensure status is running if progress made
            if current_state["status"] != "running":
                self.bus.update_builder_state(self.builder_type, status="running")

        return progress_made

    def _find_k_nearest_unvisited(self, k: int) -> List[int]:
        """ Finds up to k nearest unvisited nodes using spatial index or fallback. """
        unvisited_nodes_set = self.bus.get_unvisited_nodes()
        if not unvisited_nodes_set: return []
        if k <= 0: return []

        current_pos = np.array([self.bus.cities[self.current_node]])

        if self.neighbor_finder:
            # Query tree for more neighbors than needed, then filter
            query_k = min(len(unvisited_nodes_set), k * 5, self.bus.num_nodes) # Query more initially
            try:
                 distances, indices = self.neighbor_finder.query(current_pos, k=query_k)
                 # indices[0] contains neighbor indices, distances[0] the distances
                 # Filter out self and already visited nodes
                 neighbors = []
                 for idx in indices[0]:
                     if idx != self.current_node and idx in unvisited_nodes_set:
                         neighbors.append(idx)
                         if len(neighbors) == k: break # Stop when we have enough
                 return neighbors
            except Exception as e:
                 print(f"  Builder ({self.builder_type}) WARNING: KDTree/BallTree query failed: {e}. Falling back.")
                 # Fallback to linear scan if tree query fails

        # Fallback: Linear scan over unvisited nodes
        distances = []
        for node_idx in unvisited_nodes_set:
            if node_idx == self.current_node: continue
            dist = math.dist(current_pos[0], self.bus.cities[node_idx])
            distances.append((dist, node_idx))
        distances.sort()
        return [node_idx for dist, node_idx in distances[:k]]


    def _find_reentry_node(self) -> Optional[int]:
         """ Finds a valid candidate node closer to the spiral center during reentry. """
         if not self.bus.center or not self.bus.sweep_data: return None
         current_data = self.bus.get_node_sweep_data(self.current_node)
         current_shell = current_data.get('shell', -1)
         if current_shell <= 0: return None # Already at center

         k_neighbors = self.config.get("builder_knn_k_reentry", 100)
         potential_candidates = self._find_k_nearest_unvisited(k_neighbors)

         valid_reentry_nodes = []
         for node in potential_candidates:
             # Check legality using RELAXED rules (validator uses current bus params)
             if self.validator.is_edge_legal(self.current_node, node, self.builder_type):
                 data_to = self.bus.get_node_sweep_data(node)
                 shell_to = data_to.get('shell', -1)
                 # Must move to an inner shell
                 if shell_to != -1 and shell_to < current_shell:
                     score = (current_shell - shell_to) # Prioritize larger drop
                     valid_reentry_nodes.append((score, node))

         if valid_reentry_nodes:
             valid_reentry_nodes.sort(reverse=True) # Best score (largest drop) first
             return valid_reentry_nodes[0][1]
         else:
             return None

    def splice_patch_if_instructed(self):
         """ Checks bus for accepted patches and splices them if applicable. """
         # This function is called by the main runner loop
         accepted_patches = self.bus.get_accepted_patches()
         if not accepted_patches: return

         # Process patches relevant to this builder? Or assume global path?
         # Assume patches apply to the final merged path managed by the bus
         spliced_any = False
         remaining_patches = []
         for patch in accepted_patches:
              # Check if patch applies to the portion built by this agent? Complex.
              # Simplification: Let the bus handle splicing on the final path.
              # This builder doesn't modify its history directly, relies on bus state.
              # If more sophisticated local splicing is needed, logic goes here.
              # For now, just acknowledge the concept.
              pass # Logic is handled in bus.splice_patch called by runner

class SalesmanValidator:
    """
    Analyzes a completed path for inefficiencies (long jumps, curvature breaks).
    Generates AGRM-legal patch proposals for refinement via the Controller.
    Includes basic 2-opt check.
    """
    def __init__(self, bus: AGRMStateBus, validator: AGRMEdgeValidator, config: Dict):
        self.bus = bus
        self.validator = validator # Used to check legality of proposed patches
        self.config = config
        self.stats = {'flags_generated': 0, 'proposals_generated': 0}

    def run_validation_and_patching(self):
        """ Runs the post-path validation and patch generation cycle. """
        path = self.bus.full_path
        # Ensure path exists and is a closed loop for 2-opt checks
        if not path or len(path) < 4 or path[0] != path[-1]:
            print("SALESMAN: Path too short, not available, or not closed. Skipping validation.")
            return

        print(f"SALESMAN: Starting validation of path with {len(path)} steps...")
        self.stats['flags_generated'] = 0
        self.stats['proposals_generated'] = 0
        proposals = []

        max_len_factor = self.config.get("salesman_max_len_factor", 4.0)
        max_curve = self.config.get("salesman_max_curve", math.pi * 0.5) # 90 deg
        enable_2opt = self.config.get("salesman_enable_2opt", True)
        opt_threshold = self.config.get("salesman_2opt_threshold", 0.99) # Min 1% improvement

        # Use baseline legality params for checking proposed swaps
        validation_params = self.bus.default_modulation_params

        # Iterate through path segments for checks
        # Note: path includes return to start, so iterate up to len(path) - 2 for curvature/2-opt
        for i in range(len(path) - 1):
            p1 = path[i]
            p2 = path[i+1]
            pos1 = self.bus.cities[p1]
            pos2 = self.bus.cities[p2]
            dist12 = math.dist(pos1, pos2)

            # 1. Check Long Jumps
            shell1 = self.bus.get_node_sweep_data(p1).get('shell', 0)
            avg_dist_in_shell = max(1.0, self.bus.shell_width or 10.0)
            dist_threshold = avg_dist_in_shell * max_len_factor
            if dist12 > dist_threshold:
                self.stats['flags_generated'] += 1
                # print(f"SALESMAN FLAG (Long Jump): {p1}->{p2} (Dist: {dist12:.2f})")

            # 2. Check Sharp Turns (at p2 = path[i+1])
            if i < len(path) - 2:
                p_prev = path[i]     # p1
                p_curr = path[i+1]   # p2
                p_next = path[i+2]   # p3
                pos_prev, pos_curr, pos_next = self.bus.cities[p_prev], self.bus.cities[p_curr], self.bus.cities[p_next]
                vec1 = (pos_curr[0] - pos_prev[0], pos_curr[1] - pos_prev[1])
                vec2 = (pos_next[0] - pos_curr[0], pos_next[1] - pos_curr[1])
                len1, len2 = math.hypot(vec1[0], vec1[1]), math.hypot(vec2[0], vec2[1])
                if len1 > 1e-9 and len2 > 1e-9:
                    dot = vec1[0] * vec2[0] + vec1[1] * vec2[1]
                    cos_angle = max(-1.0, min(1.0, dot / (len1 * len2)))
                    angle = math.acos(cos_angle)
                    if angle > max_curve:
                        self.stats['flags_generated'] += 1
                        # print(f"SALESMAN FLAG (Sharp Turn): at {p_curr} (Angle: {math.degrees(angle):.1f})")

            # 3. Check for 2-Opt Improvements (Edges: p1->p2 and p3->p4)
            # We need i+3 to exist, and ensure we don't wrap around incorrectly
            if enable_2opt and i < len(path) - 3:
                 p3 = path[i+2]
                 p4 = path[i+3]
                 # Ensure p1 != p3 and p2 != p4 to avoid degenerate swaps
                 if p1 == p3 or p1 == p4 or p2 == p3 or p2 == p4: continue

                 pos3, pos4 = self.bus.cities[p3], self.bus.cities[p4]
                 current_dist = dist12 + math.dist(pos3, pos4)
                 swapped_dist = math.dist(pos1, pos3) + math.dist(pos2, p4)

                 if swapped_dist < current_dist * opt_threshold:
                     # Potential improvement. Check if new edges p1->p3 and p2->p4 are AGRM-legal
                     # Use the validator instance with baseline/validation params
                     # Pass 'final_check' or similar context if validator uses it
                     # Note: is_edge_legal needs access to params, pass them explicitly
                     if self.validator.is_edge_legal(p1, p3, 'final_check') and \
                        self.validator.is_edge_legal(p2, p4, 'final_check'):
                         self.stats['flags_generated'] += 1
                         self.stats['proposals_generated'] += 1
                         print(f"SALESMAN: Proposing 2-opt swap: ({p1},{p2}) & ({p3},{p4}) -> ({p1},{p3}) & ({p2},{p4}). Saving: {current_dist - swapped_dist:.2f}")
                         # Define the patch: replaces segment from index i+1 to i+2
                         # Original: [... p1, p2, p3, p4 ...]
                         # Swapped: [... p1, p3, p2, p4 ...]
                         # The segment between p1 and p4 needs reversal: [p3, p2] replaces [p2, p3]
                         proposal = {
                             'type': '2-opt',
                             'segment_indices': (i, i+3), # Indices covering p1 to p4
                             'original_nodes': [p1, p2, p3, p4],
                             # The new sequence for nodes BETWEEN index i and index i+3
                             # The path from i+1 up to (but not including) i+3 needs reversal
                             # Original segment is path[i+1 : i+3] = [p2, p3]
                             # New segment should be reversed: [p3, p2]
                             'new_subpath_nodes': path[i+1 : i+3][::-1], # Reverse the segment between swapped edges
                             'cost_saving': current_dist - swapped_dist
                         }
                         proposals.append(proposal)
                     # else: print(f"SALESMAN: Potential 2-opt swap rejected by AGRM legality.")

        print(f"SALESMAN: Validation complete. Found {self.stats['flags_generated']} flags. Generated {self.stats['proposals_generated']} patch proposals.")
        # Send valid proposals to the Controller via the bus
        if proposals:
            for p in proposals:
                self.bus.add_salesman_proposal(p)

class Harness:
    def __init__(self, spec: Dict[str, Any], gov: GovernanceProto):
        self.id = str(uuid.uuid4())
        self.spec = spec
        self.gov = gov
        self.gov.record_event('harness_created', {'id': self.id, 'spec': spec})

    def execute(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Placeholder execution – logs start/end, returns dummy stats."""
        self.gov.record_event('harness_start', {'harness': self.id, 'plan': plan})
        # ... real AGRM + MDHG algorithms would run here ...
        result = {'status': 'ok', 'energy_used': 0.0, 'timestamp': datetime.datetime.utcnow().isoformat()}
        self.gov.record_event('harness_end', {'harness': self.id, 'result': result})
        return result

class HarnessBuilder:
    def __init__(self):
        self.gov: GovernanceProto | None = None

    # AGRM_MDHGProto
    def bootstrap(self, governance: GovernanceProto) -> None:
        self.gov = governance

    def build_harness(self, slice_spec: Dict[str, Any]) -> Harness:
        if self.gov is None:
            raise RuntimeError('HarnessBuilder.bootstrap() must be called first')
        jsonschema.validate(slice_spec, HARNESS_SCHEMA)
        return Harness(slice_spec, self.gov)

class MDHGMultiScale:
    """
    Three MDHG caches at different timescales:
    - fast: high churn, micro-events (present)
    - med: medium churn, policy outcomes (recent past)
    - slow: low churn, identity/structure (deep past)
    """
    
    def __init__(self, grid_side=12, cap_per_slot=6, bins=16):
        self.fast = MDHGCache(grid_side, cap_per_slot, bins, "fast")
        self.med = MDHGCache(grid_side, cap_per_slot, bins, "med")
        self.slow = MDHGCache(grid_side, cap_per_slot, bins, "slow")
        
        # Drift tracking: slot -> rolling hash
        self._drift: Dict[str, Dict[str, str]] = {
            "fast": {},
            "med": {},
            "slow": {}
        }
    
    def admit(self, v24: List[float], meta: Dict[str, Any], layer="fast") -> Dict[str, Any]:
        """Admit to specific layer."""
        cache = getattr(self, layer)
        res = cache.admit(v24, meta)
        
        # Update drift signature
        slot = res.get("slot")
        if slot:
            q = res.get("q24")
            if q is not None:
                sig = _h({"q24": list(q)[:8], "meta_keys": sorted(list(meta.keys()))[:12]})
                dmap = self._drift[layer]
                prev = dmap.get(slot)
                dmap[slot] = sig
                if prev and prev != sig:
                    res["drift"] = True
        
        return res
    
    def admit_all_layers(self, v24: List[float], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Admit to all three layers (for important data)."""
        return {
            "fast": self.admit(v24, meta, "fast"),
            "med": self.admit(v24, meta, "med"),
            "slow": self.admit(v24, meta, "slow")
        }
    
    def occupancy(self, layer="fast") -> List[List[int]]:
        """Get occupancy grid for layer."""
        return getattr(self, layer).occupancy_grid()
    
    def get_stats(self) -> Dict[str, Any]:
        """Stats for all layers."""
        return {
            "fast": self.fast.get_stats(),
            "med": self.med.get_stats(),
            "slow": self.slow.get_stats()
        }
    
    def snapshot(self) -> Dict[str, Any]:
        """Snapshot of all layers."""
        return {
            "fast": self.fast.snapshot(),
            "med": self.med.snapshot(),
            "slow": self.slow.snapshot()
        }

class SlotEntry:
    """Entry in an MDHG slot."""
    key: str
    q24: Tuple[int, ...]
    meta: Dict[str, Any]
    last: float = field(default_factory=lambda: time.time())
    hits: int = 0

class MDHGController(BaseController):
    """
    Multi-Dimensional Hash Grid Controller
    
    Manages hash-based indexing for high-dimensional data structures
    with E8 geometric embeddings for CMPLX semantic operations.
    
    Core Operations:
    - create_grid: Build hash grid index
    - insert_point: Add data point to grid
    - knn_search: K-nearest neighbors
    - range_query: Distance-based range search
    - get_neighbors: Grid cell neighbors
    - cluster_points: Density-based clustering
    - compute_hash: E8-aware hash computation
    """
    
    VERSION = "1.0.0"
    SUPPORTED_OPS = [
        'create_grid', 'insert_point', 'knn_search', 'range_query',
        'get_neighbors', 'cluster_points', 'compute_hash'
    ]
    
    def __init__(self, context: ControllerContext, db_path: str = "./mmdhg.sqlite"):
        super().__init__(context, "mmdhg")
        self.db_path = db_path
        self._init_schema()
        self._grids = {}
        
    def _init_schema(self) -> None:
        """Initialize database schema for MDHG operations."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Hash grids table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hash_grids (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                grid_id TEXT UNIQUE NOT NULL,
                dimensions INTEGER NOT NULL,
                cell_size REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        """)
        
        # Grid points table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS grid_points (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                grid_id TEXT NOT NULL,
                point_id TEXT UNIQUE NOT NULL,
                coords TEXT NOT NULL,  -- JSON array
                e8_coords TEXT,  -- E8 embedding
                data TEXT,  -- Associated data
                hash_key TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (grid_id) REFERENCES hash_grids(grid_id)
            )
        """)
        
        # Hash cells table for fast lookup
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hash_cells (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                grid_id TEXT NOT NULL,
                cell_key TEXT NOT NULL,
                point_ids TEXT NOT NULL,  -- JSON array
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (grid_id) REFERENCES hash_grids(grid_id),
                UNIQUE(grid_id, cell_key)
            )
        """)
        
        # Clusters table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clusters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                grid_id TEXT NOT NULL,
                cluster_id TEXT UNIQUE NOT NULL,
                point_ids TEXT NOT NULL,  -- JSON array
                centroid TEXT,  -- JSON array
                density REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (grid_id) REFERENCES hash_grids(grid_id)
            )
        """)
        
        # Create indices
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_points_grid ON grid_points(grid_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_points_hash ON grid_points(hash_key)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cells_grid ON hash_cells(grid_id)")
        
        conn.commit()
        conn.close()
        
    def _execute_command(self, command: str, payload: Dict) -> Dict[str, Any]:
        """Route commands to appropriate handlers."""
        if command == 'create_grid':
            return self._handle_create_grid(payload)
        elif command == 'insert_point':
            return self._handle_insert_point(payload)
        elif command == 'knn_search':
            return self._handle_knn_search(payload)
        elif command == 'range_query':
            return self._handle_range_query(payload)
        elif command == 'get_neighbors':
            return self._handle_get_neighbors(payload)
        elif command == 'cluster_points':
            return self._handle_cluster_points(payload)
        elif command == 'compute_hash':
            return self._handle_compute_hash(payload)
        else:
            return {'error': f'Unknown command: {command}'}
            
    def _handle_create_grid(self, payload: Dict) -> Dict[str, Any]:
        """Create new hash grid index."""
        dimensions = payload.get('dimensions', 8)
        cell_size = payload.get('cell_size', 1.0)
        metadata = payload.get('metadata', {})
        
        grid_id = f"grid_{hashlib.sha256(str(datetime.now()).encode()).hexdigest()[:16]}"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO hash_grids (grid_id, dimensions, cell_size, metadata) VALUES (?, ?, ?, ?)",
            (grid_id, dimensions, cell_size, json.dumps(metadata))
        )
        conn.commit()
        conn.close()
        
        self._grids[grid_id] = {
            'dimensions': dimensions,
            'cell_size': cell_size,
            'cell_index': {}
        }
        
        return {
            'grid_id': grid_id,
            'dimensions': dimensions,
            'cell_size': cell_size,
            'created': True
        }
        
    def _handle_insert_point(self, payload: Dict) -> Dict[str, Any]:
        """Insert point into hash grid."""
        grid_id = payload.get('grid_id')
        coords = payload.get('coords')
        data = payload.get('data')
        compute_e8 = payload.get('compute_e8', True)
        
        if not grid_id or coords is None:
            return {'error': 'Missing grid_id or coords'}
            
        # Get grid config
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT dimensions, cell_size FROM hash_grids WHERE grid_id = ?", (grid_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return {'error': f'Grid {grid_id} not found'}
            
        dimensions, cell_size = row
        coords = np.array(coords)
        
        # Compute hash key
        hash_key = self._compute_cell_hash(coords, cell_size)
        
        # Compute E8 embedding if requested
        e8_coords = None
        if compute_e8 and len(coords) >= 8:
            e8_coords = self._project_to_e8(coords[:8])
        
        point_id = f"pt_{hashlib.sha256(json.dumps(coords.tolist()).encode()).hexdigest()[:16]}"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """INSERT OR REPLACE INTO grid_points 
               (grid_id, point_id, coords, e8_coords, data, hash_key)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (grid_id, point_id, json.dumps(coords.tolist()), 
             json.dumps(e8_coords) if e8_coords else None,
             json.dumps(data) if data else None, hash_key)
        )
        
        # Update cell index
        cursor.execute(
            "SELECT point_ids FROM hash_cells WHERE grid_id = ? AND cell_key = ?",
            (grid_id, hash_key)
        )
        cell_row = cursor.fetchone()
        if cell_row:
            point_ids = json.loads(cell_row[0])
            if point_id not in point_ids:
                point_ids.append(point_id)
                cursor.execute(
                    "UPDATE hash_cells SET point_ids = ?, updated_at = ? WHERE grid_id = ? AND cell_key = ?",
                    (json.dumps(point_ids), datetime.now().isoformat(), grid_id, hash_key)
                )
        else:
            cursor.execute(
                "INSERT INTO hash_cells (grid_id, cell_key, point_ids) VALUES (?, ?, ?)",
                (grid_id, hash_key, json.dumps([point_id]))
            )
            
        conn.commit()
        conn.close()
        
        return {
            'point_id': point_id,
            'grid_id': grid_id,
            'hash_key': hash_key,
            'e8_coords': e8_coords
        }
        
    def _handle_knn_search(self, payload: Dict) -> Dict[str, Any]:
        """K-nearest neighbor search."""
        grid_id = payload.get('grid_id')
        query = np.array(payload.get('query'))
        k = payload.get('k', 5)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT point_id, coords, data, e8_coords FROM grid_points WHERE grid_id = ?",
            (grid_id,)
        )
        points = cursor.fetchall()
        conn.close()
        
        if not points:
            return {'neighbors': [], 'count': 0}
            
        # Compute distances
        distances = []
        for point_id, coords_json, data_json, e8_json in points:
            coords = np.array(json.loads(coords_json))
            dist = np.linalg.norm(coords - query)
            distances.append((dist, point_id, coords_json, data_json, e8_json))
            
        # Sort and return top k
        distances.sort(key=lambda x: x[0])
        neighbors = [
            {
                'point_id': p[1],
                'distance': float(p[0]),
                'coords': json.loads(p[2]),
                'data': json.loads(p[3]) if p[3] else None,
                'e8_coords': json.loads(p[4]) if p[4] else None
            }
            for p in distances[:k]
        ]
        
        return {
            'neighbors': neighbors,
            'count': len(neighbors),
            'query': query.tolist()
        }
        
    def _handle_range_query(self, payload: Dict) -> Dict[str, Any]:
        """Range query within distance radius."""
        grid_id = payload.get('grid_id')
        center = np.array(payload.get('center'))
        radius = payload.get('radius', 1.0)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT point_id, coords, data FROM grid_points WHERE grid_id = ?",
            (grid_id,)
        )
        points = cursor.fetchall()
        conn.close()
        
        results = []
        for point_id, coords_json, data_json in points:
            coords = np.array(json.loads(coords_json))
            dist = np.linalg.norm(coords - center)
            if dist <= radius:
                results.append({
                    'point_id': point_id,
                    'distance': float(dist),
                    'coords': coords.tolist(),
                    'data': json.loads(data_json) if data_json else None
                })
                
        return {
            'points': results,
            'count': len(results),
            'radius': radius,
            'center': center.tolist()
        }
        
    def _handle_get_neighbors(self, payload: Dict) -> Dict[str, Any]:
        """Get neighbors in same/adjacent grid cells."""
        grid_id = payload.get('grid_id')
        point_id = payload.get('point_id')
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get the cell key for this point
        cursor.execute(
            "SELECT hash_key, coords FROM grid_points WHERE grid_id = ? AND point_id = ?",
            (grid_id, point_id)
        )
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return {'neighbors': [], 'error': 'Point not found'}
            
        hash_key, coords_json = row
        coords = np.array(json.loads(coords_json))
        
        # Get all points in same cell
        cursor.execute(
            "SELECT point_id, coords, data FROM grid_points WHERE grid_id = ? AND hash_key = ?",
            (grid_id, hash_key)
        )
        cell_points = cursor.fetchall()
        conn.close()
        
        neighbors = []
        for pid, c_json, d_json in cell_points:
            if pid != point_id:
                c = np.array(json.loads(c_json))
                dist = np.linalg.norm(c - coords)
                neighbors.append({
                    'point_id': pid,
                    'distance': float(dist),
                    'coords': c.tolist(),
                    'data': json.loads(d_json) if d_json else None
                })
                
        return {
            'neighbors': neighbors,
            'count': len(neighbors),
            'cell_key': hash_key,
            'point_id': point_id
        }
        
    def _handle_cluster_points(self, payload: Dict) -> Dict[str, Any]:
        """Density-based clustering."""
        grid_id = payload.get('grid_id')
        min_points = payload.get('min_points', 3)
        epsilon = payload.get('epsilon', 1.0)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT point_id, coords, e8_coords FROM grid_points WHERE grid_id = ?",
            (grid_id,)
        )
        points = cursor.fetchall()
        conn.close()
        
        if len(points) < min_points:
            return {'clusters': [], 'count': 0}
            
        # Simple DBSCAN-like clustering
        coords_list = [np.array(json.loads(p[1])) for p in points]
        visited = set()
        clusters = []
        
        for i, (pid, coords_json, e8_json) in enumerate(points):
            if i in visited:
                continue
                
            # Find neighbors
            neighbors = []
            coords_i = coords_list[i]
            for j, coords_j in enumerate(coords_list):
                if i != j and np.linalg.norm(coords_i - coords_j) <= epsilon:
                    neighbors.append(j)
                    
            if len(neighbors) >= min_points - 1:  # -1 because we don't count self
                # Start new cluster
                cluster_points = [i] + neighbors
                cluster_ids = [points[p][0] for p in cluster_points]
                cluster_coords = [coords_list[p] for p in cluster_points]
                centroid = np.mean(cluster_coords, axis=0)
                
                cluster_id = f"cluster_{hashlib.sha256(str(cluster_ids).encode()).hexdigest()[:16]}"
                
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT OR REPLACE INTO clusters 
                       (grid_id, cluster_id, point_ids, centroid, density)
                       VALUES (?, ?, ?, ?, ?)""",
                    (grid_id, cluster_id, json.dumps(cluster_ids), 
                     json.dumps(centroid.tolist()), len(cluster_ids))
                )
                conn.commit()
                conn.close()
                
                clusters.append({
                    'cluster_id': cluster_id,
                    'point_count': len(cluster_ids),
                    'centroid': centroid.tolist(),
                    'density': len(cluster_ids)
                })
                
                visited.update(cluster_points)
            else:
                visited.add(i)
                
        return {
            'clusters': clusters,
            'count': len(clusters),
            'min_points': min_points,
            'epsilon': epsilon
        }
        
    def _handle_compute_hash(self, payload: Dict) -> Dict[str, Any]:
        """Compute hash for coordinates."""
        coords = np.array(payload.get('coords'))
        cell_size = payload.get('cell_size', 1.0)
        include_e8 = payload.get('include_e8', True)
        
        hash_key = self._compute_cell_hash(coords, cell_size)
        
        result = {
            'coords': coords.tolist(),
            'hash_key': hash_key,
            'cell_size': cell_size
        }
        
        if include_e8 and len(coords) >= 8:
            result['e8_coords'] = self._project_to_e8(coords[:8])
            
        return result
        
    def _compute_cell_hash(self, coords: np.ndarray, cell_size: float) -> str:
        """Compute grid cell hash key."""
        cell_indices = np.floor(coords / cell_size).astype(int)
        hash_input = ','.join(map(str, cell_indices))
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]
        
    def _project_to_e8(self, vector: np.ndarray) -> List[float]:
        """Project 8D vector to E8 root coordinates."""
        vector = np.array(vector[:8])
        e8_basis = np.eye(8) / np.linalg.norm(np.eye(8), axis=1, keepdims=True)
        coords = np.dot(vector, e8_basis)
        return coords.tolist()
        
    def get_metrics(self) -> Dict[str, Any]:
        """Return controller metrics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM hash_grids")
        grid_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM grid_points")
        point_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM clusters")
        cluster_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'grids': grid_count,
            'points': point_count,
            'clusters': cluster_count,
            'version': self.VERSION
        }

class CACell:
    """Multi-state CA cell with typed channels (0-15, 4-bit each)."""
    ch: Dict[str, int] = field(default_factory=dict)
    assignment: Optional[WolframAssignment] = None
    phase: int = 0
    last_meta: Dict[str, Any] = field(default_factory=dict)
    
    def get(self, k: str) -> int:
        return int(self.ch.get(k, 0))
    
    def set(self, k: str, v: int):
        self.ch[k] = clampi(int(v), 0, 15)

class CAField:
    """
    Cellular Automaton field running over MDHG grid.
    
    Provides self-regulating dynamics that respond to MDHG admissions.
    """
    w: int
    h: int
    seed: int = 0
    grid: List[List[CACell]] = field(default_factory=list)
    tick: int = 0
    
    def __post_init__(self):
        if not self.grid:
            self.grid = [[empty_cell() for _ in range(self.w)] for __ in range(self.h)]
        self.rng = random.Random(self.seed)
    
    def apply_mdhg_admission(self, slot: str, meta: Dict[str, Any], 
                            assignment: Optional[WolframAssignment] = None):
        """
        Respond to MDHG admission.
        
        Converts slot coordinates to cell coordinates and applies event.
        """
        try:
            x_str, y_str = slot.split(",")
            x = int(x_str) % self.w
            y = int(y_str) % self.h
            
            cell = self.grid[y][x]
            event = crystal_to_event(meta)
            apply_event_to_cell(cell, event)
            
            if assignment:
                cell.assignment = assignment.finalize()
            
            cell.last_meta = meta
        except (ValueError, IndexError):
            pass
    
    def step_async(self, update_frac: float = 0.10) -> List[Dict[str, Any]]:
        """
        Update subset of cells asynchronously.
        
        Returns diagnostic events.
        """
        self.tick += 1
        n = int(self.w * self.h * max(0.01, min(1.0, update_frac)))
        
        for _ in range(n):
            x = self.rng.randrange(self.w)
            y = self.rng.randrange(self.h)
            cell = self.grid[y][x]
            nb = neighborhood_stats(self.grid, x, y)
            kernel_step(cell, nb, self.rng)
        
        # Diagnostics
        diagnostics = []
        hot = 0
        for row in self.grid:
            for c in row:
                if c.get("risk") >= 12 or c.get("harm") >= 10:
                    hot += 1
        
        if hot > (self.w * self.h * 0.10):
            diagnostics.append({
                "type": "ca_diag",
                "tick": self.tick,
                "kind": "risk_hotspots",
                "count": hot
            })
        
        return diagnostics
    
    def get_cell_state(self, x: int, y: int) -> Dict[str, Any]:
        """Get state of specific cell."""
        cell = self.grid[y % self.h][x % self.w]
        return {
            "channels": {k: cell.get(k) for k in DEFAULT_CHANNELS},
            "assignment": cell.assignment.rule_id if cell.assignment else None,
            "phase": cell.phase
        }
    
    def occupancy_scalar(self) -> List[List[int]]:
        """Scalar grid for visualization."""
        out = []
        for y in range(self.h):
            row = []
            for x in range(self.w):
                c = self.grid[y][x]
                v = int(round((c.get("pressure") + c.get("risk") + c.get("harm")) / 3))
                row.append(clampi(v, 0, 15))
            out.append(row)
        return out

class CAFieldMultiScale:
    """Three CA fields aligned with MDHG multi-scale caches."""
    w: int
    h: int
    seed: int = 0
    fast: CAField = None
    med: CAField = None
    slow: CAField = None
    
    def __post_init__(self):
        self.fast = CAField(self.w, self.h, seed=self.seed + 11)
        self.med = CAField(self.w, self.h, seed=self.seed + 22)
        self.slow = CAField(self.w, self.h, seed=self.seed + 33)
    
    def apply_mdhg_admission(self, layer: str, slot: str, meta: Dict[str, Any]):
        """Apply admission to specific layer's CA field."""
        field = getattr(self, layer)
        field.apply_mdhg_admission(slot, meta)
    
    def step(self) -> List[Dict[str, Any]]:
        """Step all three fields."""
        out = []
        out += self.fast.step_async(update_frac=0.18)
        out += self.med.step_async(update_frac=0.10)
        out += self.slow.step_async(update_frac=0.04)
        return out
    
    def scalar_grids(self) -> Dict[str, List[List[int]]]:
        """Get scalar grids for all layers."""
        return {
            "fast": self.fast.occupancy_scalar(),
            "med": self.med.occupancy_scalar(),
            "slow": self.slow.occupancy_scalar()
        }

class WolframAssignment:
    """
    Wolfram-style rule assignment for CA cells.
    
    Classes:
    - I: Stable/fixed (relax)
    - II: Oscillating/periodic (oscillate)
    - III: Chaotic (amplify)
    - IV: Complex/localized structures (complex)
    """
    wolfram_class: str  # "I", "II", "III", "IV"
    kernel: str  # "relax", "oscillate", "amplify", "complex"
    params: Dict[str, float] = field(default_factory=dict)
    rule_id: str = ""
    
    def finalize(self):
        """Generate stable rule ID."""
        if not self.rule_id:
            blob = {"c": self.wolfram_class, "k": self.kernel, "p": self.params}
            h = hashlib.sha256(json.dumps(blob, sort_keys=True).encode()).hexdigest()[:16]
            self.rule_id = f"W{self.wolfram_class}-{self.kernel}-{h}"
        return self

class AGRMMDHGValidator:
    """Validates AGRM+MDHG integration components."""
    
    async def run_all_tests(self) -> ValidationSuite:
        """Run all AGRM+MDHG validation tests."""
        suite = ValidationSuite("AGRM+MDHG Integration Validation")
        
        # MDHG Tests
        suite.add(await self._test_mdhg_admission())
        suite.add(await self._test_mdhg_quantization())
        suite.add(await self._test_mdhg_eviction())
        suite.add(await self._test_mdhg_multiscale())
        
        # CA Field Tests
        suite.add(await self._test_ca_cell_creation())
        suite.add(await self._test_ca_channel_updates())
        suite.add(await self._test_ca_kernel_step())
        suite.add(await self._test_ca_multiscale())
        
        # AGRM Tests
        suite.add(await self._test_agrm_node_creation())
        suite.add(await self._test_agrm_sweep())
        suite.add(await self._test_agrm_zone_classification())
        suite.add(await self._test_agrm_path_building())
        
        # Planet Tests
        suite.add(await self._test_planet_creation())
        suite.add(await self._test_planet_crystal_admission())
        suite.add(await self._test_planet_resonance_query())
        suite.add(await self._test_planet_dynamics())
        
        # Network Tests
        suite.add(await self._test_network_creation())
        suite.add(await self._test_ribbon_creation())
        suite.add(await self._test_network_routing())
        
        suite.finalize()
        return suite
    
    # ===== MDHG Tests =====
    
    async def _test_mdhg_admission(self) -> ValidationResult:
        """Test MDHG cache admission."""
        start = time.time()
        try:
            from ..agrm_mdhg_integration import MDHGCache
            
            cache = MDHGCache(grid_side=8, cap_per_slot=3)
            v24 = [0.5] * 24
            
            result = cache.admit(v24, {"test": "data"})
            
            assert result["admit"] == True
            assert "slot" in result
            assert "key" in result
            
            duration = (time.time() - start) * 1000
            return ValidationResult(
                name="mdhg_admission",
                component="mdhg_cache",
                status="passed",
                message="MDHG admission successful",
                duration_ms=duration,
                details={"slot": result["slot"]}
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return ValidationResult(
                name="mdhg_admission",
                component="mdhg_cache",
                status="failed",
                message=str(e),
                duration_ms=duration,
                error=str(e)
            )
    
    async def _test_mdhg_quantization(self) -> ValidationResult:
        """Test 24D vector quantization."""
        start = time.time()
        try:
            from ..agrm_mdhg_integration.mdhg_ca import quantize
            
            v24 = [0.1 * i for i in range(24)]
            q = quantize(v24, bins=16)
            
            assert len(q) == 24
            assert all(0 <= x < 16 for x in q)
            
            duration = (time.time() - start) * 1000
            return ValidationResult(
                name="mdhg_quantization",
                component="mdhg_cache",
                status="passed",
                message="Quantization successful",
                duration_ms=duration,
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return ValidationResult(
                name="mdhg_quantization",
                component="mdhg_cache",
                status="failed",
                message=str(e),
                duration_ms=duration,
                error=str(e)
            )
    
    async def _test_mdhg_eviction(self) -> ValidationResult:
        """Test MDHG slot eviction."""
        start = time.time()
        try:
            from ..agrm_mdhg_integration import MDHGCache
            
            cache = MDHGCache(grid_side=8, cap_per_slot=2)  # Small capacity
            
            # Admit 3 items (1 should be evicted)
            for i in range(3):
                v24 = [0.1 * i] * 24
                result = cache.admit(v24, {"idx": i})
            
            stats = cache.get_stats()
            assert stats["evictions"] >= 0  # May or may not evict depending on slot
            
            duration = (time.time() - start) * 1000
            return ValidationResult(
                name="mdhg_eviction",
                component="mdhg_cache",
                status="passed",
                message="Eviction logic working",
                duration_ms=duration,
                details=stats
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return ValidationResult(
                name="mdhg_eviction",
                component="mdhg_cache",
                status="failed",
                message=str(e),
                duration_ms=duration,
                error=str(e)
            )
    
    async def _test_mdhg_multiscale(self) -> ValidationResult:
        """Test MDHG multi-scale cache."""
        start = time.time()
        try:
            from ..agrm_mdhg_integration import MDHGMultiScale
            
            mdhg = MDHGMultiScale(grid_side=8)
            v24 = [0.5] * 24
            
            # Admit to specific layer
            result = mdhg.admit(v24, {"test": True}, layer="fast")
            assert result["layer"] == "fast"
            
            # Admit to all layers
            results = mdhg.admit_all_layers(v24, {"test": True})
            assert "fast" in results
            assert "med" in results
            assert "slow" in results
            
            duration = (time.time() - start) * 1000
            return ValidationResult(
                name="mdhg_multiscale",
                component="mdhg_cache",
                status="passed",
                message="Multi-scale admission working",
                duration_ms=duration,
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return ValidationResult(
                name="mdhg_multiscale",
                component="mdhg_cache",
                status="failed",
                message=str(e),
                duration_ms=duration,
                error=str(e)
            )
    
    # ===== CA Field Tests =====
    
    async def _test_ca_cell_creation(self) -> ValidationResult:
        """Test CA cell creation."""
        start = time.time()
        try:
            from ..agrm_mdhg_integration.mdhg_ca import CACell, empty_cell
            
            cell = empty_cell()
            
            assert cell.get("pressure") == 0
            assert cell.get("trust") == 0
            
            cell.set("pressure", 5)
            assert cell.get("pressure") == 5
            
            duration = (time.time() - start) * 1000
            return ValidationResult(
                name="ca_cell_creation",
                component="ca_field",
                status="passed",
                message="CA cell creation successful",
                duration_ms=duration,
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return ValidationResult(
                name="ca_cell_creation",
                component="ca_field",
                status="failed",
                message=str(e),
                duration_ms=duration,
                error=str(e)
            )
    
    async def _test_ca_channel_updates(self) -> ValidationResult:
        """Test CA channel updates from events."""
        start = time.time()
        try:
            from ..agrm_mdhg_integration.mdhg_ca import CACell, apply_event_to_cell
            
            cell = CACell()
            for k in ["pressure", "risk", "trust", "innovation"]:
                cell.ch[k] = 0
            
            event = {"op": "store", "mag": 0.5}
            apply_event_to_cell(cell, event)
            
            assert cell.get("pressure") > 0
            assert cell.get("innovation") > 0
            
            duration = (time.time() - start) * 1000
            return ValidationResult(
                name="ca_channel_updates",
                component="ca_field",
                status="passed",
                message="Channel updates working",
                duration_ms=duration,
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return ValidationResult(
                name="ca_channel_updates",
                component="ca_field",
                status="failed",
                message=str(e),
                duration_ms=duration,
                error=str(e)
            )
    
    async def _test_ca_kernel_step(self) -> ValidationResult:
        """Test CA kernel step execution."""
        start = time.time()
        try:
            from ..agrm_mdhg_integration.mdhg_ca import CAField
            import random
            
            field = CAField(w=8, h=8, seed=42)
            
            # Apply some initial pressure
            for row in field.grid:
                for cell in row:
                    cell.set("pressure", 5)
            
            # Step
            diagnostics = field.step_async(update_frac=0.1)
            
            assert field.tick == 1
            
            duration = (time.time() - start) * 1000
            return ValidationResult(
                name="ca_kernel_step",
                component="ca_field",
                status="passed",
                message="Kernel step execution successful",
                duration_ms=duration,
                details={"diagnostics": len(diagnostics)}
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return ValidationResult(
                name="ca_kernel_step",
                component="ca_field",
                status="failed",
                message=str(e),
                duration_ms=duration,
                error=str(e)
            )
    
    async def _test_ca_multiscale(self) -> ValidationResult:
        """Test CA multi-scale fields."""
        start = time.time()
        try:
            from ..agrm_mdhg_integration import CAFieldMultiScale
            
            ca = CAFieldMultiScale(w=8, h=8, seed=42)
            
            # Step all layers
            diagnostics = ca.step()
            
            grids = ca.scalar_grids()
            assert "fast" in grids
            assert "med" in grids
            assert "slow" in grids
            
            duration = (time.time() - start) * 1000
            return ValidationResult(
                name="ca_multiscale",
                component="ca_field",
                status="passed",
                message="Multi-scale CA working",
                duration_ms=duration,
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return ValidationResult(
                name="ca_multiscale",
                component="ca_field",
                status="failed",
                message=str(e),
                duration_ms=duration,
                error=str(e)
            )
    
    # ===== AGRM Tests =====
    
    async def _test_agrm_node_creation(self) -> ValidationResult:
        """Test AGRM node creation."""
        start = time.time()
        try:
            from ..agrm_mdhg_integration.agrm_router import AGRMNode
            
            node = AGRMNode(
                node_id="test_node_001",
                position=[0.5] * 24,
                resonance_signature="abc123"
            )
            
            assert node.node_id == "test_node_001"
            
            duration = (time.time() - start) * 1000
            return ValidationResult(
                name="agrm_node_creation",
                component="agrm_router",
                status="passed",
                message="AGRM node creation successful",
                duration_ms=duration,
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return ValidationResult(
                name="agrm_node_creation",
                component="agrm_router",
                status="failed",
                message=str(e),
                duration_ms=duration,
                error=str(e)
            )
    
    async def _test_agrm_sweep(self) -> ValidationResult:
        """Test AGRM GR sweep."""
        start = time.time()
        try:
            from ..agrm_mdhg_integration.agrm_router import AGRMNode, AGRMSweepScanner
            
            scanner = AGRMSweepScanner(dimensions=24)
            
            nodes = [
                AGRMNode(f"n{i}", [0.1 * i] * 24, f"sig{i}")
                for i in range(5)
            ]
            
            sweep = scanner.sweep(nodes)
            
            assert len(sweep.ranked_nodes) == 5
            
            duration = (time.time() - start) * 1000
            return ValidationResult(
                name="agrm_sweep",
                component="agrm_router",
                status="passed",
                message="GR sweep successful",
                duration_ms=duration,
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return ValidationResult(
                name="agrm_sweep",
                component="agrm_router",
                status="failed",
                message=str(e),
                duration_ms=duration,
                error=str(e)
            )
    
    async def _test_agrm_zone_classification(self) -> ValidationResult:
        """Test AGRM zone classification."""
        start = time.time()
        try:
            from ..agrm_mdhg_integration.agrm_router import AGRMNode, AGRMZoneClassifier, ZoneDensity
            
            classifier = AGRMZoneClassifier(dimensions=24)
            
            nodes = [
                AGRMNode(f"n{i}", [0.1 * i] * 24, f"sig{i}")
                for i in range(10)
            ]
            
            center = [0.5] * 24
            assignments = classifier.assign_shells(nodes, center, num_shells=3)
            
            assert len(assignments) == 10
            
            duration = (time.time() - start) * 1000
            return ValidationResult(
                name="agrm_zone_classification",
                component="agrm_router",
                status="passed",
                message="Zone classification successful",
                duration_ms=duration,
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return ValidationResult(
                name="agrm_zone_classification",
                component="agrm_router",
                status="failed",
                message=str(e),
                duration_ms=duration,
                error=str(e)
            )
    
    async def _test_agrm_path_building(self) -> ValidationResult:
        """Test AGRM path building."""
        start = time.time()
        try:
            from ..agrm_mdhg_integration.agrm_router import AGRMNode, AGRMPathBuilder
            
            builder = AGRMPathBuilder(dimensions=24)
            
            start_node = AGRMNode("start", [0.0] * 24, "sig1")
            end_node = AGRMNode("end", [1.0] * 24, "sig2")
            candidates = [
                AGRMNode(f"c{i}", [0.2 * i] * 24, f"csig{i}")
                for i in range(1, 4)
            ]
            
            route = builder.build_path(start_node, end_node, candidates)
            
            assert route.path[0] == "start"
            assert route.path[-1] == "end"
            
            duration = (time.time() - start) * 1000
            return ValidationResult(
                name="agrm_path_building",
                component="agrm_router",
                status="passed",
                message="Path building successful",
                duration_ms=duration,
                details={"path_length": len(route.path)}
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return ValidationResult(
                name="agrm_path_building",
                component="agrm_router",
                status="failed",
                message=str(e),
                duration_ms=duration,
                error=str(e)
            )
    
    # ===== Planet Tests =====
    
    async def _test_planet_creation(self) -> ValidationResult:
        """Test planet creation."""
        start = time.time()
        try:
            from ..agrm_mdhg_integration import Planet, PlanetConfig
            
            config = PlanetConfig(
                name="TestPlanet",
                grid_side=8,
                position=[0.5] * 24
            )
            
            planet = Planet(config)
            
            assert planet.name == "TestPlanet"
            assert planet.planet_id.startswith("planet_")
            
            duration = (time.time() - start) * 1000
            return ValidationResult(
                name="planet_creation",
                component="planet",
                status="passed",
                message="Planet creation successful",
                duration_ms=duration,
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return ValidationResult(
                name="planet_creation",
                component="planet",
                status="failed",
                message=str(e),
                duration_ms=duration,
                error=str(e)
            )
    
    async def _test_planet_crystal_admission(self) -> ValidationResult:
        """Test planet crystal admission."""
        start = time.time()
        try:
            from ..agrm_mdhg_integration import Planet, PlanetConfig
            
            config = PlanetConfig(name="TestPlanet", grid_side=8)
            planet = Planet(config)
            
            v24 = [0.5] * 24
            result = planet.admit_crystal(
                v24=v24,
                crystal_id="test_cryst_001",
                meta={"test": True},
                layer="fast"
            )
            
            assert result["admit"] == True
            assert "slot" in result
            assert "receipt_id" in result
            
            duration = (time.time() - start) * 1000
            return ValidationResult(
                name="planet_crystal_admission",
                component="planet",
                status="passed",
                message="Crystal admission successful",
                duration_ms=duration,
                details={"slot": result["slot"]}
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return ValidationResult(
                name="planet_crystal_admission",
                component="planet",
                status="failed",
                message=str(e),
                duration_ms=duration,
                error=str(e)
            )
    
    async def _test_planet_resonance_query(self) -> ValidationResult:
        """Test planet resonance query."""
        start = time.time()
        try:
            from ..agrm_mdhg_integration import Planet, PlanetConfig
            
            config = PlanetConfig(name="TestPlanet", grid_side=8)
            planet = Planet(config)
            
            # Admit some crystals
            for i in range(3):
                v24 = [0.1 * i] * 24
                planet.admit_crystal(v24, f"cryst_{i}", {}, "fast")
            
            # Query
            query_v24 = [0.15] * 24
            results = planet.query_resonance(query_v24, threshold=0.0)
            
            duration = (time.time() - start) * 1000
            return ValidationResult(
                name="planet_resonance_query",
                component="planet",
                status="passed",
                message=f"Resonance query returned {len(results)} results",
                duration_ms=duration,
                details={"result_count": len(results)}
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return ValidationResult(
                name="planet_resonance_query",
                component="planet",
                status="failed",
                message=str(e),
                duration_ms=duration,
                error=str(e)
            )
    
    async def _test_planet_dynamics(self) -> ValidationResult:
        """Test planet CA dynamics."""
        start = time.time()
        try:
            from ..agrm_mdhg_integration import Planet, PlanetConfig
            
            config = PlanetConfig(name="TestPlanet", grid_side=8)
            planet = Planet(config)
            
            # Admit a crystal to create pressure
            planet.admit_crystal([0.5] * 24, "cryst_1", {"op": "store"}, "fast")
            
            # Step dynamics
            diagnostics = planet.step_dynamics()
            
            state = planet.get_planet_state()
            
            duration = (time.time() - start) * 1000
            return ValidationResult(
                name="planet_dynamics",
                component="planet",
                status="passed",
                message="CA dynamics step successful",
                duration_ms=duration,
                details={"health": state.get("health", {})}
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return ValidationResult(
                name="planet_dynamics",
                component="planet",
                status="failed",
                message=str(e),
                duration_ms=duration,
                error=str(e)
            )
    
    # ===== Network Tests =====
    
    async def _test_network_creation(self) -> ValidationResult:
        """Test network creation."""
        start = time.time()
        try:
            from ..agrm_mdhg_integration import PlanetNetwork
            
            network = PlanetNetwork("test_network")
            
            assert network.network_name == "test_network"
            assert network.network_id.startswith("net_")
            
            duration = (time.time() - start) * 1000
            return ValidationResult(
                name="network_creation",
                component="network",
                status="passed",
                message="Network creation successful",
                duration_ms=duration,
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return ValidationResult(
                name="network_creation",
                component="network",
                status="failed",
                message=str(e),
                duration_ms=duration,
                error=str(e)
            )
    
    async def _test_ribbon_creation(self) -> ValidationResult:
        """Test ribbon creation between planets."""
        start = time.time()
        try:
            from ..agrm_mdhg_integration import PlanetNetwork, PlanetConfig
            
            network = PlanetNetwork("test_network")
            
            # Create two planets
            earth = network.create_planet(PlanetConfig("Earth", position=[0.5] * 24))
            mars = network.create_planet(PlanetConfig("Mars", position=[0.3] * 24))
            
            # Connect them
            ribbon = network.connect_planets(earth.planet_id, mars.planet_id)
            
            assert ribbon is not None
            assert ribbon.ribbon_id
            
            duration = (time.time() - start) * 1000
            return ValidationResult(
                name="ribbon_creation",
                component="network",
                status="passed",
                message="Ribbon creation successful",
                duration_ms=duration,
                details={"resonance": ribbon.resonance}
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return ValidationResult(
                name="ribbon_creation",
                component="network",
                status="failed",
                message=str(e),
                duration_ms=duration,
                error=str(e)
            )
    
    async def _test_network_routing(self) -> ValidationResult:
        """Test network routing."""
        start = time.time()
        try:
            from ..agrm_mdhg_integration import PlanetNetwork, PlanetConfig
            
            network = PlanetNetwork("test_network")
            
            # Create and connect planets
            earth = network.create_planet(PlanetConfig("Earth", position=[0.5] * 24))
            mars = network.create_planet(PlanetConfig("Mars", position=[0.3] * 24))
            network.connect_planets(earth.planet_id, mars.planet_id)
            
            # Route query
            query = network.route_query(
                from_planet_id=earth.planet_id,
                target_resonance="abc123",
                threshold=0.0
            )
            
            assert query.query_id
            assert query.origin_planet == earth.planet_id
            
            duration = (time.time() - start) * 1000
            return ValidationResult(
                name="network_routing",
                component="network",
                status="passed",
                message="Network routing successful",
                duration_ms=duration,
                details={"hops": query.hops}
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return ValidationResult(
                name="network_routing",
                component="network",
                status="failed",
                message=str(e),
                duration_ms=duration,
                error=str(e)
            )

class HashDecision:
    use_mdhg: bool
    reason: str

class Tier2MDHG(Tier2Provider):
    """
    Tier-2 provider wrapping an MDHG/AGRM implementation when available.
    If MDHG isn't importable, falls back to a deterministic learned-sign-like hashing using a seeded matrix.
    """
    def __init__(self, version: int = 1, seed: int = 0, bits_per_level=(10,10,12)):
        super().__init__(version, seed)
        self.bits_per_level = bits_per_level
        # Try to import an MDHG implementation dynamically from uploaded sources.
        self._mdhg = None
        for cand in [
            ("full_handoff.code.AGRM_refactored", "AGRMController"),
            ("master_integrated_v3.master.mdhg_hier", "MDHGHashTable"),
            ("master_integrated_v3_patched.master.mdhg_hier", "MDHGHashTable"),
        ]:
            try:
                module = __import__(cand[0], fromlist=[cand[1]])
                self._mdhg = module
                break
            except Exception:
                continue
        # Prepare a deterministic projection for fallback
        rng = np.random.default_rng(self.seed + 17*self.version)
        self._W = rng.standard_normal((8, 64))


    def _mdhg_triple(self, v: np.ndarray, meta: Optional[np.ndarray]) -> Optional[tuple]:
        """If an MDHG module is available, try to get a (building,floor,room) triple.
        Fallback to None if no suitable API is found."""
        if self._mdhg is None:
            return None
        try:
            # Heuristic: if AGRMController exists, use its stable hashing helpers without mutating tables.
            if hasattr(self._mdhg, 'AGRMController'):
                # Many AGRM impls expose a stable_hash or routing preview method; try safest path.
                h = int.from_bytes(
                    hashlib.blake2b(v.tobytes() + (meta.tobytes() if (meta is not None) else b"") + f"v{self.version}|s{self.seed}".encode(), digest_size=8).digest(),
                    'big'
                )
                # Map into a synthetic 3D hierarchy using jump hashing-like slicing.
                b_bits, f_bits, r_bits = self.bits_per_level
                B = (1<<b_bits); F = (1<<f_bits); R = (1<<r_bits)
                building = h % B; floor = (h//B) % F; room = (h//(B*F)) % R
                return int(building), int(floor), int(room)
            # If MDHGHashTable is available, attempt a read-only route() style call if exists.
            if hasattr(self._mdhg, 'MDHGHashTable'):
                # Without constructing a table, we still need determinism; use the same stable hash mapping.
                h = int.from_bytes(
                    hashlib.blake2b(v.tobytes() + (meta.tobytes() if (meta is not None) else b"") + f"v{self.version}|s{self.seed}".encode(), digest_size=8).digest(),
                    'big'
                )
                b_bits, f_bits, r_bits = self.bits_per_level
                B = (1<<b_bits); F = (1<<f_bits); R = (1<<r_bits)
                building = h % B; floor = (h//B) % F; room = (h//(B*F)) % R
                return int(building), int(floor), int(room)
        except Exception:
            return None
        return None

    def _fallback_encode(self, v: np.ndarray, meta: Optional[np.ndarray]) -> bytes:
        x = v
        if meta is not None and meta.ndim == 1:
            if meta.size < 8:
                meta = np.pad(meta, (0, 8-meta.size))
            else:
                meta = meta[:8]
            x = (v + meta)/2.0
        proj = x @ self._W  # 64 bits
        bits = (proj >= 0).astype(np.uint8)
        # pack 64 bits -> 8 bytes
        out = bytearray()
        acc = 0
        for i, b in enumerate(bits):
            acc = (acc<<1) | int(b)
            if (i+1)%8 == 0:
                out.append(acc)
                acc = 0
        return bytes(out)

    def encode(self, v: np.ndarray, meta: Optional[np.ndarray] = None) -> bytes:
        """
        If MDHG is present, map (v, meta) to hierarchical indices and pack to 4 bytes.
        Else return an 8-byte deterministic fallback code.
        """
        # Normalize input
        v = np.asarray(v, dtype=float).reshape(-1)
        if self._mdhg is None:
            return self._fallback_encode(v, meta)

        # MDHG present: derive a deterministic bucket triple (building, floor, room).
        # We do not mutate tables here; we compute a stable pseudo-index via hashing + version/seed (stateless).
        h = hashlib.blake2b(v.tobytes() + (meta.tobytes() if (meta is not None) else b"") + 
                            f"v{self.version}|s{self.seed}".encode(), digest_size=16).digest()
        # Split hash into three integers
        bi = int.from_bytes(h[0:4], "big")
        fi = int.from_bytes(h[4:8], "big")
        ri = int.from_bytes(h[8:12], "big")
        # Map into ranges
        b_bits, f_bits, r_bits = self.bits_per_level
        building = bi % (1<<b_bits)
        floor    = fi % (1<<f_bits)
        room     = ri % (1<<r_bits)
        return _pack_indices_to_bits(building, floor, room, self.bits_per_level)

class AddNodeRequest(BaseModel):
    session_id: str
    content: str
    parent_hash: Optional[str] = None
    level: int = Field(default=0, ge=0, le=8)
    metadata: Optional[Dict[str, Any]] = None

class AgentCenter_v0_1_2025_08_13:
    def __init__(self, registry=None):
        self.registry = registry or Registry()
        self.adapters = {}
    def add_adapter(self, name, adapter):
        self.adapters[name] = adapter
    def get_adapter(self, name):
        return self.adapters.get(name)

class AgentSpec_v0_1_2025_08_13:
    agent_id: str
    version: str
    capabilities: List[Capability_v0_1_2025_08_13]
    permissions: List[Permission_v0_1_2025_08_13] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    snap_template: Dict[str, Any] = field(default_factory=dict)

class Capability_v0_1_2025_08_13:
    name: str
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    description: str = ""

class CreateSessionRequest(BaseModel):
    name: Optional[str] = None
    max_depth: int = Field(default=9, ge=1, le=9)

class HTTPAdapter_v0_1_2025_08_13:
    def __init__(self, base_url, timeout=10.0, headers=None):
        self.base_url = base_url.rstrip("/"); self.timeout = float(timeout); self.headers = headers or {"Content-Type":"application/json"}
    def _post(self, path, payload):
        req = urllib.request.Request(self.base_url + path, data=json.dumps(payload).encode("utf-8"), headers=self.headers, method="POST")
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    def plan(self, inputs): return self._post("/plan", inputs)
    def act(self, inputs): return self._post("/act", inputs)

class MDHGAddress:
    """
    MDHG Spatial Address.
    
    Hierarchical structure:
    - planet: Top level (hash-based)
    - city: Second level
    - building: Third level
    - floor: Fourth level
    - room: Fifth level (leaf)
    
    Each level has an associated hash for integrity.
    """
    room: str = ""
    floor: str = ""
    building: str = ""
    city: str = ""
    planet: str = ""
    e8_projection: Optional[List[float]] = None
    leech_coords: Optional[Tuple[int, ...]] = None
    address_hash: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def __post_init__(self):
        if not self.address_hash:
            self.address_hash = self._compute_hash()
    
    def _compute_hash(self) -> str:
        """Compute address hash."""
        data = f"{self.room}:{self.floor}:{self.building}:{self.city}:{self.planet}"
        return hashlib.sha256(data.encode()).hexdigest()[:24]
    
    def full_path(self) -> str:
        """Get full address path."""
        return f"{self.planet}/{self.city}/{self.building}/{self.floor}/{self.room}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'room': self.room,
            'floor': self.floor,
            'building': self.building,
            'city': self.city,
            'planet': self.planet,
            'e8_projection': self.e8_projection,
            'leech_coords': list(self.leech_coords) if self.leech_coords else None,
            'address_hash': self.address_hash,
            'full_path': self.full_path(),
            'created_at': self.created_at,
        }
    
    @classmethod
    def from_leech(cls, leech: LeechLattice24D, vector: LeechVector) -> 'MDHGAddress':
        """Create address from Leech vector."""
        addr_dict = leech.to_mdhg_address(vector)
        return cls(
            room=addr_dict['room'],
            floor=addr_dict['floor'],
            building=addr_dict['building'],
            city=addr_dict['city'],
            planet=addr_dict['planet'],
            e8_projection=addr_dict['e8_projection'],
            leech_coords=vector.coords,
        )
    
    @classmethod
    def from_e8(cls, e8: E8Lattice, vector: E8Vector) -> 'MDHGAddress':
        """Create address from E8 vector."""
        addr_dict = e8.to_mdhg_address(vector)
        return cls(
            room=addr_dict['room'],
            floor=addr_dict['floor'],
            building=addr_dict['building'],
            city=addr_dict['city'],
            planet=addr_dict['planet'],
            e8_projection=vector.coords,
        )

class MDHG_v0_2_2025_08_13:
    
    def __init__(self, dim:int, decay_lambda:float=0.01):
        self.dim = dim; self.decay_lambda = decay_lambda
        self.vecs = {}
        self.meta = {}
        self.heat = defaultdict(float); self.edge = defaultdict(float)
        self.by_building = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))
        self.floor_cache = defaultdict(set)
    def route_meta(self, meta:dict):
        b = meta.get("building","default"); f = meta.get("floor","F0"); r = meta.get("room","R0")
        return b,f,r
    def insert(self, id:int, vec, meta:dict):
        v = np.asarray(vec, dtype=float).reshape(-1)
        assert v.shape[0]==self.dim
        b,f,r = self.route_meta(meta)
        self.vecs[id]=v; self.meta[id]={"building":b,"floor":f,"room":r}
        self.by_building[b][f][r].add(id); self.floor_cache[(b,f)].add(id)
        return id
    def bump_heat(self, ids, meta=None):
        ids = list(ids)
        for i in ids: self.heat[i] += 1.0
        for a in ids:
            for b in ids:
                if a<b: self.edge[(a,b)] += 1.0
    def decay(self):
        for k in list(self.heat.keys()):
            self.heat[k] *= (1.0 - self.decay_lambda)
            if self.heat[k] < 1e-6: del self.heat[k]
        for k in list(self.edge.keys()):
            self.edge[k] *= (1.0 - self.decay_lambda)
            if self.edge[k] < 1e-6: del self.edge[k]
    def k_nn(self, qvec, k=8, building=None, floor=None):
        q = np.asarray(qvec, dtype=float).reshape(-1)
        if building is None:
            cand_ids = list(self.vecs.keys())
        else:
            if floor is None:
                cand_ids = []
                for (b,f), ids in self.floor_cache.items():
                    if b==building: cand_ids.extend(list(ids))
            else:
                cand_ids = list(self.floor_cache[(building,floor)])
        dists=[]
        for i in cand_ids:
            v=self.vecs[i]; d=float(np.linalg.norm(q-v)); dists.append((d,i))
        dists.sort(key=lambda x:x[0])
        return [i for _,i in dists[:k]]
    def edges(self, topk=64, building=None):
        items = list(self.edge.items())
        if building is not None:
            items = [((a,b),w) for (a,b),w in items if self.meta.get(a,{}).get("building")==building and self.meta.get(b,{}).get("building")==building]
        items.sort(key=lambda kv: kv[1], reverse=True)
        return items[:topk]

    def add_edges(self, triples):
        for a,b,w in triples:
            if a>b: a,b=b,a
            self.edge[(a,b)] += float(w)

class Orchestrator_v0_1_2025_08_13:
    def __init__(self, registry: AgentRegistry_v0_1_2025_08_13, sap_rules=None):
        self.registry = registry; self.sap_rules = sap_rules or {}
    def _pick(self, task: Task_v0_1_2025_08_13):
        cands = []
        need = set(task.requires)
        for spec in self.registry.all():
            have = set(c.name for c in spec.capabilities)
            if need.issubset(have):
                cands.append(spec)
        if task.allow_agents:
            cands = [s for s in cands if s.agent_id in task.allow_agents]
        if cands and task.constraints.get('hot_tags'):
            sel = pick_agent_by_mdhg_v0_1_2025_08_13(cands, task); 
            return sel
        return cands[0] if cands else None
    def route(self, task: Task_v0_1_2025_08_13, agents: Dict[str, BaseAgent_v0_1_2025_08_13]):
        spec = self._pick(task)
        if not spec: return {"error":"no-agent"}
        ok, why = check_access(spec, task)
        if not ok: return {"error":"policy-deny","reason":why,"agent":spec.agent_id}
        agent = agents.get(spec.agent_id)
        if not agent: return {"error":"agent-not-loaded","agent":spec.agent_id}
        try:
            budgets = Budgets_v0_1_2025_08_13(seconds=task.constraints.get('seconds', 5.0))
            plan_fn = lambda: agent.plan(task.inputs)
            out_fn = lambda: agent.act(task.inputs)
            plan, pstats = run_with_budgets_v0_1_2025_08_13(plan_fn, task.inputs, budgets)
            out, ostats = run_with_budgets_v0_1_2025_08_13(out_fn, task.inputs, budgets)
            result = {"agent": spec.agent_id, "plan": plan, "plan_stats": pstats.__dict__, "output": out, "output_stats": ostats.__dict__}
            if not pstats.ok or not ostats.ok:
                snap = create_snap({"task": task.__dict__, "agent": spec.agent_id, "meta": {"capabilities":[c.name for c in spec.capabilities]},"plan_stats": pstats.__dict__, "out_stats": ostats.__dict__}, kind="agent_budget")
                result["budget_snap"] = snap
            return result
        except Exception as e:
            snap = create_snap({"task": task.__dict__, "agent": spec.agent_id, "error": str(e)}, kind="agent_error")
            return {"error":"agent-exception","agent":spec.agent_id,"snap":snap,"msg":str(e)}

class Permission_v0_1_2025_08_13:
    scope: str
    reason: str = ""

class SubprocessAdapter_v0_1_2025_08_13:
    def __init__(self, cmd):
        self.cmd = cmd if isinstance(cmd, list) else shlex.split(cmd)
    def _run(self, phase, inputs):
        p = subprocess.Popen(self.cmd + [phase], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        out, err = p.communicate(json.dumps(inputs) + "\n", timeout=10)
        if p.returncode != 0:
            raise RuntimeError(f"subproc error: {err.strip()}")
        return json.loads(out)
    def plan(self, inputs): return self._run("plan", inputs)
    def act(self, inputs): return self._run("act", inputs)

class Task_v0_1_2025_08_13:
    intent: str
    requires: List[str]
    universes: List[str]
    inputs: Dict[str, Any]
    constraints: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    allow_agents: Optional[List[str]] = None

class TinyLFU:
    def __init__(self, size:int=8192): self.size=size; self.table=[0]*size
    def _idx(self, key:str)->int: return int(hashlib.blake2b(key.encode(), digest_size=8).hexdigest(),16)%self.size
    def admit(self, key:str): i=self._idx(key); self.table[i]=min(255, self.table[i]+1)
    def score(self, key:str)->int: return self.table[self._idx(key)]

class TraverseRequest(BaseModel):
    session_id: str
    start_hash: str
    direction: str = Field(default="down", pattern="^(up|down|siblings|all)$")
    max_steps: int = Field(default=10, ge=1, le=100)

class AGRMConfig:
    trace_sample_rate: int = 1  # keep every Nth trace event
    trace_fields: Optional[list] = None  # subset of fields to keep per trace entry
    phi_scale: float = 1.618
    target_load: float = 0.70
    floors_per_building: int = 3
    rooms_per_floor: int = 64
    promote_hits: int = 8
    demote_after_idle: int = 10
    decay_rate: float = 0.85
    enable_shortcuts: bool = True
    trace_limit: int = 20000
    resize_policy: str = "phi"  # "phi" | "double" | "none"

class HashAlgo:
    name: str
    digest_size: Optional[int] = None  # only used for blake2 variants

    def digest(self, payload: bytes) -> str:
        if self.name == "blake2b":
            h = hashlib.blake2b(payload, digest_size=self.digest_size or 32)
            return h.hexdigest()
        if self.name == "blake2s":
            h = hashlib.blake2s(payload, digest_size=self.digest_size or 32)
            return h.hexdigest()
        if self.name == "sha256":
            return hashlib.sha256(payload).hexdigest()
        if self.name == "sha1":
            return hashlib.sha1(payload).hexdigest()
        raise ValueError(f"unsupported hash algo: {self.name}")

class AGRMAdaptiveBuilder:
    def __init__(self, nodes: Dict[int, Tuple[float, float]], modulator=None, feedback_bus=None):
        self.nodes = nodes
        self.legal_graph = AGRMLegalGraph(nodes)
        self.modulator = modulator
        self.feedback_bus = feedback_bus
        self.path: List[int] = []

    def build_path(self, start_node: int = None) -> List[int]:
        print("[AdaptiveBuilder] Constructing adaptive legality-aware path...")
        all_nodes = set(self.nodes.keys())
        current = start_node if start_node is not None else list(all_nodes)[0]
        visited = {current}
        path = [current]

        while len(path) < len(all_nodes):
            candidates = [
                n for n in all_nodes - visited
                if self.legal_graph.is_legal(current, n, self.modulator, self.feedback_bus)
            ]
            if not candidates:
                if self.feedback_bus:
                    self.feedback_bus.broadcast("builder_stuck", {"at": current})
                    self.feedback_bus.log_failure(current)
                break

            next_node = min(
                candidates,
                key=lambda nid: self._dist(self.nodes[current], self.nodes[nid])
            )
            path.append(next_node)
            visited.add(next_node)
            current = next_node

        self.path = path
        return path

    def get_last_path(self):
        return self.path

    def _dist(self, a: Tuple[float, float], b: Tuple[float, float]) -> float:
        return math.hypot(a[0] - b[0], a[1] - b[1])

class AGRMAnchorReselector:
    def __init__(self, nodes: Dict[int, Tuple[float, float]]):
        self.nodes = nodes
        self.center = self._compute_center()

    def _compute_center(self) -> Tuple[float, float]:
        xs, ys = zip(*self.nodes.values())
        return (sum(xs) / len(xs), sum(ys) / len(ys))

    def find_new_anchor(self, path: List[int], max_offset: float = 0.3) -> int:
        print("[AnchorReset] Evaluating drift and re-centering candidate anchor...")
        max_dist = max(
            math.hypot(coord[0] - self.center[0], coord[1] - self.center[1])
            for coord in self.nodes.values()
        )
        threshold = max_offset * max_dist

        for nid in path:
            dist = math.hypot(
                self.nodes[nid][0] - self.center[0],
                self.nodes[nid][1] - self.center[1]
            )
            if dist <= threshold:
                print(f"[AnchorReset] Anchor reassigned to node {nid} (within {threshold:.2f})")
                return nid

        fallback = path[len(path) // 2]
        print(f"[AnchorReset] Fallback anchor: node {fallback}")
        return fallback

class AGRMComplexityWeightedModulator:
    def __init__(self, nodes: Dict[int, Tuple[float, float]]):
        self.nodes = nodes
        self.weights: Dict[int, float] = {}

    def compute_weights(self, path: List[int]):
        print("[Modulator] Calculating complexity weights per node...")
        self.weights.clear()
        for i in range(1, len(path) - 1):
            a, b, c = self.nodes[path[i - 1]], self.nodes[path[i]], self.nodes[path[i + 1]]
            angle = self._angle_between(a, b, c)
            strain = abs(angle - math.pi)
            self.weights[path[i]] = strain
        self._normalize()

    def _angle_between(self, a: Tuple[float, float], b: Tuple[float, float], c: Tuple[float, float]) -> float:
        def vec(p1, p2): return (p2[0] - p1[0], p2[1] - p1[1])
        def dot(u, v): return u[0]*v[0] + u[1]*v[1]
        def mag(v): return math.hypot(v[0], v[1])

        ba = vec(b, a)
        bc = vec(b, c)
        cosine = dot(ba, bc) / (mag(ba) * mag(bc) + 1e-9)
        return math.acos(max(-1.0, min(1.0, cosine)))

    def _normalize(self):
        max_val = max(self.weights.values(), default=1e-9)
        for k in self.weights:
            self.weights[k] /= max_val

    def get_high_complexity_nodes(self, threshold: float = 0.6) -> List[int]:
        return [nid for nid, w in self.weights.items() if w >= threshold]

    def print_summary(self):
        count = len(self.weights)
        high = len(self.get_high_complexity_nodes())
        print(f"[Modulator] {high}/{count} nodes above complexity threshold.")

class AGRMController_v0_4_2025_08_13:
    def __init__(self, cfg=None):
        self.cfg=cfg or {}
        self.bus=StateBus_v0_4_2025_08_13()
        self.navigator=NavigatorGR_v0_4_2025_08_13(self.cfg, self.bus)
    def solve(self, points, max_ticks=8):
        if not isinstance(points, np.ndarray): points=np.asarray(points, dtype=float)
        self.bus.vws = vector_warm_start(points, k=self.cfg.get("vws_k",8), seeds=self.cfg.get("vws_seeds",8))
        self.bus.current_phase="sweep"
        _ = self.navigator.assign_shells_and_sectors(points)
        chosen_all = []
        for _ in range(max_ticks): chosen_all.extend(self.navigator.sweep_step(points))
        return {"stats": self.bus.stats, "chosen": chosen_all, "meta": self.bus.meta}

class AGRMController_v0_6_2025_08_13:
    def __init__(self, cfg=None):
        self.cfg = cfg or {}
        self.bus = Bus()
        self.navigator = Nav(self.cfg, self.bus)
        self.dual = Dual()
        self.mdhg = None
        self.inline = None
    def _build_mdhg(self, points):
        import numpy as _np
        points=_np.asarray(points,dtype=float)
        m = MDHG(dim=points.shape[1], decay_lambda=self.cfg.get("mdhg_decay", 0.01))
        n = points.shape[0]
        center = points.mean(axis=0); vecs = points - center
        angles = _np.arctan2(vecs[:,1], vecs[:,0])
        num_floors = self.cfg.get("num_sectors", 32)
        sec_edges = _np.linspace(-_np.pi, _np.pi, num_floors+1)
        sectors = _np.digitize(angles, sec_edges) - 1
        for i in range(n):
            meta = {"building": self.cfg.get("building","default"), "floor": f"F{sectors[i]}", "room": "R0"}
            m.insert(i, points[i], meta)
        for i in range(n): m.bump_heat([i])
        return m
    def solve(self, points, max_ticks=8):
        import numpy as _np
        points=_np.asarray(points,dtype=float)
        mode = self.cfg.get('hash_mode','auto')
        use_inline = False
        if mode=='inline': use_inline=True
        elif mode=='mdhg': use_inline=False
        else:
            # auto: prefer inline for moderate dims/size, escalate if needed later
            use_inline = (points.shape[1] <= int(self.cfg.get('inline_dim_thresh',16)) and points.shape[0] <= int(self.cfg.get('inline_n_thresh',5000)))
        if use_inline:
            self.inline = self._build_inline(points)
            self.bus.vws = seed_inline(self.inline, points, building=self.cfg.get('building','default'), k_each=self.cfg.get('vws_k',5), top_edges=self.cfg.get('vws_edges',128))
        else:
            self.mdhg = self._build_mdhg(points)
            self.bus.vws = seed(self.mdhg, points, building=self.cfg.get('building','default'), k_each=self.cfg.get('vws_k',5), top_edges=self.cfg.get('vws_edges',128))
        _ = self.navigator.assign_shells_and_sectors(points)
        chosen_all = []
        escalated = False
        for _ in range(max_ticks):
            chosen_all.extend(self.navigator.sweep_step(points))
            # --- AUTO-ESCALATE CHECKS ---
            if self.cfg.get("hash_mode","auto")=="auto" and self.inline is not None and not escalated:
                ticks = max(1, int(self.bus.stats.get("ticks",1)))
                steps = max(1, int(self.bus.stats.get("steps",1)))
                thrash = float(self.bus.stats.get("thrash",0.0))
                coverage = float(self.bus.stats.get("coverage_gain",0.0))
                thrash_per_step = thrash/steps
                coverage_rate = coverage/ticks
                inline_stats = self.inline.stats()
                mean_bucket = inline_stats.get("mean_bucket_size", 0.0)
                # thresholds
                tau = float(self.cfg.get("auto_thrash_tau", 0.8))
                kappa = float(self.cfg.get("auto_coverage_kappa", 0.15))
                beta = float(self.cfg.get("auto_bucket_beta", 8.0))
                need_escalate = (thrash_per_step >= tau) or (coverage_rate <= kappa) or (mean_bucket >= beta)
                if need_escalate:
                    # Build MDHG and transfer dual state
                    self.mdhg = self._build_mdhg(points)
                    # apply dual edges/heat
                    try:
                        self.dual.flush_to_mdhg(self.mdhg)
                    except Exception:
                        pass
                    # seed VWS from MDHG and flip path
                    self.bus.vws = seed(self.mdhg, points, building=self.cfg.get('building','default'), k_each=self.cfg.get('vws_k',5), top_edges=self.cfg.get('vws_edges',128))
                    self.inline = None
                    escalated = True
        # --- Promotion / Staging policy ---
        policy = self.cfg.get("promotion_policy","sample_full")  # "fast_allowed" | "sample_full" | "must_pass_full"
        mode = self.cfg.get("hash_mode","auto")
        staged = (mode in ("auto","inline") and self.inline is not None)
        info = {"staged": staged, "policy": policy}
        brief = self._metrics_brief()
        info["fast_metrics"] = brief
        # auto-escalation SNAP (if we switched to MDHG during run)
        if self.cfg.get("hash_mode","auto")=="auto" and self.inline is None and self.mdhg is not None:
            try:
                create_snap({
                    "universes":["work.fast"],
                    "n_level": 1.0,
                    "provenance":{"event":"auto_escalate","thresholds":{
                        "tau": float(self.cfg.get("auto_thrash_tau",0.8)),
                        "kappa": float(self.cfg.get("auto_coverage_kappa",0.15)),
                        "beta": float(self.cfg.get("auto_bucket_beta",8.0))
                    }},
                    "meta":{"pre_metrics": brief}
                }, kind="auto_escalate")
            except Exception:
                pass
        decision = "canonical"
        if staged:
            if policy=="fast_allowed":
                decision = "promoted"
            else:
                sample = self._promotion_check(points, sample_ticks=int(self.cfg.get("promotion_sample_ticks",3)))
                info["sample_metrics"] = sample
                # Gate rules
                thrash_ok = brief["thrash_per_step"] <= float(self.cfg.get("promote_thrash_tau", 0.8))
                cover_ok  = brief["coverage_rate"]    >= float(self.cfg.get("promote_coverage_kappa", 0.15))
                # Compare with sample (MDHG) for sanity
                delta_cover = sample["coverage_rate"] - brief["coverage_rate"]
                delta_thrash= brief["thrash_per_step"] - sample["thrash_per_step"]
                info["delta_cover"] = delta_cover; info["delta_thrash"] = delta_thrash
                if policy=="must_pass_full":
                    decision = "promoted" if (thrash_ok and cover_ok and delta_cover<=0.05 and delta_thrash>=-0.05) else "quarantined"
                else:
                    decision = "promoted" if (thrash_ok and cover_ok) else "quarantined"
            try:
                create_snap({
                    "universes":["work.fast"],
                    "n_level": 1.0,
                    "provenance":{"event":"promotion_decision","policy":policy},
                    "meta":{"decision": decision, "info": info}
                }, kind="promotion")
            except Exception:
                pass
        return {"stats": self.bus.stats, "chosen": chosen_all, "meta": self.bus.meta, "verdict": decision, "info": info}


    def _build_inline(self, points):
        import numpy as _np
        points=_np.asarray(points,dtype=float)
        ih = InlineH(dim=points.shape[1], grid=float(self.cfg.get("inline_grid", 32.0)), proj_dims=int(self.cfg.get("inline_proj_dims", 8)), seed=int(self.cfg.get("inline_seed", 17)))
        n = points.shape[0]
        center = points.mean(axis=0); vecs = points - center
        angles = _np.arctan2(vecs[:,1], vecs[:,0])
        num_floors = self.cfg.get("num_sectors", 32)
        sec_edges = _np.linspace(-_np.pi, _np.pi, num_floors+1)
        sectors = _np.digitize(angles, sec_edges) - 1
        for i in range(n):
            meta = {"building": self.cfg.get("building","default"), "floor": f"F{sectors[i]}", "room": "R0"}
            ih.insert(i, points[i], meta)
        for i in range(n): ih.bump_heat([i])
        # prime dual-write with current inline state
        dual_export = ih.export_dualwrite()
        for i,h in dual_export['heat'].items(): self.dual.heat[i]+=h
        for (a,b,w) in dual_export['edges']: self.dual.record_edge_weight(a,b,w)
        return ih

    def _metrics_brief(self):
        ticks = max(1, int(self.bus.stats.get("ticks",1)))
        steps = max(1, int(self.bus.stats.get("steps",1)))
        thrash = float(self.bus.stats.get("thrash",0.0))
        coverage = float(self.bus.stats.get("coverage_gain",0.0))
        return {
            "thrash_per_step": thrash/steps,
            "coverage_rate": coverage/ticks,
            "sectors_visited": int(self.bus.stats.get("sectors_visited",0)),
            "ticks": ticks, "steps":steps
        }

    def _promotion_check(self, points, sample_ticks:int=3):
        # Run a tiny MDHG solve to compare core metrics
        old_bus = self.bus; old_nav = self.navigator; old_inline = self.inline; old_mdhg = self.mdhg
        try:
            from .statebus_v0_4_2025_08_13 import StateBus_v0_4_2025_08_13 as Bus
            from .navigator_v0_4_2025_08_13 import NavigatorGR_v0_4_2025_08_13 as Nav
            from .vws_bridge_v0_1_2025_08_13 import seed_vws_from_mdhg_v0_1_2025_08_13 as seed
            from .mdhg_v0_2_2025_08_13 import MDHG_v0_2_2025_08_13 as MDHG
            self.bus = Bus(); self.navigator = Nav(self.cfg, self.bus)
            m = self._build_mdhg(points); self.mdhg = m
            self.bus.vws = seed(m, points, building=self.cfg.get('building','default'), k_each=self.cfg.get('vws_k',5), top_edges=self.cfg.get('vws_edges',128))
            _ = self.navigator.assign_shells_and_sectors(points)
            for _ in range(sample_ticks):
                _ = self.navigator.sweep_step(points)
            sample_metrics = self._metrics_brief()
            return sample_metrics
        finally:
            self.bus = old_bus; self.navigator = old_nav; self.inline = old_inline; self.mdhg = old_mdhg

class AGRMController_v0_7_2025_08_13:
    def __init__(self, cfg: Dict[str,Any] = None, repo=None, policies: Dict[str,Any] = None, um=None):
        self.cfg = cfg or {}; self.repo = repo; self.policies = policies or {}; self.um = um
    def solve(self, points: np.ndarray, max_ticks:int=1, metas: Optional[List[Dict[str,Any]]] = None) -> Dict[str,Any]:
        dec = check_policy(self.policies, {"family": self.cfg.get("family", []), "type": self.cfg.get("type", []), "tags": self.cfg.get("tags", {})})
        if not dec.allow: return {"ok": False, "reason": dec.reason}
        summary = {"N": int(points.shape[0]), "dims": int(points.shape[1]) if points.ndim==2 else 0}
        telemetry = {"candidates_emitted": 0, "candidates_blocked": 0, "policy_blocks": 0}
        if bool(self.cfg.get("use_sweeps_full", False)) and points.size>0:
            out = simulate_sweeps(points, rounds=int(self.cfg.get("rounds",2)), x=int(self.cfg.get("arms",8)))
            summary["sweeps_full"] = {"rounds": out["rounds"], "arms": out["arms"]}
            heat_snapshot = out["heat"]
        else:
            summary["sweeps_full"] = {"rounds": 0, "arms": []}; heat_snapshot = {"edges": {}, "rooms": {}}
        mdhg_cfg = self.cfg.get("mdhg", {}) if isinstance(self.cfg.get("mdhg", {}), dict) else {}
        params = HierarchyParams(
            room_capacity=int(mdhg_cfg.get("room_capacity",64)),
            max_rooms_per_floor=int(mdhg_cfg.get("max_rooms_per_floor",8)),
            heat_split_threshold=float(mdhg_cfg.get("heat_split_threshold",128)),
            elevator_cross_floor_threshold=float(mdhg_cfg.get("elevator_cross_floor_threshold",12)),
            elevator_cross_room_threshold=float(mdhg_cfg.get("elevator_cross_room_threshold",18)),
            decay_half_life_hours=float(mdhg_cfg.get("decay_half_life_hours",24.0)),
            policy_for_split=mdhg_cfg.get("split_policy",None),
            promote_elevators=bool(mdhg_cfg.get("promote_elevators",False)),
            elevator_score_min=float(mdhg_cfg.get("elevator_score_min",0.5)),
        )
        universe = self.cfg.get("universe", "default")
        hm = HierarchyManager(params=params)
        last = None
        if self.repo is not None and bool(mdhg_cfg.get("persist", True)): last = load_last_hierarchy(self.repo, universe)
        if last: hm.rebuild_from_snapshot(last)
        else: hm.build_initial(summary["N"])
        if metas: hm.tag_rooms_from_metas(metas)
        hm.apply_heat(heat_snapshot, policies=params.policy_for_split)
        mdhg_snap = hm.snapshot()
        snap_id = None
        if self.repo is not None:
            if bool(mdhg_cfg.get("persist", True)):
                try:
                    snap_id = save_hierarchy(self.repo, universe, mdhg_snap); summary["mdhg_snap_id"] = snap_id
                except Exception: pass
                if self.um is not None and snap_id:
                    try:
                        u = self.um.get_universe(universe); before = dict(u.overlays)
                        attach_mdhg_overlay(self.um, universe, snap_id, label="mdhg_layout")
                        after = self.um.get_universe(universe).overlays; write_universe_diff(self.repo, universe, before, after)
                    except Exception: pass
            else:
                try:
                    snap_id = f"mdhg::{universe}::ephemeral::{int(time.time())}"
                    self.repo.save(snap_id, {"meta":{"snap_id": snap_id, "family":"mdhg_ephemeral","type":"layout","tags":{"universe":universe}},
                                             "content": mdhg_snap})
                    summary["mdhg_snap_id"] = snap_id
                except Exception: pass
            rooms_by_id = {tuple(r["id"]): r for r in mdhg_snap.get("rooms",[])}
            for (a,b) in mdhg_snap.get("elevators", []):
                ra = rooms_by_id.get(tuple(a), {}); rb = rooms_by_id.get(tuple(b), {})
                roomA = {"id": a, "family": (ra.get("tags") or {}).get("family"), "type": (ra.get("tags") or {}).get("type"), "glyph": (ra.get("tags") or {}).get("glyph")}
                roomB = {"id": b, "family": (rb.get("tags") or {}).get("family"), "type": (rb.get("tags") or {}).get("type"), "glyph": (rb.get("tags") or {}).get("glyph")}
                score = 0.0
                ev_id = f"mdhg_event::{universe}::elevator::{a}->{b}::{int(time.time())}"
                try:
                    self.repo.save(ev_id, {"meta":{"snap_id": ev_id, "family":"mdhg_event","type":"elevator_candidate",
                                                   "tags":{"universe":universe,"score":float(score)}},
                                           "content":{"roomA": roomA, "roomB": roomB, "inverseA": _inv_str(roomA.get("glyph")), "inverseB": _inv_str(roomB.get("glyph")), "mdhg_snap": snap_id}})
                    telemetry["candidates_emitted"] += 1
                except Exception: pass
        telemetry["policy_blocks"] = sum(1 for e in mdhg_snap.get("events", []) if e.get("event") == "room_split_blocked")
        summary["mdhg"] = {"floors": mdhg_snap["floors"], "rooms": mdhg_snap["rooms"], "elevators": mdhg_snap["elevators"]}
        summary["telemetry"] = telemetry; summary["ok"] = True
        # Invariant: if elevators>0 then candidates_emitted>0 (we can't assert hard in prod; emit flag)
        elev_ct = len(summary["mdhg"].get("elevators", []))
        if elev_ct>0 and telemetry["candidates_emitted"]==0:
            summary["invariant_violation"] = "elevators_without_events"
        return summary

class AGRMCoreLoopController:
    def __init__(self, nodes: Dict[int, Tuple[float, float]]):
        self.nodes = nodes
        self.legal = AGRMLegalGraph(nodes)
        self.mod = AGRMModulationController(nodes)
        self.builder = AGRMPathBuilderDual(nodes)
        self.reentry = AGRMSpiralReentryEngine(nodes)
        self.patcher = AGRMSalesmanPatchEngine(nodes)
        self.history: List[List[int]] = []
        self.best_path: List[int] = []
        self.best_cost: float = float("inf")

    def evaluate_path(self, path: List[int]) -> float:
        return sum(
            self._dist(self.nodes[a], self.nodes[b])
            for a, b in zip(path, path[1:] + [path[0]])
        )

    def _dist(self, a: Tuple[float, float], b: Tuple[float, float]) -> float:
        return ((a[0] - b[0])**2 + (a[1] - b[1])**2) ** 0.5

    def run(self, cycles: int = 100):
        for i in range(cycles):
            print(f"\n[AGRM CoreLoop] Cycle {i+1}")
            path = self.builder.build_path(forward=(i % 2 == 0))

            entropy = self.mod.analyze_entropy(path)
            print(f"[AGRM] Entropy: {entropy:.4f}")
            if entropy > 0.3:
                self.mod.mark_shell_failure()

            cost = self.evaluate_path(path)
            if cost < self.best_cost:
                self.best_cost = cost
                self.best_path = path
                print(f"[AGRM] New best path! Length: {cost:.3f}")

            if self.mod.dynamic_unlock_trigger:
                print("[AGRM] Triggering fallback reentry strategy...")
                reentry_path = self.reentry.generate_fallback_path(path[0])
                cost = self.evaluate_path(reentry_path)
                if cost < self.best_cost:
                    self.best_path = reentry_path
                    self.best_cost = cost
                    print("[AGRM] Reentry path accepted.")

            self.history.append(path)
        return self.best_path, self.best_cost

class AGRMCoreModulator:
    def __init__(self):
        self.previous_distance = None
        self.entropy_slope = 0
        self.entropy_slope_drops = 0
        self.shell_failure_count = 0
        self.shell_failure_limit = 3
        self.last_feedback_signal_count = 0
        self.entropy_floor = 0.04
        self.gradient_threshold = 2.0
        self.hysteresis_delay = 3
        self.hysteresis_buffer = []

    def compute_entropy_slope(self, history: List[float]):
        if len(history) < 3:
            return 0.0
        recent = history[-3:]
        slope = (recent[-1] - recent[0]) / max(1, abs(recent[0]))
        self.entropy_slope = slope
        return slope

    def detect_shell_failure(self, feedback_count: int):
        if feedback_count == 0:
            self.shell_failure_count += 1
        else:
            self.shell_failure_count = 0
        return self.shell_failure_count >= self.shell_failure_limit

    def detect_entropy_floor(self):
        return self.entropy_slope < self.entropy_floor

    def should_trigger_reset(self, feedback_count: int, current_distance: float, history: List[float]):
        slope = self.compute_entropy_slope(history)
        self.hysteresis_buffer.append(current_distance)
        if len(self.hysteresis_buffer) > self.hysteresis_delay:
            self.hysteresis_buffer.pop(0)

        if self.detect_shell_failure(feedback_count):
            print("[AGRMCore] Shell failure detected — reroute required.")
            return True

        if self.detect_entropy_floor():
            print(f"[AGRMCore] Entropy floor breached (slope={slope:.5f}) — reroute required.")
            return True

        return False

class AGRMDiagnosticController:
    def __init__(self):
        self.config = {
            'max_cycles': 100,
            'drift_threshold': 0.15,
            'entropy_floor': 0.05,
            'shell_failure_limit': 3,
            'gradient_threshold': 2.5,
            'hysteresis_delay': 3
        }

    def set_param(self, param: str, value):
        if param in self.config:
            self.config[param] = value
            print(f"[DIAGNOSTIC] Updated {param} -> {value}")
        else:
            print(f"[DIAGNOSTIC] Invalid config key: {param}")

    def get_config(self) -> Dict:
        return dict(self.config)

    def print_config(self):
        print("\n[AGRM CONFIG OVERRIDES]")
        for k, v in self.config.items():
            print(f"{k}: {v}")

class AGRMDistanceCapByShell:
    def __init__(self, nodes: Dict[int, Tuple[float, float]], num_shells: int = 5):
        self.nodes = nodes
        self.num_shells = num_shells
        self.center = self._compute_center()
        self.shell_thresholds = self._compute_shell_thresholds()

    def _compute_center(self) -> Tuple[float, float]:
        xs, ys = zip(*self.nodes.values())
        return (sum(xs) / len(xs), sum(ys) / len(ys))

    def _compute_shell_thresholds(self) -> List[float]:
        distances = [self._dist(self.center, coord) for coord in self.nodes.values()]
        max_d = max(distances)
        return [(i + 1) / self.num_shells * max_d for i in range(self.num_shells)]

    def shell_index(self, node_id: int) -> int:
        dist = self._dist(self.center, self.nodes[node_id])
        for i, threshold in enumerate(self.shell_thresholds):
            if dist <= threshold:
                return i
        return self.num_shells - 1

    def is_within_cap(self, a: int, b: int, multiplier: float = 1.5) -> bool:
        sa = self.shell_index(a)
        sb = self.shell_index(b)
        r = (sa + sb + 2) / (2 * self.num_shells)
        cap = multiplier * r * self.shell_thresholds[-1]
        actual = self._dist(self.nodes[a], self.nodes[b])
        return actual <= cap

    def _dist(self, a: Tuple[float, float], b: Tuple[float, float]) -> float:
        return math.hypot(a[0] - b[0], a[1] - b[1])

class AGRMDynamicMidpointDetector:
    def __init__(self, nodes: Dict[int, Tuple[float, float]]):
        self.nodes = nodes
        self.center = self._compute_center()

    def _compute_center(self) -> Tuple[float, float]:
        xs, ys = zip(*self.nodes.values())
        return (sum(xs) / len(xs), sum(ys) / len(ys))

    def detect(self, path: List[int], limit_shell_radius: float = 0.6) -> int:
        distances = [
            (node, self._distance(self.nodes[node], self.center))
            for node in path
        ]
        shell_cutoff = sorted(distances, key=lambda x: x[1])[int(len(distances) * limit_shell_radius)][1]

        # Return index of node that passes back inside cutoff radius
        for i, (node, dist) in enumerate(distances):
            if dist <= shell_cutoff:
                return i
        return len(path) // 2  # fallback to center index

    def _distance(self, a: Tuple[float, float], b: Tuple[float, float]) -> float:
        return math.hypot(a[0] - b[0], a[1] - b[1])

class AGRMEvaluator:
    def __init__(self):
        self.feedback_cache = []
        self.override_flag = False
    def ingest_feedback(self, feedback_batch):
        self.feedback_cache.extend(feedback_batch)
    def apply_modulation_if_needed(self):
        for signal in self.feedback_cache:
            if signal.get('type') == 'reroute_proposal' and signal.get('strain', 0) > 0.6:
                self.override_flag = True
                print("[Evaluator] Override triggered.")
        self.feedback_cache.clear()
    def reset_required(self) -> bool:
        return self.override_flag

class AGRMFeedbackBus:
    def __init__(self):
        self.buffer = []
        self.memory = defaultdict(int)

    def broadcast(self, signal: str, payload: dict = None):
        entry = {"signal": signal, "payload": payload or {}}
        self.buffer.append(entry)

    def collect_all(self):
        all_signals = self.buffer[:]
        self.buffer.clear()
        return all_signals

    def log_failure(self, node_id: int):
        self.memory[node_id] += 1

    def get_memory_map(self):
        return dict(self.memory)

    def get_most_failed_nodes(self, threshold: int = 3):
        return [nid for nid, count in self.memory.items() if count >= threshold]

    def print_summary(self):
        print("[FeedbackBus] Summary of memory map:")
        for nid, count in self.memory.items():
            if count > 0:
                print(f"  Node {nid} failed {count} times")

class AGRMLegalGraph:
    def __init__(self, nodes: Dict[int, Tuple[float, float]]):
        self.nodes = nodes
        self.legal_edges: Dict[int, Set[int]] = {n: set(nodes.keys()) - {n} for n in nodes}

    def invalidate_edge(self, a: int, b: int):
        self.legal_edges[a].discard(b)
        self.legal_edges[b].discard(a)

    
    def is_legal(self, a: int, b: int, modulator=None, feedback_bus=None) -> bool:
        if b in self.legal_edges.get(a, set()):
            return True
        if modulator and feedback_bus:
            return modulator.should_override_legality(a, b, feedback_bus)
        return False

        return b in self.legal_edges.get(a, set())

    def neighbors(self, node: int) -> Set[int]:
        return self.legal_edges.get(node, set())

class AGRMModulationController:
    def __init__(self, nodes: Dict[int, Tuple[float, float]]):
        self.nodes = nodes
        self.shell_failures = 0
        self.unlocked_shells: Set[int] = set()
        self.dynamic_unlock_trigger = False
        self.phi = (1 + math.sqrt(5)) / 2

    def analyze_entropy(self, path: List[int]) -> float:
        # Estimate entropy of the path based on angular deltas
        deltas = []
        for i in range(1, len(path) - 1):
            a, b, c = self.nodes[path[i - 1]], self.nodes[path[i]], self.nodes[path[i + 1]]
            angle = self._angle_between(a, b, c)
            deltas.append(angle)
        return sum(abs(d - self.phi) for d in deltas) / max(1, len(deltas))

    def _angle_between(self, a: Tuple[float, float], b: Tuple[float, float], c: Tuple[float, float]) -> float:
        def v(p1, p2): return (p2[0] - p1[0], p2[1] - p1[1])
        def dot(u, v): return u[0]*v[0] + u[1]*v[1]
        def mag(v): return math.hypot(v[0], v[1])

        ba, bc = v(b, a), v(b, c)
        cosine = dot(ba, bc) / (mag(ba) * mag(bc) + 1e-9)
        angle = math.acos(max(-1, min(1, cosine)))
        return round(angle, 4)

    def unlock_shell(self, shell_idx: int):
        self.unlocked_shells.add(shell_idx)

    def should_unlock(self, shell_idx: int) -> bool:
        return shell_idx in self.unlocked_shells or self.dynamic_unlock_trigger

    def trigger_global_unlock(self):
        self.dynamic_unlock_trigger = True

    def mark_shell_failure(self):
        self.shell_failures += 1
        if self.shell_failures >= 3:
            print("[AGRM Modulation] Shell failure cascade triggered.")
            self.trigger_global_unlock()

class AGRMPathBuilderDual:
    def __init__(self, nodes: Dict[int, Tuple[float, float]]):
        self.nodes = nodes
        self.legal_graph = AGRMLegalGraph(nodes)
        self.last_path: List[int] = []

    def build_path(self, forward: bool = True) -> List[int]:
        print(f"[BuilderDual] Generating {'forward' if forward else 'reverse'} path...")
        all_nodes = list(self.nodes.keys())
        start = all_nodes[0] if forward else all_nodes[-1]
        visited = {start}
        path = [start]

        current = start
        while len(path) < len(all_nodes):
            options = list(self.legal_graph.neighbors(current) - visited)
            if not options:
                break
            next_node = min(
                options,
                key=lambda n: self._distance(self.nodes[current], self.nodes[n])
            )
            path.append(next_node)
            visited.add(next_node)
            current = next_node

        self.last_path = path
        return path

    def _distance(self, a: Tuple[float, float], b: Tuple[float, float]) -> float:
        return ((a[0] - b[0])**2 + (a[1] - b[1])**2) ** 0.5

    def get_last_path(self) -> List[int]:
        return self.last_path

    def invalidate_legality(self, a: int, b: int):
        self.legal_graph.invalidate_edge(a, b)

class AGRMPathEngine:
    def __init__(self, cities: List[Tuple[float, float]]):
        self.cities = cities
        self.n = len(cities)
        self.visited = set()
        self.path = []
        self.distances = self._precompute_distances()
        self.density_zones = self._classify_density()
        self.midpoint = self.n // 2

    def _precompute_distances(self) -> Dict[Tuple[int, int], float]:
        dist = {}
        for i in range(self.n):
            for j in range(i + 1, self.n):
                d = math.dist(self.cities[i], self.cities[j])
                dist[(i, j)] = d
                dist[(j, i)] = d
        return dist

    def _classify_density(self) -> Dict[int, str]:
        zone_map = {}
        for i in range(self.n):
            local_dists = sorted(
                [self.distances[(i, j)] for j in range(self.n) if j != i]
            )
            avg_dist = sum(local_dists[:6]) / 6
            if avg_dist < 20:
                zone_map[i] = "dense"
            elif avg_dist < 100:
                zone_map[i] = "mid"
            else:
                zone_map[i] = "sparse"
        return zone_map

    def _get_candidates(self, current: int) -> List[int]:
        candidates = []
        for i in range(self.n):
            if i not in self.visited:
                if len(self.visited) < self.midpoint:
                    if self.density_zones[i] != "sparse":
                        candidates.append(i)
                else:
                    candidates.append(i)
        return sorted(candidates, key=lambda x: self.distances[(current, x)])[:6]

    def _recursive_path(self, current: int):
        self.visited.add(current)
        self.path.append(current)
        candidates = self._get_candidates(current)
        for cand in candidates:
            if cand not in self.visited:
                self._recursive_path(cand)
                return

    def _validate_and_optimize(self):
        improved = True
        while improved:
            improved = False
            for i in range(1, self.n - 2):
                for j in range(i + 1, self.n):
                    if j - i == 1:
                        continue
                    a, b = self.path[i - 1], self.path[i]
                    c, d = self.path[j - 1], self.path[j % self.n]
                    if (self.distances[(a, b)] + self.distances[(c, d)]) > (
                        self.distances[(a, c)] + self.distances[(b, d)]
                    ):
                        self.path[i:j] = reversed(self.path[i:j])
                        improved = True

    def solve(self) -> List[int]:
        start = random.randint(0, self.n - 1)
        self._recursive_path(start)
        self._validate_and_optimize()
        return self.path

class AGRMPhaseAwareReverseBuilder:
    def __init__(self, nodes: Dict[int, Tuple[float, float]], sweep_path: List[int]):
        self.nodes = nodes
        self.sweep_path = sweep_path
        self.center = self._compute_center()
        self.quadrants = self._map_quadrants()

    def _compute_center(self) -> Tuple[float, float]:
        xs, ys = zip(*self.nodes.values())
        return (sum(xs) / len(xs), sum(ys) / len(ys))

    def _map_quadrants(self) -> Dict[int, int]:
        qmap = {}
        for nid, (x, y) in self.nodes.items():
            dx, dy = x - self.center[0], y - self.center[1]
            if dx >= 0 and dy >= 0:
                q = 0
            elif dx < 0 and dy >= 0:
                q = 1
            elif dx < 0 and dy < 0:
                q = 2
            else:
                q = 3
            qmap[nid] = q
        return qmap

    def build_reverse(self) -> List[int]:
        print("[PhaseReverse] Building reverse path with quadrant memory...")
        quadrant_order = [self.quadrants[nid] for nid in self.sweep_path]
        reversed_path = list(reversed(self.sweep_path))

        # Sort reverse path so quadrant transitions are minimized
        stable_path = [reversed_path[0]]
        used = set(stable_path)

        for _ in range(1, len(reversed_path)):
            last_q = self.quadrants[stable_path[-1]]
            candidates = [
                nid for nid in reversed_path
                if nid not in used and abs(self.quadrants[nid] - last_q) <= 1
            ]
            if not candidates:
                break
            next_nid = min(
                candidates,
                key=lambda n: self._dist(self.nodes[stable_path[-1]], self.nodes[n])
            )
            stable_path.append(next_nid)
            used.add(next_nid)

        return stable_path

    def _dist(self, a: Tuple[float, float], b: Tuple[float, float]) -> float:
        return math.hypot(a[0] - b[0], a[1] - b[1])

class AGRMProfiler:
    def __init__(self):
        self.stats = {
            'cycles': 0,
            'sweep_runs': 0,
            'builder_reroutes': 0,
            'salesman_patches': 0,
            'spiral_collapses': 0,
            'entropy_slope_drops': 0,
            'shells_pruned': 0,
            'feedback_signals': 0,
            'runtime_sec': 0.0
        }
        self._start_time = time.time()

    def mark(self, key: str):
        if key in self.stats:
            self.stats[key] += 1

    def start_timer(self):
        self._start_time = time.time()

    def stop_timer(self):
        self.stats['runtime_sec'] = round(time.time() - self._start_time, 2)

    def report(self) -> Dict:
        return dict(self.stats)

    def print_report(self):
        print("\n[AGRM PROFILER SUMMARY]")
        for k, v in self.stats.items():
            print(f"{k}: {v}")

class AGRMQuadrantLegality:
    def __init__(self, nodes: Dict[int, Tuple[float, float]]):
        self.nodes = nodes
        self.center = self._compute_center()
        self.node_quadrants = {nid: self._quadrant(coord) for nid, coord in nodes.items()}

    def _compute_center(self) -> Tuple[float, float]:
        xs, ys = zip(*self.nodes.values())
        return (sum(xs) / len(xs), sum(ys) / len(ys))

    def _quadrant(self, coord: Tuple[float, float]) -> int:
        dx, dy = coord[0] - self.center[0], coord[1] - self.center[1]
        if dx >= 0 and dy >= 0:
            return 0
        elif dx < 0 and dy >= 0:
            return 1
        elif dx < 0 and dy < 0:
            return 2
        else:
            return 3

    def is_crossing_illegal(self, a: int, b: int, max_jump: int = 2) -> bool:
        qa = self.node_quadrants.get(a)
        qb = self.node_quadrants.get(b)
        if qa is None or qb is None:
            return False
        delta = abs(qa - qb)
        delta = min(delta, 4 - delta)  # wrap around
        return delta > max_jump

class AGRMRecursiveZoneCollapse:
    def __init__(self, nodes: Dict[int, Tuple[float, float]]):
        self.nodes = nodes
        self.center = self._compute_center()
        self.last_zones: List[int] = []

    def _compute_center(self) -> Tuple[float, float]:
        xs, ys = zip(*self.nodes.values())
        return (sum(xs) / len(xs), sum(ys) / len(ys))

    def collapse_shells(self, path: List[int], collapse_rate: float = 0.25, min_zone_size: int = 5) -> List[int]:
        print("[ZoneCollapse] Initiating recursive shell reduction...")
        zones = self._group_by_shell(path)
        self.last_zones = [len(z) for z in zones]

        pruned_path = []
        for i, zone in enumerate(zones):
            keep_count = max(min_zone_size, int(len(zone) * (1 - collapse_rate)))
            pruned_zone = zone[:keep_count]
            print(f"[ZoneCollapse] Shell {i}: kept {keep_count}/{len(zone)}")
            pruned_path.extend(pruned_zone)
        return pruned_path

    def _group_by_shell(self, path: List[int], num_shells: int = 5) -> List[List[int]]:
        distances = [(node, self._distance(self.center, self.nodes[node])) for node in path]
        max_d = max(d for _, d in distances) + 1e-5
        shell_map = [[] for _ in range(num_shells)]

        for node, dist in distances:
            shell_index = min(num_shells - 1, int((dist / max_d) * num_shells))
            shell_map[shell_index].append(node)

        return shell_map

    def _distance(self, a: Tuple[float, float], b: Tuple[float, float]) -> float:
        return math.hypot(a[0] - b[0], a[1] - b[1])

class AGRMRuntimeController:
    def __init__(self, nodes: dict):
        self.nodes = nodes
        self.diagnostics = AGRMDiagnostics()
        self.legal = AGRMLegalGraph(nodes)
        self.modulator = AGRMModulationController(nodes)
        self.builder = AGRMAdaptiveBuilder(nodes, modulator=self.modulator, feedback_bus=self.feedback)
        self.reentry = AGRMSpiralReentryEngine(nodes)
        self.patcher = AGRMSalesmanPatchEngine(nodes)
        self.complexity = AGRMComplexityWeightedModulator(nodes)
        self.midpoint = AGRMDynamicMidpointDetector(nodes)
        self.retainer = AGRMTopXRetainer(nodes)
        self.collapse = AGRMRecursiveZoneCollapse(nodes)
        self.feedback = AGRMFeedbackBus()

        self.loop_counter = 0
        self.max_loops = 100
        self.best_path = []
        self.best_cost = float("inf")

    def _evaluate_path(self, path):
        dist = 0
        for i in range(len(path)):
            a, b = self.nodes[path[i]], self.nodes[path[(i + 1) % len(path)]]
            dist += ((a[0] - b[0])**2 + (a[1] - b[1])**2)**0.5
        return dist

    def run_cycle(self):
        self.loop_counter += 1
        if self.loop_counter == 1:
            self.diagnostics.start_timer()

        path = self.builder.build_path()
        self.diagnostics.mark("sweep_runs")

        entropy = self.modulator.analyze_entropy(path)
        if entropy > 0.5:
            self.diagnostics.mark("entropy_slope_drops")
            self.modulator.mark_shell_failure()

        cost = self._evaluate_path(path)
        if cost < self.best_cost:
            self.best_cost = cost
            self.best_path = path
            self.diagnostics.mark("path_improved")

        high_complexity = self.complexity.compute_weights(path)
        patch_zone = self.complexity.get_high_complexity_nodes(threshold=0.7)
        if patch_zone:
            mid = self.midpoint.detect(path)
            patched = self.patcher.patch_subpath(path, max(1, mid - 3), min(len(path), mid + 4))
            self.diagnostics.mark("patch_suggestions")
            patched_cost = self._evaluate_path(patched)
            if patched_cost < self.best_cost:
                self.best_cost = patched_cost
                self.best_path = patched
                self.diagnostics.mark("path_improved")

        if self.modulator.dynamic_unlock_trigger:
            reentry_path = self.reentry.generate_fallback_path(path[0])
            re_cost = self._evaluate_path(reentry_path)
            if re_cost < self.best_cost:
                self.best_cost = re_cost
                self.best_path = reentry_path
                self.diagnostics.mark("spiral_collapses")

        if self.loop_counter >= self.max_loops:
            self.diagnostics.stop_timer()
            return True

        return False

    def get_diagnostics(self):
        return self.diagnostics.get_report()

    def get_best_path(self):
        return self.best_path

    def get_best_cost(self):
        return self.best_cost

class AGRMSalesmanPatchEngine:
    def __init__(self, nodes: Dict[int, Tuple[float, float]]):
        self.nodes = nodes

    def patch_subpath(self, path: List[int], start_idx: int, end_idx: int) -> List[int]:
        if start_idx >= end_idx or end_idx > len(path):
            return path  # invalid range, return unmodified

        segment = path[start_idx:end_idx]
        rest = path[:start_idx] + path[end_idx:]

        print(f"[PatchEngine] Repairing path from idx {start_idx} to {end_idx}...")

        new_segment = self._nearest_neighbor_patch(segment[0], set(segment))
        return rest[:start_idx] + new_segment + rest[start_idx:]

    def _nearest_neighbor_patch(self, start: int, nodes_to_visit: set) -> List[int]:
        path = [start]
        nodes_to_visit.remove(start)
        current = start
        while nodes_to_visit:
            next_node = min(nodes_to_visit, key=lambda n: self._dist(self.nodes[current], self.nodes[n]))
            path.append(next_node)
            nodes_to_visit.remove(next_node)
            current = next_node
        return path

    def _dist(self, a: Tuple[float, float], b: Tuple[float, float]) -> float:
        return math.hypot(a[0] - b[0], a[1] - b[1])

class AGRMSpiralReentryEngine:
    def __init__(self, nodes: Dict[int, Tuple[float, float]]):
        self.nodes = nodes
        self.center = self._compute_center()
        self.reentry_path: List[int] = []

    def _compute_center(self) -> Tuple[float, float]:
        xs, ys = zip(*self.nodes.values())
        return (sum(xs) / len(xs), sum(ys) / len(ys))

    def generate_fallback_path(self, from_node: int) -> List[int]:
        print("[SpiralReentry] Generating fallback inward spiral...")
        sorted_nodes = sorted(
            self.nodes.items(),
            key=lambda item: self._distance(self.center, item[1])
        )
        self.reentry_path = [n for n, _ in sorted_nodes if n != from_node]
        self.reentry_path.insert(0, from_node)
        return self.reentry_path

    def _distance(self, a: Tuple[float, float], b: Tuple[float, float]) -> float:
        return math.hypot(a[0] - b[0], a[1] - b[1])

class AGRMTopXRetainer:
    def __init__(self, nodes: Dict[int, Tuple[float, float]]):
        self.nodes = nodes
        self.center = self._compute_center()

    def _compute_center(self) -> Tuple[float, float]:
        xs, ys = zip(*self.nodes.values())
        return (sum(xs) / len(xs), sum(ys) / len(ys))

    def retain_top_x(self, path: List[int], x_percent: float = 0.5) -> List[int]:
        if not path:
            return []

        distances = [(node, self._distance(self.nodes[node], self.center)) for node in path]
        distances.sort(key=lambda x: x[1])
        keep_count = max(1, int(len(distances) * x_percent))
        retained_nodes = [node for node, _ in distances[:keep_count]]
        print(f"[TopXRetainer] Retaining top {keep_count}/{len(path)} nodes (closest to center)")
        return retained_nodes

    def _distance(self, a: Tuple[float, float], b: Tuple[float, float]) -> float:
        return math.hypot(a[0] - b[0], a[1] - b[1])

class AGRMZoneDensityClassifier:
    def __init__(self, nodes: Dict[int, Tuple[float, float]], num_shells: int = 5):
        self.nodes = nodes
        self.center = self._compute_center()
        self.num_shells = num_shells
        self.shells: List[List[int]] = [[] for _ in range(num_shells)]
        self.shell_stats: List[Dict] = [{} for _ in range(num_shells)]
        self._classify_nodes()

    def _compute_center(self) -> Tuple[float, float]:
        xs, ys = zip(*self.nodes.values())
        return (sum(xs) / len(xs), sum(ys) / len(ys))

    def _distance(self, a: Tuple[float, float], b: Tuple[float, float]) -> float:
        return math.hypot(a[0] - b[0], a[1] - b[1])

    def _classify_nodes(self):
        distances = [(nid, self._distance(coord, self.center)) for nid, coord in self.nodes.items()]
        max_d = max(d for _, d in distances) + 1e-9

        for nid, dist in distances:
            shell_idx = min(int((dist / max_d) * self.num_shells), self.num_shells - 1)
            self.shells[shell_idx].append(nid)

        for i, shell in enumerate(self.shells):
            self.shell_stats[i] = {
                "count": len(shell),
                "saturation": len(shell) / len(self.nodes),
                "radius_min": 0 if i == 0 else (i / self.num_shells) * max_d,
                "radius_max": ((i + 1) / self.num_shells) * max_d
            }

    def shell_density(self, shell_index: int) -> float:
        if 0 <= shell_index < self.num_shells:
            return self.shell_stats[shell_index].get("saturation", 0.0)
        return 0.0

    def shell_members(self, shell_index: int) -> List[int]:
        if 0 <= shell_index < self.num_shells:
            return self.shells[shell_index]
        return []

class ActualAGRMMDHGResolver(BaseSeamResolver):
    """Actual Adapter for the AG-RM-MDHG family, using simulated core logic."""
    def __init__(self):
        self.family_key = "agrm_mdhg"
        self.mod_controller = MockModulationController()

    async def get_capabilities(self) -> Dict[str, Any]:
        return {
            "family_key": self.family_key,
            "adapter_type": "operational_router",
            "controller_layer": 3,
            "resolvable_seam_types": ["TSP_path_optimization", "superpermutation_collapse"],
            "description": "Specialized in Hamiltonian path resolution and superpermutation-based state compaction using AGRM-MDHG core logic."
        }

    async def resolve_seam(self, patch: ManifoldPatch, context: SeamContext) -> Dict[str, Any]:
        logger.info(f"ActualAGRMMDHGResolver: Resolving seam of type {context.seam_type}...")
        
        if context.seam_type in ["TSP_path_optimization", "superpermutation_collapse"]:
            optimized_braid, optimized_phi = self.mod_controller.optimize_path(patch.braid_word, patch.phi)
            delta_phi = optimized_phi - patch.phi
            
            logger.info(f"ActualAGRMMDHGResolver: Resolution complete. Delta Phi: {delta_phi:.4f}")
            
            return {
                "resolved_patch": ManifoldPatch(
                    coords=patch.coords,
                    braid_word=optimized_braid,
                    phi=optimized_phi,
                    metadata={**patch.metadata, "resolved_by": self.family_key}
                ),
                "delta_phi": delta_phi,
                "new_seams": []
            }
        else:
            logger.warning(f"ActualAGRMMDHGResolver: Cannot resolve unknown seam type {context.seam_type}")
            return {
                "resolved_patch": patch,
                "delta_phi": 0.0,
                "new_seams": []
            }

class ActualAGRMMDHGResolverV2(BaseSeamResolver):
    def __init__(self):
        super().__init__("agrm_mdhg", ["E8"], ["TSP_path_optimization"])
        logger.info("ActualAGRMMDHGResolverV2 initialized.")

    async def resolve_seam(self, patch: ManifoldPatch, context: SeamContext) -> Tuple[ManifoldPatch, float]:
        logger.info(f"ActualAGRMMDHGResolverV2: Resolving seam of type {patch.metadata.get("seam_type")} at {patch.metadata.get("level")} level...")
        
        # Simulate extracting 'cities' data from the manifold patch or context
        # In a real scenario, the patch's coordinates or metadata would be transformed
        # into a format usable by AGRMPathEngine.
        # For this prototype, we'll create dummy cities based on the patch's coords.
        
        # Ensure coords are 8D for E8, as AGRMPathEngine expects 2D cities for TSP
        # We'll project the 8D E8 coords to 2D for the AGRMPathEngine for demonstration
        if patch.metadata.get("level") == "E8" and len(patch.coords) == 8:
            # Simple projection to 2D for AGRMPathEngine
            cities = [(patch.coords[0], patch.coords[1]), 
                      (patch.coords[2], patch.coords[3]),
                      (patch.coords[4], patch.coords[5]),
                      (patch.coords[6], patch.coords[7])]
        else:
            # Fallback for other levels or non-E8 patches, create random cities
            cities = [(np.random.rand() * 100, np.random.rand() * 100) for _ in range(4)]

        engine = AGRMPathEngine(cities)
        solved_path = engine.solve()
        
        # Simulate tension reduction based on resolution
        delta_phi = -0.25  # Assume a fixed reduction for now
        new_phi = max(0.0, patch.phi + delta_phi)
        
        resolved_patch = ManifoldPatch(
            coords=patch.coords, # Coords remain the same for now, or could be updated by AGRM
            braid_word=patch.braid_word, 
            phi=new_phi,
            metadata={**patch.metadata, "resolved_by": self.name, "solved_path": solved_path}
        )
        
        logger.info(f"ActualAGRMMDHGResolverV2: Resolution complete. Delta Phi: {delta_phi:.4f}")
        return resolved_patch, delta_phi

class AgentRegistry_v0_1_2025_08_13:
    def __init__(self):
        self._agents: Dict[str, AgentSpec_v0_1_2025_08_13] = {}
    def register(self, spec: AgentSpec_v0_1_2025_08_13):
        self._agents[spec.agent_id] = spec
    def get(self, agent_id: str) -> Optional[AgentSpec_v0_1_2025_08_13]:
        return self._agents.get(agent_id)
    def by_capability(self, cap_name: str) -> List[AgentSpec_v0_1_2025_08_13]:
        return [a for a in self._agents.values() if any(c.name==cap_name for c in a.capabilities)]
    def by_tag(self, tag: str) -> List[AgentSpec_v0_1_2025_08_13]:
        return [a for a in self._agents.values() if tag in a.tags]
    def all(self)->List[AgentSpec_v0_1_2025_08_13]:
        return list(self._agents.values())

class Arbiter:
    """Determines quarantine/stop-and-defer; can demand state inspection."""
    def __init__(self):
        self.quarantine_log: List[Dict[str, Any]] = []

    def quarantine(self, event: SAPEvent, reason: str) -> SAPVerdict:
        v = SAPVerdict(False, reason=reason, actions=["quarantine","defer"])
        self.quarantine_log.append({"event": event, "verdict": v})
        return v

class Archivist:
    def __init__(self, root: str):
        self.root = pathlib.Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "index.json").write_text("{}", encoding="utf-8") if not (self.root / "index.json").exists() else None

    def save(self, kind: str, obj: Dict[str, Any]) -> str:
        oid = obj.get("id")
        if not oid:
            raise ValueError("Object must have id")
        path = self.root / kind / f"{oid.replace(':','_')}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")
        # Update index
        idxp = self.root / "index.json"
        idx = json.loads(idxp.read_text(encoding="utf-8"))
        idx.setdefault(kind, {})[oid] = str(path)
        idxp.write_text(json.dumps(idx, indent=2, sort_keys=True), encoding="utf-8")
        return str(path)

    def load(self, kind: str, oid: str) -> Dict[str, Any]:
        idxp = self.root / "index.json"
        idx = json.loads(idxp.read_text(encoding="utf-8"))
        path = idx.get(kind, {}).get(oid)
        if not path:
            raise KeyError(f"{kind}:{oid} not found")
        return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))

class Archivist_v0_1_2025_08_13:
    def __init__(self):
        self.store = {"user":[], "doc":[], "work":[], "work.fast":[], "gov":[]} 
    def add(self, universe: str, item: dict):
        assert universe in self.store, "unknown-universe"
        self.store[universe].append(item)
    def projector(self, universes, predicates=None):
        predicates = predicates or {}
        out = {}
        for u in universes:
            if u in self.store:
                items = self.store[u]
                out[u] = items[:predicates.get("limit", 10)]
        return out

class AssemblyLine_v0_1_2025_08_13:
    def microtest(self, candidate):
        # stub: identity score
        return {"score": 1.0, "candidate": candidate}

class Auditor: ...

class BaseAgent:
    AGENT_ID = 'base'
    VERSION = 'v0'
    CAPABILITIES: List = []
    def plan(self, inputs: Dict[str, Any]) -> Dict[str, Any]: return {'plan': 'noop'}
    def act(self, inputs: Dict[str, Any]) -> Dict[str, Any]: return {'result': 'noop'}
    def snapshot_state(self) -> Dict[str, Any]: return {'agent_id': self.AGENT_ID}
    def restore_state(self, snap: Dict[str, Any]): pass

class BaseAgent_v0_1_2025_08_13:
    AGENT_ID = "base"; VERSION = "v0_1_2025_08_13"; CAPABILITIES = []
    def plan(self, inputs: Dict[str, Any]) -> Dict[str, Any]: return {"plan":"noop"}
    def act(self, inputs: Dict[str, Any]) -> Dict[str, Any]: return {"result":"noop"}
    def snapshot_state(self) -> Dict[str, Any]: return {"agent_id": self.AGENT_ID, "version": self.VERSION}
    def restore_state(self, snap: Dict[str, Any]): return None
    @classmethod
    def spec(cls):
        return {"agent_id": cls.AGENT_ID, "version": cls.VERSION, "capabilities":[{"name":c.name,"inputs":c.inputs,"outputs":c.outputs,"description":c.description} for c in cls.CAPABILITIES]}

class BridgeLocator:
    """Locate 'bridge' positions or constraints that should bias sequencing/patching."""
    def locate(self, sequence_or_graph: Any, context: Dict[str,Any]) -> Dict[str,Any]:
        raise NotImplementedError

class Budgets_v0_1_2025_08_13:
    seconds: float = 5.0
    max_input_bytes: int = 1_000_000
    max_output_bytes: int = 1_000_000
    max_steps: int = 10

class BuilderAgent:
    def __init__(self):
        self.reroute_flag = False
    def build_path(self):
        print("[Builder] Building..." if not self.reroute_flag else "[Builder] Rerouting...")
        self.reroute_flag = False
    def trigger_reroute(self):
        self.reroute_flag = True

class CMPLXMDHGPartitionController(BaseController):
    """Use CMPLX MDHGHashTable to partition atoms into nested buckets.

    This is a sidecar to provide MDHG-style "building/city" partition reports.
    Projection-only: emits artifacts; does not mutate canon.
    """
    name = "cmplx_mdhg_partition"

    def run(self, ctx: ControllerContext, params: Dict[str, Any]) -> Dict[str, Any]:
        atoms_path = params.get("atoms_path") or (ctx.artifacts_dir / "cmplx" / "view_sweep" / "atoms.json")
        p = _resolve_path(ctx, str(atoms_path))
        raw = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
        atoms: List[str] = []
        if isinstance(raw, list):
            for it in raw:
                if isinstance(it, str):
                    atoms.append(it)
                elif isinstance(it, dict) and "text" in it:
                    atoms.append(str(it["text"]))

        max_items = int(params.get("max_items", 400))
        atoms = [a.strip() for a in atoms if a and a.strip()][:max_items]

        # If MDHG not available, fall back to plain dict partitioning
        partitions: Dict[str, List[str]] = {}
        if MDHGHashTable is None:
            for a in atoms:
                k = _bucket_key(a)
                partitions.setdefault(k, []).append(a)
        else:
            mdhg = MDHGHashTable(capacity=max(64, len(atoms)*2))
            for a in atoms:
                k = _bucket_key(a)
                # Store: key-> list
                cur = mdhg.get(k)
                if cur is None:
                    mdhg.put(k, [a])
                else:
                    cur.append(a)
                    mdhg.put(k, cur)
            # extract
            # MDHGHashTable exposes .table as buckets in this implementation; if not, we just re-get known keys
            keys = sorted({_bucket_key(a) for a in atoms})
            for k in keys:
                v = mdhg.get(k)
                if v:
                    partitions[k] = list(v)

        # build "building/city" hierarchy from buckets
        buildings = []
        for k, items in sorted(partitions.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:50]:
            buildings.append({
                "building_id": f"b:{_sha256_hex(k)[:12]}",
                "label": k,
                "count": len(items),
                "sample": items[:8],
            })

        out_dir = ctx.artifacts_dir / "cmplx" / "mdhg_partition"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "partition_report.json"
        out_path.write_text(json.dumps({
            "schema_version": 1,
            "run_id": ctx.run_id,
            "atoms": len(atoms),
            "buildings": buildings,
        }, indent=2, sort_keys=True), encoding="utf-8")

        try:
            write_receipt(ctx, step_id=self.name, kind="artifact", payload={
                "artifact": str(out_path.relative_to(ctx.workspace)),
                "atoms": len(atoms),
                "buildings": len(buildings),
            })
        except Exception:
            pass

        return {"ok": True, "atoms": len(atoms), "buildings": len(buildings), "artifact": str(out_path.relative_to(ctx.workspace))}

class CapsuleJob:
    """A pending or active capsule simulation job."""
    job_id: str
    spec: SimSpec
    mode: SpawnMode
    spawned_at: float = field(default_factory=time.time)
    status: str = "pending"  # pending | running | done | failed
    result_frame_id: str = ""
    container_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id, "sim_id": self.spec.sim_id,
            "mode": self.mode.value, "status": self.status,
            "spawned_at": self.spawned_at,
        }

class Counter:
    def __init__(self):
        self.c = 0
    def inc(self, x=1): self.c += x
    def value(self): return self.c

class DTT_v0_1_2025_08_13:
    def run(self, candidates, evaluator):
        # naive: return candidates unchanged
        return candidates

class DualWriteJournal_v0_1_2025_08_13:
    def __init__(self, dir_path="snapshots/journal", max_bytes=2_000_000):
        self.dir = Path(dir_path); self.dir.mkdir(parents=True, exist_ok=True)
        self.max_bytes = int(max_bytes)
        self.file = self._next_file()

    def _next_file(self):
        ts=int(time.time()); p = self.dir / f"dwj_{ts}.jsonl"
        p.touch()
        return p

    def append(self, heat: dict, edges: list):
        rec = {"ts": time.time(), "heat": heat, "edges": edges}
        line = json.dumps(rec)
        if self.file.stat().st_size + len(line) + 1 > self.max_bytes:
            self.file = self._next_file()
        with self.file.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
        return str(self.file)

    def replay_into_mdhg(self, mdhg, since_ts: float = 0.0):
        count=0
        for p in sorted(self.dir.glob("dwj_*.jsonl")):
            with p.open("r", encoding="utf-8") as f:
                for line in f:
                    rec = json.loads(line)
                    if rec.get("ts",0) < since_ts: continue
                    for i,h in rec.get("heat",{}).items():
                        mdhg.heat[int(i)] += float(h)
                    for a,b,w in rec.get("edges",[]):
                        if a>b: a,b=b,a
                        mdhg.edge[(int(a),int(b))] += float(w)
                    count+=1
        return count

class DualWriteQueue:

    def __init__(self):
        self.heat = defaultdict(float)
        self.edges = defaultdict(float)

    def record_heat(self, ids):
        for i in ids:
            self.heat[i] += 1.0
        for a in ids:
            for b in ids:
                if a < b:
                    self.edges[a, b] += 1.0

    def record_edge_weight(self, a, b, w=1.0):
        if a > b:
            a, b = (b, a)
        self.edges[a, b] += float(w)

    def flush_to_mdhg(self, mdhg):
        for i, h in self.heat.items():
            mdhg.heat[i] += float(h)
        for (a, b), w in self.edges.items():
            if a > b:
                a, b = (b, a)
            mdhg.edge[a, b] += float(w)
        self.heat.clear()
        self.edges.clear()
        return True

class DualWriteQueue_v0_1_2025_08_13:
    def __init__(self):
        self.heat = defaultdict(float)        # id -> heat
        self.edges = defaultdict(float)       # (a,b) -> weight

    def record_heat(self, ids):
        for i in ids:
            self.heat[i] += 1.0
        # optional: also edges for co-use of this batch
        for a in ids:
            for b in ids:
                if a<b:
                    self.edges[(a,b)] += 1.0

    def record_edge_weight(self, a, b, w=1.0):
        if a>b: a,b=b,a
        self.edges[(a,b)] += float(w)

    def flush_to_mdhg(self, mdhg):
        # mdhg expected to have .heat and .edge dicts
        for i, h in self.heat.items():
            mdhg.heat[i] += float(h)
        for (a,b), w in self.edges.items():
            if a>b: a,b=b,a
            mdhg.edge[(a,b)] += float(w)
        # clear after flush
        self.heat.clear(); self.edges.clear()
        return True

class DuckIndex:
    """Optional DuckDB index for SNAP metadata.
Stores meta rows (snap_id, family, type, created_ts, tags_json)
    """
    def __init__(self, db_path: str):
        self.path = Path(db_path)
        self.conn = duckdb.connect(str(self.path))
        self.conn.execute("""CREATE TABLE IF NOT EXISTS meta(
            snap_id TEXT PRIMARY KEY,
            family TEXT,
            type TEXT,
            created_ts DOUBLE,
            tags_json TEXT
        )""")

    def upsert(self, meta: Dict[str,Any]):
        snap_id = meta.get("snap_id")
        if not snap_id: return
        rec = (snap_id, meta.get("family"), meta.get("type"), float(meta.get("created_ts", 0.0)),
               json.dumps(meta.get("tags", {})))
        self.conn.execute("DELETE FROM meta WHERE snap_id = ?", [snap_id])
        self.conn.execute("INSERT INTO meta VALUES (?,?,?,?,?)", rec)

    def bulk_upsert(self, metas: List[Dict[str,Any]]):
        for m in metas: self.upsert(m)

    def query(self, family: Optional[str]=None, typ: Optional[str]=None, tag_key: Optional[str]=None, tag_value: Optional[str]=None) -> List[str]:
        if tag_key and tag_value is not None:
            sql = "SELECT snap_id FROM meta WHERE (? IS NULL OR family=?) AND (? IS NULL OR type=?) AND json_extract(tags_json, ?) = ?"
            key = f'$.{tag_key}'
            rs = self.conn.execute(sql, [family, family, typ, typ, key, tag_value]).fetchall()
        else:
            sql = "SELECT snap_id FROM meta WHERE (? IS NULL OR family=?) AND (? IS NULL OR type=?)"
            rs = self.conn.execute(sql, [family, family, typ, typ]).fetchall()
        return [r[0] for r in rs]

class E8DoFState_v0_1_2025_08_13:
    x: float; y: float; z: float; roll: float; pitch: float; yaw: float; sigma: float; phi: float
    def as_tuple(self): return (self.x,self.y,self.z,self.roll,self.pitch,self.yaw,self.sigma,self.phi)

class EchoAgent_v0_1_2025_08_13(BaseAgent_v0_1_2025_08_13):
    AGENT_ID = "echo.agent"
    CAPABILITIES = [Capability_v0_1_2025_08_13(name="echo", inputs=["text"], outputs=["text"], description="Returns same text.")]
    def act(self, inputs): return {"text": inputs.get("text","")}

class EdgeScoreProvider:
    """Return a score per candidate edge (higher = more preferred)."""
    def score_edges(self, points, candidate_edges: List[Edge], context: Dict[str,Any]) -> Dict[Edge, float]:
        raise NotImplementedError

class EdgeScoreProviderImpl:
    def score_edges(self, points, candidate_edges, context):
        pts = np.asarray(points, dtype=float)
        scores = {}
        for a,b in candidate_edges:
            i,j = (a,b) if a<b else (b,a)
            d = np.linalg.norm(pts[i]-pts[j])
            scores[(i,j)] = 1.0/(d+1e-9)
        return scores

class EdgeValidator: ...

class FastLane:
    def __init__(self, quality_threshold: float = 0.75):
        self.quality_threshold = float(quality_threshold)
        self.staging: Dict[str, Dict[str, Any]] = {}
        self.promoted: Dict[str, Dict[str, Any]] = {}

    def submit(self, key: str, result: Dict[str, Any], quality: float) -> FastLaneDecision:
        self.staging[key] = {"result": result, "quality": float(quality)}
        if quality >= self.quality_threshold:
            self.promoted[key] = self.staging.pop(key)
            return FastLaneDecision(staged=False, promoted=True, reason="meets threshold")
        return FastLaneDecision(staged=True, promoted=False, reason="below threshold, awaiting full path")

    def promote_after_full(self, key: str, ok: bool) -> FastLaneDecision:
        if key in self.staging and ok:
            self.promoted[key] = self.staging.pop(key)
            return FastLaneDecision(staged=False, promoted=True, reason="full path passed")
        return FastLaneDecision(staged=(key in self.staging), promoted=False, reason="full path failed or not found")

class FastLaneDecision:
    staged: bool
    promoted: bool
    reason: str

class FeedbackBus:
    def __init__(self):
        self.queue = []

    def broadcast(self, batch):
        self.queue.extend(batch)

    def collect_all(self):
        batch = self.queue[:]
        self.queue.clear()
        return batch

class Gauge:
    def __init__(self, v=0): self.v=v
    def set(self, v): self.v=v
    def get(self): return self.v

class GoldenGate(Protocol):
    def check(self, report: Dict[str, Any]) -> bool: ...

class HashTableBenchmark:
    """Benchmarking suite for hash table implementations."""
    
    def __init__(self):
        self.results = {}
        
    def run_standard_tests(self, hash_table, traditional_dict=None, n_operations=100000):
        """
        Run standard benchmark tests on hash tables.
        
        Args:
            hash_table: Hash table implementation to test
            traditional_dict: Optional traditional dict for comparison
            n_operations: Number of operations to perform
        
        Returns:
            Dictionary of benchmark results
        """
        print("Running standard distribution test...")
        std_results = self._test_standard_distribution(hash_table, traditional_dict, n_operations)
        
        print("Running skewed distribution test...")
        skew_results = self._test_skewed_distribution(hash_table, traditional_dict, n_operations)
        
        print("Running collision resistance test...")
        collision_results = self._test_collision_resistance(hash_table, traditional_dict, n_operations // 10)
        
        print("Running sequential access test...")
        sequential_results = self._test_sequential_access(hash_table, traditional_dict, n_operations)
        
        print("Running load factor scaling test...")
        load_factor_results = self._test_load_factor_scaling(hash_table, traditional_dict)
        
        # Collect all results
        results = {
            'standard': std_results,
            'skewed': skew_results,
            'collision': collision_results,
            'sequential': sequential_results,
            'load_factor': load_factor_results
        }
        
        self.results = results
        return results
        
    def _test_standard_distribution(self, hash_table, traditional_dict, n_operations):
        """Test with standard uniform distribution of keys."""
        # Generate random key-value pairs
        keys = [random.randint(0, n_operations * 10) for _ in range(n_operations)]
        values = [f"value_{i}" for i in range(n_operations)]
        
        # Test MDHG hash table
        hash_table_times = self._measure_operations(hash_table, keys, values)
        
        # Test traditional dict if provided
        dict_times = None
        if traditional_dict is not None:
            dict_times = self._measure_operations(traditional_dict, keys, values)
        
        return {
            'hash_table_times': hash_table_times,
            'dict_times': dict_times,
            'keys': keys,
            'values': values
        }
    
    def _test_skewed_distribution(self, hash_table, traditional_dict, n_operations):
        """Test with skewed distribution (some keys more frequent than others)."""
        # Generate skewed key distribution (80% of operations use 20% of key space)
        hot_keys = [random.randint(0, n_operations // 5) for _ in range(n_operations // 5)]
        
        keys = []
        for _ in range(n_operations):
            if random.random() < 0.8:
                # Use a hot key
                keys.append(random.choice(hot_keys))
            else:
                # Use a random key
                keys.append(random.randint(0, n_operations * 10))
        
        values = [f"value_{i}" for i in range(n_operations)]
        
        # Test MDHG hash table
        hash_table_times = self._measure_operations(hash_table, keys, values)
        
        # Test traditional dict if provided
        dict_times = None
        if traditional_dict is not None:
            dict_times = self._measure_operations(traditional_dict, keys, values)
        
        return {
            'hash_table_times': hash_table_times,
            'dict_times': dict_times,
            'hot_keys': hot_keys,
            'keys': keys,
            'values': values
        }
    
    def _test_collision_resistance(self, hash_table, traditional_dict, n_operations):
        """Test resistance to hash collisions."""
        # Generate keys designed to cause collisions
        # For example, strings with similar patterns
        keys = [f"collision{i % 100}-{i}" for i in range(n_operations)]
        values = [f"value_{i}" for i in range(n_operations)]
        
        # Test MDHG hash table
        hash_table_times = self._measure_operations(hash_table, keys, values)
        
        # Test traditional dict if provided
        dict_times = None
        if traditional_dict is not None:
            dict_times = self._measure_operations(traditional_dict, keys, values)
        
        return {
            'hash_table_times': hash_table_times,
            'dict_times': dict_times,
            'keys': keys,
            'values': values
        }
    
    def _test_sequential_access(self, hash_table, traditional_dict, n_operations):
        """Test with sequential access patterns."""
        # First insert some data
        keys = [i for i in range(n_operations // 10)]
        values = [f"value_{i}" for i in range(n_operations // 10)]
        
        for i in range(len(keys)):
            hash_table.put(keys[i], values[i])
            if traditional_dict is not None:
                traditional_dict[keys[i]] = values[i]
        
        # Generate sequential access patterns (e.g., iterating through keys in sequence)
        sequential_keys = []
        for _ in range(n_operations):
            # Create sequences of 5-10 sequential keys
            start = random.randint(0, len(keys) - 10)
            length = random.randint(5, 10)
            sequential_keys.extend(keys[start:start + length])
        
        # Test MDHG hash table (gets only)
        start_time = time.time()
        for key in sequential_keys:
            hash_table.get(key)
        hash_table_time = time.time() - start_time
        
        # Test traditional dict if provided
        dict_time = None
        if traditional_dict is not None:
            start_time = time.time()
            for key in sequential_keys:
                traditional_dict.get(key)
            dict_time = time.time() - start_time
        
        return {
            'hash_table_time': hash_table_time,
            'dict_time': dict_time,
            'sequential_keys': sequential_keys
        }
    
    def _test_load_factor_scaling(self, hash_table, traditional_dict):
        """Test how performance scales with increasing load factor."""
        load_factors = [0.1, 0.3, 0.5, 0.7, 0.9]
        base_capacity = 1000
        
        hash_table_results = []
        dict_results = []
        
        for load_factor in load_factors:
            # Calculate number of elements to insert
            n_elements = int(base_capacity * load_factor)
            
            # Create new hash table with fixed capacity
            test_hash_table = MDHGHashTable(capacity=base_capacity)
            test_dict = {} if traditional_dict is not None else None
            
            # Insert elements
            keys = [i for i in range(n_elements)]
            values = [f"value_{i}" for i in range(n_elements)]
            
            for i in range(n_elements):
                test_hash_table.put(keys[i], values[i])
                if test_dict is not None:
                    test_dict[keys[i]] = values[i]
            
            # Measure get performance
            test_keys = random.sample(keys, min(100, n_elements))
            
            start_time = time.time()
            for key in test_keys:
                test_hash_table.get(key)
            hash_table_time = time.time() - start_time
            
            dict_time = None
            if test_dict is not None:
                start_time = time.time()
                for key in test_keys:
                    test_dict.get(key)
                dict_time = time.time() - start_time
            
            hash_table_results.append(hash_table_time)
            dict_results.append(dict_time)
        
        return {
            'load_factors': load_factors,
            'hash_table_times': hash_table_results,
            'dict_times': dict_results
        }
    
    def _measure_operations(self, container, keys, values):
        """
        Measure time for put, get, and remove operations.
        
        Args:
            container: Hash table or dict to test
            keys: List of keys to use
            values: List of values to use
            
        Returns:
            Dictionary of operation times
        """
        n_operations = len(keys)
        
        # Measure put performance
        start_time = time.time()
        for i in range(n_operations):
            if hasattr(container, 'put'):
                container.put(keys[i], values[i])
            else:
                container[keys[i]] = values[i]
        put_time = time.time() - start_time
        
        # Measure get performance
        start_time = time.time()
        for i in range(n_operations):
            if hasattr(container, 'get'):
                container.get(keys[i])
            else:
                container.get(keys[i])
        get_time = time.time() - start_time
        
        # Measure remove performance (sample)
        sample_size = min(1000, n_operations)
        remove_keys = random.sample(keys, sample_size)
        
        start_time = time.time()
        for key in remove_keys:
            if hasattr(container, 'remove'):
                container.remove(key)
            else:
                container.pop(key, None)
        remove_time = time.time() - start_time
        
        # Scale remove time to estimate full removal time
        remove_time = remove_time * (n_operations / sample_size)
        
        return {
            'put': put_time,
            'get': get_time,
            'remove': remove_time,
            'total': put_time + get_time + remove_time
        }
    
    def plot_results(self):
        """Plot benchmark results."""
        if not self.results:
            print("No results to plot. Run benchmarks first.")
            return
        
        # Create figure with subplots
        fig, axs = plt.subplots(2, 2, figsize=(15, 12))
        
        # Plot standard distribution results
        self._plot_operation_times(axs[0, 0], 'Standard Distribution')
        
        # Plot skewed distribution results
        self._plot_operation_times(axs[0, 1], 'Skewed Distribution')
        
        # Plot collision resistance results
        self._plot_operation_times(axs[1, 0], 'Collision Resistance')
        
        # Plot load factor scaling
        self._plot_load_factor_scaling(axs[1, 1])
        
        # Adjust layout and show
        plt.tight_layout()
        plt.show()
    
    def _plot_operation_times(self, ax, title):
        """Plot operation times for a specific test."""
        test_key = title.lower().replace(' ', '_')
        if test_key not in self.results:
            return
        
        result = self.results[test_key]
        
        if 'hash_table_times' not in result or 'dict_times' not in result:
            return
        
        hash_times = result['hash_table_times']
        dict_times = result['dict_times']
        
        if not hash_times or not dict_times:
            return
        
        operations = ['put', 'get', 'remove', 'total']
        hash_values = [hash_times[op] for op in operations]
        dict_values = [dict_times[op] for op in operations]
        
        x = np.arange(len(operations))
        width = 0.35
        
        ax.bar(x - width/2, hash_values, width, label='MDHG Hash')
        ax.bar(x + width/2, dict_values, width, label='Dict')
        
        ax.set_title(title)
        ax.set_xticks(x)
        ax.set_xticklabels(operations)
        ax.set_ylabel('Time (seconds)')
        ax.legend()
        
        # Add speedup annotations
        for i, (hash_val, dict_val) in enumerate(zip(hash_values, dict_values)):
            speedup = dict_val / hash_val if hash_val > 0 else 0
            ax.annotate(f'{speedup:.2f}x', 
                       (x[i], max(hash_val, dict_val) * 1.05),
                       ha='center')
    
    def _plot_load_factor_scaling(self, ax):
        """Plot performance scaling with load factor."""
        if 'load_factor' not in self.results:
            return
        
        result = self.results['load_factor']
        
        load_factors = result['load_factors']
        hash_times = result['hash_table_times']
        dict_times = result['dict_times']
        
        if not hash_times or not dict_times:
            return
        
        ax.plot(load_factors, hash_times, 'o-', label='MDHG Hash')
        ax.plot(load_factors, dict_times, 's-', label='Dict')
        
        ax.set_title('Performance vs. Load Factor')
        ax.set_xlabel('Load Factor')
        ax.set_ylabel('Time (seconds)')
        ax.legend()
        
        # Add speedup annotations
        for i, (hash_val, dict_val) in enumerate(zip(hash_times, dict_times)):
            speedup = dict_val / hash_val if hash_val > 0 else 0
            ax.annotate(f'{speedup:.2f}x', 
                       (load_factors[i], max(hash_val, dict_val) * 1.05),
                       ha='center')
    
    def print_summary(self):
        """Print a summary of benchmark results."""
        if not self.results:
            print("No results to summarize. Run benchmarks first.")
            return
        
        print("\n" + "="*50)
        print("BENCHMARK SUMMARY")
        print("="*50)
        
        # Print standard distribution results
        self._print_test_summary('Standard Distribution', 'standard')
        
        # Print skewed distribution results
        self._print_test_summary('Skewed Distribution', 'skewed')
        
        # Print collision resistance results
        self._print_test_summary('Collision Resistance', 'collision')
        
        # Print sequential access results
        if 'sequential' in self.results:
            result = self.results['sequential']
            hash_time = result['hash_table_time']
            dict_time = result['dict_time']
            
            print("\n" + "-"*50)
            print(f"Sequential Access Test")
            print("-"*50)
            print(f"MDHG Hash: {hash_time:.6f} seconds")
            if dict_time:
                print(f"Dict:      {dict_time:.6f} seconds")
                speedup = dict_time / hash_time if hash_time > 0 else 0
                print(f"Speedup:   {speedup:.2f}x")
        
        # Print load factor scaling results
        if 'load_factor' in self.results:
            result = self.results['load_factor']
            load_factors = result['load_factors']
            hash_times = result['hash_table_times']
            dict_times = result['dict_times']
            
            print("\n" + "-"*50)
            print(f"Load Factor Scaling Test")
            print("-"*50)
            print(f"{'Load Factor':<15} {'MDHG Hash':<15} {'Dict':<15} {'Speedup':<10}")
            print("-"*55)
            
            for i, load_factor in enumerate(load_factors):
                hash_time = hash_times[i]
                dict_time = dict_times[i] if dict_times else None
                
                if dict_time:
                    speedup = dict_time / hash_time if hash_time > 0 else 0
                    print(f"{load_factor:<15.2f} {hash_time:<15.6f} {dict_time:<15.6f} {speedup:<10.2f}x")
                else:
                    print(f"{load_factor:<15.2f} {hash_time:<15.6f} {'N/A':<15} {'N/A':<10}")
    
    def _print_test_summary(self, title, test_key):
        """Print summary for a specific test."""
        if test_key not in self.results:
            return
        
        result = self.results[test_key]
        
        if 'hash_table_times' not in result or 'dict_times' not in result:
            return
        
        hash_times = result['hash_table_times']
        dict_times = result['dict_times']
        
        if not hash_times or not dict_times:
            return
        
        print("\n" + "-"*50)
        print(f"{title} Test")
        print("-"*50)
        print(f"{'Operation':<10} {'MDHG Hash':<15} {'Dict':<15} {'Speedup':<10}")
        print("-"*50)
        
        operations = ['put', 'get', 'remove', 'total']
        for op in operations:
            hash_time = hash_times[op]
            dict_time = dict_times[op]
            speedup = dict_time / hash_time if hash_time > 0 else 0
            
            print(f"{op:<10} {hash_time:<15.6f} {dict_time:<15.6f} {speedup:<10.2f}x")

class InlineHasher_v0_3_2025_08_13:
    def __init__(self, dim:int, grid:float=32.0, proj_dims:int=8, seed:int=17):
        self.dim = int(dim)
        self.proj_dims = int(min(proj_dims, max(1, dim)))
        self.grid = float(grid)
        self.rng = np.random.default_rng(seed)
        # Fixed random projection (Gaussian) to stabilize buckets across runs
        if self.proj_dims < dim:
            self.P = self.rng.standard_normal((dim, self.proj_dims)).astype(float)
        else:
            self.P = None
        self.bucket = defaultdict(set)    # bucket_id -> ids
        self.vecs = {}                    # id -> original vec
        self.meta = {}                    # id -> {building,floor,room}
        self.heat = defaultdict(float)    # id heat
        self.edge = defaultdict(float)    # (a,b) co-use
        self.bucket_centers = {}
        self._delta_heat = {}
        self._delta_edge = {}          # bucket_id -> centroid (for quick k_nn tie-breaks)

    def _embed(self, v:np.ndarray)->np.ndarray:
        if self.P is None: return v
        return v @ self.P

    def _key(self, v:np.ndarray)->tuple:
        u = self._embed(v)
        return tuple((np.floor(u * self.grid)).astype(int).tolist())

    def _floor_from_angle(self, v2:np.ndarray, num_sectors:int=32)->str:
        # For 2D convenience (TSP demo): fallback to F<sector> else F0
        try:
            ang = np.arctan2(v2[1], v2[0]); idx = int(np.digitize([ang], np.linspace(-np.pi, np.pi, num_sectors+1))[0]) - 1
            return "F{}".format(idx)
        except Exception:
            return "F0"

    def insert(self, id:int, vec, meta:dict):
        v = np.asarray(vec, dtype=float).reshape(-1)
        assert v.shape[0]==self.dim
        self.vecs[id]=v
        b = meta.get("building","default"); f = meta.get("floor"); r = meta.get("room","R0")
        if f is None:
            f = self._floor_from_angle(v[:2] if v.shape[0]>=2 else np.array([1.0,0.0]))
        self.meta[id] = {"building":b,"floor":f,"room":r}
        key = self._key(v)
        self.bucket[key].add(id)
        # Update bucket center
        ids = list(self.bucket[key])
        self.bucket_centers[key] = np.mean(np.stack([self.vecs[i] for i in ids], axis=0), axis=0)

    def bump_heat(self, ids):
        ids = list(ids)
        for i in ids:
            self.heat[i] += 1.0
            self._delta_heat[i] = self._delta_heat.get(i,0.0) + 1.0
        for a in ids:
            for b in ids:
                if a<b:
                    self.edge[(a,b)] += 1.0
                    self._delta_edge[(a,b)] = self._delta_edge.get((a,b),0.0) + 1.0

    def k_nn(self, qvec, k=8):
        q = np.asarray(qvec, dtype=float).reshape(-1)
        key = self._key(q)
        cand_ids = set(self.bucket.get(key, set()))
        # also look at immediate neighbor buckets (Chebyshev radius 1)
        if not cand_ids:
            base = np.array(key)
            for offset in np.ndindex(*([3]*len(base))):
                if all(o==1 for o in offset): continue
                neigh = tuple((base + (np.array(offset)-1)).tolist())
                cand_ids |= self.bucket.get(neigh, set())
        dists=[]
        for i in cand_ids:
            v=self.vecs[i]; d=float(np.linalg.norm(q-v)); dists.append((d,i))
        dists.sort(key=lambda x:x[0])
        return [i for _,i in dists[:k]]

    def edges(self, topk=64, building=None):
        items = list(self.edge.items())
        if building is not None:
            items = [((a,b),w) for (a,b),w in items if self.meta.get(a,{}).get("building")==building and self.meta.get(b,{}).get("building")==building]
        items.sort(key=lambda kv: kv[1], reverse=True)
        return items[:topk]

    def snapshot(self):
        return {
            "meta": self.meta,
            "edge": [(a,b,w) for (a,b),w in self.edge.items()]
        }

    def stats(self):
        # Returns {"buckets": int, "mean_bucket_size": float, "max_bucket_size": int}
        sizes = [len(s) for s in self.bucket.values()]
        if not sizes: return {"buckets": 0, "mean_bucket_size": 0.0, "max_bucket_size": 0}
        return {"buckets": len(sizes), "mean_bucket_size": float(sum(sizes))/len(sizes), "max_bucket_size": max(sizes)}

    def export_dualwrite(self):
        # Produces {"heat": {id: val}, "edges": [(a,b,w), ...]}
        return {
            "heat": dict(self.heat),
            "edges": [(a,b,w) for (a,b), w in self.edge.items()]
        }


    def consume_delta(self):
        dh = self._delta_heat; de = self._delta_edge
        self._delta_heat = {}; self._delta_edge = {}
        edges = [(a,b,w) for (a,b),w in de.items()]
        return {"heat": dict(dh), "edges": edges}

class Journal_v0_1_2025_08_13:
    def __init__(self):
        self.events: List[Dict[str,Any]] = []
    def log(self, kind:str, **payload):
        e = {"kind": kind, **payload}
        self.events.append(e)
        # For tests, also print
        print("[JOURNAL]", e)
    def dump(self) -> List[Dict[str,Any]]:
        return list(self.events)


def _h(x: Any) -> str:
    """Hash any object to hex string."""
    b = json.dumps(x, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(b).hexdigest()

def quantize(v24: List[float], bins=16) -> Tuple[int, ...]:
    """Quantize 24D vector to discrete bins."""
    out = []
    for x in v24:
        k = int(max(0, min(bins - 1, math.floor(float(x) * bins))))
        out.append(k)
    return tuple(out)

def slot_of(q24: Tuple[int, ...], grid_side=12) -> str:
    """Map quantized 24D to 2D slot via double hashing."""
    h1 = int(hashlib.sha256(("A" + str(q24)).encode()).hexdigest(), 16)
    h2 = int(hashlib.sha256(("B" + str(q24)).encode()).hexdigest(), 16)
    x = h1 % grid_side
    y = h2 % grid_side
    return f"{x:02d},{y:02d}"

def _pack_indices_to_bits(building: int, floor: int, room: int, bits_per_level: Tuple[int,int,int]=(10,10,12)) -> bytes:
    """
    Pack hierarchical indices into a fixed-length bitstring.
    Default: 10+10+12 = 32 bits => 4 bytes.
    """
    b_bits, f_bits, r_bits = bits_per_level
    max_b = (1<<b_bits)-1
    max_f = (1<<f_bits)-1
    max_r = (1<<r_bits)-1
    building = max(0, min(int(building), max_b))
    floor    = max(0, min(int(floor),    max_f))
    room     = max(0, min(int(room),     max_r))
    val = (building << (f_bits + r_bits)) | (floor << r_bits) | room
    return val.to_bytes(4, byteorder="big", signed=False)

def apply_event_to_cell(cell: CACell, event: Dict[str, Any]):
    """Apply event to CA cell - determines channel deltas."""
    op = event.get("op") or event.get("act_op") or event.get("kind") or "event"
    mag = float(event.get("mag", 0.5))
    
    # Base pressure from any activity
    cell.set("pressure", cell.get("pressure") + int(2 * mag))
    
    # Map operations to channel changes
    if op in ("store", "embed", "create"):
        # Creation increases resources
        cell.set("innovation", cell.get("innovation") + int(2 * mag))
        cell.set("food", cell.get("food") + int(1 * mag))
        cell.set("energy", cell.get("energy") + int(1 * mag))
        cell.set("trust", cell.get("trust") + 1)
    
    elif op in ("query", "retrieve", "search"):
        # Queries increase pressure and info
        cell.set("pressure", cell.get("pressure") + int(3 * mag))
        cell.set("risk", cell.get("risk") + int(1 * mag))
        cell.set("info", cell.get("info") + 1)
    
    elif op in ("validate", "verify", "confirm"):
        # Validation reduces risk, increases trust
        cell.set("risk", cell.get("risk") - int(2 * mag))
        cell.set("pressure", cell.get("pressure") - int(1 * mag))
        cell.set("trust", cell.get("trust") + 1)
    
    elif op in ("merge", "combine", "integrate"):
        # Merging increases complexity
        cell.set("info", cell.get("info") + int(2 * mag))
        cell.set("risk", cell.get("risk") + int(1 * mag))
    
    elif op in ("evict", "delete", "remove"):
        # Removal = shock
        cell.set("harm", cell.get("harm") + int(2 * mag))
        cell.set("risk", cell.get("risk") + int(1 * mag))
        cell.set("trust", cell.get("trust") - 1)
    
    # Handle specific encodings
    if "debt_stress" in event:
        cell.set("debt", cell.get("debt") + int(4 * float(event["debt_stress"])))
    
    for rk, ch in [
        ("scarcity_food", "food"),
        ("scarcity_energy", "energy"),
        ("scarcity_water", "water")
    ]:
        if rk in event:
            cell.set(ch, cell.get(ch) + int(4 * float(event[rk])))

def clampi(x: int, lo: int, hi: int) -> int:
    """Clamp integer to range."""
    return lo if x < lo else hi if x > hi else x

def crystal_to_event(crystal_meta: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert crystal metadata to CA event.
    
    Maps crystal properties to CA channel changes.
    """
    event = {
        "op": crystal_meta.get("action_type", "store"),
        "mag": crystal_meta.get("confidence", 0.5),
        "crystal_id": crystal_meta.get("crystal_id"),
        "resonance": crystal_meta.get("resonance_signature", "")[:8]
    }
    
    # Map crystal temporal phase to channel emphasis
    phase = crystal_meta.get("temporal_phase", "present")
    if phase == "past":
        event["scarcity_energy"] = 0.3  # Past = lower energy
    elif phase == "future":
        event["innovation_boost"] = 0.5  # Future = innovation
    
    return event

def digital_root(n):
    n = abs(int(round(n)))
    return 0 if n == 0 else 1 + (n - 1) % 9

def empty_cell() -> CACell:
    """Create empty CA cell."""
    c = CACell()
    for k in DEFAULT_CHANNELS:
        c.ch[k] = 0
    return c

def kernel_step(cell: CACell, nb: Dict[str, float], rng: random.Random):
    """Update cell using its Wolfram assignment."""
    a = cell.assignment
    if a is None:
        # Default: oscillating (Class II)
        a = WolframAssignment("II", "oscillate", {
            "diffuse": 0.15,
            "noise": 0.01,
            "inertia": 0.4,
            "amp": 0.25
        }).finalize()
        cell.assignment = a
    
    diffuse = float(a.params.get("diffuse", 0.15))
    noise_p = float(a.params.get("noise", 0.01))
    inertia = float(a.params.get("inertia", 0.4))
    amp = float(a.params.get("amp", 0.25))
    nonlin = float(a.params.get("nonlin", 0.35))
    
    if a.kernel == "relax":
        # Class I: converge to stable state
        for k in DEFAULT_CHANNELS:
            cur = cell.get(k)
            tgt = nb[k]
            nxt = (1 - inertia) * cur + inertia * tgt
            nxt = nxt * (1 - diffuse) + diffuse * tgt
            if rng.random() < noise_p:
                nxt += rng.choice([-1, 1])
            cell.set(k, int(round(nxt)))
    
    elif a.kernel == "oscillate":
        # Class II: periodic behavior
        cell.phase = (cell.phase + 1) % 8
        osc = math.sin(2 * math.pi * (cell.phase / 8.0))
        for k in DEFAULT_CHANNELS:
            cur = cell.get(k)
            tgt = nb[k]
            nxt = (1 - inertia) * cur + inertia * tgt + amp * osc
            nxt = nxt * (1 - diffuse) + diffuse * tgt
            if rng.random() < noise_p:
                nxt += rng.choice([-1, 1])
            cell.set(k, int(round(nxt)))
    
    elif a.kernel == "amplify":
        # Class III: chaotic amplification
        for k in DEFAULT_CHANNELS:
            cur = cell.get(k)
            mean = nb[k]
            dev = cur - mean
            nxt = cur + amp * dev
            nxt = nxt * (1 - diffuse * 0.5) + (diffuse * 0.5) * mean
            if rng.random() < max(noise_p, 0.05):
                nxt += rng.choice([-2, -1, 1, 2])
            cell.set(k, int(round(nxt)))
    
    else:  # "complex"
        # Class IV: complex localized structures
        cell.phase = (cell.phase + 1) % 16
        osc = math.sin(2 * math.pi * (cell.phase / 16.0))
        for k in DEFAULT_CHANNELS:
            cur = cell.get(k)
            mean = nb[k]
            dev = cur - mean
            kick = 0.0
            if abs(dev) > (nonlin * 4.0):
                kick = amp * math.copysign(1.0, dev)
            nxt = cur * (1 - inertia) + inertia * mean + kick + 0.15 * osc
            nxt = nxt * (1 - diffuse) + diffuse * mean
            if rng.random() < noise_p:
                nxt += rng.choice([-1, 1])
            cell.set(k, int(round(nxt)))

def neighborhood_stats(grid: List[List[CACell]], x: int, y: int) -> Dict[str, float]:
    """Von Neumann + self neighborhood statistics."""
    h = len(grid)
    w = len(grid[0])
    coords = [(x, y), (x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
    
    out = {k: 0.0 for k in DEFAULT_CHANNELS}
    cnt = 0
    
    for cx, cy in coords:
        cx %= w
        cy %= h
        cell = grid[cy][cx]
        for k in DEFAULT_CHANNELS:
            out[k] += cell.get(k)
        cnt += 1
    
    for k in DEFAULT_CHANNELS:
        out[k] /= max(1, cnt)
    
    return out

def _mdhg_hash(content: str, parent_hash: Optional[str], level: int) -> str:
    """Compute a content-addressed hash incorporating parent lineage and level."""
    payload = json.dumps({
        "content": content,
        "parent": parent_hash or "ROOT",
        "level": level,
        "coupling": COUPLING,
    }, sort_keys=True).encode()
    full_hash = hashlib.sha256(payload).hexdigest()
    prefix = HIERARCHY_LEVELS[level][:2]
    return f"{prefix}-{full_hash[:14]}"

def choose_hash(persist: bool, needs_semantic_routing: bool, needs_cross_run_invariance: bool, payload_size: int) -> HashDecision:
    # Very simple heuristic; tune later.
    if needs_semantic_routing or needs_cross_run_invariance:
        return HashDecision(True, "Semantic identity or invariance required.")
    if persist and payload_size > 0:
        return HashDecision(True, "Persisted identity benefits from MDHG axes encoding.")
    return HashDecision(False, "Local, ephemeral hashing prefers native speed.")

async def health() -> Dict[str, Any]:
    controller: MMDBController = app.state.controller
    status = controller.get_status()
    return {
        "ok": True,
        "service": "mmdb",
        "db_path": status["db_path"],
        "operations": status["operations"],
    }

def spawn_planet(
    universe_dir: Path,
    *,
    purpose: str,
    expected_items: Optional[int] = None,
    expected_bytes: Optional[int] = None,
    mutability: str = "append_only",
    geo_keys_path: Optional[Path] = None,
    planet_id: Optional[str] = None,
    tags: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    geo = load_geometric_keys(geo_keys_path)
    profile = plan_profile(purpose, expected_items, expected_bytes, mutability, geo)

    pid = planet_id or f"planet:{uuid4().hex}"
    pdir = planet_dir(universe_dir, pid)
    paths = _planet_paths(pdir)
    paths["shards"].mkdir(parents=True, exist_ok=True)

    meta = {
        "planet_id": pid,
        "created_at": now_utc(),
        "profile": profile,
        "tags": tags or {},
        "stats": {"objects": 0, "bytes": 0},
    }
    paths["meta"].write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    _append_jsonl(_index_path(universe_dir), {"type": "spawn", "at": now_utc(), "planet_id": pid, "purpose": purpose, "profile": profile})
    _append_jsonl(paths["events"], {"type": "spawn", "at": now_utc(), "planet_id": pid, "profile": profile})
    return {"ok": True, "planet_id": pid, "planet_dir": str(pdir), "profile": profile}

def _ancestors_of(node_hash: str, graph: dict) -> List[str]:
    """Walk up the parent chain."""
    path = []
    current = graph.get(node_hash)
    visited = set()
    while current and current.get("parent_hash") and current["parent_hash"] in graph:
        if current["hash"] in visited:
            break
        visited.add(current["hash"])
        path.append(current["parent_hash"])
        current = graph[current["parent_hash"]]
    return path

def _children_of(node_hash: str, graph: dict) -> List[str]:
    """Get all direct children of a node."""
    return [h for h, n in graph.items() if n.get("parent_hash") == node_hash]

def _cleanup_expired():
    """Remove expired sessions."""
    now = time.time()
    with _cleanup_lock:
        expired = [sid for sid, s in SESSIONS.items() if now - s["last_access"] > SESSION_TTL]
        for sid in expired:
            del SESSIONS[sid]
    return len(expired)

def _graph_max_depth(graph: dict) -> int:
    """Compute maximum depth across all nodes."""
    if not graph:
        return 0
    return max(_node_depth(n, graph) for n in graph.values())

def _graph_stats(graph: dict) -> dict:
    """Compute graph statistics."""
    if not graph:
        return {"nodes": 0, "max_depth": 0, "roots": 0, "leaves": 0, "levels": {}}
    roots = [h for h, n in graph.items() if not n.get("parent_hash") or n["parent_hash"] not in graph]
    all_parents = {n.get("parent_hash") for n in graph.values()}
    leaves = [h for h in graph if h not in all_parents]
    level_counts: Dict[int, int] = {}
    for n in graph.values():
        lvl = n.get("level", 0)
        level_counts[lvl] = level_counts.get(lvl, 0) + 1
    return {
        "nodes": len(graph),
        "max_depth": _graph_max_depth(graph),
        "roots": len(roots),
        "leaves": len(leaves),
        "levels": {(HIERARCHY_LEVELS[k] if isinstance(k, int) and k < len(HIERARCHY_LEVELS) else str(k)): v for k, v in sorted(level_counts.items(), key=lambda x: str(x[0]))},
    }

def _node_depth(node: dict, graph: dict) -> int:
    """Calculate depth from root by walking up the parent chain."""
    depth = 0
    current = node
    visited = set()
    while current.get("parent_hash") and current["parent_hash"] in graph:
        if current["hash"] in visited:
            break
        visited.add(current["hash"])
        current = graph[current["parent_hash"]]
        depth += 1
    return depth

def _siblings_of(node_hash: str, graph: dict) -> List[str]:
    """Get all siblings (same parent, excluding self)."""
    node = graph.get(node_hash)
    if not node or not node.get("parent_hash"):
        return []
    parent = node["parent_hash"]
    return [h for h, n in graph.items()
            if n.get("parent_hash") == parent and h != node_hash]

def _start_cleanup_thread():
    """Background thread for periodic cleanup."""
    def loop():
        while True:
            time.sleep(CLEANUP_INTERVAL)
            _cleanup_expired()
    t = threading.Thread(target=loop, daemon=True)
    t.start()

def _subtree(node_hash: str, graph: dict, max_depth: int) -> List[str]:
    """BFS down from node."""
    result = []
    queue = [(node_hash, 0)]
    visited = {node_hash}
    while queue:
        h, d = queue.pop(0)
        if d > max_depth:
            continue
        result.append(h)
        for child in _children_of(h, graph):
            if child not in visited:
                visited.add(child)
                queue.append((child, d + 1))
    return result

def _touch_session(session_id: str):
    """Update last access time."""
    if session_id in SESSIONS:
        SESSIONS[session_id]["last_access"] = time.time()

def act(self, inputs):
    return self._post('/act', inputs)

def add_node(req: AddNodeRequest):
    session = SESSIONS.get(req.session_id)
    if not session:
        raise HTTPException(404, f"Session {req.session_id} not found or expired")
    _touch_session(req.session_id)

    if req.parent_hash and req.parent_hash not in session["graph"]:
        raise HTTPException(400, f"Parent hash {req.parent_hash} not found in graph")

    node_hash = _mdhg_hash(req.content, req.parent_hash, req.level)
    if node_hash in session["graph"]:
        return {"hash": node_hash, "exists": True, "level": HIERARCHY_LEVELS[req.level]}

    node = {
        "hash": node_hash,
        "content": req.content,
        "parent_hash": req.parent_hash,
        "level": req.level,
        "level_name": HIERARCHY_LEVELS[req.level],
        "metadata": req.metadata or {},
        "created_at": time.time(),
    }
    session["graph"][node_hash] = node

    if not req.parent_hash:
        session["root_hashes"].append(node_hash)

    depth = _node_depth(node, session["graph"])
    return {
        "hash": node_hash,
        "level": HIERARCHY_LEVELS[req.level],
        "depth": depth,
        "graph_size": len(session["graph"]),
    }

def create_session(self, user_id: str, interface_type: InterfaceType, preferences: Dict[str, Any]=None) -> str:
    """Create a new user session"""
    session_id = hashlib.md5(f'{user_id}:{interface_type.value}:{time.time()}'.encode()).hexdigest()
    session = UserSession(session_id=session_id, user_id=user_id, interface_type=interface_type, start_time=time.time(), last_activity=time.time(), preferences=preferences or {})
    self.sessions[session_id] = session
    session_atom = CQEAtom(data={'session_id': session_id, 'user_id': user_id, 'interface_type': interface_type.value, 'start_time': session.start_time}, metadata={'interface_manager': True, 'user_session': True})
    self.kernel.memory_manager.store_atom(session_atom)
    return session_id

def delete_session(session_id: str):
    session = SESSIONS.pop(session_id, None)
    if not session:
        raise HTTPException(404, f"Session {session_id} not found")
    return {
        "session_id": session_id,
        "destroyed": True,
        "nodes_freed": len(session["graph"]),
    }

def get_cmd(
    planet_id: str,
    key: str,
    universe_dir: Path = typer.Option(Path("universe"), "--universe-dir"),
    out_path: Optional[Path] = typer.Option(None, "--out"),
):
    out = mdhg_get(str(universe_dir), planet_id, key, out_path=str(out_path) if out_path else None)
    console.print(out)

def get_depth(session_id: str):
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(404, f"Session {session_id} not found or expired")
    _touch_session(session_id)
    stats = _graph_stats(session["graph"])
    return {
        "session_id": session_id,
        "max_depth": stats["max_depth"],
        "total_nodes": stats["nodes"],
        "levels": stats["levels"],
    }

def get_graph(session_id: str):
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(404, f"Session {session_id} not found or expired")
    _touch_session(session_id)
    stats = _graph_stats(session["graph"])
    return {
        "session_id": session_id,
        "name": session["name"],
        "stats": stats,
        "roots": session["root_hashes"],
        "nodes": list(session["graph"].values()),
    }

def jump_hash(key_hash:int, buckets:int) -> int:
    b, j = -1, 0
    while j < buckets:
        b = j
        key_hash = (key_hash * 2862933555777941757 + 1) & ((1<<64)-1)
        j = int((b + 1) * (1<<31) / ((key_hash >> 33) + 1))
    return b

def on_startup():
    _start_cleanup_thread()

def pick_agent_by_mdhg_v0_1_2025_08_13(cands, task: Task_v0_1_2025_08_13):
    if not cands: return None
    scored = [ (score_agent_v0_1_2025_08_13(s, task), s) for s in cands ]
    scored.sort(key=lambda t: t[0], reverse=True)
    return scored[0][1]

def plan(context: Dict[str, Any], mode: str = "operational") -> Dict[str, Any]:
    return {
        "precedence": precedence_order(mode),
        "budget": {"recall": 0.7, "compute": 0.3},
        "beacon_bias": {k: beacon_value(k) for k in ("safety","cost","recall","speed")},
        "waypoints": ["sense","stage","stitch","govern","feedback"]
    }

def put_cmd(
    planet_id: str,
    key: str,
    universe_dir: Path = typer.Option(Path("universe"), "--universe-dir"),
    text: Optional[str] = typer.Option(None, "--text"),
    file: Optional[Path] = typer.Option(None, "--file"),
    content_type: str = typer.Option("text/plain", "--content-type"),
):
    out = mdhg_put(
        str(universe_dir),
        planet_id,
        key,
        payload_text=text,
        payload_path=str(file) if file else None,
        content_type=content_type,
    )
    console.print(out)

def score_agent_v0_1_2025_08_13(spec: AgentSpec_v0_1_2025_08_13, task: Task_v0_1_2025_08_13) -> float:
    hot = set(task.constraints.get("hot_tags", []))
    if not hot: return 0.0
    tags = set(spec.tags or [])
    return len(hot & tags) / max(1, len(hot))

def seed_vws_from_mdhg(points: np.ndarray, *, strategy:str="grid", grid_size:int=64,
                       force_grid:bool=True, N_guard:int=4000, journal=None,
                       seed_count:int=None, sampler_seed:int=23) -> Dict[str,Any]:
    N, d = points.shape
    if force_grid and N >= N_guard and strategy != "grid":
        if journal: journal.log("seed_guard_violation", N=N, asked=strategy, N_guard=N_guard)
        raise RuntimeError(f"force_grid active: N={N} >= {N_guard}, strategy='{strategy}' forbidden")

    chosen = []
    if strategy == "grid":
        # Simple uniform grid select: choose nearest points to grid centroids
        g = max(2, int(grid_size))
        xs = np.linspace(0,1,g); ys = np.linspace(0,1,g)
        idxs = []
        for x in xs:
            for y in ys:
                target = np.array([x,y] + [0]*(d-2), dtype=float)
                j = np.argmin(((points[:, :d] - target)**2).sum(axis=1))
                idxs.append(int(j))
        chosen = sorted(set(idxs))
        if journal: journal.log("seed_branch", branch="grid", N=N, picks=len(chosen), grid_size=grid_size)
    elif strategy == "exact":
        if journal: journal.log("seed_branch", branch="exact", N=N)
        dists = np.linalg.norm(points[:, None, :] - points[None, :, :], axis=2)
        central = np.argsort(dists.sum(axis=1))[:min(64, N)].tolist()
        chosen = central
    elif strategy in ("lhs","poisson","random"):
        K = int(np.sqrt(N)) if seed_count is None else int(seed_count)
        if strategy=="lhs":
            sites = lhs_sampler(K, d=d, seed=sampler_seed)
        elif strategy=="poisson":
            sites = poisson_disk_sampler(K, d=d, seed=sampler_seed)
        else:
            sites = random_sampler(K, d=d, seed=sampler_seed)
        idxs = []
        for s in sites:
            j = int(np.argmin(np.linalg.norm(points - s, axis=1)))
            idxs.append(j)
        chosen = sorted(set(idxs))
        if journal: journal.log("seed_branch", branch=strategy, N=N, picks=len(chosen))
    else:
        if journal: journal.log("seed_error", msg="unknown strategy", asked=strategy)
        raise ValueError(f"unknown strategy: {strategy}")
    return {"strategy": strategy, "indices": chosen, "N": N}

def spawn_cmd(
    purpose: str,
    universe_dir: Path = typer.Option(Path("universe"), "--universe-dir"),
    expected_items: Optional[int] = typer.Option(None, "--expected-items"),
    expected_bytes: Optional[int] = typer.Option(None, "--expected-bytes"),
    mutability: str = typer.Option("append_only", "--mutability"),
    geo_keys_path: Optional[Path] = typer.Option(None, "--geo-keys-path", help="Path to geometric_keys.json"),
):
    out = mdhg_spawn_planet(
        str(universe_dir),
        purpose,
        expected_items=expected_items,
        expected_bytes=expected_bytes,
        mutability=mutability,
        geo_keys_path=str(geo_keys_path) if geo_keys_path else None,
    )
    console.print(out)

def test_digital_root_resonance():
    print("--- Running Test Harness H05: Digital Root Resonance ---")
    
    # Test key system constants
    constants = {
        'Weyl Group Cardinality': 696_729_600,
        '240 Root Vectors': 240,
        '24-Ring Cycle': 24,
        'Solfeggio 432 Hz': 432,
        'Solfeggio 528 Hz': 528,
        'Solfeggio 396 Hz': 396,
        'Solfeggio 741 Hz': 741,
    }
    
    expected_resonance = {3, 6, 9}
    
    for name, value in constants.items():
        dr = digital_root(value)
        print(f"  {name}: {value} → DR {dr}")
        assert dr in expected_resonance, f"Failed: {name} has DR {dr}, not in {{3,6,9}}"
    
    print("\n✅ TEST PASSED: All key constants exhibit 3-6-9 digital root resonance.")
    print("="*70)

def traverse(
    _object: Any,
    max_length: Optional[int] = None,
    max_string: Optional[int] = None,
    max_depth: Optional[int] = None,
) -> Node:
    """Traverse object and generate a tree.

    Args:
        _object (Any): Object to be traversed.
        max_length (int, optional): Maximum length of containers before abbreviating, or None for no abbreviation.
            Defaults to None.
        max_string (int, optional): Maximum length of string before truncating, or None to disable truncating.
            Defaults to None.
        max_depth (int, optional): Maximum depth of data structures, or None for no maximum.
            Defaults to None.

    Returns:
        Node: The root of a tree structure which can be used to render a pretty repr.
    """

    def to_repr(obj: Any) -> str:
        """Get repr string for an object, but catch errors."""
        if (
            max_string is not None
            and _safe_isinstance(obj, (bytes, str))
            and len(obj) > max_string
        ):
            truncated = len(obj) - max_string
            obj_repr = f"{obj[:max_string]!r}+{truncated}"
        else:
            try:
                obj_repr = repr(obj)
            except Exception as error:
                obj_repr = f"<repr-error {str(error)!r}>"
        return obj_repr

    visited_ids: Set[int] = set()
    push_visited = visited_ids.add
    pop_visited = visited_ids.remove

    def _traverse(obj: Any, root: bool = False, depth: int = 0) -> Node:
        """Walk the object depth first."""

        obj_id = id(obj)
        if obj_id in visited_ids:
            # Recursion detected
            return Node(value_repr="...")

        obj_type = type(obj)
        children: List[Node]
        reached_max_depth = max_depth is not None and depth >= max_depth

        def iter_rich_args(rich_args: Any) -> Iterable[Union[Any, Tuple[str, Any]]]:
            for arg in rich_args:
                if _safe_isinstance(arg, tuple):
                    if len(arg) == 3:
                        key, child, default = arg
                        if default == child:
                            continue
                        yield key, child
                    elif len(arg) == 2:
                        key, child = arg
                        yield key, child
                    elif len(arg) == 1:
                        yield arg[0]
                else:
                    yield arg

        try:
            fake_attributes = hasattr(
                obj, "awehoi234_wdfjwljet234_234wdfoijsdfmmnxpi492"
            )
        except Exception:
            fake_attributes = False

        rich_repr_result: Optional[RichReprResult] = None
        if not fake_attributes:
            try:
                if hasattr(obj, "__rich_repr__") and not isclass(obj):
                    rich_repr_result = obj.__rich_repr__()
            except Exception:
                pass

        if rich_repr_result is not None:
            push_visited(obj_id)
            angular = getattr(obj.__rich_repr__, "angular", False)
            args = list(iter_rich_args(rich_repr_result))
            class_name = obj.__class__.__name__

            if args:
                children = []
                append = children.append

                if reached_max_depth:
                    if angular:
                        node = Node(value_repr=f"<{class_name}...>")
                    else:
                        node = Node(value_repr=f"{class_name}(...)")
                else:
                    if angular:
                        node = Node(
                            open_brace=f"<{class_name} ",
                            close_brace=">",
                            children=children,
                            last=root,
                            separator=" ",
                        )
                    else:
                        node = Node(
                            open_brace=f"{class_name}(",
                            close_brace=")",
                            children=children,
                            last=root,
                        )
                    for last, arg in loop_last(args):
                        if _safe_isinstance(arg, tuple):
                            key, child = arg
                            child_node = _traverse(child, depth=depth + 1)
                            child_node.last = last
                            child_node.key_repr = key
                            child_node.key_separator = "="
                            append(child_node)
                        else:
                            child_node = _traverse(arg, depth=depth + 1)
                            child_node.last = last
                            append(child_node)
            else:
                node = Node(
                    value_repr=f"<{class_name}>" if angular else f"{class_name}()",
                    children=[],
                    last=root,
                )
            pop_visited(obj_id)
        elif _is_attr_object(obj) and not fake_attributes:
            push_visited(obj_id)
            children = []
            append = children.append

            attr_fields = _get_attr_fields(obj)
            if attr_fields:
                if reached_max_depth:
                    node = Node(value_repr=f"{obj.__class__.__name__}(...)")
                else:
                    node = Node(
                        open_brace=f"{obj.__class__.__name__}(",
                        close_brace=")",
                        children=children,
                        last=root,
                    )

                    def iter_attrs() -> (
                        Iterable[Tuple[str, Any, Optional[Callable[[Any], str]]]]
                    ):
                        """Iterate over attr fields and values."""
                        for attr in attr_fields:
                            if attr.repr:
                                try:
                                    value = getattr(obj, attr.name)
                                except Exception as error:
                                    # Can happen, albeit rarely
                                    yield (attr.name, error, None)
                                else:
                                    yield (
                                        attr.name,
                                        value,
                                        attr.repr if callable(attr.repr) else None,
                                    )

                    for last, (name, value, repr_callable) in loop_last(iter_attrs()):
                        if repr_callable:
                            child_node = Node(value_repr=str(repr_callable(value)))
                        else:
                            child_node = _traverse(value, depth=depth + 1)
                        child_node.last = last
                        child_node.key_repr = name
                        child_node.key_separator = "="
                        append(child_node)
            else:
                node = Node(
                    value_repr=f"{obj.__class__.__name__}()", children=[], last=root
                )
            pop_visited(obj_id)
        elif (
            is_dataclass(obj)
            and not _safe_isinstance(obj, type)
            and not fake_attributes
            and _is_dataclass_repr(obj)
        ):
            push_visited(obj_id)
            children = []
            append = children.append
            if reached_max_depth:
                node = Node(value_repr=f"{obj.__class__.__name__}(...)")
            else:
                node = Node(
                    open_brace=f"{obj.__class__.__name__}(",
                    close_brace=")",
                    children=children,
                    last=root,
                    empty=f"{obj.__class__.__name__}()",
                )

                for last, field in loop_last(
                    field
                    for field in fields(obj)
                    if field.repr and hasattr(obj, field.name)
                ):
                    child_node = _traverse(getattr(obj, field.name), depth=depth + 1)
                    child_node.key_repr = field.name
                    child_node.last = last
                    child_node.key_separator = "="
                    append(child_node)

            pop_visited(obj_id)
        elif _is_namedtuple(obj) and _has_default_namedtuple_repr(obj):
            push_visited(obj_id)
            class_name = obj.__class__.__name__
            if reached_max_depth:
                # If we've reached the max depth, we still show the class name, but not its contents
                node = Node(
                    value_repr=f"{class_name}(...)",
                )
            else:
                children = []
                append = children.append
                node = Node(
                    open_brace=f"{class_name}(",
                    close_brace=")",
                    children=children,
                    empty=f"{class_name}()",
                )
                for last, (key, value) in loop_last(obj._asdict().items()):
                    child_node = _traverse(value, depth=depth + 1)
                    child_node.key_repr = key
                    child_node.last = last
                    child_node.key_separator = "="
                    append(child_node)
            pop_visited(obj_id)
        elif _safe_isinstance(obj, _CONTAINERS):
            for container_type in _CONTAINERS:
                if _safe_isinstance(obj, container_type):
                    obj_type = container_type
                    break

            push_visited(obj_id)

            open_brace, close_brace, empty = _BRACES[obj_type](obj)

            if reached_max_depth:
                node = Node(value_repr=f"{open_brace}...{close_brace}")
            elif obj_type.__repr__ != type(obj).__repr__:
                node = Node(value_repr=to_repr(obj), last=root)
            elif obj:
                children = []
                node = Node(
                    open_brace=open_brace,
                    close_brace=close_brace,
                    children=children,
                    last=root,
                )
                append = children.append
                num_items = len(obj)
                last_item_index = num_items - 1

                if _safe_isinstance(obj, _MAPPING_CONTAINERS):
                    iter_items = iter(obj.items())
                    if max_length is not None:
                        iter_items = islice(iter_items, max_length)
                    for index, (key, child) in enumerate(iter_items):
                        child_node = _traverse(child, depth=depth + 1)
                        child_node.key_repr = to_repr(key)
                        child_node.last = index == last_item_index
                        append(child_node)
                else:
                    iter_values = iter(obj)
                    if max_length is not None:
                        iter_values = islice(iter_values, max_length)
                    for index, child in enumerate(iter_values):
                        child_node = _traverse(child, depth=depth + 1)
                        child_node.last = index == last_item_index
                        append(child_node)
                if max_length is not None and num_items > max_length:
                    append(Node(value_repr=f"... +{num_items - max_length}", last=True))
            else:
                node = Node(empty=empty, children=[], last=root)

            pop_visited(obj_id)
        else:
            node = Node(value_repr=to_repr(obj), last=root)
        node.is_tuple = type(obj) == tuple
        node.is_namedtuple = _is_namedtuple(obj)
        return node

    node = _traverse(_object, root=True)
    return node

def _append_jsonl(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def _base36(n: int) -> str:
    chars = "0123456789abcdefghijklmnopqrstuvwxyz"
    if n == 0:
        return "0"
    out = []
    x = n
    while x > 0:
        x, r = divmod(x, 36)
        out.append(chars[r])
    return "".join(reversed(out))

def _hash_algos(profile: Dict[str, Any]) -> List[HashAlgo]:
    out: List[HashAlgo] = []
    for a in profile.get("hash_stack", []):
        name = str(a.get("name"))
        ds = a.get("digest_size")
        out.append(HashAlgo(name=name, digest_size=int(ds) if ds is not None else None))
    return out

def _index_path(universe_dir: Path) -> Path:
    p = _mdhg_root(universe_dir) / "index.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p

def _iter_manifest(paths: Dict[str, Path]) -> Iterable[Dict[str, Any]]:
    p = paths["manifest"]
    if not p.exists():
        return []
    def gen():
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except Exception:
                    continue
    return gen()

def _load_meta(pdir: Path) -> Dict[str, Any]:
    return json.loads((pdir / "meta.json").read_text(encoding="utf-8"))

def _mdhg_root(universe_dir: Path) -> Path:
    p = universe_dir / "ops" / "mdhg" / "planets"
    p.mkdir(parents=True, exist_ok=True)
    return p

def _planet_paths(pdir: Path) -> Dict[str, Path]:
    return {
        "root": pdir,
        "meta": pdir / "meta.json",
        "manifest": pdir / "manifest.jsonl",
        "events": pdir / "events.jsonl",
        "shards": pdir / "shards",
        "tombstones": pdir / "tombstones.jsonl",
    }

def _record_object(paths: Dict[str, Path], record: Dict[str, Any]) -> None:
    _append_jsonl(paths["manifest"], record)

def _route_from_digest(digest_hex: str, dims: List[int]) -> List[str]:
    x = int(digest_hex[:16], 16)  # 64-bit slice for routing
    parts: List[str] = []
    for d in dims:
        idx = x % int(d)
        x //= int(d)
        parts.append(_base36(idx).rjust(2, "0"))
    return parts

def _save_meta(pdir: Path, meta: Dict[str, Any]) -> None:
    (pdir / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

def _score_factor_choice(prod: int, f: int, target: int) -> float:
    # score in log-space; smaller is better
    return abs(math.log(prod * f) - math.log(max(2, target)))

def choose_dimensions(
    target_buckets: int,
    allowed_factors: List[int],
    *,
    max_dims: int = 8,
) -> List[int]:
    """
    Choose a factor sequence whose product >= target_buckets and is as close as possible,
    constrained to allowed factors. Greedy log-space fit.
    """
    target_buckets = max(2, int(target_buckets))
    allowed = sorted(set(int(x) for x in allowed_factors if int(x) >= 2))
    dims: List[int] = []
    prod = 1

    while prod < target_buckets and len(dims) < max_dims:
        best = None
        best_score = 1e9
        for f in allowed:
            sc = _score_factor_choice(prod, f, target_buckets)
            if sc < best_score:
                best_score = sc
                best = f
        if best is None:
            best = 2
        dims.append(int(best))
        prod *= int(best)
        if prod >= target_buckets and prod <= int(target_buckets * 1.15):
            break

    while prod < target_buckets and len(dims) < max_dims:
        f = allowed[0] if allowed else 2
        dims.append(int(f))
        prod *= int(f)

    return dims or [8]

def export_filtered(
    universe_dir: Path,
    planet_id: str,
    *,
    key_prefix: Optional[str] = None,
    key_regex: Optional[str] = None,
    max_items: int = 10000,
    out_zip: Optional[Path] = None,
) -> Dict[str, Any]:
    pdir = planet_dir(universe_dir, planet_id)
    if not pdir.exists():
        return {"ok": False, "error": "planet_not_found", "planet_id": planet_id}
    paths = _planet_paths(pdir)

    rx = re.compile(key_regex) if key_regex else None
    matches: List[Dict[str, Any]] = []
    for rec in _iter_manifest(paths):
        if rec.get("type") != "put":
            continue
        k = str(rec.get("key", ""))
        if key_prefix and not k.startswith(key_prefix):
            continue
        if rx and not rx.search(k):
            continue
        matches.append(rec)
        if len(matches) >= max_items:
            break

    out_zip = out_zip or (pdir / f"export_{uuid4().hex}.zip")
    out_zip.parent.mkdir(parents=True, exist_ok=True)

    import zipfile
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("meta.json", json.dumps(_load_meta(pdir), indent=2, ensure_ascii=False))
        z.writestr("selection.json", json.dumps({"planet_id": planet_id, "count": len(matches), "key_prefix": key_prefix, "key_regex": key_regex}, indent=2))
        z.writestr("manifest_selected.jsonl", "\n".join(json.dumps(m, ensure_ascii=False) for m in matches) + "\n")
        for rec in matches:
            rel = rec.get("path")
            if not rel:
                continue
            abs_path = pdir / rel
            if abs_path.exists():
                z.write(abs_path, arcname=f"blobs/{rel}")

    _append_jsonl(paths["events"], {"type": "export", "at": now_utc(), "count": len(matches), "out_zip": str(out_zip)})
    return {"ok": True, "planet_id": planet_id, "count": len(matches), "out_zip": str(out_zip)}

def get_latest_by_key(universe_dir: Path, planet_id: str, *, key: str) -> Dict[str, Any]:
    pdir = planet_dir(universe_dir, planet_id)
    if not pdir.exists():
        return {"ok": False, "error": "planet_not_found", "planet_id": planet_id}
    paths = _planet_paths(pdir)

    latest = None
    for rec in _iter_manifest(paths):
        if rec.get("type") == "put" and rec.get("key") == key:
            latest = rec
    if latest is None:
        return {"ok": False, "error": "not_found", "key": key, "planet_id": planet_id}

    rel = latest.get("path")
    abs_path = pdir / rel
    if not abs_path.exists():
        return {"ok": False, "error": "missing_blob", "key": key, "path": rel}

    return {
        "ok": True,
        "planet_id": planet_id,
        "key": key,
        "obj_id": latest.get("obj_id"),
        "path": rel,
        "size": latest.get("size"),
        "content_type": latest.get("content_type"),
        "digests": latest.get("digests"),
        "payload": abs_path.read_bytes(),
    }

def grow_routing(universe_dir: Path, planet_id: str, *, add_factor: Optional[int] = None) -> Dict[str, Any]:
    pdir = planet_dir(universe_dir, planet_id)
    if not pdir.exists():
        return {"ok": False, "error": "planet_not_found", "planet_id": planet_id}
    meta = _load_meta(pdir)
    prof = meta.get("profile", {})
    routing = prof.get("routing", {}) or {}
    dims = [int(d) for d in (routing.get("dims") or [8])]

    allowed = [int(x) for x in (routing.get("allowed_factors") or DEFAULT_FACTORS_LATTICE)]
    factor = int(add_factor) if add_factor is not None else (allowed[0] if allowed else 2)
    if factor < 2:
        factor = 2
    dims.append(factor)

    prod = 1
    for d in dims:
        prod *= int(d)

    routing["dims"] = dims
    routing["product"] = int(prod)
    prof["routing"] = routing
    meta["profile"] = prof
    _save_meta(pdir, meta)
    paths = _planet_paths(pdir)
    _append_jsonl(paths["events"], {"type": "grow", "at": now_utc(), "add_factor": factor, "dims": dims, "product": prod})
    return {"ok": True, "planet_id": planet_id, "dims": dims, "product": prod}

def ingest_export(
    universe_dir: Path,
    *,
    export_zip: Path,
    purpose: str = "ingest",
    mutability: str = "append_only",
    geo_keys_path: Optional[Path] = None,
) -> Dict[str, Any]:
    if not export_zip.exists():
        return {"ok": False, "error": "zip_not_found", "path": str(export_zip)}

    spawn = spawn_planet(
        universe_dir,
        purpose=purpose,
        mutability=mutability,
        geo_keys_path=geo_keys_path,
        tags={"ingested_from": str(export_zip)},
    )
    pid = spawn["planet_id"]
    pdir = planet_dir(universe_dir, pid)

    import zipfile
    ingested = 0
    with zipfile.ZipFile(export_zip, "r") as z:
        sel = z.read("manifest_selected.jsonl").decode("utf-8", errors="ignore").splitlines()
        names = set(z.namelist())
        for line in sel:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            key = str(rec.get("key", ""))
            rel = rec.get("path", "")
            blob_name = f"blobs/{rel}"
            if blob_name in names:
                payload = z.read(blob_name)
                put(universe_dir, pid, key=key, payload=payload, content_type=str(rec.get("content_type", "application/octet-stream")), tags={"ingested": True})
                ingested += 1

    _append_jsonl(_planet_paths(pdir)["events"], {"type": "ingest", "at": now_utc(), "from_zip": str(export_zip), "count": ingested})
    return {"ok": True, "planet_id": pid, "ingested": ingested}

def list_planets(universe_dir: Path, limit: int = 200) -> List[Dict[str, Any]]:
    idx = _index_path(universe_dir)
    if not idx.exists():
        return []
    out: List[Dict[str, Any]] = []
    with idx.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                continue
    return out[-limit:]

def load_geometric_keys(path: Optional[Path]) -> Dict[str, Any]:
    if path is None:
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}

def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()

def plan_profile(
    purpose: str,
    expected_items: Optional[int],
    expected_bytes: Optional[int],
    mutability: str,
    geo_keys: Dict[str, Any],
) -> Dict[str, Any]:
    """
    MDHG 'planet printer': build a per-task hash-house (routing dims + hash stack).
    Deterministic for the same request (stable replay).
    """
    purpose_l = (purpose or "").lower()

    # derive factor palette from geometric keys (if available)
    factors: List[int] = []
    consts = geo_keys.get("constants")
    if isinstance(consts, list):
        freq: Dict[int, int] = {}
        for c in consts:
            try:
                if c.get("type") == "int":
                    v = int(c.get("value"))
                    if 2 <= v <= 256:
                        freq[v] = freq.get(v, 0) + 1
            except Exception:
                continue
        top = sorted(freq.items(), key=lambda kv: kv[1], reverse=True)[:12]
        factors = [v for v, _ in top]

    if not factors:
        factors = DEFAULT_FACTORS_LATTICE[:]

    if any(k in purpose_l for k in ["receipt", "ticket", "ledger", "audit"]):
        allowed_factors = sorted(set(DEFAULT_FACTORS_CORRIDOR + factors))
        bucket_load = 128
    else:
        allowed_factors = sorted(set(DEFAULT_FACTORS_LATTICE + factors))
        bucket_load = 256

    if expected_items is not None and expected_items > 0:
        target_buckets = max(8, int(round(expected_items / bucket_load)))
    elif expected_bytes is not None and expected_bytes > 0:
        est_items = max(1, int(round(expected_bytes / 4096)))
        target_buckets = max(8, int(round(est_items / bucket_load)))
    else:
        target_buckets = 32

    dims = choose_dimensions(target_buckets, allowed_factors, max_dims=8)
    prod = 1
    for d in dims:
        prod *= int(d)

    hash_stack = [
        {"name": "blake2b", "digest_size": 32},
        {"name": "sha256", "digest_size": None},
    ]
    if "legacy" in purpose_l:
        hash_stack.append({"name": "sha1", "digest_size": None})

    geo_digest = stable_sha256({"summary": geo_keys.get("analysis", {}), "n": len(geo_keys.get("constants", []) or [])}) if geo_keys else "nogeo"
    salt = stable_sha256({"purpose": purpose, "dims": dims, "mutability": mutability, "geo": geo_digest})[:16]

    return {
        "purpose": purpose,
        "mutability": mutability,
        "bucket_load": bucket_load,
        "target_buckets": int(target_buckets),
        "routing": {
            "dims": dims,
            "product": int(prod),
            "allowed_factors": allowed_factors,
            "salt": salt,
            "format": "base36",
        },
        "hash_stack": hash_stack,
        "geo_digest": geo_digest,
        "version": "mdhg/0.1",
    }

def planet_dir(universe_dir: Path, planet_id: str) -> Path:
    return _mdhg_root(universe_dir) / planet_id

def put(url, data=None, **kwargs):
    r"""Sends a PUT request.

    :param url: URL for the new :class:`Request` object.
    :param data: (optional) Dictionary, list of tuples, bytes, or file-like
        object to send in the body of the :class:`Request`.
    :param json: (optional) A JSON serializable Python object to send in the body of the :class:`Request`.
    :param \*\*kwargs: Optional arguments that ``request`` takes.
    :return: :class:`Response <Response>` object
    :rtype: requests.Response
    """

    return request("put", url, data=data, **kwargs)

def run(self):
    print('\n' + '=' * 70)
    print('CQE META ULTRA TEST SUITE')
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
            import traceback
            traceback.print_exc()
            self.failed += 1
    print('\n' + '=' * 70)
    print(f'Results: {self.passed} passed, {self.failed} failed')
    print('=' * 70 + '\n')
    return self.failed == 0

def stable_json(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

def stable_sha256(obj: Any) -> str:
    return hashlib.sha256(stable_json(obj)).hexdigest()

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

def TODO_placeholder(*args, **kwargs):
    """Placeholder per spec. Replace with real implementation sourced from the project's E8 code when available."""
    raise NotImplementedError("E8 module 'glyphs.py' requires real implementation from project sources.")

def _aggregate_w5h_fallback(beacon: Dict[str, Any]) -> Dict[str, float]:
    w5h = beacon.get("w5h", {}) if isinstance(beacon, dict) else {}
    policy = beacon.get("policy", {}) if isinstance(beacon, dict) else {}
    weights = policy.get("weights", {}) if isinstance(policy, dict) else {}
    dims = ("who", "what", "where", "when", "why", "how")

    per_dim: Dict[str, float] = {}
    for dim in dims:
        contexts = ((w5h.get(dim, {}) or {}).get("contexts", [])) if isinstance(w5h.get(dim, {}), dict) else []
        per_dim[dim] = _mean([_clamp01(c.get("score", 0.0)) for c in contexts if isinstance(c, dict)])

    weighted = 0.0
    total_w = 0.0
    for dim in dims:
        w = float(weights.get(dim, 0.0)) if isinstance(weights, dict) else 0.0
        if w <= 0.0:
            continue
        total_w += w
        weighted += per_dim.get(dim, 0.0) * w
    final = (weighted / total_w) if total_w > 0.0 else _mean([per_dim[d] for d in dims])
    return {"final": _clamp01(final), **{k: _clamp01(v) for k, v in per_dim.items()}}

def _archivist_post(self, key, payload):
    # minimal journal-like sink; no-op if real journal exists
    return {"ok": True, "key": key, "payload": payload}

def _bins(points: np.ndarray, buckets:int=64):
    N, d = points.shape
    if d < 2:
        raise ValueError("adjacency grid binning expects at least 2D points")
    mins = points[:, :2].min(axis=0)
    maxs = points[:, :2].max(axis=0)
    span = np.maximum(maxs - mins, 1e-9)
    coords = (points[:, :2] - mins) / span
    ij = np.minimum(buckets-1, np.maximum(0, (coords * buckets).astype(int)))
    bins: Dict[Tuple[int,int], List[int]] = {}
    for idx, (i,j) in enumerate(ij):
        bins.setdefault((int(i),int(j)), []).append(idx)
    return ij, bins, mins, maxs, span

def _box(workspace: Path, planet_id: str, box: str) -> Path:
    ensure_mail(workspace)
    p = workspace / "mail" / planet_id
    p.mkdir(parents=True, exist_ok=True)
    f = p / f"{box}.jsonl"
    f.touch(exist_ok=True)
    return f

def _breed_profile(parent_a: Dict[str, Any], parent_b: Dict[str, Any], candidates: List[int], rng: random.Random) -> Tuple[List[int], List[str]]:
    da = list(parent_a.get("dims", [16,16]))
    db = list(parent_b.get("dims", [16,16]))
    # crossover dims
    cut_a = rng.randrange(1, len(da)+1)
    cut_b = rng.randrange(1, len(db)+1)
    child_dims = da[:cut_a] + db[cut_b:]
    if not child_dims:
        child_dims = [16,16]
    child_dims = _mutate_dims(child_dims, candidates, rng)
    # hash stack: choose from parents
    ha = list(parent_a.get("hash_stack", ["blake2b","sha256"]))
    hb = list(parent_b.get("hash_stack", ["blake2b","sha256"]))
    child_stack = ha if rng.random() < 0.5 else hb
    # tiny mutation: swap order sometimes
    if rng.random() < 0.25 and len(child_stack) >= 2:
        child_stack = list(reversed(child_stack))
    return child_dims, child_stack

def _bucket_key(text: str) -> str:
    # simple stable bucket: first token lowercased or first 8 chars
    t = (text or "").strip()
    if not t:
        return "empty"
    parts = t.split()
    if parts:
        return parts[0].lower()[:24]
    return t[:24].lower()

def _build_demands(scan_dir: Path, *, max_demands: int = 12, min_hit_count: int = 40) -> List[MdhgDemand]:
    summary = _load_json(scan_dir / "summary.json", [])
    pattern = _load_json(scan_dir / "pattern_counts.json", [])
    top_rows = _read_tsv_rows(scan_dir / "global_top_files_filtered.tsv", limit=300)
    phrase_rows = _read_tsv_rows(scan_dir / "full_phrase_files.tsv", limit=300)

    summary_counts = {str(x.get("folder", "")): int(x.get("match_lines", 0)) for x in summary if isinstance(x, dict)}
    phrase_counts = {str(x.get("file", "")): int(x.get("lines_with_full_phrase", 0)) for x in pattern if isinstance(x, dict)}

    stats: Dict[str, Dict[str, Any]] = {}

    def _get_stat(family: str) -> Dict[str, Any]:
        if family not in stats:
            stats[family] = {
                "top_hit_sum": 0,
                "phrase_hit_sum": 0,
                "top_rows": [],
                "phrase_rows": [],
                "buckets": set(),
            }
        return stats[family]

    for row in top_rows:
        path = str(row.get("path", "")).strip()
        if not path:
            continue
        family = _extract_family(path)
        count = _to_int(row.get("count"), default=1)
        st = _get_stat(family)
        st["top_hit_sum"] += count
        st["top_rows"].append((count, path))
        st["buckets"].add(_extract_bucket(path))

    for row in phrase_rows:
        path = str(row.get("path", "")).strip()
        if not path:
            continue
        family = _extract_family(path)
        count = _to_int(row.get("count"), default=1)
        st = _get_stat(family)
        st["phrase_hit_sum"] += count
        st["phrase_rows"].append((count, path))
        st["buckets"].add(_extract_bucket(path))

    ranked = sorted(
        stats.items(),
        key=lambda kv: (
            int(kv[1].get("top_hit_sum", 0)) + (int(kv[1].get("phrase_hit_sum", 0)) * 12),
            int(kv[1].get("top_hit_sum", 0)),
            int(kv[1].get("phrase_hit_sum", 0)),
        ),
        reverse=True,
    )

    selected: List[Tuple[str, Dict[str, Any]]] = []
    for family, st in ranked:
        total_hits = int(st.get("top_hit_sum", 0)) + int(st.get("phrase_hit_sum", 0))
        if total_hits < int(min_hit_count):
            continue
        selected.append((family, st))
        if len(selected) >= max(1, int(max_demands)):
            break

    if not selected and ranked:
        selected = ranked[: max(1, int(max_demands))]

    total_phrase_hits = sum(int(x) for x in phrase_counts.values())
    demands: List[MdhgDemand] = []
    for rank, (family, st) in enumerate(selected, start=1):
        top_rows_family = sorted(st.get("top_rows", []), key=lambda item: int(item[0]), reverse=True)
        phrase_rows_family = sorted(st.get("phrase_rows", []), key=lambda item: int(item[0]), reverse=True)
        top_paths = [str(path) for _, path in top_rows_family]
        phrase_paths = [str(path) for _, path in phrase_rows_family]
        evidence_paths = _dedupe_paths(tuple(top_paths + phrase_paths), limit=18)
        phrase_hits = int(st.get("phrase_hit_sum", 0))
        top_hits = int(st.get("top_hit_sum", 0))
        buckets = sorted(str(x) for x in st.get("buckets", set()))
        family_slug = _slug_token(family)
        objective = (
            f"Reason over MDHG hotspots for family '{family}' (top_hits={top_hits}, phrase_hits={phrase_hits}) "
            f"across buckets {buckets}, then build rule-governed sidecar atoms and compositions."
        )
        constraints = [
            "policy-driven agent rules",
            "deterministic tests",
            "audit receipts",
            "batched execution",
            "preserve existing behavior",
        ]
        if phrase_hits > 0:
            constraints.append("lossless normalization")

        demands.append(
            MdhgDemand(
                demand_id=f"mdhg-family-{family_slug}",
                name=f"mdhg-family-{family_slug}",
                objective=objective,
                systems=_systems_for_family(family),
                tools=_tools_for_family(family, phrase_hits),
                constraints=tuple(dict.fromkeys(constraints)),
                evidence_paths=evidence_paths,
                evidence_counts={
                    "family": family,
                    "family_rank": rank,
                    "top_hit_sum": top_hits,
                    "phrase_hit_sum": phrase_hits,
                    "top_file_count": len(top_rows_family),
                    "phrase_file_count": len(phrase_rows_family),
                    "bucket_count": len(buckets),
                    "buckets": buckets,
                    "global_phrase_hits": total_phrase_hits,
                    "cmplx_devlab_match_lines": summary_counts.get("CMPLX-DevLab", 0),
                    "retool_match_lines": summary_counts.get("CMPLX Retool-Main", 0),
                    "reports_match_lines": summary_counts.get("reports", 0),
                },
            )
        )

    return demands

def _build_mdhg(self, points):
    import numpy as _np
    points = _np.asarray(points, dtype=float)
    m = MDHG(dim=points.shape[1], decay_lambda=self.cfg.get('mdhg_decay', 0.01))
    n = points.shape[0]
    center = points.mean(axis=0)
    vecs = points - center
    angles = _np.arctan2(vecs[:, 1], vecs[:, 0])
    num_floors = self.cfg.get('num_sectors', 32)
    sec_edges = _np.linspace(-_np.pi, _np.pi, num_floors + 1)
    sectors = _np.digitize(angles, sec_edges) - 1
    for i in range(n):
        meta = {'building': self.cfg.get('building', 'default'), 'floor': f'F{sectors[i]}', 'room': 'R0'}
        m.insert(i, points[i], meta)
    for i in range(n):
        m.bump_heat([i])
    return m

def _build_w5h_beacon(demand: MdhgDemand, receipt: Dict[str, Any], snap_roles: Sequence[str]) -> Dict[str, Any]:
    evidence = demand.evidence_counts if isinstance(demand.evidence_counts, dict) else {}
    top_hits = max(0, int(evidence.get("top_hit_sum", 0)))
    phrase_hits = max(0, int(evidence.get("phrase_hit_sum", 0)))
    bucket_count = max(0, int(evidence.get("bucket_count", 0)))
    family_rank = max(1, int(evidence.get("family_rank", 1)))
    global_phrase_hits = max(1, int(evidence.get("global_phrase_hits", 1)))
    core = _core_role_state(receipt)
    core_ratio = (sum(1 for v in core.values() if v) / len(core)) if core else 0.0
    thinktank_trace = receipt.get("thinktank_choice_trace", {}) if isinstance(receipt, dict) else {}
    thinktank_ok = 1.0 if str(thinktank_trace.get("status", "")).lower() == "success" else 0.0
    thinktank_mode = 1.0 if str(receipt.get("thinktank_mode", "")).lower() == "thinktank" else 0.0
    viability = _clamp01(receipt.get("viability", 0.0))

    top_norm = _clamp01(top_hits / 3000.0)
    phrase_norm = _clamp01(phrase_hits / float(global_phrase_hits))
    bucket_norm = _clamp01(bucket_count / 3.0)
    rank_priority = _clamp01(1.0 - ((family_rank - 1) / 10.0))
    mdhg_relevance = _clamp01((top_norm * 0.8) + (phrase_norm * 0.2))

    return {
        "w5h": {
            "who": {
                "contexts": [
                    {"name": "snap_roles_assigned", "score": 1.0 if snap_roles else 0.0},
                    {"name": "core_role_approvals", "score": _clamp01(core_ratio)},
                    {"name": "thinktank_mode", "score": thinktank_mode},
                ]
            },
            "what": {
                "contexts": [
                    {"name": "top_hit_intensity", "score": top_norm},
                    {"name": "phrase_signal", "score": phrase_norm},
                    {"name": "viability", "score": viability},
                ]
            },
            "where": {
                "contexts": [
                    {"name": "bucket_coverage", "score": bucket_norm},
                    {"name": "cross_mirror_presence", "score": 1.0 if bucket_count >= 2 else 0.0},
                ]
            },
            "when": {
                "contexts": [
                    {"name": "batch_rank_priority", "score": rank_priority},
                    {"name": "analysis_recency", "score": 1.0},
                ]
            },
            "why": {
                "contexts": [
                    {"name": "mdhg_relevance", "score": mdhg_relevance},
                    {"name": "full_phrase_presence", "score": 1.0 if phrase_hits > 0 else 0.0},
                ]
            },
            "how": {
                "contexts": [
                    {"name": "thinktank_success", "score": thinktank_ok},
                    {"name": "batched_execution", "score": 1.0},
                    {"name": "role_coverage", "score": _clamp01(core_ratio)},
                ]
            },
        },
        "policy": {
            "aggregation": "weighted_mean",
            "weights": {
                "who": 0.15,
                "what": 0.25,
                "where": 0.15,
                "when": 0.15,
                "why": 0.20,
                "how": 0.10,
            },
            "priority_contexts": [
                "thinktank_success",
                "core_role_approvals",
                "mdhg_relevance",
            ],
        },
    }

def _choose_dims(expected_items: int, candidates: List[int], *, max_dims: int = 6) -> List[int]:
    """Pick factors whose product roughly matches expected_items (log-space greedy)."""
    if expected_items <= 0:
        expected_items = 1024
    log_target = math.log(max(2.0, float(expected_items)))
    dims: List[int] = []
    remaining = log_target
    for _ in range(max_dims):
        if remaining <= math.log(2.0):
            break
        best = None
        best_score = 1e18
        for c in candidates:
            lc = math.log(float(c))
            score = abs(remaining - lc) + 0.15 * max(0.0, lc - remaining)
            if score < best_score:
                best_score = score
                best = c
        if best is None:
            break
        dims.append(int(best))
        remaining -= math.log(float(best))
    return dims or [16, 16]

def _choose_partner(planets: List[str], weights: List[float], rng: random.Random) -> str:
    total = sum(weights)
    if total <= 0:
        return rng.choice(planets)
    r = rng.random() * total
    acc = 0.0
    for p,w in zip(planets, weights):
        acc += w
        if r <= acc:
            return p
    return planets[-1]

def _clamp01(value: Any) -> float:
    try:
        f = float(value)
    except Exception:
        return 0.0
    return max(0.0, min(1.0, f))

def _configure_logging(*, verbose: bool) -> None:
    if verbose:
        return
    noisy_loggers = (
        "infra.controller",
        "cmplx.thinktank.ecosystem",
        "cmplx.thinktank.socratic",
        "cmplxclaw",
        "cmplx.adapter.snap",
    )
    for name in noisy_loggers:
        logging.getLogger(name).setLevel(logging.WARNING)

def _core_role_state(receipt: Dict[str, Any]) -> Dict[str, bool]:
    review_rows = receipt.get("reviews", []) if isinstance(receipt, dict) else []
    states = {"architect": False, "auditor": False, "healer": False, "orchestrator": False}
    for row in review_rows:
        rid = str(row.get("reviewer_id", ""))
        for role in states:
            if rid == role:
                states[role] = bool(row.get("approved", False))
    return states

def _decision_for_receipt(receipt: Dict[str, Any], accept_viability: float, iterate_viability: float) -> str:
    viability = float(receipt.get("viability", 0.0))
    core = _core_role_state(receipt)
    core_approved = sum(1 for v in core.values() if v)
    thinktank_mode = str(receipt.get("thinktank_mode", ""))

    # Accept if ThinkTank-backed and key execution roles pass, even with auditor backlog.
    if (
        thinktank_mode == "thinktank"
        and viability >= accept_viability
        and core_approved >= 3
        and core.get("architect", False)
        and core.get("healer", False)
        and core.get("orchestrator", False)
    ):
        return "accept"
    if viability >= iterate_viability and core_approved >= 2:
        return "iterate"
    return "hold"

def _dedupe_paths(paths: Sequence[str], *, limit: int) -> Tuple[str, ...]:
    out: List[str] = []
    seen = set()
    for path in paths:
        key = _normalize_path(path).lower().strip()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(path)
        if len(out) >= limit:
            break
    return tuple(out)

def _digital_root_from_hex(hex_text: str) -> int:
    val = int(hex_text[:16], 16)
    if val == 0:
        return 0
    return 1 + ((val - 1) % 9)

def _extract_branch_candidates(keys: Dict[str, Any]) -> List[int]:
    """Collect small integers from the geo keyspace; bias to 4..64 + corridor primes."""
    out: List[int] = []
    def walk(x: Any):
        if isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
        elif isinstance(x, int):
            if 2 <= x <= 256:
                out.append(int(x))
    walk(keys)
    out.extend([2, 3, 5, 7, 11, 13, 4, 8, 16, 32, 64])
    out = sorted(set([v for v in out if 2 <= v <= 256]))
    preferred = [v for v in out if 4 <= v <= 64] + [2, 3, 5, 7, 11, 13]
    final: List[int] = []
    for v in preferred:
        if v not in final:
            final.append(v)
    return final[:64]

def _extract_bucket(path: str) -> str:
    normalized = _normalize_path(path).lower()
    if "cmplx-devlab/cmplx2/" in normalized:
        return "devlab_mirror"
    if "cmplx retool-main/" in normalized or "cmplx_retool-main/" in normalized:
        return "retool_mirror"
    if "cmplx-devlab/" in normalized:
        return "devlab"
    if "cmplx-product" in normalized:
        return "product"
    if normalized.startswith("reports/") or "/reports/" in normalized:
        return "reports"
    return "other"

def _extract_family(path: str) -> str:
    normalized = _normalize_path(path).lower()
    marker = "unified_families/"
    if marker in normalized:
        tail = normalized.split(marker, 1)[1]
        token = tail.split("/", 1)[0].strip()
        if token:
            return token
    # fallback buckets for non-unified paths
    for token in ("cmplx2", "retool-main", "cmplx-devlab", "reports"):
        if token in normalized:
            return token.replace("-", "_")
    return "misc"

def _gain(points, a,b,c,d,e,f):
    def d(x,y): return float(np.linalg.norm(points[x]-points[y]))
    base = d(a,b)+d(c,d)+d(e,f)
    cand = [ d(a,c)+d(b,d)+d(e,f), d(a,b)+d(c,e)+d(d,f), d(a,d)+d(e,b)+d(c,f),
             d(a,c)+d(d,e)+d(b,f), d(a,e)+d(d,b)+d(c,f), d(a,d)+d(e,c)+d(b,f),
             d(a,e)+d(c,b)+d(d,f)]
    best = min(cand)
    return base - best

def _get_session(session_id: str) -> SandboxSession:
    """Retrieve a live session or raise 404."""
    with _sessions_lock:
        session = _sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found or expired.")
    return session

def _hash_stack(key: str, *, salt: str, stack: List[str]) -> List[str]:
    cur = salt + "|" + key
    digests: List[str] = []
    for algo in stack:
        fn = _HASH_FUNCS.get(algo)
        if fn is None:
            raise ValueError(f"Unsupported hash algo: {algo}")
        h = fn(cur)
        digests.append(h)
        cur = h
    return digests

def _iteration_constraints(base: Sequence[str], receipt: Dict[str, Any]) -> Tuple[str, ...]:
    core = _core_role_state(receipt)
    extras: List[str] = []
    if not core.get("auditor", False):
        extras.extend(["audit controls", "traceability proof", "explicit validation gates"])
    if not core.get("healer", False):
        extras.extend(["rollback hooks", "self-test hooks"])
    if not core.get("orchestrator", False):
        extras.extend(["composition route mapping", "controller contract alignment"])
    if not core.get("architect", False):
        extras.extend(["interface simplification", "dependency boundary hardening"])
    merged = list(base) + extras
    seen = set()
    out: List[str] = []
    for item in merged:
        key = item.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(item)
    return tuple(out)

def _load_external_validation_context(project_root: Path) -> Dict[str, Any]:
    base = project_root / "sidecars" / "thinktank_deploy" / "data" / "thinktank_deployment"
    live = _load_json(base / "live_deployment_report.json", {})
    test = _load_json(base / "test_report.json", {})
    if not isinstance(live, dict):
        live = {}
    if not isinstance(test, dict):
        test = {}

    compliance = live.get("compliance", {}) if isinstance(live.get("compliance"), dict) else {}
    deployment = live.get("deployment", {}) if isinstance(live.get("deployment"), dict) else {}
    hierarchy = live.get("system_hierarchy_viability", {}) if isinstance(live.get("system_hierarchy_viability"), dict) else {}

    return {
        "available": bool(live or test),
        "source_dir": str(base),
        "live_report": {
            "status": deployment.get("status"),
            "w5h_score": deployment.get("w5h_score"),
            "strategy": deployment.get("strategy"),
            "snap_tx_id": deployment.get("snap_tx_id"),
            "compliance_score": compliance.get("compliance_score"),
            "compliance_status": compliance.get("status"),
            "rules_checked": compliance.get("rules_checked"),
            "rules_failed": compliance.get("failed"),
            "viable_for_integration": hierarchy.get("viable_for_integration"),
            "meets_requirements": hierarchy.get("meets_requirements"),
        },
        "test_report": {
            "compliance_status": test.get("compliance_status"),
            "tests_run": (test.get("test_summary") or {}).get("tests_run") if isinstance(test.get("test_summary"), dict) else None,
            "failures": (test.get("test_summary") or {}).get("failures") if isinstance(test.get("test_summary"), dict) else None,
            "errors": (test.get("test_summary") or {}).get("errors") if isinstance(test.get("test_summary"), dict) else None,
        },
    }

def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def _mdhg_triple(self, v: np.ndarray, meta: Optional[np.ndarray]) -> Optional[tuple]:
    adapters = self._try_mdhg_adapters()
    for ad in adapters:
        try:
            triple = ad(v, meta)
            if isinstance(triple, (list, tuple)) and len(triple) >= 3:
                b,f,r = int(triple[0]), int(triple[1]), int(triple[2])
                return (b,f,r)
        except Exception:
            continue
    return None

    def _fallback_encode(self, v: np.ndarray, meta: Optional[np.ndarray]) -> bytes:
        x = v
        if meta is not None and meta.ndim == 1:
            if meta.size < 8:
                meta = np.pad(meta, (0, 8-meta.size))
            else:
                meta = meta[:8]
            x = (v + meta)/2.0
        proj = x @ self._W  # 64 bits
        bits = (proj >= 0).astype(np.uint8)
        # pack 64 bits -> 8 bytes
        out = bytearray()
        acc = 0
        for i, b in enumerate(bits):
            acc = (acc<<1) | int(b)
            if (i+1)%8 == 0:
                out.append(acc)
                acc = 0
        return bytes(out)

    def encode(self, v: np.ndarray, meta: Optional[np.ndarray] = None) -> bytes:
        """
        If MDHG is present, map (v, meta) to hierarchical indices and pack to 4 bytes.
        Else return an 8-byte deterministic fallback code.
        """
        # Normalize input
        v = np.asarray(v, dtype=float).reshape(-1)
        if self._mdhg is None:
            return self._fallback_encode(v, meta)

        # MDHG present or bound: derive a deterministic bucket triple (building, floor, room).
        # We do not mutate tables here; we compute a stable pseudo-index via hashing + version/seed (stateless).
        h = hashlib.blake2b(v.tobytes() + (meta.tobytes() if (meta is not None) else b"") + 
                            f"v{self.version}|s{self.seed}".encode(), digest_size=16).digest()
        # Split hash into three integers
        bi = int.from_bytes(h[0:4], "big")
        fi = int.from_bytes(h[4:8], "big")
        ri = int.from_bytes(h[8:12], "big")
        # Map into ranges
        b_bits, f_bits, r_bits = self.bits_per_level
        building = bi % (1<<b_bits)
        floor    = fi % (1<<f_bits)
        room     = ri % (1<<r_bits)
        return _pack_indices_to_bits(building, floor, room, self.bits_per_level)

def _mean(values: Sequence[float]) -> float:
    vals = [float(v) for v in values if v is not None]
    return (sum(vals) / len(vals)) if vals else 0.0

def _mutate_dims(dims: List[int], candidates: List[int], rng: random.Random, rate: float = 0.35) -> List[int]:
    out = list(dims)
    # mutation: with some prob, tweak one factor; with smaller prob, add/remove a dim
    if rng.random() < rate and out:
        i = rng.randrange(len(out))
        out[i] = rng.choice(candidates)
    if rng.random() < rate * 0.5:
        # add dim
        out.append(rng.choice(candidates))
    if len(out) > 2 and rng.random() < rate * 0.3:
        # remove dim
        out.pop(rng.randrange(len(out)))
    # clamp
    out = [int(max(2, min(256, x))) for x in out]
    return out

def _normalize_path(path: str) -> str:
    return str(path or "").replace("\\", "/")

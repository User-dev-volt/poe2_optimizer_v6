# Technical Specification: Foundation - PoB Calculation Engine Integration

Date: 2025-10-10
Author: Alec
Epic ID: 1
Status: Draft

---

## Overview

Epic 1 establishes the foundational capability for the entire PoE 2 Passive Tree Optimizer: accurate headless execution of Path of Building's calculation engine in Python. Without this foundation, the optimization algorithm would have no way to evaluate build quality—making the entire product impossible.

This epic implements the critical Python-Lua bridge using the Lupa library to execute HeadlessWrapper.lua, enabling the system to calculate DPS, EHP, resistances, and all other character statistics with 100% parity to the official PoB GUI. Success here means we can parse any valid PoE 2 build code, modify its passive tree in memory, recalculate stats in <100ms per iteration, and verify results match PoB's proven calculation logic within ±0.1% tolerance.

## Objectives and Scope

### In Scope

- **PoB Code Parsing & Generation:** Base64 → zlib → XML pipeline for both decoding (user input) and encoding (optimized output)
- **Lupa + LuaJIT Integration:** Embed LuaJIT runtime in Python with proper memory management and error handling
- **Python Stub Functions:** Implement required PoB dependencies (Deflate/Inflate, ConPrintf, etc.) to enable headless execution
- **HeadlessWrapper.lua Loading:** Initialize PoB calculation engine with passive tree data and character class definitions
- **Single Build Calculation:** Accept BuildData object, execute PoB calc, return BuildStats (DPS, EHP, resistances)
- **Batch Performance Optimization:** Pre-compile Lua functions, reuse Build objects, achieve 150-500ms for 1000 calculations
- **Accuracy Validation:** Parity testing with PoB GUI results (±0.1% tolerance on 100+ sample builds)
- **Passive Tree Graph Loading:** Parse PassiveTree.lua into Python adjacency list for pathfinding and validation

### Out of Scope (Deferred to Later Epics)

- **Optimization Algorithm:** Hill climbing implementation (Epic 2)
- **Web UI:** Flask application and user interface (Epic 3)
- **Progress Tracking:** Real-time optimization progress (Epic 3)
- **Error Messages:** User-facing structured error messages (Epic 3)
- **Session Management:** Multi-user concurrency (Epic 3)

### Success Criteria

1. Parse 100 sample PoB codes with 100% success rate
2. Calculate stats for each with <100ms latency per calculation
3. Batch calculations: 1000 iterations in <1 second (target: 150-500ms)
4. Accuracy: ±0.1% tolerance compared to official PoB GUI
5. Memory: <100MB per calculation session
6. Zero Lua runtime crashes or unhandled exceptions

## System Architecture Alignment

Epic 1 implements the **Data Layer** and **Integration Layer** from the solution architecture:

### Component Mapping

- **parsers/ module** (Data Layer)
  - `pob_parser.py` - Base64/zlib/XML decoding → BuildData
  - `pob_generator.py` - BuildData → XML/zlib/Base64 encoding
  - `xml_utils.py` - XML parsing helpers
  - `exceptions.py` - PoBParseError, InvalidFormatError

- **calculator/ module** (Integration Layer)
  - `pob_engine.py` - Lupa integration, HeadlessWrapper loading, thread-local engine management
  - `stub_functions.py` - Python implementations of Deflate, Inflate, ConPrintf, etc.
  - `passive_tree.py` - PassiveTree.lua loader, adjacency list caching
  - `build_calculator.py` - High-level calculate_stats(BuildData) → BuildStats API

- **models/ module** (Shared Data Transfer Objects)
  - `build_data.py` - BuildData dataclass (character, passive nodes, items, skills)
  - `build_stats.py` - BuildStats dataclass (DPS, EHP, resistances, life, ES, mana)

### Architecture Pattern Adherence

- **Layered Architecture:** Parsers (bottom) → Calculator (middle) → Future layers depend on these
- **Dependency Rules:** Calculator depends on Parsers, but Parsers has ZERO dependencies on Calculator
- **Modular Monolith:** All components in single Python process, clear module boundaries
- **Thread-Local Resources:** Each optimization thread gets isolated LuaRuntime instance (FR-3.5 session isolation)

### External Dependencies

- **Lupa 2.0:** Python-to-LuaJIT bindings
- **xmltodict 0.13.0:** PoB XML parsing
- **external/pob-engine/ (Git submodule):** Official PoB repository
  - `HeadlessWrapper.lua` - Calculation entry point
  - `src/Data/PassiveTree.lua` - Passive tree graph
  - `src/Data/Classes.lua` - Character starting nodes

### Technology Stack (Epic 1 Specific)

| Component | Technology | Version | Justification |
|-----------|------------|---------|---------------|
| Lua Integration | Lupa | 2.0 | LuaJIT bindings for Python, <100ms calculation performance |
| XML Parsing | xmltodict | 0.13.0 | Simple dict conversion for PoB XML format |
| Compression | zlib (stdlib) | Python 3.10+ | PoB codes use zlib compression |
| Encoding | base64 (stdlib) | Python 3.10+ | PoB codes are Base64-encoded |

This epic delivers the **calculation accuracy** and **performance** required by NFR-1 (Performance) and forms the prerequisite for Epic 2 (optimization algorithm).

## Detailed Design

### Services and Modules

| Module | Responsibility | Key Functions | Inputs | Outputs | Owner |
|--------|---------------|---------------|--------|---------|-------|
| **parsers/pob_parser.py** | Decode PoB codes to structured data | `parse_pob_code(code: str) -> BuildData` | Base64 PoB code string | BuildData object | Epic 1 Story 1.1 |
| **parsers/pob_generator.py** | Encode BuildData to PoB codes | `generate_pob_code(build: BuildData) -> str` | BuildData object | Base64 PoB code string | Epic 1 Story 1.1 |
| **parsers/xml_utils.py** | XML parsing helpers | `parse_xml(xml_str: str) -> dict`, `build_xml(data: dict) -> str` | XML strings, dicts | Parsed dicts, XML strings | Epic 1 Story 1.1 |
| **parsers/exceptions.py** | Custom exceptions for parsing errors | `PoBParseError`, `InvalidFormatError`, `UnsupportedVersionError` | N/A (exception definitions) | N/A | Epic 1 Story 1.1 |
| **calculator/pob_engine.py** | Lupa integration, HeadlessWrapper management | `get_pob_engine() -> PoBCalculationEngine`, `PoBCalculationEngine.calculate(build: BuildData) -> BuildStats` | BuildData | BuildStats | Epic 1 Stories 1.2-1.5 |
| **calculator/stub_functions.py** | Python stubs for PoB Lua dependencies | `Deflate(data: bytes) -> bytes`, `Inflate(data: bytes) -> bytes`, `ConPrintf(msg: str) -> None` | Various (Lua calls) | Various (Python responses) | Epic 1 Story 1.3 |
| **calculator/passive_tree.py** | PassiveTree.lua loader and graph caching | `load_passive_tree() -> PassiveTreeGraph`, `get_node(node_id: int) -> Node` | Lua file paths | PassiveTreeGraph (adjacency list) | Epic 1 Story 1.7 |
| **calculator/build_calculator.py** | High-level calculation API | `calculate_build_stats(build: BuildData) -> BuildStats` | BuildData | BuildStats | Epic 1 Story 1.5 |
| **models/build_data.py** | Build configuration data model | BuildData dataclass | N/A (data structure) | N/A | Epic 1 Story 1.1 |
| **models/build_stats.py** | Calculated statistics data model | BuildStats dataclass | N/A (data structure) | N/A | Epic 1 Story 1.5 |

### Data Models and Contracts

#### BuildData (src/models/build_data.py)

**Purpose:** Represents a complete PoE 2 build configuration parsed from PoB code.

```python
from dataclasses import dataclass, field
from typing import Optional, Set, List
from enum import Enum

class CharacterClass(Enum):
    """PoE 2 character classes"""
    WITCH = "Witch"
    WARRIOR = "Warrior"
    RANGER = "Ranger"
    # ... other classes

@dataclass
class Item:
    """Equipment item"""
    slot: str  # "Weapon1", "BodyArmour", etc.
    name: str
    rarity: str  # "Normal", "Magic", "Rare", "Unique"
    item_level: int
    stats: dict  # Modifiers and stats

@dataclass
class Skill:
    """Active skill gem"""
    name: str
    level: int
    quality: int
    enabled: bool
    support_gems: List[str]

@dataclass
class BuildData:
    """Complete build configuration"""
    # Character identity
    character_class: CharacterClass
    level: int  # 1-100
    ascendancy: Optional[str]  # "Elementalist", "Blood Mage", etc.

    # Passive tree
    passive_nodes: Set[int]  # Set of allocated passive node IDs

    # Equipment and skills
    items: List[Item]
    skills: List[Skill]

    # PoB metadata
    tree_version: str  # "3_24" for PoE 2
    build_name: Optional[str] = None
    notes: Optional[str] = None

    # Calculated properties
    @property
    def allocated_point_count(self) -> int:
        return len(self.passive_nodes)

    @property
    def unallocated_points(self) -> int:
        """Calculate unallocated points based on level"""
        max_points = self.level + 21  # PoE 2 formula (verify)
        return max(0, max_points - self.allocated_point_count)
```

#### BuildStats (src/models/build_stats.py)

**Purpose:** Calculated statistics returned by PoB engine.

```python
from dataclasses import dataclass
from typing import Dict

@dataclass
class BuildStats:
    """Calculated character statistics from PoB engine"""
    # Offensive stats
    total_dps: float  # Combined DPS from all skills

    # Defensive stats
    effective_hp: float  # EHP calculation
    life: int
    energy_shield: int
    mana: int

    # Resistances (percentage, -60 to +90)
    resistances: Dict[str, int] = field(default_factory=lambda: {
        "fire": 0,
        "cold": 0,
        "lightning": 0,
        "chaos": 0
    })

    # Additional defensive stats
    armour: int = 0
    evasion: int = 0
    block_chance: float = 0.0
    spell_block_chance: float = 0.0

    # Utility stats
    movement_speed: float = 0.0

    def to_dict(self) -> dict:
        """Serialize for JSON responses"""
        return {
            "dps": self.total_dps,
            "ehp": self.effective_hp,
            "life": self.life,
            "es": self.energy_shield,
            "mana": self.mana,
            "resistances": self.resistances,
            "armour": self.armour,
            "evasion": self.evasion,
        }
```

#### PassiveTreeGraph (src/calculator/passive_tree.py)

**Purpose:** In-memory representation of PoB passive tree for pathfinding.

```python
from dataclasses import dataclass
from typing import Dict, Set, List

@dataclass
class PassiveNode:
    """Single passive skill node"""
    node_id: int
    name: str
    stats: List[str]  # Stat modifiers
    is_keystone: bool
    is_notable: bool
    is_mastery: bool
    position: tuple[float, float]  # x, y coordinates

@dataclass
class PassiveTreeGraph:
    """Complete passive tree graph structure"""
    nodes: Dict[int, PassiveNode]  # node_id -> PassiveNode
    edges: Dict[int, Set[int]]  # node_id -> set of connected node_ids
    class_start_nodes: Dict[str, int]  # "Witch" -> starting node_id

    def get_neighbors(self, node_id: int) -> Set[int]:
        """Get all nodes connected to given node"""
        return self.edges.get(node_id, set())

    def is_connected(self, from_node: int, to_node: int, allocated: Set[int]) -> bool:
        """BFS to check if path exists using only allocated nodes"""
        # Implementation in Epic 1 Story 1.7
        pass
```

### APIs and Interfaces

#### Parser Module API

```python
# src/parsers/pob_parser.py

def parse_pob_code(code: str) -> BuildData:
    """
    Parse Base64-encoded PoB code into BuildData object.

    Args:
        code: Base64 string (PoB import code)

    Returns:
        BuildData object with all build information

    Raises:
        PoBParseError: If code is invalid, corrupted, or unsupported

    Example:
        >>> code = "eNqVVktv..."
        >>> build = parse_pob_code(code)
        >>> print(f"{build.character_class.value}, Level {build.level}")
        Witch, Level 90
    """
    pass

def generate_pob_code(build: BuildData) -> str:
    """
    Generate Base64-encoded PoB code from BuildData object.

    Args:
        build: BuildData object

    Returns:
        Base64 string (PoB import code)

    Raises:
        PoBGenerateError: If build data is invalid

    Example:
        >>> build = BuildData(...)
        >>> code = generate_pob_code(build)
        >>> # Code can be pasted into PoB
    """
    pass
```

#### Calculator Module API

```python
# src/calculator/build_calculator.py

def calculate_build_stats(build: BuildData) -> BuildStats:
    """
    Calculate character statistics using PoB engine.

    This is the primary API for Epic 2 (optimization algorithm).

    Args:
        build: BuildData object with passive tree, items, skills

    Returns:
        BuildStats object with DPS, EHP, resistances, etc.

    Raises:
        CalculationError: If PoB engine fails
        CalculationTimeout: If calculation exceeds 5s (FR-3.4)

    Performance:
        - Single call: <100ms
        - Batch (1000 calls): 150-500ms total

    Thread Safety:
        Safe to call from multiple threads. Each thread gets
        isolated LuaRuntime instance.

    Example:
        >>> build = parse_pob_code(pob_code)
        >>> stats = calculate_build_stats(build)
        >>> print(f"DPS: {stats.total_dps:.0f}, EHP: {stats.effective_hp:.0f}")
        DPS: 125430, EHP: 42150
    """
    engine = get_pob_engine()  # Thread-local engine
    return engine.calculate(build)

# src/calculator/pob_engine.py

class PoBCalculationEngine:
    """
    Encapsulates Lupa/LuaJIT runtime with HeadlessWrapper.lua loaded.

    One instance per thread (thread-local storage pattern).
    """

    def __init__(self):
        """Initialize Lupa runtime and load HeadlessWrapper.lua"""
        pass

    def calculate(self, build: BuildData) -> BuildStats:
        """Execute PoB calculation and extract stats"""
        pass

    def cleanup(self):
        """Release Lua runtime resources"""
        pass

def get_pob_engine() -> PoBCalculationEngine:
    """
    Get thread-local PoB calculation engine.

    Returns:
        PoBCalculationEngine instance for current thread

    Thread Safety:
        Each thread gets isolated engine instance. No shared state.
    """
    pass
```

### Workflows and Sequencing

#### Workflow 1: Parse PoB Code

```
[User] Provides PoB code string
  ↓
[Step 1] Validate input size (<100KB)
  ├─ Pass → Continue
  └─ Fail → Raise PoBParseError("Code too large: X KB")
  ↓
[Step 2] Base64 decode (stdlib base64.b64decode)
  ├─ Pass → Compressed bytes
  └─ Fail → Raise PoBParseError("Invalid Base64 encoding")
  ↓
[Step 3] zlib decompress (stdlib zlib.decompress)
  ├─ Pass → XML string
  └─ Fail → Raise PoBParseError("Failed to decompress (corrupted data)")
  ↓
[Step 4] Parse XML using xmltodict
  ├─ Pass → Python dict
  └─ Fail → Raise PoBParseError("Unable to parse XML structure")
  ↓
[Step 5] Extract build data from dict
  • character_class = root["PathOfBuilding"]["Build"]["className"]
  • level = int(root["PathOfBuilding"]["Build"]["level"])
  • passive_nodes = parse passive node IDs from spec string
  • items = parse item list
  • skills = parse skill list
  ↓
[Step 6] Validate build data
  • Check PoE 2 version markers (reject PoE 1 codes)
  • Verify required fields present
  • Validate level range (1-100)
  ↓
[Step 7] Construct BuildData object
  ↓
[Return] BuildData instance
```

#### Workflow 2: Calculate Build Stats

```
[Input] BuildData object
  ↓
[Step 1] Get thread-local PoB engine
  • Call get_pob_engine()
  • If first call in thread → Initialize new PoBCalculationEngine
  • Else → Return cached instance from threading.local()
  ↓
[Step 2] Convert BuildData → Lua-compatible format
  • Serialize passive_nodes set → Lua table
  • Serialize items → Lua item objects
  • Serialize skills → Lua skill objects
  ↓
[Step 3] Call Lua function via Lupa
  lua_code = """
    local build = loadBuildFromXML(xml_string)
    build:BuildCalcs()
    return {
      dps = build.calcs.TotalDPS,
      life = build.calcs.Life,
      ehp = build.calcs.EHP,
      -- ... extract all stats
    }
  """
  results = lua_runtime.execute(lua_code)
  ↓
[Step 4] Convert Lua results → BuildStats
  stats = BuildStats(
    total_dps=results["dps"],
    effective_hp=results["ehp"],
    life=results["life"],
    resistances={...},
    ...
  )
  ↓
[Step 5] Validate results
  • Check for NaN values → Log warning
  • Check for zero DPS → May indicate unsupported build
  ↓
[Return] BuildStats instance

Performance Notes:
- First call per thread: ~200ms (Lua compilation)
- Subsequent calls: <100ms (reuse compiled code)
- Batch 1000 calls: 150-500ms (amortized compilation)
```

#### Workflow 3: Load Passive Tree Graph (One-Time Initialization)

```
[Startup] Application initialization
  ↓
[Step 1] Locate PassiveTree.lua file
  path = "external/pob-engine/src/Data/PassiveTree.lua"
  ↓
[Step 2] Load Lua file via Lupa
  lua_runtime = lupa.LuaRuntime()
  tree_data = lua_runtime.execute(f"dofile('{path}')")
  ↓
[Step 3] Parse Lua tree structure → Python adjacency list
  nodes: Dict[int, PassiveNode] = {}
  edges: Dict[int, Set[int]] = {}

  for node_id, node_data in tree_data["nodes"].items():
    nodes[node_id] = PassiveNode(
      node_id=node_id,
      name=node_data["name"],
      stats=node_data["stats"],
      is_keystone=node_data.get("isKeystone", False),
      ...
    )

    edges[node_id] = set(node_data.get("out", []))
  ↓
[Step 4] Cache in memory (global variable or singleton)
  _PASSIVE_TREE_CACHE = PassiveTreeGraph(nodes, edges, ...)
  ↓
[Usage] Optimization algorithm queries tree
  tree = get_passive_tree()  # Returns cached instance
  neighbors = tree.get_neighbors(node_id)
```

## Non-Functional Requirements

### Performance

Epic 1 delivers the performance foundation for the entire system. All optimization algorithm iterations depend on calculation speed.

**Target Metrics (from NFR-1 and FR-3.3):**

| Metric | Target | Measurement Method | Acceptance |
|--------|--------|-------------------|------------|
| Single calculation latency | <100ms | Time parse_pob_code() + calculate_build_stats() | 95th percentile <100ms |
| Batch calculation (1000 iters) | 150-500ms | Time loop of 1000 calculate_build_stats() calls | Mean <500ms |
| Parse overhead | <500ms | Time parse_pob_code() only | 95th percentile <500ms |
| Memory per session | <100MB | Process memory delta before/after | Max 100MB |
| Lua compilation (first call) | <200ms | Time first calculate_build_stats() in thread | Max 200ms |

**Performance Strategies:**

1. **Lua Function Precompilation**
   - Load and compile HeadlessWrapper.lua once per thread
   - Reuse compiled Lua functions for all calculations in session
   - Amortize compilation cost across 1000+ calls

2. **Object Reuse**
   - Cache PassiveTree.lua graph in memory (load once at startup)
   - Reuse Lupa LuaRuntime instances (thread-local storage)
   - Minimize Python↔Lua data serialization overhead

3. **Memory Management**
   - Explicit Lua garbage collection after batch operations
   - Release LuaRuntime resources when threads complete
   - Monitor memory usage with logging warnings if >80MB

4. **Profiling Requirements**
   - Profile with cProfile during development
   - Log timing metrics for calculations >100ms
   - Optimize hot paths identified in profiling

**Performance Testing:**
- Unit tests verify single calculation <100ms (pytest-benchmark)
- Integration tests verify batch performance 150-500ms
- Load tests validate performance under 10 concurrent sessions

### Security

Epic 1 handles untrusted user input (PoB codes), requiring defensive coding and input validation.

**Input Validation (FR-1.1, FR-1.2, FR-1.3):**

1. **Size Limits**
   - Reject PoB codes >100KB before processing
   - Prevents memory exhaustion attacks
   - Error: "Build code too large: X KB. Maximum: 100KB"

2. **Format Validation**
   - Validate Base64 encoding before decode
   - Validate zlib compression before decompress
   - Validate XML structure before parse
   - Catch all exceptions → structured PoBParseError

3. **Content Sanitization**
   - Escape XML content when logging errors (prevent log injection)
   - Never execute user-provided Lua code (only PoB's official scripts)
   - Validate passive node IDs against PassiveTree.lua (prevent invalid nodes)

**Lua Sandbox (NFR-3):**

- **Read-Only PoB Engine:** HeadlessWrapper.lua cannot write files
- **Stub Functions:** Python stubs (Deflate, Inflate, ConPrintf) have no side effects
- **No System Access:** SpawnProcess, OpenURL stubs are no-ops
- **Timeout Protection:** 5-second timeout per calculation (FR-3.4) prevents infinite loops

**Dependency Security:**

- **Pinned Versions:** Lupa 2.0, xmltodict 0.13.0 in requirements.txt
- **Vulnerability Scanning:** Run `pip-audit` monthly
- **PoB Version Pinning:** Git submodule pinned to specific commit hash in POB_VERSION.txt
- **Supply Chain:** Only use official PyPI packages, verify checksums

**Data Privacy (NFR-3, NFR-8):**

- **No Persistent Storage:** PoB codes never saved to disk
- **No Logging of Codes:** Logs contain build summary (class, level) but not full code
- **Session Isolation:** Thread-local LuaRuntime prevents cross-user data leaks (FR-3.5)

### Reliability/Availability

Epic 1 must handle edge cases and errors gracefully without crashing the application.

**Error Handling Strategy (FR-3.4):**

1. **Parsing Errors (parsers/ module)**
   ```python
   try:
       decoded = base64.b64decode(code)
   except Exception as e:
       raise PoBParseError("Invalid Base64 encoding") from e
   ```
   - Never crash on invalid input
   - Always raise custom exception (PoBParseError)
   - Include original exception as context (from e)

2. **Calculation Errors (calculator/ module)**
   ```python
   try:
       stats = lua_runtime.execute(calc_code)
   except lupa.LuaError as e:
       logger.error(f"Lua calculation failed: {e}")
       raise CalculationError("PoB engine failed") from e
   except TimeoutError:
       raise CalculationTimeout("Calculation exceeded 5s") from None
   ```
   - Catch Lupa-specific errors (LuaError)
   - Implement 5-second timeout per calculation
   - Log technical details, raise user-friendly exception

3. **Resource Cleanup**
   - Try/finally blocks ensure Lua resources released
   - Context managers for LuaRuntime lifecycle
   - Explicit cleanup on session completion or timeout

**Timeout Implementation (FR-3.4):**

```python
import signal

def timeout_handler(signum, frame):
    raise TimeoutError("Calculation timeout")

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(5)  # 5-second timeout
try:
    stats = calculate_build_stats(build)
finally:
    signal.alarm(0)  # Cancel timeout
```

**Session Isolation (FR-3.5):**

- Thread-local LuaRuntime instances (one per thread)
- No shared state between sessions
- Session cleanup after 15 minutes idle
- Resource limits: Max 10 concurrent sessions

**Graceful Degradation:**

- If calculation fails for one variant, log error and continue optimization
- If PassiveTree.lua missing, fail fast with clear error message
- If Lupa import fails, display: "Lupa library not installed. Run: pip install lupa"

**Testing for Reliability:**

- Fuzz testing with corrupted PoB codes
- Stress testing with 100+ concurrent calculations
- Memory leak testing with 1000+ sequential calculations
- Timeout testing with intentionally slow Lua code

### Observability

Epic 1 requires detailed logging for debugging Lua integration issues and performance problems.

**Logging Strategy (FR-6.1):**

**Log Levels:**
- **DEBUG:** Lua function calls, data serialization, tree graph loading
- **INFO:** Successful parsing, calculation completion, session creation
- **WARNING:** Parse errors, slow calculations (>100ms), memory warnings (>80MB)
- **ERROR:** Lua errors, calculation timeouts, unexpected exceptions

**Log Format:**
```
[2025-10-10 14:32:15,123] [INFO] pob_parser.py:45 - Parsed PoB code: Witch Level 90, 87 passive nodes
[2025-10-10 14:32:15,234] [DEBUG] pob_engine.py:78 - Initializing Lupa runtime (thread_id=12345)
[2025-10-10 14:32:15,456] [DEBUG] build_calculator.py:92 - Calculation complete: DPS=125430, EHP=42150 (elapsed=87ms)
[2025-10-10 14:32:16,789] [WARNING] build_calculator.py:105 - Slow calculation: 142ms (threshold=100ms)
[2025-10-10 14:32:20,012] [ERROR] pob_engine.py:123 - Lua calculation failed: attempt to index nil value
```

**Key Metrics to Log:**

| Event | Log Level | Data Logged |
|-------|-----------|-------------|
| Parse PoB code | INFO | Class, level, passive count, parse time |
| Initialize Lupa | DEBUG | Thread ID, HeadlessWrapper.lua path |
| Calculate stats | DEBUG | DPS, EHP, elapsed time |
| Slow calculation | WARNING | Elapsed time, threshold exceeded |
| Parse error | WARNING | Error type, code size, exception message |
| Calculation error | ERROR | Lua error message, stack trace |
| Timeout | ERROR | Session ID, elapsed time |

**Performance Monitoring:**

- Log timing for all calculations >100ms
- Log memory usage if session exceeds 80MB
- Aggregate metrics: Mean/P95/P99 calculation times per hour
- Alert if P95 latency exceeds 150ms

**Debugging Support:**

- **Verbose Mode:** Environment variable `DEBUG=1` enables DEBUG logs
- **Lua Stack Traces:** Capture full Lua stack on errors
- **Build Summaries:** Log character class, level, passive count (NOT full code)
- **Session Tracking:** Unique session IDs for tracing multi-step workflows

**Log Rotation (NFR-9):**

```python
import logging
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    "logs/optimizer.log",
    maxBytes=10 * 1024 * 1024,  # 10MB
    backupCount=5  # Keep 5 old files
)
```

**Testing Observability:**

- Verify logs written for all error paths
- Validate log format parseable by log aggregators
- Test log rotation (create >10MB logs, verify rotation)
- Ensure no sensitive data (PoB codes) logged

## Dependencies and Integrations

### Python Dependencies (requirements.txt)

Epic 1 requires these production dependencies:

```txt
# Core dependencies
lupa==2.0              # Python-LuaJIT bindings for PoB engine integration
xmltodict==0.13.0      # PoB XML parsing to Python dicts

# Standard library (no installation required)
# - base64: PoB code decoding
# - zlib: PoB code decompression
# - threading: Thread-local LuaRuntime instances
```

### Development Dependencies (requirements-dev.txt)

```txt
# Testing
pytest==7.4.3           # Test framework
pytest-benchmark==4.0.0 # Performance benchmarking
pytest-cov==4.1.0       # Coverage reporting

# Code quality
mypy==1.7.1            # Type checking
black==23.11.0         # Code formatting
ruff==0.1.6            # Fast linting
```

### External Dependencies (Git Submodule)

**Path of Building Engine**
- **Repository:** https://github.com/PathOfBuildingCommunity/PathOfBuilding-PoE2
- **Type:** Git submodule at `external/pob-engine/`
- **Pinned Version:** Commit hash documented in `POB_VERSION.txt`
- **License:** MIT (compatible with project)

**Required PoB Files:**

| File Path | Purpose | Usage in Epic 1 |
|-----------|---------|-----------------|
| `HeadlessWrapper.lua` | Main calculation entry point | Loaded via Lupa, provides BuildCalcs() function |
| `src/Data/PassiveTree.lua` | Passive tree node graph | Parsed to Python adjacency list for pathfinding |
| `src/Data/Classes.lua` | Character class starting nodes | Validates passive tree connectivity |
| `src/Modules/CalcPerform.lua` | DPS calculation formulas | Called internally by HeadlessWrapper |

**Submodule Setup:**

```bash
# Initialize submodule (one-time setup)
git submodule add https://github.com/PathOfBuildingCommunity/PathOfBuilding-PoE2.git external/pob-engine
git submodule update --init --recursive

# Pin to specific commit
cd external/pob-engine
git checkout <commit-hash>
cd ../..
echo "<commit-hash>" > POB_VERSION.txt
git add external/pob-engine POB_VERSION.txt
git commit -m "Pin PoB engine to commit <commit-hash>"
```

### Integration Points

**Epic 1 → External/PoB Engine:**

```
Python (calculator/pob_engine.py)
  ↓ Lupa library
Lua Runtime
  ↓ dofile()
HeadlessWrapper.lua
  ↓ require()
PoB Modules (CalcPerform, PassiveTree, Classes)
  ↓
Return calculation results to Python
```

**Epic 1 → Epic 2 Contract:**

Epic 1 exposes these APIs to Epic 2 (optimization algorithm):

```python
# Primary API for optimization loop
from calculator.build_calculator import calculate_build_stats
from parsers.pob_parser import parse_pob_code
from parsers.pob_generator import generate_pob_code
from models.build_data import BuildData
from models.build_stats import BuildStats

# Epic 2 usage:
build = parse_pob_code(pob_code)
build.passive_nodes.add(new_node_id)  # Modify tree
stats = calculate_build_stats(build)  # Recalculate
if stats.total_dps > best_dps:
    best_build = build
```

**No External Services:**

Epic 1 has ZERO network dependencies:
- No HTTP APIs called
- No database connections
- No cloud services
- 100% local computation

### Version Compatibility

| Component | Supported Versions | Notes |
|-----------|-------------------|-------|
| Python | 3.10, 3.11, 3.12 | Lupa requires 3.10+ |
| Lupa | 2.0 | Pinned version for stability |
| xmltodict | 0.13.0 | Stable API, no breaking changes expected |
| PoB Engine | PoE 2 beta (Dec 2024+) | Pinned to specific commit hash |

**Update Strategy:**

- **Python packages:** Monthly security updates via `pip-audit`, test before merging
- **PoB engine:** Update when PoE 2 game patches released, validate with parity tests
- **Breaking changes:** If PoB changes HeadlessWrapper.lua API, implement adapter layer

## Acceptance Criteria (Authoritative)

These criteria define "done" for Epic 1. All must pass before Epic 2 begins.

### Story 1.1: Parse PoB Import Code

✅ **AC-1.1.1:** System decodes Base64 PoB codes successfully (100+ sample codes)
✅ **AC-1.1.2:** System decompresses zlib-encoded XML without errors
✅ **AC-1.1.3:** System parses XML into Python data structure (BuildData object)
✅ **AC-1.1.4:** System extracts: character level, class, allocated passive nodes, items, skills
✅ **AC-1.1.5:** System validates PoB code format (detect corrupted codes)
✅ **AC-1.1.6:** System rejects codes >100KB with clear error message

**Test Method:** Unit tests with fixtures (`tests/fixtures/sample_builds/*.txt`)

---

### Story 1.2: Setup Lupa + LuaJIT Runtime

✅ **AC-1.2.1:** Lupa library installed and tested (`pip install lupa`)
✅ **AC-1.2.2:** LuaJIT runtime initializes successfully in Python
✅ **AC-1.2.3:** Can load and execute simple Lua scripts from Python
✅ **AC-1.2.4:** Lua global namespace accessible from Python
✅ **AC-1.2.5:** Python can call Lua functions and retrieve results

**Test Method:** Integration test (`tests/integration/test_lupa_basic.py`)

---

### Story 1.3: Implement Required Stub Functions

✅ **AC-1.3.1:** Implement `Deflate(str)` and `Inflate(str)` using Python `zlib`
✅ **AC-1.3.2:** Implement `ConPrintf(...)` as no-op (or print to console for debugging)
✅ **AC-1.3.3:** Implement `ConPrintTable(table)` as no-op
✅ **AC-1.3.4:** Implement `SpawnProcess(...)` and `OpenURL(...)` as no-ops (headless mode)
✅ **AC-1.3.5:** All stubs accessible from Lua global namespace
✅ **AC-1.3.6:** No errors when HeadlessWrapper.lua calls stub functions

**Test Method:** Integration test with HeadlessWrapper.lua execution

---

### Story 1.4: Load HeadlessWrapper.lua and PoB Modules

✅ **AC-1.4.1:** System locates HeadlessWrapper.lua in `external/pob-engine/`
✅ **AC-1.4.2:** System loads HeadlessWrapper.lua via Lupa without errors
✅ **AC-1.4.3:** System loads required PoB modules: Data/PassiveTree.lua, Data/Classes.lua
✅ **AC-1.4.4:** System initializes PoB calculation context
✅ **AC-1.4.5:** No Lua errors during module loading
✅ **AC-1.4.6:** PoB passive tree data accessible (nodes, connections, stats)

**Test Method:** Integration test verifying tree graph loaded

---

### Story 1.5: Execute Single Build Calculation

✅ **AC-1.5.1:** System accepts PoB XML data as input (BuildData object)
✅ **AC-1.5.2:** System calls PoB calculation engine via HeadlessWrapper
✅ **AC-1.5.3:** System extracts calculated stats: DPS, Life, EHP, resistances
✅ **AC-1.5.4:** Calculation completes in <100ms (single call)
✅ **AC-1.5.5:** No Lua errors during calculation
✅ **AC-1.5.6:** Results are numeric (not nil/undefined)

**Test Method:** Integration test with sample build, verify stats returned

---

### Story 1.6: Validate Calculation Accuracy (Parity Testing)

✅ **AC-1.6.1:** Create 10 test builds with known PoB GUI results
✅ **AC-1.6.2:** Calculate each build using headless engine
✅ **AC-1.6.3:** Compare results to PoB GUI: DPS, Life, EHP, resistances
✅ **AC-1.6.4:** All results within 0.1% tolerance (per NFR-1)
✅ **AC-1.6.5:** Document any discrepancies and root cause
✅ **AC-1.6.6:** Create automated parity test suite

**Test Method:** `tests/integration/test_pob_parity.py` with expected values

---

### Story 1.7: Handle PoE 2-Specific Passive Tree Data

✅ **AC-1.7.1:** System loads PoE 2 passive tree JSON/Lua data
✅ **AC-1.7.2:** System understands node IDs, connections (edges), and node stats
✅ **AC-1.7.3:** System identifies character class starting positions
✅ **AC-1.7.4:** System validates allocated nodes are connected (no orphan nodes)
✅ **AC-1.7.5:** System handles Notable/Keystone/Small passive types

**Test Method:** Unit tests for PassiveTreeGraph class

---

### Story 1.8: Batch Calculation Optimization

✅ **AC-1.8.1:** Batch calculate 1000 builds in <1 second (150-500ms target)
✅ **AC-1.8.2:** Pre-compile Lua functions (compile once, call 1000x)
✅ **AC-1.8.3:** Reuse Build objects where possible (avoid recreation overhead)
✅ **AC-1.8.4:** Memory usage <100MB during batch processing
✅ **AC-1.8.5:** No memory leaks (verify with repeated runs)

**Test Method:** Performance test with pytest-benchmark

---

### Epic-Level Acceptance Criteria

✅ **Epic Success Criterion 1:** Parse 100 sample PoB codes with 100% success rate
✅ **Epic Success Criterion 2:** Calculate stats for each with <100ms per calculation (95th percentile)
✅ **Epic Success Criterion 3:** Batch 1000 calculations in 150-500ms
✅ **Epic Success Criterion 4:** Accuracy within ±0.1% of PoB GUI (all test builds)
✅ **Epic Success Criterion 5:** Memory <100MB per session
✅ **Epic Success Criterion 6:** Zero Lua runtime crashes or unhandled exceptions

**Sign-Off Required:** Product Owner validates parity testing results before Epic 2 begins

## Traceability Mapping

| Acceptance Criteria | Spec Section | Component/API | Test Idea |
|---------------------|--------------|---------------|-----------|
| AC-1.1.1: Decode Base64 | Data Models: BuildData | `parsers/pob_parser.py` | Unit test: `test_parse_valid_base64()` |
| AC-1.1.2: Decompress zlib | Workflows: Parse PoB Code Step 3 | `parsers/pob_parser.py` | Unit test: `test_decompress_zlib()` |
| AC-1.1.3: Parse XML | Data Models: BuildData | `parsers/pob_parser.py` via xmltodict | Unit test: `test_parse_xml_to_builddata()` |
| AC-1.1.4: Extract build fields | Data Models: BuildData fields | `parsers/pob_parser.py` | Unit test: `test_extract_character_class_level()` |
| AC-1.1.5: Validate format | APIs: parse_pob_code() raises PoBParseError | `parsers/pob_parser.py` | Unit test: `test_reject_corrupted_codes()` |
| AC-1.1.6: Reject >100KB | NFR: Security Input Validation | `parsers/pob_parser.py` | Unit test: `test_reject_oversized_codes()` |
| AC-1.2.1-1.2.5: Lupa setup | Technology Stack: Lupa 2.0 | `calculator/pob_engine.py` | Integration test: `test_lupa_basic_execution()` |
| AC-1.3.1: Deflate/Inflate stubs | Services: stub_functions.py | `calculator/stub_functions.py` | Unit test: `test_deflate_inflate_roundtrip()` |
| AC-1.3.2-1.3.4: Other stubs | Services: stub_functions.py | `calculator/stub_functions.py` | Unit test: `test_stubs_no_errors()` |
| AC-1.4.1-1.4.6: Load PoB modules | Workflows: Load Passive Tree Graph | `calculator/pob_engine.py` | Integration test: `test_load_headless_wrapper()` |
| AC-1.5.1-1.5.6: Single calculation | APIs: calculate_build_stats() | `calculator/build_calculator.py` | Integration test: `test_single_calculation()` |
| AC-1.6.1-1.6.6: Parity testing | NFR: Performance, Detailed Design | All calculator/* | Integration test: `test_pob_parity_10_builds()` |
| AC-1.7.1-1.7.5: Passive tree | Data Models: PassiveTreeGraph | `calculator/passive_tree.py` | Unit test: `test_passive_tree_graph_structure()` |
| AC-1.8.1-1.8.5: Batch performance | NFR: Performance Strategies | `calculator/build_calculator.py` | Performance test: `test_batch_1000_calculations()` |

## Risks, Assumptions, Open Questions

### Risks

**Risk 1: PoB Engine API Changes**
- **Description:** PoB community updates HeadlessWrapper.lua API incompatibly
- **Likelihood:** Medium (PoB actively maintained, PoE 2 still in beta)
- **Impact:** High (breaks all calculations until fixed)
- **Mitigation:**
  - Pin PoB to specific commit hash in submodule
  - Monitor PoB repository for breaking changes
  - Implement adapter layer if API changes
  - Monthly testing against latest PoB commit
- **Contingency:** If PoB breaks compatibility, freeze on last working version, open issue with PoB team

**Risk 2: Lupa Performance Doesn't Meet Targets**
- **Description:** Python↔Lua serialization overhead prevents <100ms calculations
- **Likelihood:** Low (validated in prototype research)
- **Impact:** High (entire optimization approach infeasible)
- **Mitigation:**
  - Early performance testing (Story 1.5, 1.8)
  - Profile and optimize hot paths
  - Pre-compile Lua functions
  - Minimize data serialization
- **Contingency:** If <100ms impossible, relax to <200ms and increase convergence threshold

**Risk 3: PoE 2 Passive Tree Format Differs from PoE 1**
- **Description:** PassiveTree.lua structure incompatible with assumptions
- **Likelihood:** Medium (PoE 2 has different passive tree design)
- **Impact:** Medium (requires parser updates)
- **Mitigation:**
  - Verify PassiveTree.lua format early (Story 1.4, 1.7)
  - Design flexible parser (dict-based, not hardcoded)
  - Write comprehensive tests
- **Contingency:** Adapt parser to actual PoE 2 format, may require 1-2 days rework

**Risk 4: Memory Leaks in Lupa/LuaJIT**
- **Description:** Lua runtime doesn't release memory properly
- **Likelihood:** Low (Lupa is mature)
- **Impact:** Medium (server crashes after repeated use)
- **Mitigation:**
  - Explicit cleanup after sessions
  - Memory leak testing (Story 1.8)
  - Monitor memory with logging
  - Thread-local instances (limit scope)
- **Contingency:** Restart LuaRuntime periodically, investigate Lupa garbage collection

### Assumptions

**Assumption 1:** Path of Building PoE 2 repository remains MIT licensed and publicly accessible
**Validation:** Verify license before Epic 1 begins, monitor for license changes

**Assumption 2:** HeadlessWrapper.lua works without PoB GUI dependencies
**Validation:** Confirmed in prototype research, validate in Story 1.2-1.4

**Assumption 3:** PoE 2 passive tree graph fits in <50MB memory
**Validation:** Test with actual PassiveTree.lua file (Story 1.7)

**Assumption 4:** PoB calculation accuracy deterministic (same input → same output)
**Validation:** Parity testing with repeated calculations (Story 1.6)

**Assumption 5:** Python zlib compatible with PoB's Lua Deflate/Inflate
**Validation:** Round-trip testing: Python compress → Lua decompress → Python (Story 1.3)

### Open Questions

**Q1:** What is the exact PoE 2 max passive points formula?
**Current Assumption:** `max_points = level + 21` (verify with PoE 2 game data)
**Resolution Plan:** Test with level 100 character, validate against PoB GUI

**Q2:** Does HeadlessWrapper.lua require specific Lua module paths?
**Current Assumption:** Relative paths from HeadlessWrapper.lua location
**Resolution Plan:** Test in Story 1.4, document required directory structure

**Q3:** How to handle PoB configuration flags (enemy type, map mods, etc.)?
**Current Assumption:** Use default configuration, ignore for MVP
**Resolution Plan:** Epic 1 uses defaults, Epic 2 may expose configuration options

**Q4:** What passive tree version markers distinguish PoE 1 vs PoE 2 codes?
**Current Assumption:** XML root element or tree_version field
**Resolution Plan:** Analyze sample PoE 1 and PoE 2 codes (Story 1.1)

## Test Strategy Summary

### Test Pyramid Distribution

- **Unit Tests (60%):** 30-40 tests
  - Parsers: Base64, zlib, XML, BuildData extraction
  - Stubs: Deflate/Inflate, ConPrintf round-trips
  - Models: BuildData, BuildStats dataclass validation
  - Fast (<1s total suite), no external dependencies

- **Integration Tests (30%):** 15-20 tests
  - Lupa integration: Load HeadlessWrapper, execute Lua
  - PoB engine: Single calculation, extract stats
  - Parity testing: Compare with PoB GUI results
  - Passive tree: Load PassiveTree.lua, graph structure
  - Moderate speed (10-30s), requires external/pob-engine/

- **Performance Tests (10%):** 5-10 tests
  - Single calculation latency (<100ms)
  - Batch calculations (1000 in 150-500ms)
  - Memory usage (<100MB)
  - Threading: 10 concurrent calculations
  - Slow (1-5 min), benchmarking focus

### Key Test Scenarios

**Scenario 1: Happy Path (End-to-End)**
```python
def test_parse_calculate_generate_roundtrip():
    """
    Full workflow: Parse PoB code → Calculate stats → Modify tree → Regenerate code
    """
    # Parse
    build = parse_pob_code(SAMPLE_WITCH_CODE)
    assert build.character_class == CharacterClass.WITCH
    assert build.level == 90

    # Calculate baseline
    stats_before = calculate_build_stats(build)
    assert stats_before.total_dps > 0

    # Modify tree (add one node)
    build.passive_nodes.add(12345)

    # Recalculate
    stats_after = calculate_build_stats(build)
    assert stats_after.total_dps != stats_before.total_dps

    # Regenerate code
    new_code = generate_pob_code(build)
    assert len(new_code) > 0

    # Verify round-trip
    build2 = parse_pob_code(new_code)
    assert build2.passive_nodes == build.passive_nodes
```

**Scenario 2: Error Handling**
```python
def test_invalid_inputs_raise_exceptions():
    """Verify all invalid inputs raise appropriate exceptions"""

    # Corrupted Base64
    with pytest.raises(PoBParseError, match="Invalid Base64"):
        parse_pob_code("!!!invalid!!!")

    # Oversized code
    huge_code = "A" * (101 * 1024)
    with pytest.raises(PoBParseError, match="too large"):
        parse_pob_code(huge_code)

    # Invalid BuildData
    invalid_build = BuildData(level=-1, ...)
    with pytest.raises(ValueError):
        calculate_build_stats(invalid_build)
```

**Scenario 3: Performance Benchmarks**
```python
@pytest.mark.benchmark
def test_batch_calculation_performance(benchmark):
    """Batch 1000 calculations must complete in <500ms"""
    build = parse_pob_code(SAMPLE_BUILD)

    def batch_calc():
        for _ in range(1000):
            calculate_build_stats(build)

    result = benchmark(batch_calc)
    assert result.mean < 0.5  # <500ms
```

### Coverage Targets

- **Overall Coverage:** >80% (measured with pytest-cov)
- **Critical Paths:** >90%
  - parsers/pob_parser.py
  - calculator/pob_engine.py
  - calculator/build_calculator.py
- **Models:** 100% (dataclasses, simple logic)

### Continuous Integration

```bash
# Run on every commit
pytest tests/unit/                    # Fast unit tests
pytest tests/integration/ -m "not slow"  # Quick integration tests

# Run nightly
pytest tests/integration/ --cov=src --cov-report=html  # Full suite
pytest tests/performance/             # Performance benchmarks
```

### Parity Testing Process

1. **Collect Sample Builds**
   - Export 10+ builds from PoB GUI (diverse classes, levels, trees)
   - Manually record stats in PoB: DPS, Life, EHP, resistances
   - Save as `tests/fixtures/parity_build_N.txt`

2. **Automated Parity Tests**
   ```python
   @pytest.mark.parametrize("build_id,expected_dps", [
       (1, 125430),
       (2, 87652),
       # ... 10+ builds
   ])
   def test_parity(build_id, expected_dps):
       code = load_fixture(f"parity_build_{build_id}.txt")
       build = parse_pob_code(code)
       stats = calculate_build_stats(build)

       tolerance = expected_dps * 0.001  # 0.1%
       assert abs(stats.total_dps - expected_dps) < tolerance
   ```

3. **Continuous Monitoring**
   - Re-run parity tests monthly against latest PoB version
   - Alert if any test fails (PoB engine diverged)

---

**Epic 1 Tech Spec Status:** ✅ COMPLETE
**Next Steps:** Review with Product Owner → Epic 2 begins → Implement optimization algorithm
**Est. Implementation Time:** 2 weeks (Stories 1.1-1.8)

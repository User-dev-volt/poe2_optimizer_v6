# Implementation Guide: Understanding the Architecture

**Project:** poe2_optimizer_v6
**Audience:** Beginner developers new to this codebase
**Purpose:** Help you understand and use the architecture documents effectively

---

## Welcome!

This guide will help you understand the architecture and start implementing the PoE 2 Passive Tree Optimizer. If you're feeling overwhelmed by the technical documentation, this is your starting point.

**What you'll learn:**
1. How to read and use the architecture document
2. What each component does and why it exists
3. Where to start coding (step-by-step)
4. Common patterns and best practices
5. How to avoid common mistakes

---

## Document Map: Which Document Do I Need?

You have several architecture documents. Here's when to use each:

### **solution-architecture-complete.md** 📘
**When to use:** Your main reference throughout development
**What it contains:**
- Complete system design
- Technology decisions with rationale
- Component responsibilities
- Data flow diagrams
- Security and testing strategies

**How to use it:**
1. Read Sections 1-3 first (overview, requirements, architecture pattern)
2. Reference Section 4 (Technology Stack) when setting up your environment
3. Reference Section 5 (Source Tree) when creating files
4. Reference Section 7 (Component Architecture) when implementing each module

---

### **epic-alignment-matrix.md** 🗺️
**When to use:** Planning your work, understanding dependencies
**What it contains:**
- Epic-to-component mapping
- Story breakdown with estimates
- Implementation sequence
- Dependency chains

**How to use it:**
1. Read before starting each epic
2. Use story breakdown to plan your daily tasks
3. Check dependencies before starting a component

---

### **cohesion-check-report.md** ✅
**When to use:** Verifying your implementation covers all requirements
**What it contains:**
- FR/NFR coverage validation
- Requirements traceability
- Gap analysis

**How to use it:**
1. Reference when implementing a component (e.g., "Does my parser cover FR-1.2?")
2. Use as checklist during code review
3. Verify completed work against requirement mappings

---

### **tech-specs-summary.md** 🔧
**When to use:** During actual coding
**What it contains:**
- API contracts (function signatures, parameters, returns)
- Implementation steps
- Code examples
- Testing requirements

**How to use it:**
1. Open this alongside your code editor
2. Copy API contracts when creating new files
3. Follow implementation steps for each component
4. Use testing sections to write tests

---

### **validation-report-*.md** 📋
**When to use:** Understanding what was fixed during architecture review
**What it contains:**
- Checklist validation results
- Identified gaps and how they were resolved
- Quality gate assessments

**How to use it:**
1. Reference if curious about architecture decisions
2. Generally not needed for day-to-day development

---

## Understanding the System: The Big Picture

### What Are We Building?

A tool that takes a Path of Exile 2 build and automatically finds a better passive skill tree configuration.

**User's perspective:**
1. Paste PoB code into a web form
2. Click "Optimize"
3. Wait 30 seconds to 5 minutes
4. Get a new PoB code with 5-15% better stats

**Behind the scenes (our job):**
1. **Parse** the PoB code (decode Base64, decompress, read XML)
2. **Calculate** stats using Path of Building's Lua engine (via Python)
3. **Optimize** the passive tree (try different node combinations)
4. **Generate** a new PoB code with the improved tree
5. **Display** results with before/after comparison

---

### The Four Main Parts (Components)

#### 1. **Parsers** (`src/parsers/`)
**What:** Converts PoB codes to/from Python objects
**Why:** PoB codes are Base64-encoded, compressed XML. We need structured data.
**Files:**
- `pob_parser.py` - Decode PoB codes
- `pob_generator.py` - Encode PoB codes

**Analogy:** Like a translator between "PoB language" (Base64/XML) and "Python language" (objects/dicts).

---

#### 2. **Calculator** (`src/calculator/`)
**What:** Runs Path of Building calculations (DPS, EHP, etc.)
**Why:** We need to know if a tree change is an improvement. PoB has the formulas.
**Files:**
- `pob_engine.py` - Loads PoB's Lua code into Python
- `stub_functions.py` - Helper functions PoB needs (compression, logging)
- `passive_tree.py` - Loads the tree graph (which nodes connect to which)

**Analogy:** Like having a mini-PoB inside our Python code that we can ask "What's the DPS of this build?"

---

#### 3. **Optimizer** (`src/optimizer/`)
**What:** Finds better passive tree configurations
**Why:** This is our core value - automatically discovering improvements.
**Files:**
- `hill_climbing.py` - Main optimization algorithm
- `tree_validator.py` - Checks if a tree is legal (all nodes connected)
- `neighbor_generator.py` - Creates candidate trees to test
- `budget_tracker.py` - Ensures we don't exceed user's point budget

**Analogy:** Like a chess engine that tries different moves to find the best one.

---

#### 4. **Web** (`src/web/` + `src/frontend/`)
**What:** The user interface (forms, progress bar, results page)
**Why:** Users need a way to interact with our tool.
**Files:**
- `web/app.py` - Flask application setup
- `web/routes.py` - HTTP endpoints (home page, submit form, show results)
- `web/sse.py` - Real-time progress updates
- `frontend/templates/` - HTML pages (Bootstrap 5)
- `frontend/static/js/` - JavaScript for progress bar

**Analogy:** Like the steering wheel, dashboard, and seats in a car - the user-facing parts.

---

## Getting Started: Your First Steps

### Step 0: Prerequisites (Before Writing Code)

**Install required software:**
```bash
# 1. Python 3.10+ (check with)
python --version

# 2. Git (check with)
git --version
```

**Set up the repository:**
```bash
# 3. Clone the repository (if not already done)
# git clone <your-repo-url>
cd poe2_optimizer_v6

# 4. CRITICAL: Initialize PoB submodule
git submodule init
git submodule update

# 5. Verify PoB engine exists
ls external/pob-engine/HeadlessWrapper.lua
# If this file exists, you're good!

# 6. Create Python virtual environment
python -m venv venv

# 7. Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# 8. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 9. Verify Lupa installed
python -c "import lupa; print('Lupa OK')"
```

**If you get errors:**
- `lupa` install fails → Need LuaJIT installed on your system
- Submodule empty → Run `git submodule update --init --recursive`
- Python version wrong → Install Python 3.10+ from python.org

---

### Step 1: Create the Project Structure

**Create all the folders and files from the source tree (Section 5.1 in architecture):**

```bash
mkdir -p src/parsers src/calculator src/optimizer src/web src/frontend/templates src/frontend/static/css src/frontend/static/js src/models src/utils
mkdir -p tests/unit tests/integration tests/e2e
mkdir -p logs docs

# Create __init__.py files (makes folders into Python packages)
touch src/__init__.py
touch src/parsers/__init__.py
touch src/calculator/__init__.py
touch src/optimizer/__init__.py
touch src/web/__init__.py
touch src/models/__init__.py
touch src/utils/__init__.py
```

**Why?** Python needs `__init__.py` files to recognize folders as packages you can import from.

---

### Step 2: Epic 1, Week 1 - Start with Parsers

**Goal:** Get PoB code parsing working (no optimization yet)

#### Day 1-2: Create `src/parsers/pob_parser.py`

**What to do:**
1. Open `tech-specs-summary.md` → Find "parsers/pob_parser.py" section
2. Copy the API contract (function signature)
3. Follow the implementation steps

**Code template to start:**
```python
# src/parsers/pob_parser.py
import base64
import zlib
import xmltodict
from typing import Dict, Any
from src.models.build_data import BuildData

class PoBParseError(Exception):
    """Raised when PoB code parsing fails."""
    pass

def parse_pob_code(code: str) -> BuildData:
    """
    Parse Path of Building import code to structured BuildData.

    Args:
        code: Base64-encoded PoB code string (max 100KB)

    Returns:
        BuildData object with parsed build information

    Raises:
        PoBParseError: If code is invalid, corrupted, or oversized
    """
    # Step 1: Validate size
    if len(code) > 100 * 1024:  # 100KB in bytes
        raise PoBParseError(f"PoB code too large ({len(code)} bytes). Maximum: 102400 bytes")

    # Step 2: Decode Base64
    try:
        decoded_bytes = base64.b64decode(code)
    except Exception as e:
        raise PoBParseError(f"Invalid Base64 encoding: {e}")

    # Step 3: Decompress with zlib
    try:
        xml_string = zlib.decompress(decoded_bytes).decode('utf-8')
    except Exception as e:
        raise PoBParseError(f"Failed to decompress (corrupted data): {e}")

    # Step 4: Parse XML
    try:
        xml_dict = xmltodict.parse(xml_string)
    except Exception as e:
        raise PoBParseError(f"Unable to parse XML structure: {e}")

    # Step 5: Extract BuildData fields
    # TODO: Extract character_class, level, passive_nodes from xml_dict

    # Step 6: Return BuildData
    # return BuildData(...)
    pass  # Replace with actual implementation
```

**Test it:**
```python
# tests/unit/test_pob_parser.py
import pytest
from src.parsers.pob_parser import parse_pob_code, PoBParseError

def test_parse_invalid_base64():
    """Test that invalid Base64 raises error."""
    with pytest.raises(PoBParseError, match="Invalid Base64"):
        parse_pob_code("not-valid-base64!!!")

def test_parse_oversized_code():
    """Test that codes >100KB are rejected."""
    oversized_code = "A" * (101 * 1024)
    with pytest.raises(PoBParseError, match="too large"):
        parse_pob_code(oversized_code)
```

**Run tests:**
```bash
pytest tests/unit/test_pob_parser.py -v
```

---

#### Day 2-3: Create `src/calculator/pob_engine.py` (Lupa Integration)

**What to do:**
1. Open `tech-specs-summary.md` → Find "calculator/pob_engine.py" section
2. Follow implementation steps for Lupa integration

**Key concepts:**
- **LuaRuntime:** The bridge between Python and Lua
- **Thread-local storage:** Each thread gets its own PoB engine (prevents conflicts)
- **Stub functions:** Python functions that Lua code can call

**Code template:**
```python
# src/calculator/pob_engine.py
from lupa import LuaRuntime, LuaError
import threading
from pathlib import Path
from src.models.build_data import BuildData
from src.models.build_stats import BuildStats
from .stub_functions import create_stubs

class PoBCalculationEngine:
    """Wraps Path of Building Lua calculation engine."""

    def __init__(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self._initialized = False
        self._pob_path = Path(__file__).parent.parent.parent / "external" / "pob-engine"

    def initialize(self):
        """Load HeadlessWrapper.lua and inject Python stubs."""
        if self._initialized:
            return

        # Step 1: Inject Python stub functions
        stubs = create_stubs()
        for func_name, func_impl in stubs.items():
            self.lua.globals()[func_name] = func_impl

        # Step 2: Load HeadlessWrapper.lua
        wrapper_path = self._pob_path / "HeadlessWrapper.lua"
        with open(wrapper_path, 'r', encoding='utf-8') as f:
            wrapper_code = f.read()

        try:
            self.lua.execute(wrapper_code)
        except LuaError as e:
            raise RuntimeError(f"Failed to load HeadlessWrapper.lua: {e}")

        # Step 3: Verify function exists
        if not self.lua.globals().loadBuildFromXML:
            raise RuntimeError("loadBuildFromXML not found in HeadlessWrapper")

        self._initialized = True

    def calculate_build_stats(self, build: BuildData) -> BuildStats:
        """Calculate stats for a build."""
        if not self._initialized:
            self.initialize()

        # TODO: Convert BuildData → XML string
        # TODO: Call lua.globals().loadBuildFromXML(xml)
        # TODO: Call lua.globals().performCalcs(build_table)
        # TODO: Extract results → BuildStats
        pass

# Thread-local storage
_thread_local = threading.local()

def get_pob_engine() -> PoBCalculationEngine:
    """Get PoB engine for current thread."""
    if not hasattr(_thread_local, "pob_engine"):
        _thread_local.pob_engine = PoBCalculationEngine()
        _thread_local.pob_engine.initialize()
    return _thread_local.pob_engine
```

---

### Step 3: Understanding Data Flow

**How does data move through the system?**

```
[User Input]
  PoB Code (Base64 string)
    ↓
[parsers/pob_parser.py]
  parse_pob_code(code)
    ↓
[models/build_data.py]
  BuildData object (Python class with attributes)
    ↓
[calculator/build_calculator.py]
  calculate_build_stats(build_data)
    ↓
[models/build_stats.py]
  BuildStats object (DPS, EHP, etc.)
    ↓
[optimizer/hill_climbing.py]
  optimize(build_data, goal, budgets)
    ↓
[models/build_data.py]
  Optimized BuildData (modified passive_nodes)
    ↓
[parsers/pob_generator.py]
  generate_pob_code(optimized_build)
    ↓
[User Output]
  New PoB Code (Base64 string)
```

**Key insight:** We convert between formats at boundaries:
- User → Base64 → BuildData (objects) → Base64 → User

---

## Common Patterns and Best Practices

### Pattern 1: Data Classes for Models

**Why:** Type-safe, self-documenting data structures

```python
# src/models/build_data.py
from dataclasses import dataclass
from typing import Set, Optional
from enum import Enum

class CharacterClass(Enum):
    WITCH = "Witch"
    WARRIOR = "Warrior"
    # ...

@dataclass
class BuildData:
    """Structured representation of a PoB build."""
    character_class: CharacterClass
    level: int
    passive_nodes: Set[int]
    ascendancy: Optional[str] = None
```

**Benefits:**
- Auto-generates `__init__`, `__repr__`, `__eq__`
- Type hints help catch bugs
- Clear documentation

---

### Pattern 2: Custom Exceptions for Errors

**Why:** Clear error messages, easy to catch specific errors

```python
# src/parsers/exceptions.py
class PoBParseError(Exception):
    """Base exception for PoB parsing errors."""
    def __init__(self, message: str, user_message: str = None):
        super().__init__(message)
        self.user_message = user_message or message
```

**Usage:**
```python
raise PoBParseError(
    "Invalid XML structure at line 42",
    user_message="The build code appears corrupted. Please re-copy from Path of Building."
)
```

---

### Pattern 3: Thread-Local Singleton

**Why:** One instance per thread (safe concurrency)

```python
import threading

_thread_local = threading.local()

def get_pob_engine():
    if not hasattr(_thread_local, "pob_engine"):
        _thread_local.pob_engine = PoBCalculationEngine()
    return _thread_local.pob_engine
```

**When to use:** For resources that aren't thread-safe (like Lua state)

---

### Pattern 4: Progress Callbacks

**Why:** Report progress without coupling to UI

```python
def optimize(build, goal, budgets, progress_callback=None):
    for iteration in range(max_iterations):
        # ... optimization logic ...

        if iteration % 100 == 0 and progress_callback:
            progress_callback(
                iteration=iteration,
                progress=iteration / max_iterations,
                message=f"Tested {iteration} configurations"
            )
```

**Benefits:**
- Algorithm doesn't need to know about web/SSE
- Easy to test (mock the callback)
- Flexible (can log, send to UI, etc.)

---

## Common Mistakes to Avoid

### Mistake 1: Forgetting to Initialize Submodule

**Symptom:** `FileNotFoundError: external/pob-engine/HeadlessWrapper.lua`

**Fix:**
```bash
git submodule init
git submodule update
```

---

### Mistake 2: Not Activating Virtual Environment

**Symptom:** `ModuleNotFoundError: No module named 'lupa'`

**Fix:**
```bash
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate

# Verify:
which python  # Should show path inside venv/
```

---

### Mistake 3: Circular Imports

**Symptom:** `ImportError: cannot import name 'BuildData' from partially initialized module`

**Cause:** File A imports File B, File B imports File A

**Fix:** Use type hints with string notation:
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.models.build_data import BuildData

def my_function(build: 'BuildData'):  # String notation
    pass
```

---

### Mistake 4: Not Testing with Real PoB Codes

**Symptom:** Parser works with test data but fails on real codes

**Fix:** Get sample PoB codes from:
1. Path of Building GUI (export your build)
2. Community build guides (Reddit, PoE forums)
3. Save 5-10 codes in `tests/fixtures/sample-builds/`

---

## Debugging Tips

### Tip 1: Use `print()` for Quick Debugging

```python
def parse_pob_code(code):
    print(f"Code length: {len(code)} bytes")  # Quick check

    decoded = base64.b64decode(code)
    print(f"Decoded length: {len(decoded)} bytes")

    xml_string = zlib.decompress(decoded).decode('utf-8')
    print(f"XML length: {len(xml_string)} characters")
    print(f"XML preview: {xml_string[:200]}...")  # First 200 chars

    # ... rest of function
```

**Better:** Use logging (see Section 9.3 in architecture)

---

### Tip 2: Test Components in Isolation

**Don't:** Test entire system at once
**Do:** Test each component separately

```python
# Good: Test parser alone
def test_parser():
    build = parse_pob_code(sample_code)
    assert build.level == 90

# Good: Test calculator alone (with mock data)
def test_calculator():
    build = BuildData(level=90, ...)  # Mock data
    stats = calculate_stats(build)
    assert stats.total_dps > 0
```

---

### Tip 3: Read Error Messages Carefully

**Example error:**
```
LuaError: HeadlessWrapper.lua:42: attempt to call a nil value (field 'Deflate')
```

**Decode:**
- `HeadlessWrapper.lua:42` → Error is in PoB's Lua code, line 42
- `attempt to call a nil value` → Trying to call a function that doesn't exist
- `field 'Deflate'` → The missing function is `Deflate`

**Fix:** Make sure you injected the `Deflate` stub function (in `stub_functions.py`)

---

## Next Steps: Where to Go from Here

### ✅ Completed the guide?

1. **Read** `solution-architecture-complete.md` Sections 1-5
2. **Review** `tech-specs-summary.md` for Epic 1
3. **Start** implementing `src/parsers/pob_parser.py`
4. **Write tests** as you go (`tests/unit/test_pob_parser.py`)
5. **Commit often** (after each working component)

### 📚 Further Reading

- **Flask Tutorial:** https://flask.palletsprojects.com/tutorial/
- **Lupa Documentation:** https://pypi.org/project/lupa/
- **Python Type Hints:** https://docs.python.org/3/library/typing.html
- **pytest Guide:** https://docs.pytest.org/en/stable/getting-started.html

### ❓ Questions?

**Common questions and where to find answers:**

| Question | Document | Section |
|----------|----------|---------|
| "What does this component do?" | solution-architecture-complete.md | Section 7 (Component Architecture) |
| "How do I implement X?" | tech-specs-summary.md | Find component in Epic sections |
| "Does my code cover requirement Y?" | cohesion-check-report.md | FR Mapping tables |
| "What should I work on next?" | epic-alignment-matrix.md | Story Breakdown tables |
| "How do I set up my environment?" | solution-architecture-complete.md | Section 9.1 (DevOps) |

---

## Final Encouragement

**You've got this!** 🚀

This is a well-architected system with clear component boundaries. Take it one step at a time:
- **Week 1-2:** Parsers + Calculator (Epic 1)
- **Week 3-4:** Optimizer (Epic 2)
- **Week 5-6:** Web UI (Epic 3)

Each component builds on the previous one. By the end of Week 2, you'll have a working PoB calculation engine. By Week 4, you'll have an optimization algorithm. By Week 6, you'll have a complete application.

**Remember:**
- ✅ Test as you go (don't wait until the end)
- ✅ Commit often (after each working feature)
- ✅ Ask questions (architecture docs are your reference)
- ✅ Take breaks (coding is a marathon, not a sprint)

**Good luck with your implementation!**

---

**Document Created:** 2025-10-10
**Author:** Winston (System Architect)
**For:** Beginner developers starting the PoE 2 Optimizer project

---

_End of Implementation Guide_

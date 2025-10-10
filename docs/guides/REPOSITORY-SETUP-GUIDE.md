# Repository Setup Guide for Beginners

**Project:** PoE 2 Passive Tree Optimizer
**Audience:** Developers new to Git, GitHub, and project structure
**Last Updated:** 2025-10-08

---

## Overview

This guide walks you through setting up your GitHub repository and project folder structure from scratch. No prior Git experience required!

---

## Part 1: Initial GitHub Repository Setup

### Step 1: Create GitHub Repository

1. **Go to GitHub.com** and sign in (or create a free account)
2. **Click the "+" button** in the top-right corner
3. **Select "New repository"**
4. **Fill in repository details:**
   - **Repository name:** `poe2-passive-tree-optimizer`
   - **Description:** "A focused web tool that optimizes passive skill trees for Path of Exile 2 builds"
   - **Visibility:** Public (recommended for open-source) or Private
   - **Initialize with:**
     - ✅ Check "Add a README file"
     - ✅ Check "Add .gitignore" → Select **Python** template
     - ✅ Check "Choose a license" → Select **MIT License** (permissive, community-friendly)
5. **Click "Create repository"**

### Step 2: Clone Repository to Your Computer

**What is cloning?** Downloading a copy of the repository to work on locally.

**Using Command Line:**
```bash
# Open Terminal (Mac/Linux) or Git Bash (Windows)
# Navigate to where you want the project folder
cd ~/Projects  # Example: your Projects folder

# Clone the repository
git clone https://github.com/YOUR_USERNAME/poe2-passive-tree-optimizer.git

# Enter the project folder
cd poe2-passive-tree-optimizer
```

**Using GitHub Desktop (Easier for beginners):**
1. Download **GitHub Desktop** from https://desktop.github.com/
2. Open GitHub Desktop
3. Click **File → Clone Repository**
4. Select your repository from the list
5. Choose where to save it on your computer
6. Click **Clone**

---

## Part 2: Project Folder Structure

### Step 3: Create Folder Structure

Create this folder structure inside your cloned repository:

```
poe2-passive-tree-optimizer/
├── .github/                     # GitHub-specific files
│   └── workflows/               # CI/CD automation (optional for MVP)
├── .gitignore                   # Files Git should ignore (auto-created)
├── LICENSE                      # MIT License (auto-created)
├── README.md                    # Project overview (auto-created)
│
├── docs/                        # All documentation
│   ├── product-brief.md         # Your existing product brief
│   ├── PRD.md                   # Product Requirements Document
│   ├── architecture.md          # (To be created in Architecture phase)
│   ├── technical-research.md    # Your existing research docs
│   └── API.md                   # API documentation (future)
│
├── external/                    # Third-party dependencies
│   └── pob-engine/              # Path of Building (Git submodule - see below)
│
├── src/                         # Source code
│   ├── __init__.py              # Makes this a Python package
│   ├── api/                     # Web API endpoints
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── calculator/              # Core optimization engine
│   │   ├── __init__.py
│   │   ├── pob_integration.py   # Lupa + PoB wrapper
│   │   ├── stub_functions.py    # Required PoB stubs
│   │   └── optimizer.py         # Hill climbing algorithm
│   ├── parsers/                 # PoB code parsing
│   │   ├── __init__.py
│   │   └── pob_parser.py        # Base64 → XML decoder
│   └── utils/                   # Helper functions
│       ├── __init__.py
│       └── logging.py
│
├── static/                      # Frontend static files
│   ├── css/
│   │   └── styles.css
│   ├── js/
│   │   └── main.js
│   └── index.html               # Main UI page
│
├── tests/                       # Test files
│   ├── __init__.py
│   ├── test_pob_integration.py
│   ├── test_optimizer.py
│   └── fixtures/                # Sample PoB codes for testing
│
├── config/                      # Configuration files
│   ├── development.env          # Dev environment variables
│   └── production.env.example   # Production config template
│
├── scripts/                     # Utility scripts
│   └── setup_pob_submodule.sh   # Automation script for PoB setup
│
├── requirements.txt             # Python dependencies
├── requirements-dev.txt         # Development dependencies
└── main.py                      # Application entry point
```

### Step 4: Create Folders

**Using Command Line:**
```bash
# Make sure you're in the project root
cd poe2-passive-tree-optimizer

# Create all folders at once
mkdir -p docs external src/api src/calculator src/parsers src/utils static/css static/js tests/fixtures config scripts

# Create __init__.py files for Python packages
touch src/__init__.py src/api/__init__.py src/calculator/__init__.py src/parsers/__init__.py src/utils/__init__.py tests/__init__.py
```

**Using File Explorer (Windows/Mac):**
- Manually create each folder by right-clicking → New Folder
- Create blank `__init__.py` files in Python package folders

---

## Part 3: Adding Path of Building as Git Submodule

### What is a Git Submodule?

A submodule is a way to include another Git repository inside your repository. This keeps the Path of Building code separate but accessible.

### Step 5: Add PoB Repository as Submodule

```bash
# Make sure you're in project root
cd poe2-passive-tree-optimizer

# Add PoB as submodule in external/pob-engine/
git submodule add https://github.com/PathOfBuildingCommunity/PathOfBuilding-PoE2 external/pob-engine

# Initialize and update the submodule
git submodule update --init --recursive

# Pin to a specific stable commit (recommended)
cd external/pob-engine
git checkout COMMIT_HASH  # Replace with actual stable commit
cd ../..

# Commit the submodule addition
git add .gitmodules external/pob-engine
git commit -m "Add Path of Building PoE2 as submodule"
git push origin main
```

### Step 6: Create Submodule Setup Script

Create `scripts/setup_pob_submodule.sh` to automate setup for other developers:

```bash
#!/bin/bash
# Script to initialize Path of Building submodule

echo "Setting up Path of Building submodule..."

# Initialize submodule if not already done
git submodule update --init --recursive

# Enter submodule directory
cd external/pob-engine

# Checkout specific stable commit (update this as needed)
STABLE_COMMIT="abc123def456"  # Replace with actual commit hash
git checkout $STABLE_COMMIT

echo "PoB submodule setup complete!"
echo "Version: $STABLE_COMMIT"
```

Make it executable:
```bash
chmod +x scripts/setup_pob_submodule.sh
```

---

## Part 4: Essential Configuration Files

### Step 7: Create requirements.txt

Create `requirements.txt` for Python dependencies:

```text
# Core Dependencies
lupa>=2.0  # Python-Lua integration (LuaJIT)
flask>=3.0  # Web framework (or FastAPI)
python-dotenv>=1.0  # Environment variable management

# Data Processing
xmltodict>=0.13  # XML parsing for PoB codes

# Production Server
gunicorn>=21.0  # WSGI HTTP Server
```

### Step 8: Create requirements-dev.txt

Create `requirements-dev.txt` for development tools:

```text
-r requirements.txt  # Include production requirements

# Development Tools
pytest>=7.4  # Testing framework
black>=23.0  # Code formatter
flake8>=6.1  # Linting
mypy>=1.5  # Type checking

# Debugging
ipdb>=0.13  # Interactive debugger
```

### Step 9: Update .gitignore

Your Python `.gitignore` template is already good, but add these project-specific exclusions:

```bash
# Add to existing .gitignore

# Environment variables
.env
*.env
!*.env.example

# PoB-specific
external/pob-engine/builds/  # Ignore PoB build artifacts

# Project-specific
logs/
*.log
temp/
cache/
```

### Step 10: Create README.md

Update your `README.md` with project information:

```markdown
# PoE 2 Passive Tree Optimizer

A focused web tool that optimizes passive skill trees for Path of Exile 2 builds.

## Quick Start

### Prerequisites
- Python 3.10+
- Git

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/poe2-passive-tree-optimizer.git
   cd poe2-passive-tree-optimizer
   ```

2. Set up Path of Building submodule:
   ```bash
   bash scripts/setup_pob_submodule.sh
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python main.py
   ```

## Project Structure

See [docs/architecture.md](docs/architecture.md) for detailed architecture documentation.

## Documentation

- [Product Brief](docs/product-brief.md)
- [PRD](docs/PRD.md)
- [Technical Research](docs/technical-research.md)

## License

MIT License - see [LICENSE](LICENSE) file for details.
```

---

## Part 5: Initial Commit and Push

### Step 11: Commit Your Structure

```bash
# Check what files are ready to commit
git status

# Add all new files
git add .

# Commit with descriptive message
git commit -m "Initial project structure with PoB submodule integration"

# Push to GitHub
git push origin main
```

---

## Part 6: Working with Submodules (Daily Workflow)

### When You Clone the Repository Fresh

If someone else (or you on another computer) clones the repository:

```bash
# Clone the main repository
git clone https://github.com/YOUR_USERNAME/poe2-passive-tree-optimizer.git
cd poe2-passive-tree-optimizer

# Initialize submodules (PoB)
git submodule update --init --recursive

# Or use the setup script
bash scripts/setup_pob_submodule.sh
```

### When PoB Updates (Updating Submodule)

```bash
# Enter the submodule
cd external/pob-engine

# Fetch latest changes from PoB repository
git fetch origin

# Checkout specific commit or branch
git checkout origin/main  # or specific commit hash

# Return to project root
cd ../..

# Commit the submodule update
git add external/pob-engine
git commit -m "Update PoB submodule to latest version"
git push origin main
```

---

## Part 7: Verify Setup

### Step 12: Verification Checklist

Run these commands to verify everything is set up correctly:

```bash
# Check folder structure
tree -L 2  # Mac/Linux
# Windows: dir /s /b | findstr /v "pob-engine"  # Exclude PoB for clarity

# Verify submodule is initialized
git submodule status

# Check Python environment
python --version  # Should be 3.10+

# Verify dependencies can be installed
pip install -r requirements.txt

# Check PoB files are accessible
ls external/pob-engine/HeadlessWrapper.lua
```

**Expected Output:**
- ✅ All folders created
- ✅ PoB submodule initialized and files visible
- ✅ Python 3.10+ installed
- ✅ Dependencies install without errors
- ✅ HeadlessWrapper.lua file exists

---

## Common Issues and Solutions

### Issue: "Submodule not found"
**Solution:**
```bash
git submodule update --init --recursive
```

### Issue: "Permission denied" when running scripts
**Solution:**
```bash
chmod +x scripts/setup_pob_submodule.sh
```

### Issue: "Python version too old"
**Solution:** Install Python 3.10+ from python.org

### Issue: "Cannot find lupa module"
**Solution:**
```bash
pip install --upgrade pip
pip install lupa
```

---

## Next Steps

1. ✅ Repository structure created
2. ✅ PoB submodule integrated
3. ⏭️ **Next:** Proceed to Architecture phase to design system components
4. ⏭️ **Then:** Begin implementing core PoB integration using Lupa

---

**Need Help?** Open an issue on GitHub or consult the [Architecture Documentation](docs/architecture.md) once it's created.

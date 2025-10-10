# Deep Research Prompt

**Generated:** 2025-10-08
**Created by:** Alec
**Target Platform:** Claude Projects

---

## Research Prompt (Ready to Use)

### Research Question

Lua runtime integration patterns for Python - production implementation strategies

### Research Goal and Context

**Objective:** Technical architecture decision - Evaluating Lua/Python integration approaches for headless Path of Building calculation engine

**Context:**
Act as a senior Python developer evaluating Lua integration for a performance-critical calculation engine. You need production-ready patterns, not just proof-of-concepts. Focus on reliability, performance, and maintainability for a solo developer project.

### Scope and Boundaries

**Temporal Scope:** Current state only (last 6-12 months) - focus on 2024-2025 implementations

**Geographic Scope:** Global

**Thematic Focus:**

**Focus on:**
- Lupa library (Python + LuaJIT embedding)
- Production implementation patterns
- Performance optimization techniques
- Error handling and debugging strategies
- Extracting/adapting existing Lua codebases for Python

**Exclude:**
- Other languages (Node.js/Fengari already researched)
- Pure Lua development without Python integration
- Legacy Lua 5.1/5.2 (focus on LuaJIT)

### Information Requirements

**Types of Information Needed:**
- Quantitative data and performance benchmarks
- Qualitative insights and expert opinions from production use
- Case studies and real-world implementation examples
- Comparative analysis (Lupa vs alternatives)
- Technical specifications and API patterns

**Preferred Sources:**
- GitHub repositories and production code examples
- Technical documentation (Lupa, LuaJIT)
- Stack Overflow and developer forums (recent discussions)
- Technical blogs and implementation guides (2024-2025)
- Performance benchmarks and profiling data

### Output Structure

**Format:** Problem-Solution-Impact Format with technical depth

**Required Sections:**
1. **Implementation Patterns** - Common approaches for Lupa integration
2. **Code Examples** - Practical integration snippets and patterns
3. **Performance Analysis** - Benchmarks and optimization techniques
4. **Error Handling** - Common pitfalls and debugging strategies
5. **Production Gotchas** - Real-world issues and solutions
6. **Best Practices** - Recommended patterns from experienced developers

**Depth Level:** Comprehensive (3-5 paragraphs per section with code examples)

### Research Methodology

**Keywords and Technical Terms:**
- Lupa, LuaJIT, Python Lua integration
- Embedded Lua runtime, foreign function interface (FFI)
- Python-Lua bridge, lua.eval(), lua.execute()
- Cython, C extension modules
- Performance profiling, memory management
- Error handling across runtimes
- Production deployment patterns

**Special Requirements:**
- Include code snippets with explanations
- Cite sources (GitHub repos, Stack Overflow threads, blog posts with URLs)
- Prioritize 2024-2025 sources for current best practices
- Focus on Lupa library specifically
- Distinguish between theory and proven production patterns
- Highlight performance implications and bottlenecks

**Validation Criteria:**
- Cross-reference multiple sources for implementation patterns
- Verify code examples are from production use (not just tutorials)
- Identify conflicting approaches and explain trade-offs
- Note confidence levels (proven vs experimental)
- Highlight gaps requiring further testing

### Follow-up Strategy

**Anticipated Follow-up Questions:**
- If performance data is unclear, drill deeper into profiling and benchmarking techniques
- If error handling patterns are sparse, create separate analysis of exception handling across Python-Lua boundary
- If extracting existing Lua code is complex, research dependency isolation and module extraction strategies
- If Lupa limitations emerge, evaluate alternative approaches (subprocess, pure Lua rewrite)

---

## Complete Research Prompt (Copy and Paste)

```
# Research: Lua Runtime Integration Patterns for Python - Production Implementation Strategies

## Context
I'm a senior Python developer evaluating Lua integration for a performance-critical calculation engine. I need production-ready patterns for integrating LuaJIT via the Lupa library, not just proof-of-concepts. The focus is on reliability, performance, and maintainability for a solo developer project building a headless calculation engine.

## Research Scope
- **Temporal:** Focus on 2024-2025 implementations and best practices (last 6-12 months)
- **Technical Focus:** Lupa library specifically (Python + LuaJIT embedding)
- **Exclude:** Other languages (Node.js/Fengari), pure Lua development, legacy Lua 5.1/5.2

## Specific Areas to Research

### 1. Implementation Patterns
- Common approaches for embedding LuaJIT in Python using Lupa
- How to structure the Python-Lua boundary
- Module loading and initialization patterns
- Data serialization between Python and Lua

### 2. Code Examples (WITH EXPLANATIONS)
- Practical integration snippets showing:
  - Setting up Lupa environment
  - Loading and executing Lua modules
  - Passing data between Python and Lua
  - Calling Lua functions from Python
  - Error handling across runtime boundaries

### 3. Performance Analysis
- Benchmarks: Lupa vs pure Python vs other integration methods
- Performance optimization techniques
- Memory management best practices
- Profiling tools and techniques for Python-Lua applications

### 4. Error Handling & Debugging
- Common pitfalls when integrating Lua with Python
- Exception handling across the Python-Lua boundary
- Debugging strategies for multi-runtime applications
- Type conversion issues and solutions

### 5. Production Gotchas
- Real-world issues encountered in production
- Deployment considerations
- Dependency management
- Platform-specific issues (Windows, Linux, macOS)

### 6. Best Practices
- Recommended patterns from experienced developers
- When to use Lupa vs alternatives
- How to extract/adapt existing Lua codebases for Python integration
- Performance vs maintainability trade-offs

## Source Requirements
- Prioritize: GitHub repos (production code), Stack Overflow (2024-2025), technical blogs
- Include URLs for all sources
- Focus on Lupa library specifically
- Distinguish proven production patterns from experimental approaches

## Output Format
- Problem-Solution-Impact structure for each section
- Code snippets with explanations
- Performance implications clearly stated
- Trade-offs identified for different approaches
- Confidence levels noted (proven vs experimental)

## Validation
- Cross-reference multiple sources for key patterns
- Verify code examples are from production use
- Identify conflicting approaches and explain why
- Highlight gaps requiring further investigation
```

---

## Platform-Specific Usage Tips

### Claude Projects Tips

**How to Use This Prompt:**
1. Create a new Claude Project or use existing conversation
2. Copy the complete research prompt above
3. Paste into Claude and submit
4. Use Chain of Thought prompting for complex reasoning
5. Ask follow-up questions to drill deeper into specific areas

**Best Practices:**
- Break into sub-prompts if needed (e.g., "Focus on section 3: Performance Analysis")
- Add relevant documents to Project for additional context (your technical research doc)
- Provide explicit examples if Claude's response lacks specificity
- Test iteratively - refine the prompt based on initial results

**Follow-up Commands:**
- "Expand on [specific pattern] with more code examples"
- "Compare approach X vs Y with performance data"
- "Show me production-ready error handling for [scenario]"
- "What are the debugging strategies for [specific issue]?"

---

## Research Execution Checklist

### Before Running Research

- [x] Prompt clearly states the research question ✓
- [x] Scope and boundaries are well-defined ✓
- [x] Output format and structure specified ✓
- [x] Keywords and technical terms included ✓
- [x] Source guidance provided ✓
- [x] Validation criteria clear ✓

### During Research

- [ ] Paste prompt into Claude Projects
- [ ] Review initial response for completeness
- [ ] Ask clarifying follow-up questions for sparse sections
- [ ] Request code examples if missing
- [ ] Verify sources are from 2024-2025 where possible

### After Research Completion

- [ ] Verify key implementation patterns from multiple sources
- [ ] Check that code examples are production-ready (not just tutorials)
- [ ] Identify conflicting approaches and understand trade-offs
- [ ] Note confidence levels for different findings (proven vs experimental)
- [ ] Identify gaps requiring hands-on testing
- [ ] Ask follow-up: "What are the top 3 production gotchas I should watch for?"
- [ ] Save/export research results for reference during prototype

---

## Metadata

**Workflow:** BMad Research Workflow - Deep Research Prompt Generator v2.0
**Generated:** 2025-10-08
**Research Type:** Deep Research Prompt
**Platform:** Claude Projects
**Topic:** Lua Runtime Integration Patterns for Python (Lupa/LuaJIT)

---

_This research prompt was generated using the BMad Method Research Workflow, incorporating best practices from ChatGPT Deep Research, Gemini Deep Research, Grok DeepSearch, and Claude Projects (2025)._

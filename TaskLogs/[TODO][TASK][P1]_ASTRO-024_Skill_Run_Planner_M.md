# Task Log: ASTRO-024 - Skill: run-planner

**Date:** 2026-03-04
**Workspace:** `D:\Dev\CATMEastrolab`
**Status:** TODO
**Priority:** P1
**Cynefin Domain:** Complicated

## Objective

Create the `run-planner` skill that generates explicit execution plans for chart calculations. This skill breaks down user requests into ordered method runs with dependencies, tracks run metadata, and produces handoff-ready task summaries.

## Skill Location

```
.qwen/skills/run-planner/
├── SKILL.md
├── scripts/
│   └── generate_run_plan.py
└── references/
    ├── method-dependencies.md
    └── run-metadata-schema.md
```

## SKILL.md Frontmatter

```yaml
---
name: run-planner
description: Generates explicit execution plans for chart calculations. Breaks requests into ordered method runs with dependencies, tracks metadata (hashes, timestamps), produces handoff summaries. Use when user requests multi-step calculations like "натал + прогноз" or "full workbench".
license: Apache-2.0
metadata:
  author: CATMEastrolab Team
  version: 0.1.0
  output: run_plan.yaml
---
```

## Implementation Steps

### Step 1: Parse User Request

Extract intent from user input:

```python
def parse_request(user_input):
    """
    Extract:
    - chart_id (if exists)
    - birth data (if new chart)
    - requested methods
    - target dates (for forecasts)
    """
    
    patterns = {
        'natal': ['натал', 'natal', 'positions'],
        'forecast': ['прогноз', 'forecast', 'progressions', 'solar arc'],
        'synastry': ['синастрия', 'synastry', 'compatibility'],
        'houses': ['дома', 'houses', 'placidus'],
    }
    
    # Extract requested methods
    methods = []
    for method, keywords in patterns.items():
        if any(kw in user_input.lower() for kw in keywords):
            methods.append(method)
    
    # Extract chart_id if present
    chart_id = extract_chart_id(user_input)
    
    # Extract birth data if new chart
    birth_data = extract_birth_data(user_input)
    
    return {
        'methods': methods,
        'chart_id': chart_id,
        'birth_data': birth_data
    }
```

### Step 2: Define Method Dependencies

```yaml
method_dependencies:
  natal_failover:
    requires: []
    provides: [positions, aspects, moon_phase]
    
  house_placidus:
    requires: []
    provides: [houses, chart_points]
    
  secondary_progressions:
    requires: [natal_failover]  # needs natal positions for comparison
    provides: [progressed_positions, progression_aspects]
    
  solar_arc:
    requires: [natal_failover]
    provides: [directed_positions, solar_arc_aspects]
    
  synastry_matrix:
    requires: [natal_failover]  # for both charts
    provides: [synastry_aspects]
    
  cross_provider_qc:
    requires: [natal_failover]
    provides: [qc_report]
```

### Step 3: Generate Run Plan

Create ordered execution plan:

```python
def generate_run_plan(requested_methods, dependencies):
    """Topological sort of methods based on dependencies."""
    
    # Build dependency graph
    graph = build_dependency_graph(requested_methods, dependencies)
    
    # Topological sort
    ordered_methods = topological_sort(graph)
    
    # Generate run plan
    plan = {
        'plan_id': generate_plan_id(),
        'created_at': datetime.now().isoformat(),
        'chart_id': request['chart_id'],
        'methods': []
    }
    
    for i, method in enumerate(ordered_methods):
        plan['methods'].append({
            'sequence': i + 1,
            'method': method,
            'status': 'PENDING',
            'depends_on': dependencies[method]['requires'],
            'estimated_duration_sec': 30
        })
    
    return plan
```

### Step 4: Generate Run Plan YAML

```yaml
run_plan:
  plan_id: plan_trump_19460614_105400_jamaica_ny_20260304_150000
  created_at: 2026-03-04T15:00:00Z
  chart_id: trump_19460614_105400_jamaica_ny
  request: "Натал + прогноз"
  
  methods:
    - sequence: 1
      method: natal_failover
      status: PENDING
      depends_on: []
      estimated_duration_sec: 30
      params:
        datetime_utc: 1946-06-14T14:54:00Z
        latitude: 40.700000
        longitude: -73.816400
        orb: 6
        
    - sequence: 2
      method: house_placidus
      status: PENDING
      depends_on: []
      estimated_duration_sec: 30
      params:
        datetime_utc: 1946-06-14T14:54:00Z
        latitude: 40.700000
        longitude: -73.816400
        house_system: Placidus
        
    - sequence: 3
      method: secondary_progressions
      status: PENDING
      depends_on: [natal_failover]
      estimated_duration_sec: 30
      params:
        birth_utc: 1946-06-14T14:54:00Z
        target_utc: 2026-03-04T00:00:00Z
        method: secondary_progressions
        
    - sequence: 4
      method: solar_arc
      status: PENDING
      depends_on: [natal_failover]
      estimated_duration_sec: 30
      params:
        birth_utc: 1946-06-14T14:54:00Z
        target_utc: 2026-03-04T00:00:00Z
        method: solar_arc_directions
  
  summary:
    total_methods: 4
    total_estimated_duration_sec: 120
    requires_new_data: true
    chart_exists: false
```

### Step 5: Track Run Metadata

Record execution results:

```python
def update_run_status(plan_id, sequence, status, result=None):
    """Update method status in run plan."""
    
    metadata = {
        'status': status,  # PENDING, RUNNING, COMPLETE, FAILED, SKIPPED
        'started_at': datetime.now().isoformat() if status == 'RUNNING' else None,
        'completed_at': datetime.now().isoformat() if status in ['COMPLETE', 'FAILED'] else None,
        'provider_used': result.get('provider_used') if result else None,
        'output_dir': result.get('output_dir') if result else None,
        'error_message': result.get('error') if status == 'FAILED' else None,
        'response_hash': hashlib.sha256(str(result).encode()).hexdigest() if result else None
    }
    
    # Update plan file
    update_plan_metadata(plan_id, sequence, metadata)
```

### Step 6: Generate Handoff Summary

Create summary for next step:

```yaml
handoff_summary:
  plan_id: plan_trump_19460614_105400_jamaica_ny_20260304_150000
  completed_at: 2026-03-04T15:05:00Z
  
  execution_result:
    total_methods: 4
    completed: 4
    failed: 0
    skipped: 0
    actual_duration_sec: 115
    
  methods_completed:
    - sequence: 1
      method: natal_failover
      status: COMPLETE
      provider_used: swissremote
      qc_status: PASS
      output_dir: artifacts/results/natal_failover_...
      
    - sequence: 2
      method: house_placidus
      status: COMPLETE
      provider_used: swissremote
      output_dir: artifacts/results/house_placidus_...
      
    - sequence: 3
      method: secondary_progressions
      status: COMPLETE
      provider_used: swissremote
      output_dir: artifacts/results/secondary_progressions_...
      
    - sequence: 4
      method: solar_arc
      status: COMPLETE
      provider_used: swissremote
      output_dir: artifacts/results/solar_arc_...
  
  next_recommended_action: |
    All methods completed successfully.
    Ready to:
    1. Build chart-project (call chart-data-preparator)
    2. Generate delivery pack (call artifact-builder)
    3. Analyze chart (call chart-analyst)
```

### Step 7: Handle Failures

```python
def handle_method_failure(plan, sequence, error):
    """
    When method fails:
    1. Mark as FAILED
    2. Check if dependent methods should be SKIPPED
    3. Update plan
    """
    
    failed_method = plan['methods'][sequence - 1]['method']
    
    # Find dependent methods
    for method in plan['methods'][sequence:]:
        if failed_method in method['depends_on']:
            method['status'] = 'SKIPPED'
            method['skip_reason'] = f'Depends on failed method: {failed_method}'
    
    return plan
```

## Important Nuances

### 1. Parallel Execution

Some methods can run in parallel:
- `natal_failover` and `house_placidus` are independent
- `secondary_progressions` and `solar_arc` both depend on natal, but not on each other

Mark parallelizable methods:

```yaml
methods:
  - sequence: 1
    method: natal_failover
    parallel_group: A
    
  - sequence: 2
    method: house_placidus
    parallel_group: A  # Can run with natal_failover
    
  - sequence: 3
    method: secondary_progressions
    parallel_group: B
    
  - sequence: 4
    method: solar_arc
    parallel_group: B  # Can run with secondary_progressions
```

### 2. Idempotency

Check if method already completed:
```python
def check_method_completed(chart_id, method):
    """Check if method run already exists."""
    existing_runs = find_runs(chart_id, method)
    if existing_runs:
        return {
            'already_completed': True,
            'existing_run': existing_runs[0],
            'action': 'SKIP'  # or 'RERUN' if force_refresh
        }
```

### 3. Run Naming Convention

```
<method>_<chart_id>_<timestamp>

Example:
natal_failover_trump_19460614_105400_jamaica_ny_20260304_150000
```

### 4. Plan Persistence

Save run plan to file:
```
charts/<chart_id>/packs/run_plans/<plan_id>.yaml
```

### 5. Progress Tracking

Update plan in real-time:
```python
def update_plan_status(plan_id, overall_status):
    """
    overall_status: PENDING, IN_PROGRESS, COMPLETE, PARTIAL, FAILED
    """
```

## Examples

### Example 1: Natal + Forecast Request

**User says:** "Натал + прогноз для trump_19460614_105400_jamaica_ny"

**Actions:**
1. Parse request → methods: [natal_failover, house_placidus, secondary_progressions, solar_arc]
2. Check chart exists → yes
3. Generate run plan with dependencies
4. Save plan to file

**Result:**
```yaml
run_plan:
  plan_id: plan_trump_19460614_105400_jamaica_ny_20260304_150000
  methods:
    - sequence: 1, method: natal_failover
    - sequence: 2, method: house_placidus
    - sequence: 3, method: secondary_progressions
    - sequence: 4, method: solar_arc
  total_estimated_duration_sec: 120
```

### Example 2: New Chart Request

**User says:** "Calculate natal for June 13, 1982, 13:39, Jamaica Queens NY"

**Actions:**
1. Parse request → methods: [natal_failover, house_placidus]
2. Extract birth data
3. Generate chart_id: trump_19460614_105400_jamaica_ny
4. Generate run plan

**Result:**
```yaml
run_plan:
  chart_id: trump_19460614_105400_jamaica_ny (new)
  birth_data:
    local_datetime: 1946-06-14 10:54:00
    timezone: +04:00
    location: Jamaica Queens NY (40.700000, -73.816400)
  methods:
    - sequence: 1, method: natal_failover
    - sequence: 2, method: house_placidus
```

### Example 3: Method Failure

**User says:** "Run full workbench"

**Actions:**
1. Generate plan with 6 methods
2. Execute method 1 (natal_failover) → SUCCESS
3. Execute method 2 (house_placidus) → FAILED (provider timeout)
4. Mark dependent methods as SKIPPED

**Result:**
```yaml
methods:
  - sequence: 1, method: natal_failover, status: COMPLETE
  - sequence: 2, method: house_placidus, status: FAILED, error: "Timeout"
  - sequence: 3, method: secondary_progressions, status: SKIPPED, 
    skip_reason: "Depends on failed method: house_placidus"
  - sequence: 4, method: solar_arc, status: SKIPPED
```

## Troubleshooting

### Error: Circular dependency detected

- **Cause:** Bug in dependency graph
- **Solution:** Review method_dependencies, ensure no cycles

### Error: Method already exists

- **Cause:** Re-running without force_refresh
- **Solution:** Either skip existing or set force_refresh=True

### Error: Dependent method skipped

- **Cause:** Previous method failed
- **Solution:** Fix failed method, regenerate plan

## Related Tasks

| Task | Relationship |
|---|---|
| ASTRO-012 | Agent orchestrator — this skill generates run plans for orchestrator |
| ASTRO-008 | Modular architecture — skill defines method boundaries |
| ASTRO-017 | Skills architecture — this is a coordination skill |

## Available Code / Tools

### PowerShell Scripts (Method Implementations)
- `artifacts/mcp-recipes/run_natal_with_failover.ps1` — Natal method
- `artifacts/mcp-recipes/run_house_layer_placidus.ps1` — House method
- `artifacts/mcp-recipes/run_secondary_progressions.ps1` — Progressions method
- `artifacts/mcp-recipes/run_solar_arc.ps1` — Solar arc method
- `artifacts/mcp-recipes/run_synastry_matrix.ps1` — Synastry method
- `artifacts/mcp-recipes/run_full_workbench.ps1` — Full workbench reference

### Decision Tree / Runbook
- `artifacts/mcp-recipes/failover_runbook.md` — Failover decision rules
- `charts/README.md` — Chart project structure rules

### Method Dependencies (from scripts)
```
natal_failover → requires: nothing
house_placidus → requires: nothing
secondary_progressions → requires: natal_failover (for comparison)
solar_arc → requires: natal_failover (for directed aspects)
synastry_matrix → requires: natal_failover (for both charts)
```

### File Conventions
- Run naming: `<method>_<chart_id>_<timestamp>`
- Output folder: `artifacts/results/<run_name>/`
- Summary file: `<run_name>/00_summary.txt`

## Acceptance Criteria

- [ ] SKILL.md created in `.qwen/skills/run-planner/`
- [ ] User request parsed into method list
- [ ] Dependency graph built correctly
- [ ] Run plan generated with correct ordering
- [ ] Run plan saved as YAML
- [ ] Method status tracked (PENDING, RUNNING, COMPLETE, FAILED, SKIPPED)
- [ ] Handoff summary generated after completion
- [ ] Failures propagate to dependent methods (mark as SKIPPED)


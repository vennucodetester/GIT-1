# Planning Skill - Feature Implementation Protocol

## Auto-Trigger Instructions
**Apply this skill automatically when:**
- User requests a new feature or significant modification
- User describes a high-level idea that requires implementation planning
- Architectural changes are proposed (e.g., "refactor calculation engine", "add new tab")
- Cross-component modifications are needed (e.g., "change how CSV data flows")
- Any change that might affect critical features defined in the testing skill

**Do NOT trigger for:**
- Bug fixes (use testing skill to verify fix)
- Documentation updates
- Trivial changes (e.g., "change button label", "fix typo")

---

## Purpose
This skill defines the structured 3-step planning process that must be followed before implementing new features or significant changes. It ensures intentional development, minimizes regressions, and confirms the user's vision before coding begins.

---

## The 3-Step Planning Process

When a new idea or feature request is received, execute the following steps in order:

---

### **Step 1: Requirements Analysis & Code Exploration**

#### A. Clarify the Request
1. **Restate the user's idea** in technical terms
2. **Identify specific components** involved:
   - UI components (Sensor Panel, Diagram, Graph, Calculations, P-h Diagram, Comparison)
   - Data flows (CSV loading, filtering, calculations, exports)
   - Backend logic (calculation engine, port resolver, data manager)
3. **Ask clarifying questions** if requirements are ambiguous:
   - "Should this feature work with all sensor types or only specific ones?"
   - "Do you want this to apply to the current CSV only or all future CSVs?"
   - "Should this integrate with the existing diagram port mapping system?"

#### B. Explore Affected Code
Use the Task tool with `subagent_type=Explore` for comprehensive codebase exploration:
- **Find relevant files** using Glob patterns (e.g., `**/*calculation*.py`, `**/*widget*.py`)
- **Search for keywords** using Grep (e.g., "filter", "port_mapping", "CoolProp")
- **Identify key classes and functions** that will need modification
- **Map dependencies** (e.g., "Adding filter → affects data_manager → affects all tabs")

**Example Exploration:**
```
User: "Add a feature to filter data by superheat range"

Exploration findings:
- Superheat is calculated in calculation_engine.py:_compute_single_coil()
- Filtering currently exists for discharge pressure: calculations_widget.py:576-605
- Would need similar UI: QDoubleSpinBox + Apply button
- Data manager has get_filtered_data() for time-based filtering
- Need to integrate with existing filter chain
```

#### C. Draft High-Level Plan
List affected files and changes:
- **Files to modify:** (e.g., "calculations_widget.py", "data_manager.py")
- **Files to create:** (e.g., "superheat_filter_dialog.py")
- **Architectural approach:** (e.g., "Add new signal/slot for filter updates", "Extend existing _apply_discharge_filter() pattern")
- **Complexity estimate:** Simple / Moderate / Complex
- **Estimated LOC:** Approximate lines of code to add/modify

**Output Format:**
```markdown
## High-Level Implementation Plan

### Files to Modify:
1. `calculations_widget.py` (add superheat filter UI)
2. `data_manager.py` (add superheat_filter_config)

### Files to Create:
1. (None)

### Architectural Changes:
- Extend existing filter pattern from discharge pressure filter
- Add QDoubleSpinBox for min/max superheat thresholds
- Apply filter after time filtering, before calculations

### Complexity: Moderate
### Estimated Impact: 150 lines of code
```

---

### **Step 2: Impact Assessment** (CRITICAL - Cross-Reference with Testing Skill)

For **every change**, systematically check against critical requirements from the testing skill:

---

#### ✅ **A. Calculation Engine Impact (HIGHEST PRIORITY)**

**Questions to Ask:**
- [ ] Will this modify thermodynamic formulas in `calculation_engine.py`?
- [ ] Will this change sensor-to-port mapping in `port_resolver.py`?
- [ ] Will this affect CoolProp calls or unit conversions?
- [ ] Will this alter the 54-column output structure?
- [ ] Will this change how enthalpy, entropy, or density are calculated?

**Required Actions if YES to any:**
1. ⚠️ Run `python test_calculations.py ID6SU12WE-diagram-only.json` **before** changes
2. ⚠️ Document expected changes to output values
3. ⚠️ Verify CoolProp calls remain valid:
   - Refrigerant parameter still "R290"
   - Units correct (Pa, K, kJ/kg)
   - Properties called: "H" (enthalpy), "S" (entropy), "D" (density), "T" (temp)
4. ⚠️ After changes, re-run test and compare results line-by-line
5. ⚠️ Update `test_calculations.py` if expected output changes
6. ⚠️ Check impact on P-h diagram data flow

**Example Assessment:**
```markdown
## Calculation Engine Impact: ⚠️ MODERATE

This change will:
- Add superheat filtering AFTER calculations (no formula changes)
- NOT modify calculation_engine.py
- NOT affect CoolProp calls
- Filter rows based on already-calculated S.H_total values

Action: No test_calculations.py update needed (calculations unchanged)
```

---

#### ✅ **B. Data Flow Impact**

**Questions to Ask:**
- [ ] Will this affect CSV loading or parsing (`data_manager.py:load_csv()`)?
- [ ] Will this modify sensor mapping or reconciliation (`mapping_dialog.py`)?
- [ ] Will this change time filtering logic (`data_manager.py:get_filtered_data()`)?
- [ ] Will this alter how `data_changed` signal is emitted or handled?
- [ ] Will this affect data caching or performance?

**Required Actions if YES to any:**
1. ⚠️ Test with existing saved configs (`ID6SU12WE-*.json`) to ensure backward compatibility
2. ⚠️ Verify `data_changed` signal still triggers all tab updates
3. ⚠️ Check that session save/load preserves new data structures
4. ⚠️ Test with multiple CSV files to verify consistency

**Example Assessment:**
```markdown
## Data Flow Impact: ⚠️ HIGH

This change will:
- Add new filter_config to data_manager.py
- Modify get_filtered_data() to apply new filter
- Require session save/load update to persist filter settings

Action:
- Update data_manager.save_session() to include superheat_filter_config
- Update data_manager.load_session() to restore filter settings
- Test loading old sessions (must not crash if new key missing)
```

---

#### ✅ **C. UI Component Impact**

**Questions to Ask:**
- [ ] Will this modify Sensor Panel tree structure or selection behavior?
- [ ] Will this affect Diagram component schemas or port definitions (`component_schemas.py`)?
- [ ] Will this change Graph rendering, legends, or custom range selection?
- [ ] Will this alter the Calculations Tab layout or header structure?
- [ ] Will this add new dialogs or UI elements?

**Required Actions if YES to any:**
1. ⚠️ Trace signal/slot connections to ensure proper event handling
2. ⚠️ Verify user workflows remain intact:
   - CSV load → mapping → graphing → calculations
   - Sensor selection → diagram highlighting
   - Custom range selection → all tabs update
3. ⚠️ Check for UI responsiveness (no blocking operations on main thread)
4. ⚠️ Verify keyboard shortcuts and context menus still work

**Example Assessment:**
```markdown
## UI Component Impact: ⚠️ LOW

This change will:
- Add 2 QDoubleSpinBox widgets to calculations_widget.py
- Add 1 Apply button
- Reuse existing filter UI pattern (similar to discharge press filter)

Action:
- Place UI elements in existing control_row layout
- Connect Apply button to new on_apply_superheat_filter() slot
- No changes to other UI components
```

---

#### ✅ **D. Cross-Tab Dependencies**

**Questions to Ask:**
- [ ] Will this affect data passed from Calculations Tab → P-h Diagram?
- [ ] Will this impact Comparison Tab or multi-CSV handling?
- [ ] Will this change how Graph Tab receives sensor selection updates?
- [ ] Will all tabs receive the same filtered dataset?

**Required Actions if YES to any:**
1. ⚠️ Test end-to-end workflow: CSV load → map → graph → calculate → export
2. ⚠️ Verify `filtered_data_ready` signal still works (Calculations → P-h)
3. ⚠️ Check that custom range selection still applies universally
4. ⚠️ Confirm exports (CSV, PNG) reflect filtered data correctly

**Example Assessment:**
```markdown
## Cross-Tab Dependencies: ✅ NONE

This change will:
- Filter data within Calculations Tab only
- NOT affect Graph Tab or P-h Diagram (they use time-filtered data)
- Filtering happens after get_filtered_data(), before calculations run

Action: No cross-tab coordination needed
```

---

#### ✅ **E. Critical Feature Verification**

**Must NOT break these features (from testing skill):**
- [ ] Sensor Panel ↔ Diagram bidirectional highlighting
- [ ] CSV mapping dialog and reconciliation
- [ ] Graph Tab sensor selection and plotting
- [ ] Custom range selection (Keep Range / Delete Range)
- [ ] Discharge pressure filtering
- [ ] Calculations Tab 54-column output
- [ ] ON-time filtering (compressor state)
- [ ] P-h Diagram data flow
- [ ] Timestamp handling (CDT → UTC conversion)
- [ ] Port resolver dynamic mapping

**Required Actions:**
1. ⚠️ After implementation, run full regression test checklist from testing skill
2. ⚠️ Test sensor highlighting (click panel → diagram updates, click diagram → panel scrolls)
3. ⚠️ Test discharge pressure filter still works
4. ⚠️ Verify `test_calculations.py` still passes

---

#### 📋 **F. Document Potential Risks**

List any:
- **Breaking changes:** (e.g., "Old session files won't have new filter config key")
- **Backward incompatibilities:** (e.g., "Need migration script for old .json files")
- **Performance concerns:** (e.g., "Filtering 10K rows may be slow")
- **Areas needing additional testing:** (e.g., "Test with empty CSV, test with all-NaN columns")

**Example Risk Documentation:**
```markdown
## Potential Risks

### Backward Compatibility: ⚠️ MEDIUM
- Old session files won't have `superheat_filter_config` key
- Solution: Use default config if key missing (graceful fallback)

### Performance: ✅ LOW
- Filtering adds ~5ms per 1000 rows (negligible)

### Testing Needed:
- Test with CSV where superheat is all NaN (should skip filter gracefully)
- Test with extreme threshold values (verify no crashes)
```

---

### **Step 3: Visual Confirmation & Acceptance Criteria**

Before proceeding with implementation, provide the user with a clear picture of the proposed changes.

---

#### A. Visual Representation

**Provide ONE OR MORE of the following:**

1. **ASCII/Unicode Wireframe** (for UI changes):
```
┌─────────────────────────────────────────────────────────────────┐
│  Calculations Tab                                               │
├─────────────────────────────────────────────────────────────────┤
│  [Enter Rated Inputs]  [Run Calculations]  [Copy to Clipboard] │
│                                                                 │
│  discharge press: [55.00] [Apply]                              │
│  superheat range: [5.00] to [50.00] [Apply Superheat Filter]  │ ← NEW
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  [ Nested Header Table - 54 columns ]                     │ │
│  │  Row 1: AT LH coil | AT CTR coil | ...                    │ │
│  │  ...                                                       │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

2. **Detailed Textual Description**:
```markdown
## UI Layout

**Location:** Calculations Tab, control row (below "Enter Rated Inputs" buttons)

**New Elements:**
- Label: "superheat range:" (gray text, 10pt font)
- QDoubleSpinBox (min): Default 5.0, range 0-100°F, 2 decimals, 90px width
- Label: "to"
- QDoubleSpinBox (max): Default 50.0, range 0-100°F, 2 decimals, 90px width
- QPushButton: "Apply Superheat Filter" (24px height, default button style)

**Behavior:**
- User enters min/max values
- Clicks "Apply Superheat Filter" button
- Calculations re-run with filter applied
- Status message shows: "Filtered to X/Y rows (superheat 5.0-50.0°F)"
```

3. **Code Structure Preview** (for architectural changes):
```python
# calculations_widget.py

class CalculationsWidget(QWidget):
    def __init__(self):
        # ... existing code ...

        # NEW: Superheat filter UI
        self.lbl_superheat = QLabel("superheat range:")
        self.spn_sh_min = QDoubleSpinBox()
        self.spn_sh_min.setValue(5.0)
        self.lbl_to = QLabel("to")
        self.spn_sh_max = QDoubleSpinBox()
        self.spn_sh_max.setValue(50.0)
        self.btn_sh_filter = QPushButton("Apply Superheat Filter")
        self.btn_sh_filter.clicked.connect(self.on_apply_superheat_filter)

        control_row.addWidget(self.lbl_superheat)
        control_row.addWidget(self.spn_sh_min)
        control_row.addWidget(self.lbl_to)
        control_row.addWidget(self.spn_sh_max)
        control_row.addWidget(self.btn_sh_filter)

    def on_apply_superheat_filter(self):
        """Apply superheat range filter and re-run calculations."""
        self.sh_min_threshold = self.spn_sh_min.value()
        self.sh_max_threshold = self.spn_sh_max.value()
        self.run_calculation()

    def _apply_superheat_filter(self, df):
        """Filter dataframe by superheat range."""
        if 'S.H_total' not in df.columns:
            return df
        mask = (df['S.H_total'] >= self.sh_min_threshold) & \
               (df['S.H_total'] <= self.sh_max_threshold)
        return df[mask].copy()
```

4. **Reference to Existing Components**:
```markdown
## Similar Existing Feature

This feature will follow the **exact same pattern** as the existing discharge
pressure filter (`calculations_widget.py:307-605`):

- UI: QDoubleSpinBox + Apply button (lines 307-320)
- Logic: _apply_discharge_filter() method (lines 576-605)
- Integration: Called before calculations run (line 500)

**Differences:**
- Superheat filter uses 2 spinboxes (min/max range) instead of 1 (threshold)
- Filters on calculated column 'S.H_total' (not CSV column)
- Applied AFTER calculations, not before (filters results, not input)
```

---

#### B. User Workflow Description

**Provide step-by-step walkthrough of the feature:**

```markdown
## User Workflow

### Step 1: User loads CSV and runs calculations
- User loads "ID6SU12WE DOE 2.csv"
- Clicks "Run Calculations"
- 1,243 rows processed, results displayed

### Step 2: User notices many rows with excessive superheat
- Legend shows S.H_total ranging from -5°F to 95°F
- User wants to see only "healthy" superheat range (5-50°F)

### Step 3: User applies superheat filter
- Enters "5.0" in min spinbox
- Enters "50.0" in max spinbox
- Clicks "Apply Superheat Filter"

### Step 4: System re-runs calculations with filter
- Calculations engine runs again
- Only rows with 5.0 ≤ S.H_total ≤ 50.0 are kept
- Status message: "Filtered to 487/1,243 rows (superheat 5.0-50.0°F)"
- Table updates to show only filtered rows
- P-h Diagram updates to show only filtered cycle paths

### Step 5: User exports filtered results
- Clicks "Copy to Clipboard"
- Pastes into Excel
- Only 487 filtered rows appear (expected)
```

---

#### C. Acceptance Criteria (Testable Conditions)

**List specific conditions that define success:**

```markdown
## Acceptance Criteria

### Functional Requirements:
- [ ] Superheat filter UI elements appear below discharge press filter
- [ ] Default values: min=5.0, max=50.0
- [ ] Entering range 10.0-40.0 and clicking Apply filters correctly
- [ ] Status message shows: "Filtered to X/Y rows (superheat XX-XX°F)"
- [ ] Only rows within range appear in Calculations Tab table
- [ ] P-h Diagram updates to reflect filtered data
- [ ] Export (clipboard/CSV) includes only filtered rows

### Edge Cases:
- [ ] If S.H_total column missing, filter is skipped gracefully
- [ ] If min > max, show warning dialog: "Min must be ≤ Max"
- [ ] If all rows filtered out, show message: "No rows match filter criteria"
- [ ] Filter works in combination with discharge press filter
- [ ] Filter works with custom time range selection

### Performance:
- [ ] Filtering 1,000 rows completes in < 100ms
- [ ] UI remains responsive (no freezing)

### Backward Compatibility:
- [ ] Old session files load without errors (filter disabled by default)
- [ ] Existing discharge press filter still works after change
- [ ] test_calculations.py still passes (no calculation logic changed)
```

---

#### D. Request User Approval

**Before writing any code, wait for explicit confirmation:**

```markdown
## Ready to Proceed?

I've outlined the plan above. Before I start implementing, please confirm:

1. ✅ **Does the UI layout match your vision?**
   - Superheat filter below discharge press filter
   - Two spinboxes (min/max) + Apply button

2. ✅ **Is the workflow correct?**
   - Filter applied AFTER calculations (filters results, not input data)
   - Works in combination with discharge press filter

3. ✅ **Any changes or additional requirements?**
   - Should this filter be saved in session files?
   - Should there be a "Clear Filter" button?
   - Should filtered-out rows be highlighted (grayed out) instead of hidden?

**Please reply with:**
- "Go ahead" (if approved)
- Suggested changes (if adjustments needed)
- Questions/concerns (if anything is unclear)

I'll wait for your approval before writing any code.
```

---

### **Step 4: Post-Implementation Self-Verification** (CRITICAL - NEW)

**After implementing ANY code change, BEFORE declaring it complete:**

---

#### A. Search for Similar Existing Implementations

**MANDATORY:** Search the codebase for similar patterns and compare your implementation.

**For UI Items (buttons, dialogs, widgets):**
```bash
grep -n "class.*Item\|class.*Widget\|class.*Dialog" *.py
grep -n "def __init__" <similar_class_file>.py
```

**For Draggable/Hoverable Items:**
```bash
grep -n "setAcceptHoverEvents" *.py
grep -n "ItemIsMovable\|ItemIsSelectable" *.py
grep -n "mousePressEvent\|mouseReleaseEvent" *.py
```

**For Filters/Data Processing:**
```bash
grep -n "_apply.*filter\|def filter" *.py
grep -n "get_filtered_data" *.py
```

**For Calculations:**
```bash
grep -n "CoolProp\|PropsSI" *.py
grep -n "def.*calculate\|def.*compute" *.py
```

---

#### B. Pattern Matching Checklist

**Compare your implementation with existing similar code:**

- [ ] **Initialization:** Does your `__init__` match the pattern of similar classes?
  - Are you setting all the same flags? (ItemIsMovable, ItemIsSelectable, etc.)
  - Are you calling the same setup methods? (setAcceptHoverEvents, setCursor, etc.)

- [ ] **Event Handlers:** If similar items have hoverEnterEvent/hoverLeaveEvent, do you?
  - Check if existing draggable items have hover event handlers
  - Copy the exact pattern if they do

- [ ] **Data Persistence:** If similar features save state, do you?
  - Check if similar filters save to session files
  - Check if similar UI elements store offsets/positions

- [ ] **Signal Connections:** If similar items emit signals, do you?
  - Look for `.connect()` patterns in similar code
  - Ensure you're following the same signal/slot architecture

---

#### C. Common Missing Patterns Checklist

**These are FREQUENTLY missed - check ALL of them:**

##### For Draggable/Interactive Items:
- [ ] `setAcceptHoverEvents(True)` - Enables cursor changes on hover
- [ ] `setCursor(Qt.CursorShape.PointingHandCursor)` - Shows hand cursor
- [ ] `hoverEnterEvent()` / `hoverLeaveEvent()` - If other draggable items have them
- [ ] `setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)` - If positions matter
- [ ] `setZValue()` - If layering matters (check similar items)

##### For Filters/Data Processing:
- [ ] Null/NaN checks before filtering (`pd.isna()`, `is not None`)
- [ ] Empty result handling (what if filter removes all rows?)
- [ ] Session save/load for filter settings
- [ ] Signal emission after filtering (`data_changed.emit()`)

##### For UI Components:
- [ ] Layout management (addWidget, addLayout, stretch factors)
- [ ] Signal/slot connections (`.connect()` calls)
- [ ] Tooltips (`.setToolTip()` if similar widgets have them)
- [ ] Keyboard shortcuts (if similar actions have them)
- [ ] Context menus (if similar items have right-click menus)

##### For Calculations:
- [ ] Unit conversions match existing patterns
- [ ] CoolProp calls use same refrigerant/units as existing code
- [ ] Error handling for invalid values (NaN, infinite, out of range)
- [ ] Output column names match existing structure

---

#### D. Self-Review Questions

**Ask yourself these questions BEFORE committing:**

1. **Did I search for similar code?**
   - "Are there other draggable items in this codebase?"
   - "How do THEY handle initialization?"

2. **Did I copy ALL the patterns, not just some?**
   - "PortItem has setAcceptHoverEvents - did I add it too?"
   - "Other filters save to session - did I add save/load?"

3. **Did I test edge cases?**
   - "What if the data column is missing?"
   - "What if all values are NaN?"
   - "What if user enters invalid input?"

4. **Will this work with existing features?**
   - "Does this work with discharge press filter?"
   - "Does this work with custom time range?"
   - "Does this update the P-h diagram correctly?"

---

#### E. Mandatory Verification Commands

**Run these commands BEFORE declaring implementation complete:**

```bash
# 1. Check your new class/method exists
grep -n "class YourNewClass\|def your_new_method" your_file.py

# 2. Find ALL similar implementations
grep -n "similar_pattern" *.py

# 3. Compare side-by-side (example for draggable items)
grep -A 20 "class PortItem" diagram_components.py
grep -A 20 "class YourNewItem" diagram_components.py

# 4. Check for common missing patterns
grep -n "setAcceptHoverEvents" your_file.py  # Should return results!
grep -n "hoverEnterEvent" your_file.py       # If others have it, you should too!

# 5. Syntax check
python3 -m py_compile your_file.py
```

---

#### F. Documentation of Self-Check

**After verifying, add a comment in your commit message:**

```
Fix: Add draggable labels to sensor boxes

Implementation verified against existing patterns:
- Searched for similar draggable items (PortItem, PipeItem, WaypointHandle)
- Copied exact initialization pattern including setAcceptHoverEvents(True)
- Added hover event handlers matching existing code
- Verified offset persistence matches sensor box pattern
- Tested with existing sensor data

Self-check complete - no missing patterns found.
```

---

### **Implementation Guidelines** (After Approval)

Once the user approves the plan:

1. **Implement incrementally:**
   - One file/component at a time
   - Commit after each logical unit of work
   - Test after each change

2. **Run tests frequently:**
   - After modifying calculations: `python test_calculations.py`
   - After UI changes: Manual testing of user workflows
   - Before final commit: Full regression checklist from testing skill

3. **BEFORE committing - Run Step 4 Self-Verification:**
   - Search for similar implementations
   - Compare patterns side-by-side
   - Check common missing patterns checklist
   - Run verification commands
   - Document self-check in commit message

4. **Update documentation:**
   - Add docstrings to new methods
   - Update README if public API changes
   - Document new config keys in session file format

5. **Commit with clear messages:**
   - Format: `"Add superheat range filter to Calculations Tab"`
   - Include: What changed, why, and any breaking changes
   - Reference: Issue numbers if applicable
   - Include: Self-verification statement

---

## Summary: When to Apply This Skill

### ✅ **Always Apply For:**
- New features (e.g., "Add filter for...", "Create new tab for...")
- Architectural changes (e.g., "Refactor calculation engine to use...")
- Cross-component modifications (e.g., "Change how CSV data flows through...")
- UI/UX changes (e.g., "Redesign sensor panel layout...")

### ❌ **Never Apply For:**
- Bug fixes (just fix and test)
- Documentation updates
- Trivial changes (typos, label text, button colors)
- User questions (just answer)

---

## Planning Checklist

Before AND after implementing any feature, ensure:

### Pre-Implementation:
- [ ] **Step 1 Complete:** Clarified requirements, explored codebase, drafted high-level plan
- [ ] **Step 2 Complete:** Assessed impact on calculations, data flow, UI, cross-tab dependencies
- [ ] **Step 2 Complete:** Verified no breaking changes to critical features (testing skill)
- [ ] **Step 2 Complete:** Documented potential risks
- [ ] **Step 3 Complete:** Provided visual representation (wireframe/description/code preview)
- [ ] **Step 3 Complete:** Described user workflow step-by-step
- [ ] **Step 3 Complete:** Listed testable acceptance criteria
- [ ] **Step 3 Complete:** Requested user approval
- [ ] **User Approved:** Received explicit "go ahead" or approval message

### Post-Implementation (CRITICAL):
- [ ] **Step 4 Complete:** Searched for similar existing implementations
- [ ] **Step 4 Complete:** Compared implementation patterns side-by-side
- [ ] **Step 4 Complete:** Checked common missing patterns checklist
- [ ] **Step 4 Complete:** Ran verification commands (grep, syntax check)
- [ ] **Step 4 Complete:** Documented self-check in commit message

**If ALL boxes checked, commit and push. Otherwise, fix missing patterns first.**

---

## Example Planning Flow

**User Request:**
> "Can you add a feature to highlight rows in the Calculations Tab where superheat is below 5°F? I want to see which rows might have liquid slugging risk."

**Step 1: Analysis**
- Feature: Visual highlighting (not filtering) in Calculations Tab
- Component: CalculationsWidget QTreeWidget
- Approach: Add background color to QTreeWidgetItem based on S.H_total value
- Files: calculations_widget.py (modify populate_tree method)
- Complexity: Simple, ~30 lines of code

**Step 2: Impact Assessment**
- Calculation Engine: ✅ No impact (just visual change)
- Data Flow: ✅ No impact (no filtering)
- UI: ⚠️ Minor (add conditional brush color to tree items)
- Cross-Tab: ✅ No impact (Calculations Tab only)
- Critical Features: ✅ None affected

**Step 3: Visual Confirmation**
```
Calculations Tab:

┌─────────────────────────────────────────────────────────────────┐
│  Row   │ S.H_total │ T_2b  │ ...                               │
├─────────────────────────────────────────────────────────────────┤
│  1     │   3.2°F   │ 45.2  │ ... │ ← RED BACKGROUND (danger)   │
│  2     │   8.5°F   │ 48.1  │ ... │ ← YELLOW BACKGROUND (warn)  │
│  3     │  12.4°F   │ 52.3  │ ... │ ← Normal (no highlight)     │
└─────────────────────────────────────────────────────────────────┘

Color Legend:
- RED:    S.H_total < 5°F (liquid slugging risk)
- YELLOW: 5°F ≤ S.H_total < 10°F (marginal)
- Normal: S.H_total ≥ 10°F (safe)
```

**Acceptance Criteria:**
- [ ] Rows with S.H < 5°F have red background
- [ ] Rows with 5 ≤ S.H < 10°F have yellow background
- [ ] Highlighting updates when data changes
- [ ] Copy to clipboard still works (text only, no colors)

**User Approval:**
> "Perfect! Go ahead with red/yellow highlighting."

**Implementation:**
```python
# calculations_widget.py, in populate_tree():

for index, row in df.iterrows():
    item = QTreeWidgetItem()

    # ... populate item with data ...

    # NEW: Add highlighting based on superheat
    sh_total = row.get('S.H_total')
    if sh_total is not None and not pd.isna(sh_total):
        if sh_total < 5.0:
            item.setBackground(0, QBrush(QColor('#FFCCCC')))  # Light red
        elif sh_total < 10.0:
            item.setBackground(0, QBrush(QColor('#FFFFCC')))  # Light yellow

    self.tree_widget.addTopLevelItem(item)
```

**Result:** Feature implemented in 20 lines, no breaking changes, user's vision confirmed upfront.

---

**This planning process ensures we build exactly what the user needs, with no surprises.**

# Testing Skill - HVAC Diagnostic Application Core Requirements

## Auto-Trigger Instructions
**Apply this skill automatically when:**
- Running builds or deploying the application
- Making changes to calculation logic, data flow, UI components, or core features
- Reviewing pull requests or commits
- User explicitly requests verification or testing
- After implementing new features that interact with existing functionality
- **BEFORE committing code** - to verify critical features still work

---

## Purpose
This skill defines the critical functional requirements that must remain intact and verified after any code changes. All future modifications must ensure these features continue to work correctly.

---

## ⚠️ CRITICAL REMINDER: Self-Verification Before Commit

**Before committing ANY code change, you MUST:**

1. **Search for similar existing implementations**
   - Use grep to find patterns: `grep -n "setAcceptHoverEvents\|ItemIsMovable\|similar_pattern" *.py`
   - Compare your implementation side-by-side with existing code
   - Ensure you copied ALL patterns, not just some

2. **Check common missing patterns** (from planning skill Step 4):
   - Draggable items: `setAcceptHoverEvents(True)`, hover event handlers
   - Filters: null/NaN checks, session save/load
   - UI components: signal connections, tooltips, layouts
   - Calculations: unit conversions, error handling

3. **Run verification commands:**
   ```bash
   python3 -m py_compile your_file.py  # Syntax check
   grep -n "critical_pattern" your_file.py  # Pattern check
   ```

4. **Document self-check in commit message:**
   - List what patterns you searched for
   - Confirm you verified against existing code
   - Note any edge cases tested

**If you skip this, you WILL miss critical patterns and the user will find bugs during testing.**

See planning skill Step 4 for complete self-verification checklist.

---

## 1. Sensor Panel and Diagram Testing (Initial State)

### Sensor Panel (`sensor_panel.py`)
- ✅ Must load correctly and display all sensors in tree structure
- ✅ Sensors organized under groups (Ambient, Coil Out, etc.) in `data_manager.sensor_groups`
- ✅ Tree widget supports multi-selection (Ctrl+Shift)
- ✅ Search/filter functionality works across all sensors
- ✅ Statistics show live count of total/mapped/selected sensors

**Critical Methods:**
- `sensor_panel.py:86` - `on_item_clicked()` - Tree item selection handler
- `sensor_panel.py:427` - `highlight_and_scroll_to_sensor()` - Scroll to and highlight sensor

### Diagram Tab (`diagram_widget.py`)
- ✅ Diagram displays component layout on QGraphicsView
- ✅ Components are draggable, rotatable, and resizable
- ✅ Port mapping interface allows sensor-to-port assignments
- ✅ Component types: Compressor, Condenser, Evaporator, TXV, Distributor, FilterDrier, Junction, SensorBulb, Fan, AirSensorArray, ShelvingGrid

**Critical Methods:**
- `diagram_widget.py:506` - `update_sensor_highlighting()` - Update diagram when sensor selection changes
- `diagram_widget.py:512` - `build_scene_from_model()` - Rebuild diagram from saved model

### Sensor-Diagram Highlighting (Bidirectional Link)
**CRITICAL FEATURE:** Sensor selection must be synchronized between panel and diagram.

#### Panel → Diagram:
- ✅ When sensor is selected in Sensor Panel, corresponding dot on diagram **must turn RED**
- ✅ Implemented via `diagram_widget.py:677-987` - Updates dot brush color based on `data_manager.selected_sensors`

#### Diagram → Panel:
- ✅ When sensor dot is clicked on diagram, Sensor Panel **must scroll to and highlight** the sensor
- ✅ Implemented via `sensor_panel.py:427-466` - `highlight_and_scroll_to_sensor(sensor_name)`
- ✅ Expands collapsed groups if needed
- ✅ Scrolls sensor into view (centered)
- ✅ Highlights sensor by selecting it in tree

**Test Criteria:**
1. Select sensor "T_1a-lh" in panel → Red dot appears on diagram at mapped component port
2. Click red dot on diagram → Panel scrolls to "T_1a-lh" and highlights it
3. If sensor's group is collapsed, it must auto-expand when diagram dot is clicked

---

## 2. CSV Data Upload and Mapping (`mapping_dialog.py`, `data_manager.py`)

### Data Matching
- ✅ System matches sensor labels from saved config to columns in new CSV file
- ✅ Reconciliation logic: `data_manager.py:100-500` - `reconcile_csv_config()`
- ✅ Timestamp handling: Combines "Date" + "Time" columns, converts CDT → UTC

### Discrepancy Check
- ✅ If sensor names don't match CSV columns, discrepancies are detected
- ✅ MappingDialog always appears (even if no discrepancies) for user confirmation
- ✅ Provides auto-match suggestions, manual dropdown selection, or "Add New Column"

### Update Mechanism
- ✅ User confirms/adjusts mappings in dialog
- ✅ Changes propagate to Sensor Panel immediately via `data_changed` signal
- ✅ Moves/deletions update `data_manager.mappings` dictionary

### Mode Check
- ✅ **Drawing Mode:** Diagram editing (place components, draw pipes)
- ✅ **Mapping Mode:** CSV reconciliation dialog (map columns to sensors)
- ✅ **Analysis Mode:** View graphs, calculations, P-h diagrams

**Test Criteria:**
1. Load CSV → MappingDialog appears
2. Change mapping for "T_2a-LH" → Sensor Panel updates immediately
3. Save session → Load session → Mappings preserved correctly

---

## 3. Graph Tab Functionality (`graph_widget.py`)

### Group Selection
- ✅ Checking a sensor group checkbox → Highlights all sensors in that group
- ✅ Selected sensors immediately plot on Graph Tab
- ✅ Multi-sensor plotting with different colors per sensor
- ✅ X-axis: DateAxisItem with correct timestamp handling (CDT → UTC conversion to prevent 5-hour offset)

**Critical Implementation:**
- `graph_widget.py:130-150` - Timestamp conversion: `naive_local_time → UTC → Unix timestamp`
- `graph_widget.py:update_ui()` - Main graph rendering function

### Graph Removal
- ✅ Unchecking sensor group → Corresponding graph disappears immediately

### Legends
- ✅ Legend table displays at bottom with stats: **Avg, Min, Max, Delta** for each sensor
- ✅ Legend auto-updates when sensors added/removed

### Custom Range Tool
- ✅ Buttons: "Keep Range" and "Delete Range" modes
- ✅ LinearRegionItem allows user to select time range on graph

**Test Criteria:**
1. Select "Ambient" group → All ambient sensors plot with legends
2. Deselect group → Graphs and legends disappear
3. Legend shows correct Avg/Min/Max values

---

## 4. Custom Range Functionality (`graph_widget.py`, `data_manager.py`)

### User Selection
- ✅ User can select multiple non-contiguous time ranges using LinearRegionItem
- ✅ Ranges stored in `data_manager.custom_time_ranges = {'keep': [...], 'delete': [...]}`

### Delete Range
- ✅ User selects ranges → Clicks "Delete Range" → Selected data removed
- ✅ Remaining data displayed across all tabs

### Add Range (Keep Range Filter)
- ✅ User selects ranges → Clicks "Keep Range" → Only selected data shown
- ✅ All other data filtered out

### Universal Application
- ✅ Range selection triggers `data_manager.data_changed` signal
- ✅ All tabs (Graph, Calculations, P-h) update with filtered data

**Critical Methods:**
- `graph_widget.py:100-200` - `apply_custom_range()` - Apply time range filter
- `data_manager.py:200-400` - `get_filtered_data()` - Return time-filtered DataFrame

**Test Criteria:**
1. Select range 10:00-12:00 → Click "Keep Range" → Only that data shows in all tabs
2. Select range 14:00-15:00 → Click "Delete Range" → That data disappears
3. Calculations Tab and P-h Diagram reflect the same filtered data

---

## 5. Calculations Tab Integrity (`calculations_widget.py`) - **HIGHEST PRIORITY**

### Input Data
- ✅ Calculations use sensor data from port mappings (flexible, not hardcoded)
- ✅ Port resolver (`port_resolver.py`) dynamically finds sensor values
- ✅ Supports multi-circuit refrigeration (LH, CTR, RH coils)

### Calculation Engine (`calculation_engine.py`, `calculation_orchestrator.py`)
- ✅ Uses **CoolProp library** for thermodynamic properties (R290 refrigerant)
- ✅ Unit conversions: °F → K, PSIG → Pa absolute
- ✅ Isentropic compression assumption
- ✅ Isenthalpic TXV expansion

### Calculated Outputs
**Must output accurate values for:**
- ✅ Enthalpy (kJ/kg) at all 8 state points
- ✅ Entropy (kJ/kg·K)
- ✅ Density (kg/m³)
- ✅ Saturation temperatures (°F)
- ✅ Superheat (S.H) and Subcooling (S.C) in °F
- ✅ Mass flow rate (lb/hr) using volumetric efficiency
- ✅ Cooling capacity (BTU/hr, Watts)
- ✅ Compressor power, COP, EER

### Specific Locations (8 State Points)
- ✅ **TXV Outlets:** T_1a-lh, T_1a-ctr, T_1a-rh (3 circuits)
- ✅ **Evaporator Inlets:** T_2a-LH, T_2a-CTR, T_2a-RH
- ✅ **Evaporator Outlets:** T_2b-LH, T_2b-CTR, T_2b-RH
- ✅ **Compressor Inlet:** T_2b (combined)
- ✅ **Compressor Outlet:** T_3a
- ✅ **Condenser Outlet:** T_4b

### 54-Column Nested Header Output
- ✅ 4-row header structure (main sections, sub-sections, units, data keys)
- ✅ Sections: AT LH coil, AT CTR coil, AT RH coil, At compressor inlet, Comp outlet, At Condenser, AT TXV LH/CTR/RH, TOTAL
- ✅ Results displayed in collapsible QTreeWidget

### ON-Time Filtering
- ✅ Only rows where `suction_pressure > threshold` are processed (compressor ON state)
- ✅ Displays ON-time percentage

**CRITICAL TEST REQUIREMENT:**
```bash
python test_calculations.py ID6SU12WE-diagram-only.json
```
This test **MUST PASS** after any changes to:
- `calculation_engine.py`
- `calculation_orchestrator.py`
- `port_resolver.py`
- `data_manager.py` (calculation-related methods)

### Impact Warning (Code Review Protocol)
**Before modifying calculation code:**
1. ⚠️ Run `test_calculations.py` to establish baseline
2. ⚠️ Document expected changes to output values
3. ⚠️ Verify CoolProp calls remain valid (check refrigerant="R290", units)
4. ⚠️ Analyze dependencies:
   - Will this affect P-h diagram data flow?
   - Will this break port mapping resolution?
   - Will this change the 54-column output structure?
5. ⚠️ After changes, re-run test and compare results
6. ⚠️ Update documentation if thermodynamic assumptions change

**Test Criteria:**
1. Load config → Run Calculations → Verify 54-column output appears
2. Check superheat values are positive (compressor must see vapor)
3. Check subcooling values are positive (TXV must see liquid)
4. Check enthalpy increases across evaporator (heat absorbed)
5. Verify ON-time filtering works (only compressor-ON rows processed)

---

## 6. Data Filtration (`calculations_widget.py:307-605`)

### Discharge Pressure Range Filtering
**CRITICAL FEATURE:** User can filter calculation data by discharge pressure range.

#### UI Components:
- ✅ Label: "discharge press" (`calculations_widget.py:307`)
- ✅ QDoubleSpinBox: User input for minimum threshold (`calculations_widget.py:312-317`)
  - Default value: 55.0 PSIG
  - Range: -1e12 to 1e12
  - Precision: 2 decimal places
- ✅ Button: "Apply" button to trigger filter (`calculations_widget.py:319`)

#### Filter Logic:
- ✅ Method: `_apply_discharge_filter()` (`calculations_widget.py:576-605`)
- ✅ Finds discharge pressure column dynamically using port mapping
- ✅ Filters: `df[df[discharge_pressure_column] >= threshold]`
- ✅ Displays filtered row count: "X/Y rows after discharge press filter"

#### Integration:
- ✅ Filter applies **before** calculations run (`calculations_widget.py:500-501`)
- ✅ Works in combination with time-based filtering (1h, 3h, 8h, 16h, Custom)
- ✅ If discharge pressure sensor not mapped, filter is skipped gracefully

**Test Criteria:**
1. Enter "60.0" in discharge press spinbox → Click "Apply"
2. Verify only rows with `P_disch >= 60.0` are processed
3. Check status message shows filtered row count
4. Change threshold to "70.0" → Re-apply → Verify fewer rows processed
5. Set threshold to "-1e12" (disable) → Verify all rows processed

---

## 7. P-h Diagram Integration (`ph_diagram_interactive_widget.py`)

### Data Flow
- ✅ Calculations Tab emits `filtered_data_ready` signal with DataFrame
- ✅ P-h Diagram listens and calls `load_filtered_data()`
- ✅ Plots refrigeration cycle paths for LH, CTR, RH circuits

### Features
- ✅ R290 saturation dome (from CoolProp)
- ✅ Multi-circuit cycle paths (8 state points per circuit)
- ✅ Interactive cursor showing properties at any point
- ✅ PNG export functionality

**Test Criteria:**
1. Run Calculations → P-h diagram auto-updates
2. Verify 3 cycle paths appear (LH, CTR, RH)
3. Hover cursor → Properties tooltip appears
4. Export PNG → File saved successfully

---

## 8. Additional Critical Checks

### Timestamp Handling
- ✅ CSV timestamps (naive CDT) converted to UTC before Unix encoding
- ✅ Prevents 5-hour offset bug in DateAxisItem
- ✅ Implementation: `timestamp_fixer.py`, `graph_widget.py:130-150`

**Test:** Load CSV with timestamp "2025-04-13 06:02:32" → Verify graph x-axis shows correct time (not 5 hours off)

### Port Resolver Integrity
- ✅ Flexible sensor mapping (no hardcoded column names)
- ✅ Role key format: `"{ComponentType}.{ComponentID}.{PortName}"`
- ✅ Fallback: `"{ComponentID}.{PortName}"`
- ✅ Implementation: `port_resolver.py`

**Test:** Rename CSV column "T_2b-LH" to "T_2b_LH" → Mapping dialog handles gracefully

### Signal/Slot Connections
- ✅ `data_manager.data_changed` → All tabs update
- ✅ `calculations_widget.filtered_data_ready` → P-h diagram updates
- ✅ Sensor selection changes propagate to diagram highlighting

**Test:** Select sensor in panel → Verify diagram updates within 100ms

---

## When to Apply This Skill

**Automatically verify these requirements when:**
- ❗ Modifying `calculation_engine.py`, `calculation_orchestrator.py`, `port_resolver.py`
- ❗ Changing data flow in `data_manager.py`
- ❗ Updating UI components (sensor_panel, diagram_widget, graph_widget, calculations_widget)
- ❗ Modifying CSV loading, timestamp handling, or filtering logic
- ❗ Adding new features that interact with existing calculation/graphing/diagram systems
- ❗ Before merging PRs or pushing to main branch
- ❗ User explicitly requests testing or verification

**Verification Steps:**
1. Run `python test_calculations.py ID6SU12WE-diagram-only.json`
2. Manually test sensor highlighting (panel ↔ diagram)
3. Test CSV load → mapping → graphing → calculations workflow
4. Verify discharge pressure filter works
5. Check custom range selection across all tabs
6. Confirm P-h diagram updates when calculations complete

---

## Summary Checklist

Before approving any code change, verify:

- [ ] Sensor Panel displays all sensors correctly
- [ ] Diagram displays component layout
- [ ] **Sensor highlighting works bidirectionally (panel ↔ diagram)**
- [ ] CSV mapping dialog appears and updates correctly
- [ ] Graph Tab plots selected sensors with legends
- [ ] Custom range selection filters data across all tabs
- [ ] **Discharge pressure filter works (spinbox + Apply button)**
- [ ] Calculations Tab produces 54-column output with correct values
- [ ] `test_calculations.py` passes
- [ ] P-h Diagram updates when calculations complete
- [ ] Timestamp handling prevents 5-hour offset
- [ ] Port resolver maps sensors dynamically (no hardcoded names)
- [ ] Signal/slot connections propagate updates correctly

**If ANY of these fail, the code change must be revised before approval.**

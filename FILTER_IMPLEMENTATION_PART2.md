# THERMODYNAMIC DATA FILTERING SYSTEM - PART 2
## Integration and Implementation Steps

---

## 📁 FILE 3: Modifications to data_manager.py

### Add Filter Configuration Storage

```python
# In DataManager.__init__(), add:

self.filter_config = {
    'enabled_rules': [
        'R01_MIN_SUBCOOLING',      # Default enabled
        'R03_MIN_SUPERHEAT',         # Default enabled
        'R05_ENTHALPY_DIRECTION',   # Default enabled
        'R07_NO_VACUUM',             # Default enabled
        'R09_POSITIVE_QC',           # Default enabled
        'R12_WATER_TEMP_DIR',        # Default enabled
    ],
    'rule_params': {}
}
```

### Add Validation Method

```python
def apply_validation_filters(self, df: pd.DataFrame) -> tuple[pd.DataFrame, Dict]:
    """
    Apply thermodynamic validation filters to calculated results.

    Args:
        df: DataFrame with calculated results

    Returns:
        (filtered_df, statistics)
    """
    from validation_rules import ThermodynamicValidator

    if df.empty:
        return df, {'total_rows': 0, 'valid_rows': 0, 'filtered_rows': 0}

    validator = ThermodynamicValidator(
        enabled_rules=self.filter_config['enabled_rules'],
        rule_params=self.filter_config['rule_params']
    )

    filtered_df, stats = validator.validate_dataframe(df)

    print(f"[FILTER] Validation complete:")
    print(f"  Total rows: {stats['total_rows']}")
    print(f"  Valid rows: {stats['valid_rows']}")
    print(f"  Filtered out: {stats['filtered_rows']} ({stats['filter_percentage']:.1f}%)")

    return filtered_df, stats
```

### Add Session Save/Load for Filters

```python
# In save_session(), add to session dict:
"filterConfig": self.filter_config,

# In load_session(), add:
if 'filterConfig' in session_data:
    self.filter_config = session_data['filterConfig']
else:
    # Use defaults
    self.filter_config = {
        'enabled_rules': [...],  # default list
        'rule_params': {}
    }
```

---

## 📁 FILE 4: Modifications to calculation_orchestrator.py

### Apply Filters After Calculation

```python
# At the end of run_batch_processing(), before returning results:

def run_batch_processing(dataframe, mappings, compressor_specs, refrigerant):
    """
    ... existing code ...
    """

    # Calculate results (existing code)
    results_df = apply_calculations(...)  # your existing calculation logic

    # NEW: Apply validation filters
    from data_manager import DataManager  # or however you access it
    data_mgr = ...  # get reference to data manager

    filtered_df, filter_stats = data_mgr.apply_validation_filters(results_df)

    return {
        'ok': True,
        'dataframe': filtered_df,  # Return filtered data instead of raw
        'total_rows': len(results_df),
        'valid_rows': len(filtered_df),
        'filtered_rows': len(results_df) - len(filtered_df),
        'filter_stats': filter_stats
    }
```

---

## 📁 FILE 5: Modifications to calculations_widget.py

### Add Filter Configuration Button

```python
# In CalculationsWidget.__init__(), add button:

self.filter_config_btn = QPushButton("⚙️ Configure Filters")
self.filter_config_btn.clicked.connect(self.open_filter_config)
self.filter_config_btn.setToolTip("Configure thermodynamic validation rules")

# Add to button layout (near "Enter Rated Inputs" button)
button_layout.addWidget(self.filter_config_btn)
```

### Add Filter Status Label

```python
# Add label to show filter status:

self.filter_status_label = QLabel("Filters: Not configured")
self.filter_status_label.setStyleSheet("color: gray; font-size: 9pt;")
button_layout.addWidget(self.filter_status_label)

# Update after filtering:
def update_filter_status(self, stats):
    """Update filter status label with statistics."""
    if stats['filtered_rows'] == 0:
        self.filter_status_label.setText(
            f"Filters: ✅ All {stats['total_rows']} rows valid"
        )
        self.filter_status_label.setStyleSheet("color: green; font-size: 9pt;")
    else:
        self.filter_status_label.setText(
            f"Filters: ⚠️  Showing {stats['valid_rows']}/{stats['total_rows']} rows "
            f"({stats['filtered_rows']} filtered)"
        )
        self.filter_status_label.setStyleSheet("color: orange; font-size: 9pt;")
```

### Add Filter Configuration Method

```python
def open_filter_config(self):
    """Open filter configuration dialog."""
    from filter_config_dialog import FilterConfigDialog

    dialog = FilterConfigDialog(
        parent=self,
        current_config=self.data_manager.filter_config
    )

    if dialog.exec() == QDialog.DialogCode.Accepted:
        # Save new configuration
        new_config = dialog.get_config()
        self.data_manager.filter_config = new_config

        # Show summary
        enabled_count = len(new_config['enabled_rules'])
        QMessageBox.information(
            self,
            "Filters Updated",
            f"{enabled_count} validation rules enabled.\n\n"
            f"Click 'Run Calculations' to apply filters to data."
        )

        # Update button appearance
        self.filter_config_btn.setStyleSheet("font-weight: bold; background-color: #e8f5e9;")
```

### Display Filter Results

```python
def handle_calculation_complete(self, results):
    """
    Handle completion of batch calculations.

    Now receives filtered results and statistics.
    """
    if not results['ok']:
        # Handle error
        return

    df = results['dataframe']  # Already filtered
    filter_stats = results.get('filter_stats', {})

    # Update filter status display
    self.update_filter_status(filter_stats)

    # Display filtered data (existing code)
    self.populate_tree(df)

    # Optional: Add info message
    if filter_stats.get('filtered_rows', 0) > 0:
        filtered_count = filter_stats['filtered_rows']
        total_count = filter_stats['total_rows']
        msg = (
            f"Data filtering removed {filtered_count} rows with thermodynamic "
            f"impossibilities.\n\n"
            f"Showing {total_count - filtered_count} valid rows.\n\n"
            f"To adjust filters, click 'Configure Filters'."
        )
        QMessageBox.information(self, "Data Filtered", msg)
```

---

## 🎨 UI MOCKUP

```
┌────────────────────────────────────────────────────────────────────┐
│  Calculations                                                  [X] │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  [Enter Rated Inputs]  [⚙️ Configure Filters]  [Run Calculations] │
│                                                                    │
│  Filters: ⚠️  Showing 453/1243 rows (790 filtered)                │
│                                                                    │
├────────────────────────────────────────────────────────────────────┤
│  Results Tree (showing only valid data)                           │
│  ├─ Row 1: ...                                                    │
│  ├─ Row 2: ...                                                    │
│  └─ ...                                                           │
└────────────────────────────────────────────────────────────────────┘
```

### Filter Configuration Dialog Mockup

```
┌─────────────────────────────────────────────────────────────────────┐
│  Configure Thermodynamic Filters                              [X]  │
├─────────────────────────────────────────────────────────────────────┤
│  Select which validation rules to apply. Only rows that pass ALL   │
│  selected rules will be shown in the Calculations tab.             │
│                                                                     │
│  ┌─ Subcooling Rules ───────────────────────────────────────────┐ │
│  │  ☑ Eliminate Negative Subcooling                             │ │
│  │     Subcooling must be ≥ 0°F (liquid must exist)             │ │
│  │       min_subcooling: [0.0▾] °F                              │ │
│  │                                                               │ │
│  │  ☐ Require Healthy Subcooling Range                          │ │
│  │     Subcooling in healthy range (5-40°F)                     │ │
│  │       min_healthy: [5.0▾]  max_healthy: [40.0▾] °F           │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌─ Superheat Rules ────────────────────────────────────────────┐ │
│  │  ☑ Eliminate Zero/Negative Superheat                         │ │
│  │     Superheat must be ≥ 0°F (vapor must exist)               │ │
│  │       min_superheat: [0.0▾] °F                               │ │
│  │                                                               │ │
│  │  ☐ Require Safe Superheat Range                              │ │
│  │     Superheat 5-50°F (prevents liquid slugging)              │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌─ Enthalpy Rules ─────────────────────────────────────────────┐ │
│  │  ☑ Eliminate Enthalpy Reversal                               │ │
│  │     H_comp.in > H_txv (energy added in evaporator)           │ │
│  │                                                               │ │
│  │  ☐ Minimum Refrigeration Effect                              │ │
│  │     Δh_evap ≥ 50 kJ/kg (realistic cooling)                   │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌─ Cooling Capacity Rules ─────────────────────────────────────┐ │
│  │  ☑ Eliminate Negative Cooling Capacity                       │ │
│  │     qc ≥ 0 BTU/hr (must produce cooling)                     │ │
│  │                                                               │ │
│  │  ☐ Cooling Capacity Range                                    │ │
│  │     Realistic range for system size                          │ │
│  │       min_qc: [0▾]  max_qc: [100000▾] BTU/hr                 │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│                    [Restore Defaults]  [Cancel]  [OK]              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📋 IMPLEMENTATION STEPS

### Phase 1: Core Infrastructure (Day 1)
1. ✅ Create `validation_rules.py` with all validation functions
2. ✅ Create rule catalog with 12 rules
3. ✅ Implement `ThermodynamicValidator` class
4. ✅ Write unit tests for validation functions

### Phase 2: UI Development (Day 2)
5. ✅ Create `filter_config_dialog.py`
6. ✅ Build rule selection UI with checkboxes
7. ✅ Add parameter adjustment widgets
8. ✅ Test dialog with mock data

### Phase 3: Integration (Day 3)
9. ✅ Modify `data_manager.py` to store filter config
10. ✅ Add `apply_validation_filters()` method
11. ✅ Update session save/load to include filters
12. ✅ Modify `calculation_orchestrator.py` to apply filters

### Phase 4: Calculations Tab Integration (Day 4)
13. ✅ Add "Configure Filters" button to `calculations_widget.py`
14. ✅ Add filter status label
15. ✅ Connect button to dialog
16. ✅ Display filtered results
17. ✅ Show filter statistics

### Phase 5: Testing & Polish (Day 5)
18. ✅ Test with actual lab data (1,243 rows)
19. ✅ Verify 790 bad rows are filtered correctly
20. ✅ Test all rule combinations
21. ✅ Add tooltips and help text
22. ✅ Performance testing with large datasets

---

## 🧪 TESTING PLAN

### Unit Tests

```python
def test_negative_subcooling_filter():
    """Test that negative subcooling is filtered."""
    # Create test data with negative subcooling
    df = pd.DataFrame({
        'S.C': [-12.95, 5.0, -5.0, 10.0],
        'qc': [-5000, 25000, -8000, 30000]
    })

    validator = ThermodynamicValidator(
        enabled_rules=['R01_MIN_SUBCOOLING']
    )

    filtered_df, stats = validator.validate_dataframe(df)

    assert len(filtered_df) == 2  # Only rows with S.C >= 0
    assert stats['filtered_rows'] == 2
    assert stats['valid_rows'] == 2
```

### Integration Tests

```python
def test_full_filter_pipeline():
    """Test complete filtering pipeline with real data."""
    # Load actual calculated_results.csv
    df = pd.read_csv('calculated_results.csv')

    # Apply default filters
    validator = ThermodynamicValidator()
    filtered_df, stats = validator.validate_dataframe(df)

    # Verify expected filtering
    assert stats['total_rows'] == 1243
    assert stats['valid_rows'] == 453  # Expected good data
    assert stats['filtered_rows'] == 790  # Expected bad data
```

### User Acceptance Tests

1. ✅ Open filter dialog - all categories visible
2. ✅ Select/deselect rules - checkbox state preserved
3. ✅ Adjust parameters - spinboxes work correctly
4. ✅ Click OK - configuration saved
5. ✅ Run calculations - filters applied
6. ✅ Verify row count matches expected
7. ✅ Check filter status label updates
8. ✅ Reload session - filter config restored

---

## 📊 EXPECTED RESULTS

### With Default Filters Enabled

| Filter | Rows Affected | Percentage |
|--------|---------------|------------|
| R01: Min Subcooling | 789 | 63.5% |
| R03: Min Superheat | 1 | 0.1% |
| R05: Enthalpy Reversal | 465 | 37.4% |
| R07: No Vacuum | 0 | 0.0% |
| R09: Positive qc | 465 | 37.4% |
| R12: Water Temp Direction | 0 | 0.0% |
| **Combined (AND logic)** | **790** | **63.6%** |
| **Valid Data Remaining** | **453** | **36.4%** |

### Filter Impact Analysis

```
Original Data:    1,243 rows
├─ Negative qc:     465 rows (37.4%) → Filtered by R09 + R05 + R01
├─ Extreme qc:      297 rows (23.9%) → Could add R10 (qc range) filter
├─ High qc:          27 rows (2.2%)  → Could add R10 filter
├─ Very low qc:       1 row  (0.1%)  → Filtered by R03 (superheat)
└─ GOOD Data:       453 rows (36.4%) → ✅ Passes all filters
```

### User Benefits

1. **Clean Data**: Only thermodynamically valid data shown
2. **Flexible**: User controls which rules to apply
3. **Transparent**: Clear statistics on what was filtered
4. **Configurable**: Adjustable thresholds for each rule
5. **Persistent**: Filter settings saved in session

---

## 🔧 MAINTENANCE & EXTENSIBILITY

### Adding New Rules

To add a new validation rule:

1. **Create validation function** in `validation_rules.py`:
```python
def validate_my_new_rule(row: pd.Series, params: Dict) -> bool:
    # Your validation logic
    return True  # or False
```

2. **Add to RULE_CATALOG**:
```python
ValidationRule(
    rule_id='R13_MY_NEW_RULE',
    name='My New Rule Name',
    description='What this rule checks',
    category='Appropriate Category',
    validation_func=validate_my_new_rule,
    default_enabled=False,
    default_params={'threshold': 10.0},
    adjustable=True,
    param_ranges={'threshold': (5.0, 50.0)}
)
```

3. **Test the rule** - no UI changes needed!

### Customizing for Different Systems

For different refrigeration systems:

```python
# In data_manager.py or config file:

SYSTEM_PRESETS = {
    '3-ton-R290': {
        'R10_QC_RANGE': {'min_qc': 10000, 'max_qc': 40000},
        'R11_MDOT_RANGE': {'min_mdot': 100, 'max_mdot': 300},
    },
    '5-ton-R290': {
        'R10_QC_RANGE': {'min_qc': 15000, 'max_qc': 70000},
        'R11_MDOT_RANGE': {'min_mdot': 150, 'max_mdot': 500},
    },
    # Add more presets...
}
```

---

## 📖 USER DOCUMENTATION

### How to Use Filters

1. **Access Filter Configuration**
   - Click "Configure Filters" button in Calculations tab
   - Dialog shows all available validation rules

2. **Select Rules**
   - Check boxes for rules you want to apply
   - Uncheck to disable rules
   - Hover over rule names for descriptions

3. **Adjust Parameters** (if available)
   - Some rules have adjustable thresholds
   - Spin boxes appear when rule is enabled
   - Default values provided

4. **Apply Filters**
   - Click OK to save configuration
   - Click "Run Calculations" to apply filters
   - Only valid rows will appear in results

5. **Review Results**
   - Filter status shows: "X valid / Y total rows"
   - Filtered rows are not displayed
   - Can adjust filters and re-run if needed

### Recommended Filter Configurations

**Conservative (Keep more data):**
- ☑ Eliminate Negative Subcooling
- ☑ Eliminate Enthalpy Reversal
- ☑ Eliminate Negative Cooling Capacity

**Standard (Balanced):**
- ☑ All "Eliminate" rules
- ☑ No Vacuum
- ☑ Water Temperature Direction

**Strict (Best quality data):**
- ☑ All standard rules PLUS:
- ☑ Healthy Subcooling Range (5-40°F)
- ☑ Safe Superheat Range (5-50°F)
- ☑ Pressure Ratio Limits (1.5-10)
- ☑ Cooling Capacity Range (system-specific)

---

## 🎉 SUMMARY

This implementation provides:

✅ **12 thermodynamic validation rules** covering all major impossibilities
✅ **User-friendly configuration dialog** with checkboxes and parameters
✅ **Seamless integration** with existing calculations workflow
✅ **Persistent settings** saved in session files
✅ **Clear feedback** on filtering results
✅ **Extensible architecture** for adding new rules
✅ **No code changes needed** to adjust filters (user-configurable)

**Estimated Development Time:** 5 days
**Files Created:** 2 new files
**Files Modified:** 3 existing files
**Lines of Code:** ~1,500 lines

**Expected Outcome:**
- Current: 36.4% good data (453/1,243 rows)
- With filters: 100% valid data displayed (453 valid rows shown, 790 invalid hidden)
- User can adjust thresholds to get 50-90% of data depending on strictness

---

*End of Implementation Plan*

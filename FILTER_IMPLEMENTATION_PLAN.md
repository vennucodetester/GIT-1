# THERMODYNAMIC DATA FILTERING SYSTEM - IMPLEMENTATION PLAN

**Date:** 2025-11-04
**Goal:** Implement user-configurable filtering to eliminate thermodynamically impossible data
**Integration:** Pre-filter data before calculations tab display

---

## 📋 OVERVIEW

Create a validation rules system that:
1. Defines thermodynamic impossibility conditions
2. Allows user to select which rules to apply (checkboxes)
3. Filters calculated data before display
4. Shows only valid rows in calculations tab
5. Provides statistics on filtered vs total rows

---

## 🏗️ ARCHITECTURE

### Component Structure

```
┌─────────────────────────────────────────────────────────────┐
│                  User Workflow                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Click "Enter Rated Inputs" → Enter GPM, etc.           │
│  2. Click "Configure Filters" → Select validation rules    │
│  3. Click "Run Calculations" → Apply filters automatically │
│  4. View only VALID data in Calculations tab               │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  Code Architecture                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  validation_rules.py          (NEW)                         │
│  ├─ ValidationRule class                                    │
│  ├─ ThermodynamicValidator class                            │
│  └─ RULE_CATALOG (all 10+ rules defined)                    │
│                                                             │
│  filter_config_dialog.py      (NEW)                         │
│  ├─ FilterConfigDialog (QDialog)                            │
│  └─ Rule selection UI with checkboxes                       │
│                                                             │
│  data_manager.py              (MODIFY)                      │
│  ├─ Add: filter_config = {} attribute                       │
│  └─ Add: apply_validation_filters() method                  │
│                                                             │
│  calculation_orchestrator.py  (MODIFY)                      │
│  └─ Add: Filter results before returning                    │
│                                                             │
│  calculations_widget.py       (MODIFY)                      │
│  ├─ Add: "Configure Filters" button                         │
│  ├─ Add: Filter status label                                │
│  └─ Display filtered data only                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 VALIDATION RULES CATALOG

### Rule Categories

#### **Category 1: Subcooling Rules**
1. **Negative Subcooling Elimination**
   - Rule: `S.C >= min_subcooling`
   - Default: `S.C >= 0°F` (liquid must exist)
   - User adjustable: 0 to 5°F
   - Affected: 789 rows (63.5%)

2. **Insufficient Subcooling**
   - Rule: `S.C >= min_healthy_subcooling`
   - Default: `S.C >= 5°F` (healthy operation)
   - User adjustable: 3 to 15°F

3. **Excessive Subcooling**
   - Rule: `S.C <= max_subcooling`
   - Default: `S.C <= 40°F`
   - User adjustable: 20 to 60°F

#### **Category 2: Superheat Rules**
4. **Negative/Zero Superheat Elimination**
   - Rule: `S.H_total >= min_superheat`
   - Default: `S.H_total >= 0°F` (vapor must exist)
   - User adjustable: 0 to 5°F
   - Affected: 1 row (0.1%)

5. **Insufficient Superheat (Liquid Slugging Risk)**
   - Rule: `S.H_total >= min_safe_superheat`
   - Default: `S.H_total >= 5°F` (safety margin)
   - User adjustable: 3 to 10°F

6. **Excessive Superheat**
   - Rule: `S.H_total <= max_superheat`
   - Default: `S.H_total <= 50°F` (efficiency loss)
   - User adjustable: 30 to 100°F
   - Affected: 1,074 rows (86.4%) if strict

#### **Category 3: Enthalpy Rules**
7. **Enthalpy Reversal Elimination**
   - Rule: `H_comp.in > H_txv_avg` (energy added in evaporator)
   - Default: enabled
   - Affected: 465 rows (37.4%)

8. **Refrigeration Effect Minimum**
   - Rule: `(H_comp.in - H_txv_avg) >= min_delta_h_evap`
   - Default: `Δh >= 50 kJ/kg` (realistic cooling)
   - User adjustable: 30 to 150 kJ/kg

#### **Category 4: Pressure Rules**
9. **Vacuum Pressure Elimination**
   - Rule: `P_suction >= min_pressure`
   - Default: `P_suction >= -14.7 PSIG` (physical limit)
   - Affected: 0 rows (none below -14.7)

10. **Pressure Ratio Limits**
    - Rule: `min_PR <= (P_disch + 14.7) / (P_suction + 14.7) <= max_PR`
    - Default: `1.5 <= PR <= 10` (R290 typical)
    - User adjustable: 1.2 to 15
    - Affected: 10 rows (0.8%)

#### **Category 5: Cooling Capacity Rules**
11. **Negative Cooling Capacity Elimination**
    - Rule: `qc >= 0 BTU/hr`
    - Default: enabled
    - Affected: 465 rows (37.4%)

12. **Unrealistic Capacity Limits**
    - Rule: `min_qc <= qc <= max_qc`
    - Default: `0 <= qc <= 100,000 BTU/hr` (3-ton system)
    - User adjustable based on system size

#### **Category 6: Mass Flow Rules**
13. **Unrealistic Mass Flow Limits**
    - Rule: `min_mdot <= m_dot <= max_mdot`
    - Default: `50 <= m_dot <= 500 lb/hr` (typical for small system)
    - User adjustable

#### **Category 7: Temperature Consistency Rules**
14. **Water Temperature Direction**
    - Rule: `T_waterout > T_waterin` (heat rejection)
    - Default: enabled
    - Affected: 0 rows (all correct)

15. **Temperature Order Validation**
    - Rule: Verify T_hot_gas > T_condenser_out > T_evaporator_out
    - Default: optional
    - Complex rule checking thermodynamic cycle order

---

## 📁 FILE 1: validation_rules.py (NEW)

```python
"""
Thermodynamic Validation Rules System

Defines validation rules to filter thermodynamically impossible data.
Each rule checks a specific physical constraint.
"""

from typing import Dict, Any, Callable, List, Optional
import pandas as pd


class ValidationRule:
    """Represents a single validation rule."""

    def __init__(
        self,
        rule_id: str,
        name: str,
        description: str,
        category: str,
        validation_func: Callable[[pd.Series, Dict[str, Any]], bool],
        default_enabled: bool = True,
        default_params: Optional[Dict[str, Any]] = None,
        adjustable: bool = False,
        param_ranges: Optional[Dict[str, tuple]] = None
    ):
        self.rule_id = rule_id
        self.name = name
        self.description = description
        self.category = category
        self.validation_func = validation_func
        self.default_enabled = default_enabled
        self.default_params = default_params or {}
        self.adjustable = adjustable
        self.param_ranges = param_ranges or {}

    def validate(self, row: pd.Series, params: Dict[str, Any] = None) -> bool:
        """
        Validate a single row against this rule.

        Returns:
            True if row PASSES validation (keep it)
            False if row FAILS validation (filter it out)
        """
        params = params or self.default_params
        return self.validation_func(row, params)


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_min_subcooling(row: pd.Series, params: Dict) -> bool:
    """Subcooling must be >= minimum (liquid exists)."""
    sc = row.get('S.C')
    if sc is None or pd.isna(sc):
        return False  # Missing data = invalid
    return sc >= params.get('min_subcooling', 0.0)


def validate_healthy_subcooling(row: pd.Series, params: Dict) -> bool:
    """Subcooling in healthy operating range."""
    sc = row.get('S.C')
    if sc is None or pd.isna(sc):
        return False
    min_val = params.get('min_healthy', 5.0)
    max_val = params.get('max_healthy', 40.0)
    return min_val <= sc <= max_val


def validate_min_superheat(row: pd.Series, params: Dict) -> bool:
    """Superheat must be >= minimum (vapor exists)."""
    sh = row.get('S.H_total')
    if sh is None or pd.isna(sh):
        return False
    return sh >= params.get('min_superheat', 0.0)


def validate_safe_superheat(row: pd.Series, params: Dict) -> bool:
    """Superheat >= safe minimum (no liquid slugging risk)."""
    sh = row.get('S.H_total')
    if sh is None or pd.isna(sh):
        return False
    min_val = params.get('min_safe', 5.0)
    max_val = params.get('max_safe', 50.0)
    return min_val <= sh <= max_val


def validate_enthalpy_direction(row: pd.Series, params: Dict) -> bool:
    """H_comp.in > H_txv (energy added in evaporator)."""
    h_in = row.get('H_comp.in')
    h_txv_lh = row.get('H_txv.lh')
    h_txv_ctr = row.get('H_txv.ctr')
    h_txv_rh = row.get('H_txv.rh')

    if h_in is None or pd.isna(h_in):
        return False

    # Calculate average TXV enthalpy
    txv_values = [h for h in [h_txv_lh, h_txv_ctr, h_txv_rh]
                  if h is not None and not pd.isna(h)]

    if not txv_values:
        return False

    h_txv_avg = sum(txv_values) / len(txv_values)
    return h_in > h_txv_avg


def validate_min_refrigeration_effect(row: pd.Series, params: Dict) -> bool:
    """Minimum refrigeration effect (realistic cooling)."""
    h_in = row.get('H_comp.in')
    h_txv_lh = row.get('H_txv.lh')
    h_txv_ctr = row.get('H_txv.ctr')
    h_txv_rh = row.get('H_txv.rh')

    if h_in is None or pd.isna(h_in):
        return False

    txv_values = [h for h in [h_txv_lh, h_txv_ctr, h_txv_rh]
                  if h is not None and not pd.isna(h)]

    if not txv_values:
        return False

    h_txv_avg = sum(txv_values) / len(txv_values)
    delta_h = h_in - h_txv_avg

    min_delta = params.get('min_delta_h', 50.0)  # kJ/kg
    return delta_h >= min_delta


def validate_pressure_vacuum(row: pd.Series, params: Dict) -> bool:
    """Pressure >= physical minimum (no impossible vacuum)."""
    p_suc = row.get('P_suction')
    if p_suc is None or pd.isna(p_suc):
        return False
    return p_suc >= params.get('min_pressure', -14.7)


def validate_pressure_ratio(row: pd.Series, params: Dict) -> bool:
    """Pressure ratio in realistic range."""
    p_suc = row.get('P_suction')
    p_disch = row.get('P_disch')

    if p_suc is None or pd.isna(p_suc) or p_disch is None or pd.isna(p_disch):
        return False

    # Convert to absolute
    p_suc_abs = p_suc + 14.7
    p_disch_abs = p_disch + 14.7

    if p_suc_abs <= 0:
        return False

    pr = p_disch_abs / p_suc_abs

    min_pr = params.get('min_pr', 1.5)
    max_pr = params.get('max_pr', 10.0)
    return min_pr <= pr <= max_pr


def validate_cooling_capacity_positive(row: pd.Series, params: Dict) -> bool:
    """Cooling capacity must be positive."""
    qc = row.get('qc')
    if qc is None or pd.isna(qc):
        return False
    return qc >= 0


def validate_cooling_capacity_range(row: pd.Series, params: Dict) -> bool:
    """Cooling capacity in realistic range for system size."""
    qc = row.get('qc')
    if qc is None or pd.isna(qc):
        return False
    min_qc = params.get('min_qc', 0)
    max_qc = params.get('max_qc', 100000)
    return min_qc <= qc <= max_qc


def validate_mass_flow_range(row: pd.Series, params: Dict) -> bool:
    """Mass flow in realistic range."""
    m_dot = row.get('m_dot')
    if m_dot is None or pd.isna(m_dot):
        return False
    min_mdot = params.get('min_mdot', 50)
    max_mdot = params.get('max_mdot', 500)
    return min_mdot <= m_dot <= max_mdot


def validate_water_temp_direction(row: pd.Series, params: Dict) -> bool:
    """Water outlet > inlet (heat rejection)."""
    t_in = row.get('T_waterin')
    t_out = row.get('T_waterout')

    if t_in is None or pd.isna(t_in) or t_out is None or pd.isna(t_out):
        return False

    return t_out > t_in


# ============================================================================
# RULE CATALOG
# ============================================================================

RULE_CATALOG = [
    # Category 1: Subcooling
    ValidationRule(
        rule_id='R01_MIN_SUBCOOLING',
        name='Eliminate Negative Subcooling',
        description='Subcooling must be ≥ 0°F (liquid must exist at condenser outlet)',
        category='Subcooling',
        validation_func=validate_min_subcooling,
        default_enabled=True,
        default_params={'min_subcooling': 0.0},
        adjustable=True,
        param_ranges={'min_subcooling': (0.0, 5.0)}
    ),

    ValidationRule(
        rule_id='R02_HEALTHY_SUBCOOLING',
        name='Require Healthy Subcooling Range',
        description='Subcooling in healthy range (5-40°F)',
        category='Subcooling',
        validation_func=validate_healthy_subcooling,
        default_enabled=False,  # Optional stricter rule
        default_params={'min_healthy': 5.0, 'max_healthy': 40.0},
        adjustable=True,
        param_ranges={'min_healthy': (3.0, 15.0), 'max_healthy': (20.0, 60.0)}
    ),

    # Category 2: Superheat
    ValidationRule(
        rule_id='R03_MIN_SUPERHEAT',
        name='Eliminate Zero/Negative Superheat',
        description='Superheat must be ≥ 0°F (vapor must exist at compressor inlet)',
        category='Superheat',
        validation_func=validate_min_superheat,
        default_enabled=True,
        default_params={'min_superheat': 0.0},
        adjustable=True,
        param_ranges={'min_superheat': (0.0, 5.0)}
    ),

    ValidationRule(
        rule_id='R04_SAFE_SUPERHEAT',
        name='Require Safe Superheat Range',
        description='Superheat in safe range (5-50°F) - prevents liquid slugging',
        category='Superheat',
        validation_func=validate_safe_superheat,
        default_enabled=False,  # Optional
        default_params={'min_safe': 5.0, 'max_safe': 50.0},
        adjustable=True,
        param_ranges={'min_safe': (3.0, 10.0), 'max_safe': (30.0, 100.0)}
    ),

    # Category 3: Enthalpy
    ValidationRule(
        rule_id='R05_ENTHALPY_DIRECTION',
        name='Eliminate Enthalpy Reversal',
        description='H_comp.in > H_txv_avg (energy must be added in evaporator)',
        category='Enthalpy',
        validation_func=validate_enthalpy_direction,
        default_enabled=True,
        default_params={},
        adjustable=False
    ),

    ValidationRule(
        rule_id='R06_MIN_REFRIG_EFFECT',
        name='Minimum Refrigeration Effect',
        description='Δh_evap ≥ 50 kJ/kg (realistic cooling effect)',
        category='Enthalpy',
        validation_func=validate_min_refrigeration_effect,
        default_enabled=False,
        default_params={'min_delta_h': 50.0},
        adjustable=True,
        param_ranges={'min_delta_h': (30.0, 150.0)}
    ),

    # Category 4: Pressure
    ValidationRule(
        rule_id='R07_NO_VACUUM',
        name='Eliminate Impossible Vacuum',
        description='P_suction ≥ -14.7 PSIG (physical limit)',
        category='Pressure',
        validation_func=validate_pressure_vacuum,
        default_enabled=True,
        default_params={'min_pressure': -14.7},
        adjustable=False
    ),

    ValidationRule(
        rule_id='R08_PRESSURE_RATIO',
        name='Pressure Ratio Limits',
        description='1.5 ≤ PR ≤ 10 (typical R290 operation)',
        category='Pressure',
        validation_func=validate_pressure_ratio,
        default_enabled=False,
        default_params={'min_pr': 1.5, 'max_pr': 10.0},
        adjustable=True,
        param_ranges={'min_pr': (1.2, 2.0), 'max_pr': (8.0, 15.0)}
    ),

    # Category 5: Cooling Capacity
    ValidationRule(
        rule_id='R09_POSITIVE_QC',
        name='Eliminate Negative Cooling Capacity',
        description='qc ≥ 0 BTU/hr (must produce cooling)',
        category='Cooling Capacity',
        validation_func=validate_cooling_capacity_positive,
        default_enabled=True,
        default_params={},
        adjustable=False
    ),

    ValidationRule(
        rule_id='R10_QC_RANGE',
        name='Cooling Capacity Range',
        description='qc in realistic range (0-100K BTU/hr for 3-ton system)',
        category='Cooling Capacity',
        validation_func=validate_cooling_capacity_range,
        default_enabled=False,
        default_params={'min_qc': 0, 'max_qc': 100000},
        adjustable=True,
        param_ranges={'min_qc': (0, 10000), 'max_qc': (50000, 200000)}
    ),

    # Category 6: Mass Flow
    ValidationRule(
        rule_id='R11_MDOT_RANGE',
        name='Mass Flow Range',
        description='m_dot in realistic range (50-500 lb/hr)',
        category='Mass Flow',
        validation_func=validate_mass_flow_range,
        default_enabled=False,
        default_params={'min_mdot': 50, 'max_mdot': 500},
        adjustable=True,
        param_ranges={'min_mdot': (20, 100), 'max_mdot': (300, 1000)}
    ),

    # Category 7: Temperature Consistency
    ValidationRule(
        rule_id='R12_WATER_TEMP_DIR',
        name='Water Temperature Direction',
        description='T_waterout > T_waterin (heat rejection to water)',
        category='Temperature',
        validation_func=validate_water_temp_direction,
        default_enabled=True,
        default_params={},
        adjustable=False
    ),
]


class ThermodynamicValidator:
    """
    Main validator that applies selected rules to dataframe.
    """

    def __init__(self, enabled_rules: List[str] = None, rule_params: Dict[str, Dict] = None):
        """
        Initialize validator.

        Args:
            enabled_rules: List of rule IDs to enable (None = use defaults)
            rule_params: Dict of {rule_id: params} for adjustable rules
        """
        self.rule_catalog = {rule.rule_id: rule for rule in RULE_CATALOG}
        self.enabled_rules = enabled_rules or [r.rule_id for r in RULE_CATALOG if r.default_enabled]
        self.rule_params = rule_params or {}

    def validate_dataframe(self, df: pd.DataFrame) -> tuple[pd.DataFrame, Dict]:
        """
        Filter dataframe using enabled validation rules.

        Returns:
            (filtered_df, statistics_dict)
        """
        if df.empty:
            return df, {'total_rows': 0, 'valid_rows': 0, 'filtered_rows': 0}

        original_count = len(df)
        filtered_df = df.copy()

        # Track which rows pass each rule
        rule_results = {}

        for rule_id in self.enabled_rules:
            if rule_id not in self.rule_catalog:
                continue

            rule = self.rule_catalog[rule_id]
            params = self.rule_params.get(rule_id, rule.default_params)

            # Apply rule to each row
            mask = filtered_df.apply(lambda row: rule.validate(row, params), axis=1)
            rule_results[rule_id] = {
                'name': rule.name,
                'passed': mask.sum(),
                'failed': (~mask).sum()
            }

            # Filter dataframe
            filtered_df = filtered_df[mask]

        valid_count = len(filtered_df)
        filtered_count = original_count - valid_count

        statistics = {
            'total_rows': original_count,
            'valid_rows': valid_count,
            'filtered_rows': filtered_count,
            'filter_percentage': (filtered_count / original_count * 100) if original_count > 0 else 0,
            'rule_results': rule_results
        }

        return filtered_df, statistics


def get_rule_catalog_by_category() -> Dict[str, List[ValidationRule]]:
    """Get rules organized by category for UI display."""
    categories = {}
    for rule in RULE_CATALOG:
        if rule.category not in categories:
            categories[rule.category] = []
        categories[rule.category].append(rule)
    return categories
```

This is getting long. Let me create part 2 with the UI and integration code in the next file.

---

## 📁 FILE 2: filter_config_dialog.py (NEW)

```python
"""
Filter Configuration Dialog

Allows user to select which validation rules to apply.
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QCheckBox, QLabel, QPushButton, QScrollArea,
                             QWidget, QSpinBox, QDoubleSpinBox, QDialogButtonBox,
                             QFormLayout)
from PyQt6.QtCore import Qt
from validation_rules import RULE_CATALOG, get_rule_catalog_by_category
from typing import Dict, List, Any


class FilterConfigDialog(QDialog):
    """
    Dialog for configuring thermodynamic validation filters.

    Displays all available rules organized by category with:
    - Checkboxes to enable/disable each rule
    - Adjustable parameters for configurable rules
    - Descriptions of what each rule does
    """

    def __init__(self, parent=None, current_config: Dict = None):
        super().__init__(parent)
        self.setWindowTitle("Configure Thermodynamic Filters")
        self.setMinimumSize(700, 600)

        # Store current configuration
        self.config = current_config or self._get_default_config()

        # UI elements
        self.checkboxes = {}  # {rule_id: QCheckBox}
        self.param_widgets = {}  # {rule_id: {param_name: widget}}

        self._setup_ui()

    def _get_default_config(self) -> Dict:
        """Get default filter configuration."""
        return {
            'enabled_rules': [r.rule_id for r in RULE_CATALOG if r.default_enabled],
            'rule_params': {}
        }

    def _setup_ui(self):
        """Create the dialog UI."""
        layout = QVBoxLayout(self)

        # Title and instructions
        title = QLabel("<b>Thermodynamic Data Validation Filters</b>")
        title.setStyleSheet("font-size: 14pt;")
        layout.addWidget(title)

        instructions = QLabel(
            "Select which validation rules to apply. Only rows that pass ALL selected "
            "rules will be shown in the Calculations tab. This helps eliminate "
            "thermodynamically impossible data from analysis."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: gray; margin: 5px 0px;")
        layout.addWidget(instructions)

        # Scroll area for rules
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # Create rule groups by category
        categories = get_rule_catalog_by_category()
        for category_name in sorted(categories.keys()):
            rules = categories[category_name]
            group = self._create_rule_group(category_name, rules)
            scroll_layout.addWidget(group)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.RestoreDefaults
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(
            self._restore_defaults
        )
        layout.addWidget(button_box)

    def _create_rule_group(self, category_name: str, rules: List) -> QGroupBox:
        """Create a group box for a rule category."""
        group = QGroupBox(f"{category_name} Rules")
        layout = QVBoxLayout()

        for rule in rules:
            rule_widget = self._create_rule_widget(rule)
            layout.addWidget(rule_widget)

        group.setLayout(layout)
        return group

    def _create_rule_widget(self, rule) -> QWidget:
        """Create widget for a single rule."""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)

        # Checkbox for enable/disable
        checkbox = QCheckBox(rule.name)
        checkbox.setChecked(rule.rule_id in self.config['enabled_rules'])
        checkbox.setToolTip(rule.description)
        self.checkboxes[rule.rule_id] = checkbox
        layout.addWidget(checkbox)

        # Description
        desc_label = QLabel(rule.description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: gray; font-size: 9pt; margin-left: 20px;")
        layout.addWidget(desc_label)

        # Adjustable parameters (if any)
        if rule.adjustable and rule.param_ranges:
            param_layout = QFormLayout()
            param_layout.setContentsMargins(30, 0, 0, 0)

            rule_params = self.config['rule_params'].get(rule.rule_id, rule.default_params)

            for param_name, (min_val, max_val) in rule.param_ranges.items():
                # Determine widget type based on value type
                if isinstance(min_val, float):
                    spinbox = QDoubleSpinBox()
                    spinbox.setDecimals(2)
                else:
                    spinbox = QSpinBox()

                spinbox.setRange(min_val, max_val)
                spinbox.setValue(rule_params.get(param_name, rule.default_params.get(param_name, min_val)))
                spinbox.setEnabled(checkbox.isChecked())

                # Connect checkbox to enable/disable params
                checkbox.toggled.connect(spinbox.setEnabled)

                param_layout.addRow(f"  {param_name}:", spinbox)

                # Store widget reference
                if rule.rule_id not in self.param_widgets:
                    self.param_widgets[rule.rule_id] = {}
                self.param_widgets[rule.rule_id][param_name] = spinbox

            layout.addLayout(param_layout)

        widget.setLayout(layout)
        return widget

    def _restore_defaults(self):
        """Restore default settings."""
        default_config = self._get_default_config()

        # Update checkboxes
        for rule_id, checkbox in self.checkboxes.items():
            checkbox.setChecked(rule_id in default_config['enabled_rules'])

        # Update parameter widgets
        for rule_id, params in self.param_widgets.items():
            rule = next((r for r in RULE_CATALOG if r.rule_id == rule_id), None)
            if rule:
                for param_name, widget in params.items():
                    default_val = rule.default_params.get(param_name)
                    if default_val is not None:
                        widget.setValue(default_val)

    def get_config(self) -> Dict:
        """Get current configuration from UI."""
        enabled_rules = [rule_id for rule_id, checkbox in self.checkboxes.items()
                        if checkbox.isChecked()]

        rule_params = {}
        for rule_id, params in self.param_widgets.items():
            rule_params[rule_id] = {}
            for param_name, widget in params.items():
                rule_params[rule_id][param_name] = widget.value()

        return {
            'enabled_rules': enabled_rules,
            'rule_params': rule_params
        }
```

Let me continue with the integration plan in a separate document since this is getting very long.

---

*Continued in implementation document...*

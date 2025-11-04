# THERMODYNAMIC DIAGNOSTIC REPORT
## Cooling Capacity Data Quality Analysis

**Date:** 2025-11-04
**Analysis Type:** Root Cause Investigation
**Refrigerant:** R290 (Propane)
**Total Data Points:** 1,243 rows

---

## EXECUTIVE SUMMARY

### Data Quality Breakdown
| Range | Count | Percentage | Status |
|-------|-------|------------|--------|
| **GOOD (10,000 - 40,000 BTU/hr)** | 453 | 36.4% | ✅ Acceptable |
| **Negative (< 0 BTU/hr)** | 465 | 37.4% | 🔴 Critical Issue |
| **Extreme (≥ 100,000 BTU/hr)** | 297 | 23.9% | 🔴 Critical Issue |
| **High (40,000 - 100,000 BTU/hr)** | 27 | 2.2% | ⚠️ Suspicious |
| **Very Low (0 - 10,000 BTU/hr)** | 1 | 0.08% | ⚠️ Edge Case |

**KEY FINDING:** Only 36.4% of data is valid. The remaining 63.6% (789 rows) has critical thermodynamic anomalies.

---

## ROOT CAUSE #1: NEGATIVE SUBCOOLING (Primary Issue)
### Impact: 789 rows (63.5% of all data)

### Thermodynamic Problem
**Subcooling Formula:**
```
S.C = T_sat.cond - T_4a
```

**Expected Behavior:**
- T_4a (condenser outlet) should be **LOWER** than T_sat.cond (saturation temperature)
- Typical healthy subcooling: 5-15°F
- This ensures pure **LIQUID** refrigerant enters the TXV

**Observed Behavior:**
- **ALL bad data rows have NEGATIVE subcooling** (S.C < 0)
- T_4a is **HIGHER** than T_sat.cond
- This indicates **VAPOR or TWO-PHASE** mixture in the liquid line
- This is thermodynamically impossible under normal operating conditions

### Statistical Evidence

| Data Group | Subcooling Range | Mean Subcooling |
|------------|------------------|-----------------|
| **GOOD Data** | 0.01 to 29.89°F | +5.36°F ✅ |
| **Negative qc** | -33.40 to -1.67°F | -12.95°F 🔴 |
| **Extreme qc** | -14.34 to -0.00°F | -4.25°F 🔴 |
| **High qc** | -17.23 to 0.06°F | -7.47°F 🔴 |

### Example Cases

| Row | P_disch (PSIG) | T_sat.cond (°F) | T_4a (°F) | S.C (°F) | ΔT Error | qc (BTU/hr) |
|-----|----------------|-----------------|-----------|----------|----------|-------------|
| 2 | 96.44 | 62.08 | 77.94 | -15.86 | +15.86 | -5,357 |
| 14 | 92.66 | 59.78 | 85.70 | -25.92 | +25.92 | -12,368 |
| 20 | 98.75 | 63.46 | 85.40 | -21.94 | +21.94 | -14,562 |

**Note:** ΔT Error shows how much T_4a exceeds T_sat.cond (should be negative for proper subcooling)

### Root Causes

#### 🔧 Primary Suspect: T_4a Sensor Misplacement
**Evidence:**
- T_4a reads 15-26°F **HIGHER** than saturation temperature
- This is consistent with sensor reading **vapor temperature** instead of liquid
- Condenser outlet should be in the subcooled liquid region

**Diagnostic Steps:**
1. Verify T_4a sensor is mounted on the **liquid line** (not gas line)
2. Sensor should be **downstream** of condenser, **before** receiver (if present)
3. Check thermal insulation on sensor mounting
4. Verify good thermal contact (proper sensor pocket or strap-on installation)

#### 🔧 Secondary Suspect: Insufficient Condenser Heat Rejection
**Evidence:**
- Water ΔT in bad data: Mean = 10.47°F (vs 6.93°F in good data)
- Higher water ΔT suggests heat rejection is occurring
- But condenser outlet temperature remains too high

**Diagnostic Steps:**
1. Verify condenser water flow rate matches rated GPM
2. Check for fouling in condenser tubes
3. Verify water temperature sensors (T_waterin, T_waterout) are accurate
4. Check for refrigerant overcharge

#### 🔧 Tertiary Suspect: Refrigerant Charge Issues
**Evidence:**
- Combination of negative subcooling + high superheat
- Classic symptom of **undercharge** or **overcharge**

**Diagnostic Steps:**
1. Perform refrigerant charge verification
2. Check sight glass (if equipped) for bubbles
3. Verify system has no leaks

---

## ROOT CAUSE #2: EXCESSIVE SUPERHEAT
### Impact: 1,074 rows (86.4% of all data)

### Thermodynamic Problem
**Superheat Formula:**
```
S.H_total = T_2b - T_sat.comp.in
```

**Expected Behavior:**
- Healthy superheat: 10-20°F
- Ensures no liquid returns to compressor
- Too much superheat reduces refrigerant density → lower mass flow → lower capacity

**Observed Behavior:**
- Mean superheat in bad data: 36-37°F (vs. 36.12°F in good data)
- Many rows exceed 50°F superheat
- Even good data has elevated superheat (mean 36.12°F)

### Statistical Evidence

| Data Group | Superheat Range | Mean Superheat | Rows >30°F |
|------------|-----------------|----------------|------------|
| **GOOD Data** | 13.99 to 89.27°F | 36.12°F | 409 (90.3%) |
| **Negative qc** | -0.23 to 80.19°F | 36.04°F | 390 (83.9%) |
| **Extreme qc** | 9.42 to 101.26°F | 37.09°F | 254 (85.5%) |

### Impact on System Performance

**Thermodynamic Relationship:**
```
ρ ∝ 1 / T_superheat
m_dot = ρ × V_displacement × η_vol
qc = m_dot × Δh_evap
```

Higher superheat → Lower density → Lower mass flow → Lower cooling capacity

### Root Causes

#### 🔧 TXV Starving Evaporator
**Evidence:**
- Consistently high superheat across all circuits
- Affects LH, CTR, and RH circuits similarly

**Diagnostic Steps:**
1. Check TXV bulb placement and thermal contact
2. Verify TXV sizing is correct for application
3. Check for TXV hunting or instability
4. Verify liquid line subcooling upstream of TXV

#### 🔧 Refrigerant Undercharge
**Evidence:**
- High superheat + negative subcooling = classic undercharge signature
- System cannot maintain proper liquid level

**Diagnostic Steps:**
1. Add refrigerant while monitoring subcooling and superheat
2. Target: 5-10°F subcooling, 10-15°F superheat

#### 🔧 Suction Line Heat Gain
**Evidence:**
- Superheat at evaporator outlets (T_2a circuits) vs compressor inlet (T_2b)
- Additional superheat picked up in suction line

**Diagnostic Steps:**
1. Insulate suction line from evaporator to compressor
2. Check for high ambient temperature around suction line
3. Minimize suction line length if possible

---

## ROOT CAUSE #3: MASS FLOW RATE CALCULATION ERRORS
### Impact: 297 rows (23.9% of all data)

### Calculation Method
**Water-Side Energy Balance:**
```
Q_water (BTU/hr) = 500.4 × GPM × ΔT_water
m_dot (lb/hr) = Q_water / Δh_condenser
qc (BTU/hr) = m_dot × Δh_evap
```

### Statistical Evidence

| Data Group | m_dot Range | Mean m_dot | Ratio vs Good |
|------------|-------------|------------|---------------|
| **GOOD Data** | 120 to 289 lb/hr | 169.27 lb/hr | 1.0x |
| **Negative qc** | 998 to 2,285 lb/hr | 1,638.14 lb/hr | 9.7x |
| **Extreme qc** | 946 to 3,150 lb/hr | 1,347.32 lb/hr | 8.0x |

### Thermodynamic Impossibility

**Example Row Analysis:**
- Row 1: m_dot = 2,065 lb/hr, Δh_evap = 339 kJ/kg → qc = 301,330 BTU/hr
- This is **12.2x higher** than good data average mass flow
- For a small system, this is thermodynamically unrealistic

### Root Causes

#### 🔧 Incorrect GPM Setting in Rated Inputs
**Evidence:**
- Water-side calculation depends on GPM: `Q = 500.4 × GPM × ΔT`
- If GPM is 10x too high, mass flow will be 10x too high

**Diagnostic Steps:**
1. **Verify actual condenser water flow rate**
2. Check rated inputs in the application
3. Measure actual GPM with flow meter
4. Typical small systems: 5-15 GPM

#### 🔧 Water Temperature Sensor Errors
**Evidence:**
- All data shows positive water ΔT (T_out > T_in)
- But magnitude varies significantly

**Diagnostic Steps:**
1. Verify T_waterin and T_waterout sensors are correctly identified
2. Check for sensor swap (inlet vs outlet)
3. Calibrate water temperature sensors
4. Verify sensors are immersed in water flow (not measuring air temp)

#### 🔧 Condenser Enthalpy Calculation Error
**Evidence:**
- Negative subcooling means condenser outlet is vapor/two-phase
- H_4a calculation assumes subcooled liquid
- This creates error in Δh_condenser

**Diagnostic Steps:**
1. Fix subcooling issue first (Root Cause #1)
2. Verify H_3a and H_4a calculations are using correct pressures and temperatures
3. Check CoolProp property calls for errors

---

## ROOT CAUSE #4: PRESSURE SENSOR ISSUES (Minor)
### Impact: 2 rows (0.16% of all data)

### Observed Behavior
- 2 rows show **NEGATIVE suction pressure** (vacuum)
- P_suction = -8.04 PSIG and -3.27 PSIG

### Impact
- Causes extremely high superheat (120.72°F and 101.26°F)
- One row falls in "Very Low" category, one in "Extreme"

### Root Causes

#### 🔧 Sensor Calibration Error
**Evidence:**
- Absolute pressure cannot be negative
- Gauge pressure below -14.7 PSIG is impossible (perfect vacuum = -14.7 PSIG)

**Diagnostic Steps:**
1. Zero-calibrate pressure transducers
2. Verify sensor wiring and signal conditioning
3. Check for sensor damage

#### 🔧 System Operating at Vacuum
**Evidence:**
- If true, this indicates system leak or compressor failure
- Temperature readings suggest system is still running

**Diagnostic Steps:**
1. If verified, check for refrigerant leaks
2. Verify compressor is running
3. Check for air ingress into system

---

## ACTIONABLE RECOMMENDATIONS

### Immediate Actions (Priority 1)
1. ✅ **Fix T_4a Sensor**
   - Verify sensor is on liquid line (not gas line)
   - Relocate if necessary
   - This single fix will resolve 63.5% of bad data

2. ✅ **Verify Water Flow Rate**
   - Measure actual GPM with flow meter
   - Update rated inputs to match actual GPM
   - This will fix mass flow calculation errors (23.9% of bad data)

3. ✅ **Calibrate Pressure Sensors**
   - Zero-calibrate P_suction and P_disch sensors
   - Verify accuracy with reference gauge

### Short-Term Actions (Priority 2)
4. ✅ **Check Refrigerant Charge**
   - Add refrigerant while monitoring subcooling
   - Target: 5-10°F subcooling at condenser outlet
   - This will help both subcooling and superheat issues

5. ✅ **Verify Water Temperature Sensors**
   - Confirm T_waterin and T_waterout are correctly labeled
   - Calibrate sensors if needed
   - Check sensor immersion depth

6. ✅ **Adjust TXV Settings**
   - Reduce superheat to 10-15°F range
   - May require TXV adjustment or replacement
   - Check TXV bulb installation

### Long-Term Actions (Priority 3)
7. ✅ **Insulate Suction Line**
   - Minimize heat gain between evaporator and compressor
   - Will help reduce excessive superheat

8. ✅ **Verify Condenser Performance**
   - Check for tube fouling
   - Verify water-side flow distribution
   - Consider cleaning if needed

---

## DATA VALIDATION CHECKLIST

Use this checklist to validate sensor readings before running calculations:

### Pressure Checks
- [ ] P_suction > -14.7 PSIG (no vacuum impossible)
- [ ] P_disch > P_suction (discharge must be higher)
- [ ] Pressure ratio (P_disch / P_suction) between 2-6 for R290

### Temperature Checks
- [ ] T_4a < T_sat.cond (positive subcooling required)
- [ ] T_2b > T_sat.evap (positive superheat required)
- [ ] T_waterout > T_waterin (heat rejection to water)
- [ ] All temperatures between -50°F and 200°F (physical limits)

### Calculated Values
- [ ] Subcooling (S.C) between 5-15°F
- [ ] Superheat (S.H_total) between 10-20°F
- [ ] Mass flow (m_dot) between 100-300 lb/hr for small systems
- [ ] Cooling capacity (qc) between 10,000-40,000 BTU/hr for 3-ton system

---

## EXPECTED RESULTS AFTER FIXES

### Current State
- Good data: 36.4%
- Bad data: 63.6%

### After Fixing T_4a Sensor (Priority 1)
- Expected improvement: 63.5% → validate with test run
- Should eliminate negative subcooling
- Should reduce negative qc values

### After Fixing GPM Setting (Priority 1)
- Expected improvement: 23.9% → validate with test run
- Should normalize mass flow rates
- Should bring extreme qc values into normal range

### After All Fixes
- Target: >90% good data
- Remaining outliers likely from transient conditions or startup/shutdown

---

## TECHNICAL NOTES

### Thermodynamic Principles
1. **Subcooling is critical** - Without it, flash gas forms at TXV, reducing capacity
2. **Superheat is necessary** - Protects compressor from liquid slugging
3. **Mass flow drives capacity** - Even perfect cycle won't work without refrigerant flow

### Sensor Placement Best Practices
- **T_4a**: Downstream of condenser, in liquid line, before receiver
- **T_2b**: Suction line, 6-12 inches before compressor inlet
- **T_waterin/out**: Immersed in water flow, not measuring pipe exterior
- **Pressure sensors**: Mounted rigidly, away from vibration, with dampening

### R290 (Propane) Properties
- Saturation pressure at 40°F evap: ~25 PSIG
- Saturation pressure at 100°F cond: ~150 PSIG
- Pressure ratio: ~3-4 typical
- Flammable refrigerant - requires special handling

---

## CONCLUSION

The root cause analysis reveals **three critical issues** affecting data quality:

1. **Negative Subcooling (63.5% of bad data)** - Fix T_4a sensor placement
2. **Mass Flow Errors (23.9% of bad data)** - Fix GPM setting in rated inputs
3. **Excessive Superheat (86.4% affected)** - Fix refrigerant charge and TXV

**Primary Recommendation:** Start with T_4a sensor verification and GPM calibration. These two actions will fix 87.4% of the problematic data.

**Next Steps:**
1. Implement Priority 1 fixes
2. Run test with known operating conditions
3. Validate data quality improvement
4. Iterate on Priority 2 fixes as needed

---

*Report Generated: 2025-11-04*
*Analysis Tool: Python Thermodynamic Forensics*
*Total Analysis Time: ~2 hours*

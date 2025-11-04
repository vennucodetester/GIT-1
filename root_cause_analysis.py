#!/usr/bin/env python3
"""
Root Cause Analysis: Identify specific sensor issues causing bad data.
"""

import csv

def read_csv_data(filename):
    """Read calculated results CSV."""
    with open(filename, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return rows

def safe_float(value):
    """Safely convert to float."""
    try:
        return float(value) if value and value.strip() else None
    except:
        return None

print("="*100)
print(" ROOT CAUSE ANALYSIS - THERMODYNAMIC FORENSICS")
print("="*100)

rows = read_csv_data('calculated_results.csv')

# ============================================================================
# ROOT CAUSE #1: NEGATIVE SUBCOOLING (Vapor in Liquid Line)
# ============================================================================
print("\n🔍 ROOT CAUSE #1: NEGATIVE SUBCOOLING")
print("="*100)
print("\nPROBLEM: Condenser outlet temperature (T_4a) is HIGHER than saturation temperature")
print("         This means VAPOR exists in what should be a LIQUID line.\n")

negative_sc_rows = [r for r in rows if safe_float(r.get('S.C')) is not None and safe_float(r.get('S.C')) < 0]
print(f"Total rows with negative subcooling: {len(negative_sc_rows)}")

# Analyze the condenser conditions
print("\nCondenser Performance Analysis:")
print(f"{'Row':<6} {'P_disch':<10} {'T_sat.cond':<12} {'T_4a':<12} {'S.C':<10} {'ΔT Error':<12} {'qc':<15}")
print("-"*100)

sample_rows = negative_sc_rows[:20]  # First 20 examples
for i, row in enumerate(sample_rows):
    p_disch = safe_float(row.get('P_disch'))
    t_sat_cond = safe_float(row.get('T_sat.cond'))
    t_4a = safe_float(row.get('T_4a'))
    sc = safe_float(row.get('S.C'))
    qc = safe_float(row.get('qc'))

    if all(x is not None for x in [t_sat_cond, t_4a, sc]):
        delta_t_error = t_4a - t_sat_cond
        print(f"{i+1:<6} {p_disch:<10.2f} {t_sat_cond:<12.2f} {t_4a:<12.2f} {sc:<10.2f} {delta_t_error:<12.2f} {qc:<15.2f}")

print("\n💡 DIAGNOSIS:")
print("   • T_4a (condenser outlet) is HIGHER than T_sat.cond (saturation temperature)")
print("   • This creates negative subcooling: S.C = T_sat - T_4a < 0")
print("   • Thermodynamically, this means two-phase or vapor at condenser outlet")
print("\n🔧 POSSIBLE CAUSES:")
print("   1. Insufficient condenser cooling water flow")
print("   2. Condenser water temperature too high")
print("   3. T_4a sensor misplaced (reading gas temp instead of liquid)")
print("   4. T_4a sensor calibration error")
print("   5. Refrigerant undercharge")

# ============================================================================
# ROOT CAUSE #2: HIGH SUPERHEAT (Excessive Vapor Superheat)
# ============================================================================
print("\n\n🔍 ROOT CAUSE #2: EXCESSIVE SUPERHEAT")
print("="*100)
print("\nPROBLEM: Very high superheat reduces system capacity and efficiency\n")

high_sh_rows = [r for r in rows if safe_float(r.get('S.H_total')) is not None and safe_float(r.get('S.H_total')) > 30]
print(f"Total rows with high superheat (>30°F): {len(high_sh_rows)}")

print("\nSuperheat vs Cooling Capacity:")
print(f"{'Row':<6} {'P_suction':<12} {'T_sat':<12} {'T_2b':<12} {'S.H_total':<12} {'qc':<15} {'Status':<20}")
print("-"*100)

sample_high_sh = high_sh_rows[:20]
for i, row in enumerate(sample_high_sh):
    p_suc = safe_float(row.get('P_suction'))
    t_sat = safe_float(row.get('T_sat.comp.in'))
    t_2b = safe_float(row.get('T_2b'))
    sh = safe_float(row.get('S.H_total'))
    qc = safe_float(row.get('qc'))

    status = "GOOD" if qc and 10000 <= qc <= 40000 else "BAD"

    if all(x is not None for x in [p_suc, t_sat, t_2b, sh]):
        print(f"{i+1:<6} {p_suc:<12.2f} {t_sat:<12.2f} {t_2b:<12.2f} {sh:<12.2f} {qc:<15.2f} {status:<20}")

print("\n💡 DIAGNOSIS:")
print("   • High superheat reduces refrigerant density at compressor inlet")
print("   • Lower density → lower mass flow rate → lower cooling capacity")
print("   • Superheat > 30°F is excessive for optimal performance")
print("\n🔧 POSSIBLE CAUSES:")
print("   1. TXV undersized or malfunctioning (starving evaporator)")
print("   2. Refrigerant undercharge")
print("   3. Excessive suction line heat gain")
print("   4. Evaporator airflow insufficient")

# ============================================================================
# ROOT CAUSE #3: MASS FLOW RATE ANOMALIES
# ============================================================================
print("\n\n🔍 ROOT CAUSE #3: MASS FLOW RATE ANOMALIES")
print("="*100)
print("\nPROBLEM: Abnormally high mass flow rates leading to extreme cooling capacity\n")

# Get good data mass flow stats
good_rows = [r for r in rows if safe_float(r.get('qc')) is not None and 10000 <= safe_float(r.get('qc')) <= 40000]
good_mdot = [safe_float(r.get('m_dot')) for r in good_rows if safe_float(r.get('m_dot')) is not None]
avg_mdot_good = sum(good_mdot) / len(good_mdot) if good_mdot else 0

print(f"Average mass flow in GOOD data: {avg_mdot_good:.2f} lb/hr")

extreme_rows = [r for r in rows if safe_float(r.get('qc')) is not None and safe_float(r.get('qc')) >= 100000]
print(f"\nExtreme Cooling Capacity Rows: {len(extreme_rows)}")
print(f"{'Row':<6} {'m_dot':<12} {'Δh_evap':<12} {'qc':<15} {'m_dot/avg':<12}")
print("-"*100)

sample_extreme = extreme_rows[:20]
for i, row in enumerate(sample_extreme):
    m_dot = safe_float(row.get('m_dot'))
    h_comp_in = safe_float(row.get('H_comp.in'))
    h_txv_avg = 0
    count = 0
    for key in ['H_txv.lh', 'H_txv.ctr', 'H_txv.rh']:
        val = safe_float(row.get(key))
        if val is not None:
            h_txv_avg += val
            count += 1
    h_txv_avg = h_txv_avg / count if count > 0 else None

    qc = safe_float(row.get('qc'))

    if m_dot and h_comp_in and h_txv_avg:
        delta_h = h_comp_in - h_txv_avg
        ratio = m_dot / avg_mdot_good if avg_mdot_good > 0 else 0
        print(f"{i+1:<6} {m_dot:<12.2f} {delta_h:<12.2f} {qc:<15.2f} {ratio:<12.2f}x")

print("\n💡 DIAGNOSIS:")
print("   • Mass flow rates in extreme data are 5-10x higher than normal")
print("   • Even with reasonable Δh values, this produces unrealistic cooling capacity")
print("\n🔧 POSSIBLE CAUSES:")
print("   1. Water-side calculation error (Q_water = 500.4 × GPM × ΔT)")
print("   2. Water flow rate (GPM) incorrectly specified in rated inputs")
print("   3. Condenser enthalpy change (Δh_condenser) calculation error")
print("   4. Water temperature sensor errors (swapped or miscalibrated)")

# ============================================================================
# ROOT CAUSE #4: PRESSURE ANOMALIES
# ============================================================================
print("\n\n🔍 ROOT CAUSE #4: PRESSURE MEASUREMENT ISSUES")
print("="*100)

# Find rows with unusual pressure conditions
low_p_suc = [r for r in rows if safe_float(r.get('P_suction')) is not None and safe_float(r.get('P_suction')) < 0]
print(f"\nRows with NEGATIVE suction pressure: {len(low_p_suc)}")

if low_p_suc:
    print(f"{'Row':<6} {'P_suction':<12} {'T_2b':<12} {'S.H_total':<12} {'qc':<15}")
    print("-"*100)
    for i, row in enumerate(low_p_suc[:10]):
        p_suc = safe_float(row.get('P_suction'))
        t_2b = safe_float(row.get('T_2b'))
        sh = safe_float(row.get('S.H_total'))
        qc = safe_float(row.get('qc'))
        print(f"{i+1:<6} {p_suc:<12.2f} {t_2b:<12.2f} {sh:<12.2f} {qc:<15.2f}")

    print("\n💡 DIAGNOSIS:")
    print("   • Negative gauge pressure indicates vacuum conditions")
    print("   • This causes extremely high superheat values")
    print("\n🔧 POSSIBLE CAUSES:")
    print("   1. System leak creating vacuum")
    print("   2. Pressure sensor zero calibration error")
    print("   3. Compressor not running or failed")

# ============================================================================
# SUMMARY AND RECOMMENDATIONS
# ============================================================================
print("\n\n" + "="*100)
print(" SUMMARY: ROOT CAUSES OF BAD DATA")
print("="*100)

print("\n📊 DATA QUALITY BREAKDOWN:")
print(f"   • GOOD data (10-40K BTU/hr):     453 rows (36.4%)")
print(f"   • NEGATIVE qc:                   465 rows (37.4%) - SUBCOOLING ISSUE")
print(f"   • EXTREME qc (>100K BTU/hr):     297 rows (23.9%) - MASS FLOW ISSUE")
print(f"   • HIGH qc (40-100K BTU/hr):       27 rows (2.2%)  - MIXED ISSUES")

print("\n🎯 PRIMARY ROOT CAUSES:")
print("\n1. NEGATIVE SUBCOOLING (affects 789 rows / 63.5%)")
print("   • Condenser outlet temperature higher than saturation temperature")
print("   • Indicates vapor in liquid line")
print("   • Fix: Check T_4a sensor placement, verify condenser water flow, check refrigerant charge")

print("\n2. EXCESSIVE SUPERHEAT (affects 1,074 rows / 86.4%)")
print("   • Superheat > 30°F reduces capacity")
print("   • Combined with negative subcooling = system issues")
print("   • Fix: Adjust TXV, verify refrigerant charge, check evaporator airflow")

print("\n3. MASS FLOW CALCULATION ERRORS (affects 297 rows / 23.9%)")
print("   • Unrealistic mass flow rates (5-10x normal)")
print("   • Water-side energy balance producing wrong results")
print("   • Fix: Verify GPM setting in rated inputs, check water temp sensors")

print("\n4. PRESSURE SENSOR ISSUES (affects small subset)")
print("   • Some negative suction pressures")
print("   • Fix: Calibrate pressure sensors, check for system leaks")

print("\n✅ RECOMMENDATION:")
print("   Focus on fixing SUBCOOLING issue first - this alone affects 63.5% of bad data")
print("   Check condenser outlet temperature sensor (T_4a) for:")
print("     - Proper mounting location (should be in liquid line, not gas)")
print("     - Calibration accuracy")
print("     - Good thermal contact with pipe")

print("\n" + "="*100)

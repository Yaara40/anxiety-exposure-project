import csv
import sys

def load_data(filename):
    measurements = []
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['baseline_bpm'] and row['stress_bpm']:
                measurements.append({
                    'person': row['person'],
                    'measurement_num': int(row['measurement_num']),
                    'baseline': int(row['baseline_bpm']),
                    'stress': int(row['stress_bpm']),
                    'diff': int(row['diff'])
                })
    return measurements

def analyze(measurements):
    print(f"\nTotal measurements: {len(measurements)}")
    print("-" * 50)

    anxiety_count = 0
    for m in measurements:
        increase_percent = ((m['stress'] - m['baseline']) / m['baseline']) * 100
        is_anxious = increase_percent >= 10  # 10% increase = anxiety

        if is_anxious:
            anxiety_count += 1

        status = "ANXIETY DETECTED" if is_anxious else "no change"
        print(f"{m['person']} | measurement {m['measurement_num']} | "
              f"baseline: {m['baseline']} | stress: {m['stress']} | "
              f"+{increase_percent:.1f}% | {status}")

    print("-" * 50)
    print(f"Anxiety detected in {anxiety_count}/{len(measurements)} measurements "
          f"({(anxiety_count/len(measurements))*100:.0f}%)")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 anxiety_detector.py measurements_XXXX.csv")
        return

    filename = sys.argv[1]
    measurements = load_data(filename)
    analyze(measurements)

if __name__ == "__main__":
    main()

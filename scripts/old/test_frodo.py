import sys
import argparse
from collections import Counter

FRODO640_SPEC = [9288, 8720, 7216, 5264, 3384, 1918, 958, 422, 164, 56, 17, 4, 1]

def main():
    parser = argparse.ArgumentParser(description="Verify the exact distribution of the bitsliced sampler.")
    parser.add_argument("filename", help="Text file containing the serial output integers.")
    args = parser.parse_args()

    try:
        with open(args.filename, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: File '{args.filename}' not found.")
        return

    samples = []
    for line in lines:
        line = line.strip()
        try:
            samples.append(int(line))
        except ValueError:
            pass

    counts = Counter(samples)
    
    print(f"Total parsed samples: {len(samples)}\n")
    
    header = f"{'Sample':>8} | {'Expected':>10} | {'Observed':>10} | {'Diff':>6}"
    print(header)
    print("-" * len(header))

    max_val = len(FRODO640_SPEC) - 1
    all_match = True

    for val in range(-max_val, max_val + 1):
        expected = FRODO640_SPEC[abs(val)]
        observed = counts.get(val, 0)
        diff = observed - expected
        
        if diff != 0:
            all_match = False
            
        print(f"{val:>8} | {expected:>10} | {observed:>10} | {diff:>+6}")

    print("\n" + "-" * len(header))
    if all_match and len(samples) == 65536:
        print("SUCCESS: The observed distribution perfectly matches the Frodo640 specification!")
    else:
        print("FAILURE: The observed distribution does not match the specification.")

if __name__ == "__main__":
    main()

# Circuit generation scripts

The two scripts in this folder generate the C code evaluated by the sampler, and
report the gate counts of Table 2 of the paper.

* **`generate_circuit.py`** builds the Knuth-Yao DDG tree of a distribution,
  turns it into a Boolean circuit with one `SecAnd` per internal node, minimizes
  its linear part with Paar's heuristic, and writes the masked C implementation.
* **`unmask_ky.py`** turns that masked implementation into its unmasked
  counterpart, used for the unmasked benchmarks of Section 6.

Only `python3` is needed, with no external dependency.

## Usage

Both scripts use paths relative to this folder, so run them from here:

```bash
cd scripts
python3 generate_circuit.py    # writes ../code/ky_samplers.{c,h}
python3 unmask_ky.py           # writes ../code/unmasked_ky_samplers.{c,h}
```

`generate_circuit.py` takes a few minutes for the eleven distributions shipped
here, most of it spent on HAETAE, whose support is the largest. It also prints
the gate-count summary described below. `unmask_ky.py` reads the file produced
by `generate_circuit.py`, so run it second, and run it again whenever the
circuits change.

The generated code is deterministic: two runs produce the same files, byte for
byte, independently of the hash seed of the interpreter.

## Adding a distribution

Append an entry to the `parameters` list at the top of `generate_circuit.py`.
The header of the file documents the three fields in detail. In short:

* `name` identifies the generated C symbols, and selects how `spec` is read.
  A name containing `frodo` is read as a half PMF, a name containing `hawk` or
  `falcon` as a reverse CDT, a name containing `haetae` as a forward CDT. For
  any other shape, provide the PMF directly in a `pmf` field.
* `precision` is the number `n` of fractional bits of the distribution. Every
  probability must be an integer multiple of `2^-n`, and the script checks that
  the PMF sums to exactly `2^n`.
* `spec` is the specification table, as published by the scheme.

An optional `sign_bits` field overrides the cost of the sign application, which
is `0` for the half-Gaussian base samplers of Falcon and HAETAE, since their
sign is applied by the caller.

The sampler is cheap when the distribution is narrow and its probability
expansions are sparse, since the number of `SecAnd` gates is the total Hamming
weight of those expansions, minus two.

## Gate counts

The summary table printed by `generate_circuit.py` is the one reported in the
paper. The Knuth-Yao columns count the gates of the circuit that is actually
emitted, tree recombinations included. The CDT columns follow the cost model of
the bitsliced CDT sampler we compare against:

* comparisons: `l * k` `SecAnd` and `3 * l * k` `SecXor`, for a tree of depth
  `l` and a precision of `k` bits;
* pivot: `2^(l-1) - l` `SecAnd`, plus one `SecXor` per set bit of each public
  constant conditioned by a monomial. The reference implementation conditions
  every bit, set or not, so this count favours CDT;
* sign application: `q - 1` `SecAnd` and `5q - 3` `SecXor` on `q` output bits,
  which is the cost of the ripple-carry adder used by both implementations.

The pivot constants are recomputed here from the distribution, by a Moebius
transform over the levels of the CDT tree, so the table can be reproduced
without the CDT code.

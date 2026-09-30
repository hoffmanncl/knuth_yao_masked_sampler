import re

# Read the original masked code
with open("../code/ky_samplers.c", "r") as f:
    code = f.read()

# 1. Rename signatures
code = code.replace("void masked_ky_sampler_", "void unmasked_ky_sampler_")

# 2. Variable declarations: remove [NSHARES] and handle const_0
code = code.replace("[NSHARES]", "")
code = code.replace("uint32_t const_0;", "uint32_t const_0 = 0;")
code = code.replace("trivial_mask(const_0, 0);", "")

# 3. Operations: replace macro-functions with C binary operators
code = re.sub(r'masked_copy_core\(([^,]+),\s*([^)]+)\);', r'\1 = \2;', code)
code = re.sub(r'masked_not_core\(([^,]+),\s*([^)]+)\);', r'\1 = ~(\2);', code)
code = re.sub(r'masked_and_core\(([^,]+),\s*([^,]+),\s*([^)]+)\);', r'\1 = (\2) & (\3);', code)
code = re.sub(r'masked_xor_core\(([^,]+),\s*([^,]+),\s*([^)]+)\);', r'\1 = (\2) ^ (\3);', code)

# 4. Array indexing: rs + i * NSHARES -> rs[i]
code = re.sub(r'rs \+ (\d+) \* NSHARES', r'rs[\1]', code)
code = re.sub(r'output \+ (\d+) \* NSHARES', r'output[\1]', code)

# Write C file
with open("../code/unmasked_ky_samplers.c", "w") as f:
    f.write('#include "unmasked_ky_samplers.h"\n\n')
    f.write(code)

# Write Header file
with open("../code/unmasked_ky_samplers.h", "w") as f:
    f.write("#ifndef UNMASKED_KY_SAMPLERS_H\n#define UNMASKED_KY_SAMPLERS_H\n\n")
    f.write("#include <stdint.h>\n\n")
    # Extract all function signatures
    funcs = re.findall(r'void unmasked_ky_sampler_[a-zA-Z0-9_]+\(uint32_t \*output, uint32_t \*rs\)', code)
    for func in funcs:
        f.write(func + ";\n")
    f.write("\n#endif // UNMASKED_KY_SAMPLERS_H\n")

print("Unmasked files successfully generated!")

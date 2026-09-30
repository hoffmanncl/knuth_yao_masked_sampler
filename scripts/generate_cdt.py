parameters = [
    {
        "name": "frodo640",
        "precision": 15,
        "spec": [9288, 8720, 7216, 5264, 3384, 1918, 958, 422, 164, 56, 17, 4, 1]
    },
    {
        "name": "frodo976",
        "precision": 15,
        "spec": [11278, 10277, 7774, 4882, 2545, 1101, 396, 118, 29, 6, 1]
    },
    {
        "name": "frodo1344",
        "precision": 15,
        "spec": [18286, 14320, 6876, 2023, 364, 40, 2]
    },
    {
        "name": "hawk256_T0",
        "precision": 78,
        "spec": [
            0x26B871FBD58485D45050, 0x07C054114F1DC2FA7AC9, 0x00A242F74ADDA0B5AE61,
            0x0005252E2152AB5D758B, 0x00000FDE62196C1718FC, 0x000000127325DDF8CEBA,
            0x0000000008100822C548, 0x00000000000152A6E9AE, 0x0000000000000014DA4A,
            0x0000000000000000007B
        ]
    },
    {
        "name": "hawk256_T1",
        "precision": 78,
        "spec": [
            0x13459408A4B181C718B1, 0x027D614569CC54722DC9, 0x0020951C5CDCBAFF49A3,
            0x0000A3460C30AC398322, 0x000001355A8330C44097, 0x00000000DC8DE401FD12,
            0x00000000003B0FFB28F0, 0x00000000000005EFCD99, 0x00000000000000003953,
            0x00000000000000000000
        ]
    },
    {
        "name": "hawk512_T0",
        "precision": 78,
        "spec": [
            0x2C058C27920A04F8F267, 0x0E9A1C4FF17C204AA058, 0x02DBDE63263BE0098FFD,
            0x005156AEDFB0876A3BD8, 0x0005061E21D588CC61CC, 0x00002BA568D92EEC18E7,
            0x000000CF0F8687D3B009, 0x0000000216A0C344EB45, 0x0000000002EDF0B98A84,
            0x0000000000023AF3B2E7, 0x00000000000000EBCC6A, 0x000000000000000034CF,
            0x00000000000000000006
        ]
    },
    {
        "name": "hawk512_T1",
        "precision": 78,
        "spec": [
            0x1AFCBC689D9213449DC9, 0x06EBFB908C81FCE3524F, 0x01064EBEFD8FF4F07378,
            0x0015C628BC6B23887196, 0x0000FF769211F07B326F, 0x00000668F461693DFF8F,
            0x0000001670DB65964485, 0x000000002AB6E11C2552, 0x00000000002C253C7E81,
            0x00000000000018C14ABF, 0x0000000000000007876E, 0x0000000000000000013D,
            0x00000000000000000000
        ]
    },
    {
        "name": "hawk1024_T0",
        "precision": 78,
        "spec": [
            0x2C583AAA2EB76504E560, 0x0F1D70E1C03E49BB683E, 0x031955CDA662EF2D1C48,
            0x005E31E874B355421BB7, 0x000657C0676C029895A7, 0x00003D4D67696E51F820,
            0x0000014A1A8A93F20738, 0x00000003DAF47E8DFB21, 0x0000000006634617B3FF,
            0x000000000005DBEFB646, 0x00000000000002F93038, 0x0000000000000000D5A7,
            0x00000000000000000021
        ]
    },
    {
        "name": "hawk1024_T1",
        "precision": 78,
        "spec": [
            0x1B7F01AE2B17728DF2DE, 0x07506A00B82C69624C93, 0x01252685DB30348656A4,
            0x001A430192770E205503, 0x00015353BD4091AA96DB, 0x000009915A53D8667BEE,
            0x00000026670030160D5F, 0x00000000557CD1C5F797, 0x00000000006965E15B13,
            0x00000000000047E9AB38, 0x000000000000001B2445, 0x000000000000000005AA,
            0x00000000000000000000
        ]
    }
]

with open("../code/scalar_cdt_tables.h", "w") as f:
    f.write("#ifndef SCALAR_CDT_TABLES_H\n#define SCALAR_CDT_TABLES_H\n\n")
    f.write("#include <stdint.h>\n\n")

    for p in parameters:
        name = p["name"].strip().upper()
        spec = p["spec"]
        
        if "FRODO" in name:
            # Transform PMF to CDF for Frodo
            cdf = []
            current = spec[0] // 2
            cdf.append(current)
            for val in spec[1:]:
                current += val
                cdf.append(current)
            
            f.write(f"static const size_t {name}_CDT_SIZE = {len(cdf)};\n")
            f.write(f"static const uint16_t {name}_CDT_TABLE[] = {{\n    ")
            f.write(", ".join(map(str, cdf)))
            f.write("\n};\n\n")

        elif "HAWK" in name:
            # Keep RCDT for Hawk, split into 3x32-bit limbs (Little Endian)
            f.write(f"static const size_t {name}_CDT_SIZE = {len(spec)};\n")
            f.write(f"static const uint32_t {name}_CDT_TABLE[{len(spec)}][3] = {{\n")
            for val in spec:
                lo = val & 0xFFFFFFFF
                mid = (val >> 32) & 0xFFFFFFFF
                hi = (val >> 64) & 0xFFFFFFFF
                f.write(f"    {{0x{lo:08X}, 0x{mid:08X}, 0x{hi:08X}}},\n")
            f.write("};\n\n")
            
    f.write("#endif // SCALAR_CDT_TABLES_H\n")

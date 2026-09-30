from argparse import ArgumentParser
from dataclasses import dataclass

CODEDIR = "../"
HEXDIR = CODEDIR + "hex/"
FILE = "stm.hex"

import time
from collections import defaultdict
import subprocess

cw_lib_present = False
try:
    import chipwhisperer as cw
    scope = cw.scope()
    target = cw.target(scope, cw.targets.SimpleSerial)
    prog = cw.programmers.STM32FProgrammer
    time.sleep(0.05)
    scope.default_setup()
    cw_lib_present = True
except:
    print("Chipwhisperer library not detected: cannot run automatic tests.")
    print("It is necessary for communication with the target.")
    exit(1)



FRODO_param_set = {1344, 976, 640}
@dataclass
class MakeParams:
    platform : str = "STM32F4"   # 'QEMU', 'STM32F3' or 'STM32F4'
    bench    : str = "BENCH_CYC" # 'BENCH_RND' or 'BENCH_CYC'
    mode     : str = "bench"     # 'bench' or 'test' or 'bench_cdt_unmasked' or 'bench_ky_unmasked'
    nshares  : int = 2
    param    : str = "FRODO_1344"
    nb_samp  : int = 42

default_build = MakeParams()

paramsets = [
                "FRODO_1344", "FRODO_976", "FRODO_640",
                "HAWK_512_T0", "HAWK_512_T1",
                "HAWK_1024_T0", "HAWK_1024_T1",
                "HAWK_256_T0", "HAWK_256_T1",
                "HAETAE", "FALCON",
            ]

paramname = { "FRODO_1344"  : "F1344",  "FRODO_976"   : "F976", "FRODO_640" : "F640",
              "HAWK_512_T0" : "H512.0", "HAWK_512_T1" : "H512.1",
              "HAWK_1024_T0": "H1024.0","HAWK_1024_T1": "H1024.1",
             "HAWK_256_T0"  : "H256.0", "HAWK_256_T1" : "H256.1",
             "HAETAE" : "HAETAE", "FALCON" : "FALCON",
             }

modename  = { "bench_cdt_unmasked" : "UnCDT", "bench_ky_unmasked" : "UnKY", "bench" : "KY", "test" : "T"}
makename = lambda param, mode : paramname[param] + "/" + modename[mode]
modes = [ "bench", "bench_cdt_unmasked", "bench_ky_unmasked"]
unmasked_modes = ["bench_cdt_unmasked", "bench_ky_unmasked"]
non_cdt = ["HAETAE", "FALCON"] # exclude from unmasked_cdt benches
non_ky  = ["HAETAE", "FALCON",
            "HAWK_512_T0", "HAWK_512_T1",
            "HAWK_1024_T0", "HAWK_1024_T1",
            "HAWK_256_T0", "HAWK_256_T1",
] # exclude from unmasked_ky benches
#modes = [ "bench_cdt_unmasked", "bench_ky_unmasked"]

def make(make_param : MakeParams = default_build):
    return subprocess.run(["make",
                           "-C" ,f"{CODEDIR}",
                           f'PLATFORM={make_param.platform}',
                           f'NSHARES={make_param.nshares}',
                           f'BENCH={make_param.bench}',
                           f'MODE={make_param.mode}',
                           f'PARAM={make_param.param}',
                           f'NUM_BATCHES={make_param.nb_samp}',])
def make_clean():
    return subprocess.run(["make", "-C", f"{CODEDIR}", "clean"])

def program_cw_target():
    path = HEXDIR + FILE
    cw.program_target(scope, prog, path)

def poll_target_until(endmsg):
    read_data = ""
    while not(read_data.__contains__(endmsg)): # why not
        read_now = target.read(timeout=100)
        # if read_now.strip() != "": print(read_now)
        read_data += read_now
    return read_data

def full_chain(make_param = default_build):
    make(make_param)
    bench_str = ""
    if make_param.platform != "QEMU" and cw_lib_present:
        program_cw_target()
        bench_str = poll_target_until('EOF')
    else:
        subprocess.run(["make", "-C", f"{CODEDIR}", "run-qemu"])

    print(repr(bench_str))
    bench_raw = bench_str.split('\n')
    res_dic = {}
    for bench in bench_raw:
        var = bench.split(',')
        if (len(var) > 1):
            cost = int(var[-1]) / make_param.nb_samp / 32 # 32 samples computed per call
            # print(f"{var[1]}: {cost:.2f}")
            res_dic[var[1]] = cost
    return res_dic

def auto_bench(nshares_start = 1, nshares_finish = 4, paramset = "FRODO_1344", mode = "bench"):
    results_cycles = defaultdict(list)
    results_rnd = defaultdict(list)
    assert(paramset in paramsets)

    make_clean()
    nshare_range = range(nshares_start, nshares_finish + 1)
    if mode in unmasked_modes:
        nshare_range = range(1, 2)

    for i in nshare_range:
        make_param_cyc = MakeParams(nshares=i, param=paramset, mode=mode)
        make_param_rnd = MakeParams(nshares=i, bench="BENCH_RND", param=paramset, mode=mode)
        res_cyc = full_chain(make_param_cyc)
        make_clean()
        res_rnd = full_chain(make_param_rnd)
        make_clean()
        for k in res_cyc.keys():
            results_cycles[k] += [res_cyc[k]]
        for k in res_rnd.keys():
            results_rnd[k] += [res_rnd[k]]
    return (results_cycles, results_rnd)

def table_print(res, title = "", fd = None):
    ex = res['sampler']
    nshare_max = len(ex)
    sep_  = "-"
    endl = '\n'
    for key in [None] + list(res.keys()):
        ln = ""
        if key == None:
            ln = "|".join([f"{str(title)[:20]:20}"] + [f"{1 + i:20}" for i in range(nshare_max)])
        else:
            ln = "|".join([f"{key:20}"] + [f"{x:20}" for x in list(res[key])])
        if fd == None:
            print(ln)
            print(sep_ * 20 * (nshare_max + 1))
        else:
            fd.write(ln                           + endl)
            fd.write(sep_ * 20 * (nshare_max + 1) + endl)
    if fd != None:
        fd.flush()

def run_bench(n):
    fd = open(f"bench-results-1shares-to-{n}shares.txt", 'w')
    for mode in modes:
        for param in paramsets:
            if mode == "bench_cdt_unmasked" and param in non_cdt:
                continue
            if mode == "bench_ky_unmasked" and param in non_ky:
                continue
            cyc, rnd = auto_bench(nshares_start=1, nshares_finish=n, paramset=param, mode=mode)
            table_print(cyc, f"Cyc/{makename(param, mode)}", fd)
            table_print(rnd, f"Rng/{makename(param, mode)}", fd)
    fd.close()


def reset():
    scope.target_pwr = False
    time.sleep(1)
    scope.target_pwr = True

def disconnect():
    scope.dis()
    target.dis()

if __name__ == """__main__""":
    run_bench(6)

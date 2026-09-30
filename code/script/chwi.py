import subprocess
from typing import List

from tqdm import tqdm
import chipwhisperer as cw
import time
import matplotlib.pyplot as plt
import numpy as np

scope = cw.scope()
target = cw.target(scope, cw.targets.SimpleSerial)
prog = cw.programmers.STM32FProgrammer

CODEDIR = "../"
HEXDIR = "../hex/"
FILE = "stm.hex"

time.sleep(0.05)
scope.default_setup()

def build(*args):
    subprocess.run(["make", "-C", CODEDIR, *args])

def program():
    path = HEXDIR + FILE
    cw.program_target(scope, prog, path)

def reset():
    scope.target_pwr = False
    time.sleep(1)
    scope.target_pwr = True 

def disconnect():
    scope.dis()
    target.dis()

def poll_target_until(endmsg, debug=False):
    read_data = ""
    while not(read_data.__contains__(endmsg)): # why not
        read_now = target.read(timeout=100)
        if (read_now.strip() != "") and debug: print(read_now)
        read_data += read_now
        
    return read_data
def synchronized_read(endmsg, debug=False):
    data = ""
    while not data.__contains__(endmsg):
        target.write('p')
        read_now = target.read(timeout=100)
        if (read_now.strip() != "") and debug: print(read_now)
        data += read_now
    return data


def program_and_syncread():
    program()
    return synchronized_read("EOF")

def program_and_poll_eof():
    program()
    return poll_target_until("EOF")


def get_trace(mode="fixed"):
    scope.arm()
    if mode == "fixed":
        target.write('f')
    elif mode == "random":
        target.write('r')
    ret = scope.capture()
    if ret:
        print("Capture timed out...")
        return None
    return scope.get_last_trace(as_int=True)

def get_tvla_traces_extended(filename, nb_traces):
    """ prototype to get very large traces """
    try:
        project = cw.open_project(filename)
    except OSError:
        project = cw.create_project(filename)

    # automatically calibrate the number of traces needed, perform a dummy run
    print("Performing a dummy run to calibrate nb of needed samples...")
    _ = get_trace(mode='fixed')
    cycles_high = scope.adc.trig_count
    _ = get_trace(mode='random')
    cycles_high_ = scope.adc.trig_count

    print(f" First run: {cycles_high} cycles high")
    print(f"Second run: {cycles_high} cycles high")
    samples = min(max(cycles_high, cycles_high_))
    print(f" Setting adc.samples to {samples} samples")
    scope.adc.samples = min(samples, 96000)

    print(f"Starting collection of {2 * nb_traces} traces")
    for i in tqdm(range(2 * nb_traces)):
        if (i % 2) == 0:
            wave = get_trace(mode='fixed')
        else:
            wave = get_trace(mode='random')
        trace = cw.Trace(wave, textin=i, textout=i%2, key=16773)
        project.traces.append(trace)
    project.save()
    return project


def get_tvla_traces(filename, nb_traces):
    """ Measure power traces using the chipwhisperer and saves them into a project """
    try:
        project = cw.open_project(filename)
    except OSError:
        project = cw.create_project(filename)

    scope.clock.adc_src = "clkgen_x1"
    print(f"Set scope.clock.adc_src to {scope.clock.adc_src}")
    # automatically calibrate the number of traces needed, perform a dummy run
    print("Performing a dummy run to calibrate nb of needed samples...")
    _ = get_trace(mode='fixed')
    cycles_high = scope.adc.trig_count
    _ = get_trace(mode='random')
    cycles_high_ = scope.adc.trig_count

    print(f" First run: {cycles_high} cycles high")
    print(f"Second run: {cycles_high_} cycles high")
    assert(cycles_high_ == cycles_high) # if not, we have a bigger problem
    samples = min(max(cycles_high, cycles_high_), 96000) # 96000 is the max sample size of CW120
    print(f" Setting adc.samples to {samples} samples")
    scope.adc.samples = samples


    print(f"Starting collection of {2 * nb_traces} traces")
    for i in tqdm(range(2 * nb_traces)):
        if (i % 2) == 0:
            wave = get_trace(mode='fixed')
        else:
            wave = get_trace(mode='random')
        trace = cw.Trace(wave, textin=i, textout=i%2, key=16773)
        project.traces.append(trace)
    project.save()
    return project

def trace_iterator(traces : cw.project.Traces, block_size=1000):
    """ Iterate (and yield) through waves of traces by block """
    i = 0
    while i * block_size < len(traces):
        tr_array = traces[i * block_size: (i + 1) * block_size]
        wave_array = np.array([tr.wave for tr in tr_array]) 
        yield wave_array
        i += 1

def tvla_threshold(confidence_level, nb_trace, nb_datapoint):
    """ Compute tvla threshold according to eprint.iacr.org/2017/287.pdf methodology """
    from scipy.stats import t
    alpha = 1 - (1 - confidence_level) ** (1/ float(nb_datapoint))
    return t.ppf(1 - alpha / 2, nb_trace)

def run_tvla(pr : cw.project.Project, order=1, debug=False, block_size=10000):
    """
    Run scalib tvla on traces of a cw project.

    This function assumes that traces are already well interleaved
    inside the project. That is, if pr.traces is the array traces
    of traces, pr.traces[::2] are samples of a class A, while 
    pr.traces[1::2] are samples of class B. (this seems to be a
    standard requirement for ttests as per the litterature).
    If debug=True, traces are randomly generated instead of 
    loaded from project.
    """
    import scalib.metrics as sc
    
    trace_min_size = 10000000
    processed_fixed_nb = 0
    processed_random_nb = 0
    ttest = sc.Ttest(d = order)
    if not debug:
        traces = pr.traces
    else:
        # generate dummy traces with the same format as pr.traces for iterator function compatibility
        traces = [cw.Trace(w, 0, 0, 0) for w in np.random.randint(0, 256, (2000, 2000), dtype=np.int16)]
    for wave_array in trace_iterator(traces, block_size=block_size):
        # some traces are np.float64 (we assume they are in [-0.5., 0.5.])
        if wave_array.dtype == np.float64:
            fixed_tr = np.round(wave_array[::2] * 32767).astype(np.int16)
            random_tr = np.round(wave_array[1::2] * 32767).astype(np.int16)
        else:
            fixed_tr = wave_array[::2].astype(np.int16)
            random_tr = wave_array[1::2].astype(np.int16)
        trace_min_size = min(trace_min_size, fixed_tr.shape[0])
        trace_min_size = min(trace_min_size, random_tr.shape[0])
        fixed_tr_labels = np.zeros(shape=(fixed_tr.shape[0],), dtype=np.uint16)
        random_tr_labels = np.ones(shape=(random_tr.shape[0],), dtype=np.uint16)
        
        ttest.fit_u(fixed_tr, fixed_tr_labels)
        ttest.fit_u(random_tr, random_tr_labels)
        processed_fixed_nb  += len(fixed_tr_labels)
        processed_random_nb += len(random_tr_labels)
    

    t = ttest.get_ttest()
    
    print(f"[RESULT] TVLA for:")
    print(f"\t{processed_fixed_nb} traces in fixed set")
    print(f"\t{processed_random_nb} traces in random set")
    print(f"\tMax value: |{max(t.max(), abs(t.min()))}|")
    print(f"\tThreshold values:")
    alpha_values = [0.01, 0.001, 0.00001]
    spc_fill = max(map(lambda x: len(str(x)), alpha_values)) # formatting nicely
    for alpha in alpha_values:
        print(f"\t\t{alpha: >{spc_fill}}: {tvla_threshold(alpha, min(processed_fixed_nb,processed_random_nb), trace_min_size)}")

    
    plt.plot(t[0])
    plt.show()
    return t

def run_tvla_projects(projects : List[cw.project.Project], order=1, debug=False, block_size=10000):
    """
    Run scalib tvla on traces of a collection of cw project.

    This function assumes that traces are already well interleaved
    inside the projects. That is, if pr.traces is the array traces
    of traces of project pr, pr.traces[::2] are samples of a class A, while 
    pr.traces[1::2] are samples of class B. (this seems to be a
    standard requirement for ttests as per the litterature).
    If debug=True, traces are randomly generated instead of 
    loaded from project.
    """
    import scalib.metrics as sc
    
    trace_min_size = 10000000
    processed_fixed_nb = 0
    processed_random_nb = 0
    ttest = sc.Ttest(d = order)
    for pr in projects:
        if not debug:
            traces = pr.traces
        else:
            # generate dummy traces with the same format as pr.traces for iterator function compatibility
            traces = [cw.Trace(w, 0, 0, 0) for w in np.random.randint(0, 256, (2000, 2000), dtype=np.int16)]
        for wave_array in trace_iterator(traces, block_size=block_size):
            # some traces are np.float64 (we assume they are in [-0.5., 0.5.])
            if wave_array.dtype == np.float64:
                fixed_tr = np.round(wave_array[::2] * 32767).astype(np.int16)
                random_tr = np.round(wave_array[1::2] * 32767).astype(np.int16)
            else:
                fixed_tr = wave_array[::2].astype(np.int16)
                random_tr = wave_array[1::2].astype(np.int16)
            trace_min_size = min(trace_min_size, fixed_tr.shape[0])
            trace_min_size = min(trace_min_size, random_tr.shape[0])
            fixed_tr_labels = np.zeros(shape=(fixed_tr.shape[0],), dtype=np.uint16)
            random_tr_labels = np.ones(shape=(random_tr.shape[0],), dtype=np.uint16)
            
            ttest.fit_u(fixed_tr, fixed_tr_labels)
            ttest.fit_u(random_tr, random_tr_labels)
            processed_fixed_nb  += len(fixed_tr_labels)
            processed_random_nb += len(random_tr_labels)
    

    t = ttest.get_ttest()
    
    print(f"[RESULT] TVLA for:")
    print(f"\t{processed_fixed_nb} traces in fixed set")
    print(f"\t{processed_random_nb} traces in random set")
    print(f"\tMax value: |{max(t.max(), abs(t.min()))}|")
    print(f"\tThreshold values:")
    alpha_values = [0.01, 0.001, 0.00001]
    spc_fill = max(map(lambda x: len(str(x)), alpha_values)) # formatting nicely
    for alpha in alpha_values:
        print(f"\t\t{alpha: >{spc_fill}}: {tvla_threshold(alpha, min(processed_fixed_nb,processed_random_nb), trace_min_size)}")

    
    plt.plot(t[0])
    plt.show()
    return t

def plot_trace(tr):
    plt.plot(tr)
    plt.show(tr)
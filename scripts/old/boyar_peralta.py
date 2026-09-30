from itertools import combinations
import numpy as np

uint_t = np.int8

def norm1(x): # assert positive elements
    return sum(x)

def norm2(x):
    return sum(map(lambda y: y * y, x))

def base_vector(i, n):
    return np.array([0 if j != i else 1 for j in range(n)], dtype=uint_t)

#set of np.array
def set_iterator(s):
    for raw_array in s:
        yield np.frombuffer(raw_array, dtype=uint_t)

def add_to_set(s : set, array : np.ndarray):
    s.add(array.tobytes())

def add_to_dict(d : dict, array : np.ndarray, value):
    d[array.tobytes()] = value

def get_value(d : dict, array : np.ndarray):
    return d[array.tobytes()]

def is_in_set(s : set, array : np.ndarray):
    return array.tobytes() in s

def is_in_dict(d : dict, array : np.ndarray):
    return array.tobytes() in d

def recompute_distance_vector(S_vectors, new_vector, Dist, equation_matrix):
    # print("call to recompute dist")
    max_subset_size = max(Dist) + 1
    # space = list(range(1, max_diff +1 )) + list(range(max(Dist) - max_diff, max(Dist) + 1))
    Dist_ = Dist.copy()
    for i in range(max_subset_size):
        if i > max(Dist_):
            break

        for tuples in combinations(S_vectors, max_subset_size - i):
            tuple_sum = np.bitwise_xor.reduce(tuples + (new_vector,))
            for j in range(len(equation_matrix)):
                equation = equation_matrix[j]
                is_equal = np.array_equal(equation, tuple_sum)
                if is_equal and i < Dist_[j]:
                    Dist_[j] = max_subset_size - i
    return Dist_

def boyar_peralta(equation_matrix):
    n = len(equation_matrix[0])
    S = set()
    S_vectors = []
    operations = dict()

    for i in range(n):
        v = base_vector(i, n)
        add_to_set(S, v)
        S_vectors.append(v)
        add_to_dict(operations, v, (i, None ,None))
    Dist = np.array([np.sum(equation) - 1 for equation in equation_matrix]) # [HW(M_i) - 1]

    max_id = n


    while np.sum(Dist) != 0:
        print("Dist: ", Dist)
        early_abort = False
        candidates = combinations(S_vectors, 2)
        pair_scores = []
        actual_min = np.sum(Dist)
        for a, b in candidates:
            new_sum = a ^ b
            id_a, _, _ = get_value(operations, a)
            id_b, _, _ = get_value(operations, b)
            if any(np.array_equal(row, new_sum) for row in equation_matrix) and not is_in_set(S, new_sum):
                print("early abort", new_sum)
                add_to_set(S, new_sum)
                S_vectors.append(new_sum)
                Dist = recompute_distance_vector(S_vectors, new_sum, Dist, equation_matrix)
                add_to_dict(operations, new_sum, (max_id, id_a, id_b))
                max_id += 1
                
                early_abort = True
                break
            Dist_ = recompute_distance_vector(S_vectors, new_sum, Dist, equation_matrix)
            score = np.sum(Dist_)
            if score < actual_min:
                actual_min = score
                pair_scores.clear()
                pair_scores.append((new_sum, Dist_, id_a, id_b))
            elif score == actual_min:
                pair_scores.append((new_sum, Dist_, id_a, id_b))
        
        if not early_abort:
            final_candidate = None
            max_norm = 0
            for (new_sum, Dist_, id_a, id_b) in pair_scores:
                l2_norm = np.sum(Dist_ * Dist_)
                if l2_norm > max_norm:
                    max_norm = l2_norm
                    final_candidate = (new_sum, Dist_, id_a, id_b)
                print("l2_norm ",l2_norm)
                print("sumdist ",np.sum(Dist_))
            
            if final_candidate == None:
                print("[Error] No final candidate found (empty pair_scores) breaking...")
                break
            new_sum, Dist_, id_a, id_b = final_candidate
            add_to_set(S, new_sum)
            S_vectors.append(new_sum)
            print("added ", new_sum)
            Dist = Dist_
            add_to_dict(operations, new_sum, (max_id, id_a, id_b))
            max_id += 1
    return S, operations


def print_set(S):
    for x in set_iterator(S):
        print(x)
            

M = np.array([[1,1,1,0,0], [0,1,0,1,1], [1,0,1,1,1], [0,1,1,1,0], [1,1,0,1,0], [0,1,1,1,1]])




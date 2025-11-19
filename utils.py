import pickle
import numpy as np

def multiply_block(A_block, B):
    return np.dot(A_block, B)

def serialize_data(data):
    return pickle.dumps(data)

def deserialize_data(data):
    return pickle.loads(data)
import math
import cmath

pi = math.pi
complex128 = complex

class ndarray:
    def __init__(self, data):
        if hasattr(data, 'tolist'):
            self.data = data.tolist()
        elif isinstance(data, ndarray):
            self.data = list(data.data)
        else:
            self.data = list(data)

    def tolist(self):
        return self.data

    def __repr__(self):
        return f"array({self.data})"

    def __len__(self):
        return len(self.data)

    def __pow__(self, other):
        return ndarray([x ** other for x in self.data])

    def __getitem__(self, idx):
        if isinstance(idx, tuple):
            row, col = idx
            return self.data[row][col]
        item = self.data[idx]
        if isinstance(item, list):
            return ndarray(item)
        return item

    def __setitem__(self, idx, val):
        if isinstance(idx, tuple):
            row, col = idx
            self.data[row][col] = val
        else:
            if isinstance(val, ndarray):
                self.data[idx] = val.data
            else:
                self.data[idx] = val

    def __mul__(self, other):
        if isinstance(other, ndarray):
            if isinstance(self.data[0], list):
                return ndarray([[a * b for a, b in zip(row, other.data)] for row in self.data])
            return ndarray([a * b for a, b in zip(self.data, other.data)])
        if isinstance(self.data[0], list):
            return ndarray([[x * other for x in row] for row in self.data])
        return ndarray([x * other for x in self.data])

    def __rmul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other):
        if isinstance(other, ndarray):
            if len(other.data) == len(self.data):
                res = []
                for a, b in zip(self.data, other.data):
                    if isinstance(a, list) and isinstance(b, list):
                        res.append([x / y for x, y in zip(a, b)])
                    elif isinstance(a, list):
                        divisor = b[0] if isinstance(b, list) else b
                        res.append([x / divisor for x in a])
                    else:
                        res.append(a / b)
                return ndarray(res)
        return ndarray([x / other for x in self.data])

    def __sub__(self, other):
        if isinstance(other, ndarray):
            return ndarray([a - b for a, b in zip(self.data, other.data)])
        return ndarray([x - other for x in self.data])

    def __rsub__(self, other):
        if isinstance(other, ndarray):
            return ndarray([b - a for a, b in zip(self.data, other.data)])
        return ndarray([other - x for x in self.data])

    def __add__(self, other):
        if isinstance(other, ndarray):
            return ndarray([a + b for a, b in zip(self.data, other.data)])
        return ndarray([x + other for x in self.data])

    def __radd__(self, other):
        return self.__add__(other)

def array(data, dtype=None):
    return ndarray(data)

def ones(dim, dtype=None):
    return ndarray([1.0] * dim)

def eye(dim, dtype=None):
    matrix = []
    for i in range(dim):
        row = [0.0] * dim
        row[i] = 1.0
        matrix.append(row)
    return ndarray(matrix)

class linalg:
    @staticmethod
    def norm(arr, axis=None, keepdims=False):
        b_sum = __builtins__['sum'] if isinstance(__builtins__, dict) else getattr(__builtins__, 'sum')
        if axis == 1:
            res = []
            for vec in arr.data:
                squared = b_sum(abs(x)**2 for x in vec)
                val = math.sqrt(squared)
                if keepdims:
                    res.append([val])
                else:
                    res.append(val)
            return ndarray(res)
        elif axis is None:
            squared = b_sum(abs(x)**2 for x in arr.data)
            return math.sqrt(squared)
        return 0.0

def exp(x):
    if isinstance(x, ndarray):
        return ndarray([cmath.exp(item) for item in x.data])
    return cmath.exp(x)

def abs(x):
    if isinstance(x, ndarray):
        return ndarray([builtins_abs(item) for item in x.data])
    return builtins_abs(x)

builtins_abs = __builtins__['abs'] if isinstance(__builtins__, dict) else getattr(__builtins__, 'abs')
builtins_sum = __builtins__['sum'] if isinstance(__builtins__, dict) else getattr(__builtins__, 'sum')

def where(condition, x, y):
    res = []
    for idx, cond in enumerate(condition.data):
        val_x = x.data[idx] if isinstance(x, ndarray) else x
        val_y = y.data[idx] if isinstance(y, ndarray) else y
        res.append(val_x if cond else val_y)
    return ndarray(res)

def sum(x):
    if isinstance(x, ndarray):
        return ndarray_sum(x.data)
    return x

def ndarray_sum(lst):
    s = 0.0
    for item in lst:
        if isinstance(item, list):
            s += ndarray_sum(item)
        else:
            s += item
    return s

def log2(x):
    if isinstance(x, ndarray):
        return ndarray([math.log2(item) if item > 0 else -100 for item in x.data])
    return math.log2(x) if x > 0 else -100

def mean(x):
    if isinstance(x, ndarray):
        return ndarray_sum(x.data) / len(x.data)
    return x

def dot(matrix, vector):
    res = []
    for row in matrix.data:
        val = sum_zip(row, vector.data)
        res.append(val)
    return ndarray(res)

def sum_zip(row, vector_list):
    return builtins_sum(a * b for a, b in zip(row, vector_list))

def argmax(x):
    if isinstance(x, ndarray):
        items = x.data
        max_val = max(items)
        return items.index(max_val)
    return 0

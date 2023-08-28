import time
import maya.api.OpenMaya as om

def timer_decorator(func):
    '''
    Wrapper function so that we can time a function by adding this as a decorator
    '''
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time() - start
        om.MGlobal.displayInfo(f"{func.__qualname__} took {end*1000:.3f} ms to compute")
        return result
    return wrapper


class ScopedTimer:

    def __init__(self, print_str: str = None):
        self.start = time.time()
        if print_str:
            self.print_str = print_str
        else:
            self.print_str = ""

    def __del__(self):
        end = time.time() - self.start
        om.MGlobal.displayInfo(f"{self.print_str} took {end*1000:.3f} ms to compute")


class Timer:

    def __init__(self, print_str: str = None):
        self.start = time.time()
        if print_str:
            self.print_str = print_str
        else:
            self.print_str = ""

    def stop(self):
        end = time.time() - self.start
        om.MGlobal.displayInfo(f"{self.print_str} took {end*1000:.3f} ms to compute")
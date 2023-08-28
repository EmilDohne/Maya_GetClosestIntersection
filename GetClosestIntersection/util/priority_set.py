import heapq


class PrioritySet(object):
    '''
    Priority queue like heap object with a set to make sure indices are unique, adapted from here:
    https://stackoverflow.com/a/5997409
    '''
    def __init__(self):
        self.heap = []
        self.values = set()

    def add(self, d, pri):
        if not d in self.values:
            heapq.heappush(self.heap, (pri, d))
            self.values.add(d)

    def pop(self):
        pri, d = heapq.heappop(self.heap)
        self.values.remove(d)
        return d
    
    def __len__(self) -> int:
        return len(self.heap)
    
    def __str__(self) -> str:
        return str(self.values)
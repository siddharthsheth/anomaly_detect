from greedypermutation import Point

class TimeSeriesPoint():
    def __init__(self, series):
        self.points = tuple(series)
    
    def dist(self, other):
        w = len(self.points)
        return sum(self.points[i].dist(other.points[i]) for i in range(w))
    
    def __str__(self):
        return ', '.join([str(self.points[i]) for i in range(len(self.points))])
    
    def __eq__(self, other):
        return True if all(self.points[i] == other.points[i] for i in range(len(self.points))) else False
    
    def __hash__(self) -> int:
        return hash(self.points)
    
    def slide_window(self, new_point):
        self.points = tuple([Point(p) for p in self.points[1:]] + [Point(new_point)])
        # self.points = tuple(*self.points[1:], Point(new_point))
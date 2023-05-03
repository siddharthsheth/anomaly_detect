from greedypermutation import Point

class TimeSeriesPoint():
    """
    This class represents a consecutive sequence of measurements from a time-series database as a single point.
    Each measurement is stored as a `greedypermutation.Point` object.
    """
    def __init__(self, series):
        """
        Create a new TimeSeriesPoint object.
        The input `series` is a sequence of measurements (a list of tuples) where the first measurement is the oldest.
        """
        self.points = tuple(series)
    
    def dist(self, other):
        """
        The distance between two TimeSeriesPoints is the sum of the distances between corresponding measurements in the two points.
        """
        w = len(self.points)
        return sum(self.points[i].dist(other.points[i]) for i in range(w))
    
    def __str__(self):
        return ', '.join([str(self.points[i]) for i in range(len(self.points))])
    
    def __eq__(self, other):
        return True if all(self.points[i] == other.points[i] for i in range(len(self.points))) else False
    
    def __hash__(self) -> int:
        return hash(self.points)
    
    def slide_window(self, new_measure):
        """
        Update a TimeSeriesPoint by a unit of time.
        The oldest measurement in the point is discarded and `new_measure` is appended as the newest measurement.
        """
        self.points = tuple([Point(p) for p in self.points[1:]] + [Point(new_measure)])
        # self.points = tuple(*self.points[1:], Point(new_point))
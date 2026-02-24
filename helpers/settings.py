from enum import Enum

class MapQuality(Enum):
    LAAG = 1
    MIDDEL = 3
    HOOG = 5
    MAXIMAAL = 15

class ForecastMode(Enum):
    EIGEN = 0
    KNMI = 1

class MapSize(Enum):
    KLEIN = 0
    GROOT = 1

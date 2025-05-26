"""
Utility functions for True Vision application
"""

def conf(con):
    """
    Applies a confidence enhancement algorithm that scales the confidence value
    based on a non-linear formula to better express the actual certainty level.
    """
    con *= (100-con) * 0.006 + 1
    return con

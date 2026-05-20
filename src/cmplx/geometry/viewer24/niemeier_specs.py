"""
Viewer24 slot-09 (2026-05-19T01:17:22Z).
Source: Downloads/Viewer24_Controller_v2_CA_Residue.zip
"""

from typing import List
Matrix = List[List[float]]
def cartan_A(n: int) -> Matrix:
    A = [[0]*n for _ in range(n)]
    for i in range(n):
        A[i][i] = 2
        if i>0: A[i][i-1] = -1
        if i<n-1: A[i][i+1] = -1
    return [list(map(float, r)) for r in A]
def cartan_D(n: int) -> Matrix:
    A = [[0]*n for _ in range(n)]
    for i in range(n):
        A[i][i] = 2
    for i in range(n-2):
        A[i][i+1] = A[i+1][i] = -1
    A[n-3][n-1] = A[n-1][n-3] = -1
    return [list(map(float, r)) for r in A]
def cartan_E6() -> Matrix:
    A = [[2,-1,0,0,0,0],[-1,2,-1,0,0,0],[0,-1,2,-1,0,-1],[0,0,-1,2,-1,0],[0,0,0,-1,2,0],[0,0,-1,0,0,2]]
    return [list(map(float, r)) for r in A]
def cartan_E7() -> Matrix:
    A = [[2,-1,0,0,0,0,0],[-1,2,-1,0,0,0,0],[0,-1,2,-1,0,0,-1],[0,0,-1,2,-1,0,0],[0,0,0,-1,2,-1,0],[0,0,0,0,-1,2,0],[0,0,-1,0,0,0,2]]
    return [list(map(float, r)) for r in A]
def cartan_E8() -> Matrix:
    A = [[2,-1,0,0,0,0,0,0],[-1,2,-1,0,0,0,0,0],[0,-1,2,-1,0,0,0,-1],[0,0,-1,2,-1,0,0,0],[0,0,0,-1,2,-1,0,0],[0,0,0,0,-1,2,-1,0],[0,0,0,0,0,-1,2,0],[0,0,-1,0,0,0,0,2]]
    return [list(map(float, r)) for r in A]
NIEMEIER_SPECS = ["D24","D16 E8","E8^3","A24","D12^2","A17 E7","D10 E7^2","A15 D9","D8^3","A12^2","A11 D7 E6","E6^4","A9^2 D6","D6^4","A8^3","A7^2 D5^2","A6^4","A5^4 D4","D4^6","A4^6","A3^8","A2^12","A1^24"]

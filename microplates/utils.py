import re
import collections.abc
import pandas as pd
import numpy as np


plate_shapes = plate_layouts = plates = {
    6:    (2, 3),
    12:   (3, 4),
    24:   (4, 6),
    48:   (6, 8),
    96:   (8, 12),
    384:  (16, 24),
    1536: (32, 48)
}


_alpha = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
letters = dict(zip(_alpha,range(len(_alpha))))

def itertuples(x,y, by='row'):
    """Iterate across tuples from `(x[0],y[0])` ... `(x[1],y[1])`

    Parameters
    ----------
    x : tuple of int
    y : tuple of int
    by : str, defalt='row'
        `'row'` to increment the `y` values first, (e.g. `(0,0), (0,1), (0,2)`...)
        `'column'` to increment the `x` values first, e.g. (`(0,0), (1,0), (2,0)`...)

    Yields
    ------
    tuple
        Pair of values, starting with (x[0], y[0]) and ending with (x[1], y[1])
    """
    if by == 'column':
        # for each column
        for b, j in enumerate(range(x[1], y[1]+1)):
            # for each row
            for a, i in enumerate(range(x[0], y[0]+1)):
                yield (i,j)
    else:
        # for each row
        for a, i in enumerate(range(x[0], y[0]+1)):
            # for each column
            for b, j in enumerate(range(x[1], y[1]+1)):
                yield (i,j)

assert list(itertuples((0,0),(0,2))) == [(0,0),(0,1),(0,2)]
assert list(itertuples((1,0),(2,0))) == [(1,0),(2,0)]
assert list(itertuples((1,0),(2,1))) == [(1,0),(1,1),(2,0),(2,1)]
assert list(itertuples((1,0),(2,1), by='column')) == [(1,0),(2,0),(1,1),(2,1)]

# def cell2tuple(cell):
#     """convert a string cell spec e.g. 'A1' into a zero-based tuple"""
#     m = re.match(r"(\w)(\d+)",cell)
#     if m is not None:
#         g = m.groups()
#         return (letters[g[0]], int(g[1])-1)

def letters2row(r):
    """Converts a string of letters into a number, in base 26

    Examples
    --------

    >>> letters2row('A')
    0
    >>> letters2row('H')
    7
    >>> letters2row('G')
    6
    >>> letters2row('AA')
    26
    >>> letters2row('AB')
    27
    >>> letters2row('BA')
    52

    See Also
    --------
    row2letters
    """
    row_alpha = list(r)
    row = 0;
    for i in range(len(row_alpha)):
        row = row * len(_alpha)
        row = row + letters[row_alpha[i]]+1
    return row-1

assert letters2row('A') == 0
assert letters2row('H') == 7
assert letters2row('G') == 6
assert letters2row('AA') == 26
assert letters2row('AB') == 27
assert letters2row('BA') == 52

cell_regex = re.compile(r"^([a-zA-Z]+)(\d+)")
def cell2tuple(cell):
    """convert a string cell spec e.g. 'A1' into a zero-based tuple

    Examples
    --------

    >>> cell2tuple('A1')
    (0,0)
    >>> cell2tuple('G11')
    (6,10)
    >>> cell2tuple('AA1')
    (26,0)
    >>> cell2tuple('AB10')
    (27,9)
    """
    m = cell_regex.match(cell)
    if m is not None:
        g = m.groups()
        row_alpha = list(g[0])
        row = 0;
        for i in range(len(row_alpha)):
            row = row * len(_alpha)
            row = row + letters[row_alpha[i]]+1
        return (row-1, int(g[1])-1)

assert cell2tuple('A1') == (0,0)
assert cell2tuple('H10') == (7,9)
assert cell2tuple('G11') == (6,10)
assert cell2tuple('AA1') == (26,0)
assert cell2tuple('AB10') == (27,9)
assert cell2tuple('BA12') == (52,11)

def is_cell(cell):
    return cell_regex.fullmatch(cell) is not None

assert is_cell('A1')
assert is_cell('F12')
assert is_cell('BC256')
assert not is_cell('H 12')
assert not is_cell('5S')

def row2letters(i):
    """Convert a number to a string, in base 26

    Examples
    --------
    >>> row2letters(7)
    'H'
    >>> row2letters(27)
    'AB'
    >>> row2letters(55)
    'BD'

    See Also
    --------
    letters2row
    """
    r = ''
    i = int(i)
    while i >= 0:
        r = _alpha[i % len(_alpha)] + r
        i = i // len(_alpha) - 1
    return r

assert row2letters(7) == 'H'
assert row2letters(27) == 'AB'
assert row2letters(55) == 'BD'

def tuple2cell(i,j):
    """convert zero-indexed coordinates `i`, `j` to a cell name e.g. 'A1'"""
    return row2letters(i) + str(j+1)

assert tuple2cell(7,9) == 'H10'
assert tuple2cell(27,9) == 'AB10'
assert tuple2cell(55,11) == 'BD12'


def range2cells(rng,wells=96):
    """convert a range e.g. 'A1:B7' to a pair of cells e.g. ('A1', 'B7').

    Parameters
    ----------
    rng : str
        Accepts ranges of the form `'A1:B7'`, `'A:C'`, or `'2:4'`.
        For row or column ranges (e.g. 'A:C' or '2:4'), you must specify the number of `wells` in the plate
    wells : int, default=96
        number of wells in the plate (implies plate shape)

    Returns
    -------
    tuple of str
        (starting well, ending well); or `None` if the syntax is incorrect

    Notes
    -----
    The wells are sorted, so regardless how `rng` is written, the
    "starting well" is always top-left and "ending well" is bottom-right.
    """

    # e.g. A1:B7
    m = re.match(r"([a-zA-Z]\d+):([a-zA-Z]\d+)",rng)
    if m is not None:
        return tuple(sorted(m.groups()))

    # e.g. A:A -> 'A1','A12'
    # B:D -> 'B1','D12'
    # C:B -> 'B1','C12'
    m = re.match(r"([a-zA-Z]):([a-zA-Z])",rng)
    if m is not None:
        g = sorted(m.groups())
        return (g[0]+'1', g[1]+str(plates[wells][1]))

    # e.g. 1:1 -> 'A1','H1'
    # 1:3 -> 'A1','H3'
    # 3:2 -> 'A2','H2'
    m = re.match(r"(\d+):(\d+)",rng)
    if m is not None:
        g = sorted(int(x) for x in m.groups())
        return (_alpha[0]+str(g[0]), _alpha[plates[wells][0]-1]+str(g[1]))

assert range2cells('A1:B1') == range2cells('B1:A1') == ('A1', 'B1')
assert range2cells('A:B') == ('A1', 'B12')
assert range2cells('A:A') == ('A1','A12')
assert range2cells('B:D') == ('B1','D12')
assert range2cells('C:B') == ('B1','C12')
assert range2cells('1:1') == ('A1','H1')
assert range2cells('1:3') == ('A1','H3')
assert range2cells('A11:A12') == ('A11','A12')
assert range2cells('2:10') == range2cells('10:2') == ('A2','H10')
assert range2cells("A:A",wells=384) == ("A1","A24")
assert range2cells("I:I",wells=384) == ("I1","I24")
assert range2cells("23:23",wells=384) == ("A23","P23")

def range2tuple(rng,wells=96):
    """convert a range e.g. 'A1:B10' to a sorted pair of zero-based tuples, e.g. ((0,0),(1,10)).
    Accepts range in the form of `range2cells`. """
    # m = re.match(r"(\w)(\d+):(\w)(\d+)",rng)
    # if m is not None:
    #     g = m.groups()
    #     return tuple(sorted(((letters[g[0]], int(g[1])-1), (letters[g[2]], int(g[3])-1))))
    cs = range2cells(rng, wells)
    if cs is not None:
        return tuple(sorted([cell2tuple(cs[0]), cell2tuple(cs[1])]))

assert range2tuple('A1:C10') == range2tuple('C10:A1') == ((0,0),(2,9))
assert range2tuple('G7:G10') == range2tuple('G10:G7') == ((6,6),(6,9))
assert range2tuple("A:A",wells=384) == ((0,0),(0,23))

def range2cell_list(rng, wells=96, by='row'):
    """convert a range e.g. 'A1:B10' to a sorted list of cell names, e.g. ['A1', 'A2', ..., 'B9', 'B10']"""
    tuples = range2tuple(rng,wells=wells)
    if tuples is not None:
        return [tuple2cell(*t) for t in itertuples(*tuples, by=by)]

assert range2cell_list('A1:A2') == ['A1','A2']
assert range2cell_list('A1:B2') == ['A1','A2','B1','B2']
assert range2cell_list('A1:B2', by='column') == ['A1','B1','A2','B2']


def iterwells(n, start='A1', wells=96, by='rows'):
    """Generator to iterate through sequential wells.

    Parameters
    ----------
    n : int
        How many wells to yield
    start : default='A1'
        Which well to start at
    wells : int, default=96
        Layout of the plate (number of wells)
    by : str, default='rows'
        Iterate across rows or across columns

    Returns
    -------
    int
        Description of anonymous integer return value.

    Examples
    --------
    >>> np.add(1, 2)
    3

    Comment explaining the second example.

    >>> np.add([[1, 2], [3, 4]],
    ...        [[5, 6], [7, 8]])
    array([[ 6,  8],
           [10, 12]])
    """
    cell = list(cell2tuple(start))
    (rows, cols) = plates[wells]
    while n > 0:
        yield(tuple2cell(*cell))
        n = n - 1

        if by == 'columns':
            cell[0] += 1
            if cell[0] >= rows:
                cell[0] = 0
                cell[1] += 1
            if cell[1] >= cols:
                cell[1] = 0
        else:
            cell[1] += 1
            if cell[1] >= cols:
                cell[1] = 0
                cell[0] +=1
            if cell[0] >= rows:
                cell[0] = 0

iterate_wells = iterwells
assert list(iterwells(2,start='H12')) == ['H12', 'A1']
assert list(iterwells(13)) == ['A1','A2','A3','A4','A5','A6','A7','A8','A9','A10','A11','A12','B1']
assert list(iterwells(9)) == ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9']

def infer_plate_size(cells, all=False, prefer96=False):
    cells = [cell2tuple(w) for w in cells]
    max_row = max(w[0] for w in cells)
    max_col = max(w[1] for w in cells)
    possible_plates = []
    for nwells in plates:
        if plates[nwells][0] > max_row and plates[nwells][1] > max_col:
            possible_plates.append(nwells)

    if all:
        return possible_plates
    else:
        if prefer96 and 96 in possible_plates:
            return 96
        else:
            return min(possible_plates)

assert infer_plate_size(['H12']) == infer_plate_size(['A1','H12']) == 96
assert infer_plate_size(['H13']) == 384
# assert infer_plate_size(['A6']) == 24
# assert infer_plate_size(['A6'], prefer96=True) == 96

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

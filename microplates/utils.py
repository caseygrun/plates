"""
Utility functions for working with microplate data.
"""


import re
import collections.abc
import pandas as pd
import numpy as np


#: Mapping of available plate shapes; keys are the total number of wells in
#: the plate (e.g. 96, 384, etc.), values are the dimensions ``(width, height)``
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

def is_cell(cell):
    return cell_regex.fullmatch(cell) is not None

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

def tuple2cell(i,j):
    """convert zero-indexed coordinates `i`, `j` to a cell name e.g. 'A1'"""
    return row2letters(i) + str(j+1)

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


def range2tuple(rng, wells=96):
    """convert a range e.g. 'A1:B10' to a sorted pair of zero-based tuples, e.g. ((0,0),(1,10)).
    Accepts range in the form of `range2cells`. """
    # m = re.match(r"(\w)(\d+):(\w)(\d+)",rng)
    # if m is not None:
    #     g = m.groups()
    #     return tuple(sorted(((letters[g[0]], int(g[1])-1), (letters[g[2]], int(g[3])-1))))
    cs = range2cells(rng, wells)
    if cs is not None:
        return tuple(sorted([cell2tuple(cs[0]), cell2tuple(cs[1])]))


def range2cell_list(rng, wells=96, by='row'):
    """convert a range e.g. 'A1:B10' to a sorted list of cell names, e.g. ['A1', 'A2', ..., 'B9', 'B10']
    See :func:`iterrange`
    """
    # tuples = range2tuple(rng,wells=wells)
    # if tuples is not None:
    #     return [tuple2cell(*t) for t in itertuples(*tuples, by=by)]
    return list(iterrange(rng, wells=wells, by=by))

def iterrange(rngs, wells=96, by='row'):
    """Generator over each well in a rectangular range (e.g. 'A1:B10') or comma-separated list of such ranges (e.g. 'A1:B1,C2:D2')

    Parameters
    ----------
    rngs : str
        Comma-separated list of rectangular ranges
    wells : int, default=96
        Number of wells in the microplate, indicating the plate shape
    by : 'row'
        ``'row'`` to iterate through each well in a row before proceeding to the next row
        ``'column'`` to iterate through each well in a column before proceeding to the next column

    Yields
    ------
    str
        Name of each well in the range
    """
    for rng in rngs.split(','):
        tuples = range2tuple(rng, wells=wells)
        if tuples is not None:
            for t in itertuples(*tuples, wells=wells, by=by):
                yield tuple2cell(*t)

iterate_range = iterrange

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

def infer_plate_size(cells, all=False, prefer96=False, prefer=None):
    """determines the size or possible sizes of a microplate based on the list of well names

    Parameters
    ----------
    cells : array_like
        Names of wells
    all : bool, default=False
        True to give a list of all possible plate shapes, False to give only the
        smallest possible plate size that accommodates all wells
    prefer96 : bool, default=False
        Deprecated; equivalent to `prefer=96`
    prefer : int, optional
        If given, indicates a plate shape that should be preferred, which may
        not be the smallest possible shape. For instance, if ``cells`` can be
        accommodated by 48-, 96-, 384-, and 1536-well plates, but ``prefer=96``
        and ``all=False``, 96 will be returned.


    Returns
    -------
    int or list of int
        Size or sorted list of sizes of plates that can accommodate cells

    Examples
    --------
    >>> infer_plate_size(['A6'])
    24

    >>> infer_plate_size(['A6'], all=True)
    [24, 48, 96, 384, 1536]

    >>> infer_plate_size(['A6'], prefer=96)
    96

    >>> infer_plate_size(['H13'], prefer=96)
    384
    """
    if prefer96:
        prefer = 96

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
        if prefer is not None and prefer in possible_plates:
            return prefer
        else:
            return min(possible_plates)


# assert infer_plate_size(['A6']) == 24
# assert infer_plate_size(['A6'], prefer96=True) == 96

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

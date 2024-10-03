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
    """Interprets a string of letters as a number in base 26

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
def well2tuple(cell):
    """convert a string well name e.g. 'A1' into a zero-based tuple of (row, column)

    Examples
    --------

    >>> well2tuple('A1')
    (0,0)
    >>> well2tuple('G11')
    (6,10)
    >>> well2tuple('AA1')
    (26,0)
    >>> well2tuple('AB10')
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
cell2tuple = well2tuple

def is_well(cell):
    """determine if a string is a well name (e.g. A1, AA25, etc.)"""
    return cell_regex.fullmatch(str(cell)) is not None

is_cell = is_well

def row2letters(i):
    """Convert a number to a string of letters in base 26, with A=0, B=1, etc.

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

def tuple2well(i,j):
    """convert zero-indexed coordinates row `i`, column `j` to a cell name e.g. 'A1'"""
    return row2letters(i) + str(j+1)
tuple2cell = tuple2well

def range2wells(rng,wells=96):
    """convert a rectangular range e.g. 'A1:B7' to a pair of wells e.g. ('A1', 'B7').

    Parameters
    ----------
    rng : str
        Accepts ranges of the form ``'A1:B7'`` (``well:well``), ``'A:C'``
        (``row:row``), or `'2:4'` (``column:column``). For row or column ranges
        (e.g. ``'A:C'`` or ``'2:4'``), you should specify the number of ``wells``
        in the plate; the wells returned will be a rectangular range containing
        all rows or columns
    wells : int, default=96
        number of wells in the plate (implies plate shape); used for row or
        column ranges

    Examples
    --------
    >>> range2wells('A:B')
    ('A1', 'B12')
    >>> range2wells('A:B',wells=384)
    ('A1', 'B24')
    >>> range2wells('2:4')
    ('A2', 'H4')
    >>> range2wells('2:4',wells=24)
    ('A2', 'D4')
    >>> range2wells('A1:B7')
    ('A1', 'B7')

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
range2cells = range2wells

def range2tuple(rng, wells=96):
    """convert a range e.g. 'A1:B10' to a sorted pair of zero-based tuples, e.g. ``((0,0),(1,10))``.

    Parameters
    ----------
    rng : str
        range in the form accepted by :func:`range2wells`.
    wells : int, default=96
        number of wells in the plate (implies plate shape); used for row or
        column ranges

    See Also
    --------
    :func:`range2wells`
    """
    # m = re.match(r"(\w)(\d+):(\w)(\d+)",rng)
    # if m is not None:
    #     g = m.groups()
    #     return tuple(sorted(((letters[g[0]], int(g[1])-1), (letters[g[2]], int(g[3])-1))))
    cs = range2cells(rng, wells)
    if cs is not None:
        return tuple(sorted([cell2tuple(cs[0]), cell2tuple(cs[1])]))


def range2well_list(rng, wells=96, by='row'):
    """convert a range e.g. 'A1:B10' to a sorted list of cell names, e.g. ['A1', 'A2', ..., 'B9', 'B10']
    See :func:`iterrange`
    """
    # tuples = range2tuple(rng,wells=wells)
    # if tuples is not None:
    #     return [tuple2cell(*t) for t in itertuples(*tuples, by=by)]
    return list(iterrange(rng, wells=wells, by=by))

range2cell_list = range2well_list

def iterrange(rngs, wells=96, by='row'):
    """Generator over each well in a rectangular range (e.g. 'A1:B10') or comma-separated list of such ranges (e.g. 'A1:B1,C2:D2')

    Parameters
    ----------
    rngs : str
        Comma-separated list of rectangular ranges
    wells : int, default=96
        Number of wells in the microplate, indicating the plate shape
    by : str, default='row'
        ``'row'`` to iterate through each well in a row (in the range) before proceeding to the next row
        ``'column'`` to iterate through each well in a column before proceeding to the next column

    Yields
    ------
    str
        Name of each well in the range

    See Also
    --------
    iterrange
    """
    for rng in rngs.split(','):
        tuples = range2tuple(rng, wells=wells)
        if tuples is not None:
            for t in itertuples(*tuples, by=by):
                yield tuple2cell(*t)

iterate_range = iterrange

def next_well(well, wells=96, by='rows', **kwargs):
    return next(iterwells(1, start=well, wells=wells, by=by, **kwargs))


def next_row(well, wells=96, plate=False, start_plate=0):
    t = cell2tuple(well)
    t = (t[0]+1, 0)


    if t[0] >= plate_layouts[wells][0]:
        if plate:
            return (start_plate+1, 'A1')
        else:
            return 'A1'
    else:
        return tuple2cell(t)

def next_column(well, wells=96, plate=False, start_plate=0):
    t = cell2tuple(well)
    t = (0, t[1]+1)


    if t[1] >= plate_layouts[wells][1]:
        start_plate += 1
        well = 'A1'
    else:
        well = tuple2cell(t)

    if plate:
        return (start_plate, well)
    else:
        return well

def iterwells(n, start='A1', wells=96, by='rows', plate=False, start_plate=0):
    """Generator to iterate through sequential wells.

    Notes
    -----

    :func:`iterwells` iterates through a number of wells in a possibly
    non-rectangular range, traversing all wells in the plate:

    >>> list(iterwells(14, start='A3', wells=96))
    ['A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A10', 'A11', 'A12', 'B1', 'B2', 'B3', 'B4']

    :func:`iterrange` by contrast traverses all wells in a rectangular range:

    >>> list(iterrange('A3:B4'))
    ['A3', 'A4', 'B3', 'B4']

    For rectangular ranges that span the entire width or height of the plate,
    the behavior of the two functions is equivalent:

    >>> list(iterrange('A:B'))
    ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A10', 'A11', 'A12', 'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B9', 'B10', 'B11', 'B12']
    >>> list(iterwells(24, start='A1'))
    ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A10', 'A11', 'A12', 'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B9', 'B10', 'B11', 'B12']

    Parameters
    ----------
    n : int
        How many wells to yield
    start : default='A1'
        Which well to start at
    wells : int, default=96
        Layout of the plate (number of wells)
    by : str, default='row'
        ``'row'`` to iterate through each well in a row before proceeding to the next row
        ``'column'`` to iterate through each well in a column before proceeding to the next column
    plate : bool, default=False
        True to track a plate number and yield a tuple of (plate, well) rather than just a well. 
        Allows iterating across >96 wells; the 97th well will yield (start_plate+1, 'A1'), etc.
    start_plate : int, default=0
        if ``plate`` is ``True``, then what number should the first plate start with?


    Yields
    ------
    str
        Well names, in order

    Examples
    --------
    >>> list(iterwells(4))
    ['A1', 'A2', 'A3', 'A4']

    >>> list(iterwells(4,by='columns'))
    ['A1', 'B1', 'C1', 'D1']

    >>> list(iterwells(16,by='columns'))
    ['A1', 'B1', 'C1', 'D1', 'E1', 'F1', 'G1', 'H1', 'A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2']

    >>> list(iterwells(48, wells=384))
    ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A10', 'A11', 'A12', 'A13', 'A14', 'A15', 'A16', 'A17', 'A18', 'A19', 'A20', 'A21', 'A22', 'A23', 'A24', 'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B9', 'B10', 'B11', 'B12', 'B13', 'B14', 'B15', 'B16', 'B17', 'B18', 'B19', 'B20', 'B21', 'B22', 'B23', 'B24']

    See Also
    --------
    iterrange

    """
    cell = list(cell2tuple(start))
    (rows, cols) = plates[wells]

    current_plate = start_plate

    while n > 0:
        if plate:
            yield( (current_plate,tuple2cell(*cell)) )
        else:
            yield(tuple2cell(*cell))

        n = n - 1

        if by == 'columns':
            cell[0] += 1
            if cell[0] >= rows:
                cell[0] = 0
                cell[1] += 1
            if cell[1] >= cols:
                cell[1] = 0
                current_plate += 1
        else:
            cell[1] += 1
            if cell[1] >= cols:
                cell[1] = 0
                cell[0] +=1
            if cell[0] >= rows:
                cell[0] = 0
                current_plate += 1

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

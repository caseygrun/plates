from __future__ import division
import re
import pandas as pd
import numpy as np
import collections

from .data import calc_norm


__all__ = ['data']

plate_shapes = {
    6:   (2, 3),
    12:  (3, 4),
    48:  (6, 8),
    96:  (8, 12),
    384: (16, 24)
}


alpha = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
letters = dict(zip(alpha,range(len(alpha))))

def itertuples(x,y):
    # for each row
    for a, i in enumerate(range(x[0], y[0]+1)):
        # for each column
        for b, j in enumerate(range(x[1], y[1]+1)):
            yield (i,j)

assert list(itertuples((0,0),(0,2))) == [(0,0),(0,1),(0,2)]
assert list(itertuples((1,0),(2,0))) == [(1,0),(2,0)]
assert list(itertuples((1,0),(2,1))) == [(1,0),(1,1),(2,0),(2,1)]


def letters2row(r):
    """convert a string representing an excel-style row, e.g. A, G, H, AB, etc. into a zero-based row index"""
    row_alpha = list(r)
    row = 0;
    for i in range(len(row_alpha)):
        row = row * len(alpha)
        row = row + letters[row_alpha[i]]+1
    return row-1

assert letters2row('A') == 0
assert letters2row('H') == 7
assert letters2row('G') == 6
assert letters2row('AA') == 26
assert letters2row('AB') == 27
assert letters2row('BA') == 52


def cell2tuple(cell):
    """convert a string excel-style cell name e.g. 'A1' into a zero-based tuple e.g. (0,0)"""
    m = re.match(r"([a-zA-Z]+)(\d+)",cell)
    if m is not None:
        g = m.groups()
        row_alpha = list(g[0])
        row = 0;
        for i in range(len(row_alpha)):
            row = row * len(alpha)
            row = row + letters[row_alpha[i]]+1
        return (row-1, int(g[1])-1)

assert cell2tuple('A1') == (0,0)
assert cell2tuple('H10') == (7,9)
assert cell2tuple('G11') == (6,10)
assert cell2tuple('AA1') == (26,0)
assert cell2tuple('AB10') == (27,9)
assert cell2tuple('BA12') == (52,11)

def row2letters(i):
    """convert a zero-based row into an excel-style row letter"""
    r = ''
    i = int(i)
    while i >= 0:
        r = alpha[i % len(alpha)] + r
        i = i // len(alpha) - 1
    return r

assert row2letters(7) == 'H'
assert row2letters(27) == 'AB'
assert row2letters(55) == 'BD'

def tuple2cell(i,j):
    """convert zero-indexed coordinates i, j to a cell name e.g. 'A1' """
    return row2letters(i) + str(j+1)

assert tuple2cell(7,9) == 'H10'
assert tuple2cell(27,9) == 'AB10'
assert tuple2cell(55,11) == 'BD12'


def range2cells(rng,wells=96):
    """convert a range e.g. 'A1:B7' to a pair of cells e.g. ('A1', 'B7').
    Accepts ranges of the form:

        'A1:B7'
        'A:C'
        '2:4'

    For row or column ranges (e.g. 'A:C' or '2:4'), must specify the number of wells in the plate

    Returns None if syntax is incorrect"""

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
        return (g[0]+'1', g[1]+str(plate_shapes[wells][1]))

    # e.g. 1:1 -> 'A1','H1'
    # 1:3 -> 'A1','H3'
    # 3:2 -> 'A2','H2'
    m = re.match(r"(\d+):(\d+)",rng)
    if m is not None:
        g = sorted(int(x) for x in m.groups())
        return (alpha[0]+str(g[0]), alpha[plate_shapes[wells][0]-1]+str(g[1]))

assert range2cells('A1:B1') == range2cells('B1:A1') == ('A1', 'B1')
assert range2cells('A:B') == ('A1', 'B12')
assert range2cells('A:A') == ('A1','A12')
assert range2cells('B:D') == ('B1','D12')
assert range2cells('C:B') == ('B1','C12')
assert range2cells('1:1') == ('A1','H1')
assert range2cells('1:3') == ('A1','H3')
assert range2cells('A11:A12') == ('A11','A12')
assert range2cells('2:10') == range2cells('10:2') == ('A2','H10')

def range2tuple(rng,wells=96):
    """convert a range e.g. 'A1:B10' to a sorted pair of zero-based tuples, e.g. ((0,0),(1,10)).
    Accepts range in the form of range2cells. """
    # m = re.match(r"(\w)(\d+):(\w)(\d+)",rng)
    # if m is not None:
    #     g = m.groups()
    #     return tuple(sorted(((letters[g[0]], int(g[1])-1), (letters[g[2]], int(g[3])-1))))
    cs = range2cells(rng, wells)
    if cs is not None:
        return tuple(sorted([cell2tuple(cs[0]), cell2tuple(cs[1])]))

assert range2tuple('A1:C10') == range2tuple('C10:A1') == ((0,0),(2,9))
assert range2tuple('G7:G10') == range2tuple('G10:G7') == ((6,6),(6,9))

def range2cell_list(rng,wells=96):
    """convert a range e.g. 'A1:B10' to a sorted list of cell names, e.g. ['A1', 'A2', ..., 'B9', 'B10']"""
    tuples = range2tuple(rng)
    if tuples is not None:
        return [tuple2cell(*t) for t in itertuples(*tuples)]

assert range2cell_list('A1:A2') == ['A1','A2']
assert range2cell_list('A1:B2') == ['A1','A2','B1','B2']

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *  

def prog2spec(prog=None,index=None,include_row_column=False):
    """
    Convert a dict `program` containing a platemap to a tidy pandas DataFrame
    (`spec`) encoding that platemap. The `spec` can then be joined to a tidy
    dataframe to attach metadata to the plate.
    
    Program format tutorial
    -----------------------
    
    Each program is of this form:

        {
            'A1:A3': { 'strain': 'PAO1', 'drug': 'ampicillin', 'concentration' [[0, 10, 100]] }
            ...
        }

    where each _rule_ maps a range ('A1:A3' in this case) to a set of values to be applied
    to that range. Let's walk through this rule:
    
    'A1:A3' specifies that this rule applies to wells 'A1', 'A2', and 'A3'.

    The three _variables_ that apply to this range are `strain`, `drug`, and `concentration`.
    They have the following values for this range:

        - all wells have `strain = 'PAO1'`
        - all wells have `drug = 'ampicillin'`
        - concentration is spooled across the range, such that 
          `A1` has `concentration = 0`, `A2` has `concentration = 10`, etc.

    The resulting dataframe would have column for each of the variables (`strain`, `drug`, 
    and `concentration`), in addition to `well`. There would be 1 row for each well in the 
    96-well plate, like this:

            strain        drug  concentration
        A1    PAO1  ampicillin            0.0
        A2    PAO1  ampicillin           10.0
        A3    PAO1  ampicillin          100.0
        A4     NaN         NaN            NaN
        ...
        H12    NaN         NaN            NaN

        [96 rows x 3 columns]

    I mentioned that `concentration` is "spooled" across the range; in general, if the value
    given for a variable in a range is an ndarray or list of lists with the same "shape" as the
    range, then one value from the range will be selected from the array for each well. This 
    can be different per-variable (for instance, in this example `concentration` was spooled 
    while `strain` and `drug` were not).

    You can apply the same set of values to multiple ranges by separating the two ranges with
    a comma:

        {
            'A1:A3,B5:B7': { 'strain': 'PAO1', 'drug': 'ampicillin', 'concentration' [[0, 10, 100]] }
            ...
        }    

    Note that spooling applies to each range *indepdendently*; this means in the example above,
    the `concentration` of `A1` = `concentration` of `B5` = 0, `concentration` of `A2` = 
    `concentration` of `B6` = 10, and so on. On the other hand, if you did this,

        {
            'A1:A3,B5': { 'strain': 'PAO1', 'drug': 'ampicillin', 'concentration' [[0, 10, 100]] }
            ...
        }      

    `concentration` would spool across `A1:A3`, but `B5` would be assigned a concentration of 
    `[[0, 10, 100]]`... probably not what you wanted. 

    If you wanted to use a different plate shape, just add a `well` key:

        {
            "A1:A3": { 'strain': 'PAO1' },
            "well": 384
        }

    Notice that wells not appearing in the platemap have values of NaN for all columns. You can 
    easily throw away extra wells that are not in the platemap using `dropna`:

        >>> prog2spec({'A1:A3': { 'strain': 'PAO1', 'drug': 'ampicillin', 'concentration': [[0, 10, 100]] }}).dropna()
           strain        drug  concentration
        A1   PAO1  ampicillin            0.0
        A2   PAO1  ampicillin           10.0
        A3   PAO1  ampicillin          100.0
    
    Parameters
    ----------
    prog : dict
        Program describing the platemap; keys should be a range of wells,
        values should be a dict containing variables to assign to those 
        wells. One special key "wells" may be used to determine the number of 
        wells in the plate (e.g. 96, 384, etc.). See examples.
    index : None
    include_row_column : bool
        True to include columns named `row` and `column` in the resulting
        data frame, corresponding to the 0-indexed row/column in the original
        microtiter plate

    Returns
    -------
    spec: DataFrame
        Dataframe containing one row for each well in the palte

    Examples
    --------

    >>> prog2spec({'A1:A2':{ 'strain': 'B. theta' }})
           strain
    A1   B. theta
    A2   B. theta
    A3        NaN
    ...
    H12       NaN
    [96 rows x 1 columns]
    
    >>> prog2spec({'A1:A2':{ 'strain': [['B. theta','C. diff']] }})
          strain
    A1   B. theta
    A2    C. diff
    A3        NaN
    ...
    H12       NaN
    [96 rows x 1 columns]

    >>> prog2spec({'B1:C2,E1:F2':{ 'conc': [[0,1],[2,3]] }}).dropna()
        conc
    B1   0.0
    B2   1.0
    C1   2.0
    C2   3.0
    E1   0.0
    E2   1.0
    F1   2.0
    F2   3.0

    """
    if prog is None: prog = {}
    wells = prog['wells'] if 'wells' in prog else 96
    dims = plate_shapes[wells]

    columns = set()
    cells = []
    for i in range(dims[0]):
        for j in range(dims[1]):
            cells.append(tuple2cell(i,j))
    data = pd.DataFrame(index=cells)

    if include_row_column:
        for i in range(dims[0]):
            for j in range(dims[1]):
                data.loc[tuple2cell(i,j),'row'] = i
                data.loc[tuple2cell(i,j),'column'] = j

    # each key in `prog` should specify a range, and its value should be a dict of data to assign to that range
    #   e.g. 'A1:A2': {'strain': 'B. theta'}
    for rngs, values in prog.items():

        # key may be a comma-separated list of ranges
        for rng in rngs.split(','):

            # keys may be ranges (e.g. 'A1:F12')
            tup = range2tuple(rng)
            if tup is not None:

                # calculate dimensions of range
                dim = (tup[1][0]-tup[0][0]+1,tup[1][1]-tup[0][1]+1)

                # for each row
                for a, i in enumerate(range(tup[0][0], tup[1][0]+1)):

                    # for each column
                    for b, j in enumerate(range(tup[0][1], tup[1][1]+1)):
                        cell = tuple2cell(i,j)

                        # for each data, assign value
                        for key, value in values.items():
                            value_arr = None

                            # if `value` is array_like
                            if isinstance(value, collections.Sequence) and not isinstance(value, str):
                                value_arr = np.array(value)

                            # and shape is the same as range,
                            if value_arr is not None and value_arr.shape == dim:

                                # assign element-wise
                                data.loc[cell,key] = value_arr[a,b]

                            # otherwise, assign entire value
                            else:
                                data.loc[cell,key] = value

            # keys may be single cells (e.g. 'B6')
            else:
                tup = cell2tuple(rng)
                if tup is not None:
                    for key, value in values.items():
                        data.loc[rng,key] = value

    return data

def __test_prog2spec():

    s = prog2spec({'A1:A2':{ 'strain': 'B. theta' }})
    assert s.loc['A1','strain'] == s.loc['A2','strain'] == 'B. theta'

    s = prog2spec({'A1,A2':{ 'strain': 'B. theta' }})
    assert s.loc['A1','strain'] == s.loc['A2','strain'] == 'B. theta'

    s = prog2spec({'A1:A2':{ 'strain': [['B. theta','C. diff']] }})
    assert s.loc['A1','strain'] == 'B. theta'
    assert s.loc['A2','strain'] == 'C. diff'

    s = prog2spec({'F12:G12':{ 'conc': [[0],[10]] }})
    assert s.loc['F12','conc'] == 0
    assert s.loc['G12','conc'] == 10

    s = prog2spec({'B1:C2':{ 'conc': [[0,1],[2,3]] }})
    assert s.loc['B1','conc'] == 0
    assert s.loc['B2','conc'] == 1
    assert s.loc['C1','conc'] == 2
    assert s.loc['C2','conc'] == 3


    s = prog2spec({'B1:C2,E1:F2':{ 'conc': [[0,1],[2,3]] }})
    assert s.loc['B1','conc'] == s.loc['E1','conc'] == 0
    assert s.loc['B2','conc'] == s.loc['E2','conc'] == 1
    assert s.loc['C1','conc'] == s.loc['F1','conc'] == 2
    assert s.loc['C2','conc'] == s.loc['F2','conc'] == 3

    s = prog2spec({'G7:G10':{ 'conc': 5 }})
    assert s.loc['G9','conc'] == 5

__test_prog2spec()


# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *  

# build map of 96 to 384-well plates:
map96384 = {}
for i in range(plate_shapes[96][0]):
    for j in range(plate_shapes[96][1]):
        map96384[tuple2cell(i,j)] = [tuple2cell(x,y) for x in [2*i,2*i+1] for y in [2*j,2*j+1]]


plate_conversion_maps = {
    96: { 384: map96384 }
}


def convert_spec(spec,from_wells,to_wells,include_row_column=True):
    """
    private; use spec96to384
    """
    delete_row_column = ('row' in spec.columns or 'column' in spec.columns) and not include_row_column
    conversion_map = plate_conversion_maps[from_wells][to_wells]

    newspec = {}
    for name,row in spec.iterrows():
        for cell in conversion_map[name]:
            r = row.copy()
            if include_row_column:
                r['row'], r['column'] = cell2tuple(cell)
            if delete_row_column:
                del r['row'], r['column']
            newspec[cell] = r

    return pd.DataFrame(newspec).transpose()


def spec96to384(spec,**kwargs):
    """
    Converts a DataFrame spec for a 96-well plate to a spec for a 384-well plate.

    Assumes each well in the 96-well plate is replicated onto 4 wells in a 384-well
    plate; e.g. A1 in 96-well -> A1, A2, B1, B2 in 384-well. 

    Parameters
    ----------
    spec : DataFrame
        spec, as returned by ``prog2spec``

    include_row_column : bool
        True to include columns named `row` and `column` in the resulting
        data frame, corresponding to the 0-indexed row/column in the original
        microtiter plate. 

        If there are already `row`/`column` columns and 
        - `include_row_column = False`, they will be deleted
        - `include_row_column = True`, they will be replaced with values for
        the 384-well plate

    Returns
    -------
    spec : DataFrame
        spec, as returned by ``prog2spec``    

    """
    return convert_spec(spec,96,384,**kwargs)


def __test_spec96to384():

    s = spec96to384(prog2spec({'A1':{ 'strain': 'B. theta' }},include_row_column=False),include_row_column=True)
    assert s.loc['A1','strain'] == s.loc['A2','strain'] == s.loc['B1','strain'] == s.loc['B2','strain'] == 'B. theta'
    assert s.loc['A1','row'] == s.loc['A2','row'] == 0
    assert s.loc['A2','column'] == 1

    s = spec96to384(prog2spec({'A1:A2':{ 'strain': [['B. theta','C. diff']] }},include_row_column=True),include_row_column=False)
    assert s.loc['B2','strain'] == 'B. theta'
    assert s.loc['B4','strain'] == 'C. diff'
    assert not ('row' in s) and not ('column' in s)

    s = spec96to384(prog2spec({'F12:G12':{ 'conc': [[0],[10]] }}))
    assert s.loc['L23','conc'] == 0
    assert s.loc['N24','conc'] == 10

    # s = prog2spec({'B1:C2':{ 'conc': [[0,1],[2,3]] }})
    # assert s.loc['B1','conc'] == 0
    # assert s.loc['B2','conc'] == 1
    # assert s.loc['C1','conc'] == 2
    # assert s.loc['C2','conc'] == 3
    #
    # s = prog2spec({'G7:G10':{ 'conc': 5 }})
    # assert s.loc['G9','conc'] == 5
    del s

__test_spec96to384()

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *  

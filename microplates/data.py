"""Generate and manipulate tidy :class:`pandas.DataFrame`\ s representing microplate data.

- Generate a tidy DataFrame containing microplate metadata, e.g. experimental conditions, replicates, etc.:
    + :func:`platemap_to_dataframe`
    + :func:`cherrypick`
- Combine or reshape microplate DataFrames:
    + :func:`scale_plate`
    + :func:`combine_plate_dataframes`
- Munge:
    + :func:`add_row_column`
    + :func:`fortify_plate`
"""

from .utils import *

def platemap_to_dataframe(prog=None, index=None, wells=96, include_row_column=False):
    """
    Convert a dict `program` containing a platemap to a tidy pandas DataFrame
    (`spec`) encoding that platemap. The `spec` can then be joined to a tidy
    dataframe to attach metadata to the plate.

    Notes
    -----

    Each program is of this form::

        {
            'A1:A3': { 'strain': 'PAO1', 'drug': 'ampicillin', 'concentration' [[0, 10, 100]] }
            ...
        }

    where each _rule_ maps a range (``'A1:A3'`` in this case) to a set of values
    which should be applied to that range. Let's walk through this rule:

    ``A1:A3`` specifies that this rule applies to wells ``A1``, ``A2``, and ``A3``.

    The three *variables* that apply to this range are ``strain``, ``drug``,
    and ``concentration``.
    They have the following values for this range:

        - all wells have ``strain = 'PAO1'``
        - all wells have ``drug = 'ampicillin'``
        - concentration is "spooled" across the range, such that
          ``A1`` has ``concentration = 0``, ``A2`` has ``concentration = 10``,
          and ``A3`` has ``concentration = 100``.

    The resulting ``DataFrame`` would have one column for each of the variables
    (``strain``, ``drug``, and ``concentration``), in addition to ``well``,
    which would be the index. There would be 1 row for each well in the
    96-well plate, like this::

            strain        drug  concentration
        A1    PAO1  ampicillin            0.0
        A2    PAO1  ampicillin           10.0
        A3    PAO1  ampicillin          100.0
        A4     NaN         NaN            NaN
        ...
        H12    NaN         NaN            NaN

        [96 rows x 3 columns]

    I mentioned that `concentration` is "spooled" across the range; in general,
    if the value given for a variable in a range is array_like (`np.ndarray`,
    or `list` or `list`s) with the same "shape" as the range, then one value
    from the range will be selected from the array for each well. This can be
    different per-variable (for instance, in this example `concentration` was
    spooled while `strain` and `drug` were not).

    You can apply the same set of values to multiple ranges by separating the two ranges with
    a comma::

        {
            'A1:A3,B5:B7': { 'strain': 'PAO1', 'drug': 'ampicillin', 'concentration': [[0, 10, 100]] }
            ...
        }


    Note that spooling applies to each range *indepdendently*; this means in the example above,
    the ``concentration`` of `A1` = 0, `concentration` of `B5` = 0, `concentration` of ``A2`` = 10,
    `concentration` of `B6` = 10, and so on::

        >>> df = platemap_to_dataframe({
        ...     'A1:A3,B5:B7': { 'strain': 'PAO1', 'drug': 'ampicillin', 'concentration': [[0, 10, 100]] }
        ... })
        >>> df.loc[['A1','A2','A3','B5','B6','B7'],:]
             strain        drug  concentration
        well
        A1     PAO1  ampicillin            0.0
        A2     PAO1  ampicillin           10.0
        A3     PAO1  ampicillin          100.0
        B5     PAO1  ampicillin            0.0
        B6     PAO1  ampicillin           10.0
        B7     PAO1  ampicillin          100.0


    On the other hand, this will not work and will generate an error, as the
    function will try and set ``concentration`` for `B5` to ``[[0,10,100]]``::

        >>> df = platemap_to_dataframe({
        ...     'A1:A3,B5': { 'strain': 'PAO1', 'drug': 'ampicillin', 'concentration': [[0, 10, 100]] }
        ... })

    If you want to use a different plate shape, just add a ``well`` key::

        {
            "A1:A3": { 'strain': 'PAO1' },
            "well": 384
        }

    Wells not appearing in the platemap have values of NaN for all columns. You can
    easily throw away extra wells that are not in the platemap using :func:`pandas.dropna <pandas:pandas.dropna>`::

        >>> platemap_to_dataframe({'A1:A3': { 'strain': 'PAO1', 'drug': 'ampicillin', 'concentration': [[0, 10, 100]] }}).dropna()
           strain        drug  concentration
        A1   PAO1  ampicillin            0.0
        A2   PAO1  ampicillin           10.0
        A3   PAO1  ampicillin          100.0

    Or, you can fill columns with a default value, using :func:`pandas.fillna`::

        >>> (platemap_to_dataframe({'A1:A3': { 'strain': 'PAO1', 'drug': 'ampicillin', 'concentration': [[0, 10, 100]] }})
        ...    .fillna({
        ...      'drug': 'none',
        ...      'strain': 'sterile',
        ...      'concentration': 0
        ...    }))
               strain        drug  concentration
        well
        A1       PAO1  ampicillin            0.0
        A2       PAO1  ampicillin           10.0
        A3       PAO1  ampicillin          100.0
        A4    sterile        none            0.0
        A5    sterile        none            0.0
        ...       ...         ...            ...
        H8    sterile        none            0.0
        H9    sterile        none            0.0
        H10   sterile        none            0.0
        H11   sterile        none            0.0
        H12   sterile        none            0.0

        [96 rows x 3 columns]

    Parameters
    ----------
    prog : dict
        Program describing the platemap.

        each key should be a *range* of wells, in any of these forms:
            - single well (e.g. ``A1``)
            - rectangular range of specific wells (``A1:B6``)
            - range of entire columns or entire rows (e.g. ``A:A`` = ``A1``,
              ``A2``, ``A3``, etc.; ``1:6`` = all of columns ``1``, ``2``, ...
              ``6`` etc.)
            - a comma-separated series of ranges (``A:B,E:F``, etc.)

        each value should be a ``dict`` containing variables to assign to that
        range of wells. For that range, each key will be a column in the output
        DataFrame. If a value is ``array_like`` and the same shape as the range,
        then each well in the range will be assigned a matching element of the
        ``array_like`` value. See tutorial and examples.

        One special key ``"wells"`` may be used to set the number of
        wells in the plate (e.g. 96, 384, etc.).
    index : None
    include_row_column : bool
        ``True`` to include columns named ``row`` and ``column`` in the resulting
        data frame, corresponding to the 0-indexed row/column in the original
        microtiter plate

    Returns
    -------
    pd.DataFrame
        Metadata for the microplate. Each row corresponds to a single well.
        Columns are the union of all variables mentioned in the program.

    Examples
    --------

    >>> platemap_to_dataframe({'A1:A2':{ 'strain': 'B. theta' }})
           strain
    A1   B. theta
    A2   B. theta
    A3        NaN
    ...
    H12       NaN
    [96 rows x 1 columns]

    >>> platemap_to_dataframe({'A1:A2':{ 'strain': [['B. theta','C. diff']] }})
          strain
    A1   B. theta
    A2    C. diff
    A3        NaN
    ...
    H12       NaN
    [96 rows x 1 columns]

    >>> platemap_to_dataframe({'B1:C2,E1:F2':{ 'conc': [[0,1],[2,3]] }}).dropna()
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
    if 'wells' in prog:
        wells = prog['wells']
    dims = plates[wells]

    columns = set()
    cells = []
    for i in range(dims[0]):
        for j in range(dims[1]):
            cells.append(tuple2cell(i,j))
    data = pd.DataFrame(index=cells)
    data.index = data.index.rename('well')

    if include_row_column:
        for i in range(dims[0]):
            for j in range(dims[1]):
                data.loc[tuple2cell(i,j),'row'] = i
                data.loc[tuple2cell(i,j),'column'] = j

    # each key in `prog` should specify a range, and its value should be a dict of data to assign to that range
    #   e.g. 'A1:A2': {'strain': 'B. theta'}
    for rngs, values in prog.items():

        # key may be a comma-separated list of ranges
        rngs = rngs.split(',')
        for rng in rngs:

            # keys may be ranges (e.g. 'A1:F12')
            tup = range2tuple(rng,wells=wells)
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
                            if isinstance(value, collections.abc.Sequence) and not isinstance(value, str):
                                value_arr = np.array(value)
                            elif isinstance(value, np.ndarray) and not isinstance(value, str):
                                value_arr = value

                            if value_arr is not None:
                                # value_arr = value_arr.squeeze()

                                # and shape is the same as range,
                                if value_arr.shape == dim:

                                    # assign element-wise
                                    data.loc[cell,key] = value_arr[a,b]
                                    continue

                                else: 
                                    # try to treat value_arr as a 1d sequence
                                    value_arr = value_arr.squeeze()
                                    if len(value_arr.shape) == 1:
                                        # if range is a single column, treat value_arr as a column vector
                                        if value_arr.shape[0] == dim[0] and dim[1] == 1:
                                            data.loc[cell,key] = value_arr[a]
                                            continue

                                        # if range is a single row, treat value_arr as a row vector
                                        elif value_arr.shape[0] == dim[1] and dim[0] == 1:
                                            data.loc[cell,key] = value_arr[b]
                                            continue


                            # otherwise, assign entire value
                            data.loc[cell,key] = value

            # keys may be single cells (e.g. 'B6')
            else:
                tup = cell2tuple(rng)
                if tup is not None:
                    for key, value in values.items():
                        data.at[rng,key] = value

    return data
prog2spec = platemap_to_dataframe

def cherrypick(pick_wells, values={'Pick':True}, others = {}, wells=96):
    """Make a DataFrame with some value(s) for a specified list of wells.

    This is a convenience alternative to `platemap_to_dataframe` for the simple
    case where you want to set some value for a list of wells (and optionally a
    different value for all other wells).

    Parameters
    ----------
    pick_wells : list of str
        Wells to pick
    values : dict
        Values to apply to picked wells
    others : dict
        Values to apply to wells *not* in `pick_wells`
    wells : int, default=96
        number of wells in the plate

    Returns
    -------
    pd.DataFrame
        Metadata for the microplate. Each row corresponds to a single well.
        Columns are the union of all variables mentioned `values` and `others`


    Examples
    --------

    >>> cherrypick(['A1', 'A3'], wells=6)
          Pick
    well
    A1    True
    A2     NaN
    A3    True
    B1     NaN
    B2     NaN
    B3     NaN

    >>> cherrypick(['A1', 'A3'], values={'color':'red'}, others={'color':'green'}, wells=6)
          color
    well
    A1      red
    A2    green
    A3      red
    B1    green
    B2    green
    B3    green

    """

    all_wells = iterate_wells(n=wells, wells=wells)
    other_wells = set(all_wells) - set(pick_wells)

    platemap = dict()
    platemap[','.join(pick_wells)] = values
    platemap[','.join(other_wells)] = others

    df = platemap_to_dataframe(platemap, wells=wells)
    return df

def combine_plate_dataframes(
        layout,
        interleave_rows=False, interleave_columns=False,
        wells_from=96, wells_to=384,
        source_well=None):
    """
    Combines DataFrames for multiple plates into a DataFrame for one larger plate;
    typically four 96-well plates are combined into one 384-well plate, but
    other combinations are possible as long as the layout of smaller plates
    fits in the larger plate.


    Parameters
    ----------
    layout : list of list of pd.DataFrame
        Arrangement of DataFrames. `[[a, b], [c, d]]` will place DataFrame `a`
        in the top left, `b` in the top right, `c` bottom-left, `d` bottom-right.
    interleave_rows: bool, default=False
        True to add 1 row from each source plate before moving on to the next
        row.
    interleave_columns: bool, default=False
        True to add 1 column from each source plate before moving on to the next
        column.
    wells_from : int, default=96
        Dimensions of the starting plates
    wells_to : int, default=384
        Dimensions of the output plate
    source_well : str, optional
        If given, names a new column, which will record the well in the input
        plate(s).

    Returns
    -------
    pd.DataFrame
        Combined DataFrame for the larger plate.

    Examples
    --------

    """
    newspec = {}
    dims_from = plates[wells_from]
    dims_to = plates[wells_to]
    n_plate_rows = len(layout)
    n_plate_cols = len(layout[0])

    # make sure ratio is an integer
    ratio_rows = dims_to[0] // dims_from[0]
    ratio_cols = dims_to[1] // dims_from[1]

    # check that the plates in `layout` fit in the destination plate
    if dims_from[0]*n_plate_rows != dims_to[0]:
        raise Exception("Number of wells in layout (%d wells * %d plates) does not match target plate size (%d rows)".format(dims_from[0], n_plate_rows, dims_to[0]))
    if dims_from[1]*n_plate_cols != dims_to[1]:
        raise Exception("Number of wells in layout (%d wells * %d plates) does not match target plate size (%d rows)".format(dims_from[1], n_plate_cols, dims_to[1]))

    for i, plate_row in enumerate(layout):
        for j, plate in enumerate(plate_row):
            for cell,row in plate.iterrows():
                r, c = cell2tuple(cell)
                if interleave_rows:
                    r = ratio_rows * r + (i % ratio_rows)
                else:
                    r = r + dims_from[0] * i

                if interleave_columns:
                    c = ratio_cols * c + j % ratio_cols
                else:
                    c = c + dims_from[1] * j

                new_cell = tuple2cell(r,c)
                newspec[new_cell] = row
                if source_well is not None:
                    newspec[new_cell][source_well] = cell
    return pd.DataFrame(newspec).transpose()
combine_specs = combine_plate_dataframes



def _map_plate(from_wells, to_wells):
    """private
    """
    mapping = {}
    # make sure ratio is an integer
    ratio = (plates[to_wells][0] // plates[from_wells][0],
             plates[to_wells][1] // plates[from_wells][1])

    for i in range(plates[from_wells][0]):
        for j in range(plates[from_wells][1]):
            mapping[tuple2cell(i,j)] = [tuple2cell(x,y) for x in range(ratio[0]*i, ratio[0]*(i+1)) for y in range(ratio[1]*j, ratio[1]*(j+1))]
    return mapping

_plate_conversion_maps = {
    24:  {  96:  _map_plate(24, 96),   384: _map_plate(24, 384), 1536: _map_plate(24, 1536) },
    96:  {  384: _map_plate(96, 384), 1536: _map_plate(96, 1536)  },
    384: { 1536: _map_plate(96, 1536) }
}


def scale_plate(spec,from_wells,to_wells,include_row_column=True):
    """scale a plate to a larger number of wells by copying data

    Converts a tidy plate dataframe from a `from_wells`-sized plate to a
    `to_wells`-sized plate. For example, you could map data from a 24-well plate

    ===== == == == == == ==
    _     1  2  3  4  5  6
    ===== == == == == == ==
    **A** 1  2  3  4  5  6
    **B** 7  8  9  10 11 12
    **C** 13 14 15 16 17 18
    **D** 19 20 21 22 23 24
    ===== == == == == == ==

    to a 96-well plate by copying each well to 4 wells:

    ===== == == == == == == == == == == == ==
    _     1  2  3  4  5  6  7  8  9  10 11 12
    ===== == == == == == == == == == == == ==
    **A** 1  1  2  2  3  3  4  4  5  5  6  6
    **B** 1  1  2  2  3  3  4  4  5  5  6  6
    **C** 7  7  8  8  9  9  10 10 11 11 12 12
    **D** 7  7  8  8  9  9  10 10 11 11 12 12
    **E** 13 13 14 14 15 15 16 16 17 17 18 18
    **F** 13 13 14 14 15 15 16 16 17 17 18 18
    **G** 19 19 20 20 21 21 22 22 23 23 24 24
    **H** 19 19 20 20 21 21 22 22 23 23 24 24
    ===== == == == == == == == == == == == ==

    The number of rows of a `to_wells`-sized plate must be an integer multiple
    of the number of rows in a `from_wells`-sized plate, and likewise for
    columns (typically the multiple is a power of 4).
    """
    delete_row_column = ('row' in spec.columns or 'column' in spec.columns) and not include_row_column
    try:
        conversion_map = _plate_conversion_maps[from_wells][to_wells]
    except:
        # raise Exception("Do not know how to convert %d-well plate to %d-well plate".format(from_wells,to_wells))
        conversion_map = _plate_conversion_map(from_wells=from_wells, to_wells=to_wells)

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
convert_spec = scale_plate



def scale96to384(spec,**kwargs):
    """
    Converts a DataFrame for a 96-well plate to a DataFrame for a 384-well
    plate. Specific case of :func:`~microplates.data.scale_plate`

    Assumes each well in the 96-well plate is replicated onto 4 wells in a 384-well
    plate; e.g. A1 in 96-well -> A1, A2, B1, B2 in 384-well.

    Parameters
    ----------
    spec : DataFrame
        spec, as returned by ``platemap_to_dataframe``

    include_row_column : bool
        True to include columns named `row` and `column` in the resulting
        data frame, corresponding to the 0-indexed row/column in the original
        microtiter plate.

        If there are already `row`/`column` columns in the DataFrame and:

        * `include_row_column = False`, they will be deleted
        * `include_row_column = True`, they will be replaced with values for
          the 384-well plate

    Returns
    -------
    DataFrame
        spec, as returned by ``platemap_to_dataframe``

    """
    return scale_plate(spec,96,384,**kwargs)
spec96to384 = scale96to384


def fortify_plate(df, inplace=False):
    """Find the column of a microplate DataFrame indicating the wells and move it to the index

    Searches the following in order:
    * If the index is named `well` or `wells` (case insensitive),
      it is renamed to `well`
    * If all element of the index look like well names (e.g. `A1`), index is
      renamed `well`
    * If there is a column named `well` or `wells` (case insensitive), it is
      made the index and renamed `well`
    """
    names = ['well', 'wells']

    if not inplace:
        df = df.copy()

    if df.index.name is not None:
        for name in names:
            if (df.index.name.lower() == name):
                df.index.rename('well', inplace=True)
                return df

    if all(df.index.map(is_well)):
        df.index.rename('well', inplace=True)
        return df

    columns = df.columns.str.lower()
    for name in names:
        if name in columns:
            well_col = df.columns[columns.get_loc(name)]
            df.set_index(well_col, inplace=True)
            df.index.rename('well', inplace=True)
            return df

    raise Exception('Cannot find column identifying the wells; '
    'pd.DataFrame must either have an index containing well-like '
    'strings (e.g. "A1"), or there must be a colum named "well" or '
    '"wells" (case insensitive).')



def add_row_column(df, well_variable='well',
    plate_row_variable='plate_row', plate_col_variable='plate_column', natural=False,
    inplace=False):
    """convert a column of wells (e.g. 'A1') to columns showing physical rows/columns on the microplate

    Each row of the `pd.DataFrame` `df` corresponds to a well of a physical
    microplate. Some column `well_variable` contains well names, e.g. `A1`,
    `G6`, etc. This function column(s) to `df` indicating the physical row/
    column of each well in the microplate.

    Parameters
    ----------
    df : pd.DataFrame
    well_variable : str, default='well'
        Name of the column in `df` containing well names
    plate_row_variable : str, default='plate_row'
        Name of the new column to create, indicating physical row of each well.
        Set to `None` to skip creating this column.
    plate_col_variable : str, default='plate_column'
        Name of the new column to create, indicating physical row of each well
        Set to `None` to skip creating this column.
    natural : bool, default=False
        `True` to name rows `A`, `B`, `C`, etc. and columns `1`, `2`, `3`, etc.
        `False` use 0-based indices for rows and columns (e.g. `A1` = (0,0),
        etc.)
    inplace : bool, default=False
        `True` to update `df` in place, `False` to return a copy

    Returns
    -------
    pd.DataFrame
        Modified DataFrame with new column(s)

    Examples
    --------
    >>> df = pd.DataFrame({'well':['A1','A2','B3'], 'OD600': [0.25, 0.3, 0.21]})
    >>> add_row_column(df)
      well  OD600  plate_row  plate_column
    0   A1   0.25          0             0
    1   A2   0.30          0             1
    2   B3   0.21          1             2


    """
    if natural:
        def row_mapper(x):
            t = cell2tuple(x)
            if t is not None: return row2letters(t[0])
            else: return None
        def col_mapper(x):
            t = cell2tuple(x)
            if t is not None: return t[1]+1
            else: return None
    else:
        def row_mapper(x):
            t = cell2tuple(x)
            if t is not None: return t[0]
            else: return None
        def col_mapper(x):
            t = cell2tuple(x)
            if t is not None: return t[1]
            else: return None

    if not inplace:
        df = df.copy()

    if well_variable is None:
        wells = pd.Series(df.index, index=df.index)
    else: wells = df[well_variable]

    if plate_row_variable is not None:
        df[plate_row_variable] = wells.astype(str).apply(row_mapper)
    if plate_col_variable is not None:
        df[plate_col_variable] = wells.astype(str).apply(col_mapper)
    return df


def pivot_plate(data,parameter='OD600',natural=True):
    """Pivots a tidy DataFrame of microplate data into a DataFrame where rows correspond to physical rows, columns correspond to physical columns, and each value is a single parameter of a well

    Parameters
    ----------
    data : pd.DataFrame
        Tidy dataframe of microplate data
    parameter : str
        Name of the column to contain the well data
    natural : bool, default=False
        True to show plate rows as ``A``, ``B``, ``C``, etc. and columns as
        ``1``, ``2``, ``3``. False to use 0-based indices for both.

    Returns
    -------
    pd.DataFrame
        DataFrame containing one parameter per well, with the index labeled
        according to the physical rows of the microplate, and columns labeled
        by the physical columns of the microplate.

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
    df = fortify_plate(data.copy())
    df = add_row_column(df,natural=natural,well_variable=None)
    return df.pivot(index='plate_row', columns='plate_column', values=parameter)
plate_pivot = pivot_plate


def assign_wells(df, 
    start_wells = None, 
    separate_samples_by = None,
    separate_into = 'plates',
    separate_dataframes_per_plate = False,
    wells=96):
    """arrange rows of a DataFrame onto a plate or plates

    Use `separate_samples_by` and `separate_into` to arrange samples into separate plates or rows. 
    
    For example, in an experiment containing two values for `Phage Library`, `'Alpaca'` and `'Synthetic'`:

        >>> assign_wells(repeat_samples, separate_samples_by = 'Phage Library', separate_into = 'plates')
        # yields a list of DataFrames, one per plate, with one or more plates for 
        #'Alpaca' and one or more for 'Synthetic'.

        >>> assign_wells(repeat_samples, separate_samples_by = 'io', separate_into = 'plates')
        # yields a list of DataFrames, with input samples on a different plate 
        # from output samples.

        >>> assign_wells(repeat_samples, separate_samples_by = 'round', separate_into = 'rows')
        # yields a list of DataFrames, with samples from different rounds on different rows
    
    Parameters
    ----------
    repeat_samples : pd.DataFrame
        samples to repeat; should have columns [separate_samples_by] + sort_by_columns
    start_wells : list of str, optional
        for each plate of repeat samples, which well should they start on? if not given, each plate will start on well A1
    separate_samples_by : str, optional
        if given, separate samples which have different levels for this column, by default 'Phage Library'
    separate_into : str, optional
        how to separate levels of `separate_samples_by`: 
        - 'plate' (default) to place different levels on different plates; 
        - 'rows' to place each level on different rows
        - None to place samples on plate; do not separate by level of `separate_samples_by`. 
    sort_by_columns : list of str, optional
        sort the samples by these values, in order; by default ['Phage Library','Expt','Round','Sample']
    wells : int, optional
        number of wells in each plate, should be one onf 96, 384; by default 96

    Returns
    -------
    list of pd.DataFrame or pd.DataFrame
        if separate_dataframes_per_plate is False: returns a copy of `df`, augmented with columns 'Well' and 'Plate'.
        if separate_dataframes_per_plate is True: returns one DataFrame for each generated plate; each comprised of rows of `df`; each DataFrame also has a column 'Well'.
        
    """

    n_wells = wells
    

    separate_by_levels = df[separate_samples_by].unique()
    separate_groups = [df[df[separate_samples_by] == x].copy() for x in separate_by_levels]
    

    if start_wells is None: start_wells = ['A1' for r in separate_by_levels]


    if separate_into == 'plate':
        # output_plates = []
        
        out = []

        current_plate = 0
        for i, group in enumerate(separate_groups):
            plates, wells = zip(*(plates.utils.iterate_wells(len(group), start = start_wells[i], wells=n_wells, plate=True, start_plate=current_plate)))
            last_plate = max(plates)+1

            group['Well'] = list(wells)
            group['Plate'] = list(plates)

            out.append(group)
            current_plate = last_plate

    elif separate_into == 'row':

        current_well = start_wells[0]

        out = []
        plate = []
        for i, group in enumerate(separate_groups):
            plates, wells = zip(*(plates.utils.iterate_wells(len(group), start = current_well, start_plate=current_plate, wells=n_wells, plate=True)))
            
            group['Well'] = list(wells)
            group['Plate'] = list(plates)
            
            out.append(group)
            current_well, current_plate = next_row(current_well, wells=n_wells, plate=True, start_plate=current_plate)
    else:
        plates, wells = zip(*(plates.utils.iterate_wells(len(group), start = start_wells[0], start_plate=0, wells=n_wells, plate=True)))
        group = df

        group['Well'] = list(wells)
        group['Plate'] = list(plates)

        out = [group]
    
    if separate_dataframes_per_plate:
        out = pd.concat(out)
        output_plates = []
        all_plates = out['Plate'].unique()
        for j in all_plates:
            output_plates.append(group.loc[group['Plate'] == j,:])
        return output_plates
    return pd.concat(out)
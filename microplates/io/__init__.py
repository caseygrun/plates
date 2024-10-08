from ..data import platemap_to_dataframe, scale_plate
import pandas as pd

def read_multiple_plates(tables, read_single, platemap=None, **kwargs):
    """Reads data for one or more plates, then merges the data together.

    This function simplifies reading and data reduction where you have either

    1. multiple plates, each containing separate samples, and/or
    2. each sample has multiple parameters measured (e.g OD600, A450, etc).

    This function produces a ``DataFrame`` where each such ``measure`` (e.g.
    OD600, FITC, A450, etc.) is in a separate column, and each physical well is
    in a single row.

    For each entry in ``table``, this function reads each of the ``measures`` in
    that table and joins those measures horizontally (one measure per column);
    then it concatenates ``table``\ s vertically, such that there is one row per well.

    Each ``dict`` in ``tables`` represents a single plate, which may have multiple
    ``measures``. Each of the ``measures`` will be read and joined by well. The
    union of parameters in each ``measure`` and ``table`` will be passed as
    ``**kwargs`` to ``read_single``.

    Each ``table`` can have several keys which serve special functions. Other
    keys will be passed as ``kwargs`` to ``read_single`` as above

    * ``measures``: list of dicts, each representing a different variable.
      Will be merged with ``table`` (values in the ``measure`` overwrite those
      in the ``table``) and passed as ``**kwargs`` to ``read_single``.
    * ``platemap``: dict containing platemap metadata that will be passed to
      :func:`~microplates.data.platemap_to_dataframe`. The metadata from the ``platemap``
      argument and from this key will be merged
    * ``transform``: function that will be called with the ``DataFrame`` and ``table``,
      and should return a new, possibly modified ``DataFrame``
    * ``scale``: tuple ``(from_wells, to_wells)``; will be used to call
      :func:`data.scale_plate`

    Examples
    --------

    # single plate, multiple measures (OD600, FITC), each measure is in a
    # separate tab of the spreadsheet
    >>> read_multiple_plates([
    ...     { 'io': 'plate1.xlsx', 'measures': [
    ...      { 'sheet_name':'OD600', 'measure':'OD600' },
    ...      { 'sheet_name':'FITC',  'measure':'FITC' }
    ...     ]}
    ... ], read_single = pd.read_excel )

    # multiple plates, in separate excel files
    >>> read_multiple_plates([
    ...     { 'io': 'plate1.xlsx', 'measure':'OD600', 'data': {'plate':1} },
    ...     { 'io': 'plate2.xlsx', 'measure':'OD600', 'data': {'plate':2} }
    ... ], read_single = pd.read_excel )

    # multiple plates in different tabs of the same excel file
    >>> read_multiple_plates([
    ...     { 'sheet_name': 'plate1', 'measure':'OD600', 'data': {'plate':1} },
    ...     { 'sheet_name': 'plate2', 'measure':'OD600', 'data': {'plate':2} }
    ... ], read_single = pd.read_excel, io='plates.xlsx', measure='OD600' )

    # multiple plates in same excel file; can read using a function from
    # a submodule of microplates.io:
    >>> read_multiple_plates([
    ...         { 'sheet_name': 'plate1', 'measure':'OD600', 'data': {'plate':1} },
    ...         { 'sheet_name': 'plate2', 'measure':'OD600', 'data': {'plate':2} }
    ...     ],
    ...     read_single=microplates.io.tecan.read_single,
    ...     path='plates.xlsx', measure='OD600' )


    Parameters
    ----------
    tables : list of dicts
        See examples
    read_single : function
        Function to read a single plate. Generally will be a function from
        the `io` submodule. The values for a single `measure` or `table` will
        be used as `**kwargs` for `read_single`
    platemap : dict
        Platemap; will be evaluated by `data.platemap_to_dataframe` and joined
        to each `table`
    **kwargs : dict, optional
        Additional arguments will be merged into each ``table``, with values
        from the ``table`` overwriting those in ``**kwargs``.

    Returns
    -------
    int
        Description of anonymous integer return value.

    """
    dfs = []

    special_keys = set(["data","measures","transform","platemap","convert"])

    if platemap is None:
        platemap = {}
    platemap = platemap_to_dataframe(platemap)

    # for each file
    for table in tables:
        table = {**kwargs, **table}

        # extract metadata to add as constant column
        if "data" in table:
            table_metadata = table["data"]
        else:
            table_metadata = {}

        # if multiple tables are included in the file
        if "measures" in table:
            measures = table["measures"]
        else:
            measures = [table]

        # if there is a function to modify this table, extract it
        if "transform" in table:
            transform = table["transform"]
        else:
            transform = None

        # if there is a per-table platefile, grab it
        if "platemap" in table:
            table_platemap = table["platemap"]
        else:
            table_platemap = {}

        table_platemap = platemap_to_dataframe(table_platemap)

        # if instructions to broadcast the per-table mapfile from
        # one microplate shape to another (e.g. 96 to 384), do the conversion
        if "scale" in table:
            convert_from, convert_to = table["scale"]

            table_platemap = scale_plate(table_platemap, convert_from, convert_to)

        table = {x: table[x] for x in table if x not in special_keys}

        # for each table in the file
        measure_dfs = []
        for measure in measures:
            measure = {x: measure[x] for x in measure if x not in special_keys}
            
            measure_df = read_single(**{ **table, **measure })
            measure_dfs.append(measure_df)

        # concatenate different tables in this file, matching the wells
        df = pd.concat(measure_dfs, join='inner', axis=1)
        df = pd.merge(left=table_platemap, right=df, left_index=True, right_index=True)

        # apply variables given for the whole table
        for col in table_metadata:
            # create any columns that don't exist
            if col not in df:
                df[col] = table_metadata[col]
        df = df.fillna(table_metadata)

        # apply an arbitrary transformation
        if transform is not None:
            df = transform(df, table)

        dfs.append(df.reset_index())
    data = pd.concat(dfs, join='outer', ignore_index=True).set_index('well')
    # data = pd.merge(left=platemap, right=data, left_index=True, right_index=True)
    data = data.join(platemap)
    return data

from __future__ import division
import inspect

import pandas as pd
import numpy as np



def calc_norm(df, value='OD600', on='conc', columns=[], how=None):
    """
    Normalizes the `value` of some column by a particular column `on`,
    using a transformation function `how`. See examples.

    Parameters
    ----------

    df : DataFrame
        data to normalize
    value : str
        name of the column to be normalized; this should be the column you wish to change
    columns : str[]
        list of columns by which to group the data. Each unique combination of values in
        these columns will be treated as a separate group and passed to the normalization
        function `how`
    how : function(column, names, group)
        accepts a single group of values, with index set to the columns given by `on`.
        Should return a modified array of the same shape, with the normalization applied.
        Optionally, can accept additional arguments `names` and `group`:
        - `names` will be a pd.Series giving the name(s) of the group
        - `group` will be all values of the group (not just those given by `on`)
    on : str
        Name of a column which should be used to set the index in the normalization
        function `how`.

    Returns
    -------
    df : pd.DataFrame
        same shape as input, but with transformation applied.


    Examples
    --------

    Normalize to the zero timepoint for each concentration

    >>> df = pd.DataFrame([
    ...     ('A1', 0.004, 0, 10),
    ...     ('A2', 0.005, 0, 100),
    ...     ('A1', 0.022, 1, 10),
    ...     ('A2', 0.027, 1, 100),
    ... ], columns=('well','OD600','time','concentration'))
    >>> calc_norm(df,
            value='OD600',
            on='time',
            columns=['time','concentration'],
            how=lambda x: x - x.loc[0])
       time well  OD600  concentration
    0     0   A1  0.000             10
    1     0   A2  0.000            100
    2     1   A1  0.022             10
    3     1   A2  0.019            100


    Normalize to the value at concentration = 10 for each timepoint

    >>> calc_norm(df,
    ...     value='OD600',
    ...     on='concentration',
    ...     columns=['time','concentration'],
    ...     how=lambda x: x - x.loc[10])
       concentration well  OD600  time
    0             10   A1  0.000     0
    1            100   A2  0.001     0
    2             10   A1  0.000     1
    3            100   A2  0.005     1


    Normalize to the average of the measurements at time = 0

    >>> df = pd.DataFrame([
    ...     ('A1', 0.004, 0, 10),
    ...     ('A2', 0.002, 0, 10),
    ...     ('A3', 0.003, 0, 10),
    ...     ('A1', 0.044, 1, 10),
    ...     ('A2', 0.042, 1, 10),
    ...     ('A3', 0.043, 1, 10),
    ... ], columns=('well','OD600','time','concentration'))
    >>> calc_norm(df,
    ...     value='OD600',
    ...     on='time',
    ...     columns=['time','concentration'],
    ...     how=lambda x: x - x.loc[0].mean())
       time well         OD600  concentration
    0     0   A1  1.000000e-03             10
    1     0   A2 -1.000000e-03             10
    2     0   A3 -4.336809e-19             10
    3     1   A1  4.100000e-02             10
    4     1   A2  3.900000e-02             10
    5     1   A3  4.000000e-02             10

    """
    cols = columns

    # group by all other columns
    if isinstance(on, list) or isinstance(on, tuple):
        cols = list(set(cols) - set(on))
    else:
        if on in cols:
            cols.remove(on)

    # index by the column we want to normalize on
    df = df.copy().set_index(on)

    # # select the column whose value we're interested in normalizing. Iterate
    # # across all groups (e.g. all combinations of values for all other
    # # columns), and apply the transformation. Usually the transformation will
    # # be e.g. to subtract the first column
    # df[value] = df.groupby(cols)[value].transform(how)

    # # restore the index
    # return df.reset_index()

    how_signature = inspect.signature(how)
    if len(how_signature.parameters) == 1:
        transform = lambda column, name, group: how(column)
    elif len(how_signature.parameters) == 2:
        transform = lambda column, name, group: how(column, name)
    elif len(how_signature.parameters) > 2:
        transform = how

    # store transformed DataFrames
    new_dfs = []

    for name,group in df.groupby(cols):

        # `name` is a tuple of values in the same order as `cols`
        # e.g. cols=['primer','RT','strain']
        #      name=('rplU','+','PAO1')
        # convert to a series to make it easier to access
        if len(cols) == 1:
            name_series = pd.Series([name],cols)
        else:
            name_series = pd.Series(list(name),cols)

        # `group[value]` is a DataFrame indexed by `on`, with a single column `value`
        res = transform(group[value], name=name_series, group=group)  #how(group[value], name=name_series, group=group)

        # merge changed values of the group returned by the transformation function
        row = pd.DataFrame(res).combine_first(group).reset_index()
        new_dfs.append(row)

    # concatenate transformed DataFrames
    return pd.concat(new_dfs)


def normalize(df, value='OD600', on='conc', groupby=[], how=lambda x: x - x.loc[0.0], **kwargs):
    """
    Normalizes the `value` of some column using a transformation function `how`.


    Example: Normalize OD600 to the value at time = 0:

        normalize(df, value='OD600', groupby=['strain','well'], on='time', how=lambda x,n,g: x - x.loc[0])


    """
    return calc_norm(df, value=value, on=on, columns=groupby, how=how, **kwargs)
    # cols = groupby
    #
    # # group by all other columns
    # if isinstance(on, list) or isinstance(on, tuple):
    #     cols = list(set(cols) - set(on))
    # else:
    #     if on in cols:
    #         cols.remove(on)
    #
    # # index by the column we want to normalize on
    # df = df.copy().set_index(on)
    #
    #
    # # store transformed DataFrames
    # new_dfs = []
    #
    # for name,group in df.groupby(cols):
    #
    #     # `name` is a tuple of values in the same order as `cols`
    #     # e.g. cols=['primer','RT','strain']
    #     #      name=('rplU','+','PAO1')
    #     # convert to a series to make it easier to access
    #     name_series = pd.Series(list(name),cols)
    #
    #     # `group[value]` is a DataFrame indexed by `on`, with a single column `value`
    #     res = how(group[value], name=name_series, group=group)
    #
    #     # merge changed values of the group returned by the transformation function
    #     row = pd.DataFrame(res).combine_first(group).reset_index()
    #     new_dfs.append(row)
    #
    # # concatenate transformed DataFrames
    # return pd.concat(new_dfs)

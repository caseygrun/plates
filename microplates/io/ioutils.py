import pandas as pd

def find_header_row(path=None, search=["<>"], keep='first', read=pd.read_excel, df=None, **kwargs):
    """Finds the first row matching a particular pattern in an spreadsheet file

    Parameters
    ----------
    path : str, optional
        Path to spreadsheet file, will be passed to `read`
    search : list of str
        Pattern to look for in the header row
    keep : str, default='first'
        'first' to return the index of the first row that matches `search`, or
        'all' to return a list of indices that match
    read : function, default=pd.read_excel
        Function to read the spreadsheet; will be called with `path` and `**kwargs`
    df : pd.DataFrame, optional
        Spreadsheet to read directly; can be given in place of `path`

    Returns
    -------
    int or list of int
        Index/indices of header rows that match `search`
    """
    if isinstance(search, str):
        search = [search]
    search = tuple(search)

    headers = []

    if df is None:
        if path is None or read is None:
            raise Exception("Must provide either `df` or `path`")
        df = read(path, **kwargs)

    for row in df.itertuples():
        if row[1:(1+len(search))] == search:
            headers.append(row[0])
            break
    assert len(headers) > 0, ("Unrecognized data format; could not find "+
        "an appropriate header in Excel file "+path)

    if keep == 'first':
        return headers[0]
    elif keep == 'last':
        return headers[-1]
    else:
        return headers

import pandas as pd

def find_header_row(path, search=["<>"], keep='first', **kwargs):
    if isinstance(search, str):
        search = [search]
    search = tuple(search)

    headers = []
    df = pd.read_excel(path, **kwargs)
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

import pandas as pd
from ..utils import row2letters
from .ioutils import find_header_row

def read_single(path,header=None,nrows=8,measure='OD600',blank=None, **kwargs):
    if header is None: header = find_header_row(path, search=["Raw Data"], **kwargs)
    df = pd.read_excel(path, skiprows=header+1, nrows=nrows, **kwargs)

    df.index = [row2letters(r) for r in df.index]
    df.index.rename('row',inplace=True)
    df.columns = [str(i+1) for i,r in enumerate(df.columns)]
    df.columns.rename('column',inplace=True)
    df = df.reset_index()
    df = df.melt(id_vars=['row'],var_name='column', value_name=measure).reset_index()

    df['well'] = df['row'] + df['column'].map(str)
    df = df.set_index('well')
    df = df.drop(columns=['row','column','index'])

    return df

import pandas as pd
from microplates.io import *

def test_read_multiple_plates():
    def read_single(io, measure='OD600', **kwargs):
        df = pd.DataFrame([
            ('A1', 0.004),
            ('A2', 0.002),
            ('A3', 0.003)
        ], columns=('well',measure))
        return df.set_index('well')

    # each measure is in a separate spreadsheet
    #        OD600   FITC
    # well
    # A1    0.004  0.004
    # A2    0.002  0.002
    # A3    0.003  0.003
    df = read_multiple_plates([
        { 'io': 'plate1.xlsx', 'measures': [
            { 'sheet_name':'OD600', 'measure':'OD600' },
            { 'sheet_name':'FITC',  'measure':'FITC' }
        ]}
        ], read_single = read_single )
    assert(sorted(df.columns) == sorted(['OD600', 'FITC']))
    assert (df['OD600'] == df['FITC']).all()


    # # multiple plates, in separate excel files
    df = read_multiple_plates([
         { 'io': 'plate1.xlsx', 'measure':'OD600', 'data': {'plate':1} },
         { 'io': 'plate2.xlsx', 'measure':'OD600', 'data': {'plate':2} }
    ], read_single = read_single )
    assert(sorted(df.columns) == sorted(['OD600', 'plate']))
    assert(all(df.loc[df['plate'] == 1, 'OD600'] == df.loc[df['plate'] == 2, 'OD600']))

    # multiple plates in same excel file
    df = read_multiple_plates([
        { 'sheet_name': 'plate1', 'measure':'OD600', 'data': {'plate':1} },
        { 'sheet_name': 'plate2', 'measure':'OD600', 'data': {'plate':2} }
    ], read_single = read_single, io='plates.xlsx', measure='OD600' )
    assert(sorted(df.columns) == sorted(['OD600', 'plate']))
    assert(all(df.loc[df['plate'] == 1, 'OD600'] == df.loc[df['plate'] == 2, 'OD600']))

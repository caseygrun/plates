from microplates.data import *

def test_platemap_to_dataframe():

    s = platemap_to_dataframe({'A1:A2':{ 'strain': 'B. theta' }})
    assert s.loc['A1','strain'] == s.loc['A2','strain'] == 'B. theta'

    s = platemap_to_dataframe({'A1,A2':{ 'strain': 'B. theta' }})
    assert s.loc['A1','strain'] == s.loc['A2','strain'] == 'B. theta'

    s = platemap_to_dataframe({'A1:A2':{ 'strain': [['B. theta','C. diff']] }})
    assert s.loc['A1','strain'] == 'B. theta'
    assert s.loc['A2','strain'] == 'C. diff'

    s = platemap_to_dataframe({'F12:G12':{ 'conc': [[0],[10]] }})
    assert s.loc['F12','conc'] == 0
    assert s.loc['G12','conc'] == 10

    s = platemap_to_dataframe({'B1:C2':{ 'conc': [[0,1],[2,3]] }})
    assert s.loc['B1','conc'] == 0
    assert s.loc['B2','conc'] == 1
    assert s.loc['C1','conc'] == 2
    assert s.loc['C2','conc'] == 3


    s = platemap_to_dataframe({'B1:C2,E1:F2':{ 'conc': [[0,1],[2,3]] }})
    assert s.loc['B1','conc'] == s.loc['E1','conc'] == 0
    assert s.loc['B2','conc'] == s.loc['E2','conc'] == 1
    assert s.loc['C1','conc'] == s.loc['F1','conc'] == 2
    assert s.loc['C2','conc'] == s.loc['F2','conc'] == 3

    s = platemap_to_dataframe({'G7:G10':{ 'conc': 5 }})
    assert s.loc['G9','conc'] == 5


def test_spec96to384():

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


def test_cherrypick():

    df = cherrypick(['A1', 'A3'], wells=6)
    assert df.loc['A1','Pick'] == True
    assert df.loc['A3','Pick'] == True
    assert df.loc[:,'Pick'].sum() == 2

    df = cherrypick(['A1', 'A3'], values={'color':'red'}, others={'color':'green'}, wells=6)
    assert df.loc['A1','color'] == df.loc['A3','color'] == 'red'
    assert (df['color'] == 'green').sum() == 4
    #       color
    # well
    # A1      red
    # A2    green
    # A3      red
    # B1    green
    # B2    green
    # B3    green

def test_add_row_column():

    df = pd.DataFrame({'well':['A1','A2','B3'], 'OD600': [0.25, 0.3, 0.21]}).dropna()
    df2 = add_row_column(df, natural=False)
    #   well  OD600  plate_row  plate_column
    # 0   A1   0.25          0             0
    # 1   A2   0.30          0             1
    # 2   B3   0.21          1             2

    assert 'plate_row' in df2.columns
    assert 'plate_column' in df2.columns

    df2 = df2.set_index('well')
    assert df2.loc['A1','plate_row'] == 0
    assert df2.loc['A1','plate_column'] == 0
    assert df2.loc['A2','plate_row'] == 0
    assert df2.loc['A2','plate_column'] == 1
    assert df2.loc['B3','plate_row'] == 1
    assert df2.loc['B3','plate_column'] == 2

    df = df.set_index('well')
    df2 = add_row_column(df, well_variable=None, natural=False)
    assert df2.loc['A1','plate_row'] == 0
    assert df2.loc['A1','plate_column'] == 0
    assert df2.loc['A2','plate_row'] == 0
    assert df2.loc['A2','plate_column'] == 1
    assert df2.loc['B3','plate_row'] == 1
    assert df2.loc['B3','plate_column'] == 2

    df2 = add_row_column(df, well_variable=None, natural=True)
    assert df2.loc['A1','plate_row'] == 'A'
    assert df2.loc['A1','plate_column'] == 1
    assert df2.loc['A2','plate_row'] == 'A'
    assert df2.loc['A2','plate_column'] == 2
    assert df2.loc['B3','plate_row'] == 'B'
    assert df2.loc['B3','plate_column'] == 3

def test_fortify_plate():
    # there is a column called 'well'
    df = pd.DataFrame({'well':['A1','A2','A3','B1','B2','B3'], 'OD600': [0.25, 0.3, 0.21, 0.25, 0.3, 0.21], 'strain': ['Pa'] * 6}).dropna()
    df2 = fortify_plate(df)
    # .      OD600 strain
    # well
    # A1     0.25     Pa
    # A2     0.30     Pa
    # A3     0.21     Pa
    # B1     0.25     Pa
    # B2     0.30     Pa
    # B3     0.21     Pa
    assert df2.index.name == 'well'
    assert all(df2.index == ['A1','A2','A3','B1','B2','B3'])
    assert set(df2.columns) == {'OD600', 'strain'}

    # the index is called 'wells'
    df = pd.DataFrame({'wells':['A1','A2','A3','B1','B2','B3'], 'OD600': [0.25, 0.3, 0.21, 0.25, 0.3, 0.21], 'strain': ['Pa'] * 6}).dropna()
    df = df.set_index('wells')
    df2 = fortify_plate(df)

    assert df2.index.name == 'well'
    assert all(df2.index == ['A1','A2','A3','B1','B2','B3'])
    assert set(df2.columns) == {'OD600', 'strain'}

    # wells are in the index but not named
    df = pd.DataFrame({'foo':['A1','A2','A3','B1','B2','B3'], 'OD600': [0.25, 0.3, 0.21, 0.25, 0.3, 0.21], 'strain': ['Pa'] * 6}).dropna()
    df = df.set_index('foo')
    df2 = fortify_plate(df)

    assert df2.index.name == 'well'
    assert all(df2.index == ['A1','A2','A3','B1','B2','B3'])
    assert set(df2.columns) == {'OD600', 'strain'}

def test_plate_pivot():
    df = pd.DataFrame({'well':['A1','A2','A3','B1','B2','B3'], 'OD600': [0.25, 0.3, 0.21, 0.25, 0.3, 0.21]}).dropna()
    df2 = plate_pivot(df)
    # plate_column     1    2     3
    # plate_row
    # A             0.25  0.3  0.21
    # B             0.25  0.3  0.21
    assert all(df2.columns == [1, 2, 3])
    assert all(df2.index == ['A', 'B'])
    assert all(df2.loc['A',:] == df2.loc['B',:])
    assert all(df2.loc['A',:] == [0.25,  0.3,  0.21])

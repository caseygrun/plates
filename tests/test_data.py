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

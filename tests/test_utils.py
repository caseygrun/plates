from microplates.utils import *

def test_itertuples():
    assert list(itertuples((0,0),(0,2))) == [(0,0),(0,1),(0,2)]
    assert list(itertuples((1,0),(2,0))) == [(1,0),(2,0)]
    assert list(itertuples((1,0),(2,1))) == [(1,0),(1,1),(2,0),(2,1)]
    assert list(itertuples((1,0),(2,1), by='column')) == [(1,0),(2,0),(1,1),(2,1)]

def test_letters2row():
    assert letters2row('A') == 0
    assert letters2row('H') == 7
    assert letters2row('G') == 6
    assert letters2row('AA') == 26
    assert letters2row('AB') == 27
    assert letters2row('BA') == 52

def test_cell2tuple():
    assert cell2tuple('A1') == (0,0)
    assert cell2tuple('H10') == (7,9)
    assert cell2tuple('G11') == (6,10)
    assert cell2tuple('AA1') == (26,0)
    assert cell2tuple('AB10') == (27,9)
    assert cell2tuple('BA12') == (52,11)

def test_is_cell():
    assert is_cell('A1')
    assert is_cell('F12')
    assert is_cell('BC256')
    assert not is_cell('H 12')
    assert not is_cell('5S')

def test_row2letters():
    assert row2letters(7) == 'H'
    assert row2letters(27) == 'AB'
    assert row2letters(55) == 'BD'

def test_tuple2cell():
    assert tuple2cell(7,9) == 'H10'
    assert tuple2cell(27,9) == 'AB10'
    assert tuple2cell(55,11) == 'BD12'

def test_range2cells():
    assert range2cells('A1:B1') == range2cells('B1:A1') == ('A1', 'B1')
    assert range2cells('A:B') == ('A1', 'B12')
    assert range2cells('A:A') == ('A1','A12')
    assert range2cells('B:D') == ('B1','D12')
    assert range2cells('C:B') == ('B1','C12')
    assert range2cells('1:1') == ('A1','H1')
    assert range2cells('1:3') == ('A1','H3')
    assert range2cells('A11:A12') == ('A11','A12')
    assert range2cells('2:10') == range2cells('10:2') == ('A2','H10')
    assert range2cells("A:A",wells=384) == ("A1","A24")
    assert range2cells("I:I",wells=384) == ("I1","I24")
    assert range2cells("23:23",wells=384) == ("A23","P23")

def test_range2tuple():
    assert range2tuple('A1:C10') == range2tuple('C10:A1') == ((0,0),(2,9))
    assert range2tuple('G7:G10') == range2tuple('G10:G7') == ((6,6),(6,9))
    assert range2tuple("A:A",wells=384) == ((0,0),(0,23))

def test_range2cell_list():
    assert range2cell_list('A1:A2') == ['A1','A2']
    assert range2cell_list('A1:B2') == ['A1','A2','B1','B2']
    assert range2cell_list('A1:B2', by='column') == ['A1','B1','A2','B2']

def test_iterwells():
    assert list(iterwells(2,start='H12')) == ['H12', 'A1']
    assert list(iterwells(13)) == ['A1','A2','A3','A4','A5','A6','A7','A8','A9','A10','A11','A12','B1']
    assert list(iterwells(9)) == ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9']

def test_infer_plate_size():
    assert infer_plate_size(['H12']) == infer_plate_size(['A1','H12']) == infer_plate_size(range2cell_list('A1:H12')) == 96
    assert infer_plate_size(['H13']) == 384
    assert infer_plate_size(['A6'], all=True) == [24, 48, 96, 384, 1536]

    assert infer_plate_size(['A6'], prefer=96) == 96
    assert infer_plate_size(['A6'], prefer=384) == 384

# plates
Tidy data from microplate data

This package lets you process concise descriptions of [microplate](https://en.wikipedia.org/wiki/Microtiter_plate) map metadata into pandas `DataFrame`s; then you can join your dataset to the plate map to get a tidy dataset. 

## Examples

```ipython    
>>> import plates
>>> platemap = plates.prog2spec({'A1:A2':{ 'strain': 'B. theta' }})
>>> platemap
       strain
A1   B. theta
A2   B. theta
A3        NaN
...
H12       NaN
[96 rows x 1 columns]

>>> df = pd.read_excel('data.xlsx')
>>> df = pd.DataFrame([
        ('A1', 0.001, 0),
        ('A2', 0.001, 0),
        ('A1', 0.011, 1),
        ('A2', 0.012, 1),
        ('A1', 0.023, 2),
        ('A2', 0.025, 2),
        ('A1', 0.048, 3),
        ('A2', 0.051, 3)
    ], columns=('well', 'OD600', 'time'))

>>> pd.merge(df,platemap, how='inner',left_on='well',right_index=True).dropna()
  well  OD600  time    strain
0   A1  0.001     0  B. theta
2   A1  0.011     1  B. theta
4   A1  0.023     2  B. theta
6   A1  0.048     3  B. theta
1   A2  0.001     0  B. theta
3   A2  0.012     1  B. theta
5   A2  0.025     2  B. theta
7   A2  0.051     3  B. theta
```

```
>>> plates.prog2spec({'A1:A2':{ 'strain': [['B. theta','C. diff']] }})
      strain
A1   B. theta
A2    C. diff
A3        NaN
...
H12       NaN
[96 rows x 1 columns]
```

```
>>> plates.prog2spec({'B1:C2,E1:F2':{ 'conc': [[0,1],[2,3]] }}).dropna()
    conc
B1   0.0
B2   1.0
C1   2.0
C2   3.0
E1   0.0
E2   1.0
F1   2.0
F2   3.0
```
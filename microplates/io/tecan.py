import pandas as pd
from .ioutils import melt_plate

def read_single(path,header=None,nrows=8,measure='OD600',blank=None, **kwargs):
    
    # try to guess the header row if not provided
    if header is None:
        df = pd.read_excel(path, **kwargs)
        try:
            header = [row[1] for row in df.itertuples()].index("<>")+1
        except ValueError as e:
            raise Exception("Unrecognized data format; could not find "+
            "an appropriate header in Excel file "+path+". \n"+repr(kwargs))

    # read raw data from excel file, excluding prefix at beginning of file
    # and suffix at end
    df = pd.read_excel(path,header=header,index_col=0,nrows=nrows, na_values=['OVER'], **kwargs)

    assert df.index.name == "<>", ("Unrecognized data format; make sure `header` is set "+
                                  "to the row right above '<>' in Excel file "+path+". header = "+str(header))

    df = melt_plate(df, measure=measure)

    # # data will be an array mirroring the layout of the physical microtiter plate
    # # `index` will be the rows, `columns` will be the physical column, and values
    # # are OD600
    # df.index.rename('row',inplace=True)
    # df.columns.rename('column',inplace=True)
    # df = df.reset_index()

    # # convert dataframe from "wide" to "long" format (one well per row)
    # df = df.melt(id_vars=['row'],var_name='column',value_name=measure).reset_index()

    # # generate a column showing the well name (e.g. A1) from column and row
    # df['well'] = df['row'] + df['column'].map(str)
    # df = df.set_index('well')
    # df = df.drop(columns=['row','column','index'])

    # subtract and drop the blank well if given
    if blank is not None:
        df[measure] = df[measure] - df.loc[blank, measure]
        df = df.drop(index=blank)
    return df

def read_multiple(path,header=None,nrows=96,measure='OD600',blank=None,na_values=['OVER'],npositions=None,**kwargs):

    if header is None:
        df = pd.read_excel(path,**kwargs)
        for row in df.itertuples():
            if row[1] == "Well":
                header = row[0]+1
                break
        assert header is not None, ("Unrecognized data format; could not find "+
            "an appropriate header in Excel file "+path)

    # read raw data from excel file, excluding prefix at beginning of file
    # and suffix at end
    if npositions is not None:
        kwargs['parse_cols'] = npositions+2
    df = pd.read_excel(path,header=header,index_col=0,nrows=nrows, **kwargs)

    assert df.index.name == "Well", ("Unrecognized data format; make sure `header` is set "+
                                  "to the row right above '<>' in Excel file "+path)

    # collect data into "tidy" format, with one row per observation, one column for each variable (well, time, OD600)
    df.columns = df.columns.rename('position')
    df = df.drop(columns=["Mean","StDev"])
    df.index = df.index.rename('well')
    df = df.reset_index()
    df = df.melt(id_vars=['well'],value_name=measure)

    # subtract and drop the blank well if given
    if blank is not None:
        df[measure] = df[measure] - df.loc[blank, measure].mean()
        df = df.drop(index=blank)
    return df


def read_timecourse(path,header=None,platemap=None,**kwargs):
    if header is None:
        df = pd.read_excel(path)
        for row in df.itertuples():
            if row[1] == "Time [s]":
                header = row[0]+1
                break
        assert header is not None, ("Unrecognized data format; could not find "+
            "an appropriate header in Excel file "+path)

    data = pd.read_excel(path,
                  sheet_name=0, header=header, skip_footer=4, index_col=0)

    # Extract temperature vs. time as separate variable
    temps = data.loc['Temp. [°C]',:]
    # times = data.loc['Time']

    data = data.drop('Temp. [°C]')

    # collect data into "tidy" format, with one row per observation, one column for each variable (well, time, OD600)
    data.columns = data.columns.rename('time')
    data.index = data.index.rename('well')
    data = data.reset_index()
    data = data.melt(id_vars=['well'],value_name='OD600')

    # for each combination of (time, strain, NO3), subtract the OD600 of the concentration = 0, no inoculum well
    #data = plates.calc_norm(data,value='OD600',on='strain',columns=['time','strain','NO3'],
    #          how=lambda x: x - x.loc['none'].mean())

    # convert time series data from seconds to hours
    data['time'] = data['time']/3600.0
    data = data.fillna(value={'sterile':0})

    return data

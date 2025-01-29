import inflection

def snake_case(df):
    cols_old = df.columns.to_list()
    snakecase = lambda x: inflection.underscore(x)
    cols_new = map(snakecase, cols_old)
    df.columns = cols_new
    return df


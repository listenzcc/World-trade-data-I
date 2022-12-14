# %%
import pandas as pd

import plotly.express as px
import plotly.graph_objects as go

from pathlib import Path
from tqdm.auto import tqdm

# %%
input_folder = Path('../wits_en_trade_summary_allcountries_allyears')

records = []

# Collect
for csvFile in tqdm(input_folder.iterdir(), 'Iter csv files'):
    if not csvFile.is_file():
        continue

    df_raw = pd.read_csv(csvFile, encoding='gbk')

    df = df_raw[df_raw['Indicator'].map(lambda e: any([
        e == 'Trade (US$ Mil)-Top 5 Export Partner',
        e == 'Trade (US$ Mil)-Top 5 Import Partner'
    ]))]

    if len(df) == 0:
        continue

    df = df[['Reporter', 'Partner', 'Indicator Type', '2019']]
    df = df.dropna()
    df['fileName'] = csvFile.name

    records.append(df)

# Summary
df = pd.concat(records)

for col in ['Reporter', 'Partner', 'Indicator Type']:
    df[col] = df[col].map(lambda e: e.strip())

ignores = ['World', 'Unspecified']

for ign in ignores:
    df = df[df['Reporter'] != ign]
    df = df[df['Partner'] != ign]

full_df = df

full_df

# %%

export_df = full_df[full_df['Indicator Type'] ==
                    'Export'].sort_values(by='2019', ascending=False)
export_df

# %%

import_df = full_df[full_df['Indicator Type'] ==
                    'Import'].sort_values(by='2019', ascending=False)
import_df

# %%


def search_iter(df, rootReporter, results, level=0, maxLevel=3):
    '''
    Be ware it is an iterative function,
    make sure it ends properly.

    Search the df iteratively,
    the searching starts with the rootReporter,
    and stops with the maxLevel specified

    Args:
        :param: df: The raw dataframe to search in;
        :param: rootReporter: The reporter to be started with;
        :param: level: The current level;
        :param: maxLevel: The maximum level, default by 3;
        :param: results: A hash table containing the history step,
                         it is where the results are restored,
                         it also prevents the searching from being trapped in the loop.
    '''

    # maxLevel is reached
    if level > maxLevel:
        return

    # Select reporter
    select = df.query('Reporter == "{}"'.format(rootReporter))

    # Record partners
    furtherSearches = []
    for partner in select['Partner']:
        # Do nothing if exists
        if partner in results:
            continue

        # New partner found
        results[partner] = (level, results.get(
            rootReporter, (-1, []))[1] + [rootReporter])
        furtherSearches.append(partner)

    # Iterate searching
    for partner in furtherSearches:
        # Next searching
        search_iter(df, partner, results, level=level+1, maxLevel=maxLevel)

    return


def results_to_df(results, columns=dict()):
    '''
    Turn the results above into the dataframe,
    it is also sorted by level.

    Args:
        :param: results: The searching results;
        :param: columns: The columns to be added.

    Returns:
        :return: df: The sorted dataframe
    '''

    lst = []
    for key, value in results.items():
        lst.append([key, value[0], value[1]])

    df = pd.DataFrame(sorted(lst, key=lambda e: e[1]), columns=[
                      ['name', 'level', 'chain']])

    for key, value in columns.items():
        if key in df.columns:
            print('W: Can not add col: {}:{}'.format(key, value))
        df[key] = value

    return df

# %%


default_colormap = px.colors.sequential.Cividis_r


def mk_sankey_data(df, colormap=default_colormap):
    '''
    Prepare sankey data from df

    Args:
        :param: df: The input dataframe, it is generated by the results_to_df function in above;
        :param: colormap: The colormap, default by default_colormap.

    Returns:
        :return: label, color, source, target, value: The requirements of plotly Sankey graph, see https://plotly.com/javascript/sankey-diagram/#basic-sankey-diagram
        :return: root: The root country name.
    '''

    # Generate links
    links = dict()
    color_table = dict()

    root = df.iloc[0]['root']
    for i in range(len(df)):
        se = df.iloc[i]
        name = se['name']

        # if name == root:
        #     continue

        chain = [e for e in se['chain']]
        chain.append(name)

        level = se['level']
        color_table[name] = colormap[int(level) % len(colormap)]

        for i, n in enumerate(chain):
            if i == 0:
                continue

            m = chain[i-1]

            links[m] = links.get(m, dict())
            links[n] = links.get(n, dict())
            links[m][n] = links[m].get(n, 0)
            links[m][n] += 1

    # Generate label and color
    # Generate source, target and value

    label = [k for k in links]
    color = [e for e in label]

    for i, lb in enumerate(label):
        if lb == root:
            color[i] = colormap[0]
            continue
        color[i] = color_table[lb]

    source = []
    target = []
    value = []

    for src, a in links.items():
        for tar, val in a.items():
            source.append(label.index(src))
            target.append(label.index(tar))
            value.append(val)

    return label, color, source, target, value, root


# Display the sankey data
def mk_sankey_fig(label, color, source, target, value, title):
    '''
    Make sankey figure from inputs

    Args:
        :param: label, color, source, target, value: The sankey data generated by the mk_sankey_data;
        :param: title: The figure title

    Return:
        :return: fig: The figure.
    '''
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=label,
            color=color,
        ),
        link=dict(
            source=source,
            target=target,
            value=value
        ))])

    fig.update_layout(title_text=title, font_size=10)

    return fig

# %%


inp_df_dict = dict(
    Import=import_df,
    Export=export_df
)


def work_load(country, trade):
    '''
    It is C styled programming,
    make the space in results, and fill it with iterative searching,
    and convert the results into sorted dataframe
    '''
    results = dict()

    inp_df = inp_df_dict.get(trade, None)

    if inp_df is None:
        return None, None

    search_iter(inp_df, country, results, level=1, maxLevel=100)

    trace_df = results_to_df(results, dict(root=country, trade=trade))

    label, color, source, target, value, root = mk_sankey_data(trace_df)

    fig = mk_sankey_fig(label, color, source, target, value,
                        '{}, ({}), ({})'.format(country, trade, len(label)))

    return dict(fig=fig, df=trace_df)


countries = sorted(set(full_df['Reporter'].values))
trades = [k for k in inp_df_dict]

# %%
if __name__ == '__main__':
    # ---------------------------------------
    # Input
    country = 'China'
    trade = 'Export'

    # ---------------------------------------
    # Workload
    output = work_load(country, trade)

    # ---------------------------------------
    # Output
    output['fig'].show()
    output['trace_df']

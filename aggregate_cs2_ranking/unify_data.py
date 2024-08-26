import os
from datetime import date
import shutil
from .import_data import filefolder_exists
import pandas as pd
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

def get_raw_data():
    path = 'imported/'
    hltv = pd.read_pickle(path + 'hltv_raw.pkl')
    esl = pd.read_pickle(path + 'esl_raw.pkl')
    valve = pd.read_pickle(path + 'valve_raw.pkl')

    return hltv, esl, valve


def copy_to_date_folder(force=False):
    date_string = str(date.today()).replace('-', '')
    if force or not filefolder_exists(f'unified/{date_string}'):
        os.makedirs(f'unified/{date_string}')
        [shutil.copy(f'unified/{x}', f'unified/{date_string}/{x}')
         for x in ['on_rank.pkl', 'on_team.pkl']]


def run_unification():
    hltv, esl, valve = get_raw_data()
    hltv = pd.DataFrame(hltv) if type(hltv) == list else hltv  # For compatibility; can be removed in future
    hltv = hltv.rename(columns={'position': 'rank', 'name': 'teamname'})

    # TODO: add in future a check on new teamnames - potentially reusing old team IDs or cores for automatically mapping
    teamname_mapping = pd.read_csv('teamname_mapping.csv').drop_duplicates()
    teamname_mapping = teamname_mapping.set_index('teamname')
    hltv['teamname'] = hltv['teamname'].apply(lambda x: teamname_mapping.loc[x].values[0])
    esl['teamname'] = esl['teamname'].apply(lambda x: teamname_mapping.loc[x].values[0])
    valve['teamname'] = valve['teamname'].apply(lambda x: teamname_mapping.loc[x].values[0])

    # Valve ranking can include teams multiple times for different cores (only 1 or 2 overlapping players) if both cores
    # have enough points to be ranked. I could try to detect which ever is the current one, but for now I will simply
    # drop the lowest ranked one (to clarify: the one with the lowest points and the highest "rank nr").
    # Then, the rank is recalculated based on the remaining entries.
    valve = valve.drop_duplicates(subset='teamname', keep='first')
    valve['rank'] = valve['points'].rank(ascending=False, method='first')

    unified_on_rank = (esl.merge(valve, how="outer", on='rank', suffixes=["_esl", "_valve"]).
                       merge(hltv.rename(columns={"teamname": "teamname_hltv", "points": "points_hltv"}),
                             on='rank', how='left'))
    unified_on_rank = unified_on_rank.set_index('rank')

    unified_on_team = (esl.merge(valve, how="outer", on='teamname', suffixes=["_esl", "_valve"]).
                       merge(hltv.rename(columns={"rank": "rank_hltv", "points": "points_hltv"}),
                             on='teamname', how='left'))
    unified_on_team = unified_on_team.set_index('teamname')

    if not filefolder_exists('unified'):
        os.mkdir('unified')
    unified_on_rank.to_pickle('unified/on_rank.pkl')
    unified_on_team.to_pickle('unified/on_team.pkl')

    copy_to_date_folder()


if __name__ == "__main__":
    run_unification()

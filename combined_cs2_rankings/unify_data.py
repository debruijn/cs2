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

    # Filter out low scoring teams in HLTV for now
    hltv = hltv.loc[hltv.points > 1].copy()
    return hltv, esl, valve


def copy_to_date_folder(force=False):
    date_string = str(date.today()).replace('-', '')
    if force or not filefolder_exists(f'unified/{date_string}'):
        os.makedirs(f'unified/{date_string}')
        [shutil.copy(f'unified/{x}', f'unified/{date_string}/{x}')
         for x in ['on_rank.pkl', 'on_team.pkl']]


def run_unification():
    hltv, esl, valve = get_raw_data()
    hltv = hltv.rename(columns={'position': 'rank', 'name': 'teamname'})
    esl = esl.rename(columns={'position': 'rank', 'name': 'teamname'})
    valve = valve.rename(columns={'position': 'rank', 'name': 'teamname'})

    # TODO: add in future a check on new teamnames - potentially reusing old team IDs or cores for automatically mapping

    # Design:
    # - Update teams with players and check if >=3 out of 5 are same
    # - If you can't find them, check other teams to see that overlap
    # - Otherwise, add new row with name repeated for mapping
    # if members are different -> put old team to an archive csv or yaml or something - let's see

    teamname_mapping = pd.read_csv('teamname_mapping.csv').drop_duplicates()
    teamname_mapping = teamname_mapping.set_index('teamname')

    # For all teams:
    # - check if they are in their teamname_mapping
    #   - Yes: compare roster with roster(s) in rosters.csv; if different, update.
    #   - No: compare roster with all rosters for overlap for renaming
    #       - Yes: rename curr teamname to new one + add new teamname + add roster to rosters.csv
    #       - No: new teamname only + add to rosters.csv
    # Return: teamname_mapping and rosters (no application of mapping since needs to be consistent)

    # TODO: later: remove old rosters
    # TODO: add tests for update_teamnames_rosters

    rosters = pd.read_csv('rosters.csv')
    rosters = rosters.set_index('teamname')
    player_mapping = pd.read_csv('player_mapping.csv').set_index('map_from')


    def update_teamnames_rosters(df: pd.DataFrame, teamname_mapping: pd.DataFrame, rosters: pd.DataFrame):
        for row in df.iterrows():
            this_name = row[1].teamname
            this_roster = [x.lower() for x in row[1].players]
            this_roster = [player_mapping.loc[x, 'map_to'] if x in player_mapping.index else x for x in this_roster]
            if this_name in teamname_mapping.index.values:
                if this_name not in rosters.index.values:
                    rosters.loc[this_name] = {'curr_roster': this_roster, 'old_rosters': []}
                elif set(this_roster) != set(eval(str(rosters.loc[this_name]['curr_roster']))):
                    if this_roster not in eval(str((rosters.loc[this_name]['old_rosters']))):
                        rosters.loc[this_name, 'old_rosters'] = str([eval(str(rosters.loc[this_name]['curr_roster']))] +
                                                             eval(str(rosters.loc[this_name]['old_rosters'])))
                        rosters.loc[this_name, 'curr_roster'] = str(this_roster)
            else:
                best_match = 0
                matched_team = None
                for roster in rosters.iterrows():
                    if len(set(roster[1].curr_roster).intersection(set(this_roster))) >= 3:
                        if len(set(roster[1].curr_roster).intersection(set(this_roster))) > best_match:
                            best_match = len(set(roster[1].curr_roster).intersection(set(this_roster)))
                            matched_team = roster[1].teamname
                if matched_team:
                    print(teamname_mapping[matched_team])
                teamname_mapping.loc[this_name] = {'mapped_name': this_name}
                rosters.loc[this_name] = {'curr_roster': this_roster, 'old_rosters': []}

        return teamname_mapping, rosters

    teamname_mapping, rosters = update_teamnames_rosters(valve, teamname_mapping, rosters)
    teamname_mapping, rosters = update_teamnames_rosters(hltv, teamname_mapping, rosters)
    teamname_mapping, rosters = update_teamnames_rosters(esl, teamname_mapping, rosters)

    teamname_mapping.to_csv('teamname_mapping.csv')
    rosters.to_csv('rosters.csv')

    hltv['teamname'] = hltv['teamname'].apply(lambda x: teamname_mapping.loc[x].values[0])
    esl['teamname'] = esl['teamname'].apply(lambda x: teamname_mapping.loc[x].values[0]
                                                    if x in teamname_mapping.index else x)
    valve['teamname'] = valve['teamname'].apply(lambda x: teamname_mapping.loc[x].values[0]
                                                    if x in teamname_mapping.index else x)


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
    import os
    os.chdir('..')
    run_unification()

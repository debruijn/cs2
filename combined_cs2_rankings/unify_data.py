import os
from datetime import date
import shutil
from .import_data import filefolder_exists
import pandas as pd
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

def get_raw_data(incl_esl=False):
    path = 'imported/'
    hltv = pd.read_pickle(path + 'hltv_raw.pkl')
    valve = pd.read_pickle(path + 'valve_live_raw.pkl')

    # Filter out low scoring teams in HLTV for now
    hltv = hltv.loc[hltv.points > 1].copy()

    if incl_esl:
        esl = pd.read_pickle(path + 'esl_raw.pkl')
        return hltv, esl, valve
    return hltv, valve


def copy_to_date_folder(force=False):
    date_string = str(date.today()).replace('-', '')
    if force or not filefolder_exists(f'unified/{date_string}'):
        os.makedirs(f'unified/{date_string}')
        [shutil.copy(f'unified/{x}', f'unified/{date_string}/{x}')
         for x in ['on_rank.pkl', 'on_team.pkl']]


def update_teamnames_rosters(df: pd.DataFrame, teamname_mapping: pd.DataFrame, rosters: pd.DataFrame,
                             player_mapping: pd.DataFrame):
    """
    For all teams:
    - check if they are in their teamname_mapping
      - Yes: compare roster with roster(s) in rosters.csv; if different, update.
      - No: compare roster with all rosters for overlap for renaming
          - Yes: rename curr teamname to new one + add new teamname + add roster to rosters.csv
          - No: new teamname only + add to rosters.csv
    Return: teamname_mapping and rosters (no application of mapping since needs to be consistent)
    """
    for row in df.iterrows():
        # Extract info of team (name and roster)
        this_name = row[1].teamname
        this_roster = [x.lower() for x in row[1].players]
        this_roster = [player_mapping.loc[x, 'map_to'] if x in player_mapping.index else x for x in this_roster]

        if this_name in teamname_mapping.index.values:  # Teamname is already included
            if this_name not in rosters.index.values:
                rosters.loc[this_name] = {'curr_roster': this_roster, 'old_rosters': []}
            elif set(this_roster) != set(eval(str(rosters.loc[this_name]['curr_roster']))):
                # If this_roster != curr_roster, put curr_roster to old roster list
                if this_roster not in eval(str((rosters.loc[this_name]['old_rosters']))):
                    rosters.loc[this_name, 'old_rosters'] = str([eval(str(rosters.loc[this_name]['curr_roster']))] +
                                                         eval(str(rosters.loc[this_name]['old_rosters'])))
                    rosters.loc[this_name, 'curr_roster'] = str(this_roster)
        else:  # New teamname
            best_match = 0
            matched_team = None
            for roster in rosters.iterrows():
                if len(set(roster[1].curr_roster).intersection(set(this_roster))) >= 3:
                    if len(set(roster[1].curr_roster).intersection(set(this_roster))) > best_match:
                        best_match = len(set(roster[1].curr_roster).intersection(set(this_roster)))
                        matched_team = roster[1].teamname if 'teamname' in roster[1] else roster[0]
            if matched_team:
                print(f'{this_name} matched to {matched_team}')
                teamname_mapping.loc[matched_team] = {'mapped_name': this_name}
            teamname_mapping.loc[this_name] = {'mapped_name': this_name}
            rosters.loc[this_name] = {'curr_roster': this_roster, 'old_rosters': []}

    return teamname_mapping, rosters


def clean_rosters(rosters_df, teamname_mapping):
    rosters_df = rosters_df.filter(items=teamname_mapping.mapped_name.values, axis=0)  # Only keep mapped_name rosters

    for row in rosters_df.iterrows():  # Remove old_rosters that are current roster, or duplicate old_rosters
        non_dup_old_rosters = []
        curr_roster = set(eval(str(row[1].curr_roster)))
        for old_roster in eval(str(row[1].old_rosters)):
            old_roster = set(sorted(old_roster))
            if not old_roster == curr_roster and not list(old_roster) in non_dup_old_rosters:
                non_dup_old_rosters.append(list(old_roster))
        rosters_df.loc[row[0], 'old_rosters'] = str(non_dup_old_rosters)

    # Sort by index (teamname, lowercase)
    rosters_df = rosters_df.sort_index(key=lambda x: x.str.lower())
    rosters_df.index.name = 'teamname'
    return rosters_df


def sort_func(name_str):
    name_str = name_str.lower()
    if name_str.startswith('the '):
        name_str = name_str[4:]
    if name_str.startswith('team '):
        name_str = name_str[5:]
    if name_str.startswith('ex-'):
        name_str = name_str[3:]
    return name_str


def clean_teamname_mapping(teamname_df, clean=False):
    # Clean: remove unused teams -> either immediately, or rework to keep track of last time team in ranking
    if clean:
        pass  # Delay until #7

    # Sort by index (teamname, lowercase, ignore the/team/ex) -> easily recognized different namings across rankings
    teamname_df = teamname_df.reindex(sorted(teamname_df.index, key=lambda x: sort_func(x)))
    return teamname_df


def run_unification(incl_esl=False):
    if incl_esl:
        hltv, esl, valve = get_raw_data(incl_esl)
    else:
        hltv, valve = get_raw_data(incl_esl)
    hltv = hltv.rename(columns={'position': 'rank', 'name': 'teamname'})
    if incl_esl:
        esl = esl.rename(columns={'position': 'rank', 'name': 'teamname'})
    valve = valve.rename(columns={'position': 'rank', 'name': 'teamname'})

    # Load in teamname_mapping, rosters, and player_mapping from earlier runs
    teamname_mapping = pd.read_csv('teamname_mapping.csv').drop_duplicates()
    teamname_mapping = teamname_mapping.set_index('teamname')
    rosters = pd.read_csv('rosters.csv')
    rosters = rosters.set_index('teamname')
    player_mapping = pd.read_csv('player_mapping.csv').set_index('map_from')

    # Use the ranking dfs to update teamname_mapping and rosters with potential new teams or roster changes
    teamname_mapping, rosters = update_teamnames_rosters(valve, teamname_mapping, rosters, player_mapping)
    teamname_mapping, rosters = update_teamnames_rosters(hltv, teamname_mapping, rosters, player_mapping)
    if incl_esl:
        teamname_mapping, rosters = update_teamnames_rosters(esl, teamname_mapping, rosters, player_mapping)

    # Clean old teams/duplicate rosters and sort by teamname for easy comparison
    teamname_mapping = clean_teamname_mapping(teamname_mapping)
    rosters = clean_rosters(rosters, teamname_mapping)

    # Write out teamname_mapping and rosters -> check in PR if new teams are just renaming old ones
    teamname_mapping.to_csv('teamname_mapping.csv')
    rosters.to_csv('rosters.csv')

    # Apply renaming of teams to each ranking
    hltv['teamname'] = hltv['teamname'].apply(lambda x: teamname_mapping.loc[x].values[0])
    if incl_esl:
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

    if incl_esl:
        unified_on_rank = (esl.merge(valve, how="outer", on='rank', suffixes=["_esl", "_valve"]).
                           merge(hltv.rename(columns={"teamname": "teamname_hltv", "points": "points_hltv"}),
                                 on='rank', how='left'))
        unified_on_rank = unified_on_rank.set_index('rank')

        unified_on_team = (esl.merge(valve, how="outer", on='teamname', suffixes=["_esl", "_valve"]).
                           merge(hltv.rename(columns={"rank": "rank_hltv", "points": "points_hltv"}),
                                 on='teamname', how='left'))
        unified_on_team = unified_on_team.set_index('teamname')
    else:
        unified_on_rank = (valve.rename(columns={"teamname": "teamname_valve", "points": "points_valve"})
                           .merge(hltv.rename(columns={"teamname": "teamname_hltv", "points": "points_hltv"}),
                                 on='rank', how='left'))
        unified_on_rank = unified_on_rank.set_index('rank')

        unified_on_team = (valve.rename(columns={"rank": "rank_valve", "points": "points_valve"})
                           .merge(hltv.rename(columns={"rank": "rank_hltv", "points": "points_hltv"}),
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

import os
import shutil
import pandas as pd
from hltv_data2 import HLTVClient2  # TODO: replace with hltv_data when PR is merged
from bs4 import BeautifulSoup


def filefolder_exists(filename, dir=None):
    return os.path.exists(filename if dir is None else dir + '/' + filename)


def import_hltv(force=False):
    if force or not filefolder_exists('hltv_raw.pkl', dir='imported'):
        client = HLTVClient2()
        hltv_ranking = pd.DataFrame(client.get_ranking())
        pd.to_pickle(hltv_ranking, 'imported/hltv_raw.pkl')

def import_esl(force=False):
    if not force and filefolder_exists('esl_raw.pkl', dir='imported'):
        return

    # Use HLTV pulling client for ESL as well, with adjusted url of course
    base_url = "https://pro.eslgaming.com/worldranking/csgo/rankings/"
    client = HLTVClient2()
    page_source = client._get_page_source(base_url)

    # Wait to make sure page is loaded
    import time
    time.sleep(10)

    if page_source:
        soup = BeautifulSoup(page_source, "html.parser")
        teams = soup.select("div[class*=RankingsTeamItem__Row-]")

        rank, points, teamname = [], [], []
        for team in teams:
            try:  # First pull all numbers; in case of no error, add them all to the running lists
                this_pt = int(team.select('div[class*=Points]')[0].find("span").next.strip())
                this_name = str(team.select('div[class*=TeamName]')[0].select('a[class]')[0].next)
                this_rank = int(team.select('span[class*=WorldRankBadge__Number]')[0].next)
                points.append(this_pt)
                teamname.append(this_name)
                rank.append(this_rank)
            except TypeError as e:
                print('Not succeeded: ', team, e)

        data = pd.DataFrame(data={'rank': rank, 'points': points, 'teamname': teamname})
        data.to_pickle('imported/esl_raw.pkl')

    client.driver.quit()


def import_valve(force=False):
    if not force and filefolder_exists('valve_raw.pkl', dir='imported'):
        return

    # Clone valve regional standings into tmp/ and find file containing global rankings
    if not filefolder_exists('tmp/'):
        os.makedirs('tmp/')
    os.chdir('tmp/')
    os.system('git clone git@github.com:ValveSoftware/counter-strike_regional_standings.git')
    os.chdir('counter-strike_regional_standings/live/2024/')
    global_file = [x for x in os.listdir() if 'global' in x][0]

    # Read in global rankings
    with open(global_file, 'r') as f:
        valve_standings_md = f.read().splitlines()

    # Remove cloned repo and (if it's empty) tmp/
    os.chdir('../../../../')
    shutil.rmtree('tmp/counter-strike_regional_standings')
    if len(os.listdir('tmp')) == 0:
        os.removedirs('tmp')

    # Process the standings to something workable, and save it
    rank, points, teamname = [], [], []
    for row in valve_standings_md[5:-4]:
        row = [x.strip() for x in row.split('|')][1:4]  # TODO: reconsider for names with a space
        rank.append(int(row[0]))
        points.append(int(row[1]))
        teamname.append(row[2])
    data = pd.DataFrame(data={'rank': rank, 'points': points, 'teamname': teamname})
    data.to_pickle('imported/valve_raw.pkl')


def import_data(force=False):
    import_hltv(force)
    import_esl(force)
    import_valve(force)


if __name__ == "__main__":
    import_data(force=False)

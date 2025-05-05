import os
import shutil
from datetime import date
import pandas as pd
from cs_rankings import HLTVRankings, ESLRankings, ValveLiveRankings


def filefolder_exists(filename, dir=None):
    return os.path.exists(filename if dir is None else dir + '/' + filename)


def import_ranking(rankings_class, rankings_string, force=False, **kwargs):
    if force or not filefolder_exists(rankings_string + '_raw.pkl', dir='imported'):
        client = rankings_class(**kwargs)
        ranking = pd.DataFrame(client.get_ranking())
        client.close()
        pd.to_pickle(ranking, 'imported/' + rankings_string + '_raw.pkl')


def copy_to_date_folder(force=False, incl_esl=False):
    date_string = str(date.today()).replace('-', '')
    if force or not filefolder_exists(f'imported/{date_string}'):
        os.makedirs(f'imported/{date_string}', exist_ok=True)
        if incl_esl:
            [shutil.copy(f'imported/{x}', f'imported/{date_string}/{x}')
            for x in ['hltv_raw.pkl', 'esl_raw.pkl', 'valve_live_raw.pkl']]
        else:
            [shutil.copy(f'imported/{x}', f'imported/{date_string}/{x}')
            for x in ['hltv_raw.pkl', 'valve_live_raw.pkl']]



def import_data(force=False, incl_esl=False):
    import_ranking(HLTVRankings, 'hltv', force)
    import_ranking(ESLRankings, 'esl', incl_esl and force)
    import_ranking(ValveLiveRankings, 'valve_live', force)
    copy_to_date_folder(force, incl_esl)


if __name__ == "__main__":
    import_data(force=False)

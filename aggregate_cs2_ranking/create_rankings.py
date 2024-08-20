import os
from .import_data import filefolder_exists
import numpy as np
import pandas as pd
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)


def lin_scale(x, refs, targets):
    if np.isnan(x):
        return 0
    return max(targets[0] - (refs[0] - x) * (targets[0] - targets[1]) / (refs[0] - refs[1]), 0)


def create_rank_based_rankings(data):
    data = data.filter(like='rank')
    rank_cols = ['rank_esl', 'rank_hltv', 'rank_valve']

    # Fill in missings with the column max + 1 (since we can't know further)
    # Later on: we could make a data augmentation model, but that might be too complicated for this project
    data = data.fillna(value=data.max() + 1)

    data['median_rank'] = data[rank_cols].median(axis=1)
    data['mean_rank'] = data[rank_cols].mean(axis=1)
    data['exp_mean_log_rank'] = data[rank_cols].transform(np.log).mean(axis=1).transform(np.exp)

    rank_rankings = ['median_rank', 'mean_rank', 'exp_mean_log_rank']
    for rnk in rank_rankings:
        data[f"rank_by_{rnk}"] = data[rnk].rank()
    return data


def create_score_based_rankings(data):
    data = data.filter(like='points').copy()

    point_cols = ['points_esl', 'points_hltv', 'points_valve']
    for col in point_cols:
        # Create linearly scaled points, with factor such that average of top 10 is 1000 points
        mean_top_10 = np.mean(sorted(data[col].values, key=lambda x: int(x) if not np.isnan(x) else 0,
                                                      reverse=True)[:10])
        factor = 1000/mean_top_10
        data[f"lin_aligned_{col}"] = data[col] * factor

        # Create logarithmic aligned points:
        # - log-transform (for ESL and HLTV, which are exponential; Valve rankings are kept as is).
        # - align all three such that nr1 has 1000 points (so log is 3), and nr 30 has 10 points (so log is 1)
        targets = [3, 1]
        if col in ["points_esl", "points_hltv"]:
            data[f"log_{col}"] = data[col].transform(np.log)
            ref_values = sorted(data[f"log_{col}"].values, key=lambda x: float(x) if not np.isnan(x) else 0,
                                         reverse=True)[0:30:29]
            data[f"log_aligned_{col}"] = data[f"log_{col}"].transform(lambda x: lin_scale(x, refs=ref_values, targets=targets))
        else:
            ref_values = sorted(data[col].values, key=lambda x: float(x) if not np.isnan(x) else 0,
                                         reverse=True)[0:30:29]
            data[f"log_aligned_{col}"] = data[col].transform(lambda x: lin_scale(x, refs=ref_values, targets=targets))

    # For both alignments, create the rank based on the sum (or mean), and based on the median
    alignment = ['lin_aligned', 'log_aligned']
    for algn in alignment:
        algn_col = data.filter(like=algn).columns
        data[algn_col] = data.filter(like=algn).fillna(0)

        data[f"sum_{algn}"] = data.filter(like=algn).sum(axis=1)
        data[f"median_{algn}"] = data.filter(like=algn).median(axis=1)

        data[f"rank_by_sum_{algn}"] = data[f"sum_{algn}"].rank(ascending=False)
        data[f"rank_by_median_{algn}"] = data[f"median_{algn}"].rank(ascending=False)

    return data


def aggregate_ranking(raw, rank_based, score_based):

    combined = raw.join(rank_based).join(score_based)

    combined['mean_combined_rank'] = combined.mean(axis=1)
    combined['aggregate_rank'] = combined['mean_combined_rank'].rank()

    return combined


def create_rankings():

    # Read in unified data (by team)
    data = pd.read_pickle('unified/on_team.pkl')

    # Run rank-based rankings
    rank_based_rankings = create_rank_based_rankings(data)

    # Run score-based rankings
    score_based_rankings = create_score_based_rankings(data)

    # Create aggregate ranking: mean of all the above rankings
    raw_rankings = data.filter(like='rank')
    combined = aggregate_ranking(raw_rankings, rank_based_rankings.filter(like='rank_by_'),
                                                           score_based_rankings.filter(like='rank_by_'))
    aggregate_rank = combined[['mean_combined_rank', 'aggregate_rank']]
    aggregate_rank.to_csv('aggregate_rank.csv')

    # Save all rankings combined
    if not filefolder_exists('output'):
        os.mkdir('output')
    combined.to_pickle('output/all_rankings.pkl')
    score_based_rankings.to_pickle('output/aggregate_scores.pkl')


if __name__ == "__main__":
    create_rankings()

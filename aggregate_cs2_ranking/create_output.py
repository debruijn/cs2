import numpy as np
import pandas as pd
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)


def optimal_score(x):
    return np.round(np.exp(x) * 1000/np.exp(3))

    # Alternatives:
    # return np.round(x*1000/3)
    # return np.round(np.pow(10, x), 2)


def create_output():

    # Create aggregate ranking table, focused on the "best rank"
    combined_results = pd.read_pickle('output/all_rankings.pkl')
    combined_results = combined_results.rename(columns={'aggregate_rank': 'total_rank'})
    combined_results['total_rank'] = combined_results['total_rank'].transform(int)
    combined_results = combined_results.reset_index().set_index('total_rank').sort_index()
    for col in combined_results.filter(like='rank_').columns:
        combined_results[col] = combined_results[col].transform(lambda x: "" if np.isnan(x) else str(int(x)))
    combined_results['mean_combined_rank'] = combined_results['mean_combined_rank'].transform(lambda x: np.round(x, 2))

    with open("aggregate_ranking.md", 'w') as out:
        out.write(combined_results.to_markdown())

    # Create optimal score table, focused on the "best score"
    score_based_rankings = pd.read_pickle('output/aggregate_scores.pkl')
    score_based_rankings = score_based_rankings[['median_log_aligned', 'rank_by_median_log_aligned', 'points_esl',
                                                 'points_hltv', 'points_valve']]
    score_based_rankings = score_based_rankings.rename(columns={'median_log_aligned': 'optimal_score',
                                                                'rank_by_median_log_aligned': 'rank'})
    score_based_rankings['rank'] = score_based_rankings['rank'].transform(int)
    score_based_rankings = score_based_rankings.reset_index().set_index('rank').sort_index()
    score_based_rankings = score_based_rankings.loc[score_based_rankings['optimal_score'] > 0].copy()
    score_based_rankings.optimal_score = score_based_rankings.optimal_score.transform(optimal_score)
    for col in ['points_esl', 'points_hltv', 'points_valve']:
        score_based_rankings[col] = score_based_rankings[col].transform(lambda x: "" if np.isnan(x) else str(int(x)))

    with open("optimal_score.md", 'w') as out:
        out.write(score_based_rankings.to_markdown(colalign = ('left', 'left', 'right', 'right', 'right', 'right')))


if __name__ == "__main__":
    create_output()

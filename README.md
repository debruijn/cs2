# CS2 aggregate ranking

A project to combine the Counterstrike 2 rankings from ESL, HLTV and Valve.

> I don't care about explanations, give me the rankings!

Sure! You can find all kinds of combined rankings [here](aggregate_cs2_ranking/aggregate_ranking.md) and the recommended
ranking and points [here](aggregate_cs2_ranking/optimal_score.md). If you then have questions, come back here.

# Goal of this project
Combine the CS2 rankings from ESL, HLTV and Valve into a single ranking or score. Currently, I do both:
- In the above linked [aggregate_ranking.md](aggregate_cs2_ranking/aggregate_ranking.md) I include all kinds of ranks, 
from the raw ESL, HLTV and Valve rankings up to various combinations and transformations of the rankings and points of
all three. More details down below in `Methodology`.
- My personal recommended ranking is shown together with its underlying score in 
[optimal_score.md](aggregate_cs2_ranking/optimal_score.md). Ideally, this would be the standard ranking to use in CS2.

# Methodology
This project consists of four phases:
- Importing or loading data
- Unifying the data into a single dataset
- Calculating all the alternative and combined rankings
- Creating the Markdown tables linked above.

## Importing data
To get initial access to the data, we can make use of three different ways:
- The Valve rankings are publicly available via their Github (see credits below), and can easily be included by cloning
their repository as part of the process.
- The ESL rankings are publicly available on their website (see credits below), and are stored locally using 
`BeautifulSoup`.
- The HLTV rankings are pubicly available on their website (see credits below), and are stored locally using the 
`hltv-data` Python package. Note that this only includes the top 30 of HLTV since rankings >30 are not available on a
single webpage.

To make sure this project will not visit their web pages without reason, the loaded data is cached locally, in the 
`aggregate_cs2_ranking/imported` folder. Then, when rerunning the scripts, the local version is used, unless these files
are deleted or the import script is run with the `force=True` flag. Of course, this is occasionally needed to include
the newer versions of the base rankings in this project.

## Unifying data
The data is merged together to end up with (for each team) their rank and points for each of the three base rankings. To
do this, the following steps are taken:
- Team names are not 100% consistent across rankings. To make them consistent, there is a mapping table 
[teamname_mapping.csv](aggregate_cs2_ranking/teamname_mapping.csv) to convert various naming conventions into a single
one. In case you see a mistake in there, please let me know!
- In the Valve ranking, there are some team names included twice if there is no common 3-person core (for example, if
there are only 2 people remaining in a rebuild). In that case, I only include the highest ranked core for now. In the
future, I might try to include both using a numeric label, and try to match them to the right one in the ESL/HLTV
rankings.

## Alternative and combine rankings
For this, there are three type of rankings, all visible in the 
[aggregate_ranking.md](aggregate_cs2_ranking/aggregate_ranking.md):
- Rank-based ranking
- Point-based ranking
- Combined ranking

### Rank-based rankings
The rank-based rankings look at the rank for a team in all three rankings, and aggregates them somehow. Then after that,
the teams are ranked again based on these aggregations. The ones included are:
- `median_rank` (resulting in `rank_by_median_rank`), calculated by taking the median ("the middle") of the three
rankings
- `mean_rank` (resulting in `rank_by_mean_rank`), calculated by taking the mean / the average of the three rankings
- `exp_mean_log_rank` (resulting in `rank_by_exp_mean_log_rank`), calculated by taking the mean of the log 
transformation of the ranks, and then taking the exponential transformation of that.

Note that some teams have no rank in some of the rankings (especially for HLTV because we only use that up to #30). For
that, a virtual rank is included that is the value immediately after the last available rank (so if the HLTV ranking is
missing, that team gets rank #31).

### Point-based rankings
Next are the rankings making use of the points / scores given by the three ranking providers. Note that we can't just
directly take the sum or average of those points, because they work on a different scale. So first, we have to bring
them in line with each other. For this, I use two transformations:
- `lin_aligned`, which applies a linear scaling on all three such that the top 10 has 1000 points on average
- `log_aligned`, which first transforms the points with a log-transformation and then rescales that with a linear
transformation such that the #1 has 3 "log-points" and the #30 has 1 "log-point". Note that the Valve ranking already is
on a linear scale so the log-transformation is skipped there.

The motivation for the first alignment is that it is the transformation that made sense to me beforehand, whereas the 
motivation for the second alignment is that it is the transformation that turned out to make sense looking at the data:
the three rankings all follow the same pattern (roughly) from #1 to #30 using that `log_aligned` transformation, which 
is not the case for any linear transformation. In this way, they all have the same weight in the calculations and can be
treated equally. A summary of that exploratory process can be seen here:
![Summary of the exploraty process of why the log transformation makes the rankings 
comparable](summary_motivation_log_transformation.gif).

In this, E, H and V stand for ESL, HLTV and Valve respectively. 

Then, for both alignments, I convert them into new scores (and thus rankings) by taking either:
- the sum, resulting in `rank_by_sum_lin_aligned` and `rank_by_sum_log_aligned`
- the median, resulting in `rank_by_median_lin_aligned` and `rank_by_median_log_aligned`

Note again that there are missing points for some of the teams for some of the rankings. As a workaround, a virtual 
number of points equal to 0 is included. 

### Combined ranking
Finally, all three types of rankings (the raw rankings from ESL, Valve and HLTV; the rank-based rankings; and the
points-based rankings) are averaged to get a `mean_combined_rank`, which is then converted into a `total_rank` on which
[aggregate_ranking.md](aggregate_cs2_ranking/aggregate_ranking.md) is sorted.

## Creating the Markdown tables
There is little to say on how these tables are created from the results above. In case you are interested in how to
convert data into a Markdown file in Python: have a look at the source code.

# Future plans
There are several things that I consider adding in the future:
- Automated weekly runs of the entire process in a Gitlab pipeline (or on Github Actions). First, I want to manually update
the data (and thus results) to see whether stuff breaks.
- Extending the HLTV pull to include teams outside the top 30. This would mean I can't use the `hltv-data` package 
though, so I would have to write my own processing of the webpage. Also, I would likely have to load the page for each
team outside the top 30 separately. First, I will wait if perhaps someone knows a way around this.
- Imputing missing ranks using some statistical model. This would improve the usefulness of this project for teams after
rank 30, but would also make this project more complicated: currently, the methodology is nothing more than some 
transformations and averages/medians; but then, there would probably be some statistical model included which will make
the process less transparent.

# Discussion
No ranking is perfect. This holds for the base rankings from Valve, ESL and HLTV; but it for sure also holds for all my
variants. Having various rankings to compare can give additional insight into how dominant a team is; or how clear it is
that there is a top 5 separated from the rest; etc. Of course, what happens on the server is more important than what is
included here, so use this at your own risk.

Note that the three source rankings (and all my variations thereof as well) are all backwards-looking, not 
forward-looking. They are in a sense more a ranking of the achievements a team has made, than of the strength of the
teams. The only way such a backwards-looking ranking represents the power ranking perfectly as well is if there is 
long-term stability, which is probably less interesting for the fans. So instead, look at rankings to spot patterns in
teams rising and falling; and look at rankings to put those past achievements into context.

# Credits and sources
Of course, credit is due to [ESL](https://pro.eslgaming.com/worldranking/csgo/rankings/), 
[HLTV](https://www.hltv.org/ranking/teams/) and 
[Valve](https://github.com/ValveSoftware/counter-strike_regional_standings/tree/main/live/2024) themselves to create 
these rankings. For all three, a lot of thought and work has gone into these, and it is great that there are three 
competitive rankings that capture different components of what makes a CS team good. Thanks!!

Next to that, credit to dchoruzy, the creator of the [hltv-data](https://github.com/dchoruzy/hltv-data) repository, 
which was not only useful for getting programmatic access to the HLTV rankings but also acted as a starting point for my
own ESL pull. Thank you!

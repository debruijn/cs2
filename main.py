from aggregate_cs2_ranking import import_data, run_unification, create_rankings, create_output


def main():

    # Import data by scraping/cloning, or using locally cached data if present and force=False
    import_data(force=False)

    # Unify data into a single Dataframe, team based or rank based
    run_unification()

    # Creating rankings
    create_rankings()

    # Output script
    create_output()


if __name__ == "__main__":
    import os
    os.chdir('aggregate_cs2_ranking')
    main()

from combined_cs2_rankings import import_data, run_unification, create_rankings, create_output


def main():

    # Import data by scraping/cloning, or using locally cached data if present and force=False
    import_data(force=False, incl_esl=False)

    # Unify data into a single Dataframe, team based or rank based
    run_unification(incl_esl=False)

    # Creating rankings
    create_rankings(incl_esl=False)

    # Output script
    create_output(incl_esl=False)


if __name__ == "__main__":
    import os
    os.chdir('combined_cs2_rankings')
    main()

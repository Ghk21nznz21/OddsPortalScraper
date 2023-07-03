from Data.FetchNewData.OddsPortal.manage import ManageRequests


main_leagues = [
    #'England', 'France', 
    'Portugal', 'Italy', 'Spain',
    'Germany', 'Netherlands', 'Poland',
]
other_leagues = [
    'Argentina', 'Austria', 'Belgium', 'Brazil',
    'Chile', 'China', 'Czech-Republic',
    'Denmark', 'Egypt', 'Ecuador', 'Finland',
    'Japan', 'Mexico', 'Norway', 'Romania', 'Peru',
    'Russia', 'Scotland', 'Sweden', 'Turkey', 
    'USA', 'Uruguay', 'Venezuela'
]

last_n_years = 10 
max_leagues = 2
main_leagues = [(country, max_leagues, last_n_years)
                for country in main_leagues]
make_req = ManageRequests(main_leagues)
make_req.loop_requests()
class TVShow():
    def __init__(self, id, title, creator, cast, genre, overview, first_air_date,
                 episode_run_time, number_of_seasons, tagline, user_score, poster_url):
        self.id = id
        self.title = title
        self.cast = cast
        self.creator = creator
        self.genre = genre
        self.overview = overview
        self.first_air_date = first_air_date
        self.episode_run_time = episode_run_time
        self.number_of_seasons = number_of_seasons
        self.tagline = tagline
        self.user_score = user_score
        self.poster_url = poster_url

class Movie():
    def __init__(self, id, title, content_type, director, cast, genre, overview, release_date, tagline, runtime, user_score, poster_url):
        self.id = id
        self.title = title
        self.content_type = 'movie'
        self.director = director
        self.cast = cast
        self.genre = genre
        self.overview = overview
        self.release_date = release_date
        self.tagline = tagline
        self.runtime = runtime
        self.user_score = user_score
        self.poster_url = poster_url

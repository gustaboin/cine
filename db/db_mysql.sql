CREATE TABLE Actors (
    ActorID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    ImageFilename VARCHAR(255)
);

CREATE TABLE Countries (
    CountryID CHAR(2) PRIMARY KEY,
    Name VARCHAR(100) NOT NULL
);

CREATE TABLE Directors (
    DirectorID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(100) NOT NULL
);

CREATE TABLE Genres (
    GenreID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(50) NOT NULL
);

CREATE TABLE Saga (
    SagaID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    Description TEXT,
    ImageFilename VARCHAR(255),
    Slug VARCHAR(50)
);

CREATE TABLE Movies (
    MovieID INT AUTO_INCREMENT PRIMARY KEY,
    Title VARCHAR(255),
    ReleaseYear INT,
    DirectorID INT,
    GenreID INT,
    CountryID CHAR(2),
    ImageFilename VARCHAR(255),
    Watched BOOLEAN DEFAULT 0,
    IMDbRating FLOAT,
    TrailerURL VARCHAR(255),
    EnglishTitle VARCHAR(255),
    SagaID INT,
    Path VARCHAR(255),
    FOREIGN KEY (CountryID) REFERENCES Countries(CountryID),
    FOREIGN KEY (DirectorID) REFERENCES Directors(DirectorID),
    FOREIGN KEY (GenreID) REFERENCES Genres(GenreID),
    FOREIGN KEY (SagaID) REFERENCES Saga(SagaID)
);

CREATE TABLE MovieActors (
    MovieID INT,
    ActorID INT,
    PRIMARY KEY (MovieID, ActorID),
    FOREIGN KEY (MovieID) REFERENCES Movies(MovieID),
    FOREIGN KEY (ActorID) REFERENCES Actors(ActorID)
);

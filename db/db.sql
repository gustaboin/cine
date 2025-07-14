-- Create the database
CREATE DATABASE MovieDB;
GO

USE MovieDB;
GO

-- Directors table
CREATE TABLE Directors (
    DirectorID INT PRIMARY KEY IDENTITY,
    Name NVARCHAR(100) NOT NULL
);

-- Genres table
CREATE TABLE Genres (
    GenreID INT PRIMARY KEY IDENTITY,
    Name NVARCHAR(50) NOT NULL
);


CREATE TABLE Countries (
    CountryID CHAR(2) PRIMARY KEY,  -- por ejemplo 'IT', 'US'
    Name NVARCHAR(100) NOT NULL
);

-- Actors table
CREATE TABLE Actors (
    ActorID INT PRIMARY KEY IDENTITY,
    Name NVARCHAR(100) NOT NULL
);

-- Movies table
CREATE TABLE Movies (
    MovieID INT PRIMARY KEY IDENTITY(1,1),
    Title NVARCHAR(255),
    ReleaseYear INT,
    DirectorID INT,
    GenreID INT,
    CountryID CHAR(2),  -- Cambiado
    ImageFilename NVARCHAR(255),
    Watched BIT DEFAULT 0,
    FOREIGN KEY (DirectorID) REFERENCES Directors(DirectorID),
    FOREIGN KEY (GenreID) REFERENCES Genres(GenreID),
    FOREIGN KEY (CountryID) REFERENCES Countries(CountryID)
);

-- Many-to-many relationship: Movies and Actors
CREATE TABLE MovieActors (
    MovieID INT,
    ActorID INT,
    PRIMARY KEY (MovieID, ActorID),
    FOREIGN KEY (MovieID) REFERENCES Movies(MovieID),
    FOREIGN KEY (ActorID) REFERENCES Actors(ActorID)
);

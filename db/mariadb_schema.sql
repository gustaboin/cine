-- Reemplaza 'MovieDB' con el nombre real de tu base de datos si es diferente
USE MovieDB; 

-- Establece el juego de caracteres y la intercalación para la sesión
-- Esto ayuda a asegurar que las tablas se creen con la codificación deseada
SET NAMES 'utf8mb4';
SET CHARACTER SET utf8mb4;
SET default_storage_engine = InnoDB;

-- Desactivar temporalmente las verificaciones de claves foráneas
-- Esto es útil si estás recreando tablas y hay dependencias circulares
-- ¡ASEGÚRATE DE VOLVER A ACTIVARLO DESPUÉS DE CREAR TODAS LAS TABLAS!
SET FOREIGN_KEY_CHECKS = 0;

---
-- Table [dbo].[Saga]
---
DROP TABLE IF EXISTS Saga;
CREATE TABLE Saga (
	SagaID INT AUTO_INCREMENT PRIMARY KEY,
	Name VARCHAR(100) NOT NULL,
	Description TEXT, -- NVARCHAR(max) a TEXT
	ImageFilename VARCHAR(255), -- NVARCHAR a VARCHAR
	Slug VARCHAR(50)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

---
-- Table [dbo].[Countries]
---
DROP TABLE IF EXISTS Countries;
CREATE TABLE Countries (
	CountryID CHAR(2) NOT NULL PRIMARY KEY, -- PRIMARY KEY CLUSTERED a PRIMARY KEY
	Name VARCHAR(100) NOT NULL -- NVARCHAR a VARCHAR
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

---
-- Table [dbo].[Directors]
---
DROP TABLE IF EXISTS Directors;
CREATE TABLE Directors (
	DirectorID INT AUTO_INCREMENT PRIMARY KEY, -- IDENTITY(1,1) a AUTO_INCREMENT PRIMARY KEY
	Name VARCHAR(100) NOT NULL -- NVARCHAR a VARCHAR
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

---
-- Table [dbo].[Genres]
---
DROP TABLE IF EXISTS Genres;
CREATE TABLE Genres (
	GenreID INT AUTO_INCREMENT PRIMARY KEY, -- IDENTITY(1,1) a AUTO_INCREMENT PRIMARY KEY
	Name VARCHAR(50) NOT NULL -- NVARCHAR a VARCHAR
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

---
-- Table [dbo].[Actors]
---
DROP TABLE IF EXISTS Actors;
CREATE TABLE Actors (
	ActorID INT AUTO_INCREMENT PRIMARY KEY, -- IDENTITY(1,1) a AUTO_INCREMENT PRIMARY KEY
	Name VARCHAR(100) NOT NULL, -- NVARCHAR a VARCHAR
	ImageFilename VARCHAR(255) -- VARCHAR (ya era)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

---
-- Table [dbo].[Movies]
---
DROP TABLE IF EXISTS Movies;
CREATE TABLE Movies (
	MovieID INT AUTO_INCREMENT PRIMARY KEY, -- IDENTITY(1,1) a AUTO_INCREMENT PRIMARY KEY
	Title VARCHAR(255), -- NVARCHAR a VARCHAR
	ReleaseYear INT,
	DirectorID INT,
	GenreID INT,
	CountryID CHAR(2),
	ImageFilename VARCHAR(255), -- NVARCHAR a VARCHAR
	Watched BOOLEAN DEFAULT 0, -- BIT a BOOLEAN, DEFAULT ((0)) a DEFAULT 0
	IMDbRating FLOAT,
	TrailerURL VARCHAR(255), -- Ya era VARCHAR
	EnglishTitle VARCHAR(255), -- NVARCHAR a VARCHAR
	SagaID INT,
	Path VARCHAR(255), -- Ya era VARCHAR
	TmdbID INT,
    
    CONSTRAINT FK_Movies_Directors FOREIGN KEY (DirectorID) REFERENCES Directors (DirectorID),
    CONSTRAINT FK_Movies_Genres FOREIGN KEY (GenreID) REFERENCES Genres (GenreID),
    CONSTRAINT FK_Movies_Countries FOREIGN KEY (CountryID) REFERENCES Countries (CountryID),
    CONSTRAINT FK_Movies_Saga FOREIGN KEY (SagaID) REFERENCES Saga (SagaID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

---
-- Table [dbo].[ActorProfiles]
---
DROP TABLE IF EXISTS ActorProfiles;
CREATE TABLE ActorProfiles (
	ProfileID INT AUTO_INCREMENT PRIMARY KEY, -- IDENTITY(1,1) a AUTO_INCREMENT PRIMARY KEY
	ActorID INT,
	TmdbID INT,
	Bio TEXT, -- TEXTIMAGE_ON [PRIMARY] y TEXT a TEXT
	BirthDate DATE, -- DATE ya era
	Country VARCHAR(50), -- VARCHAR ya era
	ImageFilename VARCHAR(255), -- VARCHAR ya era
	imdb_id VARCHAR(50), -- VARCHAR ya era
    
    CONSTRAINT FK_ActorProfiles_Actors FOREIGN KEY (ActorID) REFERENCES Actors (ActorID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

---
-- Table [dbo].[ActorExternalMovies]
---
DROP TABLE IF EXISTS ActorExternalMovies;
CREATE TABLE ActorExternalMovies (
	ActorMovieID INT AUTO_INCREMENT PRIMARY KEY, -- IDENTITY(1,1) a AUTO_INCREMENT PRIMARY KEY
	ActorID INT,
	TmdbMovieID INT,
	Title VARCHAR(255), -- VARCHAR ya era
	ReleaseDate DATE, -- DATE ya era
	OriginalLanguage VARCHAR(10), -- VARCHAR ya era
	imdb_id VARCHAR(20), -- VARCHAR ya era
    
    CONSTRAINT FK_ActorExternalMovies_Actors FOREIGN KEY (ActorID) REFERENCES Actors (ActorID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

---
-- Table [dbo].[MovieActors]
---
DROP TABLE IF EXISTS MovieActors;
CREATE TABLE MovieActors (
	MovieID INT NOT NULL,
	ActorID INT NOT NULL,
    PRIMARY KEY (MovieID, ActorID), -- PRIMARY KEY CLUSTERED a PRIMARY KEY (compuesta)
    
    CONSTRAINT FK_MovieActors_Movies FOREIGN KEY (MovieID) REFERENCES Movies (MovieID),
    CONSTRAINT FK_MovieActors_Actors FOREIGN KEY (ActorID) REFERENCES Actors (ActorID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ¡IMPORTANTE! Vuelve a activar las verificaciones de claves foráneas
SET FOREIGN_KEY_CHECKS = 1;
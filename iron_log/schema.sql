-- Drop tables if they exist
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS exercises;
DROP TABLE IF EXISTS workouts;
DROP TABLE IF EXISTS sets;


-- Table for users
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

-- Table for workouts
CREATE TABLE workouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    date DATE NOT NULL,
    FOREIGN KEY
(user_id) REFERENCES users
(id)
);

-- Table for exercises
CREATE TABLE exercises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workout_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    notes TEXT,
    FOREIGN KEY
(workout_id) REFERENCES workouts
(id)
);

-- Table for sets
CREATE TABLE sets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exercise_id INTEGER NOT NULL,
    weight REAL NOT NULL,
    repetitions INTEGER NOT NULL,
    rating INTEGER CHECK
(rating >= 1 AND rating <= 10),
    FOREIGN KEY
(exercise_id) REFERENCES exercises
(id)
);

# This is the blueprint for workout log. It will contain all the routes for the application.

from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)
from werkzeug.exceptions import abort
from iron_log.auth import login_required
from iron_log.db import get_db

bp = Blueprint("workout_log", __name__)


@bp.route("/")
def index():
    db = get_db()
    workouts = db.execute(
        "SELECT w.id, w.name, w.date, w.user_id, u.username"
        " FROM workouts w JOIN users u ON w.user_id = u.id"
        " ORDER BY w.date DESC"
    ).fetchall()

    workout_data = []
    for workout in workouts:
        exercises = db.execute(
            "SELECT id, name, notes" " FROM exercises" " WHERE workout_id = ?",
            (workout["id"],),
        ).fetchall()

        workout["exercises"] = exercises
        workout_data.append(workout)

    return render_template("workout_log/index.html", workouts=workout_data)


# Route to create a new workout with exercises and sets
@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    if request.method == "POST":
        workout_name = request.form["workout_name"]
        date = request.form["date"]
        exercise_names = request.form.getlist("exercise_name")
        exercise_notes = request.form.getlist("exercise_notes")
        set_weights = request.form.getlist("weight")
        set_repetitions = request.form.getlist("repetitions")
        set_ratings = request.form.getlist("rating")
        error = None

        if not workout_name:
            error = "Workout name is required."
        elif len(exercise_names) == 0:
            error = "At least one exercise is required."
        elif (
            len(set_weights) != len(exercise_names)
            or len(set_repetitions) != len(exercise_names)
            or len(set_ratings) != len(exercise_names)
        ):
            error = "Please provide all sets for each exercise."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            # Insert the workout
            db.execute(
                "INSERT INTO workouts (user_id, name, date) VALUES (?, ?, ?)",
                (g.user["id"], workout_name, date),
            )
            workout_id = db.lastrowid

            # Insert the exercises
            for exercise_name, exercise_note in zip(exercise_names, exercise_notes):
                db.execute(
                    "INSERT INTO exercises (workout_id, name, notes) VALUES (?, ?, ?)",
                    (workout_id, exercise_name, exercise_note),
                )
                exercise_id = db.lastrowid

            # Insert the sets
            for exercise_id, weight, repetitions, rating in zip(
                range(1, len(exercise_names) + 1),
                set_weights,
                set_repetitions,
                set_ratings,
            ):
                db.execute(
                    "INSERT INTO sets (exercise_id, weight, repetitions, rating) VALUES (?, ?, ?, ?)",
                    (exercise_id, weight, repetitions, rating),
                )

            db.commit()
            return redirect(url_for("workout_log.index"))

    return render_template("workout_log/create.html")


# Route to get a workout with exercises and sets
def get_workout(id, check_author=True):
    workout = (
        get_db()
        .execute(
            "SELECT w.id, name, date, author_id, username"
            " FROM workouts w JOIN users u ON w.author_id = u.id"
            " WHERE w.id = ?",
            (id,),
        )
        .fetchone()
    )

    if workout is None:
        abort(404, f"Workout id {id} doesn't exist.")

    if check_author and workout["author_id"] != g.user["id"]:
        abort(403)

    # Retrieve the exercises for the workout
    exercises = (
        get_db()
        .execute(
            "SELECT id, workout_id, name, notes"
            " FROM exercises"
            " WHERE workout_id = ?",
            (id,),
        )
        .fetchall()
    )

    for exercise in exercises:
        # Retrieve the sets for each exercise
        sets = (
            get_db()
            .execute(
                "SELECT id, exercise_id, weight, repetitions, rating"
                " FROM sets"
                " WHERE exercise_id = ?",
                (exercise["id"],),
            )
            .fetchall()
        )

        exercise["sets"] = sets

    workout["exercises"] = exercises

    return workout


# Route to update a workout with exercises and sets
@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
def update(id):
    workout = get_workout(id)

    if request.method == "POST":
        name = request.form["workout_name"]
        date = request.form["date"]
        error = None

        if not name:
            error = "Workout name is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "UPDATE workouts SET name = ?, date = ? WHERE id = ?", (name, date, id)
            )
            db.commit()

            # Update exercises and sets
            exercises = request.form.getlist("exercise_name")
            weights = request.form.getlist("weight")
            repetitions = request.form.getlist("repetitions")

            # Perform update for each exercise
            for exercise_id, exercise in enumerate(workout["exercises"]):
                exercise_name = exercises[exercise_id]
                weight = weights[exercise_id]
                reps = repetitions[exercise_id]

                db.execute(
                    "UPDATE exercises SET name = ? WHERE id = ?",
                    (exercise_name, exercise["id"]),
                )

                db.execute(
                    "UPDATE sets SET weight = ?, repetitions = ? WHERE exercise_id = ?",
                    (weight, reps, exercise["id"]),
                )

            db.commit()
            return redirect(url_for("workout_log.index"))

    return render_template("workout_log/update.html", workout=workout)


@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
def delete(id):
    get_workout(id)
    db = get_db()
    db.execute("DELETE FROM workouts WHERE id = ?", (id,))
    db.commit()
    return redirect(url_for("workout_log.index"))

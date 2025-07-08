from flask import Blueprint, render_template, session, redirect, url_for

help_bp = Blueprint("help", __name__)

@help_bp.route("/help")
def help_home():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    return render_template("help_section.html", username=session.get("username", "User"))

@help_bp.route("/help/articles")
def help_articles():
    return render_template("help_articles.html")

@help_bp.route("/help/books")
def help_books():
    return render_template("help_books.html")

@help_bp.route("/help/helplines")
def help_helplines():
    return render_template("help_helplines.html")

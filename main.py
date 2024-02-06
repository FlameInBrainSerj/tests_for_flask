from market import app
# from market import db
#
#
# @app.before_first_request
# def create_tables():
#     db.create_all()


# Checks if the main.py file has executed directly and not imported
if __name__ == "__main__":
    # create_tables()
    app.run(debug=True)

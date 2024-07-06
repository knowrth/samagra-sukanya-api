from models.db import db, app
from models.ReferencModels import insert_income_levels, create_initial_admin, create_initial_user

# def create_tables():
#     with db.app.app_context():
#         db.create_all()

def create_tables_and_populate_data():
    with app.app_context():
        db.create_all()
        create_initial_admin()
        create_initial_user()
        insert_income_levels()






if __name__ == '__main__':
    create_tables_and_populate_data();
from models.db import db, app
from sqlalchemy import text
from models.ReferencModels import insert_income_levels, create_initial_admin, create_initial_user
import sys
# def create_tables():
#     with db.app.app_context():
#         db.create_all()

# def create_tables_and_populate_data():
#     with app.app_context():
#         db.create_all()
#         # create_initial_admin()
#         # create_initial_user()
#         insert_income_levels()






# if __name__ == '__main__':
#     create_tables_and_populate_data();

def execute_query(query):
    with app.app_context():
    
        try:
            with db.session() as session:
                result = session.execute(text(query))
                
                if query.strip().lower().startswith(('insert', 'update', 'delete')):
                    session.commit()
                    print("Transaction committed.")
                else:
                    rows = result.fetchall()
                    for row in rows:
                        print(row)
        except Exception as e:
            print(f"An error occurred: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <SQL_query>")
        sys.exit(1)

    query = sys.argv[1]
    execute_query(query)
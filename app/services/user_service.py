from models.db import db
from models.UserModels import UserMap, UserModel
from typing import List
def create_user(sponsor_id, username, role, image_url=None, title=None, 
                gender=None, dob=None, father_name=None, house_telephone=None,
                email=None, country=None, state=None, city=None, pin_code=None, address=None,
                marital_status=None):
    new_user=None
    with db.sesssion(expire_on_commit=False) as session:
    # Check if sponsor exists
        if role == "USER":
            stmt = db.Select(UserModel).filter_by(user_id=sponsor_id)
            sponsor = session.execute(stmt).scalars.first()
            if sponsor is not None:
                user = UserModel(sponsor_id=sponsor_id,role="USER")
                session.add(user)
                session.commit()
                new_user = dict(user)
    return new_user
                
def update_user(user_id,password=None, name=None):
    updated_user = None
    with db.session() as session:
        stmt = db.Select(UserModel).filter_by(user_id=user_id)
        user = session.execute(stmt).scalars.first()
        if user :
            user.name = name
        session.add(user)
        session.commit()
        updated_user = dict(user)
    return updated_user

def get_user_by_id(user_id):
    selected_user = None
    with db.session() as session:
        stmt = db.Select(UserModel).filter_by(user_id=user_id)
        user = session.execute(stmt).scalars.first()
        if user:
            selected_user = dict(user)
    selected_user


def list_user(filter_by:dict=None, limit:int=10,offset:int=0,order_by:List[str]=None):
    '''
    filter_by = {
        "col_name_1":"value1",
        "col_name_2" :"value2"
    }
    order_by = ["col_1","col2 desc"]
    '''
    user_list = None
    filters = {}
    with db.session() as session:
        stmt = db.Select(UserModel)
        if filter_by:
            stmt = stmt.filter_by(**filters)
        if order_by:
            stmt = stmt.order_by(*order_by)
        stmt = stmt.limit(limit).offset(offset)
        users = session.execute(stmt).scalars.all()
        user_list = [dict(x) for x in users ]
    return user_list
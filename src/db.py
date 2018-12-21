from tinydb import TinyDB, Query
from src.util.project_path import DATA_FILE

db = TinyDB(DATA_FILE)


# 유저 정보 관리
def _get_user(user_id):
    '''
    유저가 있는지 확인하는 함수
    '''
    return db.search(Query().id == user_id)


def get_user(user_id):
    '''
    슬랙의 유저 id를 받아 유저 정보(dict)를 반환하는 함수
    '''
    user = _get_user(user_id)
    return user[0] if user else None


def insert_user(user_id):
    '''
    슬랙의 유저 id를 받아서 db에 넣는 함수
    유저 id가 이미 있을 경우 저장하지 않는다

    슬랙의 유저 id 정보가 db에 있으면 그 정보를 리턴하고,
    그 정보가 없으면 유저 정보와 초기값을 db에 저장하고 'first'(처음 봇과 연동)를 리턴함
    '''
    user = db.search(Query().id == user_id)

    if not user:
        db.insert({'id': user_id, 'state': 0, 'schedule': {}})

    return user[0]


# 유저 상태 관리
def get_user_state(user_id):
    '''
    슬랙의 유저 상태를 반환하는 함수
    '''
    return get_user(user_id)['state']


def set_user_state(user_id, state=0):
    '''
    슬랙의 유저 id를 받아서 유저의 상태를 바꾸는 함수

    상태를 바꿨을 경우 유저 정보의 db 인덱스를 반환함(int)
    에러일 경우 'error'를 리턴함
    '''
    User = Query()

    user = db.search(User.id == user_id)
    if not user:
        return 'error'
    else:
        return db.update({'state': state}, User.id == user_id)[0]


# 유저 날씨 지역 관리
def set_area(user_id, area):
    '''
    슬랙의 유저 id를 받아 유저의 지역(area)를 set(update)하는 함수
    '''
    db.update({"Area": area}, Query().id == user_id)


def get_area(user_id):
    '''
     슬랙의 유저 id를 받아 유저의 지역을 get하는 함수
     '''
    return get_user(user_id)["Area"]


# 유저 일정 관리
def get_all_schedules(user_id):
    '''
    유저의 저장된 모든 일정을 불러오는 함수
    '''
    return get_user(user_id)['schedule']


def get_schedule(user_id, when):
    '''
    유저의 일정 하나를 불러오는 함수
    '''
    return get_all_schedules(user_id)[when]


def create_schedule(user_id, when, todo):
    '''
    유저의 일정을 만드는 함수
    '''
    user_schedules = get_all_schedules(user_id)
    if when in user_schedules:
        user_schedules[when].append(todo)
    else:
        user_schedules[when] = [todo]

    return db.update({'schedule': user_schedules}, Query().id == user_id)


def get_temp(user_id):
    '''
    임시로 저장한 일정을 가져오는 함수
    '''
    return get_user(user_id)['temp']


def create_temp(user_id, todo):
    '''
    임시로 일정을 저장하는 함수
    '''

    user_schedules = get_all_schedules(user_id)
    user_schedules['temp'] = todo

    return db.update(user_schedules, Query().id == user_id)


def delete_schedule_temp(user_id):
    '''
    임시로 저장된 일정을 삭제하는 함수
    '''
    user_schedules = get_all_schedules(user_id).pop('temp', None)

    return db.update({'schedule': user_schedules}, Query().id == user_id)


def delete_schedule(user_id, when='', todo=''):
    '''
    유저의 일정을 삭제하는 함수
    '''
    user_schedules = get_all_schedules(user_id)
    if when:
        user_schedules[when].remove(todo)

    return db.update({'schedule': user_schedules}, Query().id == user_id)


def get_all_user():
    '''
    모든 유저의 정보를 가져오는 함수
    '''
    return db.all()

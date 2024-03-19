from flask import Flask, render_template, jsonify, request
from flask_jwt_extended import*
import requests
import re
from pymongo import MongoClient, DESCENDING

#todo: 리프레쉬 토큰 여력이 되면 구현

app = Flask(__name__)

app.config.update(
    DEBUG = True,
    JWT_SECRET_KEY = "HIII",
)

jwt = JWTManager(app)

client = MongoClient('localhost', 27017)
db = client.meow

# 인덱스 페이지
@app.route('/')
def home():
    return render_template('index.html')

# 로그인 폼 화면
@app.route('/login/form')
def login():
    return render_template('sign_in.html')

# 로그인
@app.route("/login",methods=['POST'])
def login_proc():
    user_id = request.form["id"]
    user_pw = request.form["pw"]
    
    user_data = db.student.find_one({'id': user_id}, {'pw': 1})

    if(user_pw== user_data['pw']):
        #todo: 조금 더 보안을 강화하고 싶다면 user_id를 단방향으로 암호화해서 identity 설정
        access_token = create_access_token(identity=user_id,expires_delta=False,additional_claims={"id":user_id})
        response = jsonify(
            status = "success",
            data = access_token
        )
        return response
    else : 
        return jsonify(
            status = "fail",            
            message = "존재하지 않는 아이디 혹은 비밀번호 오류"
        )
    
# 회원가입 폼 조회
@app.route('/signup/form', methods=['GET'])
def show_signup_form():
    return render_template('signup_form.html')

# 회원 등록
@app.route('/signup', methods=['POST'])
def signup():
    random_cat_api = 'https://cataas.com/cat?json=true'
    headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}

    api_result = requests.get(random_cat_api, headers=headers).json()
    cat_id = api_result['_id']
    cat_image_url = 'https://cataas.com/cat?id=' + cat_id

    id = request.form['id']
    pw = request.form['password']
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']

    studentInfo = {
        'id': id,
        'pw': pw,
        'name': name,
        'email': email,
        'phone': phone,
        'cat_image_url': cat_image_url,
        'location': 'undefined',
    }

    if (validate_student_info(studentInfo) == False):
        return jsonify({'status': 'fail', 'message': '유효성 검사 실패. 입력하신 정보를 다시 확인해주세요'})        

    db.student.insert_one(studentInfo)

    return jsonify({'status': 'success', 'message': '회원가입에 성공하였습니다.'})

# 내 상태 변경
@app.route('/state/update', methods=['POST'])
@jwt_required(optional=True)
def update_state():
    current_user = get_jwt_identity()
    if not current_user:
        return jsonify({'status':'fail', 'message': '토큰값이 비어있음'})

    location = request.form['location']
    cat_image_url = request.form['catImageUrl']

    update_data = {}

    if (location):
        update_data['location'] = location
    if (cat_image_url):
        update_data['cat_image_url'] = cat_image_url
        
    db.student.update_one({'id': current_user}, {'$set': update_data})
    
    return jsonify({'status': 'success', 'message': '업데이트에 성공하였습니다.'})

# 전체 수강생 상태 조회
@app.route('/state/list', methods=['GET'])
@jwt_required(optional=True)
def show_student_states():
    current_user = get_jwt_identity()
    if not current_user:
        return jsonify({'status':'fail', 'message': '토큰값이 비어있음'})

    students = list(db.student.find({}, {'_id': 0, 'pw': 0}))

    # 내 정보 
    my_profile = next((item for item in students if item['id'] == current_user), None)    

    # 다른 학생 정보
    other_students = [item for item in students if item['id'] != current_user]

    data = {
        'my_profile': my_profile,
        'other_students': other_students
    }
    
    return render_template('student_states.html', data=data)

# 수강생 최신 상태정보 조회
@app.route('/state/others/renew', methods=['GET'])
@jwt_required(optional=True)
def show_recent_states():
    current_user = get_jwt_identity()
    if not current_user:
        return jsonify({'status':'fail', 'message': '토큰값이 비어있음'})

    # todo: 정렬조건 추가해야 함
    other_students = db.student.find({'id': {"$ne": current_user}}, {'_id': 0, 'pw': 0, 'id': 0})

    return jsonify({'status': 'success', 'data': list(other_students)})

# 회원가입 정보 유효성 검사
def validate_student_info(student):
    # 이메일 유효성 검사
    email_regex = r"[a-zA-Z0-9._+-]+@[a-zA-Z0-9]+\.[a-zA-Z]{2,4}"
    if not re.match(email_regex, student['email']):
        print('이메일 실패')
        return False

    # 전화번호 유효성 검사
    phone_regex = r'^01([0|1|6|7|8|9]?)-?(\d{3,4})-?(\d{4})$'
    if not re.match(phone_regex, student['phone']):
        print('전화번호 실패')
        return False

    # 비밀번호 길이 검사
    if len(student['pw']) < 8:
        print('비밀번호 실패')
        return False

    # 아이디 길이 검사
    if len(student['id']) < 5:
        print('아이디 실패')
        return False

    # 이름 빈 문자열 검사
    if not student['name'].strip():
        print('닉네임 실패')
        return False
    
    return True

# 만료된 토큰 에러 콜백
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({'status': 'fail', 'message': '토큰이 만료되었습니다.'}), 401

# 유효하지 않은 토큰 에러 콜백 
@jwt.invalid_token_loader
def invalid_token_callback(error_string):
    return jsonify({'status': 'fail', 'message': '유효하지 않은 토큰입니다.', 'error': error_string}), 422

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
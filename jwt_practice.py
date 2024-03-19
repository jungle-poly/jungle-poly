from flask import Flask
from flask_jwt_extended import*
from flask import request;
from flask import jsonify;
from flask import render_template
import logging

#로깅 설정
logging.basicConfig(level=logging.DEBUG)

application = Flask(import_name=__name__)

application.config.update(
    DEBUG = True,
    JWT_SECRET_KEY = "HIII",
    # JWT_COOKIE_SECURE = False,
    # JWT_ACCESS_COOKIE_PATH = '/',
    # JWT_TOKEN_LOCATION = ['cookies']
)

jwt = JWTManager(application)

@application.route("/")
def test_test():
    return "<h1>hello<h1><a href='http://127.0.0.1:5000/login'>로그인<\a>"

admin_id = "1234"
admin_pw = "qwer"

@application.route("/login",methods=['GET'])
def login_page():
    return render_template('login.html')

@application.route("/login",methods=['POST'])
def login_proc():
    user_id = request.form["id"]
    user_pw = request.form["pw"]
    access_token = create_access_token(identity=user_id,expires_delta=False,additional_claims={"id":user_id})

    if(user_id == admin_id and user_pw==admin_pw):
        response = jsonify(
            status = "success",
            data = access_token
        )
        # set_access_cookies(response, access_token)
        return response
    else : 
        return jsonify(
            result = "fail"
        )
    
@application.route('/user_only',methods=["GET"])
@jwt_required()
def user_only():
    cur_user = get_jwt_identity()
    if cur_user is None:
        return "User Only!"
    else:
        return "Hi, "+ cur_user
    
if __name__ == '__main__':
    application.run(host="0.0.0.0",
                    port=5000,
                    debug =True)
    
    

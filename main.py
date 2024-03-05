from flask import Flask, render_template, request, url_for, redirect, flash, jsonify, send_from_directory
from classes import Notifier, PasswordChanger, is_link_valid, get_link_storage_instance,db, LinkStorage, EmployeeVerifier
from flask_sqlalchemy import SQLAlchemy
from sql_connector import SQLConnector
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
app.config['APPLICATION_ROOT'] = os.getenv('APPLICATION_ROOT')

# Creating the database tables within the application context
with app.app_context():
    db.init_app(app)
    db.create_all()

connector = SQLConnector(
    os.getenv('SQL_HOST'),
    os.getenv('SQL_DB'),
    os.getenv('SQL_USER'),
    os.getenv('SQL_PASSWORD')
)
changer = PasswordChanger(connector)
notifier = Notifier(connector)

#when you get one with no email sent us an email address telling us he needs one
@app.route('/WinCamsPasswordReset/', methods=['GET','POST'])
def reset_form():
    if request.method == 'GET':
        return render_template("index.htm")
    elif request.method == 'POST':    
        employee_id = request.form.get('employeeID')
        email_sender = Notifier(connector)
        email_sender.send_password_reset_email(employee_id)
        return render_template("index.htm") 
    
@app.route('/WinCamsPasswordReset/resetpassword/<employee_id>/<unique_key>', methods=['GET'])
def showpasswordresetform(employee_id, unique_key):
    if is_link_valid(employee_id, unique_key):
        return render_template("newpass.htm", employee_id=employee_id, unique_key=unique_key)
    else:
        return render_template("link_expired.htm")  # Render a template indicating link expiration
    
@app.route('/WinCamsPasswordReset/resetpassword/<employee_id>/<unique_key>', methods=['POST'])
def resetpassword(employee_id, unique_key):
    if is_link_valid(employee_id, unique_key):
        new_password = request.json.get('newPassword')
        password_changer = PasswordChanger(connector)
        changed = password_changer.change_password(employee_id, new_password)

        # Attempt password change
        if changed:
            email_sender = Notifier(connector)
            email_sender.send_password_change_note(employee_id)
            return jsonify({'success': True, 'message': 'Password changed successfully!'})
        else:
            return jsonify({'success': False, 'message': 'Password reset failed. Requirements are not met.'})
    else:
         return jsonify({'success': False, 'message': 'Expired Link'})


# Route for serving CSS files
@app.route('/WinCamsPasswordReset/static/css/<path:filename>')
def send_css(filename):
    return send_from_directory('static/css', filename)

# Route for serving image files
@app.route('/WinCamsPasswordReset/static/img/<path:filename>')
def send_img(filename):
    return send_from_directory('static/img', filename)
        

if __name__ == '__main__':
    from waitress import serve
    serve(app, host="0.0.0.0", port=8000)
    #app.run(debug=True, port=8000)



import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from datetime import datetime, timedelta
import uuid, re
from flask_sqlalchemy import SQLAlchemy




db = SQLAlchemy()

class EmployeeVerifier:
    def __init__(self, connector):
        self.connector = connector
        
    def get_employee_details(self, employee_id):
        employee = None
        if self.connector.connect():
            result = self.connector.execute_stored_procedure("GetUserInfo", employee_id)
            print(result)
            if result:
                # Check if the result has exactly three elements
                if len(result[0]) == 3:
                    # Process the result and construct the Employee object
                    employee_id = result[0][0].strip()  # Remove extra spaces
                    employee_name = result[0][1].strip()  # Remove extra spaces
                    employee_email = result[0][2]  # Remove extra spaces
                    if employee_email is None or employee_email == "NULL":
                        employee_email = "BusinessandTechnologySolutionsDepartment@dept.sbcounty.gov"
                    employee = Employee(employee_id, employee_email, employee_name)
                else:
                    print("Unexpected result structure")
                    # Handle this case accordingly (e.g., log, raise an error, or assign default values)
            else:
                print("No result returned from the database")
                # Handle the case where no result is returned
        return employee
    
#another email for users without email to dpw it telling them that jon doe is trying to reset the email 
class Employee:
    def __init__(self, id, email, name):
        self.id = id
        self.name = name
        self.email = email
        



class Notifier:
    def __init__(self, connector):
        self.connector = connector

    def send_password_reset_email(self, employee_id):
        verifier = EmployeeVerifier(self.connector)
        employee = verifier.get_employee_details(employee_id)

        if employee:
            reset_link = create_reset_link(employee.id)
            names = employee.name.split(',')
            formatted_name = " ".join([name.capitalize() for name in names[::-1]])
            formatted_name = formatted_name.title()
            email_content = f"Hi {formatted_name},<br><br>Click <a href='{reset_link}'>here</a> to reset your password.<br><br>thank you"

            host = "192.168.117.135"
            from_address = "BusinessandTechnologySolutionsDepartment@dept.sbcounty.gov"
            subject = "Password Reset"

            message = MIMEMultipart()
            message['From'] = formataddr(('Sender Name', from_address))
            message['To'] = employee.email
            message['Subject'] = subject
            message.attach(MIMEText(email_content, 'html'))

            try:
                server = smtplib.SMTP(host, 25)
                server.send_message(message)
                print(f"Password reset email sent successfully to {employee.email}")
                server.quit()
            except Exception as e:
                print(f"Error sending email: {e}")
        else:
            print("Invalid employee ID")

    def send_password_change_note(self, employee_id):
        print(employee_id)
        verifier = EmployeeVerifier(self.connector)
        employee = verifier.get_employee_details(employee_id)

        if employee:
            names = employee.name.split(',')
            formatted_name = " ".join([name.capitalize() for name in names[::-1]])
            formatted_name = formatted_name.title()
            email_content = f"Hi {formatted_name.split(',')[0].strip()},<br><br>You're password has been changed if that's not you please contact our IT department Immediately<br><br>thank you"
            host = "192.168.117.135"
            from_address = "BusinessandTechnologySolutionsDepartment@dept.sbcounty.gov"
            subject = "Password Reset"

            message = MIMEMultipart()
            message['From'] = formataddr(('Sender Name', from_address))
            message['To'] = employee.email
            message['Subject'] = subject
            message.attach(MIMEText(email_content, 'html'))

            try:
                server = smtplib.SMTP(host, 25)
                server.send_message(message)
                print(f"Password reset email sent successfully to {employee.email}")
                server.quit()
            except Exception as e:
                print(f"Error sending email: {e}")
        else:
            print("Invalid employee ID")


def get_link_storage_instance():
    return LinkStorage()

def create_reset_link(employee_id):
    unique_key = generate_unique_key()
    current_time = datetime.now()
    expiry_time = current_time + timedelta(minutes=15)

    print(f"Link will expire at: {expiry_time}")

    link_data = LinkStorage(id=unique_key, employee_id=employee_id, expiry_time=expiry_time)
    db.session.add(link_data)
    db.session.commit()
    link = f"http://dpwapps.sbcounty.gov/WinCamsPasswordReset/resetpassword/{employee_id}/{unique_key}"

    return link

def generate_unique_key():
    return str(uuid.uuid4())

def is_link_valid(employee_id, unique_key):

    print(f"{employee_id=}, {unique_key=}")
    link_data = LinkStorage.query.filter_by(id=unique_key, employee_id=employee_id).first()
    print (f'{link_data=}')
    
    if link_data:
        current_time = datetime.now()
        expiry_time = link_data.expiry_time
        print ('is_link_valid', type(current_time),type(expiry_time))
        if current_time < expiry_time:
            print(current_time<expiry_time)
            return True  # Link is valid
    return False  # Link has expired or doesn't exist



class LinkStorage(db.Model):
    id = db.Column(db.String, primary_key=True)
    employee_id = db.Column(db.String)
    expiry_time = db.Column(db.DateTime)





class PasswordChanger:
    def __init__(self, connector):
        self.connector = connector

    def change_password(self, employee_id, new_password):
        if self.is_valid_password(new_password):
                result = self.connector.execute_stored_procedure("UpdateUserPassword", employee_id, new_password, fetch_type=False)
                return result
        else:
            return False

    def is_valid_password(self, new_password):
        # Check if password length is greater than or equal to 8
        if len(new_password) < 8:
            return False

        # Check if password contains at least one uppercase letter
        if not any(char.isupper() for char in new_password):
            return False

        # Check if password contains at least one lowercase letter
        if not any(char.islower() for char in new_password):
            return False

        # Check if password contains at least one special character
        special_characters = r"[!@#$%^&*(),.?\":{}|<>]"
        if not re.search(special_characters, new_password):
            return False

        # If all conditions pass, the password is valid
        return True
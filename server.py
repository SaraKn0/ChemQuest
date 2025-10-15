from flask import Flask, request, render_template, redirect, url_for, send_from_directory
from questions import get_printable_compound, validate_answer
from naming import validate_formula, get_formula_compound
import uuid
from chemlib import Compound, Element
import json
import random
import os

if not os.path.exists("student_data.json"):
    with open("student_data.json", "w") as f:
        f.write("{}")



app = Flask(__name__, static_url_path='/static')
session = {}

# ---------- HELPER FUNCTION ----------
def save_user_data(username, password, role, period=None):
    data_file = "student_data.json"
    try:
        with open(data_file, "r") as file:
            users = json.load(file)
    except FileNotFoundError:
        users = {}

    if username not in users:
        users[username] = {
            "password": password,
            "role": role,
            "period": period,
            "scores": {
                "naming": {"correct": 0, "attempts": 0},
                "formula": {"correct": 0, "attempts": 0}
            }
        }
    else:
       redirect(url_for('student_dashboard')) #Prevents a new user from being made when someone logs in again

    with open(data_file, "w") as file:
        json.dump(users, file, indent=4)


# ---------- ROUTES ----------
@app.route('/')
def home():
    return render_template('student.html')

@app.route('/choose_role')
def choose_role():
    return render_template('index.html')

@app.route('/teacher_login')
def teacher_login():
    return render_template('teacher_login.html')

@app.route('/student_login')
def student_login():
    return render_template('student_login.html')

@app.route('/student_login_submit', methods=['POST'])
def student_login_submit():
    username = request.form.get('uname')
    password = request.form.get('psw')

    session['username'] = username

    try:
        with open("student_data.json", "r") as file:
            users = json.load(file)
    except FileNotFoundError:
        users = {}
    
    # Redirect to period selection if it's not set
    if username not in users or not users[username].get("period"):
        session['password'] = password
        return redirect(url_for('select_period_student'))

    return redirect(url_for('student_dashboard'))

@app.route('/select_period_student', methods=['GET', 'POST'])
def select_period_student():
    if request.method == 'POST':
        period = request.form.get('period')
        username = session.get('username')
        password = session.get('password')
        save_user_data(username, password, role='Student', period=period)
        return redirect(url_for('student_dashboard'))

    return render_template("select_period_student.html")

@app.route('/teacher_login_submit', methods=['POST'])
def teacher_login_submit():
    username = request.form.get('uname')
    password = request.form.get('psw')
    session['username'] = username
    save_user_data(username, password, role='Teacher')
    return redirect(url_for('teacher_dashboard'))

@app.route('/student_dashboard')
def student_dashboard():
    username = session.get('username', 'Guest')
    return render_template("student_dashboard.html", username=username)

@app.route('/teacher_dashboard')
def teacher_dashboard():
    username = session.get('username', 'Teacher')
    return render_template("teacher_dashboard.html", username=username)

#generate random token, dictionary 
section = {}
teacher_token = str(uuid.uuid4())
@app.route('/manage_students', methods=['GET', 'POST'])
def manage_students():
    """
    Takes teacher to the manage students page, to view and delete students
    Returns:
        HTML page for teacher to selected period
        HTML page for teacher to view and delete students 
    """
    if request.method == 'POST':
        
        if 'period' in request.form:
            
            selected_period = request.form.get('period')


            #Store the period under the section of the token
            section[teacher_token] = {"period" : selected_period}

            with open("student_data.json", "r") as file:
                data = json.load(file)

            students_in_period = [name for name, info in data.items() if info.get("period") == selected_period and info.get("role") == "Student"]

            return render_template("manage_students.html", students=students_in_period, period=selected_period)

        #Trying to delete student - teacher 
        elif 'student' in request.form:
            #Get which student teacher is trying to delete 
            student_to_delete = request.form.get('student')
            #Open section at the index of the token
            dete = section.get(teacher_token, {})
            #Get the period student is being deleted from 
            selected_period = dete.get("period", "")

            #Open the json file 
            with open("student_data.json", "r") as file:
                data = json.load(file)
            #If student is in file, delete the student 
            if student_to_delete in data:
                del data[student_to_delete]

                #Change json file - student now deleted 
                with open("student_data.json", "w") as file:
                    json.dump(data, file, indent=4)
                #Reopen json file
                with open("student_data.json", "r") as file:
                    data = json.load(file)

            #Access all the students in the period, after deletion 
            students_in_period = [name for name, info in data.items() if info.get("period") == selected_period and info.get("role") == "Student"]
            
            #Return html file of manage students page, with new students 
            return render_template("manage_students.html", students=students_in_period, period=selected_period)
    #Where teacher can select period 
    return render_template("select_period_teacher.html")

#Formula to name 
@app.route("/questions", methods=["GET", "POST"])
def chemQuest():
    """
    Returns questions and gets + validates user's answer, given formula enter name.
    GET: return question to user
    POST: get user's answer 
    Returns:
        HTML page with question, user_token, answer (is answer correct or incorrect)

    """
    

    #Getting compound + name 
    if request.method == "GET":
        
        #Generating token, to save information for speciific question 
        user_token = str(uuid.uuid4())

        #Generating compoiund + correct answer, if compound is covalent or ionic 
        string_compound, compound_answer, compound_type = get_printable_compound()
        #Generate question 
        question = "Enter the name of the compound. If it is a transition metal, use the stock method with an 'I' as a roman numeral:\n" + string_compound
        
        #Store question, answer, and type of compound with the token 
        session[user_token] = {"question": question, 
                               "answer": compound_answer.lower(),
                               "type": compound_type
                               }
        #Return to HTML file 
        return render_template("questions.html", question=question, token=user_token)

    #Getting answer from user 
    elif request.method == "POST":
        #Get user_token, to find which answer is the correct 
        user_token = str(request.form["token"])
        #Get the user's inputted answer
        user_answer = str(request.form["answer"]).lower()

        data = session.get(user_token, {})

        #Get the question  
        question = data.get("question", "")
        #Get the correct answer 
        correct_answer = data.get("answer", "")

        #Check is user_answer matches correctt_answer, if yes answer is correct, else it is incorrect 
        result = "Correct!" if validate_answer(user_answer, correct_answer) else "Incorrect"

        #Get user's username - to update their scores 
        username = session.get('username')
        if username:

            #Open json file, access all the user 
            with open("student_data.json", "r") as f:
                users = json.load(f)
            
            if username in users:

                #At the naming: attempts section of the user's info, add 1
                users[username]['scores']['naming']['attempts'] += 1

                #If user is correct, under correct section of their info 
                if result == "Correct!":
                    users[username]['scores']['naming']['correct'] += 1
                #Add all information into json file 
                with open("student_data.json", "w") as f:
                    json.dump(users, f, indent=4)
                #Access user's correct and attempts  
                score_data = users[username]['scores']['naming']
                #Save - correct/total attempts
                score = f"{score_data['correct']}/{score_data['attempts']}"
            else:
                score = "-"
        else:
            score = "-"
        
        #Return to html file - whether answer was correct or not, question, token, their current score
        return render_template("questions.html", answer=result, question=question, token=user_token, score=score)

#Given name, enter formula 
@app.route("/name-to-formula", methods=["GET", "POST"])
def nametoform():
    """
    Returns questions and gets + validates user's answer, given name enter formula.
    GET: return question to user
    POST: get user's answer 
    Returns:
        HTML page with question, user_token, answer (is answer correct or incorrect)

    """
    if request.method == "GET":
        #Generate token
        user_token = str(uuid.uuid4())
        #Get the formula, name of compound, actual compound, compound type 
        formula_answer, compoundname, formula, compound_type = get_formula_compound()
        #Question
        question = "Enter the formula for: \n" + compoundname
        #Under user_token in session dict, store question, answer, formula, compound type
        session[user_token] = {"question": question, "answer": formula_answer, "formula": formula, "type": compound_type}
        #Return to naming html file - question and token
        return render_template("naming.html", question=question, token=user_token)

#When user submits answer
    elif request.method == "POST":
        #get token
        user_token = str(request.form["token"])
        #get user's answer they submitted
        user_answer = str(request.form["answer"])
        #Get info from user_token
        data = session.get(user_token, {})
        #Get question
        question = data.get("question", "")
        #Get answer
        correct_answer = data.get("answer", "")
        #Check if answer is correct or incorrect
        result = "Correct!" if validate_formula(user_answer, correct_answer) else "Incorrect"
        
        #GEt user's username 
        username = session.get('username')
        if username:
            #Access user info in json file 
            with open("student_data.json", "r") as f:
                users = json.load(f)
            if username in users:
                #At attempts - formula section for user, append by 1
                users[username]['scores']['formula']['attempts'] += 1
                #If correct, append correct in fomula sect for user
                if result == "Correct!":
                    users[username]['scores']['formula']['correct'] += 1
                #Add all info to json file 
                with open("student_data.json", "w") as f:
                    json.dump(users, f, indent=4)
                #Access scores
                score_data = users[username]['scores']['formula']
                score = f"{score_data['correct']}/{score_data['attempts']}"
        #Return incorrect or correct, question, token, and score to html file 
        return render_template("naming.html", answer=result, question=question, token=user_token, score = score)

#When user clicks get answer for naming 
@app.route("/get-answer", methods=["GET"])
def getAnswer():
    """
    When user clicks get answer - to show user the answer (name)
    Returns:
        HTML page, showing the correct answer
    """
    #Get user's token
    user_token = request.args.get("token", "")
    #Get their question
    question = session.get(user_token, {}).get("question", "")
    #Get correct answer
    correct_answer = session.get(user_token, {}).get("answer", "")
    #Return to html page - question, correct answer, token 
    return render_template("questions.html", question=question, answer=correct_answer, token=user_token)

#When user clicks get answer for formula 
@app.route("/get-formula", methods=["GET"])
def getFormula():
    """
    When user clicks get answer - to show user the answer (formula)
    Returns:
        HTML page, showing the correct answer
    """
    #Get user token, question, correct answer 
    user_token = request.args.get("token", "")
    question = session.get(user_token, {}).get("question", "")
    correct_answer = session.get(user_token, {}).get("formula", "")
    #Return to html page question, answer, token
    return render_template("naming.html", question=question, answer=correct_answer, token=user_token)

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)


    
@app.route("/questions_hint", methods=["POST"])
def questions(): 
    """
    Provides hints for formula to name questions based on compound type

    Returns:
    - random hint specific to the current question type
    
    """
    #get session token from the form data
    token = request.form.get("token", "")
    #retreive question data from the session using token
    data = session.get(token, {})
    #extract question text and type (default is "generic" if not found)
    question = data.get("question", "")
    qtype = data.get("type", "generic") 
 
    #dictionary of hint categories and their corresponding hints
    hints = {
        

        "covalent": [
            "Use prefixes (mono-, di-, tri-) to show the number of atoms",
            "The first element keeps its name; the second ends in -ide",
            "Don’t simplify subscripts — match them to the correct prefix"
        ],

        "ionic": [
            "Name the metal first, then the non-metal with -ide",
            "Do not use prefixes — ionic names don't use them",
            
        ],

        "transition": [
            "Use the charges to determine the Roman numeral for the metal",
            "Name the metal first, followed by the non-metal or polyatomic ion",
            "The non-metal still ends in -ide if it's a single element"
        ],

        "generic": [
            "Make sure the name matches the number of atoms or charges",
            "Check for prefixes, Roman numerals, or polyatomic ions to guide you"
        ]
    }

    #select random hint from appropriate category
    random_hint = random.choice(hints.get(qtype, hints["generic"]))
    #return the template with the hint, maintaining the current question and token
    return render_template("questions.html", hint=random_hint, question=question, token=token)



@app.route("/naming_hint", methods=["POST"])
def naming():  
    """
    Provides hints for the name-to-formula questions based on compound type.

    Returns:
    - Random hint specific to the current question type
    """
    #Gets session token from the form data
    token = request.form.get("token", "")
    #Retrieve question data from the session using the token
    data = session.get(token, {})
    #Extract question text and type (default to "generic" is not found)
    question = data.get("question", "")
    qtype = data.get("type", "generic") 

    #Dictionary of hint categories and their corresponding hints
    hints = {
        "covalent": [
            "Use prefixes like mono-, di-, tri- to decide subscripts",
            "Write element symbols in the same order as the name",
            "Do not simplify subscripts — they match the prefixes exactly",
            "Ignore charges — covalent compounds don’t use them"
        ],

        "ionic": [
            "Look up the charges of the metal and non-metal",
            "Criss-cross the charges to get subscripts",
            "Simplify subscripts to the lowest whole number ratio"
        ],

        "transition": [
            "The Roman numeral shows the metal's positive charge",
            "Use the Roman numeral and the anion charge to balance and find subscripts",
            "Criss-cross the charges and simplify if needed",
            "Don’t use prefixes for transition metals"
        ],

        "generic": [
            "Make sure the charges balance out to zero",
            "Use subscripts based on charge or prefixes depending on the type",
            "Check if it's covalent, ionic, or transition before writing"
        ]
    }

    #select a random hint from appropriate category
    random_hint = random.choice(hints.get(qtype, hints["generic"]))
    #Render the template with the hint, maintaining current question and token
    return render_template("naming.html", hint=random_hint, question=question, token=token)


   
#To clear scores when user goes to new practice 
@app.route("/clicked/<link_id>")
def clicked(link_id):
    """
    Verifies which practice student has clicked to reset their scores, send them to that practice.
    Args:
        link_id (str)
    Returns:
        HTML file to formula to name practice or name to formula practice
    """
    #If link clicked is for naming - get their username 
    if link_id == "formtoname":
        username = session.get('username')
        if username:
            #Open json file, to access all users
            with open("student_data.json", "r") as f:
                users = json.load(f)
            #Reset user's naming scores 
            if username in users:
                users[username]['scores']['naming']['attempts'] = 0
                
                users[username]['scores']['naming']['correct'] = 0
                with open("student_data.json", "w") as f:
                    json.dump(users, f, indent=4)
        #Send user to practice for naming 
        return redirect(url_for('chemQuest'))
    #If linked clicked is to practice formulas - get their username 
    elif link_id == "nametoform":
        username = session.get('username')
        #Open json file, access users 
        if username:
            with open("student_data.json", "r") as f:
                users = json.load(f)
            #Reset score for formula 
            if username in users:
                users[username]['scores']['formula']['attempts'] = 0
                
                users[username]['scores']['formula']['correct'] = 0
                with open("student_data.json", "w") as f:
                    json.dump(users, f, indent=4)
        #Send user to formula practice 
        return redirect(url_for("nametoform"))

#Teacher dashboard - view students progress in naming 
@app.route("/naming-progress", methods = ["GET", "POST"])
def naming_progress():
    """
    Teachers can view class progress in naming compounds.
    Returns:
        HTML of naming progress, students scores (list)
    """
    #User clicks button 
    if request.method == 'POST':

        #Get period teacher selected  
        selected_period = request.form.get('period')

        #Access users 
        with open("student_data.json", "r") as file:
            data = json.load(file)

        #Get all students in that period 
        students_in_period = [name for name, info in data.items() if info.get("period") == selected_period and info.get("role") == "Student"]
        correct_in_period = []
        attempts_in_period = []
        #For each student in the period, get the number of correct and attempts, store values in a list
        for i in students_in_period:
            x = data[i].get("scores").get("naming").get("correct")
            y = data[i].get("scores").get("naming").get("attempts")
            correct_in_period.append(x)
            attempts_in_period.append(y)
        
        #Join lists into one object 
        total = zip(students_in_period, correct_in_period, attempts_in_period)
        #Return to html file to view progress
        return render_template("naming_progress.html", total=total)
    #Where teacher can select student
    return render_template("select_period_teacher.html")



#For teachers - view students progress with formula 
@app.route("/formula-progress", methods = ["GET", "POST"])
def formula_progress():
    """
    Teachers can view class progress in getting formula.
    Returns:
        HTML of naming progress, students scores (list)
    """
    #USer clicks button
    if request.method == 'POST':

        #Get which period teacher selects 
        selected_period = request.form.get('period')

        #Access all students 
        with open("student_data.json", "r") as file:
            data = json.load(file)

        #GEt all students in period
        students_in_period = [name for name, info in data.items() if info.get("period") == selected_period and info.get("role") == "Student"]
        correct_in_period = []
        attempts_in_period = []
        #Add each students correct and attempts to a list
        for i in students_in_period:
            x = data[i].get("scores").get("formula").get("correct")
            y = data[i].get("scores").get("formula").get("attempts")
            correct_in_period.append(x)
            attempts_in_period.append(y)
        
        #Combine into one object, send to html file
        total = zip(students_in_period, correct_in_period, attempts_in_period)
        return render_template("formula_progress.html", total=total)
    #Where teacher selects period
    return render_template("select_period_teacher.html")



if __name__ == '__main__':
    app.run(debug=True)
 
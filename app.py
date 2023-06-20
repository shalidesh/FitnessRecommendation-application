from flask import Flask,flash, render_template, url_for, request,flash,redirect,Response,send_from_directory,jsonify,session
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import os
import random
import json
from functools import wraps
from flask_pymongo import PyMongo
import uuid
from passlib.hash import pbkdf2_sha256
from flask_session import Session
import http.client
from chat import get_response

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

app.config["SECRET_KEY"] = "db24c608640f5034b30b8e1e1eb5618ed0ffdbf5"
app.config["MONGO_URI"] = "mongodb://localhost:27017/fitnessapp"
db = PyMongo(app).db

  
data=pd.read_csv('dataset/data.csv')
df=pd.read_csv('dataset/original.csv')

dietdata=pd.read_csv('dataset/diet_data.csv')
dietdf=pd.read_csv('dataset/dietoriginal.csv')

@app.route("/")
def hello_world():

    return render_template('index.html')
    
@app.route("/bmi")
def bmi():
    return render_template('bmi.html')

def calculate_bmi(weight, height):
    bmi = weight / (height ** 2)
    if bmi < 18.5:
        return bmi, 'Underweight'
    elif bmi < 25:
        return bmi, 'Normal weight'
    elif bmi < 30:
        return bmi, 'Overweight'
    else:
        return bmi, 'Obese'
    

@app.route("/bmi/calculate",methods=['POST'])
def bmical():

    height= request.form.get('height')
    weight= request.form.get('weight')

    bmi, weight_category = calculate_bmi(float(weight), float(float(height)/100))
    
    return render_template('bmi.html',bmi=bmi,weight_category=weight_category)
    

@app.route('/user/signup', methods=['POST'])
def signup():
  
  user = {
      "_id": uuid.uuid4().hex,
      "name": request.form.get('name'),
      "email": request.form.get('email'),
      "password": request.form.get('password')
    }


  if db.users.insert_one(user):
       return redirect('/login')
  else:

    return jsonify({ "error": "Signup failed" }), 400
  

@app.route('/signup')
def signupPage():
  return render_template('signup.html')

@app.route('/login')
def loginPage():
  return render_template('login.html')

@app.route("/logout")
def logout():
    session["name"] = None
    return redirect('/')

@app.route("/chat",methods=['POST'])
def chat():
    text=request.get_json().get("message")
    print(text)
    reponse=get_response(text)
    message={"answer":reponse}
    print(message)
    return jsonify(message)

@app.route('/user/login', methods=['POST'])
def login():
    email = request.form["email"]
    password = request.form["password"]
    user = db.users.find_one({"email": email, "password": password})
    if user :
        session["name"] = request.form.get("email")
        return redirect('/')
    else:
        error = 'Invalid credentials'
        flash(error, 'error')
        return render_template('login.html', error=error)
  
@app.route("/diet")
def diet():
    return render_template('diet.html')



@app.route('/predictdiet', methods=['POST'])
def dietplan():
    gender = request.form['gender']
    age = request.form['age']
    activity = request.form['activity']
    restriction = request.form['restriction']
    goal = request.form['goal']
    bmi = request.form['bmi']

    gender_female=[]
    gender_male=[]
    age_20_30=[]
    age_30_50=[]
    age_above_50=[]
    activity_level_active=[]
    activity_level_sedentary =[]
    main_goal_muscle_gain=[]
    main_goal_weight_loss=[]
    restriction_nonVeg=[]
    restriction_veg=[]

    if gender=="male":
        gender_male.append(1)
    else:
        gender_female.append(1)

    if age=="20_30":
        age_20_30.append(1)
    elif age=='30_50':
        age_30_50.append(1)
    else:
        age_above_50.append(1)

    if activity=="active":
        activity_level_active.append(1)
    else:
        activity_level_sedentary.append(1)

    if goal=="muscle_gain":
        main_goal_muscle_gain.append(1)
    else:
        main_goal_weight_loss.append(1)

    if restriction=="nonVeg":
        restriction_nonVeg.append(1)
    else:
        restriction_veg.append(1)

    my_series1 = pd.Series(gender_female)
    my_series2 = pd.Series(gender_male)
    my_series3 = pd.Series(age_20_30)
    my_series4 = pd.Series(age_30_50)
    my_series5 = pd.Series(age_above_50)
    my_series6 = pd.Series(activity_level_active)
    my_series7 = pd.Series(activity_level_sedentary)
    my_series8 = pd.Series(main_goal_muscle_gain)
    my_series9 = pd.Series(main_goal_weight_loss)
    my_series10 = pd.Series(restriction_nonVeg)
    my_series11 = pd.Series(restriction_veg)


    my_dict = {'gender_female': my_series1, 
            'gender_male':my_series2,
            'age_20_30':my_series3,
            'age_30_50':my_series4,
            'age_above_50':my_series5,
            'activity_level_active':my_series6,
            'activity_level_sedentary':my_series7,
            'main_goal_muscle_gain':my_series8,
            'main_goal_weight_loss':my_series9,
            'restriction_nonVeg':my_series10,
            'restriction_veg':my_series11,
        
            }
    my_dataframe1 = pd.DataFrame(my_dict)
    my_dataframe1.fillna(int(0), inplace=True)
    row_to_compare = my_dataframe1.iloc[0].values.reshape(1, -1)
    similarities = cosine_similarity(dietdata, row_to_compare)
    most_similar_row_index = similarities.argmax()
    most_similar_row1=dietdf.iloc[most_similar_row_index]

    plan=most_similar_row1['diet_plan']
    directory = './static/images/planimages'
    files = os.listdir(directory)
    random_file = random.choice(files)
    print(random_file)
    print(plan)



    return render_template('diet.html',file=plan,image=random_file)

@app.route('/predict', methods=['POST'])
def index():

    if request.method == 'POST':
       
        # if 'file' not in request.files:
        #     flash('No file part')
        #     return redirect('/')
        gen = request.form['gender']
        age = request.form['age']
        # height = request.form['height']
        # weight = request.form['weight']
        fitness = request.form['fitness']
        area = request.form['group']
        goal = request.form['goal']
        location = request.form['location']
        day = request.form['day']

        gender_Female=[]
        gender_Male=[]
        focus_area_abs=[]
        focus_area_arm=[]
        focus_area_chest=[]
        focus_area_fullbody=[]
        focus_area_leg=[]
        main_goal_build_muscle=[]
        main_goal_loss_weight=[]
        workout_location_Gym=[]
        workout_location_Home=[]
        
        if gen=="Male":
            gender_Male.append(1)
        else:
            gender_Female.append(1)
      
        if area=="fullbody":
            focus_area_fullbody.append(1)
            
        elif area=="arm":
            focus_area_arm.append(1)
        elif area=="chest":
            focus_area_chest.append(1)
        elif area=="abs":
            focus_area_abs.append(1)
        else:
            focus_area_leg.append(1)

        if goal=='loss_weight':
            main_goal_loss_weight.append(1)
        else:
            main_goal_build_muscle.append(1)

        if location=='gym':
            workout_location_Gym.append(1)
        else:
            workout_location_Home.append(1)

        
        my_series1 = pd.Series(gender_Female)
        my_series2 = pd.Series(gender_Male)
        my_series3 = pd.Series(focus_area_abs)
        my_series4 = pd.Series(focus_area_arm)
        my_series5 = pd.Series(focus_area_chest)
        my_series6 = pd.Series(focus_area_fullbody)
        my_series7 = pd.Series(focus_area_leg)
        my_series8 = pd.Series(main_goal_build_muscle)
        my_series9 = pd.Series(main_goal_loss_weight)
        my_series10 = pd.Series(workout_location_Gym)
        my_series11 = pd.Series(workout_location_Home)


        my_dict = {'gender_Female': my_series1, 
                'gender_Male':my_series2,
                'focus_area_abs':my_series3,
                'focus_area_arm':my_series4,
                'focus_area_chest':my_series5,
                'focus_area_fullbody':my_series6,
                'focus_area_leg':my_series7,
                'main_goal_build_muscle':my_series8,
                'main_goal_loss_weight':my_series9,
                'workout_location_Gym':my_series10,
                'workout_location_Home':my_series11,
            
                }
        my_dataframe1 = pd.DataFrame(my_dict)
        my_dataframe1.fillna(int(0), inplace=True)

        row_to_compare = my_dataframe1.iloc[0].values.reshape(1, -1)
        similarities = cosine_similarity(data, row_to_compare)

        most_similar_row_index = similarities.argmax()
        # print(most_similar_row_index)
        # print(df.columns)
        # print(data.columns)
        # print(my_dataframe1.columns)

        most_similar_row1=df.iloc[most_similar_row_index]

        plan=most_similar_row1['workout_plan']
        # print(plan)
        print(most_similar_row1)
        directory = './static/images/planimages'
        files = os.listdir(directory)
        random_file = random.choice(files)
        print(random_file)
    

             
    return render_template('index.html',file=plan,image=random_file)


@app.route('/plan/<path:filename>', methods=['GET', 'POST'])
def plan(filename):
    name = filename.split('-')[0]
    print(name)
    if name=='Female':
        directory = './static/images/girls'
        files = os.listdir(directory)
        random_file = 'girls/'+random.choice(files)
        print(random_file)
    else:
        directory = './static/images/boys'
        files = os.listdir(directory)
        random_file = "boys/"+random.choice(files)
        print(random_file)
    
    with open('./database.json', 'r') as file:
        data = json.load(file)

    location=data[filename]['Workout Location']
    duration=data[filename]['Duration']
    warmup=data[filename]['Warm-Up']
    workout=data[filename]['Workout']
    cooldown=data[filename]['Cool Down']

    
    return render_template('plan.html',location=location,duration=duration,warmup=warmup,workout=workout,cooldown=cooldown,image=random_file)


@app.route('/getdietplan/<path:filename>', methods=['GET', 'POST'])
def getdietplan(filename):
    
    directory = './static/images/food'
    files = os.listdir(directory)
    random_file = 'food/'+random.choice(files)
    print(random_file)
    
    
    with open('./dietdatabase.json', 'r') as file:
        data = json.load(file)

    for document in data:
        if document['name'] == filename:
            breakfast=document['breakfast']
            mid_morning_snack=document['mid_morning_snack']
            lunch=document['lunch']
            AfternoonSnack=document['Afternoon Snack']
            dinner=document['dinner']

    

    
    return render_template('dietplan.html',breakfast=breakfast,mid_morning_snack=mid_morning_snack,lunch=lunch,AfternoonSnack=AfternoonSnack,dinner=dinner,image=random_file)
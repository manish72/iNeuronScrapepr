from flask import Flask, render_template, request,jsonify
from flask_cors import CORS,cross_origin
import requests
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen as uReq
import logging
import iNeuronReviewScrapper as ineuron

logging.basicConfig(filename="logs/scrapper.log" , level=logging.INFO)

app = Flask(__name__)

@app.route("/", methods = ['GET','POST'])
def homepage():
    scrapper = ineuron.iNeuronReviewScrapper()    
    category_list = scrapper.courses_list_by_category
    return render_template("index.html", result = category_list)

@app.route("/subcategory", methods = ['GET'])
def fetchCourseList():
    subID = request.args['id']
    scrapper = ineuron.iNeuronReviewScrapper()  
    return render_template("courseslist.html",result=scrapper.fetch_courses_by_subCategory(subID))

@app.route("/course", methods = ['GET'])
def fetchCourse():
    course = request.args['coursename']
    scrapper1 = ineuron.iNeuronReviewScrapper()
    courseDetails = scrapper1.scrap_one_courseInfo(course)
    #print(courseDetails)
    return render_template("coursedetails.html",result=courseDetails)
    

if __name__=="__main__":
    app.run(host="0.0.0.0",port=5003)

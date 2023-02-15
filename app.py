from flask import Flask, render_template, request, send_from_directory
from flask_cors import CORS,cross_origin
from flask import make_response
import requests
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen as uReq
import logging
import iNeuronReviewScrapper as ineuron
import pdfkit

logging.basicConfig(filename="scrapper.log" , level=logging.INFO)

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

@app.route("/course", methods = ['GET','POST'])
def fetchCourse():
    course = request.args['coursename']
    scrapper1 = ineuron.iNeuronReviewScrapper()
    courseDetails = scrapper1.scrap_one_courseInfo(course)
    html = render_template("coursedetails.html", result=courseDetails)
    # PDF options
    options = {
        "orientation": "portrait",
        "page-size": "A4",
        "margin-top": "1.0cm",
        "margin-right": "1.0cm",
        "margin-bottom": "1.0cm",
        "margin-left": "1.0cm",
        "encoding": "UTF-8",
        "enable-local-file-access": ""
    }
    # wkhtmltopdf windows installation location ---> C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe
    config = pdfkit.configuration(wkhtmltopdf = "wkhtmltopdf.exe")
    pdf = ""
    response = ""
    try:
        pdf = pdfkit.from_string(html,'PDFs/'+course+'.pdf',options=options,css='static/css/style.css', configuration=config)
        #response = make_response(pdf)
        #response.headers['Content-Type']='application/pdf'
    except Exception as e :
        logging.info(e)
    #return send_from_directory('PDFs/',course+'.pdf', as_attachment=True) 
    return render_template("coursedetails.html",result=courseDetails)
    

if __name__=="__main__":
    app.run(host="0.0.0.0",port=5003)

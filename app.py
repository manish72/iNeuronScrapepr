from flask import Flask, render_template, request
import os
from flask_cors import cross_origin
from urllib.request import urlopen as uReq
import logging
import iNeuronReviewScrapper as ineuron
import pdfkit
import boto3

logging.basicConfig(filename="scrapper.log" , level=logging.INFO, format='%(asctime)s:%(filename)s:(%(funcName)s):[%(lineno)d]:%(levelname)s:%(message)s')

app = Flask(__name__)

@app.route("/", methods = ['GET','POST'])
@cross_origin()
def homepage():
    logging.info("Getting Home page")
    scrapper = ineuron.iNeuronReviewScrapper()    
    category_list = scrapper.courses_list_by_category
    
    if category_list:
        logging.info("Retreived list of sub-categories using category")
        return render_template("index.html", result = category_list)
    else:
        logging.info("An error occured getting information")
        return render_template("servererror.html",result = "An error occured getting information")

@app.route("/subcategory", methods = ['GET'])
@cross_origin()
def fetchCourseList():
    logging.info("Getting Courses list page using sub-category ID")
    subID = request.args['id']
    scrapper = None

    if subID:
        scrapper = ineuron.iNeuronReviewScrapper() 
        logging.info("Sub-category ID found, getting information...")
        return render_template("courseslist.html",result=scrapper.fetch_courses_by_subCategory(subID))
    else:
        logging.info("Sub-category ID not found")
        return render_template("servererror.html",result = "Sub-category ID not found")

@app.route("/course", methods = ['GET','POST'])
@cross_origin()
def fetchCourse():
    course = request.args['coursename']
    if course:
        scrapper1 = ineuron.iNeuronReviewScrapper()
        courseDetails = scrapper1.scrap_one_courseInfo(course)
        if courseDetails:
            html = render_template("coursedetails.html", result=courseDetails)
            
            try:
                # wkhtmltopdf windows installation location ---> C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe
                config = pdfkit.configuration(wkhtmltopdf = "wkhtmltopdf.exe")
                pdf = ""
                response = ""
                try:
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
                    logging.info("checking if PDFs folder exists or not..")
                    if not os.path.isdir('PDFs/'):                        
                        os.mkdir('PDFs/')
                        logging.info("created folder PDFs ...")
                    else:
                        logging.info("folder exists PDFs ...")
                    pdf = pdfkit.from_string(html,'PDFs/'+course+'.pdf',options=options,css='static/css/style.css', configuration=config)
                except Exception as e :
                    logging.info("An error occured , refer error message below ...")
                    logging.info(e)
                
                try:
                    s3 = boto3.client("s3")
                    s3.upload_file(Filename='PDFs/'+course+'.pdf',Bucket="ineuron-course-pdfs",Key='PDFs/'+course+'.pdf')
                except Exception as e:
                    logging.info("Error occured at amazon s3, refer error message below ...")
                    logging.info(e)
            except Exception as e:
                logging.info(e)
            return render_template("coursedetails.html",result=courseDetails)
        else:
            return render_template("servererror.html",result = "Unable to find course information")
    else:
        return render_template("servererror.html",result = "Course not found")

if __name__=="__main__":
    app.run(host="0.0.0.0",port=5003)    

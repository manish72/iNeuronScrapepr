from flask import Flask, render_template, request,jsonify
from flask_cors import CORS,cross_origin
import requests
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen as uReq
import json
import configuration as mongoConfig
import pymongo
import logging

#logging.basicConfig(filename="logs/"+__name__+".log" , level=logging.INFO)

class iNeuronReviewScrapper:
    
    def __init__(self):
        '''
            initialize the variables course_categories_list, courses_list_by_category and rootURL with ineuron website https://ineuron.ai
        '''
        logging.info("Inside Constructor and initializing required details")
        self.course_categories_list = list()
        self.courses_list_by_category = dict()
        self.store_courses_by_category = list()
        self.total_courses_json = dict()
        self.store_instructors = list()
        self.rootURL = 'https://ineuron.ai'
        self.ineuron_html = self.getRootPage()
        self.create_courses_lists()
        self.fetch_all_instructors()
        self.userid = mongoConfig.MONGO_USER_ID
        self.password = mongoConfig.MONGO_PASSWORD
        self.DOMAIN = mongoConfig.MONGO_DOMAIN
        self.TAIL_URL = mongoConfig.MONGO_TAIL_URL
        logging.info("Constructor execution completed")  
        
    def connect(self):
        '''
            Method used to connect to MongoDB
        '''
        url = self.DOMAIN + self.userid+':' + self.password + self.TAIL_URL
        client  = pymongo.MongoClient(url)
        return client
    
    def getRootPage(self):
        '''
          Fetch the ineuron website page from https://ineuron.ai and return the HTML page
        '''
        try:
            uclient = uReq(self.rootURL)
            ineuron_page = uclient.read()
            logging.info("Retreived ineuron page information")
        except Exception as e:
            logging.info("Unable to retreive ineuron page information")
        return bs(ineuron_page,"html.parser")
    
    def create_courses_lists(self):
        '''
            Fetch and store the list of courses based on category and its sub-categories. Also fetches all the courses.
        '''
        logging.info("Fetching list of all courses")
        self.store_entire_json = self.ineuron_html.find_all('script',{'type':'application/json'})[0].text # extract JSON
        self.store_entire_json = json.loads(self.store_entire_json) #convert entire string JSON to JSON
        store_courses_json = self.store_entire_json['props']['pageProps']['initialState']['init']['categories'] # store categories and its details
        
        self.total_courses_json = self.store_entire_json['props']['pageProps']['initialState']['init']['courses'] #extract all courses list
        
        # filter data based on category and sub-categories
        for i in store_courses_json.keys():
            self.course_categories_list.append(store_courses_json[i]['title']) # fetch course categories
            courses_list = list()
            for j in store_courses_json[i]['subCategories']:
                courses_list.append(store_courses_json[i]['subCategories'][j]) # fetch and store each sub category related to category
            self.courses_list_by_category[store_courses_json[i]['title']] = courses_list # store list of categories and its sub-categories inside a list
        logging.info("Course details fetched successfully")
    
    #def fetch_sub_categories(self,categoryName):
        '''
            fetch all sub-category courses based on categoryName
        '''
        #self.course_input_list = self.courses_list_by_category[self.course_categories_list[self.course_categories_list.index(categoryName)]]
        
    
    def fetch_courses_by_subCategory(self,subCategoryId):
        '''
            Lists all courses based on sub-category id        
        '''        
        logging.info("Fetching list of courses using sub-category")
        for j in self.total_courses_json.keys():
            if subCategoryId == self.total_courses_json[j]['categoryId']:
                fetch_course_info = dict()            
                fetch_course_info['categoryId'] = self.total_courses_json[j]['categoryId']
                fetch_course_info['courseName'] = j
                fetch_course_info['description'] = self.total_courses_json[j]['description']
                fetch_course_info['mode'] = self.total_courses_json[j]['mode']
                fetch_course_info['language'] = self.total_courses_json[j]['courseMeta'][0]['overview']['language']
                fetch_course_info['instructorsDetails'] = list()
                for k in self.total_courses_json[j]['instructorsDetails']:
                    instructor = dict()
                    instructor['name'] = k['name']
                    fetch_course_info['instructorsDetails'].append(instructor)
                self.store_courses_by_category.append(fetch_course_info)
        if not self.store_courses_by_category:
            logging.info("No courses found for the sub-category")
        return self.store_courses_by_category
            
    def fetch_all_instructors(self):
        '''
            Fetches all instructor details and store in a list
        '''
        fetch_instructors = self.store_entire_json['props']['pageProps']['initialState']['init']['instructors']
        for i in fetch_instructors.keys():
            instructor = dict()  
            try:
                instructor['id'] = i
                instructor['name'] = fetch_instructors[i]['name']
                instructor['description'] = fetch_instructors[i]['description']
                instructor['email'] = fetch_instructors[i]['email']
            except KeyError as e:
                instructor['email'] = fetch_instructors[i]['email']
            self.store_instructors.append(instructor)
        if not self.store_instructors:
            logging.info("No instructors found")
    
    def scrap_one_courseInfo(self,courseName):
        '''
            Scrap all the details of course based on courseName
        '''
        logging.info("-------Inside scrap one course method----------")
        logging.info(f"Fetching course ---> {courseName}")
        res = requests.get(self.rootURL + '/course/' + courseName.replace(' ','-'))
        course_html = bs(res.text,'html.parser')
        store_course_json = course_html.find_all('script',{'type':'application/json'})[0].text
        store_course_json = json.loads(store_course_json)
        store_course_json = store_course_json['props']['pageProps']['data']
        logging.info("invoking course details method")
        try:
            fetch_course = self.course_details(store_course_json)
            try:
                connection = self.connect()
                logging.info("Connected to mongo DB")
            except Exception as e:
                logging.info("Error occured while connecting to MongoDB")
            db = connection['test_scrapper']
            course = db['courses']
            if not course.find_one({'title' : fetch_course['title']}):
                course.insert_one(fetch_course)
                logging.info(f"Inserted course --> {fetch_course['title']} in MongoDB")
            else:
                logging.info("Course exists in MongoDB")
            connection.close()
            logging.info("Disconnected from mongo DB")
        except Exception as e:
            logging.info(f"Inside except block in scrap_one_courseInfo method, refer error message below: \n {e}")
            fetch_course = ""
        logging.info("returning course details to app.py file")
        return fetch_course
        
    def course_details(self,store_course_json):
        '''
            Fetches course details from course json
        '''
        logging.info("-------Inside course details method----------")
        fetch_course_info = dict() 
        fetch_course_info['_id'] = store_course_json['_id']
        fetch_course_info['categoryId'] = store_course_json['details']['categoryId']
        fetch_course_info['title'] = store_course_json['title']
        fetch_course_info['description'] = store_course_json['details']['description']
        try:
            fetch_course_info['img'] = store_course_json['details']['img']
        except Exception as e:
            logging.info(f"Inside first except block in course_details method, refer error message below: \n {e}")
            fetch_course_info['img'] = ""
            logging.info("Image not available for this course")
        fetch_course_info['mode'] = store_course_json['details']['mode']
        fetch_course_info['courseInOneNeuron'] = store_course_json['courseInOneNeuron']
        try:
            fetch_course_info['startDate'] = store_course_json['details']['classTimings']['startDate']
            fetch_course_info['doubtClearingTime'] = store_course_json['details']['classTimings']['doubtClearing']
            fetch_course_info['timings'] = store_course_json['details']['classTimings']['timings']
        except Exception as e:
            logging.info(f"Inside second except block in course_details method, refer error message below: \n {e}")
            fetch_course_info['startDate'] = ""
            fetch_course_info['doubtClearingTime'] = ""
            fetch_course_info['timings'] = ""  
        fetch_course_info['pricing'] = store_course_json['details']['pricing']
        fetch_course_info['instructors'] = list()
        for i in store_course_json['meta']['instructors']:
            course_instructor = dict()
            for j in self.store_instructors:
                if i == j['id']:
                    course_instructor['id'] = i
                    course_instructor['name'] = j['name']
                    course_instructor['description'] = j['description']
                    fetch_course_info['instructors'].append(course_instructor)
                    break
        fetch_course_info['curriculum'] = list()
        for i in store_course_json['meta']['curriculum'].keys():
            course_curriculum_list = dict()
            course_curriculum_list['title'] = store_course_json['meta']['curriculum'][i]['title']
            course_curriculum_list['items'] = list()
            for j in store_course_json['meta']['curriculum'][i]['items']:
                course_curriculum_list['items'].append(j['title'])
            fetch_course_info['curriculum'].append(course_curriculum_list)
        fetch_course_info['learn'] = store_course_json['meta']['overview']['learn']
        fetch_course_info['requirements'] = store_course_json['meta']['overview']['requirements']
        fetch_course_info['features'] = store_course_json['meta']['overview']['features']
        fetch_course_info['language'] = store_course_json['meta']['overview']['language']
        logging.info("course Info retreived")
        return fetch_course_info
import json
import requests
import argparse
import smtplib
import os

from datetime import date, timedelta
from email.message import EmailMessage

URL = "https://cowin.gov.in/api"

def send_request(url):
    response = requests.get(url,timeout=10,headers={"accept": "application/json"})
    result = response.json()
    return result

def create_state_dict(states_dict):
    """
    Create a dictionary with keys as names and values as id
    """
    new_dict = {}
    if 'states' not in states_dict.keys():
        return "Not a vaild dict"
    for item in states_dict['states']:
        new_dict.update({item['state_name']:item['state_id']})
    return new_dict

def get_district(state_id):
    """
    Get the mapping of district name to district id
    """
    url = URL+"/v2/admin/location/districts/"+str(state_id)
    return send_request(url)

def get_states():
    """
    Get the mapping of state name to state id
    """
    url = URL+"/v2/admin/location/states"
    return send_request(url)

def parse_info(res_dict):
    """
    Parses the appropriate info from response
    """
    email_content=''
    for center in res_dict['centers']:
        for session in center['sessions']:
            if session['min_age_limit'] == 18 and int(session['available_capacity']) > 1:
                email_content += "date={5}\tcenter_name=>{0}\tcenter_pincode=>{1}\tvaccine=>{2}\tavailabe=>{3}\tdistrict_name=>{4}".format(center['name'],
                                    center['pincode'],session['vaccine'],session['available_capacity'],center['district_name'],session['date'])
                if ('vaccine_fees' in center and center['vaccine_fees']):
                    for vaccine in center['vaccine_fees']:
                        email_content=email_content+"\tvaccine_name=>{0}\tfee=>{1}\t".format(vaccine['vaccine'],vaccine['fee'])
                email_content+="\n"
    email_content=email_content.strip()
    if(email_content):
        return email_content
    return None


def get_centers(district_id=None,pincode=None,check_date=None):
    """
    Get the availabily in the given district id or pincode for given date
    """
    if not check_date:
        check_date = date.today().strftime("%d-%m-%Y")

    if pincode:
        url = URL+"/v2/appointment/sessions/public/calendarByPin?pincode={0}&date={1}".format(pincode,check_date)
    else:
        url = URL+"/v2/appointment/sessions/public/calendarByDistrict?district_id={0}&date={1}".format(district_id,check_date)
    
    response = send_request(url)
    useful_content = parse_info(response)

    return useful_content

def alert(user_name,email_content,user_email,user_slack):
    """
    Send mail and slack notification
    """
    #prep for slack
    slack_webhook = os.environ['slack_webhook']
    slack_msg = "Hi <@{0}> :wave:,\n{1}\nLogin to <https://www.cowin.gov.in/home|cowin> to book the slots :pray:".format(user_slack,email_content)
    
    #prep for mail
    mail_msg = "Hi {0},\n{1}\nLogin to https://www.cowin.gov.in/home to book the slots\n\nThanks and Regards,\nAvinash Kumar Lodhi\n".format(user_name,email_content)
    
    #Send slack
    slack_alert = requests.post(slack_webhook,json={"text":slack_msg})
    if slack_alert.status_code != 200:
        with open('running_check.txt','a') as fw:
            fw.write("Error posting at slack,time={0},content={1}\n".format(datetime.now(),email_content))
    
    #Send mail
    gmail_pass=os.environ['gmail_pass']
    msg = EmailMessage()
    msg.set_content(mail_msg)
    msg['Subject'] = "Slot availability at cowin"
    msg['From'] = 'avinash.j.p.lodhi@gmail.com'
    msg['To'] = user_email

    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    s.login("avinash.j.p.lodhi@gmail.com", gmail_pass)
    s.send_message(msg)
    s.quit()

def main():
    """
    Main method 
    """

    today = date.today()
    with open('user_info.json') as input_file:
        monitor_list = json.load(input_file)
    date_list=[]
    result_dict={}

    for i in range(4):
        date_list.append(today+timedelta(7*i))
    
    for dt in date_list:
        date_dict={}
        check_date = dt.strftime("%d-%m-%Y")
        for item in monitor_list:
            for pn in item['pincode']:
                if pn not in date_dict:
                    date_dict[pn]=get_centers(pincode=pn,check_date=check_date)
            for dst in item['district']:
                if dst not in date_dict:
                    date_dict[dst]=get_centers(district_id=dst,check_date=check_date)
        
        for key in date_dict.keys():
            if date_dict[key]:
                result_dict[key] = result_dict[key]+"\n"+date_dict[key].strip() if key in result_dict else date_dict[key].strip()
    
    for item in monitor_list:
        content = ''
        flag = False
        alert_keys = ['pincode','district']
        for dk in alert_keys:
            for kx in item[dk]:
                if kx in result_dict and result_dict[kx].strip():
                    flag=True
                    content+="\nAvailability at {3} {0}\n{1}\n{2}\n".format(kx,'='*32,result_dict[kx],dk)
        if flag:
            alert(item['name'],content,item['email'],item['slack']) if flag else print("Nothing to alert")

if __name__ == '__main__':
    main()
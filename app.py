from flask import Flask, jsonify, request, render_template, redirect, url_for
import os
# from module.question import Question
import requests
from bs4 import BeautifulSoup
import random
import json
import datetime
from pytz import timezone

app = Flask(__name__,  static_url_path='/static')

LAST_COUNT = 0

@app.route("/")
def main():
    return render_template("main.html")

@app.route("/total", methods=['POST'])
def get_total_fine():
    return jsonify({'total_fine':total_fine*1000})


@app.route("/users", methods=['POST'])
def get_user_list():
    # 저번주 토요일 구하는 함수
    last_saturday =  get_last_saturday(LAST_COUNT)

    # 저저번주 토요일 구하는 함수
    last_last_saturday =  get_last_saturday(LAST_COUNT + 1)

    users = read_user_list()
    global total_fine

    # 전체 벌금
    total_fine = 0

    # 각 유저별금 계산
    for user in users:
        url = "https://github.com/" + user["id"]
        res = requests.get(url)
        soup = BeautifulSoup(res.text, 'html.parser')

        # 각 유저의 profile url 가져오기
        user["profile"] = soup.find(class_="avatar-user")["src"]

        # commit 계산 시작 날짜 구하기
        start_date = datetime.datetime.strptime(user['start_date'].strip(), '%Y-%m-%d')

        # 초기화
        commit = int(0)
        consecutive = int(0)
        new_fine = int(0)
        fine = int(0)
        total_day = int(0)
        date_commit = int(0)
        total_days = list()

        # 각 유저의 잔디밭에 있는 데이터 가져오기
        for rect in soup.select('.ContributionCalendar-day'):
            # data-date를 못가져오면 cotninue
            if not rect.get('data-date'):
                continue
        
            data_date = datetime.datetime.strptime(rect.get('data-date'), '%Y-%m-%d')
            if last_saturday < data_date:
                continue

            # 시작 날짜가 오늘 날짜보다 전이면 continue
            if start_date <= data_date: 
                total_day = total_day + 1

                # 커밋을 하지 않았다면!
                if(rect.get('data-level') == "0"):
                    if last_last_saturday < data_date and last_saturday >= data_date:
                        # 그주의 벌금 추가
                        new_fine = new_fine + 1
                    # 연속 커밋 초기화
                    consecutive = 0
                    # 벌금 올리기
                    fine = fine + 1
                else:
                    total_days.append(data_date.strftime('%Y-%m-%d'))
                    # span으로 나누어서 몇개의 commit을 했는지 계산
                    # date_commit = int(rect.find('span').text.split(' ')[0])
                    tool_tip = rect.get('id')
                    tooltip_element = soup.find('tool-tip', attrs={'for': f'{tool_tip}'})
                    date_commit = 0
            
                    if tooltip_element:
                        tooltip_text = tooltip_element.text.split('contribution')[0].strip()
                        date_commit = int(tooltip_text)

                        if date_commit > 0:
                            consecutive = consecutive + 1
                    
                commit = commit + date_commit
                date_commit = 0
                
        # 벌금 계산
        total_fine = total_fine + fine
 
        user["commit"] = commit
        user["consecutive_date"] = consecutive
        user["fine"] = fine
        user["new_fine"] = new_fine
        user["commit_dates"] = total_days

        #print(user)

        #state = commit / total_day * 100
        state = commit / total_day * 100
        if state <= 60:
            user["state"] = "danger"
            user["state_text"] = "F"
        elif state <= 70:
            user["state"] = "warning"
            user["state_text"] = "D"
        elif state <= 80:
            user["state"] = "warning"
            user["state_text"] = "C"
        elif state <= 90:
            user["state"] = "warning"
            user["state_text"] = "B"
        else:
            user["state"] = "success"
            user["state_text"] = "A"
    
    users.sort(key=lambda user: user["consecutive_date"], reverse=True)

    return render_template("user.html", result=users)


# count = 0 > last, 1 > last-last, 2 > last-last-last
def get_last_saturday(count):
    today = datetime.datetime.strptime(datetime.datetime.now(timezone('Asia/Seoul')).strftime('%Y-%m-%d'), ('%Y-%m-%d'))
    idx = (today.weekday() + 1) % 7
    sat = today - datetime.timedelta(7 + idx - 6 + count*7)

    return sat

def read_user_list():
    users = list()

    f = open("./user_list.txt", 'r')
    lines = f.readlines()
    for line in lines:
        splitted = line.split(' ')
        user = dict()
        user["id"] = splitted[0]
        user["name"] = splitted[1]
        user["start_date"] = splitted[2]

        users.append(user)

    f.close()

    return users

def get_test_data(users):

    user = dict()
    user["name"] = "백지원"
    user["start_date"] = "06/05/2021"
    user["commit"] = "25"
    user["consecutive_date"] = "8"
    user["fine"] = "1,000"
    user["new_fine"] = "1,000"
    # Success / warning / Danger
    user["state"] = "warning"
    
    users.append(user)


    user = dict()
    user["name"] = "백지원"
    user["start_date"] = "06/05/2021"
    user["commit"] = "25"
    user["consecutive_date"] = "8"
    user["fine"] = "1,000"
    # Success / warning / Danger
    user["state"] = "warning"
    
    users.append(user)

    return users


if __name__ == '__main__':
    app.debug = True
    app.run(host=os.getenv('IP', '0.0.0.0'), port=int(os.getenv('PORT', 4444)))


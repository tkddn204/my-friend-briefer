import re
import urllib.request
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from slackclient import SlackClient

from src import db
from src.texts import *
from src.util.get_config import config

sc = SlackClient(config['slack_token'])


class BaseHandler:
    # 메세지 보내는 코드를 간결화
    @staticmethod
    def post_message(channel, text):
        return sc.api_call("chat.postMessage", channel=channel, text=text)

    # 유저가 봇하고 대화중인지 체크
    @staticmethod
    def check_user_im(slack_event):
        event_type = slack_event['type']
        channel_type = slack_event['channel_type']

        return event_type == "message" and channel_type == 'im' and 'user' in slack_event


class WeatherHandler(BaseHandler):
    def __init__(self):
        # 오늘날씨 크롤링 함수
        self.areaDict = {"서울경기": ["수원"], "서해5도": [], "강원영서": [], "강원영동": [], "충청북도": [], "충청남도": ["대전"], "경상북도": [],
                         "경상남도": [],
                         "울릉독도": [], "전라북도": ["군산", "익산", '전주'], "전라남도": ["대구"], "제주": []}
        self.areaList = [v for values in self.areaDict.values() for v in values]

    # 지역설정 핸들러
    def set_area_handler(self, slack_event):
        if self.check_user_im(slack_event):
            channel = slack_event['channel']
            user_id = slack_event['user']
            text = slack_event['text'].replace('지역설정', '').strip()

            db.insert_user(user_id)
            for area in self.areaList:
                if area in text:
                    db.set_area(user_id, text)
                    self.post_message(channel, "{} 으로 지역 설정을 했습니다!".format(text))
                    return

            self.post_message(channel, "해당 지역이 없습니다.")

    # 오늘 날씨를 가져오는 메소드
    def get_weather_today(self, user_id):
        return self._crawl_weather_today(db.get_area(user_id))

    # 오늘 날씨를 크롤링하는 메소드
    def _crawl_weather_today(self, currentArea):
        url = "https://weather.naver.com/rgn/cityWetrMain.nhn"  # re.search(r'(https?://\S+)', text.split('|')[0]).group(0)

        sourcecode = urllib.request.urlopen(url).read()
        soup = BeautifulSoup(sourcecode, "html.parser")

        dataList = []
        areas = []
        currentBigArea = ""
        weather1 = []
        weather2 = []
        weather3 = []

        data = soup.find("table", class_="tbl_weather")

        # 현재 날짜를 크롤링 한다.
        date = soup.find("span", class_="lnb_date").get_text()
        dataList.append(date)

        # 소지역(대전) 에 대한 대지역(충청남도)을 추출한다.
        for args in self.areaDict.items():
            if currentArea in args[1]:
                currentBigArea = args[0]

        # 각 리스트에 크롤링한 데이터를 추가시킨다.
        for area in data.find_all("a", attrs={'href': True}):
            areas.append(area.get_text().strip())

        for nm1 in data.find_all("li", class_="nm"):
            weather1.append(nm1.get_text().strip())

        for nm2 in data.find_all("span", class_="temp"):
            weather2.append(nm2.get_text().strip())

        for nm3 in data.find_all("span", class_="rain"):
            weather3.append(nm3.get_text().strip())

        # 현재지역에 대한 데이터를 추출하기위해 그 지역에 대한 index를 추출한다.
        index = areas.index(currentBigArea)

        # 설정지역에 대해서 추출한 index값으로 필요 데이터를 뽑는다.  날씨 기온 강수량
        currentArea_Text = currentArea + "(" + areas[index] + ")"
        morningWether_Text = (
                "%5s %-8s %-5s %-5s" % ("오전날씨 :: ", weather1[index * 2], weather2[index * 2], weather3[index * 2]))
        afterWether_Text = ("%5s %-8s %-5s %-5s" % (
            "오후날씨 :: ", weather1[(index * 2 + 1)], weather2[(index * 2 + 1)], weather3[(index * 2 + 1)]))

        dataList.append(currentArea_Text)
        dataList.append(("%15s %-8s %-5s %-5s" % ("구분 :: ", "날씨", "기온", "강수량")))
        dataList.append(morningWether_Text)
        dataList.append(afterWether_Text)

        # 14.0'C 일때 14,0 이 리스트형식으로 저장
        # 현재 오후 기온
        temperature = int(re.findall('\d+', weather2[(index * 2 + 1)])[0])
        precipitation = int(re.findall('\d+', weather3[(index * 2 + 1)])[0])

        # bot comment
        if temperature >= 25:
            dataList.append(WEATHER_TEMPERATURES_25_UP)
        if temperature <= 5:
            dataList.append(WEATHER_TEMPERATURES_5_DOWN)
        if precipitation >= 60:
            dataList.append(WEATHER_PRECIPITATION_60PER_UP)
        if precipitation <= 40:
            dataList.append(WEATHER_PRECIPITATION_40PER_DOWN)
        if weather1[(index * 2 + 1)] == '눈':
            dataList.append(WEATHER_SNOW)
        if weather1[(index * 2 + 1)] == '흐림':
            dataList.append(WEATHER_CLOUDY)
        if weather1[(index * 2 + 1)] == '구름많음':
            dataList.append(WEATHER_CLOUD)

        return u'\n'.join(dataList)

    # 날씨 메세지를 보여주는 핸들러
    def weather_message_handler(self, slack_event):
        event_type = slack_event['type']
        channel_type = slack_event["channel_type"]
        if event_type == "message" and channel_type == 'im' and 'user' in slack_event:
            channel = slack_event["channel"]

            weather_today = self.get_weather_today(slack_event["user"])
            self.post_message(channel, weather_today)


class NewsHandler(BaseHandler):
    # 카테고리별 뉴스 조회수 랭킹
    def news_ranking_section(self, section):
        # print(section)
        sectionId = 0
        if '정치' in section:
            sectionId = 100
        elif '경제' in section:
            sectionId = 101
        elif '사회' in section:
            sectionId = 102
        elif section == '생활' or section == '문화':
            section = "생활/문화"
            sectionId = 103
        elif '세계' in section:
            sectionId = 104
        elif section.lower() == 'it' or section == '과학':
            section = "IT/과학"
            sectionId = 105
        keywords = []
        if sectionId != 0:
            url = "https://news.naver.com/main/ranking/popularDay.nhn?rankingType=popular_day&sectionId=" + str(
                sectionId) + "&date=20181220"
            sourcecode = urllib.request.urlopen(url).read()
            soup = BeautifulSoup(sourcecode, "html.parser")
            table = soup.find("ol", class_="ranking_list")
            keywords.append(section + ', 가장 많이 본 뉴스입니다.' + "\t :)")
            keywords.append("=" * 50)
            for index in range(1, 16):
                href = \
                    table.find("li", class_="ranking_item is_num" + str(index)).find("div",
                                                                                     class_="ranking_headline").find(
                        "a")["href"]
                keywords.append(str(index) + ". " + "<https://news.naver.com" + href + "|" + table.find("li",
                                                                                                        class_="ranking_item is_num" + str(
                                                                                                            index)).find(
                    "div", class_="ranking_headline").get_text().strip() + ">")
            keywords.append("=" * 50)
        else:
            keywords.append("입력을 확인해 주세요 :)")
        return u'\n'.join(keywords)

    # 이시각 뉴스 크롤링
    @staticmethod
    def news_keywords():
        url = "https://news.naver.com/"
        sourcecode = urllib.request.urlopen(url).read()
        soup = BeautifulSoup(sourcecode, "html.parser")
        keywords = []
        data = soup.find("div", class_="main_component droppable")
        title = data.find("h4", class_="tit_h4 tit_main1").get_text().strip()
        date = data.find("span", class_="small").find("em").get_text().strip()
        keywords.append(title + '\t' + date + "\t :)")
        keywords.append("=" * 50)
        for area in data.find_all("div", class_="newsnow"):
            # keywords.append("<" + href +"|" +area.find("p", class_="newsnow_img_mask_p").get_text().strip() +">")
            for li in area.find_all("a", class_="nclicks(hom.headcont)"):
                link = li["href"]
                keywords.append("<" + link + "|" + li.get_text().strip() + ">")
            keywords.append("=" * 50)
        return u'\n'.join(keywords)

    def news_message_handler(self, slack_event):
        event_type = slack_event['type']
        channel_type = slack_event["channel_type"]
        if event_type == "message" and channel_type == 'im' and 'user' in slack_event:
            channel = slack_event["channel"]
            from pprint import pprint
            pprint(slack_event)
            if '뉴스' in slack_event['text']:
                message = self.news_keywords()
            else:
                message = self.news_ranking_section(slack_event["text"])
            self.post_message(channel, message)


class ScheduleHandler(BaseHandler):
    # 모든 스케쥴을 보여주는 핸들러
    def get_all_schedules_handler(self, slack_event):
        if self.check_user_im(slack_event):
            channel = slack_event['channel']
            user_id = slack_event['user']
            all_schedules = db.get_all_schedules(user_id)
            if all_schedules:
                schedule_string = ''
                for date, schedule in all_schedules.items():
                    schedule_string += "--- {} ---\n".format(date)
                    schedule_string += '\n'.join(schedule)
                    schedule_string += '\n'

                self.post_message(channel, schedule_string)
            else:
                self.post_message(channel, NOTHING_SCHEDULES_TEXT)

    # 일정 추가 핸들러
    def create_schedule_handler(self, slack_event, command):
        if self.check_user_im(slack_event):
            channel = slack_event['channel']
            user_id = slack_event['user']
            text = slack_event['text']

            try:
                if command == 'create':
                    db.set_user_state(user_id, state=30)
                    self.post_message(channel, "일정의 내용을 입력해주세요.")
                elif command == 'create_name':
                    text = text.replace('"', '').replace("'", '').strip()
                    db.set_user_state(user_id, state=31)
                    db.create_temp(user_id, text)
                    self.post_message(channel, CREATE_SCHEDULE_TIME_TEXT.format(text))
                elif command == 'create_time':
                    schedule = db.get_temp(user_id)

                    text = text.strip()
                    if text[0] != '1':
                        text = '0' + text
                    date = datetime.strptime(text, '%m월 %d일 %H시')
                    db.create_schedule(user_id, date.strftime('2018-%m-%d'), date.strftime('%H') + '시 ' + schedule)
                    db.set_user_state(user_id, 3)
                    self.post_message(channel, CREATE_SCHEDULE_SUCCESS_TEXT)
                    self.post_message(channel, SCHEDULE_TEXT)
            except Exception:
                self.post_message(channel, "잘못 입력하셨습니다. 다시 입력해주세요!")

    # 특정 날짜(오늘, 내일)의 스케쥴의 내용을 받아와서 출력해주는 핸들러
    def get_schedules_handler(self, slack_event, command):
        if self.check_user_im(slack_event):
            channel = slack_event['channel']
            user_id = slack_event['user']
            all_schedules = db.get_all_schedules(user_id)
            schedule = None
            if command == 'today':
                date = datetime.now().strftime('2018-%m-%d')
                if date in all_schedules:
                    schedule = all_schedules[date]
                else:
                    self.post_message(channel, NOTHING_SCHEDULES_TEXT)

            elif command == 'tomorrow':
                date = (datetime.now() + timedelta(days=1)).strftime('2018-%m-%d')
                if date in all_schedules:
                    schedule = all_schedules[date]
                else:
                    self.post_message(channel, NOTHING_SCHEDULES_TEXT)

            if schedule:
                schedule_string = "--- {} ---\n".format(date)
                schedule_string += '\n'.join(schedule)
                self.post_message(channel, schedule_string)
            else:
                self.post_message(channel, NOTHING_SCHEDULES_TEXT)

    # 일정 삭제
    def delete_schedule_handler(self, slack_event, command):
        if self.check_user_im(slack_event):
            channel = slack_event['channel']
            user_id = slack_event['user']
            text = slack_event['text']

            try:
                if command == 'delete':
                    db.set_user_state(user_id, 32)
                    self.post_message(channel, "삭제할 일정의 날짜를 입력해 주세요(예: 12월 20일)")
                elif command == 'delete_name':
                    if text[0] != '1':
                        text = '0' + text

                    db.create_temp(user_id, text)
                    date = datetime.strptime(text, '%m월 %d일').strftime('2018-%m-%d')
                    schedules = db.get_all_schedules(user_id)
                    if date in schedules:
                        certain_schedules = schedules[date]
                        schedule_list = []
                        for num, schedule in enumerate(certain_schedules):
                            schedule_list.append('{}번: {}'.format(num, schedule))

                        db.set_user_state(user_id, 33)
                        self.post_message(channel, '\n'.join(schedule_list))
                        self.post_message(channel, "\n삭제할 일정의 번호를 입력해 주세요(예: 1)")
                    else:
                        self.post_message(channel, "해당 날짜에 일정이 없습니다. 다른 날짜를 입력해주세요!(예: 12월 20일)")

                elif command == 'delete_final':
                    date = datetime.strptime(db.get_temp(user_id), '%m월 %d일').strftime('2018-%m-%d')
                    delete_soon_schedule = db.get_all_schedules(user_id)[date][int(text)]
                    db.delete_schedule(user_id, date, delete_soon_schedule)
                    db.set_user_state(user_id, 3)
                    self.post_message(channel, "삭제되었습니다!")
                else:
                    self.post_message(channel, SCHEDULE_TEXT)
            except Exception:
                self.post_message(channel, "잘못 입력하셨습니다. 다시 입력해주세요!")

    # 일정 핸들러 모음
    def pick_schedule_handler(self, slack_event, command='default'):
        if command == 'all':
            self.get_all_schedules_handler(slack_event)
        elif command in ['create', 'create_name', 'create_time']:
            self.create_schedule_handler(slack_event, command)
        elif command in ['delete', 'delete_name', 'delete_final']:
            self.delete_schedule_handler(slack_event, command)
        elif command in ['today', 'tomorrow']:
            self.get_schedules_handler(slack_event, command)
        else:
            self.default_schedule_handler(slack_event)

    # 일정 기본 멘트 핸들러
    def default_schedule_handler(self, slack_event):
        if self.check_user_im(slack_event):
            channel = slack_event["channel"]

            self.post_message(channel, SCHEDULE_TEXT)


class FirstHandler(BaseHandler):
    # 처음에 말했던 메세지만 답해주는 핸들러
    def first_message_handler(self, slack_event):
        if self.check_user_im(slack_event):
            channel = slack_event['channel']
            user_id = slack_event['user']

            db.insert_user(user_id)
            self.post_message(channel, START_TEXT)


class ChatBotHandler(BaseHandler):
    # 처음 화면에서 상태로 구분하는 핸들러
    def set_state_handler(self, slack_event, state=0):
        if self.check_user_im(slack_event):
            channel = slack_event["channel"]
            user_id = slack_event['user']

            db.set_user_state(user_id, state)
            if state == 0:
                self.post_message(channel, START_TEXT)
            else:
                db.set_user_state(user_id, state)
                # 날씨
                if state == 1:
                    self.post_message(channel, WEATHER_TEXT)
                # 뉴스
                elif state == 2:
                    self.post_message(channel, NEWS_MANUAL)
                # 일정
                elif state == 3:
                    self.post_message(channel, SCHEDULE_TEXT)

    # 아침 브리핑을 위한 핸들러
    def briefing_handler(self):
        users = db.get_all_user()
        for user in users:
            user_id = user['id']
            try:
                result = ''

                # 하루 날씨
                weather_today = WeatherHandler().get_weather_today(user_id)
                result += weather_today + '\n'

                # 뉴스
                keywords = NewsHandler().news_keywords()
                result += keywords + '\n'

                # 일정
                all_schedules = db.get_all_schedules(user_id)
                schedule = []
                date = datetime.now().strftime('2018-%m-%d')
                if date in all_schedules:
                    schedule = all_schedules[date]

                if schedule:
                    schedule_string = "--- 오늘의 일정 ---\n"
                    schedule_string += '\n'.join(schedule)
                    result += schedule_string
                else:
                    result += NOTHING_SCHEDULES_TEXT

                self.post_message(user_id, result)
            except Exception:
                print("fail!")

    def state_handler(self, slack_event):
        # db에 슬랙의 유저 아이디가 저장되었는지 확인합니다.
        user_id = slack_event['user']
        if db.get_user(user_id):
            # db에 슬랙의 유저 아이디가 있을 경우
            # 상태에 따라 다른 함수를 실행합니다.
            state = db.get_user_state(user_id)
            # 처음 상태일 경우
            if state == 0:
                check_list = ['날씨', '뉴스', '일정']
                for i, check in enumerate(check_list):
                    if check in slack_event['text']:
                        return self.set_state_handler(slack_event, i + 1)
                return FirstHandler().first_message_handler(slack_event)

            # 돌아가기를 말했을 경우
            elif slack_event['text'] == '돌아가기':
                return self.set_state_handler(slack_event)

            # 날씨를 말한 상태일 경우
            elif state == 1:
                weather_handler = WeatherHandler()
                if '지역설정' in slack_event['text']:
                    return weather_handler.set_area_handler(slack_event)
                elif "오늘날씨" or "날씨" in slack_event['text']:
                    return weather_handler.weather_message_handler(slack_event)

            # 뉴스를 말한 상태일 경우
            elif state == 2:
                if '뉴스' or '정치' or '사회' or '경제' or '생활' or '문화' or '세계' or 'IT' or 'it' or '과학' in \
                        slack_event['text']:
                    return NewsHandler().news_message_handler(slack_event)

            # 일정을 말한 상태일 경우
            elif state == 3 or 30 <= state <= 33:
                schedule_handler = ScheduleHandler()
                if state == 3:
                    command = ''
                    if '모든' in slack_event['text']:
                        command = 'all'
                    elif '추가' in slack_event['text']:
                        command = 'create'
                    elif '삭제' in slack_event['text']:
                        command = 'delete'
                    elif '오늘' in slack_event['text']:
                        command = 'today'
                    elif '내일' in slack_event['text']:
                        command = 'tomorrow'

                    return schedule_handler.pick_schedule_handler(slack_event, command)

                # 일정 이름을 정하고 있는 상태일 경우
                elif state == 30:
                    return schedule_handler.pick_schedule_handler(slack_event, 'create_name')
                # 일정 시간을 정하고 있는 상태일 경우
                elif state == 31:
                    return schedule_handler.pick_schedule_handler(slack_event, 'create_time')

                # 삭제할 일정의 시간을 적어야 하는 상태일 경우
                elif state == 32:
                    return schedule_handler.pick_schedule_handler(slack_event, 'delete_name')
                elif state == 33:
                    return schedule_handler.pick_schedule_handler(slack_event, 'delete_final')
        else:
            # db에 슬랙의 유저 아이디가 없을 경우
            return FirstHandler().first_message_handler(slack_event)

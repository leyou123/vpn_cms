import datetime
import time

from dateutil.relativedelta import relativedelta


def calculation_months(month):
    """
    获取指定月份日期
    :param month:
    :return:
    """
    return datetime.date.today() + relativedelta(months=+month)


def calculation_date(days):
    """
    获取指定月份日期
    :param days:
    :return:
    """
    return datetime.date.today() + relativedelta(days=+days)


def calculation_hours(hours):
    """
    获取指定月份日期
    :param hours:
    :return:
    """
    return datetime.date.today() + relativedelta(days=+hours)


def cal_time(date1, data=datetime.date.today()):
    """
    计算日期相差天数
    :param date1:
    :param data:
    :return:
    """

    return (date1 - data).days


def get_today():
    today = datetime.date.today()
    str_day = today.strftime("%Y-%m-%d").split("-")
    return str_day



def get_yesterday():
    today = datetime.date.today()
    oneday = datetime.timedelta(days=1)
    yesterday = today - oneday
    str_day = yesterday.strftime("%Y-%m-%d").split("-")
    return str_day


def get_two_day():
    today = datetime.date.today()
    oneday = datetime.timedelta(days=2)
    yesterday = today - oneday
    str_day = yesterday.strftime("%Y-%m-%d").split("-")
    return str_day


def get_seven_day():
    today = datetime.date.today()
    seven_day = datetime.timedelta(days=7)
    seven = today - seven_day
    return seven


def date_time_yesterday():
    today = datetime.date.today()
    oneday = datetime.timedelta(days=1)
    yesterday = today - oneday
    # convstr = str(yesterday)+" "+"00:00:00"
    this_date = datetime.datetime.strptime(str(yesterday), '%Y-%m-%d')
    this_date = int(time.mktime(this_date.timetuple()))

    return this_date


if __name__ == '__main__':
    print(get_yesterday())
    # res = date_time_yesterday()
    #
    # print(res,type(res))
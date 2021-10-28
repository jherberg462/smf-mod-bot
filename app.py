import requests
from bs4 import BeautifulSoup
from splinter import Browser
from selenium.webdriver.common.keys import Keys
from datetime import datetime, timedelta, timezone
import time
import os

from scrape_utils import process_new_posts, get_thread_id, get_post_id, get_last_post_time
from scrape_utils import get_poster_info_recent, get_post_info_recent, get_OP_lastposter

from threads_classes import Thread, All_threads

from report_utils import check_rule_violations, get_thread_page_info
from report_utils import report_post, check_double_post

# from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

executable_path = {'executable_path': ChromeDriverManager().install()}
browser = Browser('chrome', **executable_path, headless=True)

def login(username, password, browser_, captcha_bypass, domain='https://bitcointalk.org'):
    '''
    logs into forum account
    
    inputs:
        username: str, forum username used to report posts
        password, str, forum password for account used to report posts
        browser_: Splinter browser object
        captcha_bypass, str, code used to bypass captcha to login
        domain: str, domain the forum is housed on
    '''
    url = domain + '/index.php?action=login;ccode={}'.format(captcha_bypass)
    browser_.visit(url)
    browser_.fill('user', username)
    browser_.fill('passwrd', password)
    browser_.check('cookieneverexp') #stay logged in
    active_web_element = browser_.driver.switch_to_active_element()
    active_web_element.send_keys(Keys.ENTER)
    

#
login(os.environ['mod_user'], 
      os.environ['mod_password'], 
      browser,
      os.environ['captcha'])
threads = All_threads([178336,5117330, 5216108])

highest_postID = 0
time_since_violation_found = 0
while True:
    try:
        highest_postID = process_new_posts(threads, highest_postID)
#         time.sleep(1)
        if len(threads.get_rule_violations()) > 0:
            time_since_violation_found +=1
            if time_since_violation_found > 60:
                violations = threads.get_rule_violations()
                check_rule_violations(violations, browser)
                threads.reset_thread_violations()
                threads.reset_violations()
                time_since_violation_found = 0
    except IndexError:
        try:
            browser.quit()
            browser = Browser('chrome', **executable_path, headless=True)
            login(os.environ['mod_user'], 
                  os.environ['mod_password'], 
                  browser,
                  os.environ['captcha'])
            threads.reset_thread_violations()
            threads.reset_violations()
            highest_postID = process_new_posts(threads, highest_postID)
        except:
            raise ValueError
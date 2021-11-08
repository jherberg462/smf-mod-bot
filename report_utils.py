import time
from datetime import datetime, timedelta, timezone
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from splinter import Browser


def check_rule_violations(threads, browser_, domain='https://bitcointalk.org'):
    '''
    checks potential rule violations and acts accordingly
    
    inputs: 
        threads, dict
            keys of dict are threadIDs, and the value is another dict
            key of this dict is a str of the potential violation type
            and the value of these keys is a dict with information
            necessary to evaluate if a rule was violated
        browser_: Splinter browser object used to access thread
    '''
    thread_list = list(threads.keys())
    for thread in thread_list:
        potential_violations = list(threads[thread].keys())
        for violation in potential_violations:
            exists, postIDs, post_info = get_thread_page_info(thread,
                                                             threads[thread][violation]['post_id'],
                                                             browser_)
            if exists == False:
                continue
            if len(violation.split('excessive_bump')) == 2:
                report_post(thread,
                           violation,
                           threads[thread][violation],
                            browser_,
                            domain)
            elif len(violation.split('double_post')) == 2:
                remove_post = check_double_post(thread,
                                                threads[thread][violation]['post_id'],
                                                postIDs,
                                                post_info,
                                                browser_,
                                                domain)
                if remove_post:
                    report_post(thread,
                               violation,
                               threads[thread][violation],
                               browser_,
                               domain)
#                 else:
#                     raise (ValueError)
               
                    
def get_thread_page_info(thread, 
                         postID,
                         browser_,
                         domain='https://bitcointalk.org',
                         page_offset=None):
    '''
    checks if post still exists, and returns information about the page
    of the post
    inputs:
        thread: int, threadID post should exist in
        post: int, postID of the post
        browser_: Splinter browser object used to access thread
        domain: str, domain of forum
        page_offset: int, the reply number the thread page being viewed 
        should contain
        
    returns: 
        post_exists: bool, True if post still exists, False otherwise
        postIDs: list of ints, postID of each post in the thread page
        post_info: dict of dicts: the keys are the first dict are the postIDs
        in the thread page, the keys and their values of the child dicts are:
            'uid':int UID of person making the post
            'post_time': date_time object, date and time the post was made
            'reply_number': int, the i-th post number in the thread
    '''
    post_url = '/index.php?topic={}.msg{}#msg{}'.format(thread, postID, postID)
    if page_offset:
        post_url = '/index.php?topic={}.{}'.format(thread, page_offset)
    url = domain + post_url
    browser_.visit(url)
    still_loading = True
    while still_loading == True:
        soup = BeautifulSoup(browser_.html, 'html.parser')
        if len(soup.find_all('td', 
                             class_='maintab_back')[-1].find_all('a')) > 1:
            still_loading = False
        time.sleep(1)
    mark_unread = soup.find_all('td', class_='maintab_back')[-1]
    mark_unread = mark_unread.find_all('a')[3]
    mark_unread = str(mark_unread).split('href="')[1].split('">Mark')[0]
    post_exists = False
    postIDs = []
    post_info = {}
    for div_class in ['windowbg', 'windowbg2']:
        posts = soup.find_all('td', class_=div_class)
        for x in range(len(posts)):
            try:
                post_url = posts[x].find_all('div', class_='subject')[0]
                post_url = str(post_url).split('href="')[1].split('">')[0]
                foundPostID = post_url.split('.msg')[1].split('#msg')[0]
                if len(foundPostID) < 10:
                    postIDs.append(int(foundPostID))
                if int(foundPostID) == postID:
                    post_exists = True
                uid = posts[x].find_all('td', class_='poster_info')[0].find_all('a')[0]
                uid = str(uid).split('u=')[1].split('"')[0]
                uid = int(uid)
                reply_num = posts[x].find_all('a', class_='message_number')[0]
                reply_num = str(reply_num).split('>#')[1].split('</')[0]
                reply_num = int(reply_num)
                post_time = posts[x].find_all('div', class_='smalltext')[1]
                if len (post_time.find_all('span', class_='edited')) >=1:
                    post_time = post_time.find_all('span', class_='edited')[0]
                else:
                    post_time = posts[x].find_all('div', class_='smalltext')[1]
                post_time = str(post_time)
                fmt = '%B %d, %Y, %I:%M:%S %p'
                if len(post_time.split('Today')) == 1:
                    if len(post_time.split(':')) == 1:
                        post_time = 'January 1, 2000, 12:00:00 AM'
                    post_time = post_time.split('</')[0].split('">')[1]
                    post_time = datetime.strptime(post_time, fmt)
                else:
                    post_time = post_time.split('">')[1]
                    tme = post_time.split('at ')[1]
                    hour = int(tme.split(':')[0])
                    minute = int(tme.split(':')[1])
                    second = tme.split(':')[2]
                    AMPM = second.split(' ')[1]
                    second = int(second.split(' ')[0])
                    utc_today = datetime.now(timezone.utc)
                    if len(AMPM.split("P")) == 2:
                        hour += 12
                    if hour % 12 == 0:
                        hour -= 12
                    post_time = datetime(utc_today.year,
                                         utc_today.month,
                                         utc_today.day,
                                         hour,
                                         minute,
                                         second)
                post_info[int(foundPostID)] = {
                    'uid':uid,
                    'post_time':post_time,
                    'reply_number':reply_num
                }
            except IndexError as e:
                pass
    postIDs = sorted(postIDs)
    time.sleep(.5)
    browser_.visit(mark_unread)
    return post_exists, postIDs, post_info

def report_post(thread, 
                violation_type,
                violation,
                browser_, 
                domain):
    '''
    reports a post as being against the rules
    
    inputs:
        thread: int, thread the offending post in located in
        violation_type: str, the rule that was broken
        violation: dict, with the following keys:
            post_id: int, postID
            the dict will also have additional key/values
            that document additional information about why
            the post breaks the subject rule
        browser_: Splinter browser object used to access thread
        str, domain the forum is housed on
        
        Returns: None
    '''
    if len(violation_type.split('double_post')) == 2:
        post_id = violation['previous_post_id']
    else:
        post_id = violation['post_id']
    url = '{}/index.php?action=reporttm;topic={};msg={}'.format(domain,
                                                               thread,
                                                               post_id)
    browser_.visit(url)
    time.sleep(1)
    report_text = 'This is an automated message.'
    report_text += ' There is reason to believe this post broke the {} rule'.format(violation_type)
    report_text += ' based on the following:'
    for key_ in violation.keys():
        report_text += ' {}:{}'.format(key_, violation[key_])
#     time.sleep(1)
    browser_.fill('comment', report_text)
    active_element = browser_.driver.switch_to_active_element()
    active_element.send_keys(Keys.ENTER)
    return None

def check_double_post(thread, postID, postIDs, post_info, browser_, domain):
    '''
    checks if a post's author is the same as the previous posts author
    in the thread the post is in
    
    inputs:
        thread: int, threadID the post was written in
        postID: int, post ID of the subject post
        postIDs: list of ints, postID of each post in the thread page
        post_info: dict of dicts: the keys are the first dict are the postIDs
        in the thread page, the keys and their values of the child dicts are:
            'uid':int UID of person making the post
            'post_time': date_time object, date and time the post was made
            'reply_number': int, the i-th post number in the thread
        browser_: Splinter browser object used to access thread
        domain: str, domain of forum
    
    
    returns: bool, if the author of the post is the same as the previous 
    post, function will return True, otherwise it will return False
    '''
    postIDX = post_info[postID]['reply_number']
    if postIDX < 2:
        return False
    postIDX = postIDX % 20
    postIDX -=1
    if postIDX == 0:
        _, prev_postIDs, pre_post_info = get_thread_page_info(thread,
                                                             1,
                                                             browser_,
                                                             domain,
                                                             post_info[postID]['reply_number'] - 1,)
        if pre_post_info[prev_postIDs[-1]]['uid'] == post_info[postID]['uid']:
            return True
        else:
            return False
    
    if post_info[postID]['uid'] == post_info[postIDs[postIDX - 1]]['uid']:
        if post_info[postID]['reply_number'] == 2:
            return False
        elif post_info[postID]['reply_number'] < 10:
            double_post = False
            for postIDX_ in range(post_info[postID]['reply_number'] - 1):
                if post_info[postIDs[postIDX_]]['uid'] != post_info[postID]['uid']:
                    double_post = True
            return double_post
        else:
            return True
    else:
        return False
    
        
    
    
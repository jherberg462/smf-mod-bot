import requests
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup
from threads_classes import Thread, All_threads
import time


def process_new_posts(AllThreads, 
                      highest_postID, 
                      domain='https://bitcointalk.org'):
    '''
    inputs:
        AllThreads: instance of a All_threads class
        highest_postID: int, highest postID previously viewed
        domain: str, domain the forum is housed on
    '''
    low_postID=float('inf')
    offset = 90
    new_highest_postID = 0
    for _ in range(10):
        #add below to loop
        url = domain + '/index.php?action=recent;start={}'.format(offset)
        content = requests.get(url).content
        soup_content = BeautifulSoup(content, 'html.parser')
        page_posts = soup_content.find_all('table', class_='bordercolor')
        for idx in range(1, 11):
            post = page_posts[-idx]
            #information needed:
            #thread_id, last_post_time, OP, last_poster, post_id
            thread_info = get_post_info_recent(post)
            poster_info = get_poster_info_recent(post)
            thread_id = get_thread_id(thread_info)
            last_post_time = get_last_post_time(thread_info)
            OP = get_OP_lastposter(poster_info, OP=True)
            last_poster = get_OP_lastposter(poster_info, OP=False)
            post_id = get_post_id(thread_info)
            if idx == 11:
                low_post = post_id
            high_post = post_id
            if post_id > new_highest_postID:
                new_highest_postID = post_id
#             if post_id <= highest_postID:
#                 break
#             if post_id >= low_postID:
#                 continue
            #update thread
            AllThreads.process_post(thread_id, last_post_time, OP, last_poster, post_id)
#         if post_id <= highest_postID:
#             break
        offset -= 10
        time.sleep(1)
    return new_highest_postID
    
        
        
def get_thread_id(post):
    '''
    returns the thread ID 
    
    input: post: BeautifulSoup object, intended to be the output
    from the get_post_info_recent function
    '''
    return int(str(post.find_all('a')[-1]).split('topic=')[1].split('.')[0])


def get_post_id(post):
    '''
    returns the post ID
    
    input: post: BeautifulSoup object, intended to be the output
    from the get_post_info_recent function
    '''
    return int(str(post.find_all('a')[-1]).split('.msg')[1].split('#msg')[0])

def get_last_post_time(post,):  
    '''
    returns time of last post as as datetime object
    
    input: 
        post: BeautifulSoup object, intended to be the output
        from the get_post_info_recent function        
    '''
    if len(str(post.find_all("div",)[-1]).split("Today")) == 2:
        utc_today = datetime.now(timezone.utc)
        post_time = str(post.find_all('div',)[-1]).split('Today')[1].split("at ")[1].split(" ")[0]
        post_hour = int(post_time.split(':')[0])
        post_minute = int(post_time.split(":")[1])
        post_second = int(post_time.split(':')[2])
        if len(str(post.find_all('div',)[-1]).split("PM")) == 2:
            post_hour += 12
        if post_hour % 12 == 0:
            post_hour -= 12

        post_time_dt = datetime(utc_today.year, 
                                utc_today.month, 
                                utc_today.day, 
                                post_hour, 
                                post_minute, 
                                post_second)
        return post_time_dt
    dt_format = '%B %d, %Y, %I:%M:%S %p'
    post_time = str(post.find_all('div',)[-1]
                   ).split('on: ')[1].split('\xa0')[0]
    post_time_dt = datetime.strptime(post_time, dt_format)
    return post_time_dt

def get_poster_info_recent(post):
    '''
    returns information necessary to determine the OP and 
    last poster of a post obtained via /index.php?action=recent
    '''
    return post.find_all('span', class_='middletext')[0]

def get_post_info_recent(post):
    '''
    returns information necessary to determine the
    thread_id, last post time and post_id of a post
    obtained via /index.php?action=recent
    '''
    return post.find_all('tr', class_='titlebg2')[0]
    
def get_OP_lastposter(post, OP=False):
    '''
    returns the UID of either the OP or last person to post
    in a thread
    
    inputs:
        post: BeautifulSoup object, intended to be the output
        from the get_poster_info_recent function
        
        OP: Bool, default False, if False, function will return
        the UID of the original poster in a thread, if True, 
        functill will return the UID of the last person to post
        in a thread
    '''
    if OP:
        op_ = 0
    else:
        op_ = 1
        
    uid = int(str(post.find_all('a')[op_]
                 ).split('u=')[1].split('">')[0])
    return uid


    
from datetime import datetime, timedelta, timezone
from splinter import Browser
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import time


class Thread:
    def __init__(self, thread_id, last_post_time, OP, lastPoster, post_id, browser=None):
        self.thread_id = thread_id
        self.last_post_time = last_post_time
        self.OP = OP
        self.last_poster = lastPoster
        self.last_bump = None
        self.double_post_count = 0
        self.rule_violations = dict()
        self.last_post_id = post_id
        self._browser = browser
        self.last_bump_archive = None
    
    def update_thread(self, last_post_time, lastPoster_, post_id, browser):
        self._browser = None #browser
        if post_id > self.last_post_id:
            if self.last_poster == self.OP and lastPoster_ == self.OP:
                current_bump_archive = 'na' #self.get_archive(post_id)
                if self.last_bump:
                    current_bump_archive = 'na'#self.get_archive(post_id)
                    #check if last bump is w/i 24 hours of last_post_time (give 1.5 hours leeway)
                    if (self.last_bump + timedelta(hours=22, minutes=30)) > last_post_time:
                        if (self.last_bump + timedelta(hours=1)) < last_post_time:
                            self.rule_violations['excessive_bump'] = {
                                'post_id':post_id,
                                'last_bump_post_id':self.last_post_id,
                                'last_bump':self.last_bump,
                                'current_bump':last_post_time,
                                'current_bump_archive':current_bump_archive,
                                'last_bump_archive':self.last_bump_archive
                            }
                self.last_bump_archive = current_bump_archive
                            
                self.last_bump = last_post_time
            elif self.last_poster == lastPoster_: #consider if I want to update this to if
                if self.last_post_time + timedelta(days=1) > last_post_time:
                    self.rule_violations['double_post_{}'.format(self.double_post_count)] = {
                        'post_id': post_id,
                        'previous_post_id': self.last_post_id,
                        'current_poster': lastPoster_,
                        'last_poster':self.last_poster
                    }
                    self.double_post_count += 1
            self.last_post_time = last_post_time
            self.last_poster = lastPoster_
            self.last_post_id = post_id
        return self.rule_violations
    
    def reset_rule_violations(self):
        self.double_post_count = 0
        self.rule_violations = dict()
    
    def get_rule_violations(self):
        return self.rule_violations
    
    def get_archive(self, post_id, domain='https://bitcointalk.org/'):
        url_to_archive = '{}index.php?topic={}.msg{}'.format(domain, self.thread_id, post_id)
        archive_url = 'http://archive.md'
        self._browser.visit(archive_url)
        time.sleep(0.5)
        self._browser.fill('url', url_to_archive)
        active_web_element = self._browser.driver.switch_to.active_element
        active_web_element.send_keys(Keys.ENTER)
        time.sleep(1)
        try:
            archive_code = self._browser.driver.current_url.split('/')[-1]
            archived_url = '{}/{}'.format(archive_url, archive_code)
        except IndexError:
            archived_url = 'unsuccessfully attepted to archive post'
        return archived_url




class All_threads:
    def __init__(self, threads_to_ignore=None, browser=None):
        self.threads = set()
        self.violations = dict()
        self.thread = dict()
        # self._browser = browser
        self.executable_path = {'executable_path': ChromeDriverManager().install()}
        self._browser = Browser('chrome', **self.executable_path, headless=True)
        for thread in threads_to_ignore:
            self.add_thread(thread, None, None, None, 99999999999)
            self.threads.add(thread)
    def add_thread(self, thread_id, last_post_time, OP, last_poster, post_id):
        self.thread[thread_id] = Thread(thread_id, last_post_time, OP, last_poster, post_id, self._browser)
    def update_thread(self, last_post_time, last_poster, post_id, thread_id):
        violation_ = self.thread[thread_id].update_thread(last_post_time, last_poster, post_id, self._browser)
        if len(violation_) > 0:
            return violation_
    def process_post(self, thread_id, last_post_time, OP, last_poster, post_id):
        try: 
            pass #self._browser.visit('about:blank')
        except:
            self.reset_browser()
        if thread_id in self.threads:
            violation_ = self.update_thread(last_post_time, last_poster, post_id, thread_id)
            if violation_:
                self.violations[thread_id] = violation_
        else:
            self.add_thread(thread_id, last_post_time, OP, last_poster, post_id)
            self.threads.add(thread_id)
    def reset_violations(self):
        self.violations = dict()
    def reset_thread_violations(self):
        for threadID in self.violations.keys():
            self.thread[threadID].reset_rule_violations()
    def get_rule_violations(self):
        return self.violations
    def reset_browser(self):
        self._browser.quit()
        self._browser = Browser('chrome', **self.executable_path, headless=True)
        
            
            
            
            
                    
                

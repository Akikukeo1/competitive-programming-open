import re


s = str(input())

s = re.sub("[^A-Z]", "", s)
print(s)

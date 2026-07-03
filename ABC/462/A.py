import re

text = input()

numeric_string = re.sub(r"\D", "", text)

print(numeric_string)

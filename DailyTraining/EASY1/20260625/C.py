import sys


n, m = map(int, input().split())
s, t = list(), list()

for i in range(n):
    s.append(input())

for i in range(m):
    t.append(input())

# sys.stderr.write(str(s) + "\n")
# sys.stderr.write(str(t) + "\n")

for i in range(n):
    s[i] = s[i][-3:]

for i in range(m):
    t[i] = t[i][-3:]

sys.stderr.write(str(s) + "\n")
sys.stderr.write(str(t) + "\n")

count = 0
for i in s:
    if i in t:
        count += 1

print(count)

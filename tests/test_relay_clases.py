
"""def make_adder(n):
    def add(x):
        return x + n
    return add

plus_3 = make_adder(3)
plus_5 = make_adder(5)

print(plus_3(8))"""


x = [1,2,3]
y = []

""""for z in x:
    if z > 1 and z < 3:
        y.append(z)"""



y = [z for z in x if 1 < z and z > 2]
print(y)
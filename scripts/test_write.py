import os
p = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'write_test.txt'))
print('path', p)
try:
    with open(p, 'w') as f:
        f.write('test')
    print('wrote')
except Exception as e:
    print('error', e)

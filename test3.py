# 딕셔너리 활용
di = {
    'name': 'yeji',
    20: 'test',
    True: [1,2]
} # 선언

print(di)

di['age'] = 20 # 추가
print(di)

di['age'] = 30 # 변경 (재할당 == 이미 있는 key 값)
print(di)

print(di['name']) # 하드코딩 (직접 key값 입력)
key = 'name'
print(key)
# 없는 key를 작성하면 KeyError 발생
# print(di['test'])  # KeyError: 'test'

# 키 값이 있는지 검사
print(di.get(key))  # 'yeji' (value 반환)
print(di.get('test'))  # None (없으면 None 반환)

# 리스트는 가변, 튜플은 불변
# 파이썬 내에서 딕셔너리의 key값을 해시로 변환(숫자)하는데,
# 가변은 해시로 변환이 어렵고 불변은 용이하기에 key값에는 불변값만 활용 가능

# 튜플의 존재 이유: 값이 변경되면 안되니까 존재(ex. 함수) / 속도도 훨씬 빠름

# 리스트 활용
num = []
num.append(3)
print(num)
num.append(2)
print(num)
num.append(1)
num.append(5)
print(num)

print(num[0])
print(num[0:2])
print(num[::2])
print(num[::-1])  # 역순

# 데이터 삭제 - pop: 순서(인덱스), remove: 값
num.pop() # 맨 뒤 데이터
num.remove(2)
print(num)

# -- 재할당 -- 
a = [1, 2, 3]
b = a # 참조 복사 (메모리 복사 == 메모리 주소 공유 == 같은 객체 가르킴)
b[0] = 10

print(f'a: {a}')  # a: [10, 2, 3]
print(f'b: {b}')  # b: [10, 2, 3]

# -- 복사 --
# 객체가 아니라 값만 복사
# 얕은 복사와 깊은 복사
# 얕은 복사: 객체의 주소만 복사
# 깊은 복사: 객체의 값까지 복사

print(id(a))
print(id(b)) # b: 주소가 같음
# 2489822777856
# 2489822777856


a = [[1, 2], [3, 4]]


# 깊은 복사
# a와 별개로 a의 값을 b값으로 복사
import copy
b = copy.deepcopy(a)  # 깊은 복사
b[0][0] = 10
print(f'a: {a}')  # a: [[1, 2], [3, 4]]
print(f'b: {b}')  # b: [[10, 2], [3, 4]]
# 메모리가 완전히 다른 곳에 새로운 객체를 저장하겠다
print(id(a))  # a: 주소
print(id(b))  # b: 주소가 다름
# 2489822856704
# 2489823040128

# 얕은 복사
# 표지만 복사한 개념
# 껍데기는 따로 쓰고, 속은 함께 쓰자
c = [1, [2, 3]]
d = c.copy() # 얕은 복사

print(id(c))  # c: 주소
print(id(d))  # d: 주소가 다름

print(f'c: {c}')  # c: [1, [2, 3]]
print(f'd: {d}')  # d: [1, [2, 3]]

d[0] = 10

print(f'c: {c}')  # c: [1, [2, 3]]
print(f'd: {d}')  # d: [10, [2, 3]]

print(id(c[1]))  # c: 주소
print(id(d[1]))  # d: 주소가 같음

d[1][0] = 20
print(f'c: {c}')  # c: [1, [20, 3]]
print(f'd: {d}')  # d: [10, [20, 3]]

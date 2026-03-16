import random

def question1():
    randomlist = [[random.randint(1, 100) for i in range(10)] for j in range(10)]
    print_random_list_with_line(randomlist)

def print_random_list(randomlist):
    for i in randomlist:
        print(i)

def print_random_list_with_line(randomlist):
    for i in randomlist:
        for j in i:
            print(j if j >9 else '0' + str(j), end='|')
        print(' ')  # Print a newline after each row
        print('-' * len(i) * 3)  # Print a separator line

def question2():
    randomlist = [[random.randint(1,10) for i in range(10)] for j in range(10)]
    print(randomlist)
    duplicates = find_duplicate(randomlist)
    print("Duplicate numbers:", duplicates)
    

def find_duplicate(randomlist):
    seen = []
    duplicates = []
    for liste in randomlist:
        for num in liste:
            if num in seen and num not in duplicates:
                duplicates.append(num)
            else:
                seen.append(num)
    return duplicates

if __name__ == "__main__":
    question1()
    print('-'*10)
    question2()

    
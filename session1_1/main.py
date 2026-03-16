import random
import os
import hashlib

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
    for lst in randomlist:
        for num in lst:
            if num in seen and num not in duplicates:
                duplicates.append(num)
            else:
                seen.append(num)
    return duplicates

def question4():
        directory = "session1_1/testq4"
        duplicates, hashes = find_duplicate_files(directory)
        print("Duplicate files:")
        print(duplicates)
        print("File hashes:")
        print(hashes)

def find_duplicate_files(directory):
        hashes = {}
        duplicates = []
        for root,_, files in os.walk(directory):
            for filename in files:
                filepath = os.path.join(root, filename)
                try:
                    with open(filepath, 'rb') as f:
                        # I read the file and I verify if the hash of the file is already in the dictionary,
                        # if it is, I add the file to the list of duplicates, otherwise I add the hash to the dictionary
                        filehash = hashlib.md5(f.read()).hexdigest()
                    if filehash in hashes:
                        duplicates.append(filepath)
                    else:
                        hashes[filehash] = filepath
                except Exception as e:
                    pass
        return duplicates, hashes

if __name__ == "__main__":
    question1()
    print('-'*10)
    question2()
    print('-'*10)
    question4()

    
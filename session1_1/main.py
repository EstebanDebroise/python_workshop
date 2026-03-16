import random
import os
import hashlib

def question1():
    """
    1. Generate a random placement of numbers from 1 to 100 into a 10 x 10 table.
    Display/print this as a table with numbers right-aligned.
    """
    randomlist = [[random.randint(1, 100) for i in range(10)] for j in range(10)]
    print_random_list_with_line(randomlist)

def print_random_list_with_line(randomlist):
    """
    Print a list of lists as a table with right-aligned numbers and lines separating the rows.
    param :
        - randomlist : list of lists of numbers to print
    return : None
    """
    for i in randomlist:
        for j in i:
            print(j if j >99 else '0' + str(j) if j>9 else '00' + str(j), end='|')
        print(' ')  # Print a newline after each row
        print('-' * len(i) * 4)  # Print a separator line

def question2():
    """
    2. Generate a 10x10 table of random integers in the 1..10 range.

    Find duplicates in previous table.
    """
    randomlist = [[random.randint(1,10) for i in range(10)] for j in range(10)]
    print(randomlist)
    duplicates = find_duplicate(randomlist)
    print("Duplicate numbers:", duplicates)
    

def find_duplicate(randomlist):
    """
    Find duplicates in a list of lists of numbers.
    param :
        - randomlist : list of lists of numbers to find duplicates in
    return : list of duplicates found in the list of lists
    """
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
        """
        4. Write a script which searches for duplicate files in a directory. Let it
        """
        directory = "session1_1/testq4"
        duplicates, hashes = find_duplicate_files(directory)
        print("Duplicate files:")
        print(duplicates)
        print("File hashes:")
        print(hashes)

def find_duplicate_files(directory):
        """
        Find duplicate files in a directory based on their MD5 hashes.
        param :
            - directory : path to the directory to search for duplicates
        return : tuple of (list of duplicate file paths, dictionary of file hashes)
        """
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

    
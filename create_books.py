import pickle
from book import Book


# this module initialises the book list. it should only be ran once, as it resets the entire book list

def create_book_list():
    book_list = []
    for i in range(0, 10):
        book_list.append(Book())

    with open('resources/book_list', 'wb') as fp:
        pickle.dump(book_list, fp)


create_book_list()

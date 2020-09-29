import pickle
from book import Book

# module which provides book access methods to the nodes

# loads and returns the book list
def get_book_list():
    with open('resources/book_list', 'rb') as fp:
        book_list = pickle.load(fp)
        return book_list


# saves the modified book list back on file
def save_book_list(book_list):
    with open('resources/book_list', 'wb') as fp:
        pickle.dump(book_list, fp)


# performs the borrow operation. Updates the book's customer id and changes the status of the book
# if request is invalid, it will return false
def borrow_book(customer, book_id):
    book_list = get_book_list()
    for book in book_list:
        if book.bookID == book_id and not book.onLoan:
            print("[RESOURCE] Lending book", book.bookID, "to", customer)
            book.onLoan = True
            book.customerID = customer
            save_book_list(book_list)
            return True
    return False


# performs the return operation. Updates the book's customer id to an empty string and changes the status of the book
# if request is invalid, it will return false
def return_book(customer, book_id):
    book_list = get_book_list()
    for book in book_list:
        if book.bookID == book_id and book.onLoan and book.customerID == customer:
            print("[RESOURCE] Returning book", book.bookID, "from", customer)
            book.onLoan = False
            book.customerID = ""
            save_book_list(book_list)
            return True
    return False


# utility method to print the details of all the books in the list
def print_list_details():
    book_list = get_book_list()
    for book in book_list:
        print('book with ID:', book.bookID, 'Is on Loan?', book.onLoan, 'It is held by:', book.customerID)

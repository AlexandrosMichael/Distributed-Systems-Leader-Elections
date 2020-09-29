# module which defines the Book class whose instances will represent individual books in the book list
class Book:
    # static variable which increments whenever the class constructor is called
    # it will be the unique id of the book
    bookID = 0
    def __init__(self):
        Book.bookID += 1
        self.bookID = Book.bookID
        self.onLoan = False
        self.customerID = ""

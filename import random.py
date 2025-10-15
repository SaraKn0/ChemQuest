class Book:
    def __init__(self, title="Unknown", author="Anonymous", pages=100):
        self.title = title
        self.author = author
        self.pages = pages

book1 = Book("The Giver", "Lois Lowry", 240)
book2 = Book()  # uses default values

print(f"Book 1: {book1.title} by {book1.author}")
print(f"Book 2: {book2.title} by {book2.author}")

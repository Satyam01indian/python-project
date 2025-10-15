import collections
import uuid
import sys

# --- 1. Data Structure Definitions (DSA & OOP) ---

class Book:
    """
    Represents a book in the library.
    
    Data Structures used:
    - Queue (self.waiting_list): A FIFO structure for members waiting to borrow the book.
    """
    def __init__(self, title, author, isbn, total_copies):
        self.isbn = isbn  # Key for the main catalog (Hash Map lookup)
        self.title = title
        self.author = author
        self.total_copies = total_copies
        self.available_copies = total_copies
        self.waiting_list = collections.deque() # Queue for FIFO waiting list

    def __str__(self):
        return (f"Title: {self.title} | Author: {self.author} | ISBN: {self.isbn} | "
                f"Available: {self.available_copies}/{self.total_copies} | Waitlist: {len(self.waiting_list)}")

class Member:
    """
    Represents a library member.
    """
    def __init__(self, name):
        # Generate a unique ID for the member
        self.member_id = str(uuid.uuid4())[:8] 
        self.name = name
        # A list to track borrowed book ISBNs (Conceptually acts as a dynamic chain of transactions)
        self.borrowed_books = [] 
        self.max_borrow_limit = 3

    def __str__(self):
        return (f"Member ID: {self.member_id} | Name: {self.name} | "
                f"Books Borrowed: {len(self.borrowed_books)}/{self.max_borrow_limit}")

class Library:
    """
    The core management system, utilizing Hash Maps for efficient tracking.
    """
    def __init__(self):
        # Hash Map: ISBN -> Book object (Key: ISBN, Value: Book)
        self.catalog = {} 
        # Hash Map: MemberID -> Member object (Key: MemberID, Value: Member)
        self.members = {}

    # --- 2. Core Library Operations ---

    def add_book(self, book):
        """Adds a new book or increments copies of an existing book."""
        if book.isbn in self.catalog:
            existing_book = self.catalog[book.isbn]
            existing_book.total_copies += book.total_copies
            existing_book.available_copies += book.available_copies
            print(f"Book '{book.title}' already exists. Added {book.total_copies} new copies.")
        else:
            self.catalog[book.isbn] = book
            print(f"New book '{book.title}' added to catalog.")

    def register_member(self, member):
        """Registers a new member."""
        self.members[member.member_id] = member
        print(f"Member '{member.name}' registered with ID: {member.member_id}")

    def search_book(self, query):
        """Searches catalog by ISBN, Title, or Author (O(1) for ISBN lookup)."""
        results = []
        if query in self.catalog:
            # Direct Hash Map lookup by ISBN (O(1))
            results.append(self.catalog[query]) 
        else:
            # Sequential search by Title/Author (O(N) - necessary when not using the key)
            for book in self.catalog.values():
                if query.lower() in book.title.lower() or query.lower() in book.author.lower():
                    results.append(book)
        
        if results:
            print("\n--- Search Results ---")
            for book in results:
                print(book)
        else:
            print(f"No books found matching '{query}'.")

    def borrow_book(self, isbn, member_id):
        """Handles borrowing, checking limits, and managing the waiting list."""
        book = self.catalog.get(isbn)
        member = self.members.get(member_id)

        if not book:
            print(f"Error: Book with ISBN {isbn} not found.")
            return

        if not member:
            print(f"Error: Member with ID {member_id} not found.")
            return

        if len(member.borrowed_books) >= member.max_borrow_limit:
            print(f"Error: {member.name} has reached the borrowing limit ({member.max_borrow_limit} books).")
            return
            
        if book.available_copies > 0:
            # Successful immediate borrow
            book.available_copies -= 1
            member.borrowed_books.append(isbn)
            print(f"Success: '{book.title}' borrowed by {member.name}.")
            print(f"Remaining copies: {book.available_copies}")
        else:
            # Add to the FIFO Waiting List (Queue)
            if member_id not in book.waiting_list:
                book.waiting_list.append(member_id)
                print(f"Info: '{book.title}' is currently out. {member.name} added to the waiting list (Position: {len(book.waiting_list)}).")
            else:
                print(f"Info: {member.name} is already on the waiting list for '{book.title}'.")

    def return_book(self, isbn, member_id):
        """Handles returning a book and notifying the next member in the queue."""
        book = self.catalog.get(isbn)
        member = self.members.get(member_id)

        if not book or not member:
            print("Error: Book or Member not found.")
            return

        if isbn not in member.borrowed_books:
            print(f"Error: Book with ISBN {isbn} was not borrowed by {member.name}.")
            return

        # 1. Update book and member records
        book.available_copies += 1
        member.borrowed_books.remove(isbn)
        print(f"Success: '{book.title}' returned by {member.name}.")

        # 2. Check the Waiting List (Queue)
        if book.waiting_list:
            # Dequeue the next member (FIFO)
            next_member_id = book.waiting_list.popleft() 
            next_member = self.members.get(next_member_id)
            
            if next_member:
                print(f"\n*** NOTIFICATION ***")
                print(f"'{book.title}' is now available! Notifying next in queue: {next_member.name} (ID: {next_member_id}).")
                # Note: The system requires the member to manually borrow it now.
            else:
                print("Warning: Next member in queue was not found.")


# --- 3. Command Line Interface (CLI) ---

def display_menu():
    """Prints the main menu options."""
    print("\n" + "="*40)
    print("      Library Management System")
    print("="*40)
    print("1. Add Book")
    print("2. Register Member")
    print("3. Search Book (ISBN/Title/Author)")
    print("4. Borrow Book")
    print("5. Return Book")
    print("6. View Catalog")
    print("7. View Members")
    print("8. Exit")
    print("="*40)

def main():
    library = Library()

    # Initial Setup (Pre-populating the Hash Maps)
    library.add_book(Book("Data Structures in Python", "Smith J.", "978-1-9876", 5))
    library.add_book(Book("Graph Algorithms Handbook", "Alice K.", "978-2-3456", 2))
    library.add_book(Book("System Design Principles", "Bob L.", "978-3-4567", 1)) 
    
    member_a = Member("Emily Johnson")
    member_b = Member("Chris Lee")
    library.register_member(member_a)
    library.register_member(member_b)
    
    print("\n--- Initial Setup Complete ---")

    while True:
        display_menu()
        choice = input("Enter your choice: ").strip()

        try:
            if choice == '1':
                title = input("Title: ")
                author = input("Author: ")
                isbn = input("ISBN: ")
                copies = int(input("Total Copies: "))
                library.add_book(Book(title, author, isbn, copies))
            
            elif choice == '2':
                name = input("Member Name: ")
                library.register_member(Member(name))

            elif choice == '3':
                query = input("Enter ISBN, Title, or Author to search: ")
                library.search_book(query)

            elif choice == '4':
                member_id = input("Enter Member ID: ")
                isbn = input("Enter Book ISBN to borrow: ")
                library.borrow_book(isbn, member_id)

            elif choice == '5':
                member_id = input("Enter Member ID: ")
                isbn = input("Enter Book ISBN to return: ")
                library.return_book(isbn, member_id)

            elif choice == '6':
                print("\n--- Full Book Catalog (Hash Map Contents) ---")
                if not library.catalog:
                    print("Catalog is empty.")
                    continue
                for book in library.catalog.values():
                    print(book)

            elif choice == '7':
                print("\n--- Registered Members (Hash Map Contents) ---")
                if not library.members:
                    print("No members registered.")
                    continue
                for member in library.members.values():
                    print(member)

            elif choice == '8':
                print("Exiting Library Management System. Goodbye!")
                sys.exit()

            else:
                print("Invalid choice. Please enter a number between 1 and 8.")

        except ValueError:
            print("Invalid input. Please ensure copies is a number.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":

    main()


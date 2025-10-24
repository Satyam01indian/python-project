import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTabWidget, QToolBar, QSizePolicy
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QAction

# --- Helper Class for the Web View (The Tab Content) ---
class BrowserTab(QWebEngineView):
    """Represents a single tab/web page view."""
    # Signal to update the main window's URL bar when navigation happens inside the tab
    url_changed_in_tab = pyqtSignal(QUrl)

    def __init__(self):
        super().__init__()
        # Connect the internal signal for URL change to our custom signal
        self.urlChanged.connect(self.handle_url_change)
        # Set a title to display in the tab bar
        self.setWindowTitle("New Tab")

    def handle_url_change(self, url):
        """Emits the URL to the parent window."""
        self.url_changed_in_tab.emit(url)
        # The titleChanged connection is now handled in BrowserWindow.add_new_tab
        # This prevents the AttributeError: 'NoneType' object has no attribute 'parent'

# --- Main Browser Window ---
class BrowserWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyChrome - Python Browser")
        self.setMinimumSize(800, 600)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.current_tab_changed)

        self.setCentralWidget(self.tabs)

        # Create Navigation Toolbar (Chrome-like)
        nav_toolbar = QToolBar("Navigation")
        nav_toolbar.setStyleSheet("QToolBar { padding: 5px; background: #f1f3f4; border-bottom: 1px solid #ddd; }")
        self.addToolBar(nav_toolbar)

        # --- Navigation Buttons ---

        # Back Button (using standard Qt icons for a clean look)
        back_btn = QAction(QIcon.fromTheme("go-previous"), "Back", self)
        back_btn.triggered.connect(lambda: self.tabs.currentWidget().back())
        nav_toolbar.addAction(back_btn)

        # Forward Button
        forward_btn = QAction(QIcon.fromTheme("go-next"), "Forward", self)
        forward_btn.triggered.connect(lambda: self.tabs.currentWidget().forward())
        nav_toolbar.addAction(forward_btn)

        # Reload Button
        reload_btn = QAction(QIcon.fromTheme("view-refresh"), "Reload", self)
        reload_btn.triggered.connect(lambda: self.tabs.currentWidget().reload())
        nav_toolbar.addAction(reload_btn)

        # Home Button (Google homepage for Chrome-like feel)
        home_btn = QAction(QIcon.fromTheme("go-home"), "Home", self)
        home_btn.triggered.connect(lambda: self.navigate_home())
        nav_toolbar.addAction(home_btn)

        # --- Address Bar (Omnibox) ---
        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        self.url_bar.setPlaceholderText("Enter URL or search term here...")
        self.url_bar.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 18px; /* Rounded corners for Chrome look */
                padding: 5px 15px;
                background-color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #1a73e8; /* Blue border on focus */
                /* Removed box-shadow to prevent "Unknown property" warning */
            }
        """)
        
        # Address bar takes up most space (Chrome-like)
        self.url_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        nav_toolbar.addWidget(self.url_bar)

        # --- Add Tab Button ---
        add_tab_btn = QPushButton("+")
        add_tab_btn.setFixedSize(36, 36)
        add_tab_btn.setStyleSheet("""
            QPushButton {
                font-size: 24px;
                border-radius: 18px;
                border: 1px solid #ccc;
                background-color: #e8e8e8;
                padding: 0;
            }
            QPushButton:hover {
                background-color: #ddd;
            }
        """)
        add_tab_btn.clicked.connect(lambda: self.add_new_tab())
        nav_toolbar.addWidget(add_tab_btn)

        # Start with a home tab
        self.add_new_tab(QUrl("https://www.google.com"), "Google")

    def add_new_tab(self, qurl=None, label="New Tab"):
        """Adds a new tab with the specified URL."""
        if qurl is None:
            # Default to Google for a new tab
            qurl = QUrl("https://www.google.com")

        browser = BrowserTab()
        browser.setUrl(qurl)

        i = self.tabs.addTab(browser, label)
        self.tabs.setCurrentIndex(i)

        # CORRECT FIX: Connect the tab's title changed signal here, now that the parent hierarchy is established.
        # We pass the index 'i' so setTabText knows which tab to update.
        browser.titleChanged.connect(lambda title, index=i: self.setTabText(title, index))

        # Connect the tab's internal URL change signal to the main URL bar update
        browser.url_changed_in_tab.connect(self.update_url_bar)

        # Handle load finished for status updates
        browser.loadFinished.connect(lambda _, b=browser: self.tabs.setTabIcon(self.tabs.indexOf(b), b.icon()))

    def close_tab(self, index):
        """Closes the tab at the given index."""
        if self.tabs.count() < 2:
            # Don't close the last tab, but navigate it home
            self.tabs.currentWidget().setUrl(QUrl("https://www.google.com"))
            return

        self.tabs.removeTab(index)

    def navigate_to_url(self):
        """Handles navigation from the Omnibox."""
        q = self.url_bar.text()
        
        # Simple check: if no scheme, assume a search or add 'http://'
        if not q.startswith('http'):
            # Check for a single word, likely a search term
            if ' ' not in q and '.' not in q:
                # Treat as a search query
                q = f"https://www.google.com/search?q={q}"
            else:
                # Assume a partial URL and default to HTTPS
                q = 'https://' + q
                
        url = QUrl(q)

        if url.isValid():
            self.tabs.currentWidget().setUrl(url)
        else:
            # Handle invalid URL by turning it into a search
            search_query = f"https://www.google.com/search?q={self.url_bar.text()}"
            self.tabs.currentWidget().setUrl(QUrl(search_query))


    def update_url_bar(self, url):
        """Updates the address bar when the tab navigates."""
        if self.tabs.currentWidget() == self.sender():
            self.url_bar.setText(url.toString())
            # Ensure text is not cut off when viewing the full URL
            self.url_bar.setCursorPosition(0)

    def current_tab_changed(self, index):
        """Updates the URL bar and title when the active tab changes."""
        if index != -1:
            current_browser = self.tabs.widget(index)
            self.update_url_bar(current_browser.url())
            self.setWindowTitle(f"{current_browser.title()} - PyChrome")
        
    def setTabText(self, title, index=None):
        """Updates the title of the specified tab."""
        # Use current index if none is explicitly provided (e.g., if called directly)
        if index is None:
            index = self.tabs.currentIndex()

        if index != -1:
            # Only use the first part of the title for brevity in the tab bar
            self.tabs.setTabText(index, title.split(" - ")[0])
            
            # Only update the main window title if the tab being updated is the current one
            if index == self.tabs.currentIndex():
                self.setWindowTitle(f"{title} - PyChrome")

    def navigate_home(self):
        """Navigates the current tab to the home page."""
        self.tabs.currentWidget().setUrl(QUrl("https://www.google.com"))

# --- Main Execution ---
if __name__ == '__main__':
    # Set the application's style for a cleaner look
    QApplication.setStyle("Fusion")
    
    app = QApplication(sys.argv)
    
    main_window = BrowserWindow()
    main_window.show()

    try:
        sys.exit(app.exec())
    except SystemExit:
        # Handle graceful exit
        print("Closing PyChrome...")

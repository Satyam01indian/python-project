import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTabWidget, QToolBar, QSizePolicy
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, Qt, pyqtSignal, QSize
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

# --- Main Browser Window ---
class BrowserWindow(QMainWindow):
    # Configuration for default search and home page
    DEFAULT_HOME_URL = QUrl("https://bing.com/")
    # Placeholder {0} will be replaced by the search query
    SEARCH_URL_TEMPLATE = "https://bing.com/?q={0}"

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyChrome - Python Browser")
        self.setMinimumSize(800, 600)

        # Main Tab Widget
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.current_tab_changed)

        self.setCentralWidget(self.tabs)

        # Create Navigation Toolbar (Sleek and flat design)
        nav_toolbar = QToolBar("Navigation")
        nav_toolbar.setIconSize(QSize(20, 20))
        # Flat white background with a subtle border for a modern look
        nav_toolbar.setStyleSheet("QToolBar { background: #ffffff; border-bottom: 1px solid #eee; padding: 5px; }")
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, nav_toolbar)

        # --- Navigation Buttons ---

        # Back Button
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

        # Home Button (Now defaults to DuckDuckGo)
        home_btn = QAction(QIcon.fromTheme("go-home"), "Home", self)
        home_btn.triggered.connect(self.navigate_home)
        nav_toolbar.addAction(home_btn)

        # --- Address Bar (Omnibox) ---
        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        self.url_bar.setPlaceholderText("Enter URL or search term here...")
        self.url_bar.setStyleSheet("""
            QLineEdit {
                border: 1px solid #dfe1e5;
                border-radius: 20px; /* Slightly less rounded */
                padding: 5px 15px;
                background-color: #f1f3f4; /* Light gray background */
                font-size: 14px;
                min-height: 36px;
                color: #202124;
            }
            QLineEdit:focus {
                border: 1px solid #dadce0;
                background-color: white; /* White on focus */
                box-shadow: none; /* Reset shadow */
            }
        """)
        
        # Address bar takes up most space
        self.url_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        nav_toolbar.addWidget(self.url_bar)

        # --- Add Tab Button ---
        # Changed to a standard action button for cleaner integration
        add_tab_action = QAction(QIcon.fromTheme("list-add"), "New Tab", self)
        add_tab_action.triggered.connect(self.add_new_tab)
        nav_toolbar.addAction(add_tab_action)

        # Start with a home tab using the new default URL
        self.add_new_tab(self.DEFAULT_HOME_URL, "Home")

    def add_new_tab(self, qurl=None, label="New Tab"):
        """Adds a new tab with the specified URL."""
        if qurl is None:
            # Default to the configured home page
            qurl = self.DEFAULT_HOME_URL

        browser = BrowserTab()
        browser.setUrl(qurl)

        i = self.tabs.addTab(browser, label)
        self.tabs.setCurrentIndex(i)

        # Connect signals for the new tab
        browser.titleChanged.connect(lambda title, index=i: self.setTabText(title, index))
        browser.url_changed_in_tab.connect(self.update_url_bar)
        browser.loadFinished.connect(lambda _, b=browser: self.tabs.setTabIcon(self.tabs.indexOf(b), b.icon()))

    def close_tab(self, index):
        """Closes the tab at the given index."""
        if self.tabs.count() < 2:
            # Don't close the last tab, but navigate it home using the new default URL
            self.tabs.currentWidget().setUrl(self.DEFAULT_HOME_URL)
            return

        self.tabs.removeTab(index)

    def navigate_to_url(self):
        """Handles navigation from the Omnibox, performing a search using the configured engine if needed."""
        q = self.url_bar.text()
        
        # 1. Check if the input is a valid URL with scheme
        if q.startswith('http'):
            url = QUrl(q)
        # 2. Check if it looks like a domain (has a dot)
        elif '.' in q:
            url = QUrl('https://' + q)
        # 3. Otherwise, treat as a search query
        else:
            # Use the configured search format (DuckDuckGo)
            search_query = self.SEARCH_URL_TEMPLATE.format(q)
            url = QUrl(search_query)

        if url.isValid():
            self.tabs.currentWidget().setUrl(url)
        else:
            # If the constructed URL is invalid, fall back to a basic search using the template
            search_query = self.SEARCH_URL_TEMPLATE.format(self.url_bar.text())
            self.tabs.currentWidget().setUrl(QUrl(search_query))

    def update_url_bar(self, url):
        """Updates the address bar when the tab navigates."""
        if self.tabs.currentWidget() == self.sender():
            self.url_bar.setText(url.toString())
            # Ensure text is visible from the start
            self.url_bar.setCursorPosition(0)

    def current_tab_changed(self, index):
        """Updates the URL bar and title when the active tab changes."""
        if index != -1:
            current_browser = self.tabs.widget(index)
            self.update_url_bar(current_browser.url())
            self.setWindowTitle(f"{current_browser.title()} - PyChrome")
        
    def setTabText(self, title, index):
        """Updates the title of the specified tab."""
        if index != -1:
            # Only use the first part of the title for brevity in the tab bar
            self.tabs.setTabText(index, title.split(" - ")[0])
            
            # Only update the main window title if the tab being updated is the current one
            if index == self.tabs.currentIndex():
                self.setWindowTitle(f"{title} - PyChrome")

    def navigate_home(self):
        """Navigates the current tab to the home page (DuckDuckGo)."""
        self.tabs.currentWidget().setUrl(self.DEFAULT_HOME_URL)

# --- Main Execution ---
if __name__ == '__main__':
    # Use the 'Fusion' style for a cross-platform, modern appearance
    QApplication.setStyle("Fusion")
    
    app = QApplication(sys.argv)
    
    main_window = BrowserWindow()
    main_window.show()

    try:
        sys.exit(app.exec())
    except SystemExit:
        print("Closing PyChrome...")

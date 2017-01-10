import os
import sys
import time
import subprocess
#sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))+"/lib")

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import *
from PyQt4.QtGui import *

app_name = "fman File Manager"
initial_width = 750
initial_height = 450



my_name = "main.py"

_delim = "/"

class preferences:
	def __init__(self,should_load=True):
		if should_load:
			self.load()

	def save(self):
		f = open("data/prefs.txt",'w')
		f.write("home-->"+self.home_directory+"\n")
		f.write("open_to_home_by_default-->"+self.open_home_default+"\n")

	def set_value(self,tag,value):
		if tag == "home":
			#self.home_directory = value
			self.home_directory = "/" if os.name!="nt" else "C:\\"
			return
		if tag == "open_to_home_by_default":
			self.open_home_default = value
			return

	def load(self):
		try:
			f = open("data/prefs.txt","r")
			data = f.read()
			data = data.split("\n")
			for line in data:
				vals = line.split("-->")
				tag = vals[0]
				val = vals[1]
				self.set_value(tag,val)
		except:
			self.home_directory = "/" if os.name!="nt" else "C:\\"
			self.open_home_default = "YES"


univ_prefs = preferences()
done_setting_prefs = False

class preferences_window(QWidget):

	def __init__(self, parent=None):

		super(preferences_window,self).__init__()
		self.initUI()
		self.prefs = preferences(False)

	def initUI(self):

		self.layout = QVBoxLayout(self)
		self.setWindowTitle("Preferences")

		self.home_dir_label = QLabel("Home Directory:",self)
		self.home_dir_line = QLineEdit("",self)
		self.home_dir_line.textChanged.connect(self.prefs_changed)
		first_row = QHBoxLayout()
		first_row.addWidget(self.home_dir_label)
		first_row.addWidget(self.home_dir_line)
		self.layout.addLayout(first_row)

		self.open_home_default_label = QLabel("Open to Home directory by default?",self)
		self.open_home_default_checkbox = QCheckBox(self)
		self.open_home_default_checkbox.stateChanged.connect(self.prefs_changed)
		second_row = QHBoxLayout()
		second_row.addWidget(self.open_home_default_label)
		second_row.addWidget(self.open_home_default_checkbox)
		self.layout.addLayout(second_row)


		self.revert_button = QPushButton("Revert",self)
		self.revert_button.clicked.connect(self.revert_prefs)
		self.reset_button = QPushButton("Reset to defaults",self)
		self.reset_button.clicked.connect(self.reset_prefs)

		last_row = QHBoxLayout()
		last_row.addWidget(self.revert_button)
		last_row.addWidget(self.reset_button)
		self.layout.addLayout(last_row)

		self.save = QPushButton("Save and Return",self)
		self.save.clicked.connect(self.save_prefs)
		send_row = QHBoxLayout()
		send_row.addWidget(self.save)
		self.layout.addLayout(send_row)

	def save_prefs(self):
		global univ_prefs
		global done_setting_prefs
		univ_prefs = self.prefs
		done_setting_prefs = True
		self.hide()
		self.emit(SIGNAL("return_prefs()"))

	def revert_prefs(self):
		if hasattr(self,'provided_prefs')==False:
			return
		self.home_dir_line.setText(self.provided_prefs.home_directory)
		self.open_home_default_checkbox.setChecked(True if self.provided_prefs.open_home_default=="YES" else False)

	def reset_prefs(self):
		self.prefs = preferences()
		self.home_dir_line.setText(self.prefs.home_directory)
		self.open_home_default_checkbox.setChecked(True if self.prefs.open_home_default=="YES" else False)

	def open_window(self, prefs):
		self.provided_prefs = prefs 
		self.home_dir_line.setText(prefs.home_directory)
		self.open_home_default_checkbox.setChecked(True if prefs.open_home_default=="YES" else False)
		self.show()

	def prefs_changed(self):
		self.prefs.home_directory = self.home_dir_line.text()
		self.prefs.open_home_default = "YES" if self.open_home_default_checkbox.isChecked()==True else "NO"

class main_window(QWidget):

	def __init__(self, parent=None):

		super(main_window, self).__init__()
		self.init_vars()
		self.init_ui()

	def init_vars(self):
		global _delim
		#print "initVars()"
		self.my_prefs = preferences()
		self.child_windows = []
		self.this_dir_path = os.path.dirname(os.path.realpath(__file__))
		self.visited = []
		self.un_visited = []
		self.host_os = os.name
		if self.host_os == "nt":
			_delim = "\\"
			#_delim = "/"

		self.prefs_window = preferences_window()

	def init_ui(self):

		# Layout items
		self.layout = QVBoxLayout(self)
		if self.host_os == "nt":
			self.layout.addSpacing(20)

		# Menu items
		self.menubar = QMenuBar(self)
		self.file_menu = self.menubar.addMenu("File")
		self.edit_menu = self.menubar.addMenu("Edit")
		self.tool_menu = self.menubar.addMenu("Tools")
		self.place_menu = self.menubar.addMenu("Places")
		self.menubar.resize(self.menubar.sizeHint())

		# Menubar actions
		self.new_window_action = self.file_menu.addAction("New Window", self.new_window, QKeySequence("Ctrl+N"))
		self.new_window_action.setEnabled(False)
		self.restart_app_action = self.file_menu.addAction("Restart Application", self.restart_app, QKeySequence("Ctrl+R"))
		self.restart_app_action.setEnabled(False)
		self.exit_action = self.file_menu.addAction("Quit", self.quit_app, QKeySequence("Ctrl+Q"))
		self.edit_prefs_action = self.edit_menu.addAction("Preferences...", self.edit_prefs)
		self.home_action = self.place_menu.addAction("Home", self.open_location, QKeySequence("Ctrl+D"))

		# address bar
		self.address_bar = QLineEdit("", self)
		self.address_bar.setEnabled(False)

		# navigation buttons
		self.up_dir_button = QPushButton("",self)
		self.up_dir_button.setIcon(QIcon("resources/up.png"))
		self.up_dir_button.clicked.connect(self.up)
		self.up_dir_button.resize(self.up_dir_button.sizeHint())

		self.back_button = QPushButton("",self)
		self.back_button.setIcon(QIcon("resources/back.png"))
		self.back_button.clicked.connect(self.back)
		self.back_button.resize(self.back_button.sizeHint())

		self.forward_button = QPushButton("",self)
		self.forward_button.setIcon(QIcon("resources/forward.png"))
		self.forward_button.clicked.connect(self.forward)
		self.forward_button.resize(self.forward_button.sizeHint())

		self.home_button = QPushButton("",self)
		self.home_button.setIcon(QIcon("resources/home.png"))
		self.home_button.clicked.connect(self.home)
		self.home_button.resize(self.home_button.sizeHint())

		# search bar
		self.search_bar = QLineEdit(self)
		self.search_bar.setPlaceholderText("search...")
		self.search_bar.textChanged.connect(self.search)

		# recent locations list
		#self.recent = QListWidget()
		#self.recent.itemDoubleClicked.connect(self.recent_item_chosen)

		# layout stuff
		self.top_row = QHBoxLayout()
		self.top_row.addWidget(self.back_button)
		self.top_row.addWidget(self.forward_button)
		self.top_row.addWidget(self.up_dir_button)
		self.top_row.addWidget(self.address_bar,2)
		self.top_row.addWidget(self.search_bar,1)

		self.layout.addLayout(self.top_row)

		# initializing some layouts
		self.navigation_layout = QVBoxLayout() # left side of display square, below address bar
		self.display_layout = QVBoxLayout() # display square

		self.second_row = QHBoxLayout() # row below address bar row, holds navigation and square display
		self.second_row.addLayout(self.navigation_layout)
		self.second_row.addLayout(self.display_layout)
		self.layout.addLayout(self.second_row)

		self.navigation_top_row = QHBoxLayout()
		self.navigation_layout.addLayout(self.navigation_top_row)
		self.navigation_top_row.addWidget(self.home_button)

		self.navigation_second_row = QHBoxLayout()
		#self.navigation_second_row.addWidget(self.recent)
		self.navigation_layout.addLayout(self.navigation_second_row)

		# display area
		self.display = QListWidget()
		self.display_layout.addWidget(self.display)
		self.display.itemDoubleClicked.connect(self.item_chosen)

		self.resize(initial_width,initial_height)
		self.setWindowTitle(app_name)
		self.update_ui(True)

		QtCore.QObject.connect(self.prefs_window, QtCore.SIGNAL("return_prefs()"), self.end_pref_edit)
		self.show()

	def end_pref_edit(self):
		self.my_prefs = univ_prefs
		self.my_prefs.save()

	def edit_prefs(self):
		global done_setting_prefs
		done_setting_prefs = False

		self.prefs_window.open_window(self.my_prefs)

		#while done_setting_prefs==False:
		#	time.sleep(0.01)

		#self.my_prefs = univ_prefs
		#self.my_prefs.save()

	def forward(self):
		if len(self.un_visited)==0:
			return

		new_loc = self.un_visited[len(self.un_visited)-1]
		del self.un_visited[-1]
		self.current_location = new_loc
		self.update_ui()

	def search(self):
		print "here - search"

	def open_details(self,filename):
		print "here - open_details"

	def item_chosen(self):
		cur = self.display.currentItem().text()
		full_name = self.current_location+_delim+cur 

		if os.path.isdir(full_name):
			self.current_location = full_name
			self.update_ui()
			return

		if os.path.isfile(full_name):
			self.open_details(full_name)
			return

	def home(self):
		self.current_location = self.my_prefs.home_directory
		self.update_ui()

	def update_address_bar(self,new_loc):
		self.address_bar.setText(new_loc)

	def update_display(self,new_loc):
		elems = os.listdir(new_loc)
		self.display.clear()
		for elem in elems:

			new_widget = QListWidgetItem(elem)
			elem = new_loc+_delim+elem

			if os.path.isdir(elem):
				new_widget.setIcon(QIcon("resources/directory.png"))
			if os.path.isfile(elem):
				new_widget.setIcon(QIcon("resources/file.png"))

			self.display.addItem(new_widget)

	def update_ui(self, init=False):

		if init:
			self.current_location = self.this_dir_path

			if hasattr(self,'my_prefs')==True:
				self.current_location = self.my_prefs.home_directory

		self.visited.append(self.current_location)
		self.update_address_bar(self.current_location)
		self.update_display(self.current_location)

	def up(self):
		cur = self.address_bar.text()
		cur = cur.split(_delim)
		del cur[-1]
		new_loc = ""
		for elem in cur:
			new_loc += elem
			new_loc += _delim
		new_loc = new_loc[:len(new_loc)-1]
		self.current_location = new_loc

		self.update_ui()

	def back(self):
		if len(self.visited) <= 1:
			return

		self.un_visited.append(self.visited[len(self.visited)-1])
		del self.visited[-1]

		new_loc = self.visited[len(self.visited)-1]
		self.current_location = new_loc
		self.update_ui()


	# Redirects the UI to a new location, user's home directory by default
	def open_location(self, location="home"):

		for dirname, dirnames, filenames in os.walk('.'):
		    # print path to all subdirectories first.
		    for subdirname in dirnames:
		        print(os.path.join(dirname, subdirname))

		    # print path to all filenames.
		    for filename in filenames:
		        print(os.path.join(dirname, filename))

		    # Advanced usage:
		    # editing the 'dirnames' list will stop os.walk() from recursing into there.
		    if '.git' in dirnames:
		        # don't go into any .git directories.
		        dirnames.remove('.git')

	# Restarts the application from command line
	def restart_app(self):
		#os.system("python "+my_name)
		self.hide()
		subprocess.call(" python "+my_name, shell=True)
		#self.close()
		#self.quit_app()
		
	# Closes all auxiliary and child windows
	def collect_garbage(self):

		for child in self.child_windows:
			child.collect_garbage()

	# Close all child windows when this one is closed
	def closeEvent(self, event):
		#self.collect_garbage()
		self.my_prefs.save()
		event.accept()

	# Quits the app and closes all child windows
	def quit_app(self):
		self.collect_garbage()
		self.close()

	# Open a new child window with default preferences
	def new_window(self):
		temp = main_window(self)
		self.child_windows.append(temp)

def main():
	pyqt_app = QtGui.QApplication(sys.argv)
	pyqt_app.setWindowIcon(QIcon("resources/logo.png"))
	_ = main_window()
	sys.exit(pyqt_app.exec_())


if __name__ == '__main__':
	main()
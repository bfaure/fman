import os
import sys
import time
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))+"/lib/text_editor_files")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))+"/lib/image_editor_files")
from text_editor import text_editor
from image_editor import image_editor

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import *
from PyQt4.QtGui import *

app_name = "fman File Manager"
initial_width = 750
initial_height = 450

my_name = "main.py"

_delim = "/"

# Want to add to preferences window to allow user to add custom mappings, i.e.
# allow the user to specify which applications should be used to open certain 
# file formats. Also give the ability to set to the default application that would
# be used by their OS or the default application which comes built in with this
# distribution of fman.


class preferences:
	def __init__(self,should_load=True):

		self.extra_prefs_values = []
		self.extra_prefs_tags = []
		if should_load:
			self.load()

	def save(self):
		f = open("data/prefs.txt",'w')
		f.write("home-->"+self.home_directory+"\n")
		f.write("open_to_home_by_default-->"+self.open_home_default+"\n")

		for tag,value in list(zip(self.extra_prefs_tags,self.extra_prefs_values)):
			f.write(tag+"-->"+value+"\n")

	# Assigns values to data (sourced from data/prefs.txt)
	def set_value(self,tag,value):
		#print "here - set_value"
		if tag == "home":
			self.home_directory = value
			#self.home_directory = "/" if os.name!="nt" else "C:\\"
			return
		if tag == "open_to_home_by_default":
			self.open_home_default = value
			return

		else:
			self.extra_prefs_values.append(value)
			self.extra_prefs_tags.append(tag)
			return

	# Tries to load user preferences from data/prefs.txt
	def load(self):
		fname = "data/prefs.txt"
		if os.path.isfile(fname):
			f = open("data/prefs.txt","r")
			data = f.read()
			data = data.split("\n")
			for line in data:
				vals = line.split("-->")
				if len(vals)<2: continue
				tag = vals[0]
				val = vals[1]
				self.set_value(tag,val)
			f.close()
		else:
			print "Could not locate saved preferences file (data/prefs.txt)."
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


class tab_details:
	def __init__(self):
		self.current_location = ""
		self.tab_index = ""
		self.visited = []
		self.un_visited = []
		self.tab_widget = ""

class main_window(QWidget):

	def __init__(self, parent=None):

		super(main_window, self).__init__()
		self.init_vars()
		self.init_ui()

	def init_vars(self):
		global _delim
		#print "here - initVars"
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
		print "Saved Home Directory = "+self.my_prefs.home_directory

		# text editor window
		self.text_editor_window = text_editor()

		# image editor window
		self.image_editor_window = image_editor()

		# list of tab_details structs, one for each tab that is open
		self.tabs = []

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
		self.edit_prefs_action = self.edit_menu.addAction("User Settings", self.edit_prefs)
		self.home_action = self.place_menu.addAction("Home", self.open_location, QKeySequence("Ctrl+D"))

		# address bar
		self.address_bar = QLineEdit("", self)
		self.address_bar.setEnabled(False)

		# navigation buttons
		self.up_dir_button = QPushButton(self)
		self.up_dir_button.setIcon(QIcon("resources/up.png"))
		self.up_dir_button.clicked.connect(self.up)
		self.up_dir_button.resize(self.up_dir_button.sizeHint())

		self.back_button = QPushButton(self)
		self.back_button.setIcon(QIcon("resources/back.png"))
		self.back_button.clicked.connect(self.back)
		if os.name !="nt": 
			self.back_button.setMaximumWidth(50) 
		else:
			self.back_button.resize(self.back_button.sizeHint())
		#self.back_button.resize(self.back_button.sizeHint())

		self.forward_button = QPushButton(self)
		self.forward_button.setIcon(QIcon("resources/forward.png"))
		self.forward_button.clicked.connect(self.forward)
		if os.name !="nt": 
			self.forward_button.setMaximumWidth(50) 
		else: 
			self.forward_button.resize(self.forward_button.sizeHint())
		#self.forward_button.resize(self.forward_button.sizeHint())

		self.home_button = QPushButton(self)
		self.home_button.setIcon(QIcon("resources/home.png"))
		self.home_button.clicked.connect(self.home)
		self.home_button.resize(self.home_button.sizeHint())

		self.info_button = QPushButton(self)
		self.info_button.setIcon(QIcon("resources/info.png"))
		self.info_button.clicked.connect(self.info)
		self.info_button.resize(self.info_button.sizeHint())

		# search bar
		self.search_bar = QLineEdit(self)
		self.search_bar.setPlaceholderText("search...")
		self.search_bar.textChanged.connect(self.search)

		# layout stuff
		self.top_row = QHBoxLayout()
		self.top_row.addWidget(self.back_button)
		self.top_row.addWidget(self.forward_button)
		self.top_row.addSpacing(10)
		self.top_row.addWidget(self.up_dir_button)
		#self.top_row.addSpacing(60)
		self.top_row.addStretch()
		self.top_row.addWidget(self.home_button)
		self.top_row.addWidget(self.info_button)
		self.top_row.addWidget(self.address_bar,3)
		self.top_row.addWidget(self.search_bar,2)

		self.layout.addLayout(self.top_row)

		self.tab_widget = QTabWidget()
		self.layout.addWidget(self.tab_widget)

		# acts as parent for layout held in first tab
		first_tab_parent = QWidget()

		# initializing some layouts
		display_layout = QVBoxLayout(first_tab_parent) # display square
		self.tab_widget.addTab(first_tab_parent,self.get_final_dir(self.my_prefs.home_directory))

		# display area
		display = QListWidget()
		display_layout.addWidget(display)
		display.itemDoubleClicked.connect(self.item_chosen)

		# button to open new tab
		self.tabButton = QToolButton(self)
		self.tabButton.setText('+')
		font = self.tabButton.font()
		font.setBold(True)
		self.tabButton.setFont(font)
		self.tab_widget.setCornerWidget(self.tabButton)
		self.tabButton.clicked.connect(self.create_new_tab)

		# data for first tab (only one at this point)
		first_tab_details = tab_details()
		first_tab_details.current_location = self.my_prefs.home_directory
		first_tab_details.tab_index = 0
		self.tabs.append(first_tab_details)

		# set when the tab is changed
		self.current_display_widget = display

		# current tab index
		self.current_tab_index = 0

		self.resize(initial_width,initial_height)
		self.setWindowTitle(app_name)
		self.update_ui(True)

		self.tab_widget.currentChanged.connect(self.tab_changed)
		QtCore.QObject.connect(self.prefs_window, QtCore.SIGNAL("return_prefs()"), self.end_pref_edit)
		self.show()

	# slot called when tab is changed
	def tab_changed(self):

		# update last tab info struct
		last_index = self.current_tab_index
		last_tab_struct = self.tabs[last_index]
		last_tab_struct.current_location = self.current_location
		last_tab_struct.visited = self.visited
		last_tab_struct.un_visited = self.un_visited
		last_tab_struct.tab_index = self.current_tab_index
		self.tabs[last_index] = last_tab_struct

		# load in this tabs info struct
		new_index = self.tab_widget.currentIndex()
		this_tab_struct = self.tabs[new_index]
		self.current_location = this_tab_struct.current_location
		self.visited = this_tab_struct.visited
		self.un_visited = this_tab_struct.un_visited


		# setting the current display widget (need to fetch it from layout)
		current_tab_parent = self.tab_widget.currentWidget()
		current_tab_layout = current_tab_parent.layout()

		# pull the display widget out of the layout for this tab
		self.current_display_widget = current_tab_layout.itemAt(0).widget()

		'''
		for i in range(current_tab_layout.count()):
			print current_tab_layout.itemAt(i)
		'''
		
		self.current_tab_index = new_index
		self.update_ui()

	# Returns just the last location in a path
	def get_final_dir(self,path):
		path = path.split(_delim)
		return path[len(path)-1]

	def create_new_tab(self):
		print "here - create_new_tab"

		# saving current tab details to appropriate tab_details struct
		index = self.tab_widget.currentIndex()
		tab_info = self.tabs[index]
		tab_info.current_location = self.current_location
		tab_info.tab_index = index
		tab_info.visited = self.visited
		tab_info.un_visited = self.un_visited
		self.tabs[index] = tab_info

		# clearing back/forward buffers
		self.visited = []
		self.un_visited = []
		self.current_location = self.my_prefs.home_directory

		# creating new tab
		new_tab_parent = QWidget()
		new_tab_details = tab_details()
		new_tab_details.current_location = self.my_prefs.home_directory
		new_tab_details.tab_index = self.tab_widget.count()
		self.tabs.append(new_tab_details)

		# initializing some layouts
		display_layout = QVBoxLayout(new_tab_parent) # display square
		display = QListWidget()
		display_layout.addWidget(display)
		display.itemDoubleClicked.connect(self.item_chosen)

		self.tab_widget.addTab(new_tab_parent,self.get_final_dir(self.my_prefs.home_directory))

		self.current_display_widget = display
		self.current_tab_index = self.tab_widget.count()-1
		self.tab_widget.setCurrentIndex(self.current_tab_index)
		self.update_ui()

	def info(self):
		print "here - info"

	def end_pref_edit(self):
		self.my_prefs = univ_prefs
		self.my_prefs.save()
		self.show()

	def edit_prefs(self):
		global done_setting_prefs
		done_setting_prefs = False

		self.prefs_window.open_window(self.my_prefs)
		self.hide()

	def forward(self):
		if len(self.un_visited)==0:
			return

		new_loc = self.un_visited[len(self.un_visited)-1]
		del self.un_visited[-1]
		self.current_location = new_loc
		self.update_ui()

	def search(self):
		print "here - search"

	# Check if file selected is an image
	def is_imagefile(self,filename):
		image_exts = [".jpg",".png",".jpeg",".gif"]
		filename = str(filename)
		for ext in image_exts:
			if filename.find(ext)!=-1:
				return True
		return False

	# Check if file selected is text (returning True by default now)
	def is_textfile(self,filename):
		text_exts = [".txt"]
		return True

	# Called when user double clicks on a file in the display
	def open_details(self,filename):
		print "here - open_details"

		if self.is_imagefile(filename):
			self.image_editor_window.open_file(filename)
			return
		if self.is_textfile(filename):
			self.text_editor_window.open_file(filename)
			return

	# Called when user double clicks something in the display, routes to
	# open_details (if file) or update_ui (if directory)
	def item_chosen(self):

		cur = self.current_display_widget.currentItem().text()
		full_name = self.current_location+_delim+cur

		# cover cases where we don't want to add delim because there already is one
		if cur == "/":
			full_name = self.current_location+cur
		if len(cur)<=3 and os.name=="nt":
			full_name = self.current_location+cur

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
		self.current_display_widget.clear()
		for elem in elems:

			new_widget = QListWidgetItem(elem)
			elem = new_loc+_delim+elem

			if os.path.isdir(elem):
				new_widget.setIcon(QIcon("resources/directory.png"))
			if os.path.isfile(elem):
				new_widget.setIcon(QIcon("resources/file.png"))

			self.current_display_widget.addItem(new_widget)

	# updates the tab title
	def update_tab_title(self,new_loc):
		self.tab_widget.setTabText(self.tab_widget.currentIndex(),self.get_final_dir(new_loc))

	# handles calling of functions that update the ui elements
	def update_ui(self, init=False):

		if init:
			self.current_location = self.this_dir_path

			if hasattr(self,'my_prefs')==True:
				self.current_location = self.my_prefs.home_directory

		self.visited.append(self.current_location)
		self.update_address_bar(self.current_location)
		self.update_display(self.current_location)
		self.update_tab_title(self.current_location)
		self.update_window_title(self.current_location)

	def update_window_title(self,new_loc):
		new_loc = new_loc.split(_delim)
		new_loc = new_loc[len(new_loc)-1]
		self.setWindowTitle(new_loc)

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
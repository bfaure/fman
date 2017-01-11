import os
import sys
import time
import subprocess
import datetime

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

class details_window(QWidget):

	def __init__(self, filename, path, parent=None):
		super(details_window, self).__init__()
		self.filename = filename
		self.filepath = path

		self.init_vars()
		self.init_ui()

	def init_vars(self):
		#print "here - details_window.init_vars"
		stats = os.stat(self.filepath)

		self.filesize = stats.st_size #file size in bytes
		self.modification_date = stats.st_mtime # time of most recent content change
		self.access_date = stats.st_atime # time of most recent access
		self.metadata_modification_date = stats.st_ctime # time of most recent change to metadata
		self.user_id = stats.st_uid # user id of owner
		self.group_id = stats.st_gid # group id of owner

	def init_ui(self):
		#print "here - details_window.init_ui"

		self.layout = QVBoxLayout(self)

		self.setWindowTitle(self.filename)

		filesize_label = QLabel("Size:")
		filesize_real = str(self.filesize/1000)+" KB"
		if self.filesize<1000:
			filesize_real = str(self.filesize)+" B"
		filesize_value = QLineEdit(filesize_real)
		filesize_value.setEnabled(False)
		first_row = QHBoxLayout()
		first_row.addWidget(filesize_label)
		first_row.addWidget(filesize_value)
		self.layout.addLayout(first_row)

		modification_date_string = datetime.datetime.fromtimestamp(self.modification_date).strftime('%Y-%m-%d %H:%M:%S')
		access_date_string = datetime.datetime.fromtimestamp(self.access_date).strftime('%Y-%m-%d %H:%M:%S')
		metadata_modification_date_string = datetime.datetime.fromtimestamp(self.metadata_modification_date).strftime('%Y-%m-%d %H:%M:%S')

		modification_date_label = QLabel("Last Modified:")
		modification_date_value = QLineEdit(modification_date_string)
		modification_date_value.setEnabled(False)
		second_row = QHBoxLayout()
		second_row.addWidget(modification_date_label)
		second_row.addWidget(modification_date_value)
		self.layout.addLayout(second_row)

		access_date_label = QLabel("Last Accessed:")
		access_date_value = QLineEdit(access_date_string)
		access_date_value.setEnabled(False)
		third_row = QHBoxLayout()
		third_row.addWidget(access_date_label)
		third_row.addWidget(access_date_value)
		self.layout.addLayout(third_row)

		metadata_modification_label = QLabel("Metadata Modified:")
		metadata_modification_value = QLineEdit(metadata_modification_date_string)
		metadata_modification_value.setEnabled(False)
		fourth_row = QHBoxLayout()
		fourth_row.addWidget(metadata_modification_label)
		fourth_row.addWidget(metadata_modification_value)
		self.layout.addLayout(fourth_row)

		user_id_label = QLabel("User ID:")
		user_id_value = QLineEdit(str(self.user_id))
		user_id_value.setEnabled(False)
		fifth_row = QHBoxLayout()
		fifth_row.addWidget(user_id_label)
		fifth_row.addWidget(user_id_value)
		self.layout.addLayout(fifth_row)

		group_id_label = QLabel("Group ID:")
		group_id_value = QLineEdit(str(self.group_id))
		group_id_value.setEnabled(False)
		sixth_row = QHBoxLayout()
		sixth_row.addWidget(group_id_label)
		sixth_row.addWidget(group_id_value)
		self.layout.addLayout(sixth_row)

		self.show()

class saved_place:
	def __init__(self,name_in_list,full_path):
		self.name = name_in_list
		self.location = full_path

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

		self.user_changing_list_item = False

		# list of saved places (left hand side of ui), at outset, the only
		# one will be the home directory
		self.saved_places = []

		home = saved_place("Home",self.my_prefs.home_directory)
		self.saved_places.append(home)

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

		self.second_row = QHBoxLayout()
		self.layout.addLayout(self.second_row)
		#self.layout.addWidget(self.tab_widget)

		self.navigation_display = QListWidget()
		self.second_row.addWidget(self.navigation_display)

		self.navigation_display.setMaximumWidth(125)
		self.navigation_display.itemClicked.connect(self.navigation_clicked)
		self.navigation_display.addItem("Home")

		# acts as parent for layout held in first tab
		first_tab_parent = QWidget()

		# initializing some layouts
		display_layout = QVBoxLayout(first_tab_parent) # display square
		self.tab_widget.addTab(first_tab_parent,self.get_final_dir(self.my_prefs.home_directory))

		# display area
		display = QListWidget()
		display_layout.addWidget(display)
		display.itemDoubleClicked.connect(self.item_chosen)
		display.itemChanged.connect(self.user_changed_list_item)
		display.setContextMenuPolicy(Qt.CustomContextMenu)
		display.customContextMenuRequested.connect(self.on_context_menu)
		
		# context menu stuff
		self.popMenu = QMenu(self)
		self.context_copy_action = self.popMenu.addAction("Copy Item",self.copy)
		self.context_copy_action.setEnabled(False)
		self.context_copy_text_action = self.popMenu.addAction("Copy Text",self.copy_text)
		self.context_copy_text_action.setEnabled(False)
		self.context_paste_action = self.popMenu.addAction("Paste Item",self.paste)
		self.context_paste_action.setEnabled(False)
		self.popMenu.addSeparator()
		self.context_rename_action = self.popMenu.addAction("Rename [Enter | F2]",self.rename)
		self.popMenu.addSeparator()
		self.context_save_action = self.popMenu.addAction("Save Place",self.save_place)

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

		self.second_row.addWidget(self.tab_widget)

		self.tab_widget.currentChanged.connect(self.tab_changed)
		QtCore.QObject.connect(self.prefs_window, QtCore.SIGNAL("return_prefs()"), self.end_pref_edit)

		self.load_saved_places()
		self.show()

	def save_place(self):
		print "here - save_place"
		cur = self.current_display_widget.currentItem().text()
		full_name = self.current_location+_delim+cur 

		# cant save a file, only directories
		if str(full_name).find(".")!=-1:
			return

		if os.path.isdir(full_name):
			new_place = saved_place(cur,full_name)
			self.saved_places.append(new_place)
			self.update_navi_display()

	# Clears then reloads all of the saved places
	def update_navi_display(self):
		self.navigation_display.clear()
		for item in self.saved_places:
			self.navigation_display.addItem(item.name)

	def navigation_clicked(self):

		selected = str(self.navigation_display.currentItem().text())
		dest = ""
		for place in self.saved_places:
			if place.name == selected:
				dest = place.location

		if dest == "":
			print "Could not find saved place."
			return

		self.current_location = dest
		self.update_ui()

	def copy(self):
		print "here - copy"

	def copy_text(self):
		print "here - copy_text"

	def paste(self):
		print "here - paste"

	def rename(self):
		print "here - rename"

		item = self.current_display_widget.currentItem()
		self.list_item_text = item.text()
		item.setFlags(item.flags() | Qt.ItemIsEditable)
		self.current_display_widget.editItem(item)
		self.user_changing_list_item = True
		self.change_index = self.current_display_widget.currentRow()

	def on_context_menu(self,point):
		self.popMenu.exec_(self.current_display_widget.mapToGlobal(point))

	# check if text follows rules for file or folder naming
	def item_text_validator(self,text):
		not_allowed = [",","/","\\"]
		text = str(text)
		for item in not_allowed:
			if text.find(item)!=-1:
				return False
		return True

	# slot activated whenever one of the list items is changed, we only
	# respond if the self.user_changing_list_item flag is set to true.
	def user_changed_list_item(self):

		if hasattr(self,'user_changing_list_item')==False:
			return
		if self.user_changing_list_item==False:
			return
		if self.current_display_widget.currentRow()!=self.change_index:
			return

		item_changed = self.current_display_widget.currentItem()
		new_text = item_changed.text()
		old_text = self.list_item_text
		#print "new_text = "+new_text+" old_text = "+old_text

		if self.item_text_validator(new_text)==False:
			item_changed.setText(old_text)
			return

		old_path = self.current_location+_delim+old_text
		new_path = self.current_location+_delim+new_text

		try:
			os.rename(old_path,new_path)

		except:
			item_changed.setText(old_text)

		self.user_changing_list_item = False

	# slot called when user clicks certain keys
	def keyPressEvent(self,event):

		# return if user is not interacting with display
		if self.current_display_widget.hasFocus()==False:
			return

		allow_editing_on = [Qt.Key_Return,Qt.Key_Enter,16777224]
		if event.key() in allow_editing_on:
			item = self.current_display_widget.currentItem()
			self.list_item_text = item.text()
			item.setFlags(item.flags() | Qt.ItemIsEditable)
			self.current_display_widget.editItem(item)
			self.user_changing_list_item = True
			self.change_index = self.current_display_widget.currentRow()

		# On space we want to allow the user to open the information pane			
		elif event.key() == Qt.Key_I:
			print "open the information pane here"
			

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
		#display.currentTextChanged.connect(self.user_changed_list_item)
		display.itemChanged.connect(self.user_changed_list_item)
		display.setContextMenuPolicy(Qt.CustomContextMenu)
		display.customContextMenuRequested.connect(self.on_context_menu)

		display_layout.addWidget(display)
		display.itemDoubleClicked.connect(self.item_chosen)

		self.tab_widget.addTab(new_tab_parent,self.get_final_dir(self.my_prefs.home_directory))

		self.current_display_widget = display
		self.current_tab_index = self.tab_widget.count()-1
		self.tab_widget.setCurrentIndex(self.current_tab_index)
		self.update_ui()

	def info(self):
		print "here - info"
		cur = self.current_display_widget.currentItem().text()
		full_name = self.current_location+_delim+cur
		detail_window = details_window(cur,full_name)
		self.child_windows.append(detail_window)

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

	def is_archive(self,filename):
		filename = str(filename)
		exts = [".zip",".tar",".gz"]
		for ext in exts:
			if filename.find(ext)!=-1:
				return True
		return False

	# redirect the current tab to the home directory
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
				
				if self.is_imagefile(elem):
					new_widget.setIcon(QIcon("resources/pic.png"))
				elif self.is_archive(elem):
					new_widget.setIcon(QIcon("resources/zip.png"))
				elif self.is_textfile(elem):
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
			child.close()

	# loads in all of the saved places from data/saved_places.txt (if exists)
	def load_saved_places(self):
		fname = "data/saved_places.txt"
		orig_len = len(self.saved_places)
		if os.path.isfile(fname):
			f = open(fname,'r')
			data = f.read()
			data = data.split("\n")

			for item in data:
				if item=="":
					continue

				vals = item.split("-->")

				name = vals[0]
				path = vals[1]

				if name == "Home":
					continue

				new_place = saved_place(name,path)
				self.saved_places.append(new_place)
		if len(self.saved_places) != orig_len:
			self.update_navi_display()

	# saves all of the saved places to data/saved_places.txt
	def save_saved_places(self):
		f = open("data/saved_places.txt","w")
		for item in self.saved_places:
			f.write(item.name+"-->"+item.location+"\n")

	# Close all child windows when this one is closed
	def closeEvent(self, event):
		self.collect_garbage()
		self.my_prefs.save()
		self.save_saved_places()
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
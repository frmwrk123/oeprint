#! /usr/bin/env python3
import sys
from shutil import copyfile

from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QMenuBar, QMenu, QBoxLayout
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QMessageBox

from add_configuration_dialog import AddConfigurationDialog
from config import ConfigDialog
from configuration_view import ConfigurationView
from edit_view import EditView
from material_view import MaterialView
from config import Config
from connection import Connection
from ssh_dialog import SSHInput


class Main:
    """Main class of the application"""
    def __init__(self):
        """Initializes the application"""
        self.__application = QApplication(sys.argv)
        self.__application.setApplicationName('OE Printtool Client')
        self.__mainWindow = QMainWindow()
        self.__mainWindow.setWindowTitle('OE Printtool Client')

        # ensures that there is data before continuing
        ssh_input = SSHInput(self.__mainWindow)
        self._connection = Connection(ssh_input)
        self._config = Config()
        try:
            with open(self._config.get("Data", "file"), 'r'):
                pass
        except FileNotFoundError:
            copyfile(self._config.get('Data', 'template_file'), self._config.get('Data', 'file'))
            
        try:
            if not self._config.get('Data', 'initialized_local_data_file'):
                if self._config.get('SSH', 'host') == '':
                    raise RuntimeWarning('SSH host is needed for initial synchronization of data file')
                else:
                    print('Initial synchronization of data file with server-side data file')
                    self._connection.synchronize_data()
                    self._config.set('Data', 'initialized_local_data_file', 'true')
                    self._config.write()
        except RuntimeWarning as rw:
            message, = rw.args
            if message != 'SSH host is needed for initial synchronization of data file':
                raise
            ssh_message_box = QMessageBox()
            ssh_message_box.setText(
                'Please enter the SSH host used for the orientation unit directory in the preferences window '
                '(Edit->Preferences)'
            )
            ssh_message_box.setWindowTitle('SSH Host is missing')
            ssh_message_box.exec()

        # set up main window
        self.__configurationView = None # type: ConfigurationView
        self.__materialView = None # type: MaterialView
        self.__contentPane = self.__create_content_pane()
        self.__menuBar = self.__create_menu_bar()
        self.__mainWindow.setCentralWidget(self.__contentPane)
        self.__mainWindow.setMenuBar(self.__menuBar)
        self.__mainWindow.showMaximized()
        self.__configurationView.select_first_item()
        self.__returnCode = self.__application.exec()

    def return_code(self):
        """Returns the return code"""
        return self.__returnCode

    def __close(self):
        """Closes the application"""
        self.__application.closeAllWindows()

    def __create_content_pane(self):
        """Creates the central content pane"""
        content_pane = QWidget(self.__mainWindow)
        layout = QBoxLayout(QBoxLayout.LeftToRight)
        content_pane.setLayout(layout)
        # add configuration view
        self.__configurationView = ConfigurationView(content_pane)
        layout.addWidget(self.__configurationView)
        # add material view
        self.__materialView = MaterialView()
        layout.addWidget(self.__materialView)
        return content_pane

    def __create_menu_bar(self):
        """Creates the menu bar"""
        # create menus
        menu_bar = QMenuBar()
        # create file menu
        file_menu = QMenu('&File', menu_bar)
        close_action = file_menu.addAction('&Quit')
        close_action.triggered.connect(self.__close)
        close_action.setShortcut(QKeySequence.Quit)

        # edit menu
        edit_menu = QMenu('&Edit', menu_bar)
        config_dialog = ConfigDialog(self.__mainWindow)
        add_config_action = edit_menu.addAction('&Add configuration')
        add_config_action.triggered.connect(self.__add_configuration)
        resync_action = edit_menu.addAction('&Synchronize with server')
        resync_action.triggered.connect(self.__synchronize)
        preferences_action = edit_menu.addAction('&Preferences')
        preferences_action.triggered.connect(config_dialog.show)

        # create help menu
        help_menu = QMenu('&Help', menu_bar)
        about_qt_action = help_menu.addAction('About &Qt')
        about_qt_action.triggered.connect(self.__application.aboutQt)

        menu_bar.addMenu(file_menu)
        menu_bar.addMenu(edit_menu)
        menu_bar.addMenu(help_menu)
        return menu_bar
    
    def __add_configuration(self):
        add_dialog = AddConfigurationDialog()
        result = add_dialog.exec()
        if result == QDialog.Accepted:
            config = add_dialog.get_configuration()
            self.__configurationView.add_configuration(config)
    
    def __synchronize(self):
        self._connection.reload_config()
        self._config = Config()
        self._connection.synchronize_data()
        if not self._config.get('Data', 'initialized_local_data_file'):
            self._config.set('Data', 'initialized_local_data_file', 'true')
            self._config.write()
        self.__configurationView.update_model()
        self.__materialView.update_model()

if __name__ == '__main__':
    main = Main()
    sys.exit(main.return_code())

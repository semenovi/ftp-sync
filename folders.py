import os
import sys
import configparser
from PyQt5.QtWidgets import QInputDialog, QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QListWidget, QMessageBox, QFileDialog, QDialog, QListWidgetItem
from PyQt5.QtCore import Qt
from ftplib import FTP
from datetime import datetime

class FTPSyncApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_config()

    def init_ui(self):
        self.setWindowTitle('FTP Sync')
        self.setGeometry(100, 100, 600, 400)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.layout = QHBoxLayout(self.central_widget)

        self.folder_list = QListWidget()
        self.folder_list.itemClicked.connect(self.select_folder)
        self.layout.addWidget(self.folder_list)

        self.settings_widget = QWidget()
        self.settings_layout = QVBoxLayout(self.settings_widget)
        self.layout.addWidget(self.settings_widget)

        self.local_path_label = QLabel('Local Path:')
        self.local_path_input = QLineEdit()
        self.local_path_button = QPushButton('Browse')
        self.local_path_button.clicked.connect(self.browse_local_path)
        self.local_path_layout = QHBoxLayout()
        self.local_path_layout.addWidget(self.local_path_label)
        self.local_path_layout.addWidget(self.local_path_input)
        self.local_path_layout.addWidget(self.local_path_button)
        self.settings_layout.addLayout(self.local_path_layout)

        self.ftp_path_label = QLabel('FTP Path:')
        self.ftp_path_input = QLineEdit()
        self.ftp_path_button = QPushButton('Browse')
        self.ftp_path_button.clicked.connect(self.browse_ftp_path)
        self.ftp_path_layout = QHBoxLayout()
        self.ftp_path_layout.addWidget(self.ftp_path_label)
        self.ftp_path_layout.addWidget(self.ftp_path_input)
        self.ftp_path_layout.addWidget(self.ftp_path_button)
        self.settings_layout.addLayout(self.ftp_path_layout)

        self.save_button = QPushButton('Save')
        self.save_button.clicked.connect(self.save_config)
        self.delete_button = QPushButton('Delete')
        self.delete_button.clicked.connect(self.delete_folder)
        self.settings_layout.addWidget(self.save_button)
        self.settings_layout.addWidget(self.delete_button)

        self.settings_widget.setDisabled(True)

        self.add_folder_item = QListWidgetItem('Add folder...')
        self.folder_list.addItem(self.add_folder_item)

        self.local_size_label = QLabel()
        self.ftp_size_label = QLabel()
        self.local_modified_label = QLabel()
        self.ftp_modified_label = QLabel()
        self.settings_layout.addWidget(self.local_size_label)
        self.settings_layout.addWidget(self.ftp_size_label)
        self.settings_layout.addWidget(self.local_modified_label)
        self.settings_layout.addWidget(self.ftp_modified_label)

    def load_config(self):
        self.config = configparser.ConfigParser()
        if not os.path.exists('config.ini'):
            self.show_login_dialog()
        else:
            self.config.read('config.ini')

            if self.config.has_option('FTP', 'host'):
                self.ftp_host = self.config.get('FTP', 'host')
            else:
                self.ftp_host = ''

            if self.config.has_option('FTP', 'username'):
                self.ftp_username = self.config.get('FTP', 'username')
            else:
                self.ftp_username = ''

            if self.config.has_option('FTP', 'password'):
                self.ftp_password = self.config.get('FTP', 'password')
            else:
                self.ftp_password = ''

            self.show_login_dialog()

    def show_login_dialog(self):
        self.login_dialog = QWidget()
        self.login_dialog.setWindowTitle('FTP Login')
        self.login_dialog.setGeometry(200, 200, 300, 200)

        layout = QVBoxLayout(self.login_dialog)

        host_label = QLabel('FTP Host:')
        self.host_input = QLineEdit()
        self.host_input.setText(self.ftp_host)
        layout.addWidget(host_label)
        layout.addWidget(self.host_input)

        username_label = QLabel('Username:')
        self.username_input = QLineEdit()
        self.username_input.setText(self.ftp_username)
        layout.addWidget(username_label)
        layout.addWidget(self.username_input)

        password_label = QLabel('Password:')
        self.password_input = QLineEdit()
        self.password_input.setText(self.ftp_password)
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(password_label)
        layout.addWidget(self.password_input)

        self.status_label = QLabel()
        layout.addWidget(self.status_label)

        connect_button = QPushButton('Connect')
        connect_button.clicked.connect(self.connect_ftp)
        layout.addWidget(connect_button)

        self.login_dialog.show()

    def connect_ftp(self):
        self.ftp_host = self.host_input.text()
        self.ftp_username = self.username_input.text()
        self.ftp_password = self.password_input.text()

        try:
            ftp = FTP(self.ftp_host)
            ftp.login(self.ftp_username, self.ftp_password)
            ftp.quit()
            self.status_label.setText('Connected successfully!')

            self.config['FTP'] = {
                'host': self.ftp_host,
                'username': self.ftp_username,
                'password': self.ftp_password
            }
            with open('config.ini', 'w') as config_file:
                self.config.write(config_file)

            self.login_dialog.close()
            self.show()
            self.load_folders()
        except Exception as e:
            self.status_label.setText(f'Connection failed: {str(e)}')

    def update_folder_info(self, local_path, ftp_path):
        local_size = self.get_local_folder_size(local_path)
        ftp_size = self.get_ftp_folder_size(ftp_path)
        local_modified = os.path.getmtime(local_path)
        ftp_modified = self.get_ftp_folder_modified(ftp_path)
        size_symbol = '='
        if local_size > ftp_size:
            size_symbol = '(+)'
            self.local_size_label.setStyleSheet('color: green')
        elif local_size < ftp_size:
            size_symbol = '(-)'
            self.local_size_label.setStyleSheet('color: yellow')
        else:
            self.local_size_label.setStyleSheet('color: black')
        self.local_size_label.setText(f'Local Size: {local_size} bytes {size_symbol}')
        self.ftp_size_label.setText(f'FTP Size: {ftp_size} bytes')
        self.local_modified_label.setText(f'Local Modified: {datetime.fromtimestamp(local_modified)}')
        self.ftp_modified_label.setText(f'FTP Modified: {ftp_modified}')

    def get_ftp_folder_modified(self, ftp_path):
        ftp = FTP(self.ftp_host)
        ftp.login(self.ftp_username, self.ftp_password)
        ftp.cwd(ftp_path)
        timestamp = ftp.voidcmd(f'MDTM {ftp_path}')[4:].strip()
        modified_time = datetime.strptime(timestamp, '%Y%m%d%H%M%S')
        ftp.quit()
        return modified_time

    def load_folders(self):
        if 'Folders' in self.config.sections():
            for folder_name in self.config.options('Folders'):
                local_path = self.config.get('Folders', folder_name)
                ftp_path = self.config.get(folder_name, 'ftp_path')
                self.add_folder_to_list(folder_name, local_path, ftp_path)

    def add_folder_to_list(self, folder_name, local_path, ftp_path):
        local_size = self.get_local_folder_size(local_path)
        ftp_size = self.get_ftp_folder_size(ftp_path)
        item = QListWidgetItem(folder_name)
        if not os.path.exists(local_path) or not self.check_ftp_path(ftp_path):
            item.setForeground(Qt.red)
        else:
            if local_size > ftp_size:
                item.setForeground(Qt.green)
            elif local_size < ftp_size:
                item.setForeground(Qt.yellow)
            else:
                item.setForeground(Qt.black)
        self.folder_list.insertItem(self.folder_list.count() - 1, item)

    def check_ftp_path(self, ftp_path):
        try:
            ftp = FTP(self.ftp_host)
            ftp.login(self.ftp_username, self.ftp_password)
            ftp.cwd(ftp_path)
            ftp.quit()
            return True
        except:
            return False

    def select_folder(self, item):
        if item == self.add_folder_item:
            self.add_folder()
        else:
            self.settings_widget.setDisabled(False)
            self.selected_folder = item.text()
            local_path = self.config.get('Folders', self.selected_folder)
            ftp_path = self.config.get(self.selected_folder, 'ftp_path')
            self.local_path_input.setText(local_path)
            self.ftp_path_input.setText(ftp_path)
            self.update_folder_info(local_path, ftp_path)

    def add_folder(self):
        local_path = QFileDialog.getExistingDirectory(self, 'Select Local Folder')
        if local_path:
            folder_name, ok = QInputDialog.getText(self, 'Folder Name', 'Enter folder name:')
            if ok and folder_name:
                if not self.config.has_section('Folders'):
                    self.config.add_section('Folders')
                self.config['Folders'][folder_name] = local_path
                self.config[folder_name] = {'ftp_path': '/'}
                with open('config.ini', 'w') as config_file:
                    self.config.write(config_file)
                self.add_folder_to_list(folder_name, local_path, '/')

    def browse_local_path(self):
        local_path = QFileDialog.getExistingDirectory(self, 'Select Local Folder')
        if local_path:
            self.local_path_input.setText(local_path)

    def browse_ftp_path(self):
        ftp_path = self.ftp_path_input.text()
        ftp_dialog = FTPBrowserDialog(self.ftp_host, self.ftp_username, self.ftp_password, ftp_path)
        if ftp_dialog.exec_() == QDialog.Accepted:
            self.ftp_path_input.setText(ftp_dialog.selected_path)

    def save_config(self):
        local_path = self.local_path_input.text()
        ftp_path = self.ftp_path_input.text()
        self.config.set('Folders', self.selected_folder, local_path)
        self.config.set(self.selected_folder, 'ftp_path', ftp_path)
        with open('config.ini', 'w') as config_file:
            self.config.write(config_file)
        QMessageBox.information(self, 'Success', 'Configuration saved.')

    def delete_folder(self):
        self.config.remove_option('Folders', self.selected_folder)
        self.config.remove_section(self.selected_folder)
        with open('config.ini', 'w') as config_file:
            self.config.write(config_file)
        self.folder_list.takeItem(self.folder_list.row(self.folder_list.currentItem()))
        self.settings_widget.setDisabled(True)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F5:
            self.check_selected_folder()

    def check_selected_folder(self):
        if self.selected_folder:
            local_path = self.config.get('Folders', self.selected_folder)
            ftp_path = self.config.get(self.selected_folder, 'ftp_path')
            if not os.path.exists(local_path):
                QMessageBox.warning(self, 'Error', f'Local folder "{local_path}" does not exist.')
            if not self.check_ftp_path(ftp_path):
                QMessageBox.warning(self, 'Error', f'FTP folder "{ftp_path}" does not exist.')

    def get_ftp_folder_size(self, ftp_path):
        ftp = FTP(self.ftp_host)
        ftp.login(self.ftp_username, self.ftp_password)
        ftp.cwd(ftp_path)
        size = 0
        for filename, filestats in ftp.mlsd(facts=['size']):
            if filestats['type'] == 'file':
                size += int(filestats['size'])
            elif filestats['type'] == 'dir':
                size += self.get_ftp_folder_size(os.path.join(ftp_path, filename))
        ftp.quit()
        return size
    
    def get_local_folder_size(self, local_path):
        size = 0
        for root, dirs, files in os.walk(local_path):
            for file in files:
                file_path = os.path.join(root, file)
                size += os.path.getsize(file_path)
        return size

class FTPBrowserDialog(QDialog):
    def __init__(self, host, username, password, initial_path):
        super().__init__()
        self.setWindowTitle('FTP Browser')
        self.setGeometry(200, 200, 400, 300)

        self.host = host
        self.username = username
        self.password = password
        self.initial_path = initial_path

        layout = QVBoxLayout(self)

        self.path_label = QLabel(initial_path)
        layout.addWidget(self.path_label)

        self.folder_list = QListWidget()
        self.folder_list.itemDoubleClicked.connect(self.open_folder)
        layout.addWidget(self.folder_list)

        buttons_layout = QHBoxLayout()
        select_button = QPushButton('Select')
        select_button.clicked.connect(self.accept)
        buttons_layout.addWidget(select_button)
        cancel_button = QPushButton('Cancel')
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_button)
        layout.addLayout(buttons_layout)

        self.load_folders()

    def load_folders(self):
        self.folder_list.clear()
        ftp = FTP(self.host)
        ftp.login(self.username, self.password)
        ftp.cwd(self.initial_path)
        ftp.encoding = 'CP1251'
        folders = []
        ftp.dir(folders.append)
        for folder in folders:
            if '<DIR>' in folder:
                folder_name = folder.split()[-1]
                self.folder_list.addItem(folder_name)
        ftp.quit()

    def open_folder(self, item):
        folder_name = item.text()
        self.initial_path = os.path.join(self.initial_path, folder_name)
        self.path_label.setText(self.initial_path)
        self.load_folders()

    @property
    def selected_path(self):
        return self.initial_path

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FTPSyncApp()
    sys.exit(app.exec_())

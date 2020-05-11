#
#  GSC-18128-1, "Core Flight Executive Version 6.7"
#
#  Copyright (c) 2006-2019 United States Government as represented by
#  the Administrator of the National Aeronautics and Space Administration.
#  All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
#!/usr/bin/env python3
#
# UdpCommands.py -- This is a class that creates a simple command dialog and
#                   sends commands using the cmdUtil UDP C program.
#
#                   The commands that can be sent are defined in comma
#                   delimited text files.
#                   This class deals with one set of commands in a file (up
#                   to 20) but multiple subsystems can be represented by
#                   spawning this class multiple times.
#
#                   This class could be duplicated to send over another
#                   interface such as TCP, Cubesat Space Protocol, or Xbee
#                   wireless radio
#
import getopt
import pickle
import shlex
import subprocess
import sys
from pathlib import Path

from PyQt5.QtWidgets import QApplication, QDialog

from GenericCommandDialog import Ui_GenericCommandDialog

ROOTDIR = Path(sys.argv[0]).resolve().parent


class SubsystemCommands(QDialog, Ui_GenericCommandDialog):

    # pktCount = 0

    #
    # Init the class
    #
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle(pageTitle)

        for j in range(25):
            btn = getattr(self, f"SendButton_{j+1}")
            btn.clicked.connect(
                lambda _, x=j: self.ProcessSendButtonGeneric(x))

    #
    # Determines if command requires parameters
    #
    @staticmethod
    def checkParams(idx):
        pf = f'{ROOTDIR}/ParameterFiles/{param_files[idx]}'
        try:
            with open(pf, 'rb') as po:
                _, paramNames, _, _, _, _ = pickle.load(po)
            return len(paramNames) > 0  # if has parameters
        except IOError:
            return False

    #
    # Generic button press method
    #
    def ProcessSendButtonGeneric(self, idx):
        if cmdItemIsValid[idx]:
            param_bool = self.checkParams(idx)
            address = self.commandAddressLineEdit.text()

            # If parameters are required, launches Parameters page
            if param_bool:
                launch_string = (
                    f'python3 {ROOTDIR}/Parameter.py --title=\"{pageTitle}\" '
                    f'--descrip=\"{cmdDesc[idx]}\" --idx={idx} '
                    f'--host=\"{address}\" --port={pagePort} '
                    f'--pktid={pagePktId} --endian={pageEndian} '
                    f'--cmdcode={cmdCodes[idx]} --file={param_files[idx]}')

            # If parameters not required, directly calls cmdUtil to send command
            else:
                launch_string = (
                    f'{ROOTDIR}/../cmdUtil/cmdUtil --host=\"{address}\" '
                    f'--port={pagePort} --pktid={pagePktId} '
                    f'--endian={pageEndian} --cmdcode={cmdCodes[idx]}')

            cmd_args = shlex.split(launch_string)
            subprocess.Popen(cmd_args)


#
# Display usage
#
def usage():
    print((
        "Must specify --title=<page name> --file=<cmd_def_file> "
        "--pktid=<packet_app_id(hex)> --endian=<LE|BE> --address=<IP address> "
        "--port=<UDP port>\n\nexample: --title=\"Executive Services\" "
        "--file=cfe-es-cmds.txt --pktid=1806 --endian=LE --address=127.0.0.1 "
        "--port=1234"))


#
# Main
#
if __name__ == '__main__':

    #
    # Set defaults for the arguments
    #
    pageTitle = "Command Page"
    pagePort = 1234
    pageAddress = "127.0.0.1"
    pagePktId = 1801
    pageEndian = "LE"
    pageDefFile = "cfe__es__msg_8h"

    #
    # process cmd line args
    #
    try:
        opts, args = getopt.getopt(sys.argv[1:], "htpfeap", [
            "help", "title=", "pktid=", "file=", "endian=", "address=", "port="
        ])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-t", "--title"):
            pageTitle = arg
        elif opt in ("-f", "--file"):
            pageDefFile = arg
        elif opt in ("-p", "--pktid"):
            pagePktId = arg
        elif opt in ("-e", "--endian"):
            pageEndian = arg
        elif opt in ("-a", "--address"):
            pageAddress = arg
        elif opt in ("-p", "--port"):
            pagePort = arg

    #
    # Init the QT application and the command class
    #
    app = QApplication(sys.argv)
    Commands = SubsystemCommands()
    Commands.subSystemLineEdit.setText(pageTitle)
    Commands.packetId.display(pagePktId)
    Commands.commandAddressLineEdit.setText(pageAddress)

    #
    # Reads commands from command definition file
    #
    pickle_file = f'{ROOTDIR}/CommandFiles/{pageDefFile}'
    with open(pickle_file, 'rb') as pickle_obj:
        cmdDesc, cmdCodes, param_files = pickle.load(pickle_obj)

    cmdItemIsValid = []
    for i in range(len(cmdDesc)):
        cmdItemIsValid.append(True)
    for i in range(len(cmdDesc), 26):
        cmdItemIsValid.append(False)

    #
    # Fill the data fields on the page
    #
    for i in range(25):
        itemLabelTextBrowser = getattr(Commands, f"itemLabelTextBrowser_{i+1}")
        if cmdItemIsValid[i]:
            itemLabelTextBrowser.setText(cmdDesc[i])
        else:
            itemLabelTextBrowser.setText("(unused)")

    #
    # Display the page
    #
    Commands.show()
    Commands.raise_()
    sys.exit(app.exec_())

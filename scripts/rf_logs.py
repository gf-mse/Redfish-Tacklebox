#! /usr/bin/python
# Copyright Notice:
# Copyright 2019-2020 DMTF. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tacklebox/blob/main/LICENSE.md

"""
Redfish Logs

File : rf_logs.py

Brief : This script uses the redfish_utilities module to manage logs
"""

import argparse
import datetime
import logging
import redfish
import redfish_utilities
import traceback
import sys
from redfish.messages import RedfishPasswordChangeRequiredError

# Get the input arguments
argget = argparse.ArgumentParser( description = "A tool to manage logs on a Redfish service" )
argget.add_argument( "--user", "-u", type = str, required = True, help = "The user name for authentication" )
argget.add_argument( "--password", "-p",  type = str, required = True, help = "The password for authentication" )
argget.add_argument( "--rhost", "-r", type = str, required = True, help = "The address of the Redfish service (with scheme)" )
argget.add_argument( "--manager", "-m", type = str, nargs = "?", default = False, help = "The ID of the manager containing the log service" )
argget.add_argument( "--system", "-s", type = str, nargs = "?", default = False, help = "The ID of the system containing the log service" )
argget.add_argument( "--chassis", "-c", type = str, nargs = "?", default = False, help = "The ID of the chassis containing the log service" )
argget.add_argument( "--log", "-l", type = str, help = "The ID of the resource containing the log service" )
argget.add_argument( "--details", "-details", action = "store_true", help = "Indicates details to be shown for each log entry" )
argget.add_argument( "--clear", "-clear", action = "store_true", help = "Indicates if the log should be cleared" )
argget.add_argument( "--debug", action = "store_true", help = "Creates debug file showing HTTP traces and exceptions" )
args = argget.parse_args()

# Determine the target log service based on the inputs
# Effectively if the user gives multiple targets, some will be ignored
container_type = redfish_utilities.log_container.MANAGER
container_id = None
if args.manager != False:
    container_type = redfish_utilities.log_container.MANAGER
    container_id = args.manager
elif args.system != False:
    container_type = redfish_utilities.log_container.SYSTEM
    container_id = args.system
elif args.chassis != False:
    container_type = redfish_utilities.log_container.CHASSIS
    container_id = args.chassis

if args.debug:
    log_file = "rf_logs-{}.log".format( datetime.datetime.now().strftime( "%Y-%m-%d-%H%M%S" ) )
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logger = redfish.redfish_logger( log_file, log_format, logging.DEBUG )
    logger.info( "rf_logs Trace" )

# Set up the Redfish object
try:
    redfish_obj = redfish.redfish_client( base_url = args.rhost, username = args.user, password = args.password , timeout=5, max_retry=3)
    redfish_obj.login( auth = "session" )
except RedfishPasswordChangeRequiredError as e:
    print("Password change required\n run rf_accounts.py -r {} -u {} -p <old password> --setpassword {} <new password> \nto set your password\n".format(args.rhost ,args.user, args.user))
    try:
        redfish_obj.logout()
    except Exception as e:
        pass
    sys.exit(1)
except Exception as e:
    # other error
    error_string = str(e)
    if len(error_string) > 0:
        print("{}\nLogin Failed\n".format(error_string))
    else:
        print("Login Failed\n")
    try:
        redfish_obj.logout()
    except Exception as e:
        pass
    sys.exit(1)

try:
    redfish_obj
except Exception as e:
    print("Login Failed\n")
    sys.exit(1)

exit_code = 0
try:
    # Either clear the logs or get/print the logs
    if args.clear:
        # Clear log was requested
        print( "Clearing the log..." )
        response = redfish_utilities.clear_log_entries( redfish_obj, container_type, container_id, args.log )
        response = redfish_utilities.poll_task_monitor( redfish_obj, response )
        redfish_utilities.verify_response( response )
    else:
        # Print log was requested
        log_entries = redfish_utilities.get_log_entries( redfish_obj, container_type, container_id, args.log )
        redfish_utilities.print_log_entries( log_entries, args.details )
except Exception as e:
    if args.debug:
        logger.error( "Caught exception:\n\n{}\n".format( traceback.format_exc() ) )
    exit_code = 1
    print( e )
finally:
    # Log out
    try:
        redfish_obj.logout()
    except Exception as e:
        pass
sys.exit( exit_code )

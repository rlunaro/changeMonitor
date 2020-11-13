'''
Created on Nov 7, 2020

@author: rluna
'''
import os 
import os.path 
import sys
import logging.config
import getopt
import yaml
import json
import datetime
import sqlite3
import re 
import hashlib 

from gmail import Gmail

EXIT_OK = 0 
EXIT_ERR_1 = 1

altered_files = []


def parseArguments( argumentList : list ):
    unixArgs = ""
    gnuArgs = ["help", "config=", "logging=", "reload"]
    # default values
    config_file = 'config.yaml'
    logging_file = 'logging.json'
    reload = False
    try : 
        args, values = getopt.getopt( argumentList, 
                                      unixArgs, 
                                      gnuArgs )
        for currentArgument, currentValue in args: 
            if currentArgument == "--help" : 
                print('''changeMonitor: monitor the changes of files in a directory tree 
Usage: changeMonitor  [options] directory

--help         : show this message and ends 
--logging=file : read logging configuration from file 
--config=file  : read configuration from file 
--reload       : refresh the md5sum of the files to be monitorized
''')
                sys.exit( EXIT_ERR_1 ) 
            if currentArgument == "--config" : 
                config_file = currentValue
            if currentArgument == "--logging" :
                logging_file = currentValue
            if currentArgument == "--reload" : 
                reload = True
    except getopt.error as err:
        print( str(err) )
        sys.exit(2)
    return (config_file, logging_file, reload)

def setupLogger( logging_file : str ):
    with open( logging_file, 'rt', encoding='utf-8') as log_file_json: 
        loggingConfig = json.load( log_file_json )
    logging.config.dictConfig( loggingConfig )
    
def read_config( filepath : str ) :
    with open( filepath, encoding = 'utf-8' ) as config_file : 
        data = yaml.safe_load( config_file ) 
    return data


def send_email( _from, 
                _to, 
                subject, 
                body, 
                file_list: list ):
    gmail = Gmail()
    gmail.loadOrValidateCredentials()
    gmail.sendSimpleEmail(_from, 
                          _to, 
                          replace_variables( subject, file_list ), 
                          replace_variables( body, file_list ) )

def replace_variables( inputString, file_list ):
    outputString = inputString 
    outputString = outputString.replace( "#numberFiles", str(len(file_list)) )
    if "#file_list" in outputString : 
        outputString = outputString.replace( "#file_list", file_list_as_html(file_list) )
    return outputString

def file_list_as_html( file_list : list ):
    outString = ""
    for file in file_list : 
        outString = outString + file + '\n'
    return f'\n\n{outString}\n\n'

def traverse_paths( conn : sqlite3.Connection, 
                    paths_to_monitor : list, operation ):
    for location in paths_to_monitor:
        traverse_path( conn, location, operation )

def traverse_path( conn: sqlite3.Connection, 
                   locationInfo, operation ):
    for root, directories, files in os.walk( locationInfo['path'] ): 
        for file in files:
            if there_is_a_match( file, locationInfo['file_patterns'] ) :
                completePath = os.path.join( root, file )
                operation( conn, completePath )

def detect_deletions( conn: sqlite3.Connection, 
                   paths_to_monitor, operation ):
    global altered_files
    for location in paths_to_monitor: 
        complete_path_list = get_all_paths( conn, location['path'] )
        for path_info in complete_path_list : 
            complete_path = path_info[1]
            if not os.path.isfile( complete_path ):
                altered_files.append( "DELETED> " + complete_path )


def there_is_a_match( file : str, file_patterns : list ):
    match = False 
    for file_pattern in file_patterns : 
        if re.match( file_pattern, file ) : 
            match = True
            break
    return match 

def store_path_md5_sum( conn: sqlite3.Connection,
                        complete_path : str ):
    global altered_files
    md5_value = compute_md5( complete_path )
    if not file_exists(conn, complete_path ) : 
        insert_file( conn, complete_path, md5_value )
    else: 
        update_file( conn, complete_path, md5_value )
    altered_files.append( f"{complete_path}|{md5_value}" )

def compare_path( conn: sqlite3.Connection,
                  complete_path : str ):
    global altered_files
    computed_md5 = compute_md5( complete_path )
    stored_md5 = get_stored_md5( conn, complete_path ) 
    if computed_md5 != stored_md5 : 
        altered_files.append( complete_path )

def compute_md5( complete_path ): 
    hash_md5 = hashlib.md5()
    with open(complete_path, "rb") as file:
        for chunk in iter(lambda: file.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def get_all_paths( conn: sqlite3.Connection, path ):
    cur = conn.cursor()
    cur.execute('''select * 
    from file_list 
    where path like :path''',
    {'path' : path + '%' })
    return cur
    
def insert_file( conn: sqlite3.Connection, 
                complete_path : str, 
                md5_value :str ):
    cur = conn.cursor()
    cur.execute('''insert into file_list (path, md5sum) values (:path, :md5sum)''', 
                {'path': complete_path,
                 'md5sum': md5_value} )

def update_file( conn: sqlite3.Connection, 
                 complete_path : str, 
                 md5_value : str ):
    cur = conn.cursor()
    cur.execute('''update file_list set md5sum = :md5sum 
                where path = :path''', 
                {'md5sum': md5_value, 
                 'path': complete_path } )

def get_stored_md5( conn: sqlite3.Connection, 
                    path : str ):
    cur = conn.cursor()
    cur.execute('''select md5sum 
    from file_list 
    where path = :path''', 
    {'path': path } )
    result = cur.fetchone()
    if result : 
        return result[0]
    else : 
        return ""

def file_exists( conn: sqlite3.Connection, 
                      path : str ):
    cur = conn.cursor()
    cur.execute('''select count(*) total 
        from file_list
        where path = :path''', 
        {'path' : path } )
    return cur.fetchone()[0] != 0 


if __name__ == '__main__' : 
    (config_file, 
    logging_file, 
    reload) = parseArguments( sys.argv[1:] )
    setupLogger( logging_file )
    config = read_config( config_file )

    logging.warning(f"changeMonitor started at {datetime.datetime.now()}")

    with sqlite3.connect(config['database']) as conn : 
        altered_files = []
        if reload : 
            traverse_paths( conn, config['paths_to_monitor'], store_path_md5_sum )
            send_email( config['email_from'], 
                        config['email_to'], 
                        config['subject_reload'], 
                        config['body_reload'], 
                        altered_files )
        else:
            traverse_paths( conn, config['paths_to_monitor'], compare_path )
            detect_deletions( conn, config['paths_to_monitor'], compare_path )
            if len(altered_files) == 0 :
                print("everything is ok")
                send_email( config['email_from'], 
                            config['email_to'], 
                            config['subject_ok'], 
                            config['body_ok'], 
                            [] )
            else: 
                print('some files were altered:')
                print(altered_files)
                send_email( config['email_from'], 
                            config['email_to'], 
                            config['subject_fail'], 
                            config['body_fail'], 
                            altered_files )
        
    logging.warning(f"changeMonitor finished at {datetime.datetime.now()}")
    



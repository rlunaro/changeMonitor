'''
Created on Nov 7, 2020

@author: rluna
'''
import os 
import os.path 
import sys
import logging.config
import getopt
import json
import datetime
import re 
import hashlib

import yaml
import sqlite3


from pathspec.patterns import GitWildMatchPattern
from pathspec import PathSpec

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

def delete_paths_to_monitor( conn : sqlite3.Connection ):
    cur = conn.cursor()
    cur.execute('delete from file_list')

def traverse_paths( conn : sqlite3.Connection, 
                    paths_to_monitor : dict, 
                    operation ):
    result = []
    for (path, path_info) in paths_to_monitor.items():
        result.extend( traverse_path( conn, 
                       path, 
                       path_info, 
                       operation ) )
    return result

def traverse_path( conn: sqlite3.Connection, 
                   path : str, 
                   path_info : PathSpec, 
                   operation ):
    result = []
    for root, directories, files in os.walk( path ):
        if not directory_matches( root, path_info['directories_ignored'] ):
            matched_files = list(path_info['files'].match_files( files ))
            for file in matched_files:
                completePath = os.path.join( root, file )
                result.append( operation( conn, completePath ) )
    return result 


def directory_matches( directory: str, 
                       directories_to_check: list ):
    for dir_to_check in directories_to_check:
        if re.match( f'.*{dir_to_check}', directory ): 
            return True
    return False

def detect_deletions( conn: sqlite3.Connection, 
                   paths_to_monitor, 
                   operation ):
    result = []
    for (path, path_info) in paths_to_monitor.items(): 
        complete_path_list = get_all_paths( conn, path )
        for (_, file_path, md5_sum) in complete_path_list : 
            if not os.path.isfile( file_path ):
                result.append( { "path" : file_path, 
                                 "md5_value": md5_sum, 
                                 "deleted" : True } )
    return result



def store_path_md5_sum( conn: sqlite3.Connection,
                        complete_path : str ):
    md5_value = compute_md5( complete_path )
    if not file_exists(conn, complete_path ) : 
        insert_file( conn, complete_path, md5_value )
    else: 
        update_file( conn, complete_path, md5_value )
    return { "path": complete_path,
             "md5_value": md5_value }

def compare_path( conn: sqlite3.Connection,
                  complete_path : str ):
    computed_md5 = compute_md5( complete_path )
    stored_md5 = get_stored_md5( conn, complete_path )
    return { "path": complete_path, 
             "md5_value": computed_md5, 
             "changed": computed_md5 != stored_md5, 
             "is_new" : stored_md5 == "" }

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


def configure_pathspec_info( paths_to_monitor : dict ):
    for (path, path_info) in paths_to_monitor.items():
        if 'files' in path_info:
            paths_to_monitor[path]['files'] = PathSpec( map( GitWildMatchPattern, path_info['files']))
        else: 
            # if no element is provided, a generic specification will be provided
            paths_to_monitor[path]['files'] = PathSpec( map( GitWildMatchPattern, ['*'] ))
        if not 'directories_ignored' in path_info:
            paths_to_monitor[path]['directories_ignored'] = []


def get_altered_files( file_list : list ):
    result = []
    for item in file_list : 
        if item.get('changed') : 
            result.append( item )
        if item.get('deleted'): 
            result.append( item )
    return result 

if __name__ == '__main__' : 
    (config_file, 
    logging_file, 
    reload) = parseArguments( sys.argv[1:] )
    setupLogger( logging_file )
    config = read_config( config_file )

    logging.warning(f"changeMonitor started at {datetime.datetime.now()}")

    configure_pathspec_info( config['paths_to_monitor'] )        
            
    with sqlite3.connect(config['database'], isolation_level = None ) as conn : 
        if reload :
            delete_paths_to_monitor( conn )
            file_list = traverse_paths( conn, 
                                        config['paths_to_monitor'], 
                                        store_path_md5_sum )
            send_email( config['email']['from'], 
                        config['email']['to'], 
                        config['email']['reload']['subject'], 
                        config['email']['reload']['body'], 
                        file_list )
        else:
            file_list = traverse_paths( conn, 
                                        config['paths_to_monitor'], 
                                        compare_path )
            file_list.extend( detect_deletions( conn, 
                                      config['paths_to_monitor'], 
                                      compare_path ) )
            altered_files = get_altered_files( file_list )
            if len(altered_files) == 0 :
                print("everything is ok")
                send_email( config['email']['from'], 
                            config['email']['to'], 
                            config['email']['ok']['subject'], 
                            config['email']['ok']['body'], 
                            [] )
            else: 
                print('some files were altered:')
                print(altered_files)
                send_email( config['email']['from'], 
                            config['email']['to'], 
                            config['email']['fail']['subject'], 
                            config['email']['fail']['body'], 
                            altered_files )
        
    logging.warning(f"changeMonitor finished at {datetime.datetime.now()}")
    



#
# create_database.sql 
#


create table file_list
(
id_file integer primary key autoincrement,
path        text, 
md5sum      text
);



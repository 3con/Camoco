#!/usr/bin/python
from __future__ import print_function,division
import apsw as lite
import os as os
import time as time
import sys
import tempfile

class Camoco(object):
    def __init__(self,name,description=None,type='Camoco',basedir="~/.camoco"):
        # Set up our base directory
        self.basedir = os.path.realpath(os.path.expanduser(basedir))
        if not os.path.exists(self.basedir):
            # If it doesn't exists, set up first time directories
            try:    
                os.mkdir(self.basedir)
                os.mkdir(os.path.join(self.basedir,"logs"))
                os.mkdir(os.path.join(self.basedir,"databases"))
                os.mkdir(os.path.join(self.basedir,"analyses"))
                os.mkdir(os.path.join(self.basedir,"tmp"))
            except Exception as e:
                print("[CAMOCO]",time.ctime(), '-', *args,file=sys.stderr)
        self.log_file = open(os.path.join(self.basedir,"logs","logfile.txt"),'w')
        if description is not None:
            self.database('camoco').cursor().execute('''
                INSERT OR IGNORE INTO datasets (name,description,type)
                VALUES (?,?,?)''',(name,description,type))
            # create new sqlite file for dataset
        try:
            self.db = self.database(".".join([type,name]))
            (self.ID,self.name,self.description,
            self.type,self.added) = self.database('camoco').cursor().execute(
                "SELECT rowid,* FROM datasets WHERE name = ? AND type = ?",
                (name,type)
            ).fetchone()
            self.db.cursor().execute('''
                CREATE TABLE IF NOT EXISTS globals (
                    key TEXT,
                    val TEXT
                );
                CREATE UNIQUE INDEX IF NOT EXISTS uniqkey ON globals(key)
                ''')
        except Exception as e:
            self.log("Camoco Dataset does not exist, create one using the Builder Class")
            self.log("Error: {}",e)

    def log(self,msg,*args):
        print("[CAMOCO]",time.ctime(), '-', msg.format(*args),file=sys.stderr)
        print("[CAMOCO]",time.ctime(), '-', msg.format(*args),file=self.log_file)
           
    def _resource(self,type,filename):
        return os.path.expanduser(os.path.join(self.basedir,type,filename))

    def database(self,dbname):
        # return a connection if exists
        return lite.Connection(self._resource("databases",str(dbname)+".db"))

    def tmp_file(self):
        # returns a handle to a tmp file
        return tempfile.NamedTemporaryFile(dir=os.path.join(self.basedir,"tmp"))

    def available_datasets(self):
        cur=self.database("camoco").cursor()
        return cur.execute("SELECT type,name,description,added FROM datasets ORDER BY type;").fetchall()

    def del_dataset(self):
        con = self.database('camoco').cursor()
        con.execute(''' DELETE FROM datasets WHERE name = '{}' and type = '{}';'''.format(self.name,self.type))
        os.remove(self._resource("databases",".".join([self.type,self.name])+".db"))

    def _global(self,key,val=None):
        # set the global for the dataset
        if val is not None:
            self.db.cursor().execute('''
                INSERT OR REPLACE INTO globals (key,val)VALUES (?,?)''',(key,val)
            )
        else:
            try:
                return self.db.cursor().execute(
                    '''SELECT val FROM globals WHERE key = ?''',(key,)
                ).fetchone()[0]
            except Exception as e:
                return None
            
    def _create_tables(self):
        camocodb = self.database("camoco")
        camocodb.execute(''' 
            CREATE TABLE IF NOT EXISTS datasets (
                name TEXT NOT NULL,
                description TEXT,
                type TEXT,
                added datetime DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(name,type)
            )
        ''')

    def __getattr__(self,name):
        return self._global(name)


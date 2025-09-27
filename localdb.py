import sqlite3
import os
from PyQt6 import QtCore as qtc
#Made by dumxrg

class LocalDB:
    def __init__(self, db_name="calendar_events.db"):
 
        self.db_name = db_name
        self.init_database()
    
    def init_database(self):
      
      
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    title TEXT NOT NULL,
                    category TEXT NOT NULL,
                    time TEXT,
                    detail TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
    
    def save_event(self, date, event_data):
       
       
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            time_str = None
            if event_data['time'] is not None:
                time_str = event_data['time'].toString('hh:mm')
            
            cursor.execute('''
                INSERT INTO events (date, title, category, time, detail)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                date.toString('yyyy-MM-dd'),
                event_data['title'],
                event_data['category'],
                time_str,
                event_data['detail']
            ))
            conn.commit()
            return cursor.lastrowid
    
    def update_event(self, event_id, date, event_data):
        
        
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            time_str = None
            if event_data['time'] is not None:
                time_str = event_data['time'].toString('hh:mm')
            
            cursor.execute('''
                UPDATE events 
                SET date=?, title=?, category=?, time=?, detail=?
                WHERE id=?
            ''', (
                date.toString('yyyy-MM-dd'),
                event_data['title'],
                event_data['category'],
                time_str,
                event_data['detail'],
                event_id
            ))
            conn.commit()
    
    def delete_event(self, event_id):
       
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM events WHERE id=?', (event_id,))
            conn.commit()
    
    def get_events_for_date(self, date):
       
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, title, category, time, detail
                FROM events 
                WHERE date=?
                ORDER BY CASE WHEN time IS NULL THEN '00:00' ELSE time END
            ''', (date.toString('yyyy-MM-dd'),))
            
            events = []
            for row in cursor.fetchall():
                event_id, title, category, time_str, detail = row
                time_obj = None
                if time_str:
                    time_obj = qtc.QTime.fromString(time_str, 'hh:mm')
                
                events.append({
                    'id': event_id,
                    'title': title,
                    'category': category,
                    'time': time_obj,
                    'detail': detail
                })
            
            return events
    
    def get_all_events(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT date, id, title, category, time, detail
                FROM events 
                ORDER BY date, CASE WHEN time IS NULL THEN '00:00' ELSE time END
            ''')
            
            events_dict = {}
            for row in cursor.fetchall():
                date_str, event_id, title, category, time_str, detail = row
                date_obj = qtc.QDate.fromString(date_str, 'yyyy-MM-dd')
                
                time_obj = None
                if time_str:
                    time_obj = qtc.QTime.fromString(time_str, 'hh:mm')
                
                event = {
                    'id': event_id,
                    'title': title,
                    'category': category,
                    'time': time_obj,
                    'detail': detail
                }
                
                if date_obj not in events_dict:
                    events_dict[date_obj] = []
                events_dict[date_obj].append(event)
            
            return events_dict
    
    def close(self):
        
        pass
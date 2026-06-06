import sqlite3
import os
import json
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.logger import logger

DB_PATH = "database/queue.db"

class QueueManager:
    def __init__(self):
        """Initializes the SQLite queue database to prevent content loss across sessions."""
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        # check_same_thread=False allows sharing connection between threads if needed, 
        # though standard sqlite3 handles concurrent reads well, writes need care.
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()

    def _init_tables(self):
        """Creates the 4 distinct queue tables if they don't exist."""
        queues = ["story_queue", "video_queue", "upload_queue", "schedule_queue"]
        cursor = self.conn.cursor()
        for q in queues:
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS {q} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    payload TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    attempts INTEGER DEFAULT 0
                )
            ''')
        self.conn.commit()
        logger.info("Queue tables initialized successfully.")

    def push(self, queue_name, payload):
        """Pushes a new item (dict) to the specified queue."""
        try:
            cursor = self.conn.cursor()
            payload_str = json.dumps(payload)
            cursor.execute(f"INSERT INTO {queue_name} (payload) VALUES (?)", (payload_str,))
            self.conn.commit()
            logger.info(f"Pushed task {cursor.lastrowid} to {queue_name}")
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error pushing to {queue_name}: {e}")
            return None

    def pop(self, queue_name):
        """
        Retrieves the oldest pending item from the queue, marks it as 'processing',
        and increments the attempt counter.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(f'''
                SELECT * FROM {queue_name} 
                WHERE status = 'pending' 
                ORDER BY id ASC LIMIT 1
            ''')
            row = cursor.fetchone()
            
            if row:
                item_id = row['id']
                attempts = row['attempts'] + 1
                cursor.execute(f"UPDATE {queue_name} SET status = 'processing', attempts = ? WHERE id = ?", (attempts, item_id))
                self.conn.commit()
                
                result = dict(row)
                result['payload'] = json.loads(result['payload'])
                return result
            return None
        except Exception as e:
            logger.error(f"Error popping from {queue_name}: {e}")
            return None

    def mark_completed(self, queue_name, item_id):
        """Marks an item as successfully completed so it isn't processed again."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(f"UPDATE {queue_name} SET status = 'completed' WHERE id = ?", (item_id,))
            self.conn.commit()
            logger.info(f"Marked task {item_id} in {queue_name} as completed.")
        except Exception as e:
            logger.error(f"Error marking completed in {queue_name}: {e}")

    def requeue(self, queue_name, item_id, max_attempts=3):
        """Requeues a failed item if it hasn't exceeded max_attempts, otherwise marks it as 'failed'."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(f"SELECT attempts FROM {queue_name} WHERE id = ?", (item_id,))
            row = cursor.fetchone()
            if row:
                if row['attempts'] < max_attempts:
                    cursor.execute(f"UPDATE {queue_name} SET status = 'pending' WHERE id = ?", (item_id,))
                    self.conn.commit()
                    logger.info(f"Requeued task {item_id} in {queue_name}. (Attempt {row['attempts']} of {max_attempts})")
                else:
                    cursor.execute(f"UPDATE {queue_name} SET status = 'failed' WHERE id = ?", (item_id,))
                    self.conn.commit()
                    logger.error(f"Task {item_id} in {queue_name} reached max attempts ({max_attempts}). Marked as failed.")
        except Exception as e:
            logger.error(f"Error requeuing in {queue_name}: {e}")

    def get_queue_size(self, queue_name):
        """Returns the number of pending items in the queue."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {queue_name} WHERE status = 'pending'")
            return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error getting queue size for {queue_name}: {e}")
            return 0

if __name__ == "__main__":
    if sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
        
    print("Testing Queue Management System...")
    qm = QueueManager()
    
    # 1. Test Push
    test_payload = {"story": "Sample story", "script": "Hello world!"}
    item_id = qm.push("story_queue", test_payload)
    print(f"✅ Pushed item {item_id} to story_queue")
    
    # 2. Test Size
    size = qm.get_queue_size("story_queue")
    print(f"✅ Pending in story_queue: {size}")
    
    # 3. Test Pop
    item = qm.pop("story_queue")
    print(f"✅ Popped item ID {item['id']} (Attempt {item['attempts']})")
    
    # 4. Test Requeue
    qm.requeue("story_queue", item['id'])
    print(f"✅ Requeued item ID {item['id']}")
    
    # 5. Pop again to simulate next run
    item_retry = qm.pop("story_queue")
    print(f"✅ Popped item ID {item_retry['id']} again (Attempt {item_retry['attempts']})")
    
    # 6. Test Completion
    qm.mark_completed("story_queue", item_retry['id'])
    print(f"✅ Marked item {item_retry['id']} as completed.")
    
    final_size = qm.get_queue_size("story_queue")
    print(f"✅ Final pending in story_queue: {final_size}")

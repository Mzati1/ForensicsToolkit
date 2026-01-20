#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
WhatsApp Database Parser Module

Parses WhatsApp SQLite databases to extract chats, messages, contacts, and call logs.
"""

import sqlite3
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class Contact:
    """Represents a WhatsApp contact"""
    jid: str
    display_name: Optional[str] = None
    phone_number: Optional[str] = None
    
    def __post_init__(self):
        """Extract phone number from JID if not provided"""
        if self.phone_number is None and self.jid:
            # JID format: phone_number@s.whatsapp.net
            self.phone_number = self.jid.split("@")[0] if "@" in self.jid else self.jid


@dataclass
class Message:
    """Represents a WhatsApp message"""
    message_id: int
    chat_jid: str
    timestamp: int
    from_me: bool
    message_text: Optional[str] = None
    media_type: Optional[int] = None
    media_path: Optional[str] = None
    media_caption: Optional[str] = None
    quoted_message_id: Optional[int] = None
    remote_resource: Optional[str] = None
    status: Optional[int] = None
    
    def get_datetime(self) -> datetime:
        """Convert timestamp to datetime"""
        return datetime.fromtimestamp(self.timestamp / 1000)


@dataclass
class Chat:
    """Represents a WhatsApp chat"""
    jid: str
    display_name: Optional[str] = None
    last_message_timestamp: Optional[int] = None
    message_count: int = 0
    participants: List[str] = field(default_factory=list)
    is_group: bool = False
    messages: List[Message] = field(default_factory=list)
    
    def get_last_message_datetime(self) -> Optional[datetime]:
        """Convert last message timestamp to datetime"""
        if self.last_message_timestamp:
            return datetime.fromtimestamp(self.last_message_timestamp / 1000)
        return None


@dataclass
class CallLog:
    """Represents a WhatsApp call log entry"""
    call_id: int
    jid: str
    timestamp: int
    from_me: bool
    duration: int
    video_call: bool
    call_result: Optional[int] = None
    
    def get_datetime(self) -> datetime:
        """Convert timestamp to datetime"""
        return datetime.fromtimestamp(self.timestamp / 1000)


class WhatsAppParser:
    """
    Parser for WhatsApp SQLite databases.
    
    Extracts chats, messages, contacts, and call logs from msgstore.db and wa.db.
    """
    
    def __init__(self, msgstore_db: str, wa_db: Optional[str] = None):
        """
        Initialize parser with database paths.
        
        Args:
            msgstore_db: Path to msgstore.db (main message database)
            wa_db: Optional path to wa.db (contacts database)
        """
        self.msgstore_db = Path(msgstore_db)
        if not self.msgstore_db.exists():
            raise FileNotFoundError(f"msgstore.db not found: {msgstore_db}")
        
        self.wa_db = Path(wa_db) if wa_db and Path(wa_db).exists() else None
        self.contacts_cache: Dict[str, str] = {}
        
        # Load contacts if wa.db is available
        if self.wa_db:
            self._load_contacts()
    
    def _load_contacts(self):
        """Load contacts from wa.db"""
        try:
            conn = sqlite3.connect(self.wa_db)
            cursor = conn.cursor()
            
            # Try different possible table names
            tables_to_try = [
                "wa_contacts",
                "contacts",
                "user"
            ]
            
            for table in tables_to_try:
                try:
                    query = f"SELECT jid, display_name FROM {table}"
                    cursor.execute(query)
                    for jid, display_name in cursor.fetchall():
                        if jid:
                            self.contacts_cache[jid] = display_name or ""
                    logger.info(f"Loaded {len(self.contacts_cache)} contacts from {table}")
                    break
                except sqlite3.OperationalError:
                    continue
            
            conn.close()
        except Exception as e:
            logger.warning(f"Could not load contacts from wa.db: {e}")
    
    def _get_contact_name(self, jid: str) -> Optional[str]:
        """Get display name for a JID"""
        return self.contacts_cache.get(jid)
    
    def get_chats(self) -> List[Chat]:
        """
        Extract all chats from the database.
        
        Returns:
            List of Chat objects
        """
        chats = []
        
        try:
            conn = sqlite3.connect(self.msgstore_db)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Query for chats - try different possible schemas (simpler ones first)
            queries = [
                # Simple test schema (most basic)
                """
                SELECT 
                    jid.raw_string as jid,
                    chat.subject as display_name,
                    (SELECT COUNT(*) FROM message WHERE message.key_remote_jid = jid.raw_string) as message_count
                FROM chat
                JOIN jid ON chat.jid_row_id = jid._id
                ORDER BY chat._id DESC
                """,
                # Modern schema
                """
                SELECT 
                    jid.raw_string as jid,
                    chat.subject as display_name,
                    chat.last_message_row_id,
                    chat.last_message_table_row_id,
                    chat.last_read_message_table_row_id,
                    (SELECT COUNT(*) FROM message WHERE message.key_remote_jid = jid.raw_string) as message_count
                FROM chat
                JOIN jid ON chat.jid_row_id = jid._id
                ORDER BY chat.last_message_table_row_id DESC
                """,
                # Older schema
                """
                SELECT 
                    jid as jid,
                    subject as display_name,
                    last_message_time as last_message_timestamp,
                    (SELECT COUNT(*) FROM messages WHERE key_remote_jid = chat.jid) as message_count
                FROM chat_list
                ORDER BY last_message_time DESC
                """
            ]
            
            for query in queries:
                try:
                    cursor.execute(query)
                    rows = cursor.fetchall()
                    
                    for row in rows:
                        jid = row['jid']
                        
                        # Determine if group chat
                        is_group = jid.endswith("@g.us") or "group" in jid.lower()
                        
                        # sqlite3.Row doesn't have .get(), use try/except or check keys
                        display_name = row['display_name'] if 'display_name' in row.keys() else None
                        last_message_timestamp = None
                        if 'last_message_timestamp' in row.keys():
                            last_message_timestamp = row['last_message_timestamp']
                        elif 'last_message_table_row_id' in row.keys():
                            last_message_timestamp = row['last_message_table_row_id']
                        elif 'last_message_row_id' in row.keys():
                            last_message_timestamp = row['last_message_row_id']
                        
                        message_count = row['message_count'] if 'message_count' in row.keys() else 0
                        
                        chat = Chat(
                            jid=jid,
                            display_name=display_name or self._get_contact_name(jid),
                            last_message_timestamp=last_message_timestamp,
                            message_count=message_count,
                            is_group=is_group
                        )
                        
                        # Get participants for group chats
                        if is_group:
                            chat.participants = self._get_group_participants(jid)
                        
                        chats.append(chat)
                    
                    logger.info(f"Found {len(chats)} chats")
                    break
                    
                except sqlite3.OperationalError as e:
                    logger.debug(f"Query failed, trying next: {e}")
                    continue
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error extracting chats: {e}")
            raise
        
        return chats
    
    def _get_group_participants(self, group_jid: str) -> List[str]:
        """Get list of participants for a group chat"""
        participants = []
        
        try:
            conn = sqlite3.connect(self.msgstore_db)
            cursor = conn.cursor()
            
            queries = [
                # Modern schema
                """
                SELECT jid.raw_string as jid
                FROM group_participant_user
                JOIN jid ON group_participant_user.jid_row_id = jid._id
                JOIN group_participant ON group_participant_user.group_participant_row_id = group_participant._id
                JOIN chat ON group_participant.group_jid_row_id = chat.jid_row_id
                WHERE chat.jid_row_id = (SELECT _id FROM jid WHERE raw_string = ?)
                """,
                # Older schema
                """
                SELECT jid FROM group_participants WHERE gjid = ?
                """
            ]
            
            for query in queries:
                try:
                    cursor.execute(query, (group_jid,))
                    participants = [row[0] for row in cursor.fetchall()]
                    break
                except sqlite3.OperationalError:
                    continue
            
            conn.close()
        except Exception as e:
            logger.warning(f"Could not get participants for {group_jid}: {e}")
        
        return participants
    
    def get_messages(self, chat_jid: Optional[str] = None, limit: Optional[int] = None) -> List[Message]:
        """
        Extract messages from the database.
        
        Args:
            chat_jid: Optional JID to filter messages by chat
            limit: Optional limit on number of messages to retrieve
            
        Returns:
            List of Message objects
        """
        messages = []
        
        try:
            conn = sqlite3.connect(self.msgstore_db)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Build query based on available schema - try multiple schemas
            queries_to_try = [
                # Full schema with all columns
                """
                SELECT 
                    _id as message_id,
                    key_remote_jid as chat_jid,
                    timestamp as timestamp,
                    key_from_me as from_me,
                    data as message_text,
                    media_wa_type as media_type,
                    media_path as media_path,
                    media_caption as media_caption,
                    quoted_row_id as quoted_message_id,
                    remote_resource as remote_resource,
                    status as status
                FROM message
                """,
                # Simple schema without media_path
                """
                SELECT 
                    _id as message_id,
                    key_remote_jid as chat_jid,
                    timestamp as timestamp,
                    key_from_me as from_me,
                    data as message_text,
                    media_wa_type as media_type
                FROM message
                """,
                # Older schema with messages table
                """
                SELECT 
                    _id as message_id,
                    key_remote_jid as chat_jid,
                    timestamp as timestamp,
                    key_from_me as from_me,
                    data as message_text,
                    media_wa_type as media_type,
                    media_name as media_path
                FROM messages
                """
            ]
            
            for base_query in queries_to_try:
                try:
                    query = base_query
                    if chat_jid:
                        query += " WHERE key_remote_jid = ?"
                    
                    query += " ORDER BY timestamp ASC"
                    
                    if limit:
                        query += f" LIMIT {limit}"
                    
                    cursor.execute(query, (chat_jid,) if chat_jid else ())
                    rows = cursor.fetchall()
                    
                    for row in rows:
                        row_keys = row.keys()
                        message = Message(
                            message_id=row['message_id'],
                            chat_jid=row['chat_jid'],
                            timestamp=row['timestamp'],
                            from_me=bool(row['from_me']),
                            message_text=row['message_text'] if 'message_text' in row_keys else None,
                            media_type=row['media_type'] if 'media_type' in row_keys else None,
                            media_path=row['media_path'] if 'media_path' in row_keys else None,
                            media_caption=row['media_caption'] if 'media_caption' in row_keys else None,
                            quoted_message_id=row['quoted_message_id'] if 'quoted_message_id' in row_keys else None,
                            remote_resource=row['remote_resource'] if 'remote_resource' in row_keys else None,
                            status=row['status'] if 'status' in row_keys else None
                        )
                        messages.append(message)
                    
                    # Successfully executed, break out of loop
                    break
                    
                except sqlite3.OperationalError:
                    continue
            
            logger.info(f"Extracted {len(messages)} messages")
            conn.close()
            
        except Exception as e:
            logger.error(f"Error extracting messages: {e}")
            raise
        
        return messages
    
    def get_call_logs(self) -> List[CallLog]:
        """
        Extract call logs from the database.
        
        Returns:
            List of CallLog objects
        """
        call_logs = []
        
        try:
            conn = sqlite3.connect(self.msgstore_db)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            queries = [
                # Modern schema
                """
                SELECT 
                    _id as call_id,
                    jid.raw_string as jid,
                    timestamp as timestamp,
                    from_me as from_me,
                    duration as duration,
                    video_call as video_call,
                    call_result as call_result
                FROM call_log
                JOIN jid ON call_log.jid_row_id = jid._id
                ORDER BY timestamp DESC
                """,
                # Alternative table name
                """
                SELECT 
                    _id as call_id,
                    jid as jid,
                    timestamp as timestamp,
                    from_me as from_me,
                    duration as duration,
                    video_call as video_call,
                    call_result as call_result
                FROM calls
                ORDER BY timestamp DESC
                """
            ]
            
            for query in queries:
                try:
                    cursor.execute(query)
                    rows = cursor.fetchall()
                    
                    for row in rows:
                        call_log = CallLog(
                            call_id=row['call_id'],
                            jid=row['jid'],
                            timestamp=row['timestamp'],
                            from_me=bool(row['from_me']),
                            duration=row.get('duration', 0),
                            video_call=bool(row.get('video_call', 0)),
                            call_result=row.get('call_result')
                        )
                        call_logs.append(call_log)
                    
                    logger.info(f"Found {len(call_logs)} call logs")
                    break
                    
                except sqlite3.OperationalError:
                    continue
            
            conn.close()
            
        except Exception as e:
            logger.warning(f"Could not extract call logs: {e}")
        
        return call_logs
    
    def get_contacts(self) -> List[Contact]:
        """
        Extract contacts from the database.
        
        Returns:
            List of Contact objects
        """
        contacts = []
        
        # If wa.db is available, use it
        if self.wa_db:
            try:
                conn = sqlite3.connect(self.wa_db)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                queries = [
                    "SELECT jid, display_name FROM wa_contacts",
                    "SELECT jid, display_name FROM contacts",
                    "SELECT jid, display_name FROM user"
                ]
                
                for query in queries:
                    try:
                        cursor.execute(query)
                        rows = cursor.fetchall()
                        
                        for row in rows:
                            if row['jid']:
                                # sqlite3.Row doesn't have .get(), check if key exists
                                display_name = row['display_name'] if 'display_name' in row.keys() else None
                                contact = Contact(
                                    jid=row['jid'],
                                    display_name=display_name
                                )
                                contacts.append(contact)
                        
                        break
                    except sqlite3.OperationalError:
                        continue
                
                conn.close()
                
            except Exception as e:
                logger.warning(f"Could not load contacts from wa.db: {e}")
        
        # Also extract contacts from msgstore.db (from message senders/receivers)
        try:
            conn = sqlite3.connect(self.msgstore_db)
            cursor = conn.cursor()
            
            query = """
                SELECT DISTINCT key_remote_jid as jid
                FROM message
                WHERE key_remote_jid NOT IN (SELECT jid FROM (SELECT jid FROM contacts LIMIT 1))
            """
            
            try:
                cursor.execute(query)
                jids = [row[0] for row in cursor.fetchall()]
                
                for jid in jids:
                    # Check if already added
                    if not any(c.jid == jid for c in contacts):
                        contact = Contact(jid=jid)
                        contacts.append(contact)
                        
            except sqlite3.OperationalError:
                pass
            
            conn.close()
            
        except Exception as e:
            logger.warning(f"Could not extract contacts from msgstore.db: {e}")
        
        logger.info(f"Found {len(contacts)} contacts")
        return contacts
    
    def get_chat_with_messages(self, chat_jid: str, message_limit: Optional[int] = None) -> Chat:
        """
        Get a chat with its messages.
        
        Args:
            chat_jid: JID of the chat
            message_limit: Optional limit on number of messages
            
        Returns:
            Chat object with messages populated
        """
        chats = self.get_chats()
        chat = next((c for c in chats if c.jid == chat_jid), None)
        
        if not chat:
            raise ValueError(f"Chat not found: {chat_jid}")
        
        chat.messages = self.get_messages(chat_jid, message_limit)
        return chat

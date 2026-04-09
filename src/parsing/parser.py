#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
WhatsApp Database Parser Module

Parses WhatsApp SQLite databases to extract chats, messages, contacts, and call logs.
"""

import sqlite3
import os
import contextlib
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any, Iterator
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


@dataclass
class StatusUpdate:
    """Represents a WhatsApp status update"""
    status_id: int
    jid: str
    timestamp: int
    media_type: Optional[int] = None
    text_content: Optional[str] = None
    
    def get_datetime(self) -> datetime:
        """Convert timestamp to datetime"""
        return datetime.fromtimestamp(self.timestamp / 1000)


@dataclass
class TimelineEvent:
    """Represents a unified event in the reconstruction timeline"""
    event_type: str  # 'message', 'call', 'status'
    timestamp: int
    jid: str
    data: Any
    
    def get_datetime(self) -> datetime:
        """Convert timestamp to datetime"""
        return datetime.fromtimestamp(self.timestamp / 1000)


class WhatsAppParser:
    """
    Parser for WhatsApp SQLite databases.
    
    Extracts chats, messages, contacts, and call logs from msgstore.db, wa.db, and others.
    """
    
    def __init__(self, msgstore_db: str, wa_db: Optional[str] = None, 
                 status_db: Optional[str] = None, media_db: Optional[str] = None):
        """
        Initialize parser with database paths.
        
        Args:
            msgstore_db: Path to msgstore.db (main message database)
            wa_db: Optional path to wa.db (contacts database)
            status_db: Optional path to status.db (status updates)
            media_db: Optional path to media.db (media metadata)
        """
        self.msgstore_db = Path(msgstore_db)
        if not self.msgstore_db.exists():
            raise FileNotFoundError(f"msgstore.db not found: {msgstore_db}")
        
        self.wa_db = Path(wa_db) if wa_db and Path(wa_db).exists() else None
        self.status_db = Path(status_db) if status_db and Path(status_db).exists() else None
        self.media_db = Path(media_db) if media_db and Path(media_db).exists() else None
        
        self.contacts_cache: Dict[str, str] = {}
        self._connections: Dict[str, sqlite3.Connection] = {}
        
        # Load contacts if wa.db is available
        if self.wa_db:
            self._load_contacts()

    def __del__(self):
        """Close all connections on deletion"""
        self.close()

    def close(self):
        """Close all active database connections"""
        for conn in self._connections.values():
            try:
                conn.close()
            except Exception:
                pass
        self._connections.clear()

    @contextlib.contextmanager
    def _get_cursor(self, db_path: Path) -> Iterator[sqlite3.Cursor]:
        """Get a cursor for a database, reusing connections"""
        db_key = str(db_path.resolve())
        if db_key not in self._connections:
            try:
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                self._connections[db_key] = conn
            except Exception as e:
                logger.error(f"Failed to connect to {db_path}: {e}")
                raise
        
        conn = self._connections[db_key]
        cursor = conn.cursor()
        try:
            yield cursor
        finally:
            cursor.close()
    
    def _load_contacts(self):
        """Load contacts from wa.db"""
        try:
            with self._get_cursor(self.wa_db) as cursor:
                # Try different possible table names
                tables_to_try = ["wa_contacts", "contacts", "user"]
                
                for table in tables_to_try:
                    try:
                        query = f"SELECT jid, display_name FROM {table}"
                        cursor.execute(query)
                        for row in cursor.fetchall():
                            jid = row['jid']
                            display_name = row['display_name']
                            if jid:
                                self.contacts_cache[jid] = display_name or ""
                        logger.info(f"Loaded {len(self.contacts_cache)} contacts from {table}")
                        break
                    except sqlite3.OperationalError:
                        continue
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
            with self._get_cursor(self.msgstore_db) as cursor:
                # Query for chats - try different possible schemas
                # Enhanced query to join with jid_map to get the phone-based JID for LID chats
                queries = [
                    # Modern schema (v3+) with LID mapping
                    """
                    SELECT 
                        j.raw_string as jid,
                        COALESCE(mapped_j.raw_string, j.raw_string) as display_jid,
                        chat.subject as display_name,
                        chat.last_message_row_id,
                        chat.last_read_message_row_id,
                        (SELECT COUNT(*) FROM message WHERE message.chat_row_id = chat._id) as message_count
                    FROM chat
                    JOIN jid j ON chat.jid_row_id = j._id
                    LEFT JOIN jid_map jm ON chat.jid_row_id = jm.lid_row_id
                    LEFT JOIN jid mapped_j ON jm.jid_row_id = mapped_j._id
                    ORDER BY chat.last_message_row_id DESC
                    """,
                    # Modern schema (v2)
                    """
                    SELECT 
                        jid.raw_string as jid,
                        chat.subject as display_name,
                        chat.last_message_row_id,
                        chat.last_message_table_row_id,
                        chat.last_read_message_table_row_id,
                        (SELECT COUNT(*) FROM message WHERE message.chat_row_id = chat._id) as message_count
                    FROM chat
                    JOIN jid ON chat.jid_row_id = jid._id
                    ORDER BY chat.last_message_table_row_id DESC
                    """,
                    # Fallback schema
                    """
                    SELECT 
                        jid.raw_string as jid,
                        chat.subject as display_name,
                        (SELECT COUNT(*) FROM message WHERE message.key_remote_jid = jid.raw_string) as message_count
                    FROM chat
                    JOIN jid ON chat.jid_row_id = jid._id
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
                
                rows = None
                for query in queries:
                    try:
                        cursor.execute(query)
                        rows = cursor.fetchall()
                        break
                    except sqlite3.OperationalError:
                        continue
                
                if rows:
                    # Collect group JIDs for bulk participant fetching
                    group_jids = []
                    for row in rows:
                        jid = row['jid']
                        display_jid = row['display_jid'] if 'display_jid' in row.keys() else jid
                        is_group = jid.endswith("@g.us") or "group" in jid.lower()
                        
                        display_name = row['display_name'] if 'display_name' in row.keys() else None
                        
                        # Try to get name from wa.db using either JID or mapped JID
                        if not display_name:
                            display_name = self._get_contact_name(display_jid) or self._get_contact_name(jid)

                        last_message_timestamp = None
                        if 'last_message_timestamp' in row.keys():
                            last_message_timestamp = row['last_message_timestamp']
                        elif 'last_message_row_id' in row.keys():
                            last_message_timestamp = row['last_message_row_id']
                        elif 'last_message_table_row_id' in row.keys():
                            last_message_timestamp = row['last_message_table_row_id']
                        
                        message_count = row['message_count'] if 'message_count' in row.keys() else 0
                        
                        chat = Chat(
                            jid=jid,
                            display_name=display_name,
                            last_message_timestamp=last_message_timestamp,
                            message_count=message_count,
                            is_group=is_group
                        )
                        chats.append(chat)
                        if is_group:
                            group_jids.append(jid)
                    
                    # Bulk fetch participants if any group chats found
                    if group_jids:
                        all_participants = self._get_bulk_group_participants(group_jids)
                        for chat in chats:
                            if chat.is_group and chat.jid in all_participants:
                                chat.participants = all_participants[chat.jid]
                    
                    logger.info(f"Found {len(chats)} chats")
            
        except Exception as e:
            logger.error(f"Error extracting chats: {e}")
            raise
        
        return chats

    def _get_bulk_group_participants(self, group_jids: List[str]) -> Dict[str, List[str]]:
        """Fetch participants for multiple groups in a more efficient way"""
        group_participants = {}
        try:
            with self._get_cursor(self.msgstore_db) as cursor:
                # This is still a bit tricky because of the JOINs, but we can use IN clause
                # Modern schema
                query = """
                SELECT 
                    group_jid.raw_string as group_jid,
                    participant_jid.raw_string as participant_jid
                FROM group_participant_user
                JOIN jid as participant_jid ON group_participant_user.jid_row_id = participant_jid._id
                JOIN group_participant ON group_participant_user.group_participant_row_id = group_participant._id
                JOIN jid as group_jid ON group_participant.group_jid_row_id = group_jid._id
                WHERE group_jid.raw_string IN ({})
                """.format(','.join(['?'] * len(group_jids)))
                
                try:
                    cursor.execute(query, group_jids)
                    for row in cursor.fetchall():
                        g_jid = row['group_jid']
                        p_jid = row['participant_jid']
                        if g_jid not in group_participants:
                            group_participants[g_jid] = []
                        group_participants[g_jid].append(p_jid)
                except sqlite3.OperationalError:
                    # Fallback to individual if bulk fails
                    for g_jid in group_jids:
                        group_participants[g_jid] = self._get_group_participants(g_jid)
        except Exception as e:
            logger.warning(f"Error in bulk participant fetch: {e}")
            
        return group_participants
    
    def _get_group_participants(self, group_jid: str) -> List[str]:
        """Get list of participants for a single group chat (fallback)"""
        participants = []
        try:
            with self._get_cursor(self.msgstore_db) as cursor:
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
            with self._get_cursor(self.msgstore_db) as cursor:
                # Build query based on available schema - try multiple schemas
                queries_to_try = [
                    # Modern schema with joins (v3+)
                    """
                    SELECT 
                        m._id as message_id,
                        j.raw_string as chat_jid,
                        m.timestamp as timestamp,
                        m.from_me as from_me,
                        m.text_data as message_text,
                        m.message_type as media_type,
                        mm.file_path as media_path,
                        mm.media_caption as media_caption,
                        mq.message_row_id as quoted_message_id,
                        sender_jid.raw_string as remote_resource,
                        m.status as status
                    FROM message m
                    JOIN chat c ON m.chat_row_id = c._id
                    JOIN jid j ON c.jid_row_id = j._id
                    LEFT JOIN message_media mm ON m._id = mm.message_row_id
                    LEFT JOIN message_quoted mq ON m._id = mq.message_row_id
                    LEFT JOIN jid sender_jid ON m.sender_jid_row_id = sender_jid._id
                    """,
                    # Full schema with all columns (v2)
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
                        params = []
                        if chat_jid:
                            # Handle different column names for filtering
                            if "m.chat_row_id" in base_query:
                                query += " WHERE j.raw_string = ?"
                            else:
                                query += " WHERE key_remote_jid = ?"
                            params.append(chat_jid)
                        
                        # Handle ORDER BY
                        if "m.timestamp" in base_query:
                            query += " ORDER BY m.timestamp ASC"
                        else:
                            query += " ORDER BY timestamp ASC"
                        
                        if limit:
                            query += f" LIMIT {limit}"
                        
                        cursor.execute(query, params)
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
                        
                    except sqlite3.OperationalError as e:
                        logger.debug(f"Query failed: {e}")
                        continue
            
            logger.info(f"Extracted {len(messages)} messages")
            
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
            with self._get_cursor(self.msgstore_db) as cursor:
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
                                duration=row['duration'] if 'duration' in row.keys() else 0,
                                video_call=bool(row['video_call'] if 'video_call' in row.keys() else 0),
                                call_result=row['call_result'] if 'call_result' in row.keys() else None
                            )
                            call_logs.append(call_log)
                        
                        logger.info(f"Found {len(call_logs)} call logs")
                        break
                        
                    except sqlite3.OperationalError:
                        continue
            
        except Exception as e:
            logger.warning(f"Could not extract call logs: {e}")
        
        return call_logs

    def get_status_updates(self) -> List[StatusUpdate]:
        """
        Extract status updates from status.db.
        
        Returns:
            List of StatusUpdate objects
        """
        status_updates = []
        if not self.status_db:
            return status_updates

        try:
            with self._get_cursor(self.status_db) as cursor:
                # Based on the schema we saw earlier
                query = """
                SELECT 
                    status.row_id as status_id,
                    status_info.chat_jid as jid,
                    status.timestamp as timestamp,
                    status.type as media_type,
                    status_text.text_content_proto as text_content
                FROM status
                JOIN status_info ON status.status_info_row_id = status_info.row_id
                LEFT JOIN status_text ON status.row_id = status_text.status_row_id
                ORDER BY status.timestamp DESC
                """
                try:
                    cursor.execute(query)
                    for row in cursor.fetchall():
                        status_updates.append(StatusUpdate(
                            status_id=row['status_id'],
                            jid=row['jid'],
                            timestamp=row['timestamp'],
                            media_type=row['media_type'],
                            text_content=row['text_content']  # This might be BLOB/proto, but we'll take it
                        ))
                    logger.info(f"Found {len(status_updates)} status updates")
                except sqlite3.OperationalError as e:
                    logger.debug(f"Status query failed: {e}")
        except Exception as e:
            logger.warning(f"Could not extract status updates: {e}")

        return status_updates
    
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
                with self._get_cursor(self.wa_db) as cursor:
                    queries = [
                        "SELECT jid, display_name FROM wa_contacts",
                        "SELECT jid, display_name FROM contacts",
                        "SELECT jid, display_name FROM user"
                    ]
                    
                    for query in queries:
                        try:
                            cursor.execute(query)
                            for row in cursor.fetchall():
                                if row['jid']:
                                    display_name = row['display_name'] if 'display_name' in row.keys() else None
                                    contacts.append(Contact(jid=row['jid'], display_name=display_name))
                            break
                        except sqlite3.OperationalError:
                            continue
            except Exception as e:
                logger.warning(f"Could not load contacts from wa.db: {e}")
        
        # Also extract contacts from msgstore.db (from message senders/receivers)
        try:
            with self._get_cursor(self.msgstore_db) as cursor:
                # Try to find contacts table in msgstore too
                query = """
                    SELECT DISTINCT key_remote_jid as jid
                    FROM message
                """
                try:
                    cursor.execute(query)
                    jids = [row[0] for row in cursor.fetchall()]
                    
                    existing_jids = {c.jid for c in contacts}
                    for jid in jids:
                        if jid and jid not in existing_jids:
                            contacts.append(Contact(jid=jid))
                            existing_jids.add(jid)
                except sqlite3.OperationalError:
                    pass
        except Exception as e:
            logger.warning(f"Could not extract contacts from msgstore.db: {e}")
        
        logger.info(f"Found {len(contacts)} contacts")
        return contacts

    def get_event_timeline(self, limit: Optional[int] = None) -> List[TimelineEvent]:
        """
        Reconstruct a unified chronological timeline of all events (messages, calls, statuses).
        
        Args:
            limit: Optional limit on total events
            
        Returns:
            Sorted list of TimelineEvent objects
        """
        events = []
        
        # Fetch messages
        messages = self.get_messages(limit=limit)
        for msg in messages:
            events.append(TimelineEvent(
                event_type='message',
                timestamp=msg.timestamp,
                jid=msg.chat_jid,
                data=msg
            ))
            
        # Fetch calls
        calls = self.get_call_logs()
        for call in calls:
            events.append(TimelineEvent(
                event_type='call',
                timestamp=call.timestamp,
                jid=call.jid,
                data=call
            ))
            
        # Fetch status updates
        statuses = self.get_status_updates()
        for status in statuses:
            events.append(TimelineEvent(
                event_type='status',
                timestamp=status.timestamp,
                jid=status.jid,
                data=status
            ))
            
        # Sort by timestamp
        events.sort(key=lambda x: x.timestamp)
        
        if limit:
            events = events[-limit:]
            
        logger.info(f"Reconstructed timeline with {len(events)} events")
        return events
    
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

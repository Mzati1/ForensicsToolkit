#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
WhatsApp Forensic Report Generator

Generates comprehensive forensic reports from parsed WhatsApp data.
"""

import json
import csv
import html
from pathlib import Path
from enum import Enum
from typing import List, Dict, Optional
from datetime import datetime
import logging

from ..parsing.parser import Chat, Message, Contact, CallLog

logger = logging.getLogger(__name__)


class ReportFormat(Enum):
    """Report output formats"""
    HTML = "html"
    JSON = "json"
    CSV = "csv"


class WhatsAppReporter:
    """
    Generates forensic reports from parsed WhatsApp data.
    
    Supports multiple output formats: HTML, JSON, CSV
    """
    
    def __init__(self, output_dir: str = "output/reports"):
        """
        Initialize reporter.
        
        Args:
            output_dir: Directory to save reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_html_report(
        self,
        chats: List[Chat],
        contacts: List[Contact],
        call_logs: List[CallLog],
        metadata: Optional[Dict] = None,
        output_file: Optional[str] = None
    ) -> str:
        """
        Generate HTML forensic report.
        
        Args:
            chats: List of chats to include
            contacts: List of contacts
            call_logs: List of call logs
            metadata: Optional metadata (company, examiner, notes, etc.)
            output_file: Optional output file path
            
        Returns:
            Path to generated report
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"whatsapp_report_{timestamp}.html"
        else:
            output_file = Path(output_file)
            output_file.parent.mkdir(parents=True, exist_ok=True)
        
        metadata = metadata or {}
        
        html_content = self._generate_html_content(chats, contacts, call_logs, metadata)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Generated HTML report: {output_file}")
        return str(output_file)
    
    def _generate_html_content(
        self,
        chats: List[Chat],
        contacts: List[Contact],
        call_logs: List[CallLog],
        metadata: Dict
    ) -> str:
        """Generate HTML content"""
        company = metadata.get('company', 'WhatsApp Forensics Report')
        examiner = metadata.get('examiner', 'Unknown')
        record = metadata.get('record', 'N/A')
        unit = metadata.get('unit', 'N/A')
        notes = metadata.get('notes', '')
        date = datetime.now().strftime('%d-%m-%Y')
        
        html_content_str = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WhatsApp Forensics Report - {date}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background-color: white;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .section {{
            background-color: white;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #4CAF50;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
        .chat-message {{
            margin: 10px 0;
            padding: 10px;
            border-radius: 5px;
        }}
        .message-from-me {{
            background-color: #DCF8C6;
            text-align: right;
        }}
        .message-from-other {{
            background-color: #FFFFFF;
            text-align: left;
        }}
        .timestamp {{
            color: #666;
            font-size: 0.9em;
        }}
        h1, h2 {{
            color: #333;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{html.escape(company)}</h1>
        <table>
            <tr>
                <th>Record</th>
                <th>Unit</th>
                <th>Examiner</th>
                <th>Date</th>
            </tr>
            <tr>
                <td>{html.escape(str(record))}</td>
                <td>{html.escape(str(unit))}</td>
                <td>{html.escape(examiner)}</td>
                <td>{date}</td>
            </tr>
        </table>
        <h3>Notes</h3>
        <p>{html.escape(notes)}</p>
    </div>
    
    <div class="section">
        <h2>Summary</h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>Count</th>
            </tr>
            <tr>
                <td>Total Chats</td>
                <td>{len(chats)}</td>
            </tr>
            <tr>
                <td>Total Contacts</td>
                <td>{len(contacts)}</td>
            </tr>
            <tr>
                <td>Total Call Logs</td>
                <td>{len(call_logs)}</td>
            </tr>
            <tr>
                <td>Total Messages</td>
                <td>{sum(len(chat.messages) for chat in chats)}</td>
            </tr>
        </table>
    </div>
    
    <div class="section">
        <h2>Contacts</h2>
        <table>
            <tr>
                <th>JID</th>
                <th>Display Name</th>
                <th>Phone Number</th>
            </tr>
"""
        
        for contact in contacts[:100]:  # Limit to first 100
            html_content_str += f"""
            <tr>
                <td>{html.escape(contact.jid)}</td>
                <td>{html.escape(contact.display_name or 'N/A')}</td>
                <td>{html.escape(contact.phone_number or 'N/A')}</td>
            </tr>
"""
        
        html_content_str += """
        </table>
    </div>
    
    <div class="section">
        <h2>Chats</h2>
"""
        
        for chat in chats[:20]:  # Limit to first 20 chats
            html_content_str += f"""
        <h3>{html.escape(chat.display_name or chat.jid)}</h3>
        <p><strong>JID:</strong> {html.escape(chat.jid)}</p>
        <p><strong>Type:</strong> {'Group' if chat.is_group else 'Individual'}</p>
        <p><strong>Message Count:</strong> {chat.message_count}</p>
"""
            if chat.participants:
                html_content_str += f"<p><strong>Participants:</strong> {', '.join(chat.participants[:10])}</p>"
            
            if chat.last_message_timestamp:
                last_msg_dt = datetime.fromtimestamp(chat.last_message_timestamp / 1000)
                html_content_str += f"<p><strong>Last Message:</strong> {last_msg_dt.strftime('%Y-%m-%d %H:%M:%S')}</p>"
            
            # Show recent messages
            if chat.messages:
                html_content_str += "<h4>Recent Messages</h4>"
                for msg in chat.messages[-10:]:  # Last 10 messages
                    msg_class = "message-from-me" if msg.from_me else "message-from-other"
                    msg_time = msg.get_datetime().strftime('%Y-%m-%d %H:%M:%S')
                    msg_text = html.escape(msg.message_text or '[Media]' if msg.media_type else '[No content]')
                    html_content_str += f"""
                    <div class="chat-message {msg_class}">
                        <div class="timestamp">{msg_time}</div>
                        <div>{msg_text}</div>
                    </div>
"""
        
        html_content_str += """
    </div>
    
    <div class="section">
        <h2>Call Logs</h2>
        <table>
            <tr>
                <th>Timestamp</th>
                <th>Contact</th>
                <th>Direction</th>
                <th>Type</th>
                <th>Duration (seconds)</th>
            </tr>
"""
        
        for call in call_logs[:100]:  # Limit to first 100
            call_time = call.get_datetime().strftime('%Y-%m-%d %H:%M:%S')
            direction = "Outgoing" if call.from_me else "Incoming"
            call_type = "Video" if call.video_call else "Audio"
            html_content_str += f"""
            <tr>
                <td>{call_time}</td>
                <td>{html.escape(call.jid)}</td>
                <td>{direction}</td>
                <td>{call_type}</td>
                <td>{call.duration}</td>
            </tr>
"""
        
        html_content_str += """
        </table>
    </div>
</body>
</html>
"""
        return html_content_str
    
    def generate_json_report(
        self,
        chats: List[Chat],
        contacts: List[Contact],
        call_logs: List[CallLog],
        metadata: Optional[Dict] = None,
        output_file: Optional[str] = None
    ) -> str:
        """
        Generate JSON forensic report.
        
        Args:
            chats: List of chats to include
            contacts: List of contacts
            call_logs: List of call logs
            metadata: Optional metadata
            output_file: Optional output file path
            
        Returns:
            Path to generated report
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"whatsapp_report_{timestamp}.json"
        else:
            output_file = Path(output_file)
            output_file.parent.mkdir(parents=True, exist_ok=True)
        
        report_data = {
            "metadata": metadata or {},
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_chats": len(chats),
                "total_contacts": len(contacts),
                "total_call_logs": len(call_logs),
                "total_messages": sum(len(chat.messages) for chat in chats)
            },
            "contacts": [
                {
                    "jid": c.jid,
                    "display_name": c.display_name,
                    "phone_number": c.phone_number
                }
                for c in contacts
            ],
            "chats": [
                {
                    "jid": chat.jid,
                    "display_name": chat.display_name,
                    "is_group": chat.is_group,
                    "participants": chat.participants,
                    "message_count": chat.message_count,
                    "last_message_timestamp": chat.last_message_timestamp,
                    "messages": [
                        {
                            "message_id": msg.message_id,
                            "timestamp": msg.timestamp,
                            "from_me": msg.from_me,
                            "message_text": msg.message_text,
                            "media_type": msg.media_type,
                            "media_path": msg.media_path,
                            "status": msg.status
                        }
                        for msg in chat.messages
                    ]
                }
                for chat in chats
            ],
            "call_logs": [
                {
                    "call_id": call.call_id,
                    "jid": call.jid,
                    "timestamp": call.timestamp,
                    "from_me": call.from_me,
                    "duration": call.duration,
                    "video_call": call.video_call,
                    "call_result": call.call_result
                }
                for call in call_logs
            ]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Generated JSON report: {output_file}")
        return str(output_file)
    
    def generate_csv_report(
        self,
        chats: List[Chat],
        contacts: List[Contact],
        call_logs: List[CallLog],
        output_dir: Optional[str] = None
    ) -> List[str]:
        """
        Generate CSV reports (separate files for chats, messages, contacts, calls).
        
        Args:
            chats: List of chats
            contacts: List of contacts
            call_logs: List of call logs
            output_dir: Optional output directory
            
        Returns:
            List of generated CSV file paths
        """
        if output_dir is None:
            output_dir = self.output_dir
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        generated_files = []
        
        # Contacts CSV
        contacts_file = output_dir / f"contacts_{timestamp}.csv"
        with open(contacts_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['JID', 'Display Name', 'Phone Number'])
            for contact in contacts:
                writer.writerow([contact.jid, contact.display_name or '', contact.phone_number or ''])
        generated_files.append(str(contacts_file))
        
        # Messages CSV
        messages_file = output_dir / f"messages_{timestamp}.csv"
        with open(messages_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Message ID', 'Chat JID', 'Timestamp', 'From Me', 'Message Text', 'Media Type', 'Media Path', 'Status'])
            for chat in chats:
                for msg in chat.messages:
                    writer.writerow([
                        msg.message_id,
                        msg.chat_jid,
                        msg.timestamp,
                        msg.from_me,
                        msg.message_text or '',
                        msg.media_type or '',
                        msg.media_path or '',
                        msg.status or ''
                    ])
        generated_files.append(str(messages_file))
        
        # Call logs CSV
        if call_logs:
            calls_file = output_dir / f"calls_{timestamp}.csv"
            with open(calls_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Call ID', 'JID', 'Timestamp', 'From Me', 'Duration', 'Video Call', 'Call Result'])
                for call in call_logs:
                    writer.writerow([
                        call.call_id,
                        call.jid,
                        call.timestamp,
                        call.from_me,
                        call.duration,
                        call.video_call,
                        call.call_result or ''
                    ])
            generated_files.append(str(calls_file))
        
        logger.info(f"Generated {len(generated_files)} CSV reports")
        return generated_files

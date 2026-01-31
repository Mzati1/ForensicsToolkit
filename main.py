#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
WhatsApp Forensics Toolkit - Main Entry Point

A comprehensive toolkit for WhatsApp forensics analysis on CAINE OS.
Supports acquisition, decryption, parsing, and reporting of WhatsApp data.
"""

import argparse
import sys
import logging
from pathlib import Path

from src.acquisition import WhatsAppAcquirer, AcquisitionSource
from src.crypto import WhatsAppDecryptor
from src.parsing import WhatsAppParser
from src.reporting import WhatsAppReporter, ReportFormat

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for WhatsApp Forensics Toolkit"""
    parser = argparse.ArgumentParser(
        description='WhatsApp Forensics Toolkit - Acquisition, Decryption, Parsing, and Reporting',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Acquire from Android device via ADB
  python main.py acquire --source android_adb --output ./output

  # Acquire from local files
  python main.py acquire --source file --input ./whatsapp_data --output ./output

  # Decrypt encrypted database
  python main.py decrypt --input msgstore.db.crypt14 --key key --output msgstore.db

  # Parse database and generate report
  python main.py parse --msgstore msgstore.db --wa wa.db --output ./reports --format html

  # Full workflow: acquire, decrypt, parse, and report
  python main.py full --source file --input ./whatsapp_data --key key --output ./output
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Acquisition command
    acquire_parser = subparsers.add_parser('acquire', help='Acquire WhatsApp data')
    acquire_parser.add_argument('--source', choices=['android_adb', 'file'], required=True,
                               help='Acquisition source')
    acquire_parser.add_argument('--input', help='Input directory or device ID')
    acquire_parser.add_argument('--output', default='output', help='Output directory')
    
    # Decryption command
    decrypt_parser = subparsers.add_parser('decrypt', help='Decrypt WhatsApp database')
    decrypt_parser.add_argument('--input', required=True, help='Encrypted database file')
    decrypt_parser.add_argument('--key', required=True, help='Key file path')
    decrypt_parser.add_argument('--output', help='Output decrypted database file')
    
    # Parsing command
    parse_parser = subparsers.add_parser('parse', help='Parse WhatsApp database')
    parse_parser.add_argument('--msgstore', required=True, help='Path to msgstore.db')
    parse_parser.add_argument('--wa', help='Path to wa.db (optional)')
    parse_parser.add_argument('--output', default='output/reports', help='Output directory for reports')
    parse_parser.add_argument('--format', choices=['html', 'json', 'csv', 'pdf', 'all'], default='html',
                             help='Report format')
    parse_parser.add_argument('--chat-limit', type=int, help='Limit number of chats to process')
    parse_parser.add_argument('--message-limit', type=int, help='Limit number of messages per chat')
    
    # Full workflow command
    full_parser = subparsers.add_parser('full', help='Complete workflow: acquire, decrypt, parse, report')
    full_parser.add_argument('--source', choices=['android_adb', 'file'], required=True,
                            help='Acquisition source')
    full_parser.add_argument('--input', help='Input directory or device ID')
    full_parser.add_argument('--key', help='Key file for decryption (if needed)')
    full_parser.add_argument('--output', default='output', help='Output directory')
    full_parser.add_argument('--format', choices=['html', 'json', 'csv', 'pdf', 'all'], default='html',
                            help='Report format')
    full_parser.add_argument('--metadata-company', help='Company name for report')
    full_parser.add_argument('--metadata-examiner', help='Examiner name for report')
    full_parser.add_argument('--metadata-record', help='Record number for report')
    full_parser.add_argument('--metadata-notes', help='Notes for report')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == 'acquire':
            handle_acquire(args)
        elif args.command == 'decrypt':
            handle_decrypt(args)
        elif args.command == 'parse':
            handle_parse(args)
        elif args.command == 'full':
            handle_full(args)
        else:
            parser.print_help()
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error executing command: {e}", exc_info=True)
        sys.exit(1)


def handle_acquire(args):
    """Handle acquisition command"""
    logger.info(f"Starting acquisition from {args.source}")
    
    acquirer = WhatsAppAcquirer(output_dir=args.output)
    
    if args.source == 'android_adb':
        device_id = args.input if args.input else None
        acquired = acquirer.acquire_from_android_adb(device_id)
        summary = acquirer.get_acquisition_summary(acquired)
        logger.info(f"Acquisition complete. Summary: {summary}")
        
    elif args.source == 'file':
        if not args.input:
            raise ValueError("--input is required for file acquisition")
        acquired = acquirer.acquire_from_files(args.input)
        summary = acquirer.get_acquisition_summary(acquired)
        logger.info(f"Acquisition complete. Summary: {summary}")
        
    else:
        raise ValueError(f"Unsupported source: {args.source}")


def handle_decrypt(args):
    """Handle decryption command"""
    logger.info(f"Decrypting {args.input}")
    
    decryptor = WhatsAppDecryptor(args.key)
    output_file = args.output or Path(args.input).with_suffix('.db')
    
    decrypted = decryptor.decrypt(args.input, str(output_file))
    
    if decrypted:
        logger.info(f"Successfully decrypted to: {decrypted}")
    else:
        logger.error("Decryption failed")
        sys.exit(1)


def handle_parse(args):
    """Handle parsing command"""
    logger.info(f"Parsing database: {args.msgstore}")
    
    parser = WhatsAppParser(args.msgstore, args.wa)
    
    # Get data
    logger.info("Extracting chats...")
    chats = parser.get_chats()
    if args.chat_limit:
        chats = chats[:args.chat_limit]
    
    logger.info("Extracting messages...")
    for chat in chats:
        chat.messages = parser.get_messages(chat.jid, args.message_limit)
    
    logger.info("Extracting contacts...")
    contacts = parser.get_contacts()
    
    logger.info("Extracting call logs...")
    call_logs = parser.get_call_logs()
    
    # Generate reports
    reporter = WhatsAppReporter(output_dir=args.output)
    
    metadata = {
        'company': 'WhatsApp Forensics Report',
        'examiner': 'Forensics Tool',
        'record': 'N/A',
        'unit': 'Forensics Unit',
        'notes': 'Automated forensic analysis report'
    }
    
    formats = [args.format] if args.format != 'all' else ['html', 'json', 'csv', 'pdf']
    
    for fmt in formats:
        if fmt == 'html':
            report_file = reporter.generate_html_report(chats, contacts, call_logs, metadata)
            logger.info(f"Generated HTML report: {report_file}")
        elif fmt == 'json':
            report_file = reporter.generate_json_report(chats, contacts, call_logs, metadata)
            logger.info(f"Generated JSON report: {report_file}")
        elif fmt == 'csv':
            report_files = reporter.generate_csv_report(chats, contacts, call_logs)
            logger.info(f"Generated CSV reports: {report_files}")
        elif fmt == 'pdf':
            report_file = reporter.generate_pdf_report(chats, contacts, call_logs, metadata)
            logger.info(f"Generated PDF report: {report_file}")


def handle_full(args):
    """Handle full workflow command"""
    logger.info("Starting full workflow...")
    
    output_dir = Path(args.output)
    
    # Step 1: Acquire
    logger.info("Step 1: Acquisition")
    acquirer = WhatsAppAcquirer(output_dir=str(output_dir / "acquisition"))
    
    if args.source == 'android_adb':
        device_id = args.input if args.input else None
        acquired = acquirer.acquire_from_android_adb(device_id)
    elif args.source == 'file':
        if not args.input:
            raise ValueError("--input is required for file acquisition")
        acquired = acquirer.acquire_from_files(args.input)
    else:
        raise ValueError(f"Unsupported source: {args.source}")
    
    summary = acquirer.get_acquisition_summary(acquired)
    logger.info(f"Acquisition summary: {summary}")
    
    # Step 2: Decrypt if needed
    msgstore_path = None
    
    # Find encrypted databases in acquired files
    encrypted_dbs = [path for name, path in acquired.items() if 'crypt' in Path(path).name or Path(path).name.endswith(('.crypt12', '.crypt14', '.crypt15'))]
    
    if encrypted_dbs:
        logger.info("Step 2: Decryption")
        if not args.key:
            logger.warning("Encrypted databases found but no key provided. Skipping decryption.")
        else:
            decryptor = WhatsAppDecryptor(args.key)
            for enc_db in encrypted_dbs:
                decrypted = decryptor.decrypt(enc_db)
                if decrypted:
                    msgstore_path = decrypted
                    logger.info(f"Decrypted database: {decrypted}")
                    break
    
    # If no encrypted databases or decryption failed, look for unencrypted
    if not msgstore_path:
        # Find unencrypted msgstore.db
        unencrypted_dbs = [path for name, path in acquired.items() if Path(path).name == 'msgstore.db']
        if unencrypted_dbs:
            msgstore_path = unencrypted_dbs[0]
            logger.info(f"Using unencrypted database: {msgstore_path}")
        else:
            raise ValueError("No database found to parse")
    
    # Step 3: Parse
    logger.info("Step 3: Parsing")
    # Find wa.db if available
    wa_dbs = [path for name, path in acquired.items() if Path(path).name == 'wa.db']
    wa_db_path = wa_dbs[0] if wa_dbs else None
    
    parser = WhatsAppParser(msgstore_path, wa_db_path)
    
    chats = parser.get_chats()
    for chat in chats:
        chat.messages = parser.get_messages(chat.jid, limit=1000)  # Limit messages per chat
    
    contacts = parser.get_contacts()
    call_logs = parser.get_call_logs()
    
    # Step 4: Generate report
    logger.info("Step 4: Report generation")
    reporter = WhatsAppReporter(output_dir=str(output_dir / "reports"))
    
    metadata = {
        'company': args.metadata_company or 'WhatsApp Forensics Report',
        'examiner': args.metadata_examiner or 'Forensics Tool',
        'record': args.metadata_record or 'N/A',
        'unit': 'Forensics Unit',
        'notes': args.metadata_notes or 'Automated forensic analysis report'
    }
    
    formats = [args.format] if args.format != 'all' else ['html', 'json', 'csv']
    
    for fmt in formats:
        if fmt == 'html':
            report_file = reporter.generate_html_report(chats, contacts, call_logs, metadata)
            logger.info(f"Generated HTML report: {report_file}")
        elif fmt == 'json':
            report_file = reporter.generate_json_report(chats, contacts, call_logs, metadata)
            logger.info(f"Generated JSON report: {report_file}")
        elif fmt == 'csv':
            report_files = reporter.generate_csv_report(chats, contacts, call_logs)
            logger.info(f"Generated CSV reports: {report_files}")
    
    logger.info("Full workflow complete!")


if __name__ == '__main__':
    main()

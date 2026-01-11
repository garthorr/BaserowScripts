#!/usr/bin/env python3
"""
Test script for update_contacts.py

This script tests the core functionality with mocked API calls.
"""

import sys
import logging
from unittest.mock import Mock, patch, MagicMock
from update_contacts import BaserowContactsSync

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_read_excel():
    """Test reading Excel file."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST: Reading Excel file")
    logger.info("=" * 60)

    syncer = BaserowContactsSync(
        api_url="https://api.baserow.io",
        api_token="test_token",
        table_id=12345
    )

    contacts = syncer.read_excel_contacts('test_enrollment.xlsx')

    assert len(contacts) == 5, f"Expected 5 contacts, got {len(contacts)}"
    assert contacts[0]['email'] == 'john.doe@example.com'
    assert contacts[0]['first_name'] == 'John'
    assert contacts[0]['last_name'] == 'Doe'

    logger.info(f"✓ Successfully read {len(contacts)} contacts from Excel")
    for contact in contacts:
        logger.info(f"  - {contact['first_name']} {contact['last_name']} ({contact['email']})")

    return True


def test_sync_logic():
    """Test sync logic with mocked Baserow API."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST: Sync logic with mocked API")
    logger.info("=" * 60)

    # Mock existing contacts in Baserow
    # - john.doe@example.com exists and is active (should stay active)
    # - jane.smith@example.com exists but is inactive (should be marked active)
    # - old.user@example.com exists and is active (should be marked inactive - not in Excel)
    mock_baserow_contacts = [
        {
            'id': 1,
            'First Name': 'John',
            'Last Name': 'Doe',
            'Email': 'john.doe@example.com',
            'Active': True
        },
        {
            'id': 2,
            'First Name': 'Jane',
            'Last Name': 'Smith',
            'Email': 'jane.smith@example.com',
            'Active': False
        },
        {
            'id': 3,
            'First Name': 'Old',
            'Last Name': 'User',
            'Email': 'old.user@example.com',
            'Active': True
        }
    ]

    syncer = BaserowContactsSync(
        api_url="https://api.baserow.io",
        api_token="test_token",
        table_id=12345
    )

    # Mock the API methods
    with patch.object(syncer, 'fetch_all_contacts', return_value=mock_baserow_contacts):
        with patch.object(syncer, 'create_contact', return_value=True) as mock_create:
            with patch.object(syncer, 'update_contact', return_value=True) as mock_update:
                stats = syncer.sync_contacts(
                    excel_file='test_enrollment.xlsx',
                    dry_run=True
                )

    logger.info("\nSync Statistics:")
    logger.info(f"  Excel contacts: {stats['excel_contacts']}")
    logger.info(f"  Baserow contacts: {stats['baserow_contacts']}")
    logger.info(f"  New contacts: {stats['new_contacts']}")
    logger.info(f"  To mark active: {stats['marked_active']}")
    logger.info(f"  To mark inactive: {stats['marked_inactive']}")

    # Verify results
    assert stats['excel_contacts'] == 5, "Should read 5 contacts from Excel"
    assert stats['baserow_contacts'] == 3, "Should have 3 existing contacts"

    # New contacts: Bob, Alice, Charlie (3 total)
    assert stats['new_contacts'] == 3, f"Expected 3 new contacts, got {stats['new_contacts']}"

    # To mark active: Jane (1 total)
    assert stats['marked_active'] == 1, f"Expected 1 to mark active, got {stats['marked_active']}"

    # To mark inactive: Old User (1 total)
    assert stats['marked_inactive'] == 1, f"Expected 1 to mark inactive, got {stats['marked_inactive']}"

    logger.info("\n✓ All sync logic tests passed!")
    return True


def test_sync_with_actions():
    """Test sync with actual actions (not dry run)."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST: Sync with actions (mocked)")
    logger.info("=" * 60)

    mock_baserow_contacts = [
        {
            'id': 1,
            'First Name': 'John',
            'Last Name': 'Doe',
            'Email': 'john.doe@example.com',
            'Active': True
        },
        {
            'id': 2,
            'First Name': 'Old',
            'Last Name': 'User',
            'Email': 'old.user@example.com',
            'Active': True
        }
    ]

    syncer = BaserowContactsSync(
        api_url="https://api.baserow.io",
        api_token="test_token",
        table_id=12345
    )

    # Mock the API methods and track calls
    create_calls = []
    update_calls = []

    def mock_create(data):
        create_calls.append(data)
        return True

    def mock_update(row_id, data):
        update_calls.append({'row_id': row_id, 'data': data})
        return True

    with patch.object(syncer, 'fetch_all_contacts', return_value=mock_baserow_contacts):
        with patch.object(syncer, 'create_contact', side_effect=mock_create):
            with patch.object(syncer, 'update_contact', side_effect=mock_update):
                stats = syncer.sync_contacts(
                    excel_file='test_enrollment.xlsx',
                    dry_run=False
                )

    logger.info("\nActions taken:")
    logger.info(f"  Created contacts: {len(create_calls)}")
    for call in create_calls:
        logger.info(f"    - {call['Email']}")

    logger.info(f"  Updated contacts: {len(update_calls)}")
    for call in update_calls:
        logger.info(f"    - Row {call['row_id']}: {call['data']}")

    # Verify
    # Should create 4 new contacts (Jane, Bob, Alice, Charlie)
    assert len(create_calls) == 4, f"Expected 4 creates, got {len(create_calls)}"

    # Should update 1 contact (Old User to inactive)
    assert len(update_calls) == 1, f"Expected 1 update, got {len(update_calls)}"
    assert update_calls[0]['row_id'] == 2, "Should update row 2 (Old User)"
    assert update_calls[0]['data']['Active'] == False, "Should mark as inactive"

    logger.info("\n✓ All action tests passed!")
    return True


def main():
    """Run all tests."""
    try:
        logger.info("Starting update_contacts.py tests\n")

        # Test 1: Read Excel
        test_read_excel()

        # Test 2: Sync logic
        test_sync_logic()

        # Test 3: Sync with actions
        test_sync_with_actions()

        logger.info("\n" + "=" * 60)
        logger.info("✓ ALL TESTS PASSED!")
        logger.info("=" * 60)

        return 0

    except AssertionError as e:
        logger.error(f"\n✗ TEST FAILED: {e}")
        return 1
    except Exception as e:
        logger.error(f"\n✗ UNEXPECTED ERROR: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""
Check Sales Partner Portal Permissions for Number Cards
"""

import sys
import os

bench_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(bench_dir)
sys.path.insert(0, 'apps')
os.chdir('sites')

import frappe

frappe.init(site='koraflow-site')
frappe.connect()

role = 'Sales Partner Portal'

print(f'Checking permissions for role: {role}')
print()

# Check Number Card DocType permissions
print('1. Number Card DocType Permissions:')
nc_perms = frappe.get_all('DocPerm', 
    filters={'parent': 'Number Card', 'role': role},
    fields=['read', 'write', 'create', 'delete']
)

if nc_perms:
    for p in nc_perms:
        print(f'   Read: {p.read}, Write: {p.write}, Create: {p.create}, Delete: {p.delete}')
else:
    print('   ❌ No permissions found!')

print()

# Check Sales Invoice DocType permissions
print('2. Sales Invoice DocType Permissions:')
si_perms = frappe.get_all('DocPerm', 
    filters={'parent': 'Sales Invoice', 'role': role},
    fields=['read', 'write', 'create', 'delete']
)

if si_perms:
    for p in si_perms:
        print(f'   Read: {p.read}, Write: {p.write}, Create: {p.create}, Delete: {p.delete}')
else:
    print('   ❌ No permissions found!')

print()

# Check Number Card is_public status
print('3. Number Cards is_public status:')
cards = frappe.get_all('Number Card', 
    filters={'name': ['like', 'SP %']},
    fields=['name', 'is_public', 'type', 'document_type']
)

for card in cards:
    print(f'   {card.name}: is_public={card.is_public}, type={card.type}, document_type={card.document_type}')

print()

# Test permission check as sales partner user
print('4. Testing permission check:')
# Get a sales partner user
sp_users = frappe.get_all('User', 
    filters={'user_type': 'Website User', 'enabled': 1},
    fields=['name'],
    limit=1
)

if sp_users:
    user = sp_users[0].name
    print(f'   Testing as user: {user}')
    
    # Switch to that user's context
    frappe.set_user(user)
    
    # Check if they can see Number Cards
    visible_cards = frappe.get_all('Number Card', 
        filters={'name': ['like', 'SP %']},
        fields=['name']
    )
    print(f'   Number Cards visible: {len(visible_cards)}')
    for card in visible_cards:
        print(f'     - {card.name}')
    
    frappe.set_user('Administrator')
else:
    print('   ⚠️  No sales partner users found')

frappe.destroy()


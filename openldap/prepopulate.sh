#!/bin/bash

echo "Pre-populating ldap entries, first waiting for ldap to start"

sleep 3

adminUserDn="cn=admin,dc=lomin,dc=ai"
adminPassword="lomin"

for file in `ls /etc/ldap/prepopulate/*.ldif`; do
  ldapadd -x -D $adminUserDn -w $adminPassword -f "$file"
done

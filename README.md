Version: 0.1.0
Author: Jesus Moscosa
License: MIT

Gmai-Salesforce Integration is a Python-based automation project that pulls promotional emails from a Gmail account into Salesforce to simulate real-world transactions. 

When a promotional or marketing email arrives in Gmail, the integration:
1. Extract sender and metadata information
2. Checks Salesforce for an existing Contact or Lead. 
3. Updates the record if details have changed.
4. Creates a new contact is no match is found. 

This workflow aims to elminate data entry and to capture and analyze marketing campaings from companies that we intentionally register for. 
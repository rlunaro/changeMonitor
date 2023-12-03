'''
Created on Nov 7, 2020

@author: rluna
'''

import os
import os.path
import pickle
import base64

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from email.mime.text import MIMEText
from googleapiclient.discovery import build


class Gmail(object):
    '''
    sends an email using gmail
    '''
    # If modifying these scopes, delete the file token.pickle.
    SCOPES = ['https://www.googleapis.com/auth/gmail.send']
    token_file = "token.pickle"
    credentials = {}


    def __init__(self, credentials : dict ):
        self.credentials = credentials
    

    def loadOrValidateCredentials( self ):
        self.creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time
        if os.path.exists(self.token_file) : 
            with open(self.token_file, 'rb') as token : 
                self.creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_config(
                                self.credentials, self.SCOPES )
                self.creds = flow.run_local_server(port=50507)
            # Save the credentials for the next run
            with open(self.token_file, 'wb') as token:
                pickle.dump(self.creds, token)
        self._createService()
    

    def _createService(self):
        self._gmail_service = build('gmail', 'v1', credentials=self.creds)
        
    def sendSimpleEmail(self,
                    emailFrom, 
                    emailTo,
                    emailSubject, 
                    emailBody ):
        if isinstance( emailTo, str ) : 
            emailTo = [emailTo]
        
        for address in emailTo :  
            message = MIMEText(emailBody)
            message['from'] = emailFrom
            message['to'] = address
            message['subject'] = emailSubject
            encoded_message = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode('ascii')}
            self._gmail_service.users().messages().send(userId=emailFrom, body=encoded_message).execute()    

    def sendHtmlEmail(self,
                    emailFrom, 
                    emailTo,
                    emailSubject, 
                    emailBody ):
        if isinstance( emailTo, str ) : 
            emailTo = [emailTo]
        
        for address in emailTo :  
            message = MIMEText(emailBody, "html")
            message['from'] = emailFrom
            message['to'] = address
            message['subject'] = emailSubject
            encoded_message = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode('ascii')}
            self._gmail_service.users().messages().send(userId=emailFrom, body=encoded_message).execute()    



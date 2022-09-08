

import json
import datetime
import time
import os
import dateutil.parser
import logging
import boto3
import tarfile
import csv
import re
from io import StringIO
from io import BytesIO


logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3client = boto3.client('s3')
s3 = boto3.resource('s3')

comprehend = boto3.client('comprehend')

bucket=os.environ['S3_BUCKET']
input_bucket = s3.Bucket(bucket)




def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }


def confirm_intent(session_attributes, intent_name, slots, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ConfirmIntent',
            'intentName': intent_name,
            'slots': slots,
            'message': message
        }
    }


def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type':'Close',
            'fulfillmentState':fulfillment_state,
            'message':message
        }
    }
    return response


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }





def safe_int(n):
    
    if n is not None:
        return int(n)
    return n


def try_ex(func):
   

    try:
        return func()
    except KeyError:
        return None





def build_validation_result(isvalid, violated_slot, message_content):
    return {
        'isValid': isvalid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }



def get_summary(intent_request):
    # Declare variables and get handle to the S3 bucket containing the Textract output
    session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}

    i = 0
    qty = 0

    for file in input_bucket.objects.all():
        i += 1
        selected_phrases = ""
        input_bucket_text_file = s3.Object(bucket, file.key)
        text_file_contents = str(input_bucket_text_file.get()['Body'].read().decode('utf-8'))

        
        detected_entities = comprehend.detect_entities(
        Text=text_file_contents,
        LanguageCode="en"
        )
        print(detected_entities)

        selected_entity_types = ["ORGANIZATION", "OTHER", "DATE", "QUANTITY", "LOCATION"]
        
        for x in detected_entities['Entities']:
            if x['Type'] == "OTHER" and x['EndOffset'] < 40:
                nr = x['Text']
            if x['Type'] == "QUANTITY" and x['EndOffset'] > 350:
                qty = round((qty + float(x['Text'])), 2)
    return close(
        session_attributes,
        'Fulfilled',
        {
            'contentType': 'PlainText',
            'content': 'I reviewed your input documents and found {} invoices with invoice numbers {} totaling ${}. I can get you invoice details or invoice notes. Simply type your request'.format(i, nr, str(qty))
        }
    )


def get_details(intent_request):
    bill = ""
    billsum = []
    result = ""
    y = True
    session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
    inr = intent_request['currentIntent']['slots']['invoicenr']

    r = 0
    i = 0
    for file in input_bucket.objects.all():
        i += 1
        selected_phrases = ""
        input_bucket_text_file = s3.Object(bucket, file.key)
        text_file_contents = str(input_bucket_text_file.get()['Body'].read().decode('utf-8'))
        
        detected_entities = comprehend.detect_entities(
        Text=text_file_contents,
        LanguageCode="en"
        )


        print(detected_entities)
        selected_entity_types = ["DATE", "QUANTITY"]
        for x in detected_entities['Entities']:
            if x['Type'] in "OTHER":
                detnr = x['Text']
        if detnr == inr:
            htmlstring = "Invoice Details for " + detnr + ": "
            for x in detected_entities['Entities']:
                if x['Type'] in selected_entity_types and x['EndOffset'] > 40 and x['EndOffset'] <= 337:
                    r += 1
                    if r == 1:
                        htmlstring += "On " + x['Text'] + " "
                    elif r == 2:
                        htmlstring += "for the item " + x['Text'] + " "
                    else:
                        htmlstring += " there is a charge of " + str(x['Text'].split()[0]) + ". "
                        r = 0
                    print("HTMLString is: " + htmlstring)

            result = htmlstring + " You can request me for invoice notes or simply close this chat."
        else:
            result = 'Sorry I could not find a match for that Invoice Number. Please request for invoice details with a valid Invoice Number.'
    return close(
        session_attributes,
        'Fulfilled',
        {
            'contentType': 'PlainText',
            'content': result
        }
    )




def get_notes(intent_request):

    session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
    inr = intent_request['currentIntent']['slots']['invoicenr']

    i = 0
    notes = ""
    phrases = []

    for file in input_bucket.objects.all():
        i += 1
        selected_phrases = ""
        input_bucket_text_file = s3.Object(bucket, file.key)
        text_file_contents = str(input_bucket_text_file.get()['Body'].read().decode('utf-8'))

        detected_entities = comprehend.detect_entities(
        Text=text_file_contents,
        LanguageCode="en"
        )
        #print(detected_entities)
        #selected_entity_types = ["ORGANIZATION", "OTHER", "DATE", "QUANTITY", "LOCATION"]
        for x in detected_entities['Entities']:
            if x['Type'] in "OTHER":
                detnr = x['Text']
        if detnr == inr:
        #Comprehend Key Phrases Detection
            detected_key_phrases = comprehend.detect_key_phrases(
                Text=text_file_contents,
                LanguageCode="en"
                )
            print(detected_key_phrases)
            for y in detected_key_phrases['KeyPhrases']:
                if y['EndOffset'] > 185 and y['EndOffset'] <= 337:
                    selected_phrases = " " + y['Text'] + selected_phrases + " "

            #phrases.append(selected_phrases)
            print("Selected Phrases are: " + selected_phrases)
            #notes = notes + ".  Notes for Invoice " + str(i) + " are: " + str(phrases[i - 1])
            result = "Invoice Notes for " + detnr + ": " + selected_phrases
        else:
            result = 'Sorry I could not find a match for that Invoice Number. Please request for invoice notes with a valid Invoice Number'
    return close(
        session_attributes,
        'Fulfilled',
        {
            'contentType': 'PlainText',
            'content': result + '. Feel free to try the options again or you can simply close this chat'
        }
    )

def dispatch(intent_request):
    
    print("Intent Request is: " + str(intent_request))
    logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request['currentIntent']['name']

    if intent_name == 'GetInvoiceSummary':
        return get_summary(intent_request)
    elif intent_name == 'GetInvoiceDetails':
        return get_details(intent_request)
    elif intent_name == 'GetInvoiceNotes':
        return get_notes(intent_request)

    raise Exception('Intent with name ' + intent_name + ' not supported')





def lambda_handler(event, context):
    
    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)

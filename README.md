# Conversational Insights from Invoices Solution

Industrial organizations have a large number of physical documents such as invoices that need to processed. It is difficult to extract information from a scanned invoices that contains data in form of tables, forms and check boxes. Usually these problems have been addressed either by manual effort or custom code or by using Optical Character Recognition (OCR) technology. However, that too requires pre-defined templates for form extraction and workflows.

Extracting insights from these invoices for their end users require building a complex NLP model. Training the model would require a large amount of training data , computing resources and can be expensive and time-consuming.

Also , it is quite expensive and cumbersome to use human help desk for organizations.

This project aims to solve these problems by using AWS AI services(Textract, Comprehend and Lex) to create an automated serverless solution for text processing ,insight discovery and interaction in natural language with end users. 

## How does it work on backend?
1 ) The backend administrator uses the AWS Console or AWS CLI to upload the PDF documents or images to S3 bucket.
2 ) The Amazon S3 upload triggers a AWS Lambda function.


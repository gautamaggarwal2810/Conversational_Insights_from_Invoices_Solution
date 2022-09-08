import json
import time
import boto3
import os
textract = boto3.client('textract')
s3 = boto3.client('s3')
 
def handler(event, context):
    message = json.loads(event['Records'][0]['Sns']['Message'])
    jobId = message['JobId']
    print("JobId="+jobId)
    output_bucket = os.environ["OUT_PUT_S3_BUCKET"]

    status = message['Status']
    print("Status="+status)

    if status != "SUCCEEDED":
        return {
            
            "status": status
        }
    text_extractor = TextExtractor()

    pages = text_extractor.extract_text(jobId)
    file=jobId
    content=pages[1]['Content']
    f = open("/tmp/file.txt", "w")
    f.write(content)
    f.close()
    s3_response = s3.upload_file("/tmp/file.txt",output_bucket,file+".txt")
    print(list(pages.values()))

class TextExtractor():
    def extract_text(self, jobId):
       

        textract_result = self.__get_textract_result(jobId)
        pages = {}
        self.__extract_all_pages(jobId, textract_result, pages, [])
        return pages

    def __get_textract_result(self, jobId):
        

        result = textract.get_document_text_detection(
            JobId=jobId
        )
        return result

    def __extract_all_pages(self, jobId, textract_result, pages, page_numbers):
      

        blocks = [x for x in textract_result['Blocks']
                  if x['BlockType'] == "LINE"]
        for block in blocks:
            if block['Page'] not in page_numbers:
                page_numbers.append(block['Page'])
                pages[block['Page']] = {
                    "Number": block['Page'],
                    "Content": block['Text']
                }
            else:
                pages[block['Page']]['Content'] += " " + block['Text']

        nextToken = textract_result.get("NextToken", "")
        if nextToken != '':
            textract_result = textract.get_document_text_detection(
                JobId=jobId,
                NextToken=nextToken
            )
            self.__extract_all_pages(jobId,
                                     textract_result,
                                     pages,
                                     page_numbers)